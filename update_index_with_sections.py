#!/usr/bin/env python3
"""
提取章节HTML文件中的小标题，并更新index.html页面
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

def extract_sections_from_html(html_file):
    """提取HTML文件中的h2和h3标题"""
    sections = []

    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')

        # 提取h2和h3标题
        for tag in soup.find_all(['h2', 'h3']):
            # 获取文本内容（去掉span标签，只保留文本）
            text = tag.get_text(strip=True)

            # 尝试找到第一个有id的a标签或直接获取标签的id
            section_id = None
            a_tag = tag.find('a', id=True)
            if a_tag and a_tag.get('id'):
                section_id = a_tag.get('id')
            elif tag.get('id'):
                section_id = tag.get('id')

            if text:
                sections.append({
                    'level': tag.name,  # h2 or h3
                    'text': text,
                    'id': section_id
                })
    except Exception as e:
        print(f"Error processing {html_file}: {e}")

    return sections

def generate_index_html(chapters_dir, output_file):
    """生成包含小标题的index.html"""

    # 扫描所有HTML文件
    html_files = sorted(Path(chapters_dir).glob('*.tagged.html'))

    chapters_info = []
    for html_file in html_files:
        filename = html_file.name
        # 提取章节号和标题
        match = re.match(r'(\d+)_(.+?)\.tagged\.html', filename)
        if match:
            chapter_num = match.group(1)
            chapter_title = match.group(2)
            sections = extract_sections_from_html(html_file)

            chapters_info.append({
                'num': chapter_num,
                'title': chapter_title,
                'filename': filename,
                'sections': sections
            })

    # 生成HTML内容
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>史记 - 知识库</title>
    <link rel="stylesheet" href="css/shiji-styles.css">
    <style>
        .chapter-list {
            list-style: none;
            padding: 0;
        }

        .chapter-item {
            margin: 30px 0;
            padding: 20px;
            background-color: #fffef0;
            border-left: 5px solid #8B4513;
            border-radius: 5px;
            transition: background-color 0.3s;
        }

        .chapter-item:hover {
            background-color: #FFF8E1;
        }

        .chapter-title {
            text-decoration: none;
            color: #8B0000;
            font-size: 1.3em;
            font-weight: 600;
            display: block;
            margin-bottom: 15px;
        }

        .chapter-title:hover {
            color: #8B4513;
        }

        .sections-container {
            margin-top: 10px;
            padding-left: 10px;
        }

        .section-link {
            display: inline-block;
            margin: 5px 15px 5px 0;
            padding: 3px 0;
            color: #555;
            text-decoration: none;
            font-size: 0.95em;
            transition: color 0.2s;
        }

        .section-link:hover {
            color: #8B4513;
            text-decoration: underline;
        }

        .section-link.h2 {
            font-weight: 500;
            color: #333;
        }

        .section-link.h3 {
            margin-left: 20px;
            color: #666;
            font-size: 0.9em;
        }

        .section-link.h3:before {
            content: "· ";
            color: #999;
        }

        .intro {
            background-color: #faf8ff;
            padding: 20px;
            border-radius: 5px;
            border: 1px solid #e6e0c0;
            margin: 30px 0;
        }

        .intro h2 {
            margin-top: 0;
            border: none;
            padding: 0;
        }
    </style>
</head>
<body>
    <h1>史记 - 知识库</h1>

    <div class="intro">
        <h2>简介</h2>
        <p>本项目是《史记》知识库的在线展示，对文本进行了命名实体标注，包括人名、地名、官职、朝代、族群、器物等类别，并进行了段落编号和对话标识，便于阅读和研究。</p>
        <p>文本中的实体使用不同颜色和样式标识：
            <span class="person">人名</span>、
            <span class="place">地名</span>、
            <span class="official">官职</span>、
            <span class="dynasty">朝代/氏族</span>、
            <span class="tribe">族群</span>、
            <span class="artifact">器物</span> 等。
        </p>
    </div>

    <h2>章节目录</h2>

    <ul class="chapter-list">
'''

    # 添加每个章节
    for chapter in chapters_info:
        html_content += f'''        <li class="chapter-item">
            <a href="chapters/{chapter['filename']}" class="chapter-title">{chapter['num']} {chapter['title']}</a>
'''

        # 添加小标题
        if chapter['sections']:
            html_content += '            <div class="sections-container">\n'
            for section in chapter['sections']:
                section_class = section['level']
                section_text = section['text']
                section_id = section['id']

                if section_id:
                    link = f"chapters/{chapter['filename']}#{section_id}"
                else:
                    link = f"chapters/{chapter['filename']}"

                html_content += f'                <a href="{link}" class="section-link {section_class}">{section_text}</a>\n'

            html_content += '            </div>\n'

        html_content += '        </li>\n'

    # 结束HTML
    html_content += '''    </ul>

    <hr>

    <footer style="text-align: center; color: #666; margin-top: 40px;">
        <p>史记知识库 | 命名实体标注版</p>
    </footer>
</body>
</html>
'''

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ 已生成更新的index.html，包含 {len(chapters_info)} 个章节的小标题")

if __name__ == '__main__':
    chapters_dir = '/home/baojie/work/shiji-kb/docs/chapters'
    output_file = '/home/baojie/work/shiji-kb/docs/index.html'

    generate_index_html(chapters_dir, output_file)
