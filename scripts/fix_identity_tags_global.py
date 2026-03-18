#!/usr/bin/env python3
"""
全局修复所有130章的身份标注错误

基于121章修复脚本，扩展到全局
"""

import re
import shutil
from pathlib import Path
from datetime import datetime

# 目录
CHAPTER_DIR = Path('chapter_md')
BACKUP_DIR = Path('backups') / f'identity_fix_global_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

def create_backup():
    """创建备份"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    tagged_files = list(CHAPTER_DIR.glob('*.tagged.md'))
    for file in tagged_files:
        shutil.copy2(file, BACKUP_DIR / file.name)

    print(f"✓ 备份创建: {BACKUP_DIR}/")
    print(f"  文件数: {len(tagged_files)}")
    return BACKUP_DIR

def fix_identity_tags(content):
    """修复身份标注（与121章相同的逻辑）"""
    changes = []

    # 【优先级1】处理复合词：〖#弟〗〖#子〗 → 〖_弟子〗
    compound_patterns = [
        (r'〖#弟〗〖#子〗', '〖_弟子〗'),
        (r'〖#夫〗〖#子〗', '〖_夫子〗'),  # 夫子=先生
        (r'〖#士〗〖#大夫〗', '〖_士大夫〗'),
    ]

    for pattern, replacement in compound_patterns:
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            changes.append((pattern, replacement, count))

    # 【优先级2】身份称谓
    identity_mappings = [
        '天子', '诸侯', '士', '臣', '民', '夫', '子', '孙', '弟', '父',
        '匹夫', '缙绅', '庶民', '万民', '百姓', '庶人'
    ]

    for entity in identity_mappings:
        pattern = rf'〖#{re.escape(entity)}〗'
        replacement = f'〖_{entity}〗'
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            changes.append((pattern, replacement, count))

    # 【优先级3】官职称谓
    official_mappings = [
        '君', '卿相', '公卿', '大夫', '太后', '太子', '陛下',
        '王', '帝', '上', '主', '天王'
    ]

    for entity in official_mappings:
        pattern = rf'〖#{re.escape(entity)}〗'
        replacement = f'〖;{entity}〗'
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            changes.append((pattern, replacement, count))

    return content, changes

def fix_nested_person_tags(content):
    """修复人名嵌套标注"""
    # 匹配 〖@...〖_/# /;/^...〗...〗
    pattern = r'〖@([^〗]*)〖[_#;^%]([^〗]+)〗([^〗]*)〗'

    def replacer(match):
        prefix, middle, suffix = match.groups()
        full_name = prefix + middle + suffix
        return f'〖@{full_name}〗'

    nested_matches = re.findall(pattern, content)
    new_content = re.sub(pattern, replacer, content)

    return new_content, len(nested_matches)

def process_chapter(file_path):
    """处理单个章节"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 步骤1: 修复身份/官职标注
    content, identity_changes = fix_identity_tags(content)

    # 步骤2: 修复人名嵌套
    content, nested_count = fix_nested_person_tags(content)

    # 写回
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    total_changes = sum(c[2] for c in identity_changes) + nested_count
    return total_changes, nested_count

def main():
    print("=" * 70)
    print("全局修复130章身份标注错误")
    print("=" * 70)

    # 创建备份
    create_backup()

    # 获取所有章节
    tagged_files = sorted(CHAPTER_DIR.glob('*.tagged.md'))

    print(f"\n开始处理 {len(tagged_files)} 个章节...")
    print("-" * 70)

    total_global_changes = 0
    total_global_nested = 0
    processed_chapters = []

    for i, file_path in enumerate(tagged_files, 1):
        chapter_name = file_path.stem.replace('.tagged', '')
        changes, nested = process_chapter(file_path)

        if changes > 0:
            processed_chapters.append((chapter_name, changes, nested))
            print(f"{i:3d}. {chapter_name:<35} 修复:{changes:4d} (嵌套:{nested:3d})")

        total_global_changes += changes
        total_global_nested += nested

    print("\n" + "=" * 70)
    print(f"修复完成！")
    print("=" * 70)
    print(f"处理章节: {len(processed_chapters)}/{len(tagged_files)}")
    print(f"总修复数: {total_global_changes}")
    print(f"  - 人名嵌套: {total_global_nested}")
    print(f"  - 身份/官职: {total_global_changes - total_global_nested}")
    print(f"\n备份位置: {BACKUP_DIR}/")
    print("\n⚠️  提醒：")
    print("  1. 子/孙/弟/父 可能需要人工审核（代际关系 vs 身份称谓）")
    print("  2. 建议执行 validate_tagging.py 验证修复结果")
    print("  3. 修复后需重新生成所有HTML: python generate_all_chapters.py")

if __name__ == '__main__':
    main()
