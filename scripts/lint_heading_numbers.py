#!/usr/bin/env python3
"""
检测标题中的段落编号

规则：二级和三级标题（##、###）不应包含段落编号，如 ## [6] 论法家 是错误的。
正确格式应为：## 论法家

检测模式：
- ## [数字] 标题文本
- ### [数字] 标题文本
- ## [数字.数字] 标题文本
- ### [数字.数字] 标题文本

注意：一级标题 # [0] 篇名 是合法的，不检测。
"""

import re
import sys
from pathlib import Path


def check_heading_numbers(file_path):
    """检查文件中标题是否包含段落编号"""
    errors = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 跳过一级标题（# [0] 篇名是合法的）
        if stripped.startswith('# '):
            continue

        # 检测二级标题中的编号
        if stripped.startswith('## '):
            match = re.match(r'^##\s+\[(\d+(?:\.\d+)*)\]\s+(.+)$', stripped)
            if match:
                pn = match.group(1)
                title = match.group(2)
                errors.append({
                    'line': i + 1,
                    'original': stripped,
                    'pn': pn,
                    'title': title,
                    'level': 2,
                    'fixed': f'## {title}'
                })

        # 检测三级标题中的编号
        elif stripped.startswith('### '):
            match = re.match(r'^###\s+\[(\d+(?:\.\d+)*)\]\s+(.+)$', stripped)
            if match:
                pn = match.group(1)
                title = match.group(2)
                errors.append({
                    'line': i + 1,
                    'original': stripped,
                    'pn': pn,
                    'title': title,
                    'level': 3,
                    'fixed': f'### {title}'
                })

    return errors


def main():
    # 获取所有tagged.md文件
    chapter_dir = Path(__file__).parent.parent / 'chapter_md'
    tagged_files = sorted(chapter_dir.glob('*.tagged.md'))

    total_errors = 0
    files_with_errors = []

    print("=" * 80)
    print("标题编号检查报告")
    print("=" * 80)
    print()

    for file_path in tagged_files:
        errors = check_heading_numbers(file_path)

        if errors:
            total_errors += len(errors)
            files_with_errors.append((file_path.name, errors))

            print(f"【{file_path.name}】发现 {len(errors)} 处错误")
            print("-" * 80)

            for err in errors:
                print(f"  行 {err['line']}: {err['original']}")
                print(f"    → 应改为: {err['fixed']}")
                print(f"    → 编号 [{err['pn']}] 应该移除")
                print()

            print()

    # 汇总报告
    print("=" * 80)
    print("汇总")
    print("=" * 80)
    print(f"检查文件数: {len(tagged_files)}")
    print(f"有错误的文件数: {len(files_with_errors)}")
    print(f"错误总数: {total_errors}")
    print()

    if files_with_errors:
        print("有错误的文件列表:")
        for filename, errors in files_with_errors:
            print(f"  - {filename}: {len(errors)}处错误")
        print()
        return 1
    else:
        print("✓ 所有文件检查通过！")
        return 0


if __name__ == '__main__':
    sys.exit(main())
