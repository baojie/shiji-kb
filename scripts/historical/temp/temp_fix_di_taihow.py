#!/usr/bin/env python3
"""
临时脚本：修复058章中的"帝"、"太后"、"上"等称谓标注
"""

import re

def fix_titles(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 先保护已经标注的
    content = content.replace('〖@景帝〗', '【KEEP_JINGDI】')
    content = content.replace('〖@孝文〗', '【KEEP_XIAOWENDI】')
    content = content.replace('〖@文帝〗', '【KEEP_WENDI】')
    content = content.replace('〖@孝景帝〗', '【KEEP_XIAOJINGDI】')
    content = content.replace('〖@窦太后〗', '【KEEP_DOUTAIHOU】')
    content = content.replace('〖@陈太后〗', '【KEEP_CHENTAIHOU】')
    content = content.replace('〖@李太后〗', '【KEEP_LITAIHOU】')
    content = content.replace('〖@高帝〗', '【KEEP_GAODI】')
    content = content.replace('〖@成王〗', '【KEEP_CHENGWANG】')
    content = content.replace('〖@宋宣公〗', '【KEEP_SONGXUANGONG】')
    content = content.replace('〖@宣公〗', '【KEEP_XUANGONG】')
    content = content.replace('〖@栗太子〗', '【KEEP_LITAIZI】')
    content = content.replace('〖;太子〗', '【KEEP_TAIZI】')
    content = content.replace('〖;太后〗', '【KEEP_TAIHOUGW】')  # 官位标注
    content = content.replace('〖#天子〗', '【KEEP_TIANZI】')
    content = content.replace('〖#皇帝〗', '【KEEP_HUANGDI】')
    content = content.replace('〖;天王〗', '【KEEP_TIANWANG】')

    # 在本章中：
    # - "帝" 大多指景帝
    # - "太后" 指窦太后
    # - "上" 指当朝皇帝（景帝或武帝）

    # 1. 处理单独的"帝" → 〖@帝|汉景帝〗
    # 但要排除一些特殊情况
    content = re.sub(r'(?<![〖@#;])帝(?![〗])', '〖@帝|汉景帝〗', content)

    # 2. 处理"今帝" → 保持原样（指代不明确）
    content = content.replace('今〖@帝|汉景帝〗', '今帝')

    # 3. 处理"太后" → 〖@太后|窦太后〗
    content = re.sub(r'(?<![〖@])太后(?![〗])', '〖@太后|窦太后〗', content)

    # 4. 处理"上" → 〖@上|汉景帝〗
    # 但要排除一些特殊情况：背上、於上、以上等
    # 只处理句首或动作主语的"上"
    content = re.sub(r'(^|[。！？"」』]|[\s]+)上(?=[^上下林])', r'\1〖@上|汉景帝〗', content)

    # 恢复保护的标注
    content = content.replace('【KEEP_JINGDI】', '〖@景帝〗')
    content = content.replace('【KEEP_XIAOWENDI】', '〖@孝文〗')
    content = content.replace('【KEEP_WENDI】', '〖@文帝〗')
    content = content.replace('【KEEP_XIAOJINGDI】', '〖@孝景帝〗')
    content = content.replace('【KEEP_DOUTAIHOU】', '〖@窦太后〗')
    content = content.replace('【KEEP_CHENTAIHOU】', '〖@陈太后〗')
    content = content.replace('【KEEP_LITAIHOU】', '〖@李太后〗')
    content = content.replace('【KEEP_GAODI】', '〖@高帝〗')
    content = content.replace('【KEEP_CHENGWANG】', '〖@成王〗')
    content = content.replace('【KEEP_SONGXUANGONG】', '〖@宋宣公〗')
    content = content.replace('【KEEP_XUANGONG】', '〖@宣公〗')
    content = content.replace('【KEEP_LITAIZI】', '〖@栗太子〗')
    content = content.replace('【KEEP_TAIZI】', '〖;太子〗')
    content = content.replace('【KEEP_TAIHOUGW】', '〖;太后〗')
    content = content.replace('【KEEP_TIANZI】', '〖#天子〗')
    content = content.replace('【KEEP_HUANGDI】', '〖#皇帝〗')
    content = content.replace('【KEEP_TIANWANG】', '〖;天王〗')

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
    print(f"  - 〖@帝|汉景帝〗: {content.count('〖@帝|汉景帝〗')}")
    print(f"  - 〖@太后|窦太后〗: {content.count('〖@太后|窦太后〗')}")
    print(f"  - 〖@上|汉景帝〗: {content.count('〖@上|汉景帝〗')}")

if __name__ == '__main__':
    file_path = '/home/baojie/work/knowledge/shiji-kb/chapter_md/058_梁孝王世家.tagged.md'
    fix_titles(file_path)
