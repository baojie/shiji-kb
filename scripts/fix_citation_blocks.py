"""
fix_citation_blocks.py
======================
修复 wiki 页面引文摘录块的两个格式问题：

1. 连续 `>` 行之间补空行（Markdown 要求独立 blockquote 须空行分隔）
2. PN 格式修复：`[[NNN_xxx]]（YYY）` → `[[NNN_xxx]]（NNN-YYY）`
   - 例：`[[005_秦本纪]]（67）` → `[[005_秦本纪]]（005-67）`
   - 已含章节前缀的（如 `005-67`）不重复处理

用法：
  python3 scripts/fix_citation_blocks.py           # 处理所有页面
  python3 scripts/fix_citation_blocks.py --dry-run # 只打印，不写文件
  python3 scripts/fix_citation_blocks.py --page 大梁
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PAGES_DIR = ROOT / "wiki/public/pages"

# 匹配 [[NNN_...]]（PN） 中尚未含章节前缀的 PN
# 捕获组 1: 章节三位编号, 捕获组 2: 括号内原 PN（不含章节前缀）
PN_RE = re.compile(
    r'(\[\[(\d{3})_[^\]]+\]\])'   # group 1: wikilink, group 2: 3-digit chapter no
    r'（'
    r'(?!\d{3}-)'                  # 负前瞻：不以"NNN-"开头（避免重复修复）
    r'([^）]+)'                    # group 3: 原 PN 内容
    r'）'
)


def fix_pn(line: str) -> str:
    """将 [[NNN_xxx]]（YYY）中缺少章节前缀的 PN 修正为 [[NNN_xxx]]（NNN-YYY）"""
    def repl(m):
        wikilink = m.group(1)
        chapter_no = m.group(2)
        pn_body = m.group(3)
        return f"{wikilink}（{chapter_no}-{pn_body}）"
    return PN_RE.sub(repl, line)


def fix_content(content: str) -> tuple[str, int, int]:
    """
    返回 (new_content, blank_line_fixes, pn_fixes)
    """
    lines = content.splitlines(keepends=True)
    out = []
    blank_fixes = 0
    pn_fixes = 0

    for i, line in enumerate(lines):
        is_blockquote = line.lstrip().startswith('>')

        # 问题1：在连续 > 行之间插入空行
        if is_blockquote and out:
            prev = out[-1]
            if prev.lstrip().startswith('>') and prev.strip():
                out.append('\n')
                blank_fixes += 1

        # 问题2：修复 PN 格式
        if is_blockquote and '[[' in line:
            fixed = fix_pn(line)
            if fixed != line:
                pn_fixes += 1
                line = fixed

        out.append(line)

    return ''.join(out), blank_fixes, pn_fixes


def main():
    ap = argparse.ArgumentParser(description="修复引文摘录块格式")
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--page', metavar='NAME', help='只处理指定页面')
    args = ap.parse_args()

    pages = sorted(PAGES_DIR.glob('*.md'))
    if args.page:
        pages = [p for p in pages if p.stem == args.page]
        if not pages:
            print(f"未找到页面: {args.page}", file=sys.stderr)
            sys.exit(1)

    total_blank = total_pn = total_changed = 0

    for path in pages:
        content = path.read_text(encoding='utf-8')
        if '引文摘录' not in content and '> **出自' not in content:
            continue

        new_content, blank_fixes, pn_fixes = fix_content(content)
        if new_content == content:
            continue

        total_blank += blank_fixes
        total_pn += pn_fixes
        total_changed += 1

        flag = '[DRY]' if args.dry_run else '✓'
        print(f"  {flag} {path.stem}  空行+{blank_fixes}  PN修复+{pn_fixes}")

        if not args.dry_run:
            path.write_text(new_content, encoding='utf-8')

    print(f"\n完成: 修改 {total_changed} 个文件，补空行 {total_blank} 处，PN修复 {total_pn} 处")


if __name__ == '__main__':
    main()
