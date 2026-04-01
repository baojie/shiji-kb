#!/usr/bin/env python3
"""
删除所有PN编号，然后为每个自然段重新添加连续的PN编号

自然段定义：前后有空行的独立段落（不包括标题、列表、表格等）

用法：
    python scripts/renumber_chapter.py 037
    python scripts/renumber_chapter.py chapter_md/037_卫康叔世家.tagged.md
"""

import re
import sys
import os
import glob

def renumber_chapter(file_path):
    """重新编号章节"""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 步骤1: 删除所有PN编号
    print("步骤1: 删除所有现有PN编号...")
    cleaned_lines = []
    removed_count = 0

    for line in lines:
        # 删除行首的 [N] 或 [N.M] 或 [N.M.K] 编号
        match = re.match(r'^\[(\d+(?:\.\d+)*)\]\s*(.*)$', line)
        if match:
            content = match.group(2)
            if content:  # 如果有内容，保留内容
                cleaned_lines.append(content + '\n')
            # 如果是空的PN行，直接删除（不添加）
            removed_count += 1
        else:
            cleaned_lines.append(line)

    print(f"  删除了 {removed_count} 个PN编号")

    # 步骤2: 为每个自然段添加新编号
    print("\n步骤2: 为每个自然段添加新的PN编号...")
    numbered_lines = []
    pn = 0  # 从0开始（篇名）
    i = 0
    added_count = 0

    while i < len(cleaned_lines):
        line = cleaned_lines[i]
        stripped = line.strip()

        # 跳过空行
        if not stripped:
            numbered_lines.append(line)
            i += 1
            continue

        # 跳过markdown标题（以 # 开头）
        if stripped.startswith('#'):
            numbered_lines.append(line)
            i += 1
            continue

        # 跳过引用块（以 > 开头）
        if stripped.startswith('>'):
            numbered_lines.append(line)
            i += 1
            continue

        # 跳过分隔线和custom block标记
        if stripped in ['---', '***', '___', ':::']:
            numbered_lines.append(line)
            i += 1
            continue

        # 跳过列表项（以 - 或 * 或 + 或数字. 开头）
        if (stripped.startswith('- ') or
            stripped.startswith('* ') or
            stripped.startswith('+ ') or
            re.match(r'^\d+\.\s', stripped)):
            numbered_lines.append(line)
            i += 1
            continue

        # 跳过表格行（包含 |）
        if '|' in stripped:
            # 简单判断：移除标注后检查 | 数量
            line_without_annotations = re.sub(r'[〖⟦][^〗⟧]+[〗⟧]', '', stripped)
            if line_without_annotations.startswith('|') or line_without_annotations.count('|') >= 2:
                numbered_lines.append(line)
                i += 1
                continue

        # 这是一个内容行
        # 检查是否前面有空行（或是文件开头）
        has_prev_empty = (i == 0 or not cleaned_lines[i-1].strip())

        # 检查是否后面有空行（或是文件结尾）
        has_next_empty = (i >= len(cleaned_lines) - 1 or not cleaned_lines[i+1].strip())

        # 如果是独立段落（前后都有空行），添加PN编号
        if has_prev_empty and has_next_empty:
            # 添加编号
            numbered_line = f'[{pn}] {line.lstrip()}'
            numbered_lines.append(numbered_line)
            pn += 1
            added_count += 1
        else:
            # 不是独立段落，保持原样
            numbered_lines.append(line)

        i += 1

    print(f"  添加了 {added_count} 个新的PN编号 (从 [0] 到 [{pn-1}])")

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(numbered_lines)

    return {
        'removed': removed_count,
        'added': added_count,
        'max_pn': pn - 1
    }

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/renumber_chapter.py <chapter_number_or_path>")
        print("示例:")
        print("  python scripts/renumber_chapter.py 037")
        print("  python scripts/renumber_chapter.py chapter_md/037_卫康叔世家.tagged.md")
        sys.exit(1)

    arg = sys.argv[1]

    # 判断是章节号还是文件路径
    if arg.isdigit():
        pattern = f"chapter_md/{arg}_*.tagged.md"
        files = glob.glob(pattern)
        if not files:
            print(f"❌ 找不到章节 {arg} 的文件")
            sys.exit(1)
        file_path = files[0]
    else:
        file_path = arg
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            sys.exit(1)

    print(f"{'='*70}")
    print(f"重新编号: {os.path.basename(file_path)}")
    print('='*70)

    result = renumber_chapter(file_path)

    print(f"\n{'='*70}")
    print("✓ 重新编号完成！")
    print(f"  删除: {result['removed']} 个旧编号")
    print(f"  添加: {result['added']} 个新编号")
    print(f"  编号范围: [0] ~ [{result['max_pn']}]")
    print('='*70)

if __name__ == '__main__':
    main()
