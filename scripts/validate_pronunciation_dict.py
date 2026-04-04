#!/usr/bin/env python3
"""
验证特殊读音词表的完整性和准确性

检查：
1. 每个词条在史记中的实际出现次数
2. 是否有高频但未覆盖的多音字词组
3. pypinyin对这些词条的标注效果
"""

import json
from pathlib import Path
from pypinyin import pinyin, Style
from collections import Counter, defaultdict

# 文件路径
SHIJI_TEXT = Path("corpus/shiji/史记.简体.txt")
DICT_FILE = Path("docs/data/special-pronunciation.json")

def load_data():
    """加载数据"""
    with open(SHIJI_TEXT, 'r', encoding='utf-8') as f:
        shiji_text = f.read()

    with open(DICT_FILE, 'r', encoding='utf-8') as f:
        dict_data = json.load(f)

    return shiji_text, dict_data

def validate_entries(shiji_text, entries):
    """验证词条"""
    results = []

    for entry in entries:
        text = entry['text']
        count = shiji_text.count(text)

        # 测试pypinyin标注
        py = pinyin(text, style=Style.TONE)
        actual_pinyin = [p[0] for p in py]
        expected_pinyin = entry['pinyin']

        is_correct = actual_pinyin == expected_pinyin

        results.append({
            'text': text,
            'count': count,
            'expected': ' '.join(expected_pinyin),
            'actual': ' '.join(actual_pinyin),
            'is_correct': is_correct,
            'context': entry['context']
        })

    return results

def main():
    print("=" * 80)
    print("特殊读音词表验证报告")
    print("=" * 80)

    # 加载数据
    print("\n📖 加载数据...")
    shiji_text, dict_data = load_data()
    entries = dict_data['entries']

    print(f"  词表版本：v{dict_data['version']}")
    print(f"  更新日期：{dict_data['lastUpdated']}")
    print(f"  词条总数：{len(entries)}")

    # 验证词条
    print("\n🔍 验证词条...")
    results = validate_entries(shiji_text, entries)

    # 统计
    total = len(results)
    has_occurrence = sum(1 for r in results if r['count'] > 0)
    no_occurrence = sum(1 for r in results if r['count'] == 0)
    correct_pinyin = sum(1 for r in results if r['is_correct'])
    incorrect_pinyin = sum(1 for r in results if not r['is_correct'] and r['count'] > 0)

    print(f"\n📊 验证统计")
    print(f"  词条总数：{total}")
    print(f"  在史记中出现：{has_occurrence} ({has_occurrence/total*100:.1f}%)")
    print(f"  在史记中未出现：{no_occurrence} ({no_occurrence/total*100:.1f}%)")
    print(f"  pypinyin标注正确：{correct_pinyin} ({correct_pinyin/total*100:.1f}%)")
    print(f"  pypinyin标注错误：{incorrect_pinyin}")

    # 按类别统计
    print(f"\n📋 按类别统计")
    category_stats = defaultdict(lambda: {'total': 0, 'has_occ': 0, 'correct': 0})
    for r in results:
        cat = r['context']
        category_stats[cat]['total'] += 1
        if r['count'] > 0:
            category_stats[cat]['has_occ'] += 1
        if r['is_correct']:
            category_stats[cat]['correct'] += 1

    for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]['total'], reverse=True):
        total_cat = stats['total']
        has_occ = stats['has_occ']
        correct = stats['correct']
        print(f"  {cat:12s}: {total_cat:3d}条 | 出现{has_occ:3d}条 | 正确{correct:3d}条")

    # 高频词条
    print(f"\n🔥 高频词条 (Top 20)")
    high_freq = sorted([r for r in results if r['count'] > 0],
                      key=lambda x: x['count'], reverse=True)[:20]
    for i, r in enumerate(high_freq, 1):
        status = "✅" if r['is_correct'] else "❌"
        print(f"  {i:2d}. {status} {r['text']:12s} | {r['count']:4d}次 | {r['context']}")

    # 未出现的词条
    print(f"\n⚠️  未在史记中出现的词条 ({no_occurrence}条)")
    no_occ_entries = [r for r in results if r['count'] == 0]
    if no_occ_entries:
        print("  建议检查这些词条是否需要保留：")
        for r in no_occ_entries[:10]:
            print(f"  - {r['text']:12s} | {r['context']}")
        if len(no_occ_entries) > 10:
            print(f"  ... 还有 {len(no_occ_entries) - 10} 条")

    # pypinyin标注错误的词条
    if incorrect_pinyin > 0:
        print(f"\n❌ pypinyin标注错误的词条 ({incorrect_pinyin}条)")
        incorrect = [r for r in results if not r['is_correct'] and r['count'] > 0]
        for r in incorrect[:10]:
            print(f"  ❌ {r['text']:12s} | 期望: {r['expected']:30s} | 实际: {r['actual']}")

    # 覆盖率评估
    print(f"\n📈 覆盖率评估")
    total_chars = len(shiji_text)
    covered_chars = sum(r['count'] * len(r['text']) for r in results if r['count'] > 0)
    coverage = covered_chars / total_chars * 100

    print(f"  史记总字符数：{total_chars:,}")
    print(f"  词表覆盖字符数：{covered_chars:,}")
    print(f"  覆盖率：{coverage:.3f}%")

    print(f"\n✅ 验证完成！")


if __name__ == "__main__":
    main()
