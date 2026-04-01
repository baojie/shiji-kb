#!/usr/bin/env python3
"""
创建v3.0自定义词库
合并v2.0和新发现的规则，处理冲突
"""

import json
from pathlib import Path
from collections import OrderedDict

def main():
    # 加载v2.0词库
    v2_file = Path('/home/baojie/work/knowledge/shiji-kb/docs/data/custom-variants-v2.json')
    v2_variants = json.loads(v2_file.read_text(encoding='utf-8'))
    print(f"v2.0词库: {len(v2_variants)} 条规则")

    # 加载新规则
    new_file = Path('/home/baojie/work/knowledge/shiji-kb/doc/spec/DATA_新增词库规则v3.0.json')
    new_variants = json.loads(new_file.read_text(encoding='utf-8'))
    print(f"新规则: {len(new_variants)} 条")

    # 合并规则（有序字典，保持顺序）
    v3_variants = OrderedDict()

    # 问题：v2.0中的 "于": "於" 规则会导致所有"于"转为"於"
    # 但我们需要姓氏"于"保持不变
    # 解决方案：删除通用规则，只保留特定上下文规则

    print("\n处理规则...")

    # 先添加"后"字相关规则（v2.0的核心）
    hou_rules = {}
    for key, value in v2_variants.items():
        if '后' in key:
            hou_rules[key] = value

    print(f"- 保留'后'字规则: {len(hou_rules)} 条")
    v3_variants.update(hou_rules)

    # "发"字规则：合并v2.0和新规则
    fa_rules = {}
    for key, value in v2_variants.items():
        if '发' in key:
            fa_rules[key] = value
    for key, value in new_variants.items():
        if '发' in key and key not in fa_rules:
            fa_rules[key] = value

    print(f"- 合并'发'字规则: {len(fa_rules)} 条")
    v3_variants.update(fa_rules)

    # "历"字规则：合并（v2.0已有，新规则补充）
    li_rules = {}
    for key, value in v2_variants.items():
        if '历' in key:
            li_rules[key] = value
    for key, value in new_variants.items():
        if '历' in key and key not in li_rules:
            li_rules[key] = value

    print(f"- 合并'历'字规则: {len(li_rules)} 条")
    v3_variants.update(li_rules)

    # "于"字规则：**移除通用规则**，只保留特定词组
    # v2.0中的问题规则：
    # "于": "於",  ← 这条会导致姓氏"于"错误转换，必须删除
    # "于今": "於今", ← 这些特定词组规则可以保留
    # "于是": "於是",

    yu_rules = {}
    # 保留v2.0中的特定词组（不含单字"于"）
    for key, value in v2_variants.items():
        if '于' in key and key != '于':  # 排除单字"于"
            yu_rules[key] = value

    # 添加姓氏"于"的规则（保持不变）
    for key, value in new_variants.items():
        if '于' in key:
            yu_rules[key] = value

    print(f"- 修正'于'字规则: {len(yu_rules)} 条（移除了通用规则 '于': '於'）")
    v3_variants.update(yu_rules)

    # 其他规则（即、原、措、琅等）
    # 但要排除单字"于"规则
    other_rules = {}
    for key, value in v2_variants.items():
        if key not in v3_variants and key != '于':  # 排除单字"于"
            other_rules[key] = value

    print(f"- 保留其他规则: {len(other_rules)} 条")
    v3_variants.update(other_rules)

    print(f"\nv3.0总计: {len(v3_variants)} 条规则")

    # 保存v3.0
    v3_file = Path('/home/baojie/work/knowledge/shiji-kb/docs/data/custom-variants-v3.json')
    v3_file.write_text(json.dumps(v3_variants, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n已保存到: {v3_file}")

    # 生成变更报告
    print("\n" + "="*80)
    print("v2.0 → v3.0 变更")
    print("="*80)

    print("\n🗑️  移除的规则:")
    for key in v2_variants:
        if key not in v3_variants:
            print(f'  - "{key}": "{v2_variants[key]}" (原因: 过于通用，导致错误)')

    print("\n➕ 新增的规则:")
    for key in v3_variants:
        if key not in v2_variants:
            print(f'  + "{key}": "{v3_variants[key]}"')

    print(f"\n总结:")
    print(f"  v2.0: {len(v2_variants)} 条")
    print(f"  v3.0: {len(v3_variants)} 条")
    print(f"  净增: {len(v3_variants) - len(v2_variants)} 条")

if __name__ == '__main__':
    main()
