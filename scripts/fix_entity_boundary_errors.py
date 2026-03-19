#!/usr/bin/env python3
"""
实体边界错误修复脚本 - 综合反思版本

基于启发式规则修复真正的边界切分错误
"""

import re
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 目录
CHAPTER_DIR = Path('chapter_md')
BACKUP_DIR = Path('backups') / f'boundary_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
LOG_DIR = Path('logs')

# 修复规则 - 基于语义和上下文的启发式规则
BOUNDARY_FIX_RULES = [
    {
        'name': '诸侯服边界错误',
        'pattern': r'诸〖\^侯服〗',
        'replacement': '〖#诸侯〗服',
        'desc': '"诸侯服秦"误标为"诸+侯服制度"，应为"诸侯+服"',
        'examples': ['诸〖^侯服〗〖\'秦〗 → 〖#诸侯〗服〖\'秦〗']
    },
    {
        'name': '诸侯边界错误',
        'pattern': r'诸〖;侯〗',
        'replacement': '〖#诸侯〗',
        'desc': '"诸侯"（各位诸侯）是身份群体，不是官职',
        'examples': ['诸〖;侯〗 → 〖#诸侯〗']
    },
    {
        'name': '诸将边界错误',
        'pattern': r'诸〖;将〗',
        'replacement': '〖#诸将〗',
        'desc': '"诸将"（各位将领）是身份群体，不是官职',
        'examples': ['诸〖;将〗 → 〖#诸将〗']
    },
    {
        'name': '诸侯王边界错误',
        'pattern': r'诸〖;侯王〗',
        'replacement': '〖#诸侯王〗',
        'desc': '"诸侯王"（各位侯王）是身份群体，不是官职',
        'examples': ['诸〖;侯王〗 → 〖#诸侯王〗']
    },
    {
        'name': '群臣边界错误(#)',
        'pattern': r'群〖#臣〗',
        'replacement': '〖#群臣〗',
        'desc': '"群臣"（所有大臣）是完整词汇，应整体标注',
        'examples': ['群〖#臣〗 → 〖#群臣〗']
    },
    {
        'name': '群臣边界错误(;)',
        'pattern': r'群〖;臣〗',
        'replacement': '〖#群臣〗',
        'desc': '"群臣"是身份群体，不是官职',
        'examples': ['群〖;臣〗 → 〖#群臣〗']
    },
    {
        'name': '群公边界错误',
        'pattern': r'群〖;公〗',
        'replacement': '〖#群公〗',
        'desc': '"群公"（各位公爵）是身份群体',
        'examples': ['群〖;公〗 → 〖#群公〗']
    },
    {
        'name': '群公子边界错误',
        'pattern': r'群〖;公子〗',
        'replacement': '〖#群公子〗',
        'desc': '"群公子"（各位公子）是身份群体',
        'examples': ['群〖;公子〗 → 〖#群公子〗']
    },
    {
        'name': '群弟边界错误',
        'pattern': r'群〖#弟〗',
        'replacement': '〖#群弟〗',
        'desc': '"群弟"（众位兄弟）是完整词汇',
        'examples': ['群〖#弟〗 → 〖#群弟〗']
    },
    {
        'name': '群母边界错误',
        'pattern': r'群〖#母〗',
        'replacement': '〖#群母〗',
        'desc': '"群母"（诸位母亲）是完整词汇',
        'examples': ['群〖#母〗 → 〖#群母〗']
    },
    {
        'name': '入臣边界错误',
        'pattern': r'入〖#臣〗',
        'replacement': '入臣',
        'desc': '"入臣"意为"臣服"，是动词，不应标注为身份',
        'examples': ['入〖#臣〗於X → 入臣於X']
    },
]

