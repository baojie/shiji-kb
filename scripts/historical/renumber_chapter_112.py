#!/usr/bin/env python3
"""重新编号112章并添加段落空行"""

import re

file_path = "chapter_md/112_平津侯主父列传.tagged.md"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

result = []
pn_counter = 1  # 从1开始编号段落
prev_was_paragraph = False  # 跟踪上一行是否是段落

for i, line in enumerate(lines):
    stripped = line.rstrip()

    # 标题行
    if stripped.startswith('#'):
        # 修复第41行的错误标题
        if '拜为御史〖;大夫〗#夫〗' in stripped:
            stripped = stripped.replace('拜为御史〖;大夫〗#夫〗', '拜为御史〖;大夫〗')
        result.append(stripped)
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

    # 空行
    elif stripped == '':
        result.append('')
        prev_was_paragraph = False

    # ::: 块标记
    elif stripped == '::: 太史公曰' or stripped == ':::':
        result.append(stripped)
        prev_was_paragraph = False

    # 赞语诗句（无编号的内容）
    else:
        # 检查是否在赞语章节中（122号之后的诗句）
        if result and any('[122]' in l for l in result[-5:]):
            # 赞语诗句保持无编号
            if prev_was_paragraph and result and result[-1] != '':
                result.append('')
            result.append(stripped)
            prev_was_paragraph = True
        else:
            result.append(stripped)
            prev_was_paragraph = False

# 写入文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(result) + '\n')

print(f"✓ 112章重新编号完成")
print(f"✓ 总段落数: {pn_counter - 1}")
print(f"✓ 已添加段落间空行")
