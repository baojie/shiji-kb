#!/usr/bin/env python3
"""
临时脚本：修复058章中的各个王的完整人名标注
"""

import re

def fix_wang_names(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. 梁怀王
    content = content.replace('〖=梁〗怀〖;王〗', '〖@梁怀王〗')
    content = content.replace('怀〖;王〗', '〖@怀王|梁怀王〗')

    # 2. 梁共王
    content = content.replace('〖=梁〗共〖;王〗', '〖@梁共王〗')
    content = content.replace('共〖;王〗', '〖@共王|梁共王〗')

    # 3. 梁平王
    content = content.replace('〖=梁〗平〖;王〗', '〖@梁平王〗')
    content = content.replace('平〖;王〗', '〖@平王|梁平王〗')

    # 4. 但要排除：谥为平〖;王〗（这是谥号本身）
    content = content.replace('，谥为〖@平王|梁平王〗。', '，谥为平〖;王〗。')

    # 5. 其他国家的王
    # 代王、济川王、济东王、山阳王、济阴王
    # 这些在"为XX王"的语境下保持不变（如"为济川王"）
    # 但单独出现时需要标注

    # 代王
    content = content.replace('〖=代〗共〖;王〗', '〖@代共王〗')

    # 山阳哀王、济阴哀王
    content = content.replace('〖=山阳〗哀〖;王〗', '〖@山阳哀王〗')
    content = content.replace('〖=济阴〗哀〖;王〗', '〖@济阴哀王〗')

    # 济川王、济东王 - 这些只在"为XX王"的语境出现，保持不变

    # 检查修改
    lines_changed = 0
    for old_line, new_line in zip(original_content.split('\n'), content.split('\n')):
        if old_line != new_line:
            lines_changed += 1
            print(f"  {new_line[:80]}...")

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✓ 修改完成")
    print(f"  - 修改了 {lines_changed} 行")
    print(f"  - 〖@梁怀王〗: {content.count('〖@梁怀王〗')}")
    print(f"  - 〖@梁共王〗: {content.count('〖@梁共王〗')}")
    print(f"  - 〖@梁平王〗: {content.count('〖@梁平王〗')}")
    print(f"  - 〖@怀王|梁怀王〗: {content.count('〖@怀王|梁怀王〗')}")
    print(f"  - 〖@共王|梁共王〗: {content.count('〖@共王|梁共王〗')}")
    print(f"  - 〖@平王|梁平王〗: {content.count('〖@平王|梁平王〗')}")

    return True

if __name__ == '__main__':
    file_path = '/home/baojie/work/knowledge/shiji-kb/chapter_md/058_梁孝王世家.tagged.md'
    fix_wang_names(file_path)
