#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计 classify_officials.py 中的 EXPLICIT_* 白名单，找出：
1. 不在 entity_index.json 的条目（死词）
2. 一词出现在多个 EXPLICIT_* 的（冲突，可能需合并为多标签）
3. 没被任何 chapter_md 引用的条目（孤立词）

用法：python3 audit_official_whitelists.py
输出：报告到 doc/entities/官职反思/第六轮_白名单审计.md
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import classify_officials as co

INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
OUT = _ROOT / 'doc' / 'entities' / '官职反思' / '第六轮_白名单审计.md'


def main():
    idx = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
    officials = idx.get('official', {})
    official_names = set(officials.keys())

    # 收集所有 EXPLICIT_* 白名单
    whitelists = {
        'EXPLICIT_SANGONG':        (co.EXPLICIT_SANGONG, '三公'),
        'EXPLICIT_JIUQING':        (co.EXPLICIT_JIUQING, '九卿'),
        'EXPLICIT_LIQING':         (co.EXPLICIT_LIQING, '列卿'),
        'EXPLICIT_MILITARY':       (co.EXPLICIT_MILITARY, '军职'),
        'EXPLICIT_JUE':            (co.EXPLICIT_JUE, '爵位'),
        'EXPLICIT_PALACE':         (co.EXPLICIT_PALACE, '宫廷近侍'),
        'EXPLICIT_WENXUE':         (co.EXPLICIT_WENXUE, '文学顾问'),
        'EXPLICIT_SHIFU':          (co.EXPLICIT_SHIFU, '宗师宾傅'),
        'EXPLICIT_ANCIENT':        (co.EXPLICIT_ANCIENT, '上古官'),
        'EXPLICIT_FOREIGN':        (co.EXPLICIT_FOREIGN, '外邦职'),
        'EXPLICIT_JIACHEN':        (co.EXPLICIT_JIACHEN, '家臣'),
        'EXPLICIT_GENERIC':        (co.EXPLICIT_GENERIC, '泛称'),
        'EXPLICIT_JUNLI_VASSAL':   (co.EXPLICIT_JUNLI_VASSAL, '郡国长吏'),
        'EXPLICIT_JUNLI_EXTRA':    (co.EXPLICIT_JUNLI_EXTRA, '郡国长吏'),
        'EXPLICIT_XIANLI':         (co.EXPLICIT_XIANLI, '县乡吏'),
        'EXPLICIT_NEED_SPLIT':     (co.EXPLICIT_NEED_SPLIT, '待拆分'),
        'EXPLICIT_PERSON_MIS':     (co.EXPLICIT_PERSON_MIS, '人名误标'),
        'EXPLICIT_IDENTITY_MIS':   (co.EXPLICIT_IDENTITY_MIS, '身份误标'),
        'EXPLICIT_SHIHAO_MIS':     (co.EXPLICIT_SHIHAO_MIS, '谥号误标'),
        'EXPLICIT_MIS':            (co.EXPLICIT_MIS, '误标'),
    }

    lines = ['# 白名单审计报告（第六轮）', '']
    lines.append(f'共 {sum(len(s) for s, _ in whitelists.values())} 项白名单条目。')
    lines.append('')

    # 1. 死词（不在 entity_index）
    lines.append('## 1. 死词（白名单有，但 entity_index 没有）')
    lines.append('')
    lines.append('这些条目在 `〖;X〗` 标注中从未出现。可能的原因：')
    lines.append('- 未来可能出现的"预防性"条目')
    lines.append('- 拼写错误导致白名单失效')
    lines.append('- 已被源头修正清除')
    lines.append('')

    total_dead = 0
    for wl_name, (names, cat) in whitelists.items():
        dead = sorted(n for n in names if n not in official_names)
        if dead:
            total_dead += len(dead)
            lines.append(f'### {wl_name} ({cat}) — {len(dead)} 死词')
            for n in dead:
                lines.append(f'- `{n}`')
            lines.append('')

    if total_dead == 0:
        lines.append('**✓ 所有白名单项都在 entity_index.json 中有对应条目。**')
        lines.append('')
    else:
        lines.append(f'**共 {total_dead} 条死词。可考虑删除或修正拼写。**')
        lines.append('')

    # 2. 冲突（多白名单共现）
    lines.append('## 2. 白名单间冲突（同名出现在多个 EXPLICIT_*）')
    lines.append('')
    name_to_wls = defaultdict(list)
    for wl_name, (names, cat) in whitelists.items():
        for n in names:
            name_to_wls[n].append((wl_name, cat))

    conflicts = {n: wls for n, wls in name_to_wls.items() if len(wls) > 1}
    if not conflicts:
        lines.append('**✓ 无冲突。**')
    else:
        lines.append(f'共 **{len(conflicts)}** 条多白名单词（多数为合理多标签）：')
        lines.append('')
        # 区分"误标族内冲突"（预期）vs "跨族冲突"（可能误配）
        MIS_WLS = {'EXPLICIT_MIS', 'EXPLICIT_PERSON_MIS', 'EXPLICIT_IDENTITY_MIS',
                   'EXPLICIT_SHIHAO_MIS', 'EXPLICIT_NEED_SPLIT'}
        cross_conflicts = []
        within_mis = []
        for n, wls in sorted(conflicts.items()):
            wl_set = {w[0] for w in wls}
            if wl_set & MIS_WLS and not (wl_set <= MIS_WLS):
                cross_conflicts.append((n, wls))
            elif wl_set <= MIS_WLS:
                within_mis.append((n, wls))

        if cross_conflicts:
            lines.append('### 跨族冲突（误标类 vs 正常类 —— 需审查）')
            lines.append('')
            for n, wls in cross_conflicts:
                labels = ', '.join(f'{wl}({cat})' for wl, cat in wls)
                lines.append(f'- `{n}` — {labels}')
            lines.append('')

        if within_mis:
            lines.append('### 误标类内部冲突（应选一类）')
            lines.append('')
            for n, wls in within_mis:
                labels = ', '.join(f'{wl}({cat})' for wl, cat in wls)
                lines.append(f'- `{n}` — {labels}')
            lines.append('')

        other_conflicts = [(n, wls) for n, wls in sorted(conflicts.items())
                          if n not in {x[0] for x in cross_conflicts}
                          and n not in {x[0] for x in within_mis}]
        if other_conflicts:
            lines.append('### 正常多白名单（可能是合理多标签）')
            lines.append('')
            for n, wls in other_conflicts:
                labels = ', '.join(f'{wl}({cat})' for wl, cat in wls)
                lines.append(f'- `{n}` — {labels}')
            lines.append('')

    # 3. 孤立词（在 entity_index 但 count=0 或仅 1 次）
    lines.append('## 3. 低频条目（count ≤ 2 的白名单项）')
    lines.append('')
    lines.append('白名单维护成本的一半来自只出现 1-2 次的 "长尾条目"。如确认无误可不动，')
    lines.append('但若分类错误则影响不大。')
    lines.append('')

    low_freq = []
    for wl_name, (names, cat) in whitelists.items():
        for n in names:
            if n in official_names and officials[n].get('count', 0) <= 2:
                low_freq.append((officials[n]['count'], n, wl_name, cat))
    low_freq.sort()

    if low_freq:
        lines.append(f'共 **{len(low_freq)}** 条低频白名单项：')
        lines.append('')
        for cnt, n, wl, cat in low_freq[:60]:
            lines.append(f'- `{n}` (count={cnt}, 在 {wl} → {cat})')
        if len(low_freq) > 60:
            lines.append(f'- ...另有 {len(low_freq)-60} 条')
        lines.append('')

    # 4. 统计汇总
    lines.append('## 4. 统计汇总')
    lines.append('')
    lines.append(f'- 总白名单条目: {sum(len(s) for s, _ in whitelists.values())}')
    lines.append(f'- 死词: {total_dead}')
    lines.append(f'- 冲突: {len(conflicts)}')
    lines.append(f'- 低频（count ≤ 2）: {len(low_freq)}')
    lines.append('')

    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print(f'写入: {OUT}')
    print(f'死词 {total_dead}, 冲突 {len(conflicts)}, 低频 {len(low_freq)}')


if __name__ == '__main__':
    main()
