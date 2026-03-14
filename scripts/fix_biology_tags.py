#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复生物标注：移除误标 + 补标遗漏

1. 移除非生物词的 〖+X〗 标注（还原为裸文本）
2. 补标词表词的遗漏实例
"""

import re
from pathlib import Path
from collections import defaultdict

CHAPTER_DIR = Path('chapter_md')

# 误标为生物的词 → 移除〖+〗标注
FALSE_POSITIVES = {
    '山河', '山', '黄云', '石', '毛', '脣', '竿', '目', '车',
    '黄砾', '黄', '屣', '靧', '亸', '澥昉', '桂林', '木铁',
}

# 需要补标的词（从scan报告的untagged发现）
# 格式: {章节前缀: [(词, 补标后)]}
TAG_FIXES = {
    # 六畜 - 常见合称，应标生物
    # 猛兽 - 应标生物
    # 白鹿 - 012 中有未标注的
    # 禽兽 - 060 中有未标注的
}


def fix_false_positives():
    """移除误标的〖+X〗标注"""
    total_removed = 0
    for fpath in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        text = fpath.read_text(encoding='utf-8')
        original = text

        for word in FALSE_POSITIVES:
            pattern = f'〖+{re.escape(word)}〗'
            count = text.count(pattern)
            if count > 0:
                text = text.replace(pattern, word)
                total_removed += count
                print(f'  移除 {fpath.name}: 〖+{word}〗 × {count}')

        if text != original:
            fpath.write_text(text, encoding='utf-8')

    return total_removed


def tag_untagged():
    """补标遗漏的生物词（谨慎模式：只补上下文确定的）"""
    # 这里只做自动可判定的补标
    # 复杂的上下文判断留给LLM反思
    total_tagged = 0

    # 六畜 → 〖+六畜〗（确定是生物合称）
    for fpath in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        text = fpath.read_text(encoding='utf-8')
        original = text

        # 只在未被标注的位置替换"六畜"
        # 使用负向前后瞻确保不在已有标注内
        # 简单方法：找到裸"六畜"（不在〖〗内）
        def replace_untagged(text, word, tagged):
            result = []
            i = 0
            while i < len(text):
                # Check if we're inside a tag
                if text[i:i+1] == '〖':
                    # Find closing 〗
                    end = text.find('〗', i)
                    if end != -1:
                        result.append(text[i:end+1])
                        i = end + 1
                        continue
                elif text[i:i+1] in ('〚', '《', '〈', '【', '〔'):
                    # Other tag types - skip
                    closers = {'〚': '〛', '《': '》', '〈': '〉', '【': '】', '〔': '〕'}
                    closer = closers.get(text[i:i+1])
                    if closer:
                        end = text.find(closer, i)
                        if end != -1:
                            result.append(text[i:end+1])
                            i = end + 1
                            continue

                if text[i:i+len(word)] == word:
                    result.append(tagged)
                    i += len(word)
                else:
                    result.append(text[i])
                    i += 1

            return ''.join(result)

        for word in ['六畜', '猛兽', '禽兽']:
            if word in text and f'〖+{word}〗' not in text:
                new_text = replace_untagged(text, word, f'〖+{word}〗')
                if new_text != text:
                    count = new_text.count(f'〖+{word}〗') - text.count(f'〖+{word}〗')
                    if count > 0:
                        text = new_text
                        total_tagged += count
                        print(f'  补标 {fpath.name}: 〖+{word}〗 × {count}')

        if text != original:
            fpath.write_text(text, encoding='utf-8')

    return total_tagged


def main():
    print('=== 移除误标 ===')
    removed = fix_false_positives()
    print(f'\n移除了 {removed} 处误标')

    print('\n=== 补标遗漏 ===')
    tagged = tag_untagged()
    print(f'\n补标了 {tagged} 处遗漏')


if __name__ == '__main__':
    main()
