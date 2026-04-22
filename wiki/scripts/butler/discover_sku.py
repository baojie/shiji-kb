#!/usr/bin/env python3
"""
discover_sku.py — 扫 ontology-v2 的 SKU 文件找 wiki 缺对应 topic 页的.

策略:
    只看 shiji-2026-04-05-v1/skus/ 下的 facts 和 skills (高层级 SKU).
    章节级 SKU 太细粒度, 暂不入 queue.
    从 SKU 的第一个 # heading 派生 topic slug.

输出: markdown (默认) 或 JSON.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKU_DIRS = [
    ROOT / 'kg/ontology/ontology-v2/shiji-2026-04-05-v1/skus/facts',
    ROOT / 'kg/ontology/ontology-v2/shiji-2026-04-05-v1/skus/skills',
]
PAGES_DIR = ROOT / 'wiki/public/pages'

FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
H1_RE = re.compile(r'^#\s+(.+?)\s*$', re.M)


def extract_title(md_path: Path) -> str:
    text = md_path.read_text(encoding='utf-8')
    m = FRONTMATTER_RE.match(text)
    if m:
        text = text[m.end():]
    h = H1_RE.search(text)
    if h:
        title = h.group(1)
        # 冒号后视为副标题, 只取主
        title = re.split(r'[:：——]', title, maxsplit=1)[0].strip()
        # 过滤常见装饰符号
        title = title.strip('《》')
        return title
    return md_path.stem


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-format', choices=['md', 'json'], default='md')
    args = ap.parse_args()

    existing = {p.stem for p in PAGES_DIR.glob('*.md')}

    candidates = []
    for d in SKU_DIRS:
        if not d.exists():
            continue
        for md in sorted(d.glob('*.md')):
            title = extract_title(md)
            if not title or title in existing:
                continue
            candidates.append({
                'slug': title,
                'sku_path': md.relative_to(ROOT).as_posix(),
                'sku_id': md.stem,
            })

    today = date.today().isoformat()

    if args.output_format == 'json':
        out = []
        for c in candidates:
            out.append({
                'target': f'wiki/public/pages/{c["slug"]}.md',
                'action': 'import-sku-as-topic',
                'source': c['sku_path'],
                'mode': 'explore',
                'priority': 'P1',
                'rationale': f'SKU {c["sku_id"]} 无对应 topic 页',
                'discovered': today,
            })
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print('## 来自 discover_sku (ontology-v2 SKU 缺 topic 页)\n')
        for c in candidates:
            print(f'- [ ] {c["slug"]}: `import-sku-as-topic` '
                  f'(源: `{c["sku_path"]}`) [P1] [{today}]')

    print(f'\n[discover_sku] 扫 {len(SKU_DIRS)} 目录, '
          f'发现 {len(candidates)} 个缺 topic.',
          file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
