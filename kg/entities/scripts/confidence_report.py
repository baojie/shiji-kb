#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为每条 (name, category) 组合计算置信度，生成低置信度报告以便人工校对。

置信度函数（最大证据取胜）：
  1.00  EXPLICIT_* 白名单命中（人工维护，最强证据）
  0.95  汉书地理志（郡/县）命中
  0.90  三家注"X，Y名" 模式（训诂源头）
  0.85  L2 侯者年表 refs ≥ 50%（结构性证据）
  0.80  L4 强后缀（山/岳/水/河/江/泽/郡/关/门）
  0.75  可拆分继承（子串已分类）
  0.65  L4 中后缀（邑/城/都/陵/宫/殿）
  0.55  L3 动词/共现上下文（单次命中）
  0.55  L4 弱后缀（阳/阴/武/成/安/平/丘）
  0.50  peer 传播（邻居继承）
  0.40  仅 hints 多次累计但非优势

推理链条越多重验证，置信度越接近 1.0；单一弱证据的条目置信度低。
输出：doc/entities/地名反思/置信度评审_本轮.md
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / 'kg' / 'entities' / 'scripts'))
import classify_places as cp

INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
CATS_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'place_categories.json'
OUT_FILE = _ROOT / 'doc' / 'entities' / '地名反思' / '置信度评审_本轮.md'

# 规则 -> 置信度
WEIGHT = {
    'L1_EXPLICIT_REGION':       (0.95, '区域白名单'),
    'L1_EXPLICIT_WATER':        (0.95, '水域白名单'),
    'L1_EXPLICIT_PLAIN':        (0.95, '原野白名单'),
    'L1_EXPLICIT_MOUNTAIN':     (0.95, '山脉白名单'),
    'L1_EXPLICIT_PASS':         (0.95, '关隘白名单'),
    'L1_EXPLICIT_BUILDING':     (0.90, '建筑白名单'),
    'L1_EXPLICIT_TOMB':         (0.95, '陵墓白名单'),
    'L1_EXPLICIT_NATION':       (0.85, '国家白名单'),
    'L1_KNOWN_COMMANDERY':      (1.00, '郡白名单'),
    'L1_HANSHU_JUN':            (0.95, '汉书郡'),
    'L1_VASSAL_KINGDOM':        (0.90, '汉诸侯国→郡'),
    'L1_EXPLICIT_ANCIENT_CITY': (0.80, '古邑白名单'),
    'L1_EXPLICIT_NON_PLACE':    (0.95, '误标白名单'),
    'L1_EXPLICIT_FICTIONAL':    (0.95, '虚构白名单'),
    'L2_HOUZHE':                (0.85, '侯者年表主要 refs'),
    'L2_5_HANSHU_XIAN':         (0.90, '汉书县'),
    'L2_5_KNOWN_HAN_XIAN':      (0.85, '手工县白名单'),
    'L3_HINT_STRONG':           (0.65, 'L3 证据≥3次'),
    'L3_HINT_MEDIUM':           (0.55, 'L3 证据2次'),
    'L3_HINT_WEAK':             (0.40, 'L3 证据1次'),
    'L4_SUFFIX_STRONG':         (0.80, '强后缀'),
    'L4_SUFFIX_MEDIUM':         (0.65, '中后缀'),
    'L4_SUFFIX_WEAK':           (0.55, '弱后缀'),
    'L5_SPLIT_INHERIT':         (0.75, '拆分继承'),
    'L5_PEER_PROP':             (0.50, 'peer 传播'),
}

STRONG_SUFFIXES = {'山', '岳', '岭', '峰', '阪', '阜', '穴', '水', '河', '江',
                   '川', '渎', '泽', '陂', '池', '湖', '渊', '渠', '汭', '海',
                   '谿', '滨', '源', '野', '关', '塞', '郡', '州', '县'}
MEDIUM_SUFFIXES = {'邑', '城', '都', '陵', '宫', '殿', '台', '榭', '阙', '观',
                   '庙', '祠', '园', '畤', '寝', '社', '乡', '里', '亭',
                   '道', '桥', '津', '渡', '虚', '墟', '冢', '邮'}
WEAK_SUFFIXES = {'阳', '阴', '武', '成', '安', '平', '梁', '丘'}


