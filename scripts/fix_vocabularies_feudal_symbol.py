#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复 kg/vocabularies/ 目录下的邦国标注符号

将旧符号 〖' 替换为新符号 〖◆
将旧符号 '〗 替换为新符号 ◆〗

用法：
    python scripts/fix_vocabularies_feudal_symbol.py
"""

from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VOCABULARIES_DIR = PROJECT_ROOT / 'kg' / 'vocabularies'

def fix_file(file_path):
    """修复单个文件中的邦国符号"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 定义旧符号和新符号
    # 注意：标注模式是 〖'文字〗，而不是 〖'文字'〗
    old_marker = "〖'"
    new_marker = "〖◆"

    # 统计替换数量
    old_count = content.count(old_marker)

    # 执行替换
    new_content = content.replace(old_marker, new_marker)

    # 验证替换成功
    new_count = new_content.count(new_marker)
    remaining_old = new_content.count(old_marker)

    if remaining_old > 0:
        print(f"  ⚠️  警告：{file_path.name} 中仍有 {remaining_old} 个旧符号未替换")
        return False

    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return old_count > 0

def main():
    print("=" * 60)
    print("修复 kg/vocabularies/ 目录下的邦国标注符号")
    print("=" * 60)

    # 查找所有 .md 文件
    md_files = sorted(VOCABULARIES_DIR.glob('*.md'))

    total_files = 0
    modified_files = 0

    for md_file in md_files:
        total_files += 1
        if fix_file(md_file):
            modified_files += 1
            print(f"✓ {md_file.name}")
        else:
            print(f"- {md_file.name} (无需修改)")

    print("=" * 60)
    print(f"完成！共处理 {total_files} 个文件，修改 {modified_files} 个文件")
    print("=" * 60)

if __name__ == '__main__':
    main()
