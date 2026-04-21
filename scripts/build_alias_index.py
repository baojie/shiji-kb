#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_alias_index.py — 为 docs/ 静态站构建别名扩展索引

合并两份数据源，按 (type, canonical) 聚合每个 canonical 的 "别名集合"，
然后在 surface 粒度做查表：每个 surface 的变体 = 所有把它列入别名集合的
canonical 对应簇的并集。

**不做跨 canonical 的全局合并**。并查集会因"上"、"帝"等高频共享别名把
多个皇帝合为一簇，使查询严重污染。直接映射使污染只发生在查询共享别名
本身时（如查"上"），而查"刘邦"时只汇聚 (person, 刘邦) 与 (person, 汉高祖)
这两个明确指向 刘邦 的簇。

数据源:
    kg/entities/data/entity_aliases.json   # (surface → canonical) 边，类型最全
    kg/entities/data/entity_index.json     # canonical → {aliases, refs}

排除规则:
    - type == 'identity'：上下文指代（如"君王"指刘邦），非正式别名，整类跳过
    - **title-like surface**：若 S 同时出现在多个 canonical 的别名集里，且这些
      canonical 彼此之间没有其它共享 surface 把他们串成同一人，则 S 是称谓
      （如"上"、"帝"、"王"、"主"），从所有别名集中剔除、不入变体表。
    - 变体数 < 2：无真正可扩展内容，不入表

输出:
    docs/data/alias-index.json
    {
      "version": 3,
      "sources": [...],
      "excluded_types": ["identity"],
      "variants": { "刘邦": ["刘邦", "上", "刘季", ...], ... }
    }
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALIASES_FILE = ROOT / 'kg' / 'entities' / 'data' / 'entity_aliases.json'
INDEX_FILE = ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
OUT_FILE = ROOT / 'docs' / 'data' / 'alias-index.json'

EXCLUDED_TYPES = {'identity'}


def build_alias_sets(aliases_data: dict, index_data: dict) -> dict:
    """为每个 (type, canonical) 聚合其完整的别名集合（含 canonical 本身）。"""
    sets: dict[tuple, set[str]] = {}

    # entity_aliases.json：按类型分组的 (surface, canonical) 边
    for typ, items in aliases_data.items():
        if typ in EXCLUDED_TYPES:
            continue
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            c = it.get('canonical')
            s = it.get('surface')
            if not (isinstance(c, str) and c and isinstance(s, str) and s):
                continue
            key = (typ, c)
            sets.setdefault(key, set()).update([c, s])

    # entity_index.json：canonical → {aliases, ...}
    for typ, ents in index_data.items():
        if typ in EXCLUDED_TYPES:
            continue
        if not isinstance(ents, dict):
            continue
        for canonical, node in ents.items():
            if not (isinstance(canonical, str) and canonical and isinstance(node, dict)):
                continue
            key = (typ, canonical)
            cluster = sets.setdefault(key, set())
            cluster.add(canonical)
            for a in node.get('aliases') or []:
                if isinstance(a, str) and a:
                    cluster.add(a)

    return sets


