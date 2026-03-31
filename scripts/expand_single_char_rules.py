#!/usr/bin/env python3
"""
将单字规则扩展为词组规则
分析每个单字在《史记》中的实际用法，生成高频词组规则
"""

import json
from pathlib import Path
from opencc import OpenCC
from collections import Counter
import re

def load_shiji_text():
    """加载所有史记文本"""
    archive_dir = Path('/home/baojie/work/knowledge/shiji-kb/archive')
    all_text = ""
    for txt_file in sorted(archive_dir.glob('史记*.txt')):
        all_text += txt_file.read_text(encoding='utf-8')
    return all_text

def find_phrases_with_char(text, char, min_freq=3):
    """
    找出包含指定字符的高频词组
    返回2-4字的词组及其出现频率
    """
    phrases = Counter()

    # 2字词组
    for match in re.finditer(f'[\\u4e00-\\u9fff]{char}', text):
        phrases[match.group()] += 1
    for match in re.finditer(f'{char}[\\u4e00-\\u9fff]', text):
        phrases[match.group()] += 1

    # 3字词组
    for match in re.finditer(f'[\\u4e00-\\u9fff]{{{2}}}{char}', text):
        phrases[match.group()] += 1
    for match in re.finditer(f'[\\u4e00-\\u9fff]{char}[\\u4e00-\\u9fff]', text):
        phrases[match.group()] += 1
    for match in re.finditer(f'{char}[\\u4e00-\\u9fff]{{{2}}}', text):
        phrases[match.group()] += 1

    # 过滤低频词组
    return {phrase: count for phrase, count in phrases.items() if count >= min_freq}

def main():
    print("加载史记文本...")
    text = load_shiji_text()

    # 加载v3.0
    v3_file = Path('/home/baojie/work/knowledge/shiji-kb/docs/data/custom-variants-v3.json')
    v3_variants = json.loads(v3_file.read_text(encoding='utf-8'))

    # 找出单字规则
    single_char_rules = {k: v for k, v in v3_variants.items() if len(k) == 1}

    print(f"\n发现 {len(single_char_rules)} 个单字规则:")
    for char, trad in single_char_rules.items():
        print(f'  "{char}": "{trad}"')

    cc = OpenCC('s2t')

    print("\n" + "="*80)
    print("分析每个单字的使用情况，生成词组规则")
    print("="*80)

    new_phrase_rules = {}

    for char, expected_trad in single_char_rules.items():
        print(f"\n字符: {char} → {expected_trad}")

        # 统计该字符出现次数
        char_count = text.count(char)
        print(f"总出现次数: {char_count}")

        # 找出高频词组（至少出现3次）
        phrases = find_phrases_with_char(text, char, min_freq=3)
        print(f"找到 {len(phrases)} 个高频词组（≥3次）")

        # 检查哪些词组需要自定义规则
        rules_added = 0
        for phrase, count in sorted(phrases.items(), key=lambda x: x[1], reverse=True)[:30]:  # 只看前30个
            # OpenCC转换
            opencc_result = cc.convert(phrase)

            # 期望的转换（基于单字规则）
            expected = phrase.replace(char, expected_trad)

            # 如果OpenCC转换不符合预期，则需要添加规则
            if opencc_result != expected:
                new_phrase_rules[phrase] = expected
                rules_added += 1
                if rules_added <= 10:  # 只显示前10个
                    print(f"  + \"{phrase}\" → \"{expected}\" (出现{count}次, OpenCC转为:{opencc_result})")

        if rules_added > 10:
            print(f"  ... 共{rules_added}条规则")

    print("\n" + "="*80)
    print(f"共生成 {len(new_phrase_rules)} 条词组规则")
    print("="*80)

    # 保存扩展规则
    output_file = Path('/home/baojie/work/knowledge/shiji-kb/doc/spec/单字扩展为词组规则.json')
    output_file.write_text(json.dumps(new_phrase_rules, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n已保存到: {output_file}")

    # 创建v3.0-expanded版本（移除单字规则，添加词组规则）
    v3_expanded = {}

    # 保留所有非单字规则
    for key, value in v3_variants.items():
        if len(key) > 1:
            v3_expanded[key] = value

    # 添加新的词组规则
    v3_expanded.update(new_phrase_rules)

    print(f"\n生成v3.0-expanded:")
    print(f"  移除单字规则: {len(single_char_rules)} 条")
    print(f"  添加词组规则: {len(new_phrase_rules)} 条")
    print(f"  总规则数: {len(v3_variants)} → {len(v3_expanded)}")

    expanded_file = Path('/home/baojie/work/knowledge/shiji-kb/docs/data/custom-variants-v3-expanded.json')
    expanded_file.write_text(json.dumps(v3_expanded, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n已保存到: {expanded_file}")

if __name__ == '__main__':
    main()
