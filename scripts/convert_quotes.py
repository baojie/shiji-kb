#!/usr/bin/env python3
"""
将标注文件中的直引号转换为中文弯引号
保持开引号（"）和闭引号（"）的正确配对
"""

import re
from pathlib import Path


def convert_quotes_to_chinese(text):
    """
    将直引号转换为中文弯引号
    规则：
    1. 句首、冒号后、逗号后的引号 → 开引号 "
    2. 句末、逗号前、句号前的引号 → 闭引号 "
    3. 通过配对来判断
    """
    # 使用Unicode码位确保正确性
    OPEN_QUOTE = '\u201c'  # "
    CLOSE_QUOTE = '\u201d'  # "

    result = []
    quote_open = False  # 跟踪引号是否已打开

    i = 0
    while i < len(text):
        if text[i] == '"':
            # 简单配对：奇数个引号用开引号，偶数个用闭引号
            if not quote_open:
                result.append(OPEN_QUOTE)
                quote_open = True
            else:
                result.append(CLOSE_QUOTE)
                quote_open = False
        else:
            result.append(text[i])

        i += 1

    return ''.join(result)


def process_file(file_path):
    """处理单个文件"""
    print(f"处理文件: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计直引号数量
    quote_count = content.count('"')
    print(f"发现 {quote_count} 个直引号")

    # 转换引号
    converted = convert_quotes_to_chinese(content)

    # 统计转换后的引号（使用Unicode码位）
    open_count = converted.count('\u201c')  # "
    close_count = converted.count('\u201d')  # "
    print(f"转换为 {open_count} 个开引号，{close_count} 个闭引号")

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(converted)

    print(f"✅ 文件已更新")

    return quote_count, open_count, close_count


if __name__ == '__main__':
    md_file = Path('/home/baojie/work/shiji-kb/chapter_md/005_秦本纪.tagged.md')

    if not md_file.exists():
        print(f"错误: 文件不存在: {md_file}")
        exit(1)

    quote_count, open_count, close_count = process_file(md_file)

    if open_count != close_count:
        print(f"\n⚠️  警告: 开引号和闭引号数量不匹配！")
        print(f"   开引号: {open_count}")
        print(f"   闭引号: {close_count}")
    else:
        print(f"\n✅ 引号配对正确！")
