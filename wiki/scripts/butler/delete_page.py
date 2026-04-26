#!/usr/bin/env python3
"""
delete_page.py — "删除" wiki 页面：保留文件，改为 deleted stub 或 REDIRECT。

用法:
    # 默认：改为 deleted stub（type: deleted，内容清空）
    python3 wiki/scripts/butler/delete_page.py <slug> \
        [--summary "butler/delete: ..."] \
        [--author butler]

    # 合并后保留入口：改为 REDIRECT 页
    python3 wiki/scripts/butler/delete_page.py <slug> \
        --redirect-to <target_slug> \
        [--summary "butler/delete: 合并至 target"] \
        [--author butler]

规则:
    - 永远不物理删除文件（unlink 已被移除）
    - 先调用 record_revision.py 存档当前版本快照
    - 无 --redirect-to：写入 type:deleted stub，record_revision 使用 --action delete
    - 有 --redirect-to：写入 type:redirect 页，record_revision 使用默认 edit action
    - 修订历史目录 wiki/public/history/<slug>.json 始终保留
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES = ROOT / 'wiki' / 'public' / 'pages'


def _redirect_content(slug: str, target: str) -> str:
    return (
        f'---\n'
        f'id: {slug}\n'
        f'type: redirect\n'
        f'target: {target}\n'
        f'quality: standard\n'
        f'---\n'
        f'#REDIRECT [[{target}]]\n'
    )


def _deleted_content(slug: str) -> str:
    return (
        f'---\n'
        f'id: {slug}\n'
        f'type: deleted\n'
        f'---\n'
    )


def _record(slug: str, summary: str, author: str, action: str = 'edit') -> bool:
    cmd = [
        sys.executable,
        str(ROOT / 'wiki' / 'scripts' / 'butler' / 'record_revision.py'),
        slug,
        '--summary', summary,
        '--author', author,
        '--action', action,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout, end='')
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
    return r.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', help='页面 slug（不含 .md）')
    ap.add_argument('--redirect-to', metavar='TARGET', default=None,
                    help='若提供：改为 REDIRECT 页而非 deleted stub')
    ap.add_argument('--summary', default='', help='删除/重定向原因说明')
    ap.add_argument('--author', default='butler')
    args = ap.parse_args()

    target_file = PAGES / f'{args.slug}.md'
    if not target_file.exists():
        print(f'✗ 页面不存在: {target_file}', file=sys.stderr)
        sys.exit(1)

    # 先存档当前版本
    archive_summary = args.summary or f'butler/delete: {args.slug} 存档'
    record_action = 'edit' if args.redirect_to else 'delete'
    if not _record(args.slug, archive_summary, args.author, action=record_action):
        sys.exit(1)

    # 写入新内容（redirect 或 deleted stub）
    if args.redirect_to:
        new_content = _redirect_content(args.slug, args.redirect_to)
        target_file.write_text(new_content, encoding='utf-8')
        print(f'✓ {args.slug} → REDIRECT [[{args.redirect_to}]]（文件保留）')
    else:
        new_content = _deleted_content(args.slug)
        target_file.write_text(new_content, encoding='utf-8')
        print(f'✓ {args.slug} → deleted stub（文件保留，内容已清空）')


if __name__ == '__main__':
    main()
