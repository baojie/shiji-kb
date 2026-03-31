#!/usr/bin/env python3
"""
从维基文库HTML提取三家注（集解、索隐、正义）
生成每章的notes JSON文件
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from collections import defaultdict

def extract_notes_from_html(html_path):
    """从维基文库HTML提取三家注"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    notes = []
    note_id_counter = 1

    # 查找所有包含三家注的<small>标签
    small_tags = soup.find_all('small', style=lambda value: value and 'color:var(--color-destructive--visited' in value)

    for small_tag in small_tags:
        note_items = []
        anchor_text = ""

        # 尝试找到锚点文本（注释前的文字）
        # 向前遍历，找到最近的正文文本
        prev = small_tag.previous_sibling
        while prev:
            if isinstance(prev, NavigableString):
                text = str(prev).strip()
                if text and not text.startswith('，') and not text.startswith('。'):
                    anchor_text = text[-20:] if len(text) > 20 else text  # 取最后20字作为锚点
                    break
            elif prev.name and prev.name not in ['small', 'span', 'a']:
                # 如果遇到其他标签，从其文本末尾提取
                text = prev.get_text().strip()
                if text:
                    anchor_text = text[-20:] if len(text) > 20 else text
                    break
            prev = prev.previous_sibling

        # 解析三家注内容
        # 查找所有带颜色标签的span（集解=green, 索隐=deeppink, 正义=#966或其他）
        note_spans = small_tag.find_all('span', style=lambda v: v and ('background-color' in v or 'color:green' in v or 'color:deeppink' in v))

        current_source = None
        current_text = []

        for span in note_spans:
            style = span.get('style', '')
            text = span.get_text().strip()

            # 识别注释类型标签
            if 'background-color: green' in style or text == '集解':
                # 保存前一个注释
                if current_source and current_text:
                    note_items.append({
                        'source': current_source,
                        'label': {'jijie': '集解', 'suoyin': '索隱', 'zhengyi': '正義'}[current_source],
                        'text': ''.join(current_text).strip()
                    })
                current_source = 'jijie'
                current_text = []
            elif 'background-color: deepPink' in style or text == '索隱':
                if current_source and current_text:
                    note_items.append({
                        'source': current_source,
                        'label': {'jijie': '集解', 'suoyin': '索隱', 'zhengyi': '正義'}[current_source],
                        'text': ''.join(current_text).strip()
                    })
                current_source = 'suoyin'
                current_text = []
            elif 'background-color: #966' in style or text == '正義':
                if current_source and current_text:
                    note_items.append({
                        'source': current_source,
                        'label': {'jijie': '集解', 'suoyin': '索隱', 'zhengyi': '正義'}[current_source],
                        'text': ''.join(current_text).strip()
                    })
                current_source = 'zhengyi'
                current_text = []
            elif 'color:green' in style and current_source == 'jijie':
                # 集解的内容文本
                current_text.append(text)
            elif 'color:deeppink' in style and current_source == 'suoyin':
                # 索隐的内容文本
                current_text.append(text)
            elif current_source == 'zhengyi' and not ('background-color' in style):
                # 正义的内容文本（没有特殊颜色标记）
                current_text.append(text)

        # 保存最后一个注释
        if current_source and current_text:
            note_items.append({
                'source': current_source,
                'label': {'jijie': '集解', 'suoyin': '索隱', 'zhengyi': '正義'}[current_source],
                'text': ''.join(current_text).strip()
            })

        # 只有当有实际注释内容时才添加
        if note_items:
            notes.append({
                'id': f'n{note_id_counter:03d}',
                'anchor_text': anchor_text,
                'items': note_items,
                'sentence_id': None  # 后续可以关联句子ID
            })
            note_id_counter += 1

    return notes

def main():
    # 输入和输出目录
    input_dir = Path('archive/wikisource_sanjia')
    output_dir = Path('data/notes')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 处理所有HTML文件
    html_files = sorted(input_dir.glob('*.html'))

    for html_file in html_files:
        print(f'正在处理: {html_file.name}')

        # 提取章节编号和名称
        # 文件名格式: 001_五帝本紀.html
        chapter_match = re.match(r'(\d+)_(.*?)\.html', html_file.name)
        if not chapter_match:
            print(f'  跳过: 无法解析文件名')
            continue

        chapter_num = chapter_match.group(1)
        chapter_name = chapter_match.group(2)

        # 提取注释
        notes = extract_notes_from_html(html_file)

        # 构建输出数据
        output_data = {
            'chapter': f'{chapter_num}_{chapter_name}',
            'notes': notes
        }

        # 保存为JSON
        output_file = output_dir / f'{chapter_num}-notes.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f'  提取 {len(notes)} 条注释 -> {output_file.name}')

if __name__ == '__main__':
    main()
