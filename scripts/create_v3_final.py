#!/usr/bin/env python3
"""
创建最终的v3.0词库
移除：
1. 单字"于"规则（过于通用）
2. 4个错误的单字规则：即、原、措、琅（OpenCC已正确处理）

添加：
- 姓氏"于"的词组规则
- "发"字头发义规则
- "历"字历法义规则
"""

import json
from pathlib import Path
from collections import OrderedDict

def main():
    # 加载v2.0
    v2_file = Path('/home/baojie/work/knowledge/shiji-kb/docs/data/custom-variants-v2.json')
    v2_variants = json.loads(v2_file.read_text(encoding='utf-8'))

    # 加载新规则
    new_file = Path('/home/baojie/work/knowledge/shiji-kb/doc/spec/DATA_新增词库规则v3.0.json')
    new_variants = json.loads(new_file.read_text(encoding='utf-8'))

    print("="*80)
    print("创建v3.0最终版本")
    print("="*80)

    print(f"\nv2.0词库: {len(v2_variants)} 条")
    print(f"新规则: {len(new_variants)} 条")

    # 需要移除的规则
    rules_to_remove = {
        '于',    # 通用规则，导致姓氏错误
        '即',    # OpenCC已正确
        '原',    # OpenCC已正确（否则"平原"会错转为"平願"）
        '措',    # OpenCC已正确
        '琅',    # OpenCC已正确
    }

    print(f"\n移除 {len(rules_to_remove)} 个问题规则:")
    for rule in rules_to_remove:
        if rule in v2_variants:
            print(f'  - "{rule}": "{v2_variants[rule]}"')

    # 创建v3.0
    v3_variants = OrderedDict()

    # 保留v2.0中的非问题规则
    for key, value in v2_variants.items():
        if key not in rules_to_remove:
            v3_variants[key] = value

    # 添加新规则
    for key, value in new_variants.items():
        if key not in v3_variants:
            v3_variants[key] = value

    print(f"\n新增 {len(new_variants)} 条规则:")
    for key, value in new_variants.items():
        print(f'  + "{key}": "{value}"')

    print(f"\nv3.0总计: {len(v3_variants)} 条规则")
    print(f"变化: {len(v2_variants)} → {len(v3_variants)} (移除{len(rules_to_remove)}条, 新增{len(new_variants)}条)")

    # 保存v3.0
    v3_file = Path('/home/baojie/work/knowledge/shiji-kb/docs/data/custom-variants-v3.json')
    v3_file.write_text(json.dumps(v3_variants, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n已保存到: {v3_file}")

    # 分类统计
    print("\n" + "="*80)
    print("规则分类统计")
    print("="*80)

    categories = {
        '后字规则': 0,
        '发字规则': 0,
        '历字规则': 0,
        '于字规则': 0,
        '其他规则': 0,
    }

    for key in v3_variants:
        if '后' in key:
            categories['后字规则'] += 1
        elif '发' in key:
            categories['发字规则'] += 1
        elif '历' in key:
            categories['历字规则'] += 1
        elif '于' in key:
            categories['于字规则'] += 1
        else:
            categories['其他规则'] += 1

    for cat, count in categories.items():
        print(f"  {cat}: {count} 条")

if __name__ == '__main__':
    main()
