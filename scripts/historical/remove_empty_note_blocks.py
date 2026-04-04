#!/usr/bin/env python3
"""
移除tagged.md文件中的空note-box块

空块模式：
:::<可选空白>
:::<可选空白>

这些会导致HTML生成空的 <div class="note-box"></div> 标签
"""

import re
import sys
from pathlib import Path


def remove_empty_note_blocks(content: str) -> tuple[str, int]:
    """
    移除空的note-box块

    Returns:
        (cleaned_content, count) - 清理后的内容和移除的数量
    """
    # 匹配空的:::块 (开始标签后紧跟结束标签，中间可能有空行)
    pattern = r'^:::\s*\n(?:\s*\n)*:::\s*\n'

    cleaned, count = re.subn(pattern, '', content, flags=re.MULTILINE)

    return cleaned, count


def main():
    if len(sys.argv) < 2:
        print("用法: python remove_empty_note_blocks.py <file1.tagged.md> [file2.tagged.md ...]")
        print("示例: python remove_empty_note_blocks.py chapter_md/058_*.tagged.md")
        return 1

    for filepath in sys.argv[1:]:
        path = Path(filepath)
        if not path.exists():
            print(f"✗ 文件不存在: {filepath}")
            continue

        # 读取文件
        content = path.read_text(encoding='utf-8')

        # 清理空块
        cleaned, count = remove_empty_note_blocks(content)

        if count == 0:
            print(f"✓ {filepath}: 无需修改")
            continue

        # 写回文件
        path.write_text(cleaned, encoding='utf-8')
        print(f"✓ {filepath}: 移除了 {count} 个空note-box块")

    return 0


if __name__ == '__main__':
    sys.exit(main())
