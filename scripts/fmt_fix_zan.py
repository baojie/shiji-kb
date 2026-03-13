#!/usr/bin/env python3
"""修复所有章节的"赞"格式：合并为单编号，句子换行不分段。

适配 ::: 赞 fenced div 格式。

规则：
- 赞部分各句子换行但不分段（无空行）
- 整个赞只保留一个段落编号（第一个 [X.Y]）
- 后续句子去掉 [X.Y] 编号，直接换行
"""

import re
import glob
import os


def fix_zan_format(filepath):
    """修复单个文件的赞格式。返回是否有修改。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    in_zan = False
    zan_lines = []
    modified = False

    for line in lines:
        if line.strip() == '::: 赞':
            in_zan = True
            zan_lines = []
            new_lines.append(line)
            continue

        if in_zan and line.strip() == ':::':
            # 处理收集到的赞内容：合并编号
            first_number = None
            merged = []
            for zl in zan_lines:
                stripped = zl.strip()
                if not stripped:
                    continue
                m = re.match(r'\[(\d+(?:\.\d+)*)\]\s*(.*)', stripped)
                if m:
                    if first_number is None:
                        first_number = m.group(1)
                        merged.append(f'[{first_number}] {m.group(2)}')
                    else:
                        # 去掉后续编号
                        merged.append(m.group(2))
                        modified = True
                else:
                    merged.append(stripped)

            for ml in merged:
                new_lines.append(ml)
            new_lines.append(line)  # closing :::
            in_zan = False
            continue

        if in_zan:
            zan_lines.append(line)
        else:
            new_lines.append(line)

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

    return modified


def main():
    chapter_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'chapter_md')
    files = sorted(glob.glob(os.path.join(chapter_dir, '*.tagged.md')))

    modified = []

    for filepath in files:
        filename = os.path.basename(filepath)
        if fix_zan_format(filepath):
            modified.append(filename)
            print(f'✓ 已修复: {filename}')

    print(f'\n共修复 {len(modified)} 个文件')


if __name__ == '__main__':
    main()
