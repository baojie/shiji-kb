#!/usr/bin/env python3
"""
批量将标注文件中的直引号转换为中文弯引号
"""

import sys
from pathlib import Path
from convert_quotes import convert_quotes_to_chinese


def process_file(file_path):
    """处理单个文件"""
    print(f"\n处理文件: {file_path.name}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计直引号数量
    quote_count = content.count('"')
    print(f"  发现 {quote_count} 个直引号")

    if quote_count == 0:
        print(f"  ✅ 无需转换")
        return 0, 0, 0

    # 转换引号
    converted = convert_quotes_to_chinese(content)

    # 统计转换后的引号
    open_count = converted.count('\u201c')  # "
    close_count = converted.count('\u201d')  # "
    print(f"  转换为 {open_count} 个开引号，{close_count} 个闭引号")

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(converted)

    print(f"  ✅ 文件已更新")

    return quote_count, open_count, close_count


def main():
    base_dir = Path('/home/baojie/work/shiji-kb')

    # 处理章节 001-004
    chapters = [1, 2, 3, 4]

    print("="*80)
    print("批量转换引号 - 章节 001-004")
    print("="*80)

    total_straight = 0
    total_open = 0
    total_close = 0

    for num in chapters:
        # 查找文件
        md_files = list(base_dir.glob(f'chapter_md/{num:03d}_*.tagged.md'))

        if not md_files:
            print(f"\n⚠️  章节 {num:03d}: 文件不存在")
            continue

        md_file = md_files[0]

        straight, open_q, close_q = process_file(md_file)
        total_straight += straight
        total_open += open_q
        total_close += close_q

    print("\n" + "="*80)
    print("转换汇总")
    print("="*80)
    print(f"总计转换 {total_straight} 个直引号")
    print(f"  → {total_open} 个开引号(\u201c)")
    print(f"  → {total_close} 个闭引号(\u201d)")

    if total_open != total_close:
        print(f"\n⚠️  警告: 开引号和闭引号数量不匹配！")
        return 1
    else:
        print(f"\n✅ 所有引号配对正确！")
        return 0


if __name__ == '__main__':
    sys.exit(main())
