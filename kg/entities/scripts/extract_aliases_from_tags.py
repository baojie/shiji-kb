#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从标注文件的 〖@X|Y〗 内联消歧 + disambiguation_map.json + rulers.json
+ 鲍捷私文档（可选） + 旧 entity_aliases.json 合并生成新 entity_aliases.json。

新结构（4 列数组）：
{
  "person": [
    {"surface": "昭王", "type": "person", "canonical": "秦昭王",
     "refs": [["005_秦本纪","20.1"], ["071_樗里子甘茂列传","3"]]},
    {"surface": "昭王", "type": "person", "canonical": "燕昭王",
     "refs": [["034_燕召公世家","17"]]}
  ],
  "place": [...],
  ...
}

数据来源优先级：
  1. chapter_md/*.tagged.md 的 〖@X|Y〗（最权威）
  2. disambiguation_map.json 章节级消歧
  3. rulers.json 别名字段
  4. private/to鲍捷 史记里的人名.md（可选）
  5. 旧 entity_aliases.json 保底

输出：
  kg/entities/data/entity_aliases.json（新 4 列结构）
  kg/entities/data/entity_aliases.v1.bak.json（旧结构备份，若未备份过）
  kg/entities/data/alias_conflicts.json（冲突记录）
"""

import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CHAPTER_DIR = _ROOT / 'chapter_md'
ALIAS_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_aliases.json'
BACKUP_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_aliases.v1.bak.json'
CONFLICT_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'alias_conflicts.json'
DISAMBIG_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'disambiguation_map.json'
RULERS_JSON = _ROOT / 'kg' / 'relations' / 'rulers.json'
BAOJIE_MD = _ROOT / 'private' / 'to鲍捷 史记里的人名.md'

# 10 类对称符号 + 5 类非对称
ENTITY_TYPES = [
    ('person',       r'〖@([^〖〗\n]+)〗'),
    ('place',        r'〖=([^〖〗\n]+)〗'),
    ('official',     r'〖;([^〖〗\n]+)〗'),
    ('time',         r'〖%([^〖〗\n]+)〗'),
    ('dynasty',      r'〖&([^〖〗\n]+)〗'),
    ('feudal-state', r'〖◆([^〖〗\n]+)〗'),
    ('institution',  r'〖\^([^〖〗\n]+)〗'),
    ('tribe',        r'〖~([^〖〗\n]+)〗'),
    ('identity',     r'〖#([^〖〗\n]+)〗'),
    ('artifact',     r'〖•([^〖〗\n]+)〗'),
    ('astronomy',    r'〖!([^〖〗\n]+)〗'),
    ('biology',      r'〖\+([^〖〗\n]+)〗'),
    ('quantity',     r'〖\$([^〖〗\n]+)〗'),
    ('mythical',     r'〖\?([^〖〗\n]+)〗'),
    ('book',         r'〖\{([^〖〗\n]+)〗'),
    ('ritual',       r'〖:([^〖〗\n]+)〗'),
    ('legal',        r'〖\[([^〖〗\n]+)〗'),
    ('concept',      r'〖_([^〖〗\n]+)〗'),
]

PARA_NUM_PATTERN = r'\[(\d+(?:\.\d+)*)\]'


def extract_inline_aliases():
    """扫描所有 tagged.md，提取 〖TYPE X|Y〗 内联消歧对。

    Returns: {type: {(surface, canonical): set of (chapter, para)}}
    """
    records = defaultdict(lambda: defaultdict(set))

    for fpath in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        chap = fpath.stem.replace('.tagged', '')
        content = fpath.read_text(encoding='utf-8')
        current_para = '0'

        for line in content.split('\n'):
            pn = re.search(PARA_NUM_PATTERN, line)
            if pn:
                current_para = pn.group(1)
            for type_key, pat in ENTITY_TYPES:
                for m in re.finditer(pat, line):
                    raw = m.group(1).strip()
                    if '|' not in raw:
                        continue
                    parts = raw.split('|', 1)
                    surface = parts[0].strip()
                    canonical = parts[1].strip()
                    if not surface or not canonical:
                        continue
                    records[type_key][(surface, canonical)].add((chap, current_para))

    return records


def load_disambig_map():
    """disambiguation_map.json → {(surface, canonical): {(chapter, '*')}}."""
    records = defaultdict(set)
    if not DISAMBIG_JSON.exists():
        return records
    with open(DISAMBIG_JSON, encoding='utf-8') as f:
        data = json.load(f)
    # data is {"004": {"武王": "周武王", ...}, ...}
    for chap, d in data.items():
        # chap might be just "004", need to match with full chapter id
        # leave as "004" for now; we don't strictly need full id for alias refs
        if not isinstance(d, dict):
            continue
        for surface, canonical in d.items():
            records[(surface, canonical)].add((chap, '*'))
    return records


def load_rulers():
    """rulers.json 的别名字段 → {(surface, canonical): set()}（refs 空）."""
    records = defaultdict(set)
    if not RULERS_JSON.exists():
        return records
    with open(RULERS_JSON, encoding='utf-8') as f:
        data = json.load(f)
    rulers = data.get('rulers', [])
    for r in rulers:
        canonical = (r.get('谥号') or r.get('名') or '').strip()
        if not canonical:
            continue
        aliases = r.get('别名') or []
        if not isinstance(aliases, list):
            continue
        for alias in aliases:
            alias = (alias or '').strip()
            if not alias or alias == canonical:
                continue
            records[(alias, canonical)].add(('rulers.json', '*'))
        # 名 作为 canonical 的别名（若谥号存在）
        name = (r.get('名') or '').strip()
        if name and name != canonical and r.get('谥号'):
            records[(name, canonical)].add(('rulers.json', '*'))
    return records


def load_baojie_md():
    """解析 private/to鲍捷 史记里的人名.md 的称呼对照。

    格式示例：
        黄帝：有熊氏、帝轩辕、轩辕、黄宗（《竹书纪年》）、...
        商鞅：商君、卫鞅、公孙鞅、鞅（《战国策·秦策》）、...
    """
    records = defaultdict(set)
    if not BAOJIE_MD.exists():
        return records
    content = BAOJIE_MD.read_text(encoding='utf-8')
    # 模式：行首可能缩进 + 数字编号. + 空格 + 规范名：别名列表 OR 规范名：别名
    for line in content.split('\n'):
        line = line.strip()
        # 匹配 "canonical：aliases..."（中文冒号）
        m = re.match(r'^(?:\d+\.\s*)?([\u4e00-\u9fff]{1,8})[：:](.+)$', line)
        if not m:
            continue
        canonical = m.group(1).strip()
        aliases_part = m.group(2).strip()
        # 按"、"分割，去掉括号及内部注明来源
        for alias in re.split(r'[、，,]', aliases_part):
            alias = re.sub(r'[（(][^）)]*[）)]', '', alias).strip()
            alias = alias.strip('"" """"\'\'')
            if not alias or alias == '无' or alias == canonical:
                continue
            # 过滤过长或非汉字项
            if len(alias) > 12:
                continue
            if not re.match(r'^[\u4e00-\u9fff]+$', alias):
                continue
            records[(alias, canonical)].add(('baojie_md', '*'))
    return records


def load_legacy_aliases():
    """旧 entity_aliases.json 若为旧结构，按 {canonical:[aliases]} 展开。"""
    records = defaultdict(lambda: defaultdict(set))
    if not ALIAS_JSON.exists():
        return records
    with open(ALIAS_JSON, encoding='utf-8') as f:
        data = json.load(f)
    # 判断是否旧结构
    if not isinstance(data, dict):
        return records
    for type_key, d in data.items():
        if isinstance(d, dict):
            # 旧结构 {canonical: [aliases]}
            for canonical, aliases in d.items():
                if not isinstance(aliases, list):
                    continue
                for alias in aliases:
                    if not alias or alias == canonical:
                        continue
                    records[type_key][(alias, canonical)].add(('legacy', '*'))
        elif isinstance(d, list):
            # 已经是新结构，跳过（本函数不应被调用）
            pass
    return records


def merge_all():
    print('[1/5] 扫描 chapter_md 内联消歧 〖TYPE X|Y〗 ...', file=sys.stderr)
    inline = extract_inline_aliases()
    n_inline = sum(len(v) for v in inline.values())
    print(f'      → {n_inline} 条 (surface, canonical) 对', file=sys.stderr)

    print('[2/5] 加载 disambiguation_map.json ...', file=sys.stderr)
    disambig = load_disambig_map()
    print(f'      → {len(disambig)} 条章节级消歧', file=sys.stderr)

    print('[3/5] 加载 rulers.json 别名 ...', file=sys.stderr)
    rulers = load_rulers()
    print(f'      → {len(rulers)} 条君主别名', file=sys.stderr)

    print('[4/5] 加载 鲍捷 md (private/to鲍捷 史记里的人名.md) ...', file=sys.stderr)
    baojie = load_baojie_md()
    print(f'      → {len(baojie)} 条鲍捷别名', file=sys.stderr)

    print('[5/5] 加载旧 entity_aliases.json ...', file=sys.stderr)
    legacy = load_legacy_aliases()
    n_legacy = sum(len(v) for v in legacy.values())
    print(f'      → {n_legacy} 条旧别名', file=sys.stderr)

    # 合并：只有 person 类型才吃 disambig/rulers/baojie
    merged = defaultdict(lambda: defaultdict(set))

    # 1. inline（所有类型）
    for type_key, d in inline.items():
        for key, refs in d.items():
            merged[type_key][key].update(refs)

    # 2. disambig 全部视为 person
    for key, refs in disambig.items():
        merged['person'][key].update(refs)

    # 3. rulers 视为 person
    for key, refs in rulers.items():
        merged['person'][key].update(refs)

    # 4. baojie 视为 person
    for key, refs in baojie.items():
        merged['person'][key].update(refs)

    # 5. legacy（按 type 分类）
    for type_key, d in legacy.items():
        for key, refs in d.items():
            # 只在完全缺失时补录
            if key not in merged.get(type_key, {}):
                merged[type_key][key].update(refs)

    return merged


def build_output(merged):
    """转换为输出 JSON 结构。"""
    output = {}
    conflicts = []

    for type_key in sorted(merged.keys()):
        rows = []
        # 按 surface 分组检查冲突
        by_surface = defaultdict(list)
        for (surface, canonical), refs in merged[type_key].items():
            by_surface[surface].append((canonical, refs))

        for surface in sorted(by_surface.keys()):
            cans = by_surface[surface]
            # 生成每个 (surface, canonical) 一行
            for canonical, refs in sorted(cans):
                refs_list = sorted(list(refs))
                rows.append({
                    'surface': surface,
                    'type': type_key,
                    'canonical': canonical,
                    'refs': refs_list,
                })
            # 若 surface 映射到 > 1 canonical，记入冲突/歧义报告
            if len(cans) > 1:
                conflicts.append({
                    'type': type_key,
                    'surface': surface,
                    'canonicals': [c for c, _ in cans],
                })

        output[type_key] = rows

    return output, conflicts


def main():
    merged = merge_all()
    output, conflicts = build_output(merged)

    # 备份旧文件
    if ALIAS_JSON.exists() and not BACKUP_JSON.exists():
        shutil.copy(ALIAS_JSON, BACKUP_JSON)
        print(f'已备份旧 entity_aliases.json → {BACKUP_JSON.name}', file=sys.stderr)

    # 写入新文件
    with open(ALIAS_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    with open(CONFLICT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'ambiguous_surfaces': conflicts}, f, ensure_ascii=False, indent=2)

    # 汇总
    print('\n== 输出汇总 ==', file=sys.stderr)
    for t in sorted(output.keys()):
        print(f'  {t}: {len(output[t])} 条', file=sys.stderr)
    print(f'  歧义 surface 总数（多 canonical）: {len(conflicts)}', file=sys.stderr)
    print(f'\n写入 {ALIAS_JSON.relative_to(_ROOT)}', file=sys.stderr)
    print(f'写入 {CONFLICT_JSON.relative_to(_ROOT)}', file=sys.stderr)


if __name__ == '__main__':
    main()
