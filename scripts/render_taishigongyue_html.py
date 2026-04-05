#!/usr/bin/env python3
"""
将太史公曰渲染为HTML页面
"""

import json
from pathlib import Path
import sys

# 导入统一的语义标签处理模块
sys.path.insert(0, str(Path(__file__).parent))
from semantic_tags import render_tags_to_html, get_entity_css_path


def clean_markdown_tags(text):
    """清理markdown标记，保留实体标注"""
    # 保留实体标注：〖TYPE content〗
    # 移除其他markdown格式
    return text


def render_entity_tags(text):
    """将实体标注转换为HTML（使用统一标准）"""
    return render_tags_to_html(text, normalize_legacy=True)


def generate_html(taishigongyue_list):
    """生成HTML页面"""

    html_content = """<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>太史公曰 - 史记专项索引</title>
    <link rel="stylesheet" href="../css/shiji-styles-v6.css">
    <style>
        /* 页面布局专用样式（不涉及实体标注） */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
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
    data_dir = project_root / "data"
    json_file = data_dir / "taishigongyue.json"
    md_file = data_dir / "taishigongyue.md"

    with open(json_file, 'r', encoding='utf-8') as f:
        taishigongyue_list = json.load(f)

    print(f"读取了 {len(taishigongyue_list)} 篇太史公曰")

    # 生成HTML
    html_content = generate_html(taishigongyue_list)

    # 发布到docs/special/目录
    special_dir = project_root / "docs" / "special"
    special_dir.mkdir(parents=True, exist_ok=True)

    # 保存HTML
    html_file = special_dir / "taishigongyue.html"
    html_file.write_text(html_content, encoding='utf-8')
    print(f"✅ HTML已生成: {html_file}")

    # 复制MD和JSON文件到docs/special/
    import shutil
    shutil.copy2(json_file, special_dir / "taishigongyue.json")
    print(f"✅ JSON已复制: {special_dir / 'taishigongyue.json'}")

    shutil.copy2(md_file, special_dir / "taishigongyue.md")
    print(f"✅ MD已复制: {special_dir / 'taishigongyue.md'}")

    # 自动生成PDF
    try:
        from weasyprint import HTML, CSS

        pdf_path = special_dir / "taishigongyue.pdf"
        print(f"正在生成PDF: {pdf_path}")

        # 添加PDF专用CSS样式
        pdf_css = CSS(string='''
            @page {
                size: A4;
                margin: 2.5cm 2cm;

                @top-center {
                    content: "史记·太史公曰";
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

            .section {
                page-break-inside: avoid;
                margin-bottom: 30pt;
            }

            .section-title {
                font-size: 16pt;
                page-break-after: avoid;
            }

            .nav {
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


if __name__ == "__main__":
    main()
