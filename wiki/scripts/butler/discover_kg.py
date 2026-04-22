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

    missing = [e for e in top if e['id'] not in existing]

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

    print(f'\n[discover_kg] 扫 top-{args.top}, 发现 {len(missing)} 个缺失.',
          file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
