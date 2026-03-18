#!/usr/bin/env python3
"""
渲染韵文HTML页面
将韵文JSON数据渲染为带实体高亮的HTML页面
"""

import json
import re
from pathlib import Path

# 实体类型与颜色映射（与太史公曰保持一致）
ENTITY_COLORS = {
    '@': ('person', '人名', '#c00'),
    '=': ('place', '地名', '#080'),
    '^': ('office', '官职', '#660'),
    '%': ('time', '时间', '#06c'),
    '•': ('object', '器物', '#c0c'),
    '{': ('book', '典籍', '#900'),
    '&': ('clan', '氏族', '#c60'),
    "'": ('state', '邦国', '#009'),
    '~': ('event', '事件', '#690'),
    '#': ('identity', '身份', '#939'),
    '+': ('biology', '生物', '#060'),
    '?': ('myth', '神话', '#939'),
    ';': ('title', '称号', '#960'),
    '!': ('concept', '概念', '#069'),
    '$': ('measure', '度量', '#666'),
    ':': ('position', '方位', '#093'),
    '[': ('artifact', '古物', '#c6c'),
}

def render_entity_tags(text):
    """将实体标注转换为HTML span标签"""
    for marker, (css_class, title, color) in ENTITY_COLORS.items():
        # 〖TYPE 内容〗 格式
        pattern = f'〖{re.escape(marker)}([^〗]+)〗'
        replacement = f'<span class="entity {css_class}" title="{title}">\\1</span>'
        text = re.sub(pattern, replacement, text)

    # 处理其他标注（如 〖_xxx〗、〖\xxx〗）
    text = re.sub(r'〖[_\\]([^〗]+)〗', r'<span class="entity other" title="其他标注">\1</span>', text)

    return text

def format_yunwen_content(content, yunwen_type):
    """
    格式化韵文内容
    - 保留原文的分行
    - 加粗诗句（** 包围的部分）
    - 转换实体标注
    """
    lines = content.split('\n')
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 去掉段落编号 [N] 或 [N.M]
        line = re.sub(r'^\[\d+(?:\.\d+)?\]\s*', '', line)

        # 处理加粗标记 **text**
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)

        # 转换实体标注
        line = render_entity_tags(line)

        formatted_lines.append(line)

    # 根据类型决定分行方式
    if yunwen_type in ['赞', '诗歌']:
        # 诗歌类：每行独立，用<br>分隔
        return '<br>\n'.join(formatted_lines)
    else:
        # 赋类：段落式，用双<br>分隔
        return '<br><br>\n'.join(formatted_lines)