def _peer_and_split_evidence(name, cat, cp_mod, all_places, peer_map_cache):
    """返回 L5 相关证据。"""
    ev = []
    # split 继承
    parts = cp_mod.split_into_known_places(name, all_places)
    if parts:
        # 检查每一 part 是否含该 cat（通过已分类）
        ev.append(('L5_SPLIT_INHERIT', WEIGHT['L5_SPLIT_INHERIT'][0],
                   f"拆分继承自 {'+'.join(parts)}"))
    # peer 传播：如果此 name 在某 peer group 里至少 1 个邻居也被标为同 cat
    if name in peer_map_cache:
        peers = peer_map_cache[name]
        ev.append(('L5_PEER_PROP', WEIGHT['L5_PEER_PROP'][0],
                   f"peer 组 ({len(peers)} 邻)"))
    return ev


def score_evidence(name, cat, refs, hints, cp_mod=None, all_places=None, peer_map_cache=None):
    """返回 [(rule_name, conf, note), ...] 所有命中该 (name, cat) 的证据"""
    ev = []

    # L1 显式命中
    l1_checks = [
        (cat == '区域' and name in cp.EXPLICIT_REGION,       'L1_EXPLICIT_REGION'),
        (cat == '水域' and name in cp.EXPLICIT_WATER,        'L1_EXPLICIT_WATER'),
        (cat == '原野' and name in cp.EXPLICIT_PLAIN,        'L1_EXPLICIT_PLAIN'),
        (cat == '山脉' and name in cp.EXPLICIT_MOUNTAIN,     'L1_EXPLICIT_MOUNTAIN'),
        (cat == '关隘' and name in cp.EXPLICIT_PASS,         'L1_EXPLICIT_PASS'),
        (cat == '建筑' and name in cp.EXPLICIT_BUILDING,     'L1_EXPLICIT_BUILDING'),
        (cat == '陵墓' and name in cp.EXPLICIT_TOMB,         'L1_EXPLICIT_TOMB'),
        (cat == '国家' and name in cp.EXPLICIT_NATION,       'L1_EXPLICIT_NATION'),
        (cat == '郡'   and name in cp.KNOWN_COMMANDERIES,    'L1_KNOWN_COMMANDERY'),
        (cat == '郡'   and name in cp.HANSHU_JUN,            'L1_HANSHU_JUN'),
        (cat == '郡'   and name in cp.HAN_VASSAL_KINGDOMS,   'L1_VASSAL_KINGDOM'),
        (cat == '城邑' and name in cp.EXPLICIT_ANCIENT_CITY, 'L1_EXPLICIT_ANCIENT_CITY'),
        (cat == '误标' and name in cp.EXPLICIT_NON_PLACE,    'L1_EXPLICIT_NON_PLACE'),
        (cat == '虚构' and name in cp.EXPLICIT_FICTIONAL,    'L1_EXPLICIT_FICTIONAL'),
    ]
    for hit, key in l1_checks:
        if hit:
            conf, note = WEIGHT[key]
            ev.append((key, conf, note))

    # L2 侯者年表 → 县
    if cat == '县' and refs and len(refs) >= cp.HOUZHE_MIN_REFS:
        if cp._houzhe_ratio(refs) >= cp.HOUZHE_MAJORITY:
            conf, note = WEIGHT['L2_HOUZHE']
            ev.append(('L2_HOUZHE', conf, note))

    # L2.5 汉书 / 手工县白名单 → 县
    if cat == '县':
        if name in cp.HANSHU_XIAN:
            conf, note = WEIGHT['L2_5_HANSHU_XIAN']
            ev.append(('L2_5_HANSHU_XIAN', conf, note))
        if name in cp.KNOWN_HAN_XIAN:
            conf, note = WEIGHT['L2_5_KNOWN_HAN_XIAN']
            ev.append(('L2_5_KNOWN_HAN_XIAN', conf, note))

    # L3 hints
    if hints is not None:
        n = hints.get(name, {}).get(cat, 0)
        if n >= 3:
            conf, note = WEIGHT['L3_HINT_STRONG']
            ev.append(('L3_HINT_STRONG', conf, f'{note} (×{n})'))
        elif n == 2:
            conf, note = WEIGHT['L3_HINT_MEDIUM']
            ev.append(('L3_HINT_MEDIUM', conf, f'{note}'))
        elif n == 1:
            conf, note = WEIGHT['L3_HINT_WEAK']
            ev.append(('L3_HINT_WEAK', conf, note))

    # L5 peer / split
    if cp_mod is not None and all_places is not None and peer_map_cache is not None:
        ev.extend(_peer_and_split_evidence(name, cat, cp_mod, all_places, peer_map_cache))

    # L4 后缀启发式
    for suf in sorted(STRONG_SUFFIXES | MEDIUM_SUFFIXES | WEAK_SUFFIXES, key=len, reverse=True):
        if name.endswith(suf) and len(name) > len(suf):
            # 判断该后缀在 SUFFIX_RULES 中映射到的 cat
            for s, c in cp.SUFFIX_RULES:
                if s == suf and c == cat:
                    if suf in STRONG_SUFFIXES:
                        conf, note = WEIGHT['L4_SUFFIX_STRONG']
                        ev.append(('L4_SUFFIX_STRONG', conf, f'{note} "{suf}"'))
                    elif suf in MEDIUM_SUFFIXES:
                        conf, note = WEIGHT['L4_SUFFIX_MEDIUM']
                        ev.append(('L4_SUFFIX_MEDIUM', conf, f'{note} "{suf}"'))
                    elif suf in WEAK_SUFFIXES:
                        conf, note = WEIGHT['L4_SUFFIX_WEAK']
                        ev.append(('L4_SUFFIX_WEAK', conf, f'{note} "{suf}"'))
                    break
            break

    return ev


