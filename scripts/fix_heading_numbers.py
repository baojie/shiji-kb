#!/usr/bin/env python3
"""
修复标题中的段落编号

规则：二级和三级标题（##、###）不应包含段落编号。

修复操作：
- ## [数字] 标题文本 → ## 标题文本
- ### [数字] 标题文本 → ### 标题文本
- ## [数字.数字] 标题文本 → ## 标题文本
- ### [数字.数字] 标题文本 → ### 标题文本

注意：一级标题 # [0] 篇名 保持不变。
"""

import re
import sys
from pathlib import Path


def fix_heading_numbers(file_path, dry_run=False):
    """修复文件中标题的段落编号"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_count = 0
    new_lines = []

    for line in lines:
        stripped = line.strip()
        original_line = line

        # 跳过一级标题
        if stripped.startswith('# '):
            new_lines.append(line)
            continue

        # 修复二级标题
        if stripped.startswith('## '):
            match = re.match(r'^(##\s+)\[(\d+(?:\.\d+)*)\]\s+(.+)$', stripped)
            if match:
                prefix = match.group(1)
                title = match.group(3)
                # 保持原有的缩进和换行符
                indent = line[:len(line) - len(line.lstrip())]
                newline = line[len(line.rstrip()):]
                line = f'{indent}{prefix}{title}{newline}'
                fixed_count += 1

        # 修复三级标题
        elif stripped.startswith('### '):
            match = re.match(r'^(###\s+)\[(\d+(?:\.\d+)*)\]\s+(.+)$', stripped)
            if match:
                prefix = match.group(1)
                title = match.group(3)
                # 保持原有的缩进和换行符
                indent = line[:len(line) - len(line.lstrip())]
                newline = line[len(line.rstrip()):]
                line = f'{indent}{prefix}{title}{newline}'
                fixed_count += 1

        new_lines.append(line)

    # 如果不是dry-run且有修复，写回文件
    if not dry_run and fixed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return fixed_count


def main():
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    # 获取所有tagged.md文件
    chapter_dir = Path(__file__).parent.parent / 'chapter_md'
    tagged_files = sorted(chapter_dir.glob('*.tagged.md'))

    total_fixed = 0
    files_fixed = []

    print("=" * 80)
    if dry_run:
        print("标题编号修复预览（dry-run模式）")
    else:
        print("标题编号修复")
    print("=" * 80)
    print()

    for file_path in tagged_files:
        fixed_count = fix_heading_numbers(file_path, dry_run)

        if fixed_count > 0:
            total_fixed += fixed_count
            files_fixed.append((file_path.name, fixed_count))

            if not dry_run:
                print(f"【{file_path.name}】已修复 {fixed_count} 处 ✓")

    # 汇总报告
    print()
    print("=" * 80)
    print("汇总")
    print("=" * 80)
    print(f"检查文件数: {len(tagged_files)}")
    print(f"{'将修复' if dry_run else '已修复'}文件数: {len(files_fixed)}")
    print(f"{'预计修复' if dry_run else '实际修复'}总数: {total_fixed}")
    print()

    if files_fixed:
        print(f"{'将修复' if dry_run else '已修复'}的文件列表:")
        for filename, count in files_fixed:
            print(f"  - {filename}: {count}处")
        print()

    if dry_run:
        print("这是预览模式。要真正修复，请运行：")
        print(f"  python scripts/fix_heading_numbers.py")
    else:
        print("✓ 修复完成！")
        print()
        print("建议运行以下命令验证修复结果：")
        print("  python scripts/lint_heading_numbers.py")

    return 0


if __name__ == '__main__':
    sys.exit(main())
