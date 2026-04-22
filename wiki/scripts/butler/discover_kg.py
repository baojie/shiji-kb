#!/usr/bin/env python3
"""
discover_kg.py — 扫 wiki/data/semantic.json 找 kg 里高频但 wiki 无页的实体.

输出: markdown (默认) 或 JSON, 可直接 append 到 logs/wiki_butler/queue.md.

用法:
    python wiki/scripts/butler/discover_kg.py
    python wiki/scripts/butler/discover_kg.py --top 50 --output-format json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEMANTIC = ROOT / 'wiki/data/semantic.json'
PAGES_DIR = ROOT / 'wiki/public/pages'

# W5 反思 2026-04-22 · 提案 2 引入:
# KG 层 canonical 质量过滤, 跳过明显错误的 canonical, 避免 butler 把噪音当候选.
# 这些应在 KG 侧修, 不在 butler 范围.

# 上古传说帝王的单字名若被包进"姓氏+单字" canonical, 多半是消歧错
LEGEND_SINGLE_CHARS = set('舜尧禹汤启契稷')
# 已知重复 canonical (应合并到左侧) 的前缀/后缀形式
KNOWN_REDUNDANT_PATTERNS = [
    r'^汉孝.+帝$',      # 汉孝文帝 / 汉孝景帝 = 汉文帝 / 汉景帝
    r'^秦[张李赵白王吕].+$',  # 秦张仪 / 秦白起 / 秦王翦 / 秦吕不韦
    r'^张楚.+王$',      # 张楚楚隐王 类
    r'^西周.+(王|公)$', # 西周幽王 = 周幽王
    r'^纵横家.+$',      # 纵横家苏秦 = 苏秦
    r'^燕荆.+$',        # 燕荆轲 = 荆轲 (邦国+人名)
    r'^西魏.+$',        # 西魏王 等冗余
    r'^东周.+(王|公)$', # 东周平王 = 周平王
    r'^郑子.+$',        # 郑子产 = 子产 (邦国+字)
    r'^项籍$',          # = 项羽
    r'^楚屈.+$',        # 楚屈原 = 屈原
    r'^匈奴.+单于$',    # 匈奴冒顿单于 = 冒顿单于
    r'.*（.*）.*',      # 括号噪音 如 楚怀王（义帝）
]
# 职位/头衔类 canonical (非人名)
TITLE_CANONICALS = {'雍王', '梁王', '赵王', '齐王', '楚王', '汉王', '韩王',
                    '燕王', '魏王', '吴王', '秦王', '陈王'}


def is_bad_canonical(entity):
    """返回 (is_bad, reason) 或 (False, None)."""
    import re
    c = entity['id']
    aliases = entity.get('aliases', [])

    if c in TITLE_CANONICALS:
        return True, 'title-not-person'
    for pat in KNOWN_REDUNDANT_PATTERNS:
        if re.match(pat, c):
            return True, f'redundant-form:{pat}'
    # aliases 里只有"单字传说帝王"且 canonical 含姓氏 (如 刘舜/舜)
    if (len(aliases) == 1 and aliases[0] in LEGEND_SINGLE_CHARS
            and len(c) > 1 and c[-1] == aliases[0]):
        return True, f'legend-char-merged:{aliases[0]}'
    return False, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=30,
                    help='扫描 top-N by total_refs (默认 30)')
    ap.add_argument('--output-format', choices=['md', 'json'], default='md')
    ap.add_argument('--min-refs', type=int, default=30,
                    help='最低 refs 阈值 (默认 30)')
    args = ap.parse_args()

    if not SEMANTIC.exists():
        print(f'✗ {SEMANTIC} 不存在, 先跑:', file=sys.stderr)
        print('    node wiki/server/api/seed.js', file=sys.stderr)
        return 1

    data = json.loads(SEMANTIC.read_text(encoding='utf-8'))
    entities = data.get('entities', {})
    existing = {p.stem for p in PAGES_DIR.glob('*.md')}

    top = sorted(
        (e for e in entities.values() if e.get('total_refs', 0) >= args.min_refs),
        key=lambda e: -e.get('total_refs', 0),
    )[:args.top]

    missing, skipped = [], []
    for e in top:
        if e['id'] in existing:
            continue
        bad, reason = is_bad_canonical(e)
        if bad:
            skipped.append((e['id'], reason))
            continue
        missing.append(e)

    today = date.today().isoformat()

    if args.output_format == 'json':
        out = []
        for e in missing:
            priority = 'P0' if e['total_refs'] >= 100 else 'P1'
            out.append({
                'target': f'wiki/public/pages/{e["id"]}.md',
                'action': 'create-stub',
                'source': 'kg/entities/data/entity_aliases.json',
                'mode': 'explore',
                'priority': priority,
                'rationale': f'kg top-{args.top} 缺 wiki 页 (refs={e["total_refs"]}/章={e["total_chapters"]})',
                'discovered': today,
            })
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print('## 来自 discover_kg (kg top-N 缺 wiki 页)\n')
        for e in missing:
            p = 'P0' if e['total_refs'] >= 100 else 'P1'
            print(f'- [ ] {e["id"]}: `create-stub` '
                  f'(refs={e["total_refs"]}/章={e["total_chapters"]}) '
                  f'[源:A] [{p}] [{today}]')

    print(f'\n[discover_kg] 扫 top-{args.top}, 发现 {len(missing)} 个缺失, '
          f'跳过 {len(skipped)} 个 bad canonical.', file=sys.stderr)
    if skipped:
        print('[discover_kg] 跳过的 canonical (需 KG 侧修):', file=sys.stderr)
        for name, reason in skipped:
            print(f'  - {name} [{reason}]', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
