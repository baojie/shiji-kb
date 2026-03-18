#!/usr/bin/env python3
"""
渲染成语典故HTML页面
将成语JSON数据渲染为带实体高亮的HTML页面
"""

import json
import re
from pathlib import Path

# 实体类型与颜色映射
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

    # 处理其他标注（如 〖_xxx〗、〖\\xxx〗）
    text = re.sub(r'〖[_\\]([^〗]+)〗', r'<span class="entity other" title="其他标注">\1</span>', text)

    return text

def highlight_chengyu_in_original(original_text, chengyu_name):
    """
    在原文中高亮（加粗）成语的关键字

    例如：成语"网开三面"，原文"汤出，见野张网四面…乃去其三面"
    应该高亮"网"、"三面"、"四面"
    """
    # 先渲染实体标签
    text = render_entity_tags(original_text)

    # 提取成语中的关键字（去掉斜杠、括号等）
    keywords = []

    # 处理特殊成语名称（如"浑沌/穷奇/梼杌/饕餮"）
    if '/' in chengyu_name:
        # 拆分每个成语
        parts = chengyu_name.split('/')
        keywords.extend(parts)
    else:
        # 单个成语，提取2-4字的关键词
        clean_name = chengyu_name.strip()
        if len(clean_name) >= 4:
            # 四字成语：尝试2+2拆分或完整
            keywords.append(clean_name[:2])
            keywords.append(clean_name[2:4])
            keywords.append(clean_name)
        elif len(clean_name) >= 2:
            keywords.append(clean_name)

    # 对关键字按长度排序（长的优先，避免部分匹配）
    keywords = sorted(set(keywords), key=len, reverse=True)

    # 在文本中查找并加粗关键字
    for keyword in keywords:
        if len(keyword) >= 2:  # 至少2字
            # 注意：不要匹配HTML标签内的文本
            # 使用负向预查确保不在标签内
            pattern = f'(?<!>)({re.escape(keyword)})(?![^<]*>)'
            text = re.sub(pattern, r'<strong>\1</strong>', text)

    return text

def generate_html(json_path, output_path):
    """生成HTML页面"""

    # 读取JSON数据
    with open(json_path, 'r', encoding='utf-8') as f:
        chengyu_data = json.load(f)

    # 按章节分组
    by_chapter = {}
    for item in chengyu_data:
        chapter_key = f"{item['chapter_num']}_{item['chapter_title']}"
        if chapter_key not in by_chapter:
            by_chapter[chapter_key] = []
        by_chapter[chapter_key].append(item)

    # 统计定位成功数
    located_count = sum(1 for item in chengyu_data if item.get('context'))

    # 生成HTML
    html = '''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>史记成语典故集</title>
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

        .chapter-section {
            margin-bottom: 60px;
        }

        .chapter-header {
            font-size: 1.8em;
            color: #8b4513;
            margin-bottom: 20px;
            border-left: 5px solid #8b4513;
            padding-left: 15px;
        }

        .chengyu-item {
            margin-bottom: 40px;
            border-left: 3px solid #d4a373;
            padding-left: 20px;
        }

        .item-title {
            font-size: 1.6em;
            color: #8b4513;
            margin-bottom: 10px;
            font-weight: bold;
        }

        .item-meaning {
            font-size: 1em;
            color: #666;
            margin-bottom: 15px;
            font-style: italic;
        }

        .item-original {
            font-size: 1.1em;
            color: #444;
            margin-bottom: 15px;
            padding: 10px;
            background: #f9f6f2;
            border-left: 3px solid #c9a56c;
        }

        .item-original strong {
            color: #8b4513;
            font-weight: 700;
            text-decoration: underline;
            text-decoration-color: #d4a373;
            text-decoration-thickness: 2px;
            text-underline-offset: 2px;
        }

        .item-meta {
            font-size: 0.9em;
            color: #999;
            margin-bottom: 10px;
        }

        .item-context {
            line-height: 2.2;
            color: #555;
            padding: 15px;
            background: #fefdfb;
            border: 1px solid #e9e3d9;
            border-radius: 3px;
        }

        .no-context {
            color: #999;
            font-style: italic;
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
        <h1>史记成语典故集</h1>
        <div class="subtitle">史记中共有 ''' + str(len(chengyu_data)) + ''' 条成语典故 | 定位 ''' + str(located_count) + ''' 条原文</div>

        <div class="nav">
            <a href="../index.html">← 返回首页</a>
            <a href="special_index.html">专项索引</a>
            <a href="chengyu.pdf" class="pdf">📥 下载PDF</a>
        </div>

'''

    # 按章节顺序输出
    for chapter_key in sorted(by_chapter.keys()):
        items = by_chapter[chapter_key]
        chapter_num, chapter_title = chapter_key.split('_', 1)

        html += f'''
        <div class="chapter-section" id="chapter-{chapter_num}">
            <div class="chapter-header">{chapter_num} {chapter_title}（{len(items)}条）</div>

'''

        for item in items:
            chengyu = item['chengyu']
            meaning = item['meaning']
            context = item.get('context', '')
            paragraph = item.get('paragraph', '')

            html += f'''
            <div class="chengyu-item">
                <div class="item-title">{chengyu}</div>
                <div class="item-meaning">{meaning}</div>
'''

            if paragraph:
                html += f'                <div class="item-meta">位置：第 {paragraph} 段</div>\n'

            if context:
                # 在长引文中高亮成语关键字
                context_html = highlight_chengyu_in_original(context, chengyu)
                html += f'''                <div class="item-context">
                    {context_html}
                </div>
'''
            else:
                # 无长引文时显示短引文
                original = highlight_chengyu_in_original(item['original'], chengyu)
                html += f'                <div class="item-original">{original}</div>\n'
                html += '                <div class="no-context">（原文位置未定位）</div>\n'

            html += '            </div>\n\n'

        html += '        </div>\n\n'

    html += '''
        <div class="footer">
            <p>史记知识库 | 成语典故专项索引</p>
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
    json_path = project_root / "data/chengyu.json"
    # 保存HTML到docs/special/
    output_path = project_root / "docs/special/chengyu.html"

    if not json_path.exists():
        print(f"错误: JSON文件不存在: {json_path}")
        print("请先运行 extract_chengyu.py")
        return 1

    generate_html(json_path, output_path)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
