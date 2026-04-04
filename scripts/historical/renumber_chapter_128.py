#!/usr/bin/env python3
"""重新编号128章龟策列传"""

import re

file_path = "chapter_md/128_龟策列传.tagged.md"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

result = []
pn_counter = 1  # 从1开始编号段落

for i, line in enumerate(lines):
    stripped = line.rstrip()

    # 标题行
    if stripped.startswith('#'):
        result.append(stripped)

    # 空行
    elif stripped == '':
        result.append('')

    # Purple Number段落
    elif stripped.startswith('['):
        # 提取编号后的内容
        match = re.match(r'\[[\d\.]+\]\s*(.*)', stripped)
        if match:
            content = match.group(1)
            # 重新编号
            result.append(f'[{pn_counter}] {content}')
            pn_counter += 1
        else:
            result.append(stripped)

    # 引用块等其他内容
    else:
        result.append(stripped)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(result) + '\n')

print(f"✓ 128章重新编号完成")
print(f"✓ 总段落数: {pn_counter - 1}")
