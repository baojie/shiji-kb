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

    # 仅允许在去重/纠错操作时才可编辑史记引文节（需显式声明）:
    python3 wiki/scripts/butler/edit_page.py <slug> <file> \
        --allow-citation-edit --summary "fix-citation: ..."

规则:
    - 若页面不存在则退出（用 add_page.py）
    - 覆写 wiki/public/pages/<slug>.md
    - 自动调用 record_revision.py 记录本次修订

铁律（不可绕过）:
    - 若旧版有 ## 史记引文 节，新版必须保留该节
    - 唯一例外：--allow-citation-edit 标志（仅限去重/纠错操作使用）
    - 若旧版有 frontmatter（--- 开头），新版没有 → 拒绝写入（退出码 3）
    - 若新版 size < 旧版 size × 0.6 → 拒绝写入（退出码 4）
    - 上述两条的例外：--allow-shrink 标志（仅限明确需要缩减内容的操作）
    - 违反时脚本以对应退出码终止，不写入任何内容
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES = ROOT / 'wiki' / 'public' / 'pages'

CITATION_SECTION = '## 史记引文'


def has_citation_section(text: str) -> bool:
    return any(line.strip() == CITATION_SECTION for line in text.splitlines())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', help='页面 slug（不含 .md）')
    ap.add_argument('content_file', help='内容文件路径，或 - 表示 stdin')
    ap.add_argument('--summary', default='', help='修订说明')
    ap.add_argument('--author', default='butler')
    ap.add_argument(
        '--allow-citation-edit',
        action='store_true',
        help='允许修改/删除史记引文节（仅限去重 H1 和纠错 fix-citation/H10 操作）',
    )
    ap.add_argument(
        '--allow-shrink',
        action='store_true',
        help='允许 frontmatter 丢失或内容大幅缩减（仅限 redirect/merge/disambiguation 操作）',
    )
    args = ap.parse_args()

    target = PAGES / f'{args.slug}.md'
    if not target.exists():
        print(f'✗ 页面不存在: {target}（请用 add_page.py）', file=sys.stderr)
        sys.exit(1)

    old_content = target.read_text(encoding='utf-8')

    if args.content_file == '-':
        new_content = sys.stdin.read()
    else:
        src = Path(args.content_file)
        if not src.exists():
            print(f'✗ 内容文件不存在: {src}', file=sys.stderr)
            sys.exit(1)
        new_content = src.read_text(encoding='utf-8')

    # 铁律1：史记引文节不得被非授权操作删除
    if (not args.allow_citation_edit
            and has_citation_section(old_content)
            and not has_citation_section(new_content)):
        print(
            f'⛔ 禁止写入：{args.slug} 旧版含 "{CITATION_SECTION}" 节，'
            f'新版缺失该节。\n'
            f'   若确为去重/纠错操作，请加 --allow-citation-edit 标志。',
            file=sys.stderr,
        )
        sys.exit(2)

    # 铁律2：frontmatter 不得被非授权操作删除
    old_has_fm = old_content.lstrip().startswith('---')
    new_has_fm = new_content.lstrip().startswith('---')
    if not args.allow_shrink and old_has_fm and not new_has_fm:
        print(
            f'⛔ 禁止写入：{args.slug} 旧版含 frontmatter，新版缺失。\n'
            f'   expand/narrative 操作必须保留原 frontmatter。\n'
            f'   若确为 redirect/merge 操作，请加 --allow-shrink 标志。',
            file=sys.stderr,
        )
        sys.exit(3)

    # 铁律3：禁止内容大幅缩减（新版 < 旧版 60%）
    old_size = len(old_content.encode('utf-8'))
    new_size = len(new_content.encode('utf-8'))
    if not args.allow_shrink and old_size > 400 and new_size < old_size * 0.6:
        print(
            f'⛔ 禁止写入：{args.slug} 新版大小 {new_size}B 不足旧版 {old_size}B 的 60%。\n'
            f'   expand 操作应追加内容，不得整页替换。\n'
            f'   若确为 redirect/merge 操作，请加 --allow-shrink 标志。',
            file=sys.stderr,
        )
        sys.exit(4)

    target.write_text(new_content, encoding='utf-8')
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
