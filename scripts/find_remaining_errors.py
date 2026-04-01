#!/usr/bin/env python3
"""
找出OpenCC转换中剩余的错误用例
分析除"后"字外的其他一对多映射字符的错误转换
"""

import json
from pathlib import Path
from opencc import OpenCC
from collections import defaultdict
import re

def load_shiji_text():
    """加载所有史记文本"""
    archive_dir = Path('/home/baojie/work/knowledge/shiji-kb/archive')
    all_text = ""
    for txt_file in sorted(archive_dir.glob('史记*.txt')):
        all_text += txt_file.read_text(encoding='utf-8')
    return all_text

def load_custom_variants():
    """加载现有自定义词库（v2.0）"""
    variants_file = Path('/home/baojie/work/knowledge/shiji-kb/docs/data/custom-variants-v2.json')
    if variants_file.exists():
        return json.loads(variants_file.read_text(encoding='utf-8'))
    return {}

def load_mapping_data():
    """加载繁简映射数据"""
    data_file = Path('/home/baojie/work/knowledge/shiji-kb/doc/spec/DATA_繁简映射.json')
    return json.loads(data_file.read_text(encoding='utf-8'))

def extract_context(text, pos, context_len=10):
    """提取上下文"""
    start = max(0, pos - context_len)
    end = min(len(text), pos + context_len + 1)
    return text[start:end]

def analyze_character_errors(text, char, custom_variants):
    """分析单个字符的错误转换"""
    cc = OpenCC('s2t')
    errors = []

    # 找出所有该字符的位置
    for match in re.finditer(re.escape(char), text):
        pos = match.start()

        # 提取上下文（前后各5字）
        context_start = max(0, pos - 5)
        context_end = min(len(text), pos + 6)
        context = text[context_start:context_end]

        # OpenCC转换
        converted_context = cc.convert(context)
        char_pos_in_context = pos - context_start

        if char_pos_in_context < len(converted_context):
            converted_char = converted_context[char_pos_in_context]

            # 检查是否被自定义词库覆盖
            is_covered = False
            for phrase, correct_trad in custom_variants.items():
                if phrase in context:
                    # 检查该phrase中的目标字符位置
                    phrase_start = context.find(phrase)
                    if phrase_start != -1:
                        char_pos_in_phrase = char_pos_in_context - phrase_start
                        if 0 <= char_pos_in_phrase < len(phrase) and phrase[char_pos_in_phrase] == char:
                            is_covered = True
                            break

            if not is_covered:
                # 提取更大的上下文用于展示（前后各15字）
                display_context = extract_context(text, pos, 15)
                errors.append({
                    'char': char,
                    'context': display_context,
                    'converted': converted_char,
                    'position': pos
                })

    return errors

def analyze_specific_character_patterns(char, errors):
    """分析特定字符的错误模式，生成词库规则建议"""

    # 按转换结果分组
    by_conversion = defaultdict(list)
    for error in errors:
        by_conversion[error['converted']].append(error['context'])

    suggestions = []

    # 特殊字符规则
    if char == '于':
        # 姓氏"于"应保持"于"
        patterns = [
            r'于[定单仲]',  # 于定国、于单、于仲
            r'于丹',
            r'相于'  # "相于定"
        ]
        for pattern in patterns:
            for error in errors:
                if re.search(pattern, error['context']):
                    # 提取匹配的短语
                    match = re.search(pattern, error['context'])
                    if match:
                        phrase = match.group()
                        suggestions.append({
                            'phrase': phrase,
                            'reason': '姓氏应保持"于"'
                        })

    elif char == '发':
        # "头发"相关应转"髮"
        hair_patterns = [
            r'\w发',  # X发（头发、毛发等）
            r'发\w冠',  # 发X冠
        ]
        for pattern in hair_patterns:
            for error in errors:
                if re.search(pattern, error['context']):
                    match = re.search(pattern, error['context'])
                    if match:
                        phrase = match.group()
                        if phrase not in ['出发', '发兵', '发使']:  # 排除非头发义
                            suggestions.append({
                                'phrase': phrase,
                                'reason': '头发义应转"髮"'
                            })

    elif char == '历':
        # "历法"相关应转"曆"
        calendar_patterns = [
            r'历\w',  # 历X（历法相关）
            r'\w历',
        ]
        for pattern in calendar_patterns:
            for error in errors:
                if re.search(pattern, error['context']):
                    match = re.search(pattern, error['context'])
                    if match:
                        phrase = match.group()
                        # 排除"经历"义
                        if phrase not in ['经历', '历任', '历代']:
                            suggestions.append({
                                'phrase': phrase,
                                'reason': '历法义应转"曆"'
                            })

    return suggestions

def main():
    print("加载史记文本...")
    text = load_shiji_text()
    print(f"总字符数: {len(text):,}")

    print("\n加载现有自定义词库...")
    custom_variants = load_custom_variants()
    print(f"已有规则数: {len(custom_variants)}")

    print("\n加载繁简映射数据...")
    mapping_data = load_mapping_data()
    one_to_many = mapping_data['one_to_many']
    frequency = mapping_data['frequency']

    # 排除已完全覆盖的字符
    excluded_chars = {'后', '复', '夫', '欲', '周', '家', '梁', '里'}  # 后已完全覆盖，其他OpenCC正确

    # 重点分析的低频字符（根据错误率分析）
    focus_chars = ['于', '发', '历']  # 已知有错误的字符

    print("\n" + "="*80)
    print("分析剩余错误...")
    print("="*80)

    all_suggestions = {}
    total_errors = 0

    for char in focus_chars:
        if char not in one_to_many:
            continue

        print(f"\n分析字符: {char} (频率: {frequency.get(char, 0)})")
        print("-" * 80)

        errors = analyze_character_errors(text, char, custom_variants)
        total_errors += len(errors)

        print(f"发现 {len(errors)} 处未覆盖的使用")

        if errors:
            # 显示前10个错误案例
            print("\n错误案例（前10个）:")
            for i, error in enumerate(errors[:10], 1):
                print(f"{i}. {error['context']} → {error['converted']}")

            # 分析模式并生成建议
            suggestions = analyze_specific_character_patterns(char, errors)
            if suggestions:
                all_suggestions[char] = suggestions
                print(f"\n生成 {len(suggestions)} 条规则建议")

    # 现在分析所有其他低频字符
    print("\n" + "="*80)
    print("分析其他低频一对多字符...")
    print("="*80)

    other_chars = [c for c in one_to_many.keys()
                   if c not in excluded_chars and c not in focus_chars]

    # 按频率排序
    other_chars_sorted = sorted(other_chars, key=lambda c: frequency.get(c, 0), reverse=True)

    for char in other_chars_sorted[:20]:  # 只看前20个低频字符
        freq = frequency.get(char, 0)
        if freq < 50:  # 频率太低的跳过
            continue

        print(f"\n检查字符: {char} (频率: {freq})")
        errors = analyze_character_errors(text, char, custom_variants)

        if errors:
            total_errors += len(errors)
            print(f"  发现 {len(errors)} 处潜在错误")
            # 显示2个案例
            for error in errors[:2]:
                print(f"    {error['context']}")

    print("\n" + "="*80)
    print(f"总计发现未覆盖用例: {total_errors}")
    print("="*80)

    # 保存建议
    if all_suggestions:
        output_file = Path('/home/baojie/work/knowledge/shiji-kb/doc/spec/DATA_低频字符词库规则.json')
        output_file.write_text(json.dumps(all_suggestions, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n规则建议已保存到: {output_file}")

if __name__ == '__main__':
    main()