def generate_html(json_path, output_path):
    """生成HTML页面"""

    # 读取JSON数据
    with open(json_path, 'r', encoding='utf-8') as f:
        yunwen_data = json.load(f)

    # 按类型分组
    by_type = {}
    for item in yunwen_data:
        yunwen_type = item['type']
        if yunwen_type not in by_type:
            by_type[yunwen_type] = []
        by_type[yunwen_type].append(item)

    # 生成HTML
    html = '''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>史记韵文集</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: "Source Han Serif SC", "Noto Serif SC", serif;
            line-height: 2;
            color: #333;
            background-color: #fdfaf6;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        h1 {
            text-align: center;
            color: #8b4513;
            font-size: 2.5em;
            margin-bottom: 10px;
            border-bottom: 3px double #8b4513;
            padding-bottom: 20px;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 40px;
            font-size: 1.1em;
        }

        .nav {
            background: #f5f5f5;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 5px;
        }

        .nav a {
            color: #8b4513;
            text-decoration: none;
            margin-right: 20px;
        }

        .nav a:hover {
            text-decoration: underline;
        }

        .nav a.pdf {
            color: #c00;
            font-weight: bold;
        }

        .type-section {
            margin-bottom: 60px;
        }

        .type-header {
            font-size: 2em;
            color: #8b4513;
            margin-bottom: 10px;
            border-left: 5px solid #8b4513;
            padding-left: 15px;
        }

        .type-desc {
            color: #666;
            margin-bottom: 30px;
            padding-left: 20px;
            font-style: italic;
        }

        .yunwen-item {
            margin-bottom: 50px;
            border-left: 3px solid #d4a373;
            padding-left: 20px;
        }

        .item-title {
            font-size: 1.5em;
            color: #8b4513;
            margin-bottom: 10px;
            font-weight: bold;
        }

        .item-subtitle {
            font-size: 0.9em;
            color: #999;
            margin-bottom: 20px;
            font-style: italic;
        }

        .item-subtitle a {
            color: #999;
        }

        .item-subtitle a:hover {
            color: #8b4513;
            text-decoration: underline;
        }

        .item-content {
            line-height: 2.5;
            color: #444;
        }

        .item-content.verse {
            /* 诗歌样式：左对齐，每行独立 */
            text-align: left;
            line-height: 1.8;
            padding-left: 2em;
            font-size: 1.05em;
            white-space: pre-wrap; /* 保留空格和换行 */
            text-indent: 0; /* 取消首行缩进 */
        }

        .item-content.prose {
            /* 散文样式：两端对齐，首行缩进 */
            text-align: justify;
            text-indent: 2em;
            line-height: 2.2;
        }

        .entity {
            font-weight: 500;
            border-bottom: 1px dotted;
            cursor: help;
        }

        .entity.person { color: #c00; border-bottom-color: #c00; }
        .entity.place { color: #080; border-bottom-color: #080; }
        .entity.office { color: #660; border-bottom-color: #660; }
        .entity.time { color: #06c; border-bottom-color: #06c; }
        .entity.object { color: #c0c; border-bottom-color: #c0c; }
        .entity.book { color: #900; border-bottom-color: #900; }
        .entity.clan { color: #c60; border-bottom-color: #c60; }
        .entity.state { color: #009; border-bottom-color: #009; }
        .entity.event { color: #690; border-bottom-color: #690; }
        .entity.identity { color: #939; border-bottom-color: #939; }
        .entity.biology { color: #060; border-bottom-color: #060; }
        .entity.myth { color: #939; border-bottom-color: #939; }
        .entity.title { color: #960; border-bottom-color: #960; }
        .entity.concept { color: #069; border-bottom-color: #069; }
        .entity.measure { color: #666; border-bottom-color: #666; }
        .entity.position { color: #093; border-bottom-color: #093; }
        .entity.artifact { color: #c6c; border-bottom-color: #c6c; }
        .entity.other { color: #999; border-bottom-color: #999; }

        .footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #999;
            font-size: 0.9em;
        }

        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>史记韵文集</h1>
        <div class="subtitle">史记中共有 ''' + str(len(yunwen_data)) + ''' 篇韵文作品</div>

        <div class="nav">
            <a href="../index.html">← 返回首页</a>
            <a href="special_index.html">专项索引</a>
            <a href="yunwen.pdf" class="pdf">📥 下载PDF</a>
        </div>

'''

    # 按类型输出
    type_order = ['赞', '诗歌', '赋']
    for yunwen_type in type_order:
        if yunwen_type not in by_type:
            continue

        items = by_type[yunwen_type]
        html += f'''
        <div class="type-section" id="type-{yunwen_type}">
            <div class="type-header">{yunwen_type}（{len(items)}篇）</div>
            <div class="type-desc">{items[0]['type_desc']}</div>

'''

        for item in items:
            chapter_num = item['chapter_num']
            chapter_title = item['chapter_title']
            yunwen_title = item.get('title', chapter_title)
            content = format_yunwen_content(item['content'], yunwen_type)

            # 根据类型决定样式类
            content_class = 'verse' if yunwen_type in ['赞', '诗歌'] else 'prose'

            html += f'''
            <div class="yunwen-item" id="chapter-{chapter_num}">
                <div class="item-title">
                    {yunwen_title}
                </div>
                <div class="item-subtitle">
                    <a href="../chapters/{chapter_num}_{chapter_title}.html" style="text-decoration: none; color: #999;">
                        {chapter_num} {chapter_title}
                    </a>
                </div>
                <div class="item-content {content_class}">
                    {content}
                </div>
            </div>

'''

        html += '        </div>\n\n'

    html += '''
        <div class="footer">
            <p>史记知识库 | 韵文专项索引</p>
            <p>数据提取自《史记》标注版本</p>
        </div>
    </div>
</body>
</html>
'''

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ HTML 已生成: {output_path}")

def main():
    project_root = Path(__file__).parent.parent
    # 从data/目录读取JSON
    json_path = project_root / "data/yunwen.json"
    # 保存HTML到docs/special/
    output_path = project_root / "docs/special/yunwen.html"

    if not json_path.exists():
        print(f"错误: JSON文件不存在: {json_path}")
        print("请先运行 extract_yunwen.py")
        return 1

    generate_html(json_path, output_path)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
