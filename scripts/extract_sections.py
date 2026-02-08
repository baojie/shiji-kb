#!/usr/bin/env python3
"""
提取所有章节的小节信息
为index.html生成小节链接
"""

import re
from pathlib import Path
import json

def extract_sections_from_chapter(md_file):
    """从markdown文件中提取主要段落（一级段落）"""
    sections = []

    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配一级段落：## [数字] 标题
        # 匹配格式：## [0] 标题 或 ## [1] 标题 等
        pattern = r'^## \[(\d+)\] (.+)$'

        for line in content.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                num = match.group(1)
                title = match.group(2)
                sections.append({
                    'num': num,
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


def generate_section_links_html(chapter_name, sections, max_display=8):
    """为一个章节生成小节链接的HTML"""

    if not sections:
        return ""

    # 限制显示的小节数量
    display_sections = sections[:max_display]
    has_more = len(sections) > max_display

    links = []
    for section in display_sections:
        # 生成链接，格式：chapters/章节名.tagged.html#pn-段落号
        link = f'<a href="chapters/{chapter_name}.tagged.html#pn-{section["num"]}">[{section["num"]}] {section["title"]}</a>'
        links.append(link)

    if has_more:
        links.append(f'<span class="more-sections">... 共{len(sections)}节</span>')

    html = '<div class="section-links">' + ' · '.join(links) + '</div>'
    return html


def save_sections_data(data, output_file='sections_data.json'):
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
