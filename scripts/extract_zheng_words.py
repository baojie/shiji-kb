#!/usr/bin/env python3
"""
提取《史记》中所有含"徵"字的词汇
"""
import re
import glob
from collections import Counter

def extract_zheng_contexts(file_path):
    """从标注文件中提取含"徵"字的上下文"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 移除所有标注符号
    clean_text = re.sub(r'[〖〗⟦⟧]', '', content)
    clean_text = re.sub(r'[#@%&\'=:;\[\]\{\}!?~\^•\$\+\-\*◈◉\|]', '', clean_text)

    # 找出所有含"徵"的3-5字词组
    contexts = []
    for match in re.finditer(r'徵', clean_text):
        start = max(0, match.start() - 3)
        end = min(len(clean_text), match.end() + 3)
        context = clean_text[start:end]
        contexts.append(context)

    return contexts

def main():
    all_contexts = []

    # 遍历所有标注文件
    for file_path in glob.glob('chapter_md/*.tagged.md'):
        contexts = extract_zheng_contexts(file_path)
        all_contexts.extend(contexts)

    # 统计出现次数
    counter = Counter(all_contexts)

    print(f"共找到 {len(all_contexts)} 处含'徵'字的文本")
    print(f"共有 {len(counter)} 种不同的上下文\n")

    print("=" * 60)
    print("出现频次统计（按出现次数排序）：")
    print("=" * 60)

    for context, count in counter.most_common():
        print(f"{count:3d}  {context}")

    # 提取关键词汇
    print("\n" + "=" * 60)
    print("关键词汇分类：")
    print("=" * 60)

    # 音律用法（五音之一，读zhǐ）
    music_terms = []
    # 征召用法（通"征"，读zhēng）
    recruit_terms = []
    # 人名
    person_names = []
    # 其他
    other_terms = []

    for context in set(all_contexts):
        if '宫' in context or '商' in context or '角' in context or '羽' in context:
            music_terms.append(context)
        elif any(x in context for x in ['徵师', '徵兵', '徵求', '徵召', '徵发']):
            recruit_terms.append(context)
        elif '徵舒' in context:
            person_names.append(context)
        elif any(x in context for x in ['徵', '庶徵', '休徵', '咎徵', '变徵']):
            other_terms.append(context)

    print("\n【五音之一】（读 zhǐ）")
    for term in sorted(set(music_terms)):
        print(f"  {term}")

    print('\n【征召义】（读 zhēng，通"征"）')
    for term in sorted(set(recruit_terms)):
        print(f"  {term}")

    print("\n【人名】")
    for term in sorted(set(person_names)):
        print(f"  {term}")

    print("\n【其他用法】")
    for term in sorted(set(other_terms)):
        print(f"  {term}")

if __name__ == '__main__':
    main()
