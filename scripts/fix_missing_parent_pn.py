#!/usr/bin/env python3
"""
修复所有章节中缺失的父段落编号
为每个缺失的父编号 [N] 插入空段落

规则：
1. 在第一个子编号（如 [67.1]）之前插入空段落 [67]
2. 如果前面有标题（## 或 ###），在标题后、子编号前插入
3. 空段落只包含编号，不包含任何内容
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_pn_info(file_path):
    """提取文件中的所有段落编号及其行号"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    pn_info = []
    for line_num, line in enumerate(lines):
        # 匹配行首的段落编号
        match = re.match(r'^\[(\d+(?:\.\d+)*)\]', line)
        if match:
            pn = match.group(1)
            pn_info.append((pn, line_num, line))

    return lines, pn_info

def find_missing_parents(pn_info):
    """找出缺失的父编号"""
    level1 = set()
    level2_plus = defaultdict(list)

    for pn, line_num, _ in pn_info:
        if '.' in pn:
            parent = pn.split('.')[0]
            level2_plus[parent].append((pn, line_num))
        else:
            level1.add(pn)

    missing = []
    for parent in sorted(level2_plus.keys(), key=lambda x: int(x)):
        if parent not in level1:
            # 找到第一个子编号的位置
            first_child = level2_plus[parent][0]
            missing.append((parent, first_child[1]))  # (父编号, 第一个子编号的行号)

    return missing

def fix_file(file_path, dry_run=False):
    """修复单个文件"""
    lines, pn_info = extract_pn_info(file_path)
    missing = find_missing_parents(pn_info)

    if not missing:
        return False, []

    # 按行号倒序插入，避免行号偏移
    missing.sort(key=lambda x: x[1], reverse=True)

    modifications = []
    for parent_pn, insert_before_line in missing:
        # 在 insert_before_line 之前插入 [parent_pn]
        # 检查前面是否有标题
        check_line = insert_before_line - 1
        insert_line = insert_before_line

        # 向前查找，跳过空行和标题行
        while check_line >= 0:
            stripped = lines[check_line].strip()
            if stripped == '':
                # 空行，继续向前
                check_line -= 1
                continue
            elif stripped.startswith('###') or stripped.startswith('##'):
                # 找到标题，在标题后插入（跳过后面的空行）
                insert_line = check_line + 1
                # 跳过标题后的空行
                while insert_line < len(lines) and lines[insert_line].strip() == '':
                    insert_line += 1
                break
            else:
                # 遇到其他内容，在当前位置插入
                break

        # 插入空段落
        empty_para = f'[{parent_pn}]\n'
        lines.insert(insert_line, empty_para)
        modifications.append((parent_pn, insert_line + 1))  # 报告时使用1-based行号

    if not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    return True, modifications

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='修复缺失的父段落编号')
    parser.add_argument('--dry-run', action='store_true', help='只检查不修改文件')
    parser.add_argument('--dir', choices=['chapter_md', 'archive'], default='chapter_md',
                        help='选择处理的目录：chapter_md（默认）或 corpus/archive/chapter_numbered')
    parser.add_argument('chapters', nargs='*', help='指定章节编号（如 004 006），不指定则处理全部')
    args = parser.parse_args()

    if args.dir == 'chapter_md':
        target_dir = Path('chapter_md')
        file_pattern = '*.tagged.md'
        chapter_pattern = lambda num: f"{num}_*.tagged.md"
    else:  # archive
        target_dir = Path('corpus/archive/chapter_numbered')
        file_pattern = '*.txt'
        chapter_pattern = lambda num: f"{num}_*.txt"

    if not target_dir.exists():
        print(f"错误：目录不存在 {target_dir}")
        return

    # 获取需要处理的文件
    if args.chapters:
        files = []
        for chapter_num in args.chapters:
            pattern = chapter_pattern(chapter_num)
            found = list(target_dir.glob(pattern))
            if found:
                files.extend(found)
            else:
                print(f"警告：未找到章节 {chapter_num}")
        files.sort()
    else:
        files = sorted(target_dir.glob(file_pattern))

    if not files:
        print("未找到任何文件")
        return

    if args.dry_run:
        print("【模拟运行模式 - 不会修改文件】")
    print(f"处理目录：{target_dir}")
    print("=" * 80)

    fixed_count = 0
    total_insertions = 0

    for file_path in files:
        modified, modifications = fix_file(file_path, dry_run=args.dry_run)

        if modified:
            fixed_count += 1
            total_insertions += len(modifications)
            print(f"\n文件：{file_path.name}")
            print(f"插入 {len(modifications)} 个空段落：")
            for parent_pn, line_num in sorted(modifications, key=lambda x: int(x[0])):
                print(f"  [{parent_pn}] (第 {line_num} 行)")

    print("\n" + "=" * 80)
    if fixed_count > 0:
        action = "将修改" if args.dry_run else "已修改"
        print(f"{action}：{fixed_count} 个文件，共插入 {total_insertions} 个空段落")
    else:
        print("所有文件都正常，无需修改")

    if args.dry_run:
        print("\n提示：去掉 --dry-run 参数以实际修改文件")

if __name__ == '__main__':
    main()
