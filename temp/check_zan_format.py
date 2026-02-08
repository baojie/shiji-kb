#!/usr/bin/env python3
"""检查所有章节的赞格式是否正确：
1. 各句换行
2. 所有句子在同一段（无空行）
3. 只有一个段落编号
"""

import re
import glob
import os

def check_zan_format(filepath):
    """检查单个文件的赞格式。返回 (has_zan, issues)"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 从后往前找赞标题
    zan_start = None
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if re.match(r'^#{1,4}\s+.*赞', line):
            zan_start = i
            break

    if zan_start is None:
        return False, []

    # 收集赞部分的内容（标题之后）
    content_lines = lines[zan_start + 1:]
    issues = []

    # 去掉开头的空行
    while content_lines and content_lines[0].strip() == '':
        content_lines = content_lines[1:]

    if not content_lines:
        return True, ['赞部分无内容']

    # 检查1：是否有多个段落编号（空行分隔的带编号行）
    numbered_lines = []
    for i, line in enumerate(content_lines):
        stripped = line.strip()
        # 去掉 > 前缀
        text = re.sub(r'^>\s*', '', stripped)
        if re.match(r'\[\d+', text):
            numbered_lines.append((i, stripped))

    if len(numbered_lines) > 1:
        issues.append(f'多个段落编号（{len(numbered_lines)}个）: {[l[1][:30] for l in numbered_lines[:3]]}...')

    # 检查2：是否有空行在内容中间（表示分段）
    # 找到第一个非空内容行和最后一个非空内容行
    first_content = None
    last_content = None
    for i, line in enumerate(content_lines):
        if line.strip():
            if first_content is None:
                first_content = i
            last_content = i

    if first_content is not None and last_content is not None:
        blank_lines_in_middle = []
        for i in range(first_content, last_content + 1):
            line = content_lines[i].strip()
            # > 后面跟空行也算空行（如 ">\n"）
            if line == '' or line == '>':
                blank_lines_in_middle.append(i + zan_start + 2)  # 1-based line number

        if blank_lines_in_middle:
            issues.append(f'赞内容中有{len(blank_lines_in_middle)}个空行（行号: {blank_lines_in_middle[:5]}）= 分段了')

    # 检查3：内容是否只有一行（应该多行）
    non_empty = [l for l in content_lines if l.strip() and l.strip() != '>']
    if len(non_empty) == 1 and len(non_empty[0].strip()) > 40:
        # 单行但很长，可能没换行
        text = non_empty[0].strip()
        # 检查是否有多个句号
        sentences = re.findall(r'[。！？]', text)
        if len(sentences) > 2:
            issues.append(f'可能未换行：单行{len(text)}字含{len(sentences)}个句号')

    return True, issues

def main():
    chapter_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'chapter_md')
    files = sorted(glob.glob(os.path.join(chapter_dir, '*.tagged.md')))

    has_zan_count = 0
    ok_count = 0
    problem_files = []

    for filepath in files:
        filename = os.path.basename(filepath)
        has_zan, issues = check_zan_format(filepath)
        if has_zan:
            has_zan_count += 1
            if issues:
                problem_files.append((filename, issues))
                print(f'✗ {filename}')
                for issue in issues:
                    print(f'    {issue}')
            else:
                ok_count += 1

    print(f'\n=== 统计 ===')
    print(f'有赞的章节: {has_zan_count}')
    print(f'格式正确: {ok_count}')
    print(f'有问题: {len(problem_files)}')

if __name__ == '__main__':
    main()