def create_backup():
    """创建备份"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    tagged_files = list(CHAPTER_DIR.glob('*.tagged.md'))
    for file in tagged_files:
        shutil.copy2(file, BACKUP_DIR / file.name)

    print(f"✓ 备份创建: {BACKUP_DIR}/")
    print(f"  文件数: {len(tagged_files)}\n")
    return BACKUP_DIR

def apply_boundary_fixes(content, file_name):
    """应用边界修复规则"""
    fixes_applied = []

    for rule in BOUNDARY_FIX_RULES:
        pattern = rule['pattern']
        replacement = rule['replacement']

        # 查找所有匹配
        matches = list(re.finditer(pattern, content))

        if matches:
            # 应用替换
            new_content = re.sub(pattern, replacement, content)

            fixes_applied.append({
                'rule': rule['name'],
                'count': len(matches),
                'matches': [m.group(0) for m in matches],
                'desc': rule['desc']
            })

            content = new_content

    return content, fixes_applied

def process_all_chapters():
    """处理所有章节"""
    LOG_DIR.mkdir(exist_ok=True)

    all_fixes = defaultdict(list)
    chapter_stats = {}

    tagged_files = sorted(CHAPTER_DIR.glob('*.tagged.md'))

    print(f"开始处理 {len(tagged_files)} 个章节...\n")

    for file_path in tagged_files:
        chapter_num = file_path.stem.split('_')[0]

        # 读取内容
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # 应用修复
        new_content, fixes = apply_boundary_fixes(original_content, file_path.name)

        if fixes:
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            total_fixes = sum(f['count'] for f in fixes)
            all_fixes[chapter_num] = fixes
            chapter_stats[chapter_num] = total_fixes

            print(f"✓ {chapter_num} - 修复 {total_fixes} 处边界错误")
            for fix in fixes:
                print(f"    {fix['rule']}: {fix['count']} 处")

    return all_fixes, chapter_stats

def generate_report(all_fixes, chapter_stats, backup_dir):
    """生成修复报告"""
    total_fixes = sum(chapter_stats.values())

    print(f"\n{'='*70}")
    print(f"实体边界错误修复报告")
    print(f"{'='*70}\n")

    print(f"备份目录: {backup_dir}/")
    print(f"总计修复: {total_fixes} 处边界错误")
    print(f"涉及章节: {len(chapter_stats)} 章\n")

    # 按规则类型统计
    rule_stats = defaultdict(int)
    for fixes_list in all_fixes.values():
        for fix in fixes_list:
            rule_stats[fix['rule']] += fix['count']

    print("按修复类型统计:")
    for rule_name, count in sorted(rule_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rule_name}: {count} 处")

    print(f"\n{'='*70}\n")

    # 详细修复日志
    print("详细修复记录:\n")

    for chapter, fixes_list in sorted(all_fixes.items()):
        print(f"章节 {chapter}:")
        for fix in fixes_list:
            print(f"  [{fix['rule']}] {fix['count']} 处")
            print(f"      说明: {fix['desc']}")
            if fix['matches']:
                print(f"      示例: {fix['matches'][0]}")
        print()

    # 保存日志
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = LOG_DIR / 'entity_boundary_fix_log.md'

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n## 边界错误修复 - {timestamp}\n\n")
        f.write(f"- 备份: {backup_dir}/\n")
        f.write(f"- 总计修复: {total_fixes} 处\n")
        f.write(f"- 涉及章节: {len(chapter_stats)} 章\n\n")

        f.write("### 按修复类型统计\n\n")
        for rule_name, count in sorted(rule_stats.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- {rule_name}: {count} 处\n")

        f.write("\n### 详细记录\n\n")
        for chapter, fixes_list in sorted(all_fixes.items()):
            f.write(f"**章节 {chapter}:**\n\n")
            for fix in fixes_list:
                f.write(f"- [{fix['rule']}] {fix['count']} 处\n")
                f.write(f"  - 说明: {fix['desc']}\n")
            f.write("\n")

    print(f"修复日志已保存: {log_file}\n")

def main():
    """主函数"""
    print("="*70)
    print("实体边界错误综合反思与修复")
    print("="*70)
    print()

    # 创建备份
    backup_dir = create_backup()

    # 处理所有章节
    all_fixes, chapter_stats = process_all_chapters()

    if all_fixes:
        # 生成报告
        generate_report(all_fixes, chapter_stats, backup_dir)

        print("✅ 修复完成！")
        print(f"\n如需恢复，请使用备份: {backup_dir}/")
    else:
        print("未发现需要修复的边界错误。")

if __name__ == '__main__':
    main()
