#!/usr/bin/env python3
"""
验证v3.0词库是否覆盖了所有183个真实错误
"""

import json
from pathlib import Path
from opencc import OpenCC

def apply_custom_variants(text, variants_dict):
    """
    应用自定义词库规则
    注意：OpenCC的词库是按最长匹配优先的，我们需要模拟这个行为
    """
    result = text
    # 按键长度降序排序，优先匹配长词组
    sorted_items = sorted(variants_dict.items(), key=lambda x: len(x[0]), reverse=True)

    for simp, trad in sorted_items:
        result = result.replace(simp, trad)

    return result

def main():
    # 加载错误分析数据
    errors_file = Path('/home/baojie/work/knowledge/shiji-kb/doc/spec/DATA_真实错误分析.json')
    errors_data = json.loads(errors_file.read_text(encoding='utf-8'))

    # 加载v3.0词库
    v3_file = Path('/home/baojie/work/knowledge/shiji-kb/docs/data/custom-variants-v3.json')
    v3_variants = json.loads(v3_file.read_text(encoding='utf-8'))

    print("="*80)
    print("验证v3.0词库覆盖率")
    print("="*80)

    print(f"\n总错误数: {errors_data['total_errors']}")
    print(f"v3.0规则数: {len(v3_variants)}\n")

    cc = OpenCC('s2t')

    total_errors = 0
    covered_errors = 0
    uncovered_errors = []

    # 检查每个字符的错误
    for char, errors in errors_data['detailed_errors'].items():
        print(f"\n字符: {char}")
        print(f"错误数: {len(errors)}")

        char_covered = 0
        char_uncovered = []

        for error in errors:
            phrase = error['phrase']
            wrong = error['wrong']
            correct = error['correct']

            total_errors += 1

            # 模拟OpenCC + custom variants的转换过程
            # 1. 先OpenCC转换
            opencc_result = cc.convert(phrase)

            # 2. 再应用自定义词库
            final_result = apply_custom_variants(phrase, v3_variants)

            # 检查是否修复
            if final_result == correct:
                char_covered += 1
                covered_errors += 1
            else:
                char_uncovered.append({
                    'phrase': phrase,
                    'expected': correct,
                    'got': final_result,
                    'opencc': opencc_result
                })

        print(f"  覆盖: {char_covered}/{len(errors)} ({char_covered/len(errors)*100:.1f}%)")

        if char_uncovered:
            print(f"  未覆盖案例:")
            for uc in char_uncovered[:5]:  # 只显示前5个
                print(f"    - '{uc['phrase']}' → 期望:{uc['expected']} 实际:{uc['got']} (OpenCC:{uc['opencc']})")

        uncovered_errors.extend(char_uncovered)

    print("\n" + "="*80)
    print(f"总体覆盖率: {covered_errors}/{total_errors} = {covered_errors/total_errors*100:.2f}%")
    print("="*80)

    if uncovered_errors:
        print(f"\n⚠️  发现 {len(uncovered_errors)} 个未覆盖的错误")
        print("\n建议补充的规则:")

        # 统计未覆盖的phrase
        from collections import Counter
        phrase_count = Counter([uc['phrase'] for uc in uncovered_errors])

        for phrase, count in phrase_count.most_common(20):
            # 找到对应的正确转换
            correct = None
            for uc in uncovered_errors:
                if uc['phrase'] == phrase:
                    correct = uc['expected']
                    break

            if correct:
                print(f'  "{phrase}": "{correct}"  # 出现{count}次')
    else:
        print("\n✅ 所有错误均已覆盖！")

if __name__ == '__main__':
    main()
