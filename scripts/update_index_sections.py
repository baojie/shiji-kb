#!/usr/bin/env python3
"""
更新docs/index.html中的小节链接

读取kg/structure/data/sections_data.json，为每个章节生成小节链接，
替换index.html中的<div class="chapter-desc">内容
"""

import json
import re
import urllib.parse
from pathlib import Path


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
    for section in display_sections:
        title = section["title"]
        # 生成与HTML文件中相同的锚点ID
        heading_id = generate_heading_id(title)
        # 清理显示文本中的实体标注
        display_title = clean_entity_markers(title)
        link = f'<a href="chapters/{chapter_name}.html#{heading_id}">{display_title}</a>'
        links.append(link)

    if has_more:
        links.append(f'<span class="section-more">... 共{len(sections)}节</span>')

    return ' · '.join(links)


def update_index_html(index_file='docs/index.html', sections_file='kg/structure/data/sections_data.json'):
    """更新index.html中的章节小节链接"""

    # 读取sections数据
    print(f"读取小节数据: {sections_file}")
    with open(sections_file, 'r', encoding='utf-8') as f:
        sections_data = json.load(f)

    print(f"共 {len(sections_data)} 个章节有小节数据")

    # 读取index.html
    print(f"\n读取 {index_file}")
    with open(index_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 查找并替换每个章节的chapter-desc
    # 匹配格式：
    # <a href="chapters/NNN_章节名.html">章节名</a>
    # </div>
    # <div class="chapter-desc">原有描述</div>

    pattern = r'(<a href="chapters/(\d+_[^"]+)\.html">[^<]+</a>\s*</div>\s*<div class="chapter-desc">)[^<]*(</div>)'

    def replace_func(match):
        full_match = match.group(0)
        prefix = match.group(1)
        chapter_name = match.group(2)
        suffix = match.group(3)

        # 获取该章节的小节数据
        if chapter_name in sections_data:
            sections = sections_data[chapter_name]
            section_links = generate_section_links_html(chapter_name, sections)
            return f"{prefix}{section_links}{suffix}"
        else:
            # 没有小节数据，保持原样
            return full_match

    updated_html = re.sub(pattern, replace_func, html_content)

    # 统计更新了多少章节
    updates = re.findall(pattern, html_content)
    print(f"\n找到 {len(updates)} 个章节可更新")

    # 写回文件
    print(f"写入更新后的 {index_file}")
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(updated_html)

    print("\n✓ 更新完成!")


if __name__ == '__main__':
    update_index_html()
