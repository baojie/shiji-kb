#!/usr/bin/env python3
"""
修复章节中的重复编号问题

问题模式：[N] 空行 + [N.N] 内容行
解决方案：合并为 [N] 内容行

用法：
    python scripts/fix_duplicate_pn.py chapter_md/035_管蔡世家.tagged.md
    python scripts/fix_duplicate_pn.py 035
    python scripts/fix_duplicate_pn.py 035 036 037
"""

import re
import sys
import os
from pathlib import Path

def fix_duplicate_pn(file_path):
    """修复重复的PN编号"""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    changes = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 检测是否是形如 [N.N] 的编号行（数字重复）
        match_dup = re.match(r'^\[(\d+)\.(\1)\]\s*(.*)', line)

        if match_dup:
            num = match_dup.group(1)
            content = match_dup.group(3)

            # 检查前面是否有 [N] 空行
            if (fixed_lines and
                fixed_lines[-1].strip() == '' and
                len(fixed_lines) >= 2 and
                re.match(rf'^\[{num}\]\s*$', fixed_lines[-2].strip())):

                # 情况1: [N] 空行 + [N.N] -> 合并
                fixed_lines.pop()  # 删除空行
                fixed_lines.pop()  # 删除 [N] 空行
                fixed_lines.append(f'[{num}] {content}\n')
                changes.append(f"Line {i+1}: Merged [{num}] + [{num}.{num}] -> [{num}]")

            else:
                # 情况2: 单独的 [N.N] -> 直接删除编号
                if content:
                    fixed_lines.append(f'{content}\n')
                changes.append(f"Line {i+1}: Removed [{num}.{num}], kept content")

        else:
            # 正常行，直接保留
            fixed_lines.append(line)

        i += 1

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    return changes

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/fix_duplicate_pn.py <chapter_number_or_path> [...]")
        print("示例:")
        print("  python scripts/fix_duplicate_pn.py 035")
        print("  python scripts/fix_duplicate_pn.py 035 036 037")
        print("  python scripts/fix_duplicate_pn.py chapter_md/035_管蔡世家.tagged.md")
        sys.exit(1)

    for arg in sys.argv[1:]:
        # 判断是章节号还是文件路径
        if arg.isdigit():
            # 章节号，需要查找对应的文件
            chapter_num = arg
            pattern = f"chapter_md/{chapter_num}_*.tagged.md"
            import glob
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

        changes = fix_duplicate_pn(file_path)

        if changes:
            print(f"✓ 修复完成！共修复 {len(changes)} 处")
            for change in changes[:10]:  # 只显示前10个
                print(f"  {change}")
            if len(changes) > 10:
                print(f"  ... 还有 {len(changes) - 10} 处修改")
        else:
            print("✓ 未发现重复编号问题")

if __name__ == '__main__':
    main()
