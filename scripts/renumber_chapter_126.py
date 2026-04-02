#!/usr/bin/env python3
"""重新编号126章滑稽列传"""

import re

file_path = "chapter_md/126_滑稽列传.tagged.md"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复标题
content = content.replace('# 滑稽列传', '# [0] 滑稽列传')

# 修复标注错误
content = content.replace('棺椁〖;大夫〗#夫〗礼', '棺椁〖;大夫〗礼')
content = content.replace('〖#子〗#子〗也', '〖#子〗也')

# 按行处理
lines = content.split('\n')
result = []
pn_counter = 1  # 从1开始正式段落编号

for line in lines:
    stripped = line.rstrip()

    # Purple Number行
    if stripped.startswith('['):
        # 提取编号和内容
        match = re.match(r'\[[\d\.]+\]\s*(.*)', stripped)
        if match:
            content_text = match.group(1)

            # 重新编号
            result.append(f'[{pn_counter}] {content_text}')
            pn_counter += 1
        else:
            result.append(stripped)
    else:
        result.append(stripped)

# 写入文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(result) + '\n')

print(f"✓ 126章重新编号完成")
print(f"✓ 总段落数: {pn_counter - 1}")
print(f"✓ 标题已添加[0]编号")
print(f"✓ 已修复标注错误")
