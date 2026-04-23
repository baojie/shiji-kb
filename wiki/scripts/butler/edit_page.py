#!/usr/bin/env python3
"""
edit_page.py — 编辑 wiki 页面并自动记录修订历史。

用法:
    python3 wiki/scripts/butler/edit_page.py <slug> <content_file> \
        [--summary "butler/trail: ..."] \
        [--author butler]

    # 内容也可从 stdin 读取:
    echo "# 新内容" | python3 wiki/scripts/butler/edit_page.py <slug> - \
        --summary "butler/trail: ..."

规则:
    - 若页面不存在则退出（用 add_page.py）
    - 覆写 wiki/public/pages/<slug>.md
    - 自动调用 record_revision.py 记录本次修订
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
    ap.add_argument('content_file', help='内容文件路径，或 - 表示 stdin')
    ap.add_argument('--summary', default='', help='修订说明')
    ap.add_argument('--author', default='butler')
    args = ap.parse_args()

    target = PAGES / f'{args.slug}.md'
    if not target.exists():
        print(f'✗ 页面不存在: {target}（请用 add_page.py）', file=sys.stderr)
        sys.exit(1)

    if args.content_file == '-':
        content = sys.stdin.read()
    else:
        src = Path(args.content_file)
        if not src.exists():
            print(f'✗ 内容文件不存在: {src}', file=sys.stderr)
            sys.exit(1)
        content = src.read_text(encoding='utf-8')

    target.write_text(content, encoding='utf-8')
    print(f'✓ 更新 {target}')

    summary = args.summary or f'butler/trail: {args.slug}'
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


if __name__ == '__main__':
    main()
