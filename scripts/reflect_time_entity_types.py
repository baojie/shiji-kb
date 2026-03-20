#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间实体类型错误广泛反思

使用AI对所有时间标注进行审查，检测：
1. 被误标为时间的非时间实体
2. 应该是时间但未标注的
3. 时间标注的边界问题

用法：
  python scripts/reflect_time_entity_types.py --all
  python scripts/reflect_time_entity_types.py --chapter 001
"""

import re
import json
import argparse
from pathlib import Path
from collections import defaultdict, Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = PROJECT_ROOT / 'chapter_md'
OUTPUT_FILE = PROJECT_ROOT / 'logs' / 'time_entity_reflection_report.json'

# 时间特征分类
TIME_FEATURES = {
    '年份': ['年', '载'],
    '月份': ['月', '正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月', '闰月'],
    '日期': ['日', '朔', '望', '晦'],
    '季节': ['春', '夏', '秋', '冬'],
    '干支': ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸', '子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'],
    '纪元': ['元', '元年', '初', '建元', '太初', '元鼎', '元封', '元狩', '元朔', '征和'],
    '时辰': ['朝', '夕', '夜', '晨', '暮', '旦', '昏', '时', '刻'],
    '相对时间': ['前', '后', '先', '今', '昔', '往', '来', '将', '既'],
}

# 非时间指示词
NON_TIME_INDICATORS = {
    '度量单位': ['石', '尺', '寸', '斤', '两', '蹄', '足', '匹', '驷'],
    '物品': ['章', '篇', '卷', '社', '车', '马'],
    '行政': ['郡', '县', '国', '家', '户', '里'],
    '人群': ['人', '辈', '众'],
    '事物': ['事', '物', '器'],
}


def extract_all_time_entities():
    """提取所有时间标注"""
    all_entities = defaultdict(list)
    pattern = re.compile(r'〖%([^〗]+)〗')

    for fpath in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        chapter = fpath.stem.replace('.tagged', '')
        content = fpath.read_text(encoding='utf-8')

        for match in pattern.finditer(content):
            entity = match.group(1)
            # 获取上下文（前后各20字）
            start = max(0, match.start() - 20)
            end = min(len(content), match.end() + 20)
            context = content[start:end].replace('\n', ' ')

            all_entities[entity].append({
                'chapter': chapter,
                'pos': match.start(),
                'context': context
            })

    return all_entities


def classify_entity(entity):
    """分类时间实体"""
    features = []

    for category, indicators in TIME_FEATURES.items():
        if any(ind in entity for ind in indicators):
            features.append(category)

    non_time_features = []
    for category, indicators in NON_TIME_INDICATORS.items():
        if any(ind in entity for ind in indicators):
            non_time_features.append(category)

    return {
        'time_features': features,
        'non_time_features': non_time_features,
        'is_suspicious': len(non_time_features) > 0 and len(features) == 0
    }


def analyze_entities():
    """分析所有时间实体"""
    print("正在提取所有时间标注...")
    entities = extract_all_time_entities()

    print(f"共提取 {len(entities)} 种不同的时间表达")
    print(f"总出现次数：{sum(len(occs) for occs in entities.values())}")

    # 分类分析
    results = {
        'total_unique': len(entities),
        'total_occurrences': sum(len(occs) for occs in entities.values()),
        'categories': defaultdict(list),
        'suspicious': [],
        'pure_time': [],
        'mixed': [],
    }

    for entity, occurrences in entities.items():
        classification = classify_entity(entity)
        count = len(occurrences)

        record = {
            'entity': entity,
            'count': count,
            'time_features': classification['time_features'],
            'non_time_features': classification['non_time_features'],
            'examples': occurrences[:3]  # 保留前3个示例
        }

        # 分类
        if classification['is_suspicious']:
            results['suspicious'].append(record)
        elif classification['non_time_features']:
            results['mixed'].append(record)
        else:
            results['pure_time'].append(record)

        # 按时间特征分类
        for feat in classification['time_features']:
            results['categories'][feat].append((entity, count))

    # 排序
    results['suspicious'].sort(key=lambda x: x['count'], reverse=True)
    results['mixed'].sort(key=lambda x: x['count'], reverse=True)
    results['pure_time'].sort(key=lambda x: x['count'], reverse=True)

    return results


def generate_report(results):
    """生成分析报告"""
    report = []

    report.append("=" * 80)
    report.append("时间实体类型广泛反思报告")
    report.append("=" * 80)
    report.append("")

    report.append(f"总体统计：")
    report.append(f"  - 不同时间表达：{results['total_unique']} 种")
    report.append(f"  - 总出现次数：{results['total_occurrences']} 次")
    report.append(f"  - 可疑标注：{len(results['suspicious'])} 种")
    report.append(f"  - 混合特征：{len(results['mixed'])} 种")
    report.append(f"  - 纯时间表达：{len(results['pure_time'])} 种")
    report.append("")

    # 可疑标注（应该不是时间）
    if results['suspicious']:
        report.append("=" * 80)
        report.append(f"可疑标注（共 {len(results['suspicious'])} 种，可能不是时间）")
        report.append("=" * 80)
        report.append("")

        for i, rec in enumerate(results['suspicious'][:50], 1):
            report.append(f"{i}. 〖%{rec['entity']}〗 (出现 {rec['count']} 次)")
            report.append(f"   非时间特征：{', '.join(rec['non_time_features'])}")
            if rec['examples']:
                report.append(f"   示例：{rec['examples'][0]['chapter']}")
                report.append(f"   上下文：{rec['examples'][0]['context'][:60]}")
            report.append("")

    # 混合特征（需要人工审查）
    if results['mixed']:
        report.append("=" * 80)
        report.append(f"混合特征标注（共 {len(results['mixed'])} 种，需人工审查）")
        report.append("=" * 80)
        report.append("")

        for i, rec in enumerate(results['mixed'][:30], 1):
            report.append(f"{i}. 〖%{rec['entity']}〗 (出现 {rec['count']} 次)")
            report.append(f"   时间特征：{', '.join(rec['time_features']) if rec['time_features'] else '无'}")
            report.append(f"   非时间特征：{', '.join(rec['non_time_features'])}")
            report.append("")

    # 按类型分布
    report.append("=" * 80)
    report.append("时间类型分布")
    report.append("=" * 80)
    report.append("")

    for category, items in sorted(results['categories'].items()):
        total = sum(count for _, count in items)
        report.append(f"{category}: {len(items)} 种表达，{total} 次出现")
        top_5 = sorted(items, key=lambda x: x[1], reverse=True)[:5]
        for entity, count in top_5:
            report.append(f"  - {entity} ({count}次)")
        report.append("")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='时间实体类型广泛反思')
    parser.add_argument('--all', action='store_true', help='分析所有章节')
    parser.add_argument('--chapter', help='分析特定章节')
    args = parser.parse_args()

    if not (args.all or args.chapter):
        parser.print_help()
        return

    results = analyze_entities()

    # 生成报告
    report = generate_report(results)
    print(report)

    # 保存JSON结果
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n详细结果已保存到：{OUTPUT_FILE}")

    # 保存Markdown报告
    md_file = OUTPUT_FILE.with_suffix('.md')
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Markdown报告已保存到：{md_file}")


if __name__ == '__main__':
    main()
