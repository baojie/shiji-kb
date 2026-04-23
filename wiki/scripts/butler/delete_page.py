#!/usr/bin/env python3
"""
delete_page.py — 删除 wiki 页面，保留修订历史快照并记录删除事件。

用法:
    python3 wiki/scripts/butler/delete_page.py <slug> \
        [--summary "butler/delete: ..."] \
        [--author butler]

规则:
    - 在删除前先调用 record_revision.py 保存最终版本快照
    - 然后删除 wiki/public/pages/<slug>.md
    - 修订历史目录 wiki/public/history/<slug>/ 保留不删（可查阅）
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES = ROOT / 'wiki' / 'public' / 'pages'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', help='页面 slug（不含 .md）')
    ap.add_argument('--summary', default='', help='删除原因说明')
    ap.add_argument('--author', default='butler')
    args = ap.parse_args()

    target = PAGES / f'{args.slug}.md'
    if not target.exists():
        print(f'✗ 页面不存在: {target}', file=sys.stderr)
        sys.exit(1)

    # 删除前先存档最终版本
    summary = args.summary or f'butler/delete: {args.slug} 删除前存档'
    rec = subprocess.run(
        [sys.executable,
         str(ROOT / 'wiki' / 'scripts' / 'butler' / 'record_revision.py'),
         args.slug,
         '--summary', summary,
         '--author', args.author],
        capture_output=True, text=True
    )
    print(rec.stdout, end='')
    if rec.returncode != 0:
        print(rec.stderr, file=sys.stderr)
        sys.exit(rec.returncode)

    target.unlink()
    print(f'✓ 已删除 {target}（修订历史保留）')


if __name__ == '__main__':
    main()
