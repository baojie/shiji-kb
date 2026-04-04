#!/usr/bin/env python3
"""重新编号127章日者列传"""

import re

file_path = "chapter_md/127_日者列传.tagged.md"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

result = []
pn_counter = 1  # 从1开始编号段落
prev_was_paragraph = False  # 跟踪上一行是否是段落
in_chu_section = False  # 标记是否进入褚先生补述部分

for i, line in enumerate(lines):
    stripped = line.rstrip()

    # 标题行
    if stripped.startswith('#'):
        # 修复第1行的标题
        if i == 0 and stripped == '# 日者列传':
            result.append('# [0] 日者列传')
        else:
            result.append(stripped)
        prev_was_paragraph = False
        # 检测是否进入褚先生补述部分
        if '褚先生补述' in stripped:
            in_chu_section = True

    # 空行
    elif stripped == '':
        result.append('')
        prev_was_paragraph = False

    # Purple Number段落
    elif stripped.startswith('['):
        # 提取编号后的内容
        match = re.match(r'\[[\d\.]+\]\s*(.*)', stripped)
        if match:
            content = match.group(1)

            # 如果上一行也是段落，且result最后一行不是空行，插入空行
            if prev_was_paragraph and result and result[-1] != '':
                result.append('')

            # 重新编号
            result.append(f'[{pn_counter}] {content}')
            pn_counter += 1
            prev_was_paragraph = True
        else:
            result.append(stripped)
            prev_was_paragraph = False

    # 引用块（太史公曰等）
    elif stripped.startswith(':::'):
        result.append(stripped)
        prev_was_paragraph = False

    # 褚先生补述部分的普通段落（需要添加PN）
    elif in_chu_section and stripped and not stripped.startswith('#') and not stripped.startswith('['):
        # 如果上一行也是段落，且result最后一行不是空行，插入空行
        if prev_was_paragraph and result and result[-1] != '':
            result.append('')

        # 为褚先生补述部分添加Purple Number
        result.append(f'[{pn_counter}] {stripped}')
        pn_counter += 1
        prev_was_paragraph = True

    # 其他行（包括太史公曰等前言部分的普通段落，保持不变）
    else:
        result.append(stripped)
        prev_was_paragraph = False

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(result) + '\n')

print(f"✓ 127章重新编号完成")
print(f"✓ 总段落数: {pn_counter - 1}")
