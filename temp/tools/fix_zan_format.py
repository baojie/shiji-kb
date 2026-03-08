#!/usr/bin/env python3
"""修复所有章节的"赞"格式：合并为单编号，句子换行不分段。

规则：
- 赞部分各句子换行但不分段（无空行）
- 整个赞只保留一个段落编号（第一个 [X.Y]）
- 后续句子去掉 [X.Y] 编号，直接换行
"""

import re
import glob
import os

def find_zan_section(lines):
    """找到赞部分的起始行号（标题行）。返回 (header_line_idx, header_text) 或 None。"""
    # 从后往前找，赞通常在文件末尾
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if re.match(r'^#{1,4}\s+.*赞', line):
            return i
    return None

def fix_zan_format(filepath):
    """修复单个文件的赞格式。返回是否有修改。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    zan_start = find_zan_section(lines)
    if zan_start is None:
        return False

    # 收集赞部分的内容行（标题之后的所有行）
    header_line = lines[zan_start]

    # 找到赞部分的内容开始位置（跳过标题后的空行）
    content_start = zan_start + 1
    while content_start < len(lines) and lines[content_start].strip() == '':
        content_start += 1

    if content_start >= len(lines):
        return False

    # 收集赞的所有内容行（去掉空行和编号）
    zan_lines = []
    first_number = None

    for i in range(content_start, len(lines)):
        line = lines[i].strip()
        if line == '':
            continue
        # 跳过以 > NOTE 开头的注释行（保留）
        if line.startswith('> NOTE'):
            zan_lines.append(line)
            continue

        # 提取 [X.Y] 编号
        m = re.match(r'\[(\d+(?:\.\d+)*)\]\s*(.*)', line)
        if m:
            if first_number is None:
                first_number = m.group(1)
                zan_lines.append(f'[{first_number}] {m.group(2)}')
            else:
                # 去掉编号，只保留内容
                zan_lines.append(m.group(2))
        else:
            # 没有编号的行（如引用格式 > 开头的行）直接保留
            zan_lines.append(line)

    if not zan_lines:
        return False

    # 检查是否有变化：比较新旧内容
    # 新的赞部分：标题 + 空行 + 内容行（用换行连接，无空行）
    new_zan_content = '\n'.join(zan_lines)

    # 重建文件
    before_zan = lines[:zan_start]
    new_lines = before_zan + [header_line, '', new_zan_content, '']
    new_content = '\n'.join(new_lines)

    if new_content == content:
        return False

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True

def main():
    chapter_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chapter_md')
    files = sorted(glob.glob(os.path.join(chapter_dir, '*.tagged.md')))

    modified = []
    skipped = []

    for filepath in files:
        filename = os.path.basename(filepath)
        if fix_zan_format(filepath):
            modified.append(filename)
            print(f'✓ 已修复: {filename}')
        else:
            skipped.append(filename)

    print(f'\n共修复 {len(modified)} 个文件，跳过 {len(skipped)} 个文件')

if __name__ == '__main__':
    main()
