#!/usr/bin/env python3
"""
临时脚本：修复058章的最后标注问题
1. 单字名消歧（武、胜、参等）
2. 移除燕饮标注
3. 单独的"王"消歧
4. 长公主标注
"""

import re

def fix_final_annotations(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. 单字名消歧
    # 武 → 梁孝王刘武
    content = re.sub(r'(?<!〖)〖@武〗(?!帝)', '〖@武|刘武〗', content)

    # 胜 → 梁怀王刘胜（文帝子）和羊胜（梁孝王幸臣）
    # 需要区分：第一个胜是梁怀王，后面的胜是羊胜
    # 先保护羊胜
    content = content.replace('〖@羊胜〗', '【KEEP_YANGSHENG】')
    content = content.replace('〖@胜〗', '〖@胜|刘胜〗')  # 梁怀王刘胜
    content = content.replace('【KEEP_YANGSHENG】', '〖@羊胜〗')

    # 参 → 代王刘参
    content = content.replace('〖@参〗', '〖@参|刘参〗')

    # 登 → 代共王刘登
    content = content.replace('〖@登〗', '〖@登|刘登〗')

    # 义 → 代王刘义
    content = content.replace('〖@义〗', '〖@义|刘义〗')

    # 买 → 梁共王刘买
    content = content.replace('〖@买〗', '〖@买|刘买〗')

    # 明 → 济川王刘明
    content = content.replace('〖@明〗', '〖@明|刘明〗')

    # 彭离 → 济东王刘彭离
    content = content.replace('〖@彭离〗', '〖@彭离|刘彭离〗')

    # 定 → 山阳哀王刘定
    content = content.replace('〖@定〗', '〖@定|刘定〗')

    # 不识 → 济阴哀王刘不识
    content = content.replace('〖@不识〗', '〖@不识|刘不识〗')

    # 襄 → 梁平王刘襄
    content = content.replace('〖@襄〗', '〖@襄|刘襄〗')

    # 无伤 → 梁王刘无伤
    content = content.replace('〖@无伤〗', '〖@无伤|刘无伤〗')

    # 2. 移除燕饮标注 - 〖:燕〗饮改为燕饮（不标注）
    content = content.replace('〖:燕〗饮', '燕饮')

    # 3. 长公主标注
    # 长〖;公主〗 → 〖@长公主|窦太主〗（窦太后之女）
    content = content.replace('长〖;公主〗', '〖@长公主|窦太主〗')

    # 4. 单独的"王"消歧
    # 这个比较复杂，需要根据上下文判断
    # 暂时不处理，因为大部分"王"都已经在前面处理过了

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 统计
    lines_changed = 0
    for old_line, new_line in zip(original_content.split('\n'), content.split('\n')):
        if old_line != new_line:
            lines_changed += 1

    print(f"✓ 修改完成")
    print(f"  - 修改了 {lines_changed} 行")
    print(f"  - 单字名消歧: 武、胜、参、登、义、买、明、彭离、定、不识、襄、无伤")
    print(f"  - 移除燕饮标注")
    print(f"  - 长公主标注: {content.count('〖@长公主|窦太主〗')}")

if __name__ == '__main__':
    file_path = '/home/baojie/work/knowledge/shiji-kb/chapter_md/058_梁孝王世家.tagged.md'
    fix_final_annotations(file_path)
