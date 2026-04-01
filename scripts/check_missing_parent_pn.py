#!/usr/bin/env python3
"""
检查所有章节中缺失父段落编号的问题
例如：存在[67.1]但不存在[67]的情况

扫描 chapter_md/*.tagged.md 文件
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_pn_numbers(file_path):
    """提取文件中的所有段落编号"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配行首的 [数字] 或 [数字.数字] 或 [数字.数字.数字] 格式
    # 使用 MULTILINE 模式，匹配行首
    pattern = r'^\[(\d+(?:\.\d+)*)\]'
    matches = re.findall(pattern, content, re.MULTILINE)
    return matches

def analyze_chapter(file_path):
    """分析单个章节的段落编号问题"""
    pn_numbers = extract_pn_numbers(file_path)

    # 分类：一级编号和多级编号
    level1 = set()
    level2_plus = defaultdict(list)

    for pn in pn_numbers:
        if '.' in pn:
            # 提取父编号：67.1 → 67，67.1.2 → 67
            parent = pn.split('.')[0]
            level2_plus[parent].append(pn)
        else:
            level1.add(pn)

    # 找出缺失的父编号
    missing_parents = []
    for parent in sorted(level2_plus.keys(), key=lambda x: int(x)):
        if parent not in level1:
            missing_parents.append(parent)

    return {
        'level1': sorted(level1, key=lambda x: int(x)),
        'level2_plus': level2_plus,
        'missing_parents': missing_parents
    }

def main():
    """主函数"""
    chapter_md_dir = Path('chapter_md')

    if not chapter_md_dir.exists():
        print(f"错误：目录不存在 {chapter_md_dir}")
        return

    all_issues = {}

    # 检查所有章节文件
    for md_file in sorted(chapter_md_dir.glob('*.tagged.md')):
        chapter_num = md_file.stem.split('_')[0].replace('.tagged', '')
        result = analyze_chapter(md_file)

        if result['missing_parents']:
            all_issues[md_file.name] = result

    # 输出报告
    if all_issues:
        print("=" * 80)
        print("发现缺失父段落编号的章节：")
        print("=" * 80)

        for filename, info in all_issues.items():
            print(f"\n文件：{filename}")
            print(f"缺失的父编号：{', '.join(info['missing_parents'])}")

            for parent in info['missing_parents']:
                children = info['level2_plus'][parent]
                print(f"  [{parent}] 缺失，但存在子编号：{', '.join(children)}")

        print("\n" + "=" * 80)
        print(f"总计：{len(all_issues)} 个章节存在问题")
        print("=" * 80)
    else:
        print("✓ 所有章节的段落编号都正常，没有发现缺失父编号的情况")

if __name__ == '__main__':
    main()