def detect_title_surfaces(alias_sets: dict) -> set[str]:
    """
    称谓检测：若 surface S 出现在多个 canonical 簇中、且这些簇通过
    非-S surface 分成 2+ 个不相交组，则 S 是 title-like（称谓/泛指）。

    典型例：
      - "上" 出现在 (person, 汉高祖) 与 (person, 汉景帝)，两簇除"上"外无交集
        → 上 = 皇上的泛称，非真别名 → 剔除
      - "汉王" 出现在 (person, 刘邦) 与 (person, 汉高祖)，两簇还共享
        刘季/沛公/高祖 等 → 同一人 → 保留
    """
    surface_owners: dict[str, set] = {}
    for key, cluster in alias_sets.items():
        for s in cluster:
            surface_owners.setdefault(s, set()).add(key)

    titles: set[str] = set()
    for s, owners in surface_owners.items():
        if len(owners) < 2:
            continue
        # 只考虑 rich owner：除 s 外至少还有一个 surface 可用来判定身份同一性。
        # 纯 singleton canonical（如 person/汉王 只含自己）既无法证明"同一人"
        # 也无法证伪，应保持中立，不让它们凭空把 surface 判为称谓。
        rich_owners = [o for o in owners if len(alias_sets[o] - {s}) >= 1]
        if len(rich_owners) < 2:
            continue
        parent = {o: o for o in rich_owners}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        # 收集每个 rich owner 拥有的非-S surface
        surf_idx: dict[str, list] = {}
        for o in rich_owners:
            for other in alias_sets[o]:
                if other == s:
                    continue
                surf_idx.setdefault(other, []).append(o)
        for olist in surf_idx.values():
            if len(olist) < 2:
                continue
            base = olist[0]
            for o in olist[1:]:
                union(base, o)

        # 聚合每个连通分量的非-S surface；分量至少含 2 个非-S surface
        # 才算"强分量"——能独立证明自己是一个完整实体。弱分量（如某个孤立
        # canonical 只恰好含 S 和一个罕见 surface）不足以证伪 S 的同一性。
        comp_surfaces: dict = {}
        for o in rich_owners:
            r = find(o)
            comp_surfaces.setdefault(r, set()).update(alias_sets[o] - {s})
        strong_components = sum(1 for surfs in comp_surfaces.values() if len(surfs) >= 2)
        if strong_components >= 2:
            titles.add(s)
    return titles


def build_variants(alias_sets: dict, title_surfaces: set[str]) -> dict[str, list[str]]:
    """surface → 所有包含它的簇的并集变体；剔除 title-like surface。"""
    surface_to_variants: dict[str, set[str]] = {}
    for _key, cluster in alias_sets.items():
        cleaned = cluster - title_surfaces
        for s in cleaned:
            surface_to_variants.setdefault(s, set()).update(cleaned)

    result: dict[str, list[str]] = {}
    for surface, variants in surface_to_variants.items():
        if len(variants) < 2:
            continue
        rest = sorted(v for v in variants if v != surface)
        result[surface] = [surface] + rest
    return result


def main():
    if not ALIASES_FILE.is_file():
        print(f'错误: 源文件不存在 {ALIASES_FILE}', file=sys.stderr)
        sys.exit(1)
    if not INDEX_FILE.is_file():
        print(f'错误: 源文件不存在 {INDEX_FILE}', file=sys.stderr)
        sys.exit(1)

    with ALIASES_FILE.open(encoding='utf-8') as f:
        aliases_data = json.load(f)
    with INDEX_FILE.open(encoding='utf-8') as f:
        index_data = json.load(f)

    alias_sets = build_alias_sets(aliases_data, index_data)
    title_surfaces = detect_title_surfaces(alias_sets)
    variants = build_variants(alias_sets, title_surfaces)

    payload = {
        'version': 4,
        'sources': [
            'kg/entities/data/entity_aliases.json',
            'kg/entities/data/entity_index.json',
        ],
        'excluded_types': sorted(EXCLUDED_TYPES),
        'excluded_titles_count': len(title_surfaces),
        'variants': variants,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(',', ':')),
        encoding='utf-8',
    )

    total_variants = sum(len(v) for v in variants.values())
    size_kb = OUT_FILE.stat().st_size / 1024
    print(f'✓ canonical 簇: {len(alias_sets)}')
    print(f'✓ 剔除 title-like surface: {len(title_surfaces)}')
    if title_surfaces:
        sample = sorted(title_surfaces, key=len)[:15]
        print(f'  样例: {sample}')
    print(f'✓ 可扩展 surface: {len(variants)}')
    print(f'✓ 变体总数（含重复）: {total_variants}')
    print(f'✓ 排除类型: {sorted(EXCLUDED_TYPES)}')
    print(f'✓ 输出: {OUT_FILE} ({size_kb:.1f} KB)')


if __name__ == '__main__':
    main()
