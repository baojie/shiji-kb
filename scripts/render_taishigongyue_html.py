#!/usr/bin/env python3
"""
将太史公曰渲染为HTML页面
"""

import json
import re
from pathlib import Path


def clean_markdown_tags(text):
    """清理markdown标记，保留实体标注"""
    # 保留实体标注：〖TYPE content〗
    # 移除其他markdown格式
    return text


def render_entity_tags(text):
    """将实体标注转换为HTML"""
    # 人名 @
    text = re.sub(r'〖@([^〗]+)〗', r'<span class="entity person" title="人名">\1</span>', text)
    # 地名 =
    text = re.sub(r'〖=([^〗]+)〗', r'<span class="entity place" title="地名">\1</span>', text)
    # 官职 ;
    text = re.sub(r'〖;([^〗]+)〗', r'<span class="entity office" title="官职">\1</span>', text)
    # 时间 %
    text = re.sub(r'〖%([^〗]+)〗', r'<span class="entity time" title="时间">\1</span>', text)
    # 器物 •
    text = re.sub(r'〖•([^〗]+)〗', r'<span class="entity object" title="器物">\1</span>', text)
    # 典籍 {
    text = re.sub(r'〖\{([^〗]+)〗', r'<span class="entity book" title="典籍">\1</span>', text)
    # 氏族 &
    text = re.sub(r'〖&([^〗]+)〗', r'<span class="entity clan" title="氏族">\1</span>', text)
    # 邦国 '
    text = re.sub(r'〖\'([^〗]+)〗', r'<span class="entity state" title="邦国">\1</span>', text)
    # 事件 ^
    text = re.sub(r'〖\^([^〗]+)〗', r'<span class="entity event" title="事件">\1</span>', text)
    # 身份 #
    text = re.sub(r'〖#([^〗]+)〗', r'<span class="entity identity" title="身份">\1</span>', text)
    # 生物 +
    text = re.sub(r'〖\+([^〗]+)〗', r'<span class="entity biology" title="生物">\1</span>', text)

    return text


def generate_html(taishigongyue_list):
    """生成HTML页面"""

    html_content = """<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>太史公曰 - 史记专项索引</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: "Source Han Serif SC", "Noto Serif SC", serif;
            line-height: 1.8;
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

        .section {
            margin-bottom: 50px;
            border-left: 3px solid #8b4513;
            padding-left: 20px;
        }

        .section-title {
            font-size: 1.5em;
            color: #8b4513;
            margin-bottom: 15px;
            font-weight: bold;
        }

        .section-content {
            text-indent: 2em;
            line-height: 2;
            color: #444;
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
        <h1>太史公曰</h1>
        <div class="subtitle">史记中共有 """ + str(len(taishigongyue_list)) + """ 篇太史公曰</div>

        <div class="nav">
            <a href="../index.html">← 返回首页</a>
            <a href="special_index.html">专项索引</a>
        </div>

"""

    for item in taishigongyue_list:
        chapter_link = f"../chapters/{item['chapter_num']}_{item['chapter_title']}.html"
        content_html = render_entity_tags(item['content'])

        html_content += f"""
        <div class="section" id="chapter-{item['chapter_num']}">
            <div class="section-title">
                <a href="{chapter_link}" style="text-decoration: none; color: inherit;">
                    {item['chapter_num']} {item['chapter_title']}
                </a>
            </div>
            <div class="section-content">
                {content_html}
            </div>
        </div>
"""

    html_content += """
        <div class="footer">
            史记知识库 · 太史公曰专项索引
        </div>
    </div>
</body>
</html>
"""

    return html_content


def main():
    project_root = Path(__file__).parent.parent

    # 从data/目录读取JSON数据
    json_file = project_root / "data" / "taishigongyue.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        taishigongyue_list = json.load(f)

    print(f"读取了 {len(taishigongyue_list)} 篇太史公曰")

    # 生成HTML
    html_content = generate_html(taishigongyue_list)

    # 保存HTML到docs/special/
    html_file = project_root / "docs" / "special" / "taishigongyue.html"
    html_file.write_text(html_content, encoding='utf-8')

    print(f"✅ HTML已生成: {html_file}")


if __name__ == "__main__":
    main()
