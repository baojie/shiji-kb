#!/usr/bin/env python3
"""
渲染战争事件HTML页面
将战争JSON数据渲染为HTML页面
"""

import json
from pathlib import Path

def generate_html(json_path, output_path):
    """生成HTML页面"""

    # 读取JSON数据
    with open(json_path, 'r', encoding='utf-8') as f:
        wars_data = json.load(f)

    # 统计信息
    total_wars = len(wars_data)
    multi_source = sum(1 for w in wars_data if w['source_count'] > 1)
    chapters = len(set(w['chapter_num'] for w in wars_data))

    # 生成HTML
    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>史记战争事件索引</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: "Source Han Serif SC", "Noto Serif SC", serif;
            line-height: 1.8;
            color: #333;
            background-color: #fdfaf6;
            padding: 20px;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        h1 {{
            text-align: center;
            color: #8b0000;
            font-size: 2.5em;
            margin-bottom: 10px;
            border-bottom: 3px double #8b0000;
            padding-bottom: 20px;
        }}

        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 40px;
            font-size: 1.1em;
        }}

        .stats {{
            background: #fff8dc;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
            border-left: 5px solid #8b0000;
        }}

        .stats h3 {{
            color: #8b0000;
            margin-bottom: 10px;
        }}

        .stats ul {{
            list-style: none;
            padding-left: 20px;
        }}

        .stats li {{
            margin: 5px 0;
        }}

        .nav {{
            background: #f5f5f5;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 5px;
        }}

        .nav a {{
            color: #8b0000;
            text-decoration: none;
            margin-right: 20px;
        }}

        .nav a:hover {{
            text-decoration: underline;
        }}

        .chapter-section {{
            margin-bottom: 60px;
        }}

        .chapter-header {{
            font-size: 1.8em;
            color: #8b0000;
            margin-bottom: 20px;
            border-left: 5px solid #8b0000;
            padding-left: 15px;
        }}

        .war-item {{
            margin-bottom: 40px;
            border-left: 3px solid #cd5c5c;
            padding-left: 20px;
            background: #fffaf0;
            padding: 20px;
            border-radius: 5px;
        }}

        .war-title {{
            font-size: 1.5em;
            color: #8b0000;
            margin-bottom: 10px;
            font-weight: bold;
        }}

        .war-id {{
            font-size: 0.9em;
            color: #666;
            margin-left: 10px;
        }}

        .war-meta {{
            margin: 15px 0;
            padding: 10px;
            background: white;
            border-radius: 3px;
        }}

        .meta-item {{
            margin: 8px 0;
            padding-left: 10px;
            border-left: 2px solid #ddd;
        }}

        .meta-label {{
            font-weight: bold;
            color: #8b0000;
            display: inline-block;
            width: 100px;
        }}

        .meta-value {{
            color: #333;
        }}

        .war-description {{
            margin-top: 15px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 3px;
            color: #555;
            line-height: 2;
        }}

        .multi-source {{
            display: inline-block;
            background: #ff6347;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            margin-left: 10px;
        }}

        .sources {{
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
            .nav {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>史记战争事件索引</h1>
        <div class="subtitle">War Events in Records of the Grand Historian</div>

        <div class="stats">
            <h3>统计概览</h3>
            <ul>
                <li><strong>总战争数</strong>: {total_wars} 个</li>
                <li><strong>多源战争</strong>: {multi_source} 个（在多个章节被记载）</li>
                <li><strong>单源战争</strong>: {total_wars - multi_source} 个</li>
                <li><strong>覆盖章节</strong>: {chapters} 章（占比 {chapters/130*100:.1f}%）</li>
                <li><strong>时间跨度</strong>: 前2690年（阪泉之战）— 前119年（漠北之战）</li>
            </ul>
        </div>

        <div class="nav">
            <a href="../../index.html">← 返回主页</a>
            <a href="special_index.html">专项索引</a>
            <a href="#" class="pdf">📥 下载PDF（待生成）</a>
        </div>

'''

    # 按章节分组
    by_chapter = {}
    for item in wars_data:
        chapter_key = f"{item['chapter_num']}_{item['chapter_title']}"
        if chapter_key not in by_chapter:
            by_chapter[chapter_key] = []
        by_chapter[chapter_key].append(item)

    # 生成各章节内容
    for chapter_key in sorted(by_chapter.keys()):
        wars = by_chapter[chapter_key]
        chapter_num, chapter_title = chapter_key.split('_', 1)

        html += f'''
        <div class="chapter-section" id="chapter-{chapter_num}">
            <h2 class="chapter-header">{chapter_num}_{chapter_title}</h2>
'''

        for war in wars:
            multi_badge = f'<span class="multi-source">{war["source_count"]}源</span>' if war['source_count'] > 1 else ''

            # 解析description中的各个字段
            desc_lines = war['description'].split('\n')
            meta_html = ''
            for line in desc_lines:
                if line.startswith('**') and '**:' in line:
                    label = line.split('**')[1]
                    value = line.split('**:', 1)[1].strip() if '**:' in line else ''
                    meta_html += f'''
                <div class="meta-item">
                    <span class="meta-label">{label}:</span>
                    <span class="meta-value">{value}</span>
                </div>
'''

            # 完整描述
            full_desc = war.get('full_description', '')
            if len(full_desc) > 300:
                full_desc = full_desc[:300] + '...'

            # 其他来源
            sources_html = ''
            if war['source_count'] > 1:
                other_chapters = ', '.join(war['chapters'][1:])
                sources_html = f'<div class="sources"><strong>其他来源</strong>: {other_chapters}</div>'

            html += f'''
            <div class="war-item">
                <div class="war-title">
                    {war['war_name']}
                    <span class="war-id">{war['war_id']}</span>
                    {multi_badge}
                </div>

                <div class="war-meta">
                    {meta_html}
                </div>

                <div class="war-description">
                    <strong>描述</strong>: {full_desc}
                </div>

                {sources_html}
            </div>
'''

        html += '''
        </div>
'''

    html += '''
    </div>
</body>
</html>
'''

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML已生成: {output_path}")
    print(f"总战争数: {total_wars}")
    print(f"多源战争: {multi_source}")
    print(f"覆盖章节: {chapters}")


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    json_path = project_root / 'data' / 'wars.json'
    output_path = project_root / 'docs' / 'special' / 'wars.html'

    generate_html(json_path, output_path)
