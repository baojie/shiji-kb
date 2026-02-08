#!/usr/bin/env python3
"""
更新index.html，添加小节链接并改进样式
"""
import json
import re
from pathlib import Path

def load_sections_data():
    """加载小节数据"""
    with open('sections_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_section_links(chapter_name, sections_data):
    """为一个章节生成小节链接的HTML，显示所有小节"""
    if chapter_name not in sections_data:
        return ""

    sections = sections_data[chapter_name]
    if not sections:
        return ""

    # 过滤掉无锚点和通用段落名的小节
    sections = [s for s in sections
                if s.get('anchor') and not s['title'].startswith('段落')]

    if not sections:
        return ""

    links = []
    for section in sections:
        anchor = section["anchor"]
        link = f'<a href="chapters/{chapter_name}.html#pn-{anchor}">[{anchor}] {section["title"]}</a>'
        links.append(link)

    html = '<div class="section-links">' + ' · '.join(links) + '</div>'
    return html

def read_index_html():
    """读取现有的index.html"""
    with open('docs/index.html', 'r', encoding='utf-8') as f:
        return f.read()

def update_index_html(sections_data):
    """更新index.html"""
    content = read_index_html()

    # 1. 改进统计部分的CSS
    # 找到 .stats 的样式定义并替换
    new_stats_style = """        .stats {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 30px;
            border-radius: 12px;
            margin-bottom: 40px;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }

        .stats h3 {
            color: white;
            text-align: center;
            font-size: 1.8em;
            margin-top: 0;
            margin-bottom: 30px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 25px;
            margin-top: 15px;
        }

        .stat-item {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px 20px;
            border-radius: 10px;
            text-align: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        .stat-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            background: white;
        }

        .stat-num {
            font-size: 2.8em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .stat-label {
            color: #555;
            font-size: 1em;
            margin-top: 8px;
            font-weight: 500;
        }"""

    # 替换 .stats 样式块
    old_stats_block = re.search(
        r'        \.stats \{.*?        \.stat-label \{.*?\}',
        content,
        re.DOTALL
    )
    if old_stats_block:
        content = content.replace(old_stats_block.group(0), new_stats_style)

    # 2. 添加小节链接的CSS样式（仅在尚未存在时添加）
    if '.section-links {' not in content:
        section_links_style = """
        .section-links {
            margin-top: 12px;
            padding-top: 10px;
            border-top: 1px dashed #d4af37;
            font-size: 0.85em;
            line-height: 1.8;
        }

        .section-links a {
            color: #8B4513;
            text-decoration: none;
            transition: color 0.2s ease;
        }

        .section-links a:hover {
            color: #d4af37;
            text-decoration: underline;
        }

        .more-sections {
            color: #999;
            font-style: italic;
        }
"""
        # 在 footer 样式前插入
        content = content.replace(
            '        footer {',
            section_links_style + '\n        footer {'
        )

    # 3. 先移除已有的小节链接（避免重复）
    content = re.sub(r'\s*<div class="section-links">.*?</div>', '', content)

    # 4. 为每个章节卡片添加小节链接
    def add_section_links_to_card(match):
        card_html = match.group(0)

        # 提取章节名称（兼容 .tagged.html 和 .html）
        chapter_match = re.search(
            r'<a href="chapters/(\d+_[^"]+?)(?:\.tagged)?\.html">',
            card_html
        )

        if not chapter_match:
            return card_html

        chapter_name = chapter_match.group(1)

        # 生成小节链接
        section_links_html = generate_section_links(chapter_name, sections_data)

        if not section_links_html:
            return card_html

        # 在 chapter-desc 的闭合 div 之后插入
        desc_div_match = re.search(r'<div class="chapter-desc">.*?</div>', card_html, re.DOTALL)
        if desc_div_match:
            insert_pos = desc_div_match.end()
            new_card = card_html[:insert_pos] + '\n                ' + section_links_html + card_html[insert_pos:]
            return new_card

        return card_html

    # 匹配所有的 chapter-card（使用更精确的模式）
    content = re.sub(
        r'<div class="chapter-card">\s*<div class="chapter-title">.*?</div>\s*<div class="chapter-desc">.*?</div>\s*</div>',
        add_section_links_to_card,
        content,
        flags=re.DOTALL
    )

    return content

def main():
    print("加载小节数据...")
    sections_data = load_sections_data()
    print(f"已加载 {len(sections_data)} 个章节的小节信息")

    print("\n更新index.html...")
    updated_content = update_index_html(sections_data)

    # 保存更新后的文件
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print("✅ index.html 更新完成！")
    print("   - 改进了统计部分的样式（渐变色、卡片效果）")
    print("   - 为每章添加了小节链接（最多显示6个）")

if __name__ == '__main__':
    main()
