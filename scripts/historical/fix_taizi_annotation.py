#!/usr/bin/env python3
"""
修正"太子"标注错误
将 太〖#子〗 修正为 〖;太子〗

错误模式：太〖#子〗 - 只有"子"被标注为身份
正确模式：〖;太子〗 - 整个"太子"作为官职标注

使用示例：
    python scripts/fix_taizi_annotation.py chapter_md/*.tagged.md
"""

import re
import sys
from pathlib import Path


def fix_taizi_annotation(content: str) -> tuple[str, int]:
    """
    修正"太子"标注错误

    Args:
        content: 文件内容

    Returns:
        (修正后的内容, 修正次数)
    """
    # 匹配：太〖#子〗
    # 替换为：〖;太子〗
    pattern = r'太〖#子〗'
    replacement = r'〖;太子〗'

    new_content, count = re.subn(pattern, replacement, content)

    return new_content, count


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/fix_taizi_annotation.py <文件1> [文件2] ...")
        sys.exit(1)

    total_files = 0
    total_fixes = 0

    for file_path in sys.argv[1:]:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ 文件不存在: {file_path}")
            continue

        # 读取文件
        content = path.read_text(encoding='utf-8')

        # 修正
        new_content, count = fix_taizi_annotation(content)

        if count > 0:
            # 写回文件
            path.write_text(new_content, encoding='utf-8')
            print(f"✓ {path.name}: 修正 {count} 处")
            total_files += 1
            total_fixes += count
        else:
            print(f"  {path.name}: 无需修正")

    print(f"\n汇总: 修正 {total_files} 个文件，共 {total_fixes} 处")


if __name__ == '__main__':
    main()
