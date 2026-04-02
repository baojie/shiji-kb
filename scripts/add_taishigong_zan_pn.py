#!/usr/bin/env python3
"""
为"太史公曰"和"赞"添加Purple Numbers

规则：
1. "太史公曰"整段一个编号
2. "赞"整段一个编号
3. 在段落第一行（非空行）前添加编号
"""

import re
import sys
from pathlib import Path


def add_section_pn(content: str, section_marker: str, pn_number: str) -> tuple[str, bool]:
    """
    为某个章节（太史公曰或赞）添加Purple Number

    Returns:
        (修改后的内容, 是否添加了编号)
    """
    # 找到该章节的起始和结束位置
    pattern = rf'(^::: {section_marker}\n)(.*?)(^:::)'

    added = False

    def replace_section(match):
        nonlocal added
        start_marker = match.group(1)
        section_content = match.group(2)
        end_marker = match.group(3)

        # 检查是否已经有编号
        if re.match(r'^\[\d+\] ', section_content.lstrip()):
            # 已有编号，不修改
            return match.group(0)

        # 在第一个非空行前添加编号
        lines = section_content.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                lines[i] = f'[{pn_number}] {line}'
                added = True
                break

        new_content = '\n'.join(lines)
        return start_marker + new_content + end_marker

    new_content = re.sub(pattern, replace_section, content, flags=re.MULTILINE | re.DOTALL)

    return new_content, added


def get_max_pn(content: str) -> int:
    """获取正文中最大的Purple Number"""
    # 查找所有形如 [数字] 的模式
    pattern = r'^\[(\d+)\] '
    matches = re.findall(pattern, content, re.MULTILINE)

    if not matches:
        return 0

    # 排除太史公曰和赞部分的编号
    # 只看正文部分
    lines = content.split('\n')
    max_num = 0
    in_taishigong = False
    in_zan = False

    for line in lines:
        if line.startswith('::: 太史公曰'):
            in_taishigong = True
            continue
        elif line.startswith('::: 赞'):
            in_zan = True
            continue
        elif line.startswith(':::'):
            in_taishigong = False
            in_zan = False
            continue

        if not in_taishigong and not in_zan:
            match = re.match(r'^\[(\d+)\] ', line)
            if match:
                num = int(match.group(1))
                max_num = max(max_num, num)

    return max_num


def process_chapter(file_path: Path) -> dict:
    """处理单个章节文件"""

    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # 获取正文中最大的Purple Number
    max_pn = get_max_pn(content)

    # 为"太史公曰"添加编号（下一个编号）
    taishigong_pn = max_pn + 1
    content, taishigong_added = add_section_pn(content, '太史公曰', str(taishigong_pn))

    # 为"赞"添加编号（再下一个编号）
    zan_pn = taishigong_pn + 1 if taishigong_added else max_pn + 1
    content, zan_added = add_section_pn(content, '赞', str(zan_pn))

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return {
            'modified': True,
            'taishigong_added': taishigong_added,
            'zan_added': zan_added,
            'taishigong_pn': taishigong_pn if taishigong_added else None,
            'zan_pn': zan_pn if zan_added else None
        }
    else:
        return {'modified': False}


def main():
    if len(sys.argv) < 2:
        print("用法: python add_taishigong_zan_pn.py <chapter_file_or_range>")
        print("示例: python add_taishigong_zan_pn.py 065-130")
        print("示例: python add_taishigong_zan_pn.py chapter_md/065_孙子吴起列传.tagged.md")
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
    total_taishigong_added = 0
    total_zan_added = 0

    print("=" * 70)
    print("为太史公曰和赞添加Purple Numbers")
    print("=" * 70)

    for file_path in sorted(chapter_files):
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            continue

        result = process_chapter(file_path)

        if result['modified']:
            total_modified += 1

            print(f"✓ {file_path.name}")
            if result['taishigong_added']:
                total_taishigong_added += 1
                print(f"  - 太史公曰: 添加编号 [{result['taishigong_pn']}]")
            if result['zan_added']:
                total_zan_added += 1
                print(f"  - 赞: 添加编号 [{result['zan_pn']}]")

    print("=" * 70)
    print(f"✓ 处理完成!")
    print(f"  修改文件数: {total_modified}")
    print(f"  添加编号总数: {total_taishigong_added + total_zan_added}")
    print(f"    - 太史公曰: {total_taishigong_added}")
    print(f"    - 赞: {total_zan_added}")
    print("=" * 70)


if __name__ == '__main__':
    main()
