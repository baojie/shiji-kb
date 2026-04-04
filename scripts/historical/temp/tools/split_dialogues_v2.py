#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话拆分工具 V2 - 简化版
将包含多个"X曰"的段落拆分成独立的对话行

策略：
1. 在每个"X曰："或"X曰："之前拆分（除了第一个）
2. 保持引号完整性

用法：
    python3 tools/split_dialogues_v2.py chapter_md/002_夏本纪.md
"""

import re
import sys
from pathlib import Path


def split_dialogue_line(line):
    """
    拆分包含多个"X曰"的行

    策略：找到所有"X曰："或"X曰："的位置，在每个位置之前拆分
    """
    # 找到所有"曰："或"曰："的位置
    pattern = r'([^曰]+曰[：:])'
    matches = list(re.finditer(pattern, line))

    if len(matches) <= 1:
        return [line]

    result = []

    # 第一段：从开头到第一个"曰"之后的引号结束
    first_match = matches[0]
    first_end = first_match.end()

    # 找到第一个引号结束的位置
    quote_end = find_next_quote_end(line, first_end)
    if quote_end > first_end:
        result.append(line[:quote_end].strip())
        last_pos = quote_end
    else:
        # 没有引号，到句号
        period_pos = line.find('。', first_end)
        if period_pos > 0:
            result.append(line[:period_pos + 1].strip())
            last_pos = period_pos + 1
        else:
            result.append(line[:first_end].strip())
            last_pos = first_end

    # 后续段：从上一个位置到下一个"曰"之前
    for i in range(1, len(matches)):
        match = matches[i]
        match_end = match.end()

        # 找到这个"曰"之后的引号结束
        quote_end = find_next_quote_end(line, match_end)
        if quote_end > match_end:
            result.append(line[last_pos:quote_end].strip())
            last_pos = quote_end
        else:
            # 没有引号，到句号或下一个"曰"
            if i + 1 < len(matches):
                next_start = matches[i + 1].start()
                result.append(line[last_pos:next_start].strip())
                last_pos = next_start
            else:
                # 最后一段
                result.append(line[last_pos:].strip())
                last_pos = len(line)

    # 添加剩余部分
    if last_pos < len(line):
        remaining = line[last_pos:].strip()
        if remaining:
            result.append(remaining)

    return [r for r in result if r]


def find_next_quote_end(text, start_pos):
    """
    从start_pos开始查找下一个引号结束的位置
    """
    # 引号对
    quote_pairs = {
        '"': '"',
        "'": "'",
        '「': '」',
        '『': '』'
    }

    # 查找开始引号
    for i in range(start_pos, len(text)):
        if text[i] in quote_pairs:
            # 找到开始引号，查找结束引号
            closing = quote_pairs[text[i]]
            for j in range(i + 1, len(text)):
                if text[j] == closing:
                    return j + 1
            break

    return start_pos


def split_dialogues_in_file(input_file, output_file=None):
    """
    处理文件中的对话拆分
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
        print("用法: python3 tools/split_dialogues_v2.py <markdown文件> [输出文件]")
        print("示例: python3 tools/split_dialogues_v2.py chapter_md/002_夏本纪.md")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    split_dialogues_in_file(input_file, output_file)
