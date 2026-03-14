#!/usr/bin/env python3
"""
修复所有章节"赞"韵文的格式，确保每句（以。结尾）换行。
适配 ::: 赞 fenced div 格式。
"""
import re
import os
from pathlib import Path


def strip_tags(text):
    """去除实体标注符号，返回纯文本"""
    text = re.sub(r'[〖〗〖+〗〚〛〔〕]', '', text)
    text = re.sub(r'[;@&=^~!%*#]', '', text)
    return text


def is_single_line_verse(text):
    """判断是否为单行韵文（多个。在同一行）"""
    clean = strip_tags(text)
    periods = clean.count('。')
    return periods >= 3  # 至少3个句号才认为需要拆分


def split_verse_line(line):
    """将单行韵文按。拆分为多行"""
    # 匹配段落编号前缀 [N.N] 或 [N]
    prefix_match = re.match(r'^(\[[\d.]+\]\s*)', line)
    if prefix_match:
        prefix = prefix_match.group(1)
        rest = line[len(prefix):]
    else:
        prefix = ''
        rest = line

    # 按。拆分，但保留。
    sentences = re.split(r'(。)', rest)

    result_lines = []
    current = prefix
    for part in sentences:
        if part == '。':
            current += '。'
            result_lines.append(current)
            current = ''
        else:
            current += part

    if current.strip():
        result_lines.append(current)

    result_lines = [l for l in result_lines if l.strip()]
    return result_lines


def process_file(filepath):
    """处理单个文件：在 ::: 赞 块内拆分单行韵文"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    in_zan = False
    modified = False

    for line in lines:
        if line.strip() == '::: 赞':
            in_zan = True
            new_lines.append(line)
            continue
        if in_zan and line.strip() == ':::':
            in_zan = False
            new_lines.append(line)
            continue

        if in_zan and line.strip() and is_single_line_verse(line):
            split_lines = split_verse_line(line)
            if len(split_lines) > 1:
                new_lines.extend(split_lines)
                modified = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

    return modified


def main():
    chapter_dir = Path('chapter_md')
    files = sorted(chapter_dir.glob('*.tagged.md'))

    modified_count = 0
    no_zan_count = 0

    for filepath in files:
        filename = filepath.name
        with open(filepath) as f:
            if '::: 赞' not in f.read():
                no_zan_count += 1
                continue

        if process_file(filepath):
            print(f"  ✅ 已修复 {filename}")
            modified_count += 1

    print(f"\n统计:")
    print(f"  已修复: {modified_count} 个文件")
    print(f"  无赞块: {no_zan_count} 个文件")


if __name__ == '__main__':
    main()
