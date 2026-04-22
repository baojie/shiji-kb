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


def _build_table_row_anchors(content):
    """为每张表格数据行生成 rN 锚点（与 render_shiji_html.py 行号规则一致）"""
    anchors = {}
    lines = content.split('\n')
    row_counter = 0
    i, n = 0, len(lines)
    while i < n:
        stripped = lines[i].strip()
        if stripped.startswith('|') and '|' in stripped[1:]:
            block = []
            j = i
            while j < n and lines[j].strip().startswith('|'):
                block.append(j)
                j += 1
            if len(block) >= 2:
                sep = lines[block[1]].strip().replace('-', '')
                data_start = 2 if re.match(r'^[\s|:-]+$', sep) else 1
                for idx in block[data_start:]:
                    row_text = lines[idx].strip()
                    first_cell = row_text[1:].split('|', 1)[0] if row_text.startswith('|') else ''
                    m = re.match(r'^\s*\[r(\d+)\]\s*', first_cell)
                    if m:
                        rn = m.group(1)
                    else:
                        row_counter += 1
                        rn = str(row_counter)
                    anchors[idx] = f'r{rn}'
            i = j
        else:
            i += 1
    return anchors


def extract_inline_aliases():
    """扫描所有 tagged.md，提取 〖TYPE X|Y〗 内联消歧对。

    Returns: {type: {(surface, canonical): set of (chapter, para)}}
    """
    records = defaultdict(lambda: defaultdict(set))

    for fpath in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        chap = fpath.stem.replace('.tagged', '')
        content = fpath.read_text(encoding='utf-8')
        row_anchor_map = _build_table_row_anchors(content)
        current_para = '0'

        for idx, line in enumerate(content.split('\n')):
            if idx in row_anchor_map:
                current_para = row_anchor_map[idx]
            else:
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


# 不加国名前缀的 所属国（上古/三代/外邦/汉朝 — 谥号单独足以识别或另有命名约定）
_NO_PREFIX_GUO = {
    '上古', '夏', '商', '殷', '商（殷）', '汉',
    '匈奴', '南越', '东越', '闽越', '东越（东瓯）', '夜郎', '滇',
    '箕子朝鲜', '卫氏朝鲜',
    '翟', '塞', '雍', '临菑',
}


def _normalize_guo(guo):
    """把 rulers.json 的 所属国 字段标准化为用作 canonical 的国名前缀；
    返回空串表示不加前缀。"""
    if not guo:
        return ''
    # 剥离括号备注：'齐（田齐）' → '齐'；'胶东国（景帝子所封）' → '胶东国'
    g = re.sub(r'[（(].*?[）)]', '', guo).strip()
    # 前缀特殊判定：带"国"后缀的汉侯国（梁国/代国/河间国/…）去掉"国"
    if g.endswith('国') and len(g) > 1:
        g = g[:-1]
    # 吴/越/赵/燕/... 等原本就是单字
    # 不加前缀的情形
    if g in _NO_PREFIX_GUO:
        return ''
    if '朝鲜' in g:
        return ''
    return g


# 传统谥号模式：1-2 字 + 公/王/侯/伯/君/子（总长 ≤3）
# 覆盖 "穆公"/"昭王"/"惠文王"/"武灵王"/"孝成王" 等，
# 排除 "西楚霸王"(4字)/"始皇帝" 等自号。
_CONVENTIONAL_SHIHAO_RE = re.compile(r'^[\u4e00-\u9fff]{1,2}[公王侯伯君子]$')


def _ruler_canonical(r):
    """构造 ruler 的 canonical：所属国前缀 + 谥号；若无 谥号 退回 名。
    - 已含前缀则不重复追加
    - 特殊 所属国（上古/夏/商/匈奴/…）不加前缀
    - 仅传统 "XX公/XX王/XX侯/..." 才加前缀；自号如 "西楚霸王"/"始皇帝" 保留原形
    """
    shihao = (r.get('谥号') or '').strip()
    if shihao:
        prefix = _normalize_guo(r.get('所属国') or '')
        if prefix and not shihao.startswith(prefix) \
                and _CONVENTIONAL_SHIHAO_RE.match(shihao):
            return prefix + shihao
        return shihao
    return (r.get('名') or '').strip()


def load_rulers():
    """rulers.json 的别名字段 → {(surface, canonical): set()}（refs 空）.

    canonical 构造规则见 _ruler_canonical：所属国+谥号（避免裸谥号歧义）。
    """
    records = defaultdict(set)
    if not RULERS_JSON.exists():
        return records
    with open(RULERS_JSON, encoding='utf-8') as f:
        data = json.load(f)
    rulers = data.get('rulers', [])
    for r in rulers:
        canonical = _ruler_canonical(r)
        if not canonical:
            continue
        # 裸谥号本身作为别名 → 指向带前缀 canonical（覆盖 rulers.json 旧 alias 结构）
        shihao = (r.get('谥号') or '').strip()
        if shihao and shihao != canonical:
            records[(shihao, canonical)].add(('rulers.json', '*'))
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


# 可用作 canonical 前缀的诸侯邦国（单字+双字）
_CANONICAL_STATE_PREFIXES = {
    '周', '秦', '齐', '鲁', '晋', '楚', '燕', '赵', '魏', '韩',
    '宋', '郑', '卫', '陈', '蔡', '曹', '吴', '越', '虢', '杞',
    '徐', '邾', '滕', '许', '莒', '代', '梁', '中山', '东周', '西周',
    '吕', '薛',
}


def _promote_state_prefixed_canonical(canonical, aliases):
    """若 aliases 中存在 '{state}+canonical' 形式（如 '秦穆公'、'周文王'），
    则返回该形式作为真正 canonical；否则返回原 canonical。
    用于修正 鲍捷 md / legacy 里用裸谥号作 canonical 的历史问题。"""
    for alias in aliases:
        if not alias or alias == canonical:
            continue
        if alias.endswith(canonical) and len(alias) > len(canonical):
            prefix = alias[:-len(canonical)]
            if prefix in _CANONICAL_STATE_PREFIXES:
                return alias
    return canonical


def load_baojie_md():
    """解析 private/to鲍捷 史记里的人名.md 的称呼对照。

    格式示例：
        黄帝：有熊氏、帝轩辕、轩辕、黄宗（《竹书纪年》）、...
        商鞅：商君、卫鞅、公孙鞅、鞅（《战国策·秦策》）、...

    归一化：若首列是裸谥号（穆公/昭王/…）且别名列含 {国}+canonical
    （秦穆公/周昭王），则把带前缀形作为真正 canonical，避免裸谥号歧义。
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
        # 先 parse 出 clean alias 列表
        clean_aliases = []
        for alias in re.split(r'[、，,]', aliases_part):
            alias = re.sub(r'[（(][^）)]*[）)]', '', alias).strip()
            alias = alias.strip('"" """"\'\'')
            if not alias or alias == '无':
                continue
            if len(alias) > 12:
                continue
            if not re.match(r'^[\u4e00-\u9fff]+$', alias):
                continue
            clean_aliases.append(alias)
        # 提升带国名前缀的 alias 为真 canonical
        canonical = _promote_state_prefixed_canonical(canonical, clean_aliases)
        for alias in clean_aliases:
            if alias == canonical:
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
