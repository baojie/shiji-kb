#!/usr/bin/env python3
"""
从维基文库HTML提取三家注（集解、索隐、正义）V3版本
改进：添加anchor的前后文本context，便于精确定位
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

def extract_notes_from_html(html_path):
    """从维基文库HTML提取三家注，包含前后文context"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    notes = []
    note_id_counter = 1

    # 查找所有包含三家注的<small>标签
    small_tags = soup.find_all('small', style=lambda value: value and 'color:var(--color-destructive--visited' in value)

    for small_tag in small_tags:
        note_items = []
        anchor_text = ""
        before_context = ""
        after_context = ""

        # 提取前文context（anchor之前的文字）
        prev = small_tag.previous_sibling
        before_parts = []
        chars_collected = 0
        max_before_chars = 30  # 收集最多30字

        while prev and chars_collected < max_before_chars:
            if isinstance(prev, NavigableString):
                text = str(prev).strip()
                if text:
                    before_parts.insert(0, text)
                    chars_collected += len(text)
            elif prev.name and prev.name not in ['small', 'script', 'style']:
                text = prev.get_text().strip()
                if text:
                    before_parts.insert(0, text)
                    chars_collected += len(text)
            prev = prev.previous_sibling

        before_context = ''.join(before_parts)
        # 截取最后30字
        if len(before_context) > 30:
            before_context = '...' + before_context[-30:]

        # 提取anchor_text（最接近的文字作为锚点）
        if before_parts:
            last_part = before_parts[-1]
            anchor_text = last_part[-20:] if len(last_part) > 20 else last_part

        # 提取后文context（anchor之后的文字）
        next_elem = small_tag.next_sibling
        after_parts = []
        chars_collected = 0
        max_after_chars = 30  # 收集最多30字

        while next_elem and chars_collected < max_after_chars:
            if isinstance(next_elem, NavigableString):
                text = str(next_elem).strip()
                if text:
                    after_parts.append(text)
                    chars_collected += len(text)
            elif next_elem.name and next_elem.name not in ['small', 'script', 'style']:
                text = next_elem.get_text().strip()
                if text:
                    after_parts.append(text)
                    chars_collected += len(text)
                    break  # 遇到标签就停止
            next_elem = next_elem.next_sibling

        after_context = ''.join(after_parts)
        # 截取最前30字
        if len(after_context) > 30:
            after_context = after_context[:30] + '...'

        # 获取small标签内的完整HTML文本
        html_content = str(small_tag)

        # 使用正则表达式提取三家注
        # 集解模式
        jijie_pattern = r'<span[^>]*background-color:\s*green[^>]*>集解</span><span[^>]*color:green[^>]*>(.*?)</span>(?=<span[^>]*background-color:|$)'
        # 索隐模式
        suoyin_pattern = r'<span[^>]*background-color:\s*deepPink[^>]*>索隱</span><span[^>]*color:deeppink[^>]*>(.*?)</span>(?=<span[^>]*background-color:|$)'
        # 正义模式
        zhengyi_pattern = r'<span[^>]*background-color:\s*#966[^>]*>正義</span>(.*?)(?=<span[^>]*background-color:|</small>)'

        # 提取集解
        jijie_matches = re.finditer(jijie_pattern, html_content, re.DOTALL)
        for match in jijie_matches:
            text_html = match.group(1)
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
                'before_context': before_context,
                'after_context': after_context,
                'items': note_items,
                'sentence_id': None
            })
            note_id_counter += 1

    return notes

def main():
    # 输入和输出目录
    input_dir = Path('archive/wikisource_sanjia')
    output_dir = Path('data/notes')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取所有HTML文件并排序
    html_files = sorted(input_dir.glob('*.html'))

    print(f'找到 {len(html_files)} 个HTML文件，开始处理...\n')

    success_count = 0
    error_count = 0

    for html_file in html_files:
        try:
            # 提取章节编号和名称（如：001_五帝本紀）
            chapter_name = html_file.stem  # 去掉.html后缀
            chapter_num = chapter_name.split('_')[0]

            print(f'处理 [{chapter_num}] {chapter_name}...', end=' ')

            # 提取注释
            notes = extract_notes_from_html(html_file)

            if notes:
                # 统计每种注的数量
                jijie_count = sum(1 for note in notes for item in note['items'] if item['source'] == 'jijie')
                suoyin_count = sum(1 for note in notes for item in note['items'] if item['source'] == 'suoyin')
                zhengyi_count = sum(1 for note in notes for item in note['items'] if item['source'] == 'zhengyi')

                # 保存
                output_data = {
                    'chapter': chapter_name,
                    'notes': notes
                }
                output_file = output_dir / f'{chapter_num}-notes.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)

                print(f'✓ {len(notes)}个位置 (集解:{jijie_count} 索隐:{suoyin_count} 正义:{zhengyi_count})')
                success_count += 1
            else:
                print('⚠ 未提取到注释')
                # 仍然保存空文件
                output_data = {
                    'chapter': chapter_name,
                    'notes': []
                }
                output_file = output_dir / f'{chapter_num}-notes.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                success_count += 1

        except Exception as e:
            print(f'✗ 错误: {str(e)}')
            error_count += 1

    print(f'\n处理完成！')
    print(f'  成功: {success_count} 章')
    print(f'  失败: {error_count} 章')
    print(f'  数据保存在: {output_dir}/')

if __name__ == '__main__':
    main()
