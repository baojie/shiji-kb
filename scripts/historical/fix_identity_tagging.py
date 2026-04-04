#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复系统性身份标注错误

问题：诸侯、天子等身份词被错误标注为思想 〖_XXX〗
正确：应该标注为身份 〖#XXX〗

影响范围：121个章节，约1588次出现
"""

import re
from pathlib import Path

# 需要从思想改为身份的词
# 这些词在3月19日的fix_identity_tags_global.py中被错误地从 〖#XXX〗 改为了 〖_XXX〗
# 实际上它们表示社会身份/角色，应该使用身份标注 〖#XXX〗
IDENTITY_TERMS = [
    '天子',
    '诸侯',
    '士',
    '臣',
    '民',
    '夫',
    '子',
    '孙',
    '弟',
    '父',
    '匹夫',
    '缙绅',
    '庶民',
    '万民',
    '百姓',
    '庶人',
]

# 需要排除的复合词（这些应该保留为 〖_XXX〗 因为它们是复合概念）
COMPOUND_EXCLUSIONS = [
    '弟子',   # 学生、门徒（概念）
    '夫子',   # 先生、老师（尊称概念）
    '士大夫', # 士大夫阶层（社会概念）
    '君子',   # 有德之人（道德概念）
    '父子',   # 父子关系（伦理概念）
]

def fix_identity_in_file(file_path):
    """修复单个文件中的身份标注错误

    注意：需要避免替换复合词中的单字
    例如：〖_弟子〗 不应该被拆分为 〖#弟〗子〗
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes = []

    # 先保护复合词：临时替换为占位符
    protected_compounds = {}
    for i, compound in enumerate(COMPOUND_EXCLUSIONS):
        placeholder = f'<<<COMPOUND_{i}>>>'
        pattern = f'〖_{re.escape(compound)}〗'
        if pattern in content:
            protected_compounds[placeholder] = pattern
            content = content.replace(pattern, placeholder)

    # 替换单字身份词
    for term in IDENTITY_TERMS:
        # 查找 〖_term〗 并替换为 〖#term〗
        pattern = f'〖_{re.escape(term)}〗'
        replacement = f'〖#{term}〗'

        count = content.count(pattern)
        if count > 0:
            content = content.replace(pattern, replacement)
            changes.append(f"  {term}: {count}次")

    # 恢复复合词
    for placeholder, original in protected_compounds.items():
        content = content.replace(placeholder, original)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes

    return None

def main():
    """批量修复所有章节文件"""
    chapter_dir = Path('chapter_md')

    if not chapter_dir.exists():
        print(f"错误: {chapter_dir} 目录不存在")
        return

    tagged_files = sorted(chapter_dir.glob('*.tagged.md'))

    if not tagged_files:
        print(f"错误: 在 {chapter_dir} 中未找到 .tagged.md 文件")
        return

    print(f"开始修复身份标注错误...")
    print(f"目标词汇: {', '.join(IDENTITY_TERMS)}")
    print(f"保护复合词: {', '.join(COMPOUND_EXCLUSIONS)}")
    print(f"发现 {len(tagged_files)} 个章节文件")
    print("=" * 60)

    total_fixed_files = 0
    total_changes = {term: 0 for term in IDENTITY_TERMS}

    for file_path in tagged_files:
        changes = fix_identity_in_file(file_path)

        if changes:
            total_fixed_files += 1
            print(f"\n✓ {file_path.name}")
            for change_msg in changes:
                print(change_msg)
                # 提取数字累加到总计
                for term in IDENTITY_TERMS:
                    if term in change_msg:
                        count = int(change_msg.split(':')[1].strip().replace('次', ''))
                        total_changes[term] += count

    print("\n" + "=" * 60)
    print("修复完成！")
    print(f"修复文件数: {total_fixed_files}")
    print(f"修复明细:")
    for term, count in total_changes.items():
        if count > 0:
            print(f"  {term}: {count}次 (〖_{term}〗 → 〖#{term}〗)")
    print(f"总计: {sum(total_changes.values())}次修改")

if __name__ == '__main__':
    main()
