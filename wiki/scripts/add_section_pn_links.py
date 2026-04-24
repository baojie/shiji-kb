#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给 wiki 章页面的 **章节结构** 小节标题加上指向原文 PN 的链接。

处理两种行格式（在 **章节结构** 块内）：
  - **大节标题**              → - **[大节标题](url#pn-N)**
  - **大节标题**：首句...     → - **[大节标题](url#pn-N)**：首句...
  -   小节标题：首句...       → -   [小节标题](url#pn-N)：首句...

已有链接的行跳过（幂等）。

用法:
    python wiki/scripts/add_section_pn_links.py [--dry-run] [--chapter 007_项羽本纪]
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE_URL = 'https://baojie.github.io/shiji-kb/chapters'
SKIP_TITLES = {'太史公曰', '赞', '论', '索隐', '集解', '正义'}

# 与 wiki 页面中 **章节结构** 块的起止条件
STRUCT_START = re.compile(r'^\*\*章节结构\*\*')
# 下一个 ## 或空行后跟非列表行 → 离开结构块（用行状态机控制）

# 匹配 L2 行: - **Title** 或 - **Title**：...
L2_RE = re.compile(r'^(- \*\*)([^*\[]+?)(\*\*)(.*)$')
# 匹配 L3 行: -   Title：...（两空格缩进，无 **）
L3_RE = re.compile(r'^(  - )([^\[*][^：\n]*?)(：.*)$')


def make_link(title: str, chapter_id: str, pn: str) -> str:
    url = f'{BASE_URL}/{chapter_id}.html#pn-{pn}'
    return f'[{title}]({url})'


def process_page(md_path: Path, index: dict, dry_run: bool) -> int:
    chapter_id = md_path.stem
    pn_map = index.get(chapter_id)
    if pn_map is None:
        return 0

    text = md_path.read_text(encoding='utf-8')
    lines = text.split('\n')
    new_lines = []
    in_struct = False
    changed = 0

    for line in lines:
        # 检测进入 **章节结构** 块
        if STRUCT_START.match(line):
            in_struct = True
            new_lines.append(line)
            continue

        # 离开结构块：遇到下一个 ## 标题
        if in_struct and line.startswith('## '):
            in_struct = False

        if not in_struct:
            new_lines.append(line)
            continue

        # --- 在结构块内 ---

        # L2: - **Title** 或 - **Title**：text
        m2 = L2_RE.match(line)
        if m2:
            prefix, title, suffix_stars, rest = m2.groups()
            title = title.strip()
            if title in SKIP_TITLES:
                new_lines.append(line)
                continue
            pn = pn_map.get(title)
            if pn:
                link = make_link(title, chapter_id, pn)
                new_line = f'- **{link}**{rest}'
                if new_line != line:
                    changed += 1
                    line = new_line

        else:
            # L3: "  - Title：text"（两空格）
            m3 = L3_RE.match(line)
            if m3:
                indent_dash, title, rest = m3.groups()
                title = title.strip()
                if title in SKIP_TITLES:
                    new_lines.append(line)
                    continue
                pn = pn_map.get(title)
                if pn:
                    link = make_link(title, chapter_id, pn)
                    new_line = f'{indent_dash}{link}{rest}'
                    if new_line != line:
                        changed += 1
                        line = new_line

        new_lines.append(line)

    if changed == 0:
        return 0

    new_text = '\n'.join(new_lines)
    if not dry_run:
        md_path.write_text(new_text, encoding='utf-8')
    print(f'  {"[dry]" if dry_run else "[ok]"} {chapter_id}: {changed} 处')
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='只预览，不写文件')
    ap.add_argument('--chapter', help='只处理指定章节（如 007_项羽本纪）')
    args = ap.parse_args()

    repo_root = Path(__file__).parent.parent.parent
    index_path = repo_root / 'data' / 'section_pn_index.json'
    pages_dir = repo_root / 'wiki' / 'public' / 'pages'

    if not index_path.exists():
        print(f'[error] 未找到 {index_path}，请先运行 scripts/build_section_pn_index.py',
              file=sys.stderr)
        sys.exit(1)

    index = json.loads(index_path.read_text(encoding='utf-8'))

    if args.chapter:
        md_files = [pages_dir / f'{args.chapter}.md']
    else:
        # 只处理形如 NNN_xxx.md 的章节页
        md_files = sorted(pages_dir.glob('[0-9][0-9][0-9]_*.md'))

    total_changed = 0
    for md_path in md_files:
        if not md_path.exists():
            print(f'[warn] 文件不存在: {md_path}', file=sys.stderr)
            continue
        total_changed += process_page(md_path, index, args.dry_run)

    print(f'\n共修改 {total_changed} 处'
          + (' (dry-run，未写入)' if args.dry_run else ''))


if __name__ == '__main__':
    main()
