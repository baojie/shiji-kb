#!/usr/bin/env python3
"""
修复所有章节"赞"韵文的格式，确保每句（以。结尾）换行。
跳过035-040（正在被其他代理编辑）。
"""
import re
import os
from pathlib import Path

def find_verse_section(lines):
    """找到赞诗/赞/总赞 section的起始行索引"""
    verse_start = None
    for i, line in enumerate(lines):
        # 匹配各种赞标题
        if re.match(r'^#{2,3}\s+.*赞', line):
            verse_start = i
    return verse_start

def is_single_line_verse(text):
    """判断是否为单行韵文（多个。在同一行）"""
    # 去掉标签后计算句号数
    clean = re.sub(r'[@=\$%\^~&!?\[\]#\*>]', '', text)
    periods = clean.count('。')
    return periods >= 3  # 至少3个句号才认为需要拆分

def split_verse_line(line):
    """将单行韵文按。拆分为多行"""
    # 匹配段落编号前缀 [N.N] 或 [N]
    prefix_match = re.match(r'^(\[[\d.]+\]\s*)', line)
    if prefix_match:
        prefix = prefix_match.group(1)
        rest = line[len(prefix):]
    elif line.startswith('> '):
        # blockquote格式
        inner = line[2:]
        prefix_match = re.match(r'^(\[[\d.]+\]\s*)', inner)
        if prefix_match:
            prefix = '> ' + prefix_match.group(1)
            rest = inner[len(prefix_match.group(1)):]
        else:
            return [line]  # 无法解析，保持原样
    else:
        return [line]  # 无法解析，保持原样

    # 按。拆分，但保留。
    sentences = re.split(r'(。)', rest)

    # 重新组合：每两个元素（文本+。）组成一句
    result_lines = []
    current = prefix
    for i in range(0, len(sentences)):
        part = sentences[i]
        if part == '。':
            current += '。'
            result_lines.append(current)
            current = ''
        else:
            current += part

    # 处理末尾可能没有。的部分
    if current.strip():
        result_lines.append(current)

    # 过滤空行
    result_lines = [l for l in result_lines if l.strip()]

    return result_lines

def process_file(filepath):
    """处理单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # 找到赞section
    verse_start = find_verse_section(lines)
    if verse_start is None:
        return False, "无赞section"

    # 从赞section开始到文件末尾
    modified = False
    new_lines = lines[:verse_start]  # 保留赞section之前的内容

    i = verse_start
    while i < len(lines):
        line = lines[i]

        # 检查是否为包含段落编号的韵文行
        is_verse_para = bool(re.match(r'^\[[\d.]+\]', line)) or bool(re.match(r'^> \[[\d.]+\]', line))

        if is_verse_para and is_single_line_verse(line):
            # 需要拆分
            split_lines = split_verse_line(line)
            if len(split_lines) > 1:
                new_lines.extend(split_lines)
                modified = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

        i += 1

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

    return modified, f"赞section在第{verse_start+1}行"

def main():
    chapter_dir = Path('chapter_md')

    # 跳过035-040（正在被代理编辑）
    skip_prefixes = ['035_', '036_', '037_', '038_', '039_', '040_']

    files = sorted(chapter_dir.glob('*.tagged.md'))

    modified_count = 0
    skipped_count = 0
    no_verse_count = 0
    already_ok_count = 0

    for filepath in files:
        filename = filepath.name

        # 检查是否需要跳过
        if any(filename.startswith(p) for p in skip_prefixes):
            print(f"  跳过 {filename}（代理正在编辑）")
            skipped_count += 1
            continue

        modified, info = process_file(filepath)

        if "无赞section" in info:
            no_verse_count += 1
        elif modified:
            print(f"  ✅ 已修复 {filename} - {info}")
            modified_count += 1
        else:
            already_ok_count += 1

    print(f"\n统计:")
    print(f"  已修复: {modified_count} 个文件")
    print(f"  已跳过: {skipped_count} 个文件（代理编辑中）")
    print(f"  无赞section: {no_verse_count} 个文件")
    print(f"  格式已正确: {already_ok_count} 个文件")

if __name__ == '__main__':
    main()
