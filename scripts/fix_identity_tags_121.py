#!/usr/bin/env python3
"""
修复121章《儒林列传》中的身份标注错误

问题：大量身份/官职被错误标注为时间类型 〖#xxx〗
原因：早期标注时#符号可能用于"称谓"，后期重新定义为"时间"
"""

import re
import shutil
from pathlib import Path

# 文件路径
CHAPTER_FILE = Path('chapter_md/121_儒林列传.tagged.md')
BACKUP_DIR = Path('backups/identity_fix_121')

def create_backup():
    """创建备份"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_file = BACKUP_DIR / CHAPTER_FILE.name
    shutil.copy2(CHAPTER_FILE, backup_file)
    print(f"✓ 备份创建: {backup_file}")
    return backup_file

def fix_identity_tags(content):
    """修复身份标注"""

    # 修正规则：
    # 1. 身份类 〖#xxx〗 → 〖_xxx〗
    # 2. 官职类 〖#xxx〗 → 〖;xxx〗

    changes = []

    # 【优先级1】处理嵌套的"弟子"错误：〖#弟〗〖#子〗 → 〖_弟子〗
    pattern = r'〖#弟〗〖#子〗'
    replacement = '〖_弟子〗'
    count = len(re.findall(pattern, content))
    if count > 0:
        content = re.sub(pattern, replacement, content)
        changes.append(f"  {pattern} → {replacement}  ({count}次)")

    # 【优先级2】身份称谓
    identity_mappings = [
        ('天子', '天子'),      # 君主称谓
        ('诸侯', '诸侯'),      # 诸侯
        ('士', '士'),          # 士阶层（但要排除嵌套情况）
        ('夫', '夫'),          # 夫（但要排除"匹夫"等复合词）
        ('臣', '臣'),          # 臣子
        ('民', '民'),          # 百姓
        ('匹夫', '匹夫'),      # 平民
    ]

    for old_entity, new_entity in identity_mappings:
        # 避免重复替换已经修正的内容
        pattern = rf'〖#{re.escape(old_entity)}〗'
        replacement = f'〖_{new_entity}〗'
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            changes.append(f"  {pattern} → {replacement}  ({count}次)")

    # 【优先级3】官职称谓
    official_mappings = [
        ('卿相', '卿相'),
        ('公卿', '公卿'),
        ('大夫', '大夫'),
        ('太后', '太后'),
        ('太子', '太子'),
        ('陛下', '陛下'),
        ('君', '君'),
    ]

    for old_entity, new_entity in official_mappings:
        pattern = rf'〖#{re.escape(old_entity)}〗'
        replacement = f'〖;{new_entity}〗'
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            changes.append(f"  {pattern} → {replacement}  ({count}次)")

    # 【特殊处理】"子"、"孙"、"弟"、"父" - 需要保留一些作为代际关系
    # 这里简单处理，全部改为身份（后续可人工审核）
    for entity in ['子', '孙', '弟', '父']:
        pattern = rf'〖#{re.escape(entity)}〗'
        replacement = f'〖_{entity}〗'
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            changes.append(f"  {pattern} → {replacement}  ({count}次) ⚠️ 需人工审核")

    return content, changes

def main():
    print("=" * 60)
    print("修复121章《儒林列传》身份标注错误")
    print("=" * 60)

    # 创建备份
    backup_file = create_backup()

    # 读取原文
    with open(CHAPTER_FILE, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # 执行修复
    fixed_content, changes = fix_identity_tags(original_content)

    # 显示变更
    print("\n修正列表:")
    print("-" * 60)
    for change in changes:
        print(change)

    print("\n" + "=" * 60)
    print(f"总计修正: {len(changes)} 种模式")
    print("=" * 60)

    # 写回文件
    with open(CHAPTER_FILE, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"\n✓ 修复完成: {CHAPTER_FILE}")
    print(f"✓ 备份位置: {backup_file}")
    print("\n⚠️  提醒：子/孙/弟/父 需要人工审核是否为代际关系")
    print("    建议下一步：执行实体反思验证修正结果")

if __name__ == '__main__':
    main()
