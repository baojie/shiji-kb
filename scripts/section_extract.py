#!/usr/bin/env python3
"""
提取所有章节的小节信息
为index.html生成小节链接
"""

import re
from pathlib import Path
import json
import urllib.parse

def extract_sections_from_chapter(md_file):
    """从markdown文件中提取主要段落（二级标题）"""
    sections = []

    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配二级标题：## 标题
        pattern = r'^## (.+)$'

        for line in content.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                title = match.group(1).strip()
                sections.append({
                    'title': title
                })

    except Exception as e:
        print(f"Error processing {md_file}: {e}")

    return sections


def process_all_chapters():
    """处理所有130个章节"""

    chapter_dir = Path('chapter_md')
    result = {}

    # 获取所有tagged.md文件
    md_files = sorted(chapter_dir.glob('*.tagged.md'))

    print(f"Found {len(md_files)} tagged markdown files")

    for md_file in md_files:
        chapter_name = md_file.stem.replace('.tagged', '')
        sections = extract_sections_from_chapter(md_file)

        if sections:
            result[chapter_name] = sections
            print(f"{chapter_name}: {len(sections)} sections")

    return result


def generate_heading_id(text):
    """从标题文本生成URL安全的锚点ID（与render_shiji_html.py保持一致）"""
    # 移除〖TYPE content|canonical〗标注，保留content（消歧格式）
    clean_text = re.sub(r'〖[^〗]*?\|([^〗|]+)〗', r'\1', text)
    # 移除〖TYPE content〗标注，保留content（普通格式）
    clean_text = re.sub(r'〖[^〗]+?〗', lambda m: m.group(0)[2:-1], clean_text)
    # 移除⟦TYPE content⟧标注（动词），保留content
    clean_text = re.sub(r'⟦[^⟧]+?⟧', lambda m: m.group(0)[2:-1], clean_text)
    # 移除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', clean_text)
    # URL编码（中文会被编码）
    return urllib.parse.quote(clean_text.strip())


def clean_entity_markers(text):
    """移除文本中的实体标注符号，用于显示"""
    # 移除〖TYPE content|canonical〗标注，保留content（消歧格式）
    clean = re.sub(r'〖[^〗]*?\|([^〗|]+)〗', r'\1', text)
    # 移除〖TYPE content〗标注，保留content（普通格式）
    clean = re.sub(r'〖[^〗]+?〗', lambda m: m.group(0)[2:-1], clean)
    # 移除⟦TYPE content⟧标注（动词），保留content
    clean = re.sub(r'⟦[^⟧]+?⟧', lambda m: m.group(0)[2:-1], clean)
    return clean.strip()


def generate_section_links_html(chapter_name, sections, max_display=10):
    """为一个章节生成小节链接的HTML"""

    if not sections:
        return ""

    # 限制显示的小节数量
    display_sections = sections[:max_display]
    has_more = len(sections) > max_display

    links = []
    for i, section in enumerate(display_sections):
        title = section["title"]
        # 生成与HTML文件中相同的锚点ID
        heading_id = generate_heading_id(title)
        # 清理显示文本中的实体标注
        display_title = clean_entity_markers(title)
        link = f'<a href="chapters/{chapter_name}.html#{heading_id}">{display_title}</a>'
        links.append(link)

    if has_more:
        links.append(f'<span class="more-sections">... 共{len(sections)}节</span>')

    html = '<div class="section-links">' + ' · '.join(links) + '</div>'
    return html


def save_sections_data(data, output_file='kg/structure/data/sections_data.json'):
    """保存提取的段落数据"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved sections data to {output_file}")


if __name__ == '__main__':
    print("Extracting sections from all chapters...")
    print("=" * 60)

    # 提取所有章节的段落信息
    sections_data = process_all_chapters()

    print("=" * 60)
    print(f"\nTotal chapters processed: {len(sections_data)}")

    # 保存数据
    save_sections_data(sections_data)

    # 显示示例
    print("\n" + "=" * 60)
    print("Sample HTML output for chapter 092:")
    print("=" * 60)

    if '092_淮阴侯列传' in sections_data:
        sample_html = generate_section_links_html(
            '092_淮阴侯列传',
            sections_data['092_淮阴侯列传']
        )
        print(sample_html)

    print("\nDone!")
