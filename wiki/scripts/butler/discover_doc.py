#!/usr/bin/env python3
"""
discover_doc.py — 扫 doc/ 下的分析报告, 找与 wiki 页对应的"引证候选".

策略:
    - doc/lifespan_inference/**/*.md: 单人生卒推断报告
      文件名 (去 .md) = 对应 wiki 人物 slug
    - 若 wiki/public/pages/<slug>.md 存在, 输出候选:
      "wiki 页应在生卒字段加脚注到此 doc"

输出: markdown 格式入 queue.md, 或 JSON 给后续 cite-doc-report 动作消费.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC_LIFESPAN = ROOT / 'doc/lifespan_inference'
PAGES_DIR = ROOT / 'wiki/public/pages'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--format', choices=['md', 'json'], default='md')
    args = ap.parse_args()

    if not DOC_LIFESPAN.exists():
        print(f'✗ {DOC_LIFESPAN} 不存在', file=sys.stderr)
        return 1

    existing = {p.stem for p in PAGES_DIR.glob('*.md')}

    # 扫所有 doc md, 文件名作 slug
    candidates = []
    for md in DOC_LIFESPAN.rglob('*.md'):
        if md.name in {'README.md'}:
            continue
        slug = md.stem
        # 过滤 wiki 无对应页
        if slug not in existing:
            continue
        # 记相对路径
        rel = md.relative_to(ROOT).as_posix()
        candidates.append({
            'slug': slug,
            'doc_path': rel,
            'reason': 'lifespan_inference',
        })

    today = date.today().isoformat()

    if args.format == 'json':
        out = [
            {
                'target': f'wiki/public/pages/{c["slug"]}.md',
                'action': 'cite-doc-report',
                'source': c['doc_path'],
                'mode': 'explore',
                'priority': 'P2',
                'rationale': f'doc 有 {c["reason"]} 报告, wiki 页可加脚注',
                'discovered': today,
            }
            for c in candidates
        ]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print('## 来自 discover_doc (wiki 页可加 doc 脚注)\n')
        for c in candidates:
            print(f'- [ ] {c["slug"]}: `cite-doc-report` '
                  f'(源: `{c["doc_path"]}`) [P2] [{today}]')

    print(f'\n[discover_doc] 发现 {len(candidates)} 页可加脚注.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
