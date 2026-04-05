#!/usr/bin/env python3
"""
为17篇新发现的赞添加区块标注

基于detect_hidden_yunwen.py的检测结果，自动添加 ## 赞 标题和 ::: 赞 区块标记
"""

import json
from pathlib import Path
import re


def add_zan_block_to_chapter(chapter_file, zan_text, start_line):
    """
    在指定位置添加赞区块标注

    参数:
        chapter_file: 章节文件路径
        zan_text: 赞的完整文本
        start_line: 赞开始的行号（1-based）
    """
    with open(chapter_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 计算要插入的位置（转为0-based）
    insert_pos = start_line - 1

    # 获取赞的行数
    zan_lines = zan_text.strip().split('\n')
    zan_end_pos = insert_pos + len(zan_lines)

    # 检查赞的前面是否有 ## 赞 标题
    has_zan_title = False
    title_pos = -1

    # 向前查找最近的 ## 标题
    for i in range(insert_pos - 1, max(0, insert_pos - 10), -1):
        line = lines[i].strip()
        if line == '## 赞':
            has_zan_title = True
            title_pos = i
            break
        elif line.startswith('##'):
            # 遇到其他二级标题，说明没有赞标题
            break

    # 准备插入的内容
    insertions = []

    if not has_zan_title:
        # 需要添加 ## 赞 标题
        # 在赞内容前插入空行、标题、空行
        insertions.append((insert_pos, '\n'))
        insertions.append((insert_pos, '## 赞\n'))
        insertions.append((insert_pos, '\n'))
        insert_pos += 3

    # 在赞内容前添加 ::: 赞
    insertions.append((insert_pos, '::: 赞\n'))
    insertions.append((insert_pos, '\n'))

    # 在赞内容后添加 :::
    end_insert_pos = insert_pos + len(zan_lines) + 2
    insertions.append((end_insert_pos, '\n'))
    insertions.append((end_insert_pos, ':::\n'))

    # 反向插入（从后往前），避免索引偏移
    insertions.sort(key=lambda x: x[0], reverse=True)
    for pos, text in insertions:
        lines.insert(pos, text)

    # 写回文件
    with open(chapter_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return True


def process_missing_chapters():
    """处理所有缺失赞标注的章节"""

    project_root = Path(__file__).parent.parent
    detection_file = project_root / "logs/hidden_yunwen_detection.json"
    chapter_dir = project_root / "chapter_md"

    # 读取检测结果
    with open(detection_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # 筛选出明确的赞（得分≥0.9，主要是4字句）
    chapters_to_process = []
    for chapter_num, data in results.items():
        for item in data['potential_yunwen']:
            if item['score'] >= 0.9 and item['char_dist'].get('4', 0) >= 8:
                chapters_to_process.append({
                    'chapter_num': chapter_num,
                    'title': data['title'],
                    'zan_text': item['full_text'],
                    'start_line': item['start_line'],
                    'score': item['score']
                })
                break

    print(f"准备处理 {len(chapters_to_process)} 个章节\n")

    for item in chapters_to_process:
        chapter_num = item['chapter_num']
        chapter_title = item['title']

        # 查找章节文件
        chapter_files = list(chapter_dir.glob(f"{chapter_num}_*.tagged.md"))
        if not chapter_files:
            print(f"⚠ 跳过 {chapter_num}: 找不到文件")
            continue

        chapter_file = chapter_files[0]

        # 检查是否已经有 ::: 赞 标记
        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if '::: 赞' in content:
            print(f"✓ 跳过 {chapter_num} {chapter_title}: 已有 ::: 赞 标记")
            continue

        # 添加区块标注
        try:
            add_zan_block_to_chapter(chapter_file, item['zan_text'], item['start_line'])
            print(f"✓ {chapter_num} {chapter_title}: 已添加赞区块标注（第{item['start_line']}行起）")
        except Exception as e:
            print(f"✗ {chapter_num} {chapter_title}: 处理失败 - {e}")

    print(f"\n完成！共处理 {len(chapters_to_process)} 个章节")


if __name__ == "__main__":
    process_missing_chapters()
