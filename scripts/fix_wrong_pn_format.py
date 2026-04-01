#!/usr/bin/env python3
"""
修复错误的PN格式 [N.M] 其中 M = N+1

这种格式应该是 [M]，例如：
  [30.31] -> [31]
  [1.2] -> [2]
  [5.6] -> [6]

用法：
    python scripts/fix_wrong_pn_format.py 001
    python scripts/fix_wrong_pn_format.py 001 002 003
    python scripts/fix_wrong_pn_format.py --all
"""

import re
import sys
import os
import glob

def fix_wrong_pn_format(file_path):
    """修复 [N.N+1] 格式为 [N+1]"""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    changes = []

    for i, line in enumerate(lines):
        # 匹配 [N.M] 其中 M = N+1
        match = re.match(r'^\[(\d+)\.(\d+)\](.*)$', line)

        if match:
            n = int(match.group(1))
            m = int(match.group(2))
            rest = match.group(3)

            if m == n + 1:
                # 修正：[N.N+1] -> [N+1]
                fixed_line = f'[{m}]{rest}\n'
                fixed_lines.append(fixed_line)
                changes.append({
                    'line': i + 1,
                    'old': f'[{n}.{m}]',
                    'new': f'[{m}]'
                })
            else:
                # 保持不变
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    return changes

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/fix_wrong_pn_format.py <chapter_number> [...]")
        print("      python scripts/fix_wrong_pn_format.py --all")
        print("示例:")
        print("  python scripts/fix_wrong_pn_format.py 001")
        print("  python scripts/fix_wrong_pn_format.py 001 002 003")
        print("  python scripts/fix_wrong_pn_format.py --all")
        sys.exit(1)

    # 获取要处理的文件列表
    if sys.argv[1] == '--all':
        files = sorted(glob.glob('chapter_md/*.tagged.md'))
    else:
        files = []
        for arg in sys.argv[1:]:
            if arg.isdigit():
                pattern = f"chapter_md/{arg}_*.tagged.md"
                matches = glob.glob(pattern)
                if not matches:
                    print(f"❌ 找不到章节 {arg} 的文件")
                    continue
                files.extend(matches)
            else:
                if os.path.exists(arg):
                    files.append(arg)
                else:
                    print(f"❌ 文件不存在: {arg}")

    total_changes = 0

    for file_path in files:
        chapter = os.path.basename(file_path).split('_')[0]

        changes = fix_wrong_pn_format(file_path)

        if changes:
            print(f"\n{'='*70}")
            print(f"[{chapter}] {os.path.basename(file_path)}")
            print('='*70)
            print(f"✓ 修复 {len(changes)} 处错误编号")
            for change in changes[:5]:
                print(f"  Line {change['line']}: {change['old']} -> {change['new']}")
            if len(changes) > 5:
                print(f"  ... 还有 {len(changes) - 5} 处修改")
            total_changes += len(changes)

    print(f"\n{'='*70}")
    print(f"总计修复: {total_changes} 处错误编号")
    print('='*70)

if __name__ == '__main__':
    main()
