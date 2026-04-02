#!/usr/bin/env python3
"""
修复"太史公曰"和"赞"部分的Purple Numbers

规则：
1. 删除原有的内部编号
2. "太史公曰"整段保留一个编号（如果有）
3. "赞"整段保留一个编号（如果有）
"""

import re
import sys
from pathlib import Path


def fix_section_pn(content: str, section_marker: str) -> tuple[str, int]:
    """
    修复某个章节（太史公曰或赞）的Purple Numbers

    Returns:
        (修复后的内容, 删除的编号数)
    """
    # 找到该章节的起始和结束位置
    pattern = rf'(^::: {section_marker}\n)(.*?)(^:::)'

    deleted_count = 0

    def replace_section(match):
        nonlocal deleted_count
        start_marker = match.group(1)
        section_content = match.group(2)
        end_marker = match.group(3)

        # 统计删除的编号数
        pn_matches = re.findall(r'^\[\d+\] ', section_content, re.MULTILINE)
        deleted_count = len(pn_matches)

        # 删除所有行首的Purple Numbers
        cleaned_content = re.sub(r'^\[\d+\] ', '', section_content, flags=re.MULTILINE)

        return start_marker + cleaned_content + end_marker

    new_content = re.sub(pattern, replace_section, content, flags=re.MULTILINE | re.DOTALL)

    return new_content, deleted_count


def process_chapter(file_path: Path) -> dict:
    """处理单个章节文件"""

    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # 修复"太史公曰"
    content, taishigong_deleted = fix_section_pn(content, '太史公曰')

    # 修复"赞"
    content, zan_deleted = fix_section_pn(content, '赞')

    total_deleted = taishigong_deleted + zan_deleted

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return {
            'modified': True,
            'taishigong_deleted': taishigong_deleted,
            'zan_deleted': zan_deleted,
            'total_deleted': total_deleted
        }
    else:
        return {'modified': False}


def main():
    if len(sys.argv) < 2:
        print("用法: python fix_taishigong_zan_pn.py <chapter_file_or_range>")
        print("示例: python fix_taishigong_zan_pn.py 065-130")
        print("示例: python fix_taishigong_zan_pn.py chapter_md/065_孙子吴起列传.tagged.md")
        sys.exit(1)

    arg = sys.argv[1]

    # 判断是范围还是单个文件
    if '-' in arg and arg.replace('-', '').isdigit():
        # 范围模式：065-130
        start, end = map(int, arg.split('-'))
        chapter_files = []
        for i in range(start, end + 1):
            pattern = f"chapter_md/{i:03d}_*.tagged.md"
            matches = list(Path('.').glob(pattern))
            if matches:
                chapter_files.append(matches[0])
    else:
        # 单个文件模式
        chapter_files = [Path(arg)]

    total_modified = 0
    total_taishigong_deleted = 0
    total_zan_deleted = 0

    print("=" * 70)
    print("修复太史公曰和赞的Purple Numbers")
    print("=" * 70)

    for file_path in sorted(chapter_files):
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            continue

        result = process_chapter(file_path)

        if result['modified']:
            total_modified += 1
            total_taishigong_deleted += result['taishigong_deleted']
            total_zan_deleted += result['zan_deleted']

            print(f"✓ {file_path.name}")
            if result['taishigong_deleted'] > 0:
                print(f"  - 太史公曰: 删除 {result['taishigong_deleted']} 个编号")
            if result['zan_deleted'] > 0:
                print(f"  - 赞: 删除 {result['zan_deleted']} 个编号")

    print("=" * 70)
    print(f"✓ 处理完成!")
    print(f"  修改文件数: {total_modified}")
    print(f"  删除编号总数: {total_taishigong_deleted + total_zan_deleted}")
    print(f"    - 太史公曰: {total_taishigong_deleted}")
    print(f"    - 赞: {total_zan_deleted}")
    print("=" * 70)


if __name__ == '__main__':
    main()
