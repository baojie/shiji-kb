#!/usr/bin/env python3
"""
临时脚本：修复058章中的梁王/孝王标注
将指代梁孝王刘武的简称标注为人名+消歧
"""

import re

def fix_liang_wang(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 规则1：〖=梁〗王 → 〖@梁王|梁孝王〗
    # 但要排除：〖=梁〗王〖@胜〗（这是梁王胜，不是梁孝王）
    # 排除：〖=梁〗王之初王〖=梁〗（这里"王"是动词）
    # 排除：〖=梁〗王，是为共〖;王〗（这是"梁王买"）

    # 先标记需要保留的特殊情况
    content = content.replace('〖=梁〗王〖@胜〗', '【KEEP_LIANG_WANG_SHENG】')
    content = content.replace('〖=梁〗王之初王〖=梁〗', '【KEEP_LIANG_WANG_ZHI】')
    content = content.replace('为〖=梁〗王，是为共〖;王〗', '【KEEP_LIANG_WANG_MAI】')
    content = content.replace('子〖@不识〗为〖=济阴〗〖;王〗', '【KEEP_JIYIN_WANG】')
    content = content.replace('为〖=济阴〗〖;王〗。', '【KEEP_JIYIN_WANG_END】')

    # 执行替换
    content = content.replace('〖=梁〗王', '〖@梁王|梁孝王〗')

    # 恢复特殊情况
    content = content.replace('【KEEP_LIANG_WANG_SHENG】', '〖=梁〗王〖@胜〗')
    content = content.replace('【KEEP_LIANG_WANG_ZHI】', '〖@梁王|梁孝王〗之初王〖=梁〗')  # 这个也改为梁王
    content = content.replace('【KEEP_LIANG_WANG_MAI】', '为〖@梁王|梁共王〗，是为共〖;王〗')  # 这是梁共王买
    content = content.replace('【KEEP_JIYIN_WANG】', '子〖@不识〗为〖=济阴〗〖;王〗')
    content = content.replace('【KEEP_JIYIN_WANG_END】', '为〖=济阴〗〖;王〗。')

    # 规则2：孝〖;王〗 → 〖@孝王|梁孝王〗
    # 但要排除：谥为孝〖;王〗（这是谥号，是代王参的）
    # 排除：谥曰孝〖;王〗（这是梁孝王的谥号，也保留）

    # 先标记特殊情况
    content = content.replace('，谥为孝〖;王〗。', '【KEEP_DAI_XIAO_WANG】')  # 代王参
    content = content.replace('卒，谥曰孝〖;王〗。', '【KEEP_XIE_HAO_XIAO_WANG】')  # 梁孝王谥号

    # 执行替换
    content = content.replace('孝〖;王〗', '〖@孝王|梁孝王〗')

    # 恢复特殊情况
    content = content.replace('【KEEP_DAI_XIAO_WANG】', '，谥为孝〖;王〗。')
    content = content.replace('【KEEP_XIE_HAO_XIAO_WANG】', '卒，谥曰孝〖;王〗。')

    # 修复：〖=梁〗孝〖;王〗 在特定位置保持不变（完整人名）
    # 但也有些地方需要保持，比如标题、子嗣说明等
    # [1] 〖=梁〗孝〖;王〗武者 - 标题，保持
    # [5] 〖=梁〗孝〖;王〗城守 - 保持（完整称呼）
    # [8] 〖=梁〗孝〖;王〗入朝 - 保持
    # [14] 〖=梁〗孝〖;王〗长子 - 保持
    # [19] 〖=梁〗孝〖;王〗子 - 保持
    # [23] 〖=梁〗孝〖;王〗虽以 - 保持

    # 这些位置的〖=梁〗孝〖;王〗都是完整人名，应保持不变

    # 检查是否有意外改变
    if '〖@梁王|梁孝王〗〖@胜〗' in content:
        print("错误：误改了梁王胜")
        return False

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 统计变更
    lines_changed = 0
    for old_line, new_line in zip(original_content.split('\n'), content.split('\n')):
        if old_line != new_line:
            lines_changed += 1

    print(f"✓ 修改完成")
    print(f"  - 修改了 {lines_changed} 行")
    print(f"  - 〖@梁王|梁孝王〗 出现次数: {content.count('〖@梁王|梁孝王〗')}")
    print(f"  - 〖@孝王|梁孝王〗 出现次数: {content.count('〖@孝王|梁孝王〗')}")

    return True

if __name__ == '__main__':
    file_path = '/home/baojie/work/knowledge/shiji-kb/chapter_md/058_梁孝王世家.tagged.md'
    fix_liang_wang(file_path)
