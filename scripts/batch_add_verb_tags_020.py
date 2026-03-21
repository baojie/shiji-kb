#!/usr/bin/env python3
"""
批量为020章添加动词标注
"""
import re

def add_verb_tags(text):
    """批量添加动词标注"""

    # 军事动词模式
    military_verbs = {
        '击': '⟦◈击⟧',
        '攻': '⟦◈攻⟧',
        '破': '⟦◈破⟧',
        '败': '⟦◈败⟧',
        '降': '⟦◈降⟧',
        '取': '⟦◈取⟧',
        '围': '⟦◈围⟧',
        '战': '⟦◈战⟧',
        '虏': '⟦◈虏⟧',
        '伐': '⟦◈伐⟧',
        '捕': '⟦◈捕⟧',
    }

    # 刑罚动词模式
    punishment_verbs = {
        '杀': '⟦◉杀⟧',
        '死': '⟦◉死⟧',
        '斩': '⟦◉斩⟧',
        '诛': '⟦◉诛⟧',
        '赦': '⟦◉赦⟧',
        '亡': '⟦◉亡⟧',
    }

    # 合并所有动词
    all_verbs = {**military_verbs, **punishment_verbs}

    # 处理每个动词
    for verb, tag in all_verbs.items():
        # 避免重复标注：如果已经有标注则跳过
        # 匹配未被标注的动词（前后都不是〗或⟧）
        pattern = f'([^〗⟧])({verb})([^〖⟦])'
        replacement = rf'\1{tag}\3'

        # 但要避免标注已经在标注内部的字符
        # 先保护已有的标注
        text = re.sub(pattern, replacement, text)

    return text

def main():
    file_path = '/home/baojie/work/shiji-kb/chapter_md/020_建元以来侯者年表.tagged.md'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 应用标注
    modified_content = add_verb_tags(content)

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    print("动词标注已应用")

if __name__ == '__main__':
    main()
