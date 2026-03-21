#!/usr/bin/env python3
"""
批量修复108-112章旧格式
⟦◈X⟧ → 〖[X〗 (军事动词)
⟦◉X⟧ → 〖[X〗 (刑法动词)
"""

import re
import shutil
from pathlib import Path
from datetime import datetime

WORK_DIR = Path("/home/baojie/work/shiji-kb")
CHAPTER_DIR = WORK_DIR / "chapter_md"

CHAPTERS = [
    ("108", "韩长孺列传"),
    ("109", "李将军列传"),
    ("110", "匈奴列传"),
    ("111", "卫将军骠骑列传"),
    ("112", "平津侯主父列传"),
]

def backup_file(filepath):
    """备份文件"""
    backup_path = filepath.with_suffix(filepath.suffix + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(filepath, backup_path)
    return backup_path

def fix_old_format(text):
    """修复旧格式"""
    # ⟦◈X⟧ → 〖[X〗
    text = re.sub(r'⟦◈([^⟧]+)⟧', r'〖[\1〗', text)
    # ⟦◉X⟧ → 〖[X〗
    text = re.sub(r'⟦◉([^⟧]+)⟧', r'〖[\1〗', text)
    # ⟦○X⟧ → 去除（误标）
    text = re.sub(r'⟦○([^⟧]+)⟧', r'\1', text)
    return text

def process_chapter(chapter_num, chapter_name):
    """处理单个章节"""
    filepath = CHAPTER_DIR / f"{chapter_num}_{chapter_name}.tagged.md"

    if not filepath.exists():
        print(f"文件不存在: {filepath}")
        return 0

    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # 统计旧格式数量
    count_old = len(re.findall(r'⟦[◈◉○]', original_text))

    if count_old == 0:
        print(f"{chapter_num}_{chapter_name}: 无旧格式")
        return 0

    # 备份
    backup_path = backup_file(filepath)
    print(f"已备份: {backup_path.name}")

    # 修复
    fixed_text = fix_old_format(original_text)

    # 写回
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_text)

    # 验证
    count_new = len(re.findall(r'⟦[◈◉○]', fixed_text))

    print(f"{chapter_num}_{chapter_name}: 修复 {count_old} 处旧格式")

    if count_new > 0:
        print(f"  ⚠️ 警告: 仍有 {count_new} 处旧格式未修复")

    return count_old

def main():
    """主函数"""
    print("=" * 70)
    print("批量修复108-112章旧格式")
    print("=" * 70)

    total = 0
    for chapter_num, chapter_name in CHAPTERS:
        count = process_chapter(chapter_num, chapter_name)
        total += count

    print("=" * 70)
    print(f"总计修复: {total} 处旧格式")
    print("=" * 70)

if __name__ == "__main__":
    main()