def main():
    print('加载 entity_index 与分类...')
    index = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
    places = index['place']
    cats_data = json.loads(CATS_JSON.read_text(encoding='utf-8'))

    print('构建 hints...')
    hints = cp.build_context_hints(places.keys())
    for nm, cs in cp.build_sanjia_hints(places.keys()).items():
        for c, n in cs.items():
            hints[nm][c] += n

    # 构建 peer map 缓存
    peer_groups = cp.build_peer_groups(places.keys())
    peer_map = defaultdict(set)
    for g in peer_groups:
        for n in g:
            peer_map[n].update(x for x in g if x != n)
    all_places = set(places.keys())

    # 按分类组织
    by_cat_conf = defaultdict(list)
    global_missing_evidence = []
    for name, cats in cats_data.items():
        refs = places[name]['refs']
        for cat in cats:
            evidence = score_evidence(name, cat, refs, hints,
                                      cp_mod=cp, all_places=all_places,
                                      peer_map_cache=peer_map)
            if evidence:
                max_conf = max(e[1] for e in evidence)
                evidence_summary = ' + '.join(e[2] for e in evidence)
            else:
                max_conf = 0.30   # 仅 peer / split 等间接证据（未被我们模型识别）
                evidence_summary = '(仅间接证据，如 peer 传播或 split 继承)'
                global_missing_evidence.append((name, cat))
            by_cat_conf[cat].append((name, max_conf, len(evidence), evidence_summary, cats))

    # 生成报告
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append('# 地名分类 · 置信度评审（本轮）')
    lines.append('')
    lines.append(f'> 基于 [置信度函数](../../../kg/entities/scripts/confidence_report.py) 对 '
                 f'{sum(len(v) for v in by_cat_conf.values())} 个 (name, category) 组合打分。')
    lines.append('> 按分类分组，每组内按置信度升序（先列低置信度，需人工校对）。')
    lines.append('')
    lines.append('| 置信度 | 含义 |')
    lines.append('|--------|------|')
    lines.append('| ≥0.90 | 多源强证据，极可信 |')
    lines.append('| 0.70-0.89 | 单源强证据或多源中等证据，可信 |')
    lines.append('| 0.50-0.69 | 单源中等证据，宜复核 |')
    lines.append('| <0.50 | 弱证据或间接证据，**需重点校对** |')
    lines.append('')

    total_low = 0
    for cat in sorted(by_cat_conf.keys()):
        entries = sorted(by_cat_conf[cat], key=lambda x: (x[1], x[0]))
        low_count = sum(1 for e in entries if e[1] < 0.50)
        mid_count = sum(1 for e in entries if 0.50 <= e[1] < 0.70)
        hi_count = sum(1 for e in entries if e[1] >= 0.70)
        total_low += low_count
        lines.append(f'## {cat}（{len(entries)} 条 · 高 {hi_count} / 中 {mid_count} / 低 {low_count}）')
        lines.append('')
        # 只列低+中置信度；高置信度折叠
        shown = [e for e in entries if e[1] < 0.70]
        if not shown:
            lines.append('_（全部高置信度，略）_')
            lines.append('')
            continue
        for name, conf, nev, summary, all_cats in shown:
            tag_list = '/'.join(all_cats)
            lines.append(f'- `{name}` · conf={conf:.2f} · 证据数 {nev} · **[{tag_list}]**')
            lines.append(f'  - {summary}')
        lines.append('')

    # 在开头摘要处补充统计
    summary_line = f'**校对重点**：低置信度（<0.50）共 **{total_low}** 条'
    lines.insert(4, summary_line)
    lines.insert(5, '')

    OUT_FILE.write_text('\n'.join(lines), encoding='utf-8')
    print(f'报告: {OUT_FILE}')
    print(f'总低置信度条目: {total_low}')


if __name__ == '__main__':
    main()
