#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话拆分工具
将包含多个"X曰"的段落拆分成独立的对话行

用法：
    python3 tools/split_dialogues.py chapter_md/002_夏本纪.md

功能：
1. 识别包含多个"X曰"模式的段落
2. 在"X曰"处拆分段落
3. 保留段落编号在第一行
4. 将拆分后的对话转换为列表项
"""

import re
import sys
from pathlib import Path


def split_dialogue_line(line):
    """
    拆分包含多个"X曰"的行

    策略：
    1. 在每个"X曰"之前拆分（除了第一个）
    2. 保留完整的引号内容

    Args:
        line: 输入行

    Returns:
        拆分后的行列表
    """
    # 匹配"X曰："或"X曰："模式
    # 使用正则找到所有"曰："或"曰："的位置
    pattern = r'([^。！？\n]+?曰[：:])'
    matches = list(re.finditer(pattern, line))

    if len(matches) <= 1:
        # 只有一个或没有"曰"，不需要拆分
        return [line]

    result = []
    parts = []

    # 简单策略：在每个"X曰"之前拆分（保留第一个在原位置）
    last_pos = 0
    for i, match in enumerate(matches):
        if i == 0:
            # 第一个"曰"，继续累积到引号结束
            continue
        else:
            # 从上一个位置到这个"曰"之前
            start = match.start()
            # 向前查找合适的拆分点（句号、引号结束等）
            split_pos = find_split_point(line, last_pos, start)
            if split_pos > last_pos:
                parts.append(line[last_pos:split_pos].strip())
                last_pos = split_pos

    # 添加最后一部分
    if last_pos < len(line):
        parts.append(line[last_pos:].strip())

    # 如果拆分失败，使用更简单的方法：按句号拆分
    if len(parts) <= 1:
        # 尝试按"。"拆分，但保留引号内的句号
        parts = smart_split_by_period(line)

    return parts if parts else [line]


def find_split_point(text, start, end):
    """
    在start和end之间找到合适的拆分点
    优先在引号结束后、句号后拆分
    """
    # 从end向前查找最近的句号或引号结束
    split_chars = ['。', '"', '"', ''', ''', '」', '』']
    for i in range(end - 1, start, -1):
        if text[i] in split_chars:
            return i + 1
    return end


def smart_split_by_period(text):
    """
    智能按句号拆分，但保留引号内的内容完整
    """
    result = []
    current = []
    in_quote = False
    quote_char = None

    # 引号对应关系
    quote_pairs = {'"': '"', "'": "'", '「': '」', '『': '』'}

    for i, char in enumerate(text):
        current.append(char)

        # 检查引号状态
        if char in quote_pairs and not in_quote:
            in_quote = True
            quote_char = quote_pairs[char]
        elif char == quote_char and in_quote:
            in_quote = False
            quote_char = None

        # 在句号处拆分（但不在引号内）
        if char == '。' and not in_quote:
            # 检查后面是否紧跟"X曰"
            remaining = text[i+1:].lstrip()
            if remaining and '曰' in remaining[:10]:
                # 后面有"曰"，这里拆分
                result.append(''.join(current).strip())
                current = []

    # 添加剩余部分
    if current:
        result.append(''.join(current).strip())

    return result


def find_quote_end(text, start_pos):
    """找到从start_pos开始的引号内容的结束位置"""
    # 支持的引号：""、''、「」、『』
    quote_pairs = {
        '"': '"',
        "'": "'",
        '「': '」',
        '『': '』'
    }

    # 从start_pos开始查找引号
    for i in range(start_pos, len(text)):
        if text[i] in quote_pairs:
            # 找到开始引号，查找对应的结束引号
            closing = quote_pairs[text[i]]
            for j in range(i + 1, len(text)):
                if text[j] == closing:
                    return j + 1

    return start_pos


def find_sentence_end(text, start_pos):
    """找到从start_pos开始的句子结束位置"""
    sentence_ends = '。！？；'
    for i in range(start_pos, len(text)):
        if text[i] in sentence_ends:
            return i + 1
    return len(text)


def split_dialogues_in_file(input_file, output_file=None):
    """
    处理文件中的对话拆分

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选，默认覆盖原文件）
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"错误：文件 {input_file} 不存在")
        return

    # 读取文件
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result_lines = []
    changes_made = 0

    for line_num, line in enumerate(lines, 1):
        # 跳过空行、标题
        if not line.strip() or line.startswith('#'):
            result_lines.append(line)
            continue

        # 检查是否是列表项
        is_list_item = line.strip().startswith('- ')
        content = line.strip()[2:] if is_list_item else line.strip()

        # 检查是否包含多个"曰"
        yue_count = content.count('曰：') + content.count('曰：')

        if yue_count > 1:
            # 需要拆分
            print(f"第 {line_num} 行包含 {yue_count} 个'曰'，进行拆分...")
            split_lines = split_dialogue_line(content)

            # 所有行都作为列表项
            for split_line in split_lines:
                if split_line:
                    result_lines.append('- ' + split_line + '\n')

            changes_made += 1
        else:
            result_lines.append(line)

    # 写入文件
    if output_file is None:
        output_file = input_file

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    print(f"✓ 处理完成：{changes_made} 处拆分")
    print(f"✓ 已保存到：{output_file}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 tools/split_dialogues.py <markdown文件> [输出文件]")
        print("示例: python3 tools/split_dialogues.py chapter_md/002_夏本纪.md")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    split_dialogues_in_file(input_file, output_file)
