#!/usr/bin/env python3
"""
修复分节标题位置错误

规则：分节标题（##、###）必须出现在顶级段落之前。

修复策略：
当检测到标题后直接跟着非顶级段落（如[2.1]）时，在标题后、[2.1]前插入对应的顶级段落（如[2]）。

修复前：
### 秦国疆域与〖#大臣〗
[2.1] 当是之时...

修复后：
### 秦国疆域与〖#大臣〗
[2]
[2.1] 当是之时...
"""

import re
import sys
from pathlib import Path


def is_heading(line):
    """判断是否为标题行（##、###，但不包括# [0]这样的带编号一级标题）"""
    stripped = line.strip()
    if stripped.startswith('# ['):
        return False
    if stripped.startswith('## ') or stripped.startswith('### '):
        return True
    return False


def is_paragraph_number_line(line):
    """判断是否为以段落编号开头的行，返回匹配对象"""
    stripped = line.strip()
    match = re.match(r'^\[(\d+(?:\.\d+)*)\]', stripped)
    return match


def is_top_level_paragraph(pn):
    """判断段落编号是否为顶级"""
    return '.' not in pn


def get_top_level_pn(pn):
    """从段落编号中提取顶级编号，如 '4.1' -> '4'"""
    return pn.split('.')[0]


def fix_file(file_path, dry_run=False):
    """修复单个文件中的分节位置错误"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    changes = []  # 记录所有需要的变更
    i = 0

    # 第一遍：找出所有需要插入顶级段落的位置
    while i < len(lines):
        line = lines[i]

        # 检测模式：标题 -> 非顶级段落
        if is_heading(line):
            heading_line = line
            heading_idx = i

            # 查找标题后的第一个段落编号（跳过空行）
            j = i + 1
            first_pn = None
            first_pn_idx = None

            while j < len(lines):
                next_line = lines[j]

                # 跳过空行、分隔线、::: 标记
                if not next_line.strip() or next_line.strip() == '---' or next_line.strip().startswith(':::'):
                    j += 1
                    continue

                # 如果是段落编号
                match = is_paragraph_number_line(next_line)
                if match:
                    first_pn = match.group(1)
                    first_pn_idx = j
                    break
                else:
                    # 遇到其他内容，停止
                    break

            # 如果标题后是非顶级段落，需要插入顶级段落
            if first_pn and not is_top_level_paragraph(first_pn):
                top_level_pn = get_top_level_pn(first_pn)

                # 检查是否已经存在该顶级段落（向前查找）
                found_top_level = False
                for k in range(heading_idx - 1, -1, -1):
                    match = is_paragraph_number_line(lines[k])
                    if match:
                        pn = match.group(1)
                        if pn == top_level_pn:
                            found_top_level = True
                            break
                        # 如果找到其他顶级段落，说明确实缺少目标顶级段落
                        if is_top_level_paragraph(pn):
                            break

                # 如果不存在，记录需要插入
                if not found_top_level:
                    changes.append({
                        'insert_idx': first_pn_idx,
                        'top_level_pn': top_level_pn,
                        'heading_text': heading_line.strip(),
                        'heading_idx': heading_idx,
                        'first_pn': first_pn
                    })

        i += 1

    # 如果是dry-run，只打印计划
    if dry_run:
        for change in changes:
            print(f"  将插入顶级段落 [{change['top_level_pn']}]")
            print(f"    在: 第{change['insert_idx'] + 1}行（[{change['first_pn']}]之前）")
            print(f"    标题: {change['heading_text']} (第{change['heading_idx'] + 1}行)")
            print()
        return len(changes)

    # 执行修复
    if not changes:
        return 0

    # 第二遍：插入缺失的顶级段落
    # 按倒序处理，避免索引混乱
    for change in reversed(changes):
        insert_idx = change['insert_idx']
        top_level_pn = change['top_level_pn']

        # 插入空的顶级段落
        # 格式：[N] \n\n
        lines.insert(insert_idx, f'[{top_level_pn}] \n')
        lines.insert(insert_idx + 1, '\n')

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return len(changes)


def main():
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    # 获取所有tagged.md文件
    chapter_dir = Path(__file__).parent.parent / 'chapter_md'
    tagged_files = sorted(chapter_dir.glob('*.tagged.md'))

    total_fixed = 0
    files_fixed = []

    print("=" * 80)
    if dry_run:
        print("分节位置修复预览（dry-run模式）")
    else:
        print("分节位置修复")
    print("=" * 80)
    print()

    for file_path in tagged_files:
        fixed_count = fix_file(file_path, dry_run)

        if fixed_count > 0:
            total_fixed += fixed_count
            files_fixed.append((file_path.name, fixed_count))

            if not dry_run:
                print(f"【{file_path.name}】已修复 {fixed_count} 处错误 ✓")

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
        print(f"  python scripts/fix_section_position.py")
    else:
        print("✓ 修复完成！")
        print()
        print("建议运行以下命令验证修复结果：")
        print("  python scripts/lint_section_position.py")

    return 0


if __name__ == '__main__':
    sys.exit(main())
