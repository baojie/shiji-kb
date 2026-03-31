#!/usr/bin/env python3
"""
找出真实的OpenCC错误
区分：
1. "于"字：只有姓氏用法是错误（应保持"于"），介词用法转"於"是正确的
2. "发"字：只有头发义转"發"是错误（应转"髮"），其他转"發"是正确的
3. "历"字：只有历法义转"歷"是错误（应转"曆"），经历义转"歷"是正确的
4. 其他低频字符：需要根据具体上下文判断
"""

import json
from pathlib import Path
from opencc import OpenCC
from collections import defaultdict, Counter
import re

def load_shiji_text():
    """加载所有史记文本"""
    archive_dir = Path('/home/baojie/work/knowledge/shiji-kb/archive')
    all_text = ""
    for txt_file in sorted(archive_dir.glob('史记*.txt')):
        all_text += txt_file.read_text(encoding='utf-8')
    return all_text

def find_surname_yu(text):
    """找出"于"作为姓氏的用法（真实错误）"""
    cc = OpenCC('s2t')
    errors = []

    # 姓氏"于"的模式
    # 1. 于+单字名（于定、于单等）
    # 2. 于+双字名（于定国等）
    patterns = [
        r'于定国',  # 最常见
        r'于定',
        r'于单',
        r'相于',  # "相于定"中的姓氏
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            phrase = match.group()
            pos = match.start()

            # 检查OpenCC转换
            converted = cc.convert(phrase)
            if '於' in converted:  # 如果转为"於"就是错误
                context = text[max(0, pos-10):min(len(text), pos+20)]
                errors.append({
                    'char': '于',
                    'phrase': phrase,
                    'context': context,
                    'wrong_conversion': converted,
                    'correct': phrase.replace('于', '于'),  # 应保持"于"
                    'reason': '姓氏应保持"于"'
                })

    return errors

def find_hair_fa(text):
    """找出"发"作为头发义的用法（真实错误）"""
    cc = OpenCC('s2t')
    errors = []

    # 头发相关的明确词汇
    hair_phrases = [
        '头发', '须发', '发上', '发指', '白发', '鬓发',
        '剪发', '理发', '剃发', '披发', '散发', '束发',
        '毛发', '黑发', '断发', '长发', '短发'
    ]

    for phrase in hair_phrases:
        for match in re.finditer(re.escape(phrase), text):
            found_phrase = match.group()
            pos = match.start()

            # 检查OpenCC转换
            converted = cc.convert(found_phrase)
            # 如果转为"發"就是错误（应该转"髮"）
            if '發' in converted and '髮' not in converted:
                context = text[max(0, pos-10):min(len(text), pos+20)]
                correct = found_phrase.replace('发', '髮')
                errors.append({
                    'char': '发',
                    'phrase': found_phrase,
                    'context': context,
                    'wrong_conversion': converted,
                    'correct': correct,
                    'reason': '头发义应转"髮"'
                })

    return errors

def find_calendar_li(text):
    """找出"历"作为历法义的用法（真实错误）"""
    cc = OpenCC('s2t')
    errors = []

    # 历法相关的明确词汇
    calendar_phrases = [
        '历日', '历数', '历法', '太初历', '颛顼历', '夏历',
        '历书', '历象', '历度'
    ]

    for phrase in calendar_phrases:
        for match in re.finditer(re.escape(phrase), text):
            found_phrase = match.group()
            pos = match.start()

            # 检查OpenCC转换
            converted = cc.convert(found_phrase)
            # 如果转为"歷"就是错误（应该转"曆"）
            if '歷' in converted and '曆' not in converted:
                context = text[max(0, pos-10):min(len(text), pos+20)]
                correct = found_phrase.replace('历', '曆')
                errors.append({
                    'char': '历',
                    'phrase': found_phrase,
                    'context': context,
                    'wrong_conversion': converted,
                    'correct': correct,
                    'reason': '历法义应转"曆"'
                })

    return errors

def find_other_character_errors(text):
    """找出其他低频字符的明确错误"""
    cc = OpenCC('s2t')
    errors = defaultdict(list)

    # 根据《史记》的实际用法定义错误规则
    error_rules = {
        # 人名、地名中的特殊用法
        '广': [
            ('广汉', '廣漢'),  # 地名不应转，但OpenCC可能转
        ],
        '辟': [
            ('复辟', '復辟'),  # 应该是"辟"不是"闢"
        ],
        '云': [
            ('云梦', '雲夢'),  # 地名，应该保持"云"可能更好
        ],
    }

    for char, rules in error_rules.items():
        for simp_phrase, expected_trad in rules:
            for match in re.finditer(re.escape(simp_phrase), text):
                found_phrase = match.group()
                pos = match.start()

                converted = cc.convert(found_phrase)
                if converted != expected_trad:  # 如果转换结果不符合预期
                    context = text[max(0, pos-10):min(len(text), pos+20)]
                    errors[char].append({
                        'phrase': found_phrase,
                        'context': context,
                        'wrong_conversion': converted,
                        'correct': expected_trad,
                        'reason': '专有名词特殊用法'
                    })

    return errors

def main():
    print("加载史记文本...")
    text = load_shiji_text()
    print(f"总字符数: {len(text):,}\n")

    print("="*80)
    print("分析真实错误（OpenCC转换不符合《史记》用法的情况）")
    print("="*80)

    all_errors = {}
    total_count = 0

    # 1. "于"字姓氏错误
    print('\n1. 分析"于"字姓氏用法...')
    yu_errors = find_surname_yu(text)
    if yu_errors:
        all_errors['于'] = yu_errors
        total_count += len(yu_errors)
        print(f"   发现 {len(yu_errors)} 处错误")
        print(f"   示例：")
        for error in yu_errors[:5]:
            print(f"     - {error['phrase']} (错转: {error['wrong_conversion']}) → 应保持: {error['correct']}")

    # 2. "发"字头发义错误
    print('\n2. 分析"发"字头发义用法...')
    fa_errors = find_hair_fa(text)
    if fa_errors:
        all_errors['发'] = fa_errors
        total_count += len(fa_errors)
        print(f"   发现 {len(fa_errors)} 处错误")

        # 统计哪些词组出现频率高
        phrase_count = Counter([e['phrase'] for e in fa_errors])
        print(f"   高频错误词组：")
        for phrase, count in phrase_count.most_common(10):
            print(f"     - {phrase}: {count}次")

    # 3. "历"字历法义错误
    print('\n3. 分析"历"字历法义用法...')
    li_errors = find_calendar_li(text)
    if li_errors:
        all_errors['历'] = li_errors
        total_count += len(li_errors)
        print(f"   发现 {len(li_errors)} 处错误")

        phrase_count = Counter([e['phrase'] for e in li_errors])
        print(f"   高频错误词组：")
        for phrase, count in phrase_count.most_common(10):
            print(f"     - {phrase}: {count}次")

    # 4. 其他字符错误
    print('\n4. 分析其他字符...')
    other_errors = find_other_character_errors(text)
    for char, errors in other_errors.items():
        if errors:
            all_errors[char] = errors
            total_count += len(errors)
            print(f'   "{char}"字: {len(errors)} 处错误')

    print("\n" + "="*80)
    print(f"总计真实错误: {total_count} 处")
    print("="*80)

    # 生成词库规则建议
    print("\n生成自定义词库规则...")
    custom_variants = {}

    for char, errors in all_errors.items():
        # 统计哪些phrase最常见
        phrase_count = Counter([e['phrase'] for e in errors])

        # 为每个phrase生成规则
        for phrase, count in phrase_count.items():
            # 获取正确的繁体形式
            correct = errors[0]['correct']  # 从第一个错误中获取
            for e in errors:
                if e['phrase'] == phrase:
                    correct = e['correct']
                    break

            custom_variants[phrase] = correct
            print(f'  "{phrase}": "{correct}" (出现 {count} 次)')

    print(f"\n共生成 {len(custom_variants)} 条规则")

    # 保存结果
    output_file = Path('/home/baojie/work/knowledge/shiji-kb/doc/spec/真实错误分析.json')
    output_data = {
        'total_errors': total_count,
        'errors_by_char': {char: len(errors) for char, errors in all_errors.items()},
        'custom_variants': custom_variants,
        'detailed_errors': {
            char: [
                {
                    'phrase': e['phrase'],
                    'wrong': e['wrong_conversion'],
                    'correct': e['correct'],
                    'reason': e['reason'],
                    'example': e['context']
                }
                for e in errors[:10]  # 每个字符只保存前10个案例
            ]
            for char, errors in all_errors.items()
        }
    }

    output_file.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n详细分析已保存到: {output_file}")

    # 保存词库规则
    variants_file = Path('/home/baojie/work/knowledge/shiji-kb/doc/spec/新增词库规则v3.0.json')
    variants_file.write_text(json.dumps(custom_variants, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"词库规则已保存到: {variants_file}")

if __name__ == '__main__':
    main()
