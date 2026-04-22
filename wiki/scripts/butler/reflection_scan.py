#!/usr/bin/env python3
"""
reflection_scan.py — W5 反思时调用, 扫结构化列表找问题模式.

用法:
    python3 wiki/scripts/butler/reflection_scan.py
    python3 wiki/scripts/butler/reflection_scan.py --aspect alias|dup|notl|quality

输出: markdown 片段, 给 reflection md 引用.

按 W5 v6 提案 17 设计:
    - alias_conflicts.json 里最严重的冲突 (同 surface 指向 >= 3 pages 的)
    - duplicate_candidates.json 里已 alias 交集的 canonical 对 (忽略 '武子/某公' 谥号噪音)
    - 无 timeline 且 quality < 15 的页
    - quality 最低 10 页
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ALIAS_CONFL = ROOT / 'wiki/data/alias_conflicts.json'
DUP_CAND = ROOT / 'wiki/data/duplicate_candidates.json'
PAGES_JSON = ROOT / 'wiki/public/pages.json'
PAGES_DIR = ROOT / 'wiki/public/pages'

# 谥号/头衔后缀 — duplicate_candidates 里大多共享这些, 应过滤
WEAK_SUFFIXES = ('武子', '昭公', '襄公', '文公', '武公', '惠公', '宣公',
                 '庄公', '桓公', '景公', '哀公', '成公', '厉公', '平公',
                 '灵公', '孝公', '穆公', '桓', '昭', '襄', '惠', '武', '文',
                 '王', '帝', '公', '侯', '君', '子')


def scan_alias_conflicts():
    if not ALIAS_CONFL.exists():
        return '### Alias 冲突: 文件不存在\n'
    d = json.loads(ALIAS_CONFL.read_text(encoding='utf-8'))
    confs = d.get('conflicts', [])
    # 同 surface 指向多少 page
    by_alias = Counter()
    surface_to_pages = {}
    for c in confs:
        by_alias[c['alias']] += 1
        surface_to_pages.setdefault(c['alias'], set()).update([c['kept'], c['ignored']])
    # Top 最严重的
    top = by_alias.most_common(5)
    out = ['### Alias 严重冲突 Top 5 (同 surface 指向多 page)\n']
    for alias, cnt in top:
        pages = sorted(surface_to_pages[alias])
        out.append(f'- `{alias}` → {pages} ({cnt} 次冲突)')
    return '\n'.join(out)


def scan_duplicates():
    if not DUP_CAND.exists():
        return '### 重复 canonical: 文件不存在\n'
    d = json.loads(DUP_CAND.read_text(encoding='utf-8'))
    cands = d.get('candidates', [])
    # 过滤谥号类噪音
    filtered = []
    for c in cands:
        if c['alias'].endswith(WEAK_SUFFIXES):
            continue
        if c['alias'] in WEAK_SUFFIXES:
            continue
        filtered.append(c)
    out = [f'### 重复 canonical Top 10 (过滤谥号噪音, 剩 {len(filtered)} 对)\n']
    for c in filtered[:10]:
        out.append(f"- `{c['alias']}` 同时是 `{c['canonicals'][0]}` 和 `{c['canonicals'][1]}` 的别名")
    return '\n'.join(out)


def scan_no_timeline():
    d = json.loads(PAGES_JSON.read_text(encoding='utf-8'))
    low = []
    for pid, p in d['pages'].items():
        q = p.get('quality_score', 0)
        if q >= 15:
            continue
        md = PAGES_DIR / f'{pid}.md'
        if not md.exists():
            continue
        content = md.read_text(encoding='utf-8')
        if '## 生平大事' in content:
            continue
        low.append((pid, q, p.get('total_refs', 0)))
    low.sort(key=lambda x: x[1])
    out = [f'### 无 timeline 且 quality < 15 的页 (共 {len(low)})\n']
    for pid, q, refs in low:
        out.append(f'- `{pid}` (q={q}, refs={refs})')
    return '\n'.join(out)


def scan_quality_bottom():
    d = json.loads(PAGES_JSON.read_text(encoding='utf-8'))
    sorted_p = sorted(d['pages'].items(), key=lambda x: x[1].get('quality_score', 0))[:10]
    out = ['### Quality 最低 10 页\n']
    for pid, p in sorted_p:
        q = p.get('quality_score', 0)
        parts = p.get('_score_parts', {})
        out.append(f"- `{pid}` q={q}  " +
                   f"(base={parts.get('base_refs',0)} " +
                   f"tags={parts.get('tags',0)} " +
                   f"rev={parts.get('revs',0)} " +
                   f"narrative={parts.get('narrative',0)})")
    return '\n'.join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--aspect', choices=['alias', 'dup', 'notl', 'quality', 'all'],
                    default='all')
    args = ap.parse_args()

    sections = []
    if args.aspect in ('alias', 'all'): sections.append(scan_alias_conflicts())
    if args.aspect in ('dup', 'all'): sections.append(scan_duplicates())
    if args.aspect in ('notl', 'all'): sections.append(scan_no_timeline())
    if args.aspect in ('quality', 'all'): sections.append(scan_quality_bottom())

    print('\n\n'.join(sections))
    return 0


if __name__ == '__main__':
    sys.exit(main())
