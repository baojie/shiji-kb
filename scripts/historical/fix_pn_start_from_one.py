#!/usr/bin/env python3
"""
修复PN编号：将所有非标题的编号加1

问题：第一个自然段被编号为 [0]，应该是 [1]
解决：
  - 保持一级标题的 [0] 不变
  - 将所有其他 [N] 改为 [N+1]

用法：
    python scripts/fix_pn_start_from_one.py 037
"""

import re
import sys
import os
import glob

def fix_pn_start_from_one(file_path):
    """将非标题的PN编号全部加1"""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    changes = []

    for i, line in enumerate(lines):
        # 检测一级标题的 [0]，保持不变
        if line.strip().startswith('# [0]'):
            fixed_lines.append(line)
            continue

        # 检测普通行的 [N]，将 N 加 1
        match = re.match(r'^\[(\d+)\](.*)$', line)
        if match:
            n = int(match.group(1))
            rest = match.group(2)

            # 将编号加1
            new_n = n + 1
            fixed_line = f'[{new_n}]{rest}\n'
            fixed_lines.append(fixed_line)

            changes.append({
                'line': i + 1,
                'old': f'[{n}]',
                'new': f'[{new_n}]'
            })
        else:
            fixed_lines.append(line)

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    return changes

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/fix_pn_start_from_one.py <chapter_number_or_path>")
        print("示例:")
        print("  python scripts/fix_pn_start_from_one.py 037")
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
    print(f"修复编号: {os.path.basename(file_path)}")
    print('='*70)

    changes = fix_pn_start_from_one(file_path)

    if changes:
        print(f"✓ 修复完成！共修改 {len(changes)} 个编号")
        print(f"  编号范围: [0]（标题） + [1] ~ [{changes[-1]['new'][1:-1]}]")
    else:
        print("✓ 无需修复")

    print('='*70)

if __name__ == '__main__':
    main()
