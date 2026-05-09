#!/usr/bin/env python3
"""修复 wiki 页面中 `\|` 错误（反斜杠+管道符）→ `|`。

问题：wikilink 内 `[[target\|display]]` 多余的反斜杠导致链接目标
变成 `target\`（含尾部反斜杠），造成断链。

用法：
  python3 scripts/fix_wikilink_backslash.py          # 修复并报告
  python3 scripts/fix_wikilink_backslash.py --dry-run  # 仅预览
"""
import os, re, sys

PAGES_DIR = 'docs/wiki/pages'

def fix_file(fp: str, dry_run: bool = False) -> int:
    with open(fp, encoding='utf-8') as f:
        content = f.read()

    # Only fix \| inside wikilinks [[...]]
    count_before = content.count('\\|')

    # Replace \| inside [[...]] only
    def fix_wikilink(m):
        return m.group(0).replace('\\|', '|')

    new_content = re.sub(r'\[\[.*?\]\]', fix_wikilink, content)
    count_after = new_content.count('\\|')

    fixed = count_before - count_after
    if fixed == 0 or dry_run:
        return fixed

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return fixed

def main():
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print('=== DRY RUN ===\n')

    total = 0
    for fname in sorted(os.listdir(PAGES_DIR)):
        if not fname.endswith('.md'):
            continue
        fp = os.path.join(PAGES_DIR, fname)
        n = fix_file(fp, dry_run)
        if n > 0:
            print(f'  {fname}: 修复 {n} 处')
            total += n

    label = '将修复' if dry_run else '已修复'
    print(f'\n总计 {label} {total} 处断链反斜杠')

if __name__ == '__main__':
    main()
