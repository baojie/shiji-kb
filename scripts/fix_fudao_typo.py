#!/usr/bin/env python3
"""
修正"衤复道"→"複道"的全局性错误

同步修改：
1. corpus/archive/chapter_numbered/ (4个文件)
2. chapter_md/*.tagged.md (4个文件)
"""

import sys
from pathlib import Path

# 定义需要修改的文件
FILES_NUMBERED = [
    "corpus/archive/chapter_numbered/006_秦始皇本纪.txt",
    "corpus/archive/chapter_numbered/012_孝武本纪.txt",
    "corpus/archive/chapter_numbered/028_封禅书.txt",
    "corpus/archive/chapter_numbered/099_刘敬叔孙通列传.txt",
]

FILES_TAGGED = [
    "chapter_md/006_秦始皇本纪.tagged.md",
    "chapter_md/012_孝武本纪.tagged.md",
    "chapter_md/028_封禅书.tagged.md",
    "chapter_md/099_刘敬叔孙通列传.tagged.md",
]

def fix_file(file_path: str) -> tuple[int, int]:
    """
    修复单个文件中的"衤复道"错误

    Returns:
        (替换次数, 字符变化数)
    """
    path = Path(file_path)
    if not path.exists():
        print(f"⚠️  文件不存在: {file_path}")
        return 0, 0

    # 读取原文
    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()

    original_len = len(original)

    # 执行替换
    modified = original.replace("衤复道", "複道")

    # 计算替换次数
    count = (len(original) - len(modified)) // 2  # "衤复道"(3字) → "複道"(2字)，每次减少2字符

    if count > 0:
        # 写回文件
        with open(path, 'w', encoding='utf-8') as f:
            f.write(modified)

        char_diff = original_len - len(modified)
        print(f"✅ {path.name}: 替换 {count} 处，字符数 {original_len} → {len(modified)} (-{char_diff})")
        return count, char_diff
    else:
        print(f"⏭️  {path.name}: 无需修改")
        return 0, 0

def main():
    print("=" * 60)
    print("修正全局typo: 衤复道 → 複道")
    print("=" * 60)

    total_count = 0
    total_char_diff = 0

    print("\n📁 修改 corpus/archive/chapter_numbered/")
    print("-" * 60)
    for file in FILES_NUMBERED:
        count, diff = fix_file(file)
        total_count += count
        total_char_diff += diff

    print("\n📁 修改 chapter_md/*.tagged.md")
    print("-" * 60)
    for file in FILES_TAGGED:
        count, diff = fix_file(file)
        total_count += count
        total_char_diff += diff

    print("\n" + "=" * 60)
    print(f"✅ 完成！共替换 {total_count} 处，总字符数减少 {total_char_diff}")
    print("=" * 60)

    if total_count > 0:
        print("\n⚠️  请运行以下命令验证文本完整性：")
        print("   python scripts/lint_text_integrity.py")

if __name__ == "__main__":
    main()
