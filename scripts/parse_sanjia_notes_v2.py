#!/usr/bin/env python3
"""
从维基文库HTML提取三家注（集解、索隐、正义）V2版本
改进的解析逻辑，更好地处理嵌套HTML结构
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

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
        prev = small_tag.previous_sibling
        while prev:
            if isinstance(prev, NavigableString):
                text = str(prev).strip()
                if text and not text.startswith('，') and not text.startswith('。'):
                    anchor_text = text[-20:] if len(text) > 20 else text
                    break
            elif prev.name and prev.name not in ['small', 'script', 'style']:
                text = prev.get_text().strip()
                if text:
                    anchor_text = text[-20:] if len(text) > 20 else text
                    break
            prev = prev.previous_sibling

        # 获取small标签内的完整HTML文本
        html_content = str(small_tag)

        # 使用正则表达式提取三家注
        # 集解模式
        jijie_pattern = r'<span[^>]*background-color:\s*green[^>]*>集解</span><span[^>]*color:green[^>]*>(.*?)</span>(?=<span[^>]*background-color:|$)'
        # 索隐模式
        suoyin_pattern = r'<span[^>]*background-color:\s*deepPink[^>]*>索隱</span><span[^>]*color:deeppink[^>]*>(.*?)</span>(?=<span[^>]*background-color:|$)'
        # 正义模式 - 注意正义后面的文本没有特殊颜色标记
        zhengyi_pattern = r'<span[^>]*background-color:\s*#966[^>]*>正義</span>(.*?)(?=<span[^>]*background-color:|</small>)'

        # 提取集解
        jijie_matches = re.finditer(jijie_pattern, html_content, re.DOTALL)
        for match in jijie_matches:
            text_html = match.group(1)
            # 移除HTML标签，保留纯文本
            text_soup = BeautifulSoup(text_html, 'html.parser')
            text = text_soup.get_text().strip()
            if text:
                note_items.append({
                    'source': 'jijie',
                    'label': '集解',
                    'text': text
                })

        # 提取索隐
        suoyin_matches = re.finditer(suoyin_pattern, html_content, re.DOTALL)
        for match in suoyin_matches:
            text_html = match.group(1)
            text_soup = BeautifulSoup(text_html, 'html.parser')
            text = text_soup.get_text().strip()
            if text:
                note_items.append({
                    'source': 'suoyin',
                    'label': '索隱',
                    'text': text
                })

        # 提取正义
        zhengyi_matches = re.finditer(zhengyi_pattern, html_content, re.DOTALL)
        for match in zhengyi_matches:
            text_html = match.group(1)
            text_soup = BeautifulSoup(text_html, 'html.parser')
            text = text_soup.get_text().strip()
            if text:
                note_items.append({
                    'source': 'zhengyi',
                    'label': '正義',
                    'text': text
                })

        # 只有当有实际注释内容时才添加
        if note_items:
            notes.append({
                'id': f'n{note_id_counter:03d}',
                'anchor_text': anchor_text,
                'items': note_items,
                'sentence_id': None
            })
            note_id_counter += 1

    return notes

def main():
    # 输入和输出目录
    input_dir = Path('corpus/shiji/wikisource_sanjia')
    output_dir = Path('data/notes')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 先测试001
    test_file = input_dir / '001_五帝本紀.html'
    if test_file.exists():
        print(f'测试解析: {test_file.name}')
        notes = extract_notes_from_html(test_file)

        # 统计每种注的数量
        jijie_count = sum(1 for note in notes for item in note['items'] if item['source'] == 'jijie')
        suoyin_count = sum(1 for note in notes for item in note['items'] if item['source'] == 'suoyin')
        zhengyi_count = sum(1 for note in notes for item in note['items'] if item['source'] == 'zhengyi')

        print(f'  总计 {len(notes)} 个注释位置')
        print(f'  集解: {jijie_count} 条')
        print(f'  索隱: {suoyin_count} 条')
        print(f'  正義: {zhengyi_count} 条')

        # 显示前3个注释示例
        print('\n前3个注释示例:')
        for i, note in enumerate(notes[:3], 1):
            print(f'\n注释 {i} (id={note["id"]}, anchor="{note["anchor_text"][:10]}..."):')
            for item in note['items']:
                text_preview = item['text'][:50] + '...' if len(item['text']) > 50 else item['text']
                print(f'  [{item["label"]}] {text_preview}')

        # 保存
        output_data = {
            'chapter': '001_五帝本紀',
            'notes': notes
        }
        output_file = output_dir / '001-notes-v2.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f'\n已保存到: {output_file}')

if __name__ == '__main__':
    main()
