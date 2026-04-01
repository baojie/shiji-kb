#!/usr/bin/env python3
"""
修复空的PN编号行

问题：脚本处理后留下了空的 [N] 行，下一行是实际内容
解决：将 [N] 空行与下一行内容合并

用法：
    python scripts/fix_empty_pn_lines.py 036
    python scripts/fix_empty_pn_lines.py chapter_md/036_陈杞世家.tagged.md
"""

import re
import sys
import os
import glob

def fix_empty_pn_lines(file_path):
    """修复空的PN编号行"""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    changes = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 检测是否是空的PN编号行（只有 [N]，后面无内容）
        match_empty_pn = re.match(r'^\[(\d+)\]\s*$', line)

        if match_empty_pn and i + 1 < len(lines):
            num = match_empty_pn.group(1)
            next_line = lines[i + 1]

            # 如果下一行不是空行，且不是已经有编号的行
            if next_line.strip() and not re.match(r'^\[', next_line):
                # 合并：[N] + 下一行内容
                merged = f'[{num}] {next_line.lstrip()}'
                fixed_lines.append(merged)
                changes.append(f"Line {i+1}: Merged [{num}] + content on line {i+2}")
                i += 2  # 跳过下一行
                continue

        # 正常行，直接保留
        fixed_lines.append(line)
        i += 1

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    return changes

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/fix_empty_pn_lines.py <chapter_number_or_path> [...]")
        print("示例:")
        print("  python scripts/fix_empty_pn_lines.py 036")
        print("  python scripts/fix_empty_pn_lines.py 035 036 037")
        print("  python scripts/fix_empty_pn_lines.py chapter_md/036_陈杞世家.tagged.md")
        sys.exit(1)

    for arg in sys.argv[1:]:
        # 判断是章节号还是文件路径
        if arg.isdigit():
            # 章节号，需要查找对应的文件
            chapter_num = arg
            pattern = f"chapter_md/{chapter_num}_*.tagged.md"
            files = glob.glob(pattern)
            if not files:
                print(f"❌ 找不到章节 {chapter_num} 的文件")
                continue
            file_path = files[0]
        else:
            # 文件路径
            file_path = arg
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                continue

        print(f"\n{'='*70}")
        print(f"处理文件: {file_path}")
        print('='*70)

        changes = fix_empty_pn_lines(file_path)

        if changes:
            print(f"✓ 修复完成！共修复 {len(changes)} 处")
            for change in changes:
                print(f"  {change}")
        else:
            print("✓ 未发现空的PN编号行")

if __name__ == '__main__':
    main()
