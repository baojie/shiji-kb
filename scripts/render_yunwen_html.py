#!/usr/bin/env python3
"""
渲染韵文HTML页面
将韵文JSON数据渲染为带实体高亮的HTML页面
"""

import json
import re
from pathlib import Path
import sys

# 导入统一的语义标签处理模块
sys.path.insert(0, str(Path(__file__).parent))
from semantic_tags import render_tags_to_html, get_entity_css_styles


def render_entity_tags(text):
    """将实体标注转换为HTML span标签（使用统一标准）"""
    return render_tags_to_html(text, normalize_legacy=True)

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
        # 诗歌类：每行独立，用<br>分隔（不要换行符，避免white-space: pre-wrap时出现缩进）
        return '<br>'.join(formatted_lines)
    else:
        # 赋类：段落式，用双<br>分隔
        return '<br><br>'.join(formatted_lines)

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
    <link rel="stylesheet" href="../css/shiji-styles-v6.css">
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

        .toc {
            background: #f9f9f9;
            padding: 20px 30px;
            margin-bottom: 40px;
            border-radius: 5px;
            border-left: 4px solid #8b4513;
        }

        .toc h2 {
            font-size: 1.5em;
            color: #8b4513;
            margin-bottom: 15px;
        }

        .toc ul {
            list-style: none;
            padding-left: 0;
        }

        .toc li {
            margin-bottom: 8px;
            padding-left: 20px;
            position: relative;
        }

        .toc li:before {
            content: "📖";
            position: absolute;
            left: 0;
            margin-right: 8px;  /* 图标右边距 */
        }

        .toc a {
            color: #333;
            text-decoration: none;
            font-size: 1.1em;
        }

        .toc a:hover {
            color: #8b4513;
            text-decoration: underline;
        }

        /* 子目录样式（诗歌和赋的篇名） */
        .toc-sub {
            list-style: none;
            padding-left: 20px;
            margin-top: 8px;
        }

        .toc-sub li {
            margin-bottom: 5px;
            padding-left: 15px;
            font-size: 0.95em;
        }

        .toc-sub li:before {
            content: "•";
            color: #999;
            font-size: 1.2em;
        }

        .toc-sub a {
            font-size: 1em;
            color: #666;
        }

        .toc-sub a:hover {
            color: #8b4513;
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

        /* 实体标注样式继承自 shiji-styles-v6.css */

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

    # 生成目录
    type_order = ['赞', '诗歌', '赋']
    html += '''
        <div class="toc">
            <h2>目录</h2>
            <ul>
'''

    # 为每篇韵文分配唯一ID
    for idx, item in enumerate(yunwen_data):
        item['_unique_id'] = f"yunwen-{idx}"

    for yunwen_type in type_order:
        if yunwen_type not in by_type:
            continue
        items = by_type[yunwen_type]

        # 赞只显示类型和数量，诗歌和赋显示具体篇名
        if yunwen_type == '赞':
            html += f'                <li><a href="#type-{yunwen_type}">{yunwen_type}（{len(items)}篇）</a></li>\n'
        else:
            # 诗歌和赋：显示具体篇名
            html += f'                <li><a href="#type-{yunwen_type}">{yunwen_type}（{len(items)}篇）</a>\n'
            html += '                    <ul class="toc-sub">\n'
            for item in items:
                unique_id = item['_unique_id']
                title = item.get('title', item['chapter_title'])
                html += f'                        <li><a href="#{unique_id}">{title}</a></li>\n'
            html += '                    </ul>\n'
            html += '                </li>\n'

    html += '''            </ul>
        </div>

'''

    # 按类型输出内容
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
            unique_id = item['_unique_id']
            chapter_num = item['chapter_num']
            chapter_title = item['chapter_title']
            yunwen_title = item.get('title', chapter_title)
            content = format_yunwen_content(item['content'], yunwen_type)

            # 根据类型决定样式类
            content_class = 'verse' if yunwen_type in ['赞', '诗歌'] else 'prose'

            html += f'''
            <div class="yunwen-item" id="{unique_id}">
                <div class="item-title">
                    {yunwen_title}
                </div>
                <div class="item-subtitle">
                    <a href="../chapters/{chapter_num}_{chapter_title}.html" style="text-decoration: none; color: #999;">
                        {chapter_num} {chapter_title}
                    </a>
                </div>
                <div class="item-content {content_class}">{content}</div>
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

    # 从data/目录读取JSON和MD
    data_dir = project_root / "data"
    json_file = data_dir / "yunwen.json"
    md_file = data_dir / "yunwen.md"

    if not json_file.exists():
        print(f"错误: JSON文件不存在: {json_file}")
        print("请先运行 extract_yunwen.py")
        return 1

    # 发布到docs/special/目录
    special_dir = project_root / "docs" / "special"
    special_dir.mkdir(parents=True, exist_ok=True)

    # 生成HTML
    html_file = special_dir / "yunwen.html"
    generate_html(json_file, html_file)

    # 复制MD和JSON文件到docs/special/
    import shutil
    shutil.copy2(json_file, special_dir / "yunwen.json")
    print(f"✅ JSON已复制: {special_dir / 'yunwen.json'}")

    shutil.copy2(md_file, special_dir / "yunwen.md")
    print(f"✅ MD已复制: {special_dir / 'yunwen.md'}")

    # 自动生成PDF
    try:
        from weasyprint import HTML, CSS

        pdf_path = special_dir / "yunwen.pdf"
        print(f"正在生成PDF: {pdf_path}")

        # 添加PDF专用CSS样式
        pdf_css = CSS(string='''
            @page {
                size: A4;
                margin: 2.5cm 2cm;

                @top-center {
                    content: "史记·韵文集";
                    font-size: 10pt;
                    color: #666;
                }

                @bottom-center {
                    content: counter(page);
                    font-size: 10pt;
                    color: #666;
                }
            }

            body {
                font-family: "Noto Serif SC", "Source Han Serif SC", serif;
                font-size: 12pt;
                line-height: 1.8;
            }

            h1 {
                font-size: 24pt;
                page-break-after: avoid;
            }

            .type-section {
                page-break-inside: avoid;
                margin-bottom: 30pt;
            }

            .type-header {
                font-size: 18pt;
                page-break-after: avoid;
            }

            .yunwen-item {
                page-break-inside: avoid;
                margin-bottom: 20pt;
            }

            .item-title {
                font-size: 14pt;
                page-break-after: avoid;
            }

            .nav, .toc {
                display: none;
            }

            a {
                color: #8b4513;
                text-decoration: none;
            }
        ''')

        HTML(filename=str(html_file)).write_pdf(
            str(pdf_path),
            stylesheets=[pdf_css]
        )

        file_size = pdf_path.stat().st_size / 1024 / 1024
        print(f"✅ PDF已生成: {pdf_path} ({file_size:.2f} MB)")

    except ImportError:
        print("⚠️  WeasyPrint未安装，跳过PDF生成")
        print("   安装命令: pip install weasyprint")
    except Exception as e:
        print(f"⚠️  PDF生成失败: {e}")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
