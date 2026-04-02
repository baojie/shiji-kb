#!/usr/bin/env python3
"""
删除"曰："后面、":::" 引用块前面的多余Purple Numbers

规则：
当出现这种模式时：
    曰：

    [数字]

    :::
删除中间的 [数字] 行
"""

import re
import sys
from pathlib import Path


def fix_pn_before_quote(content: str) -> tuple[str, int]:
    """
    删除"曰："和":::"之间的多余PN

    Returns:
        (修改后的内容, 删除的编号数)
    """
    deleted_count = 0
    lines = content.split('\n')
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        result_lines.append(line)

        # 检查是否匹配模式：曰：
        if line.rstrip().endswith('曰：'):
            # 查看接下来的行
            if i + 1 < len(lines) and lines[i + 1].strip() == '':  # 空行
                if i + 2 < len(lines) and re.match(r'^\[\d+\]$', lines[i + 2].strip()):  # 独立的PN
                    if i + 3 < len(lines) and lines[i + 3].strip() == '':  # 空行
                        if i + 4 < len(lines) and lines[i + 4].strip().startswith(':::'):  # ::: 标记
                            # 匹配成功，跳过空行和PN行
                            result_lines.append(lines[i + 1])  # 保留第一个空行
                            # 跳过 lines[i + 2] (PN)
                            # 跳过 lines[i + 3] (空行)
                            i += 4  # 跳到 ::: 行
                            deleted_count += 1
                            continue

        i += 1

    return '\n'.join(result_lines), deleted_count


def process_chapter(file_path: Path) -> dict:
    """处理单个章节文件"""

    content = file_path.read_text(encoding='utf-8')
    new_content, deleted_count = fix_pn_before_quote(content)

    if deleted_count > 0:
        file_path.write_text(new_content, encoding='utf-8')
        return {
            'modified': True,
            'deleted_count': deleted_count
        }
    else:
        return {'modified': False}


def main():
    if len(sys.argv) < 2:
        print("用法: python fix_pn_before_quote_block.py <chapter_files...>")
        print("示例: python fix_pn_before_quote_block.py chapter_md/081*.tagged.md")
        sys.exit(1)

    chapter_files = [Path(arg) for arg in sys.argv[1:]]

    total_modified = 0
    total_deleted = 0

    print("=" * 70)
    print("删除'曰：'和':::'之间的多余Purple Numbers")
    print("=" * 70)

    for file_path in sorted(chapter_files):
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            continue

        result = process_chapter(file_path)

        if result['modified']:
            total_modified += 1
            total_deleted += result['deleted_count']
            print(f"✓ {file_path.name}: 删除 {result['deleted_count']} 个多余编号")

    print("=" * 70)
    print(f"✓ 处理完成!")
    print(f"  修改文件数: {total_modified}")
    print(f"  删除编号总数: {total_deleted}")
    print("=" * 70)


if __name__ == '__main__':
    main()
