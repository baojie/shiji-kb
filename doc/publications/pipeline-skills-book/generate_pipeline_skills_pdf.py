#!/usr/bin/env python3
"""
生成管线技能文档PDF合集
将SKILL 00-09系列Markdown文档合并为单个HTML，然后生成PDF
"""

import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS

def read_pipeline_skill_files():
    """读取SKILL 00-09系列文件（管线技能）"""
    skills_dir = Path(__file__).parent.parent.parent.parent / "skills"

    # 读取SKILL_00到SKILL_09的所有文件
    files = []
    for i in range(10):  # 0-9
        pattern = f"SKILL_{i:02d}*.md"
        matched_files = sorted(skills_dir.glob(pattern))
        files.extend(matched_files)

    # 按文件名排序
    files.sort(key=lambda x: x.name)

    print(f"找到 {len(files)} 个管线技能文档:")
    for f in files:
        print(f"  - {f.name}")

    return files

def markdown_to_html_content(md_text, title):
    """将单个Markdown文档转换为HTML片段"""
    # 使用markdown库转换，支持表格、代码块等扩展
    html_content = markdown.markdown(
        md_text,
        extensions=[
            'tables',           # 表格支持
            'fenced_code',      # 代码块支持
            'nl2br',            # 换行支持
            'sane_lists',       # 列表支持
            'toc',              # 目录支持
        ]
    )

    # 包裹在section中，添加页面分隔
    return f'''
    <section class="pipeline-skill" id="{title}">
        {html_content}
    </section>
    '''

def generate_combined_html(skill_files, output_html):
    """生成合并的HTML文档"""
    print("\n正在合并Markdown文档...")

    sections = []
    toc_items = []

    for idx, file_path in enumerate(skill_files, 1):
        print(f"  [{idx}/{len(skill_files)}] 处理 {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 提取文件名作为ID
        file_id = file_path.stem

        # 提取标题（第一行）
        first_line = md_content.split('\n')[0]
        if first_line.startswith('# '):
            title = first_line[2:].strip()
        else:
            title = file_path.stem

        # 生成HTML片段
        html_section = markdown_to_html_content(md_content, file_id)
        sections.append(html_section)

        # 添加到目录
        toc_items.append(f'<li><a href="#{file_id}">{title}</a></li>')

    # 生成完整HTML
    html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>史记知识库构造管线技能手册</title>
    <style>
        body {{
            font-family: "Noto Serif SC", "Source Han Serif SC", "SimSun", serif;
            font-size: 11pt;
            line-height: 1.7;
            color: #333;
            max-width: 100%;
            margin: 0;
            padding: 0;
        }}

        .cover {{
            page-break-after: always;
            text-align: center;
            padding-top: 200px;
        }}

        .cover h1 {{
            font-size: 32pt;
            color: #2C5F8D;
            margin-bottom: 20pt;
        }}

        .cover .subtitle {{
            font-size: 18pt;
            color: #666;
            margin-bottom: 40pt;
        }}

        .cover .info {{
            font-size: 12pt;
            color: #999;
        }}

        .toc {{
            page-break-after: always;
            padding: 40px;
        }}

        .toc h2 {{
            font-size: 20pt;
            color: #2C5F8D;
            border-bottom: 2px solid #2C5F8D;
            padding-bottom: 10pt;
            margin-bottom: 20pt;
        }}

        .toc ul {{
            list-style: none;
            padding: 0;
        }}

        .toc li {{
            margin: 12pt 0;
            font-size: 12pt;
        }}

        .toc a {{
            color: #333;
            text-decoration: none;
        }}

        .toc a:hover {{
            color: #2C5F8D;
        }}

        .pipeline-skill {{
            page-break-before: always;
            padding: 40px;
        }}

        .pipeline-skill:first-of-type {{
            page-break-before: auto;
        }}

        /* 优化区块分页 */
        pre, blockquote, table {{
            page-break-inside: auto;
            orphans: 3;
            widows: 3;
        }}

        /* 允许代码块在页面间分割 */
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        h1 {{
            font-size: 22pt;
            color: #2C5F8D;
            border-bottom: 3px solid #2C5F8D;
            padding-bottom: 10pt;
            margin-top: 0;
            margin-bottom: 20pt;
            page-break-after: avoid;
        }}

        h2 {{
            font-size: 16pt;
            color: #4682B4;
            margin-top: 20pt;
            margin-bottom: 12pt;
            page-break-after: avoid;
        }}

        h3 {{
            font-size: 14pt;
            color: #666;
            margin-top: 16pt;
            margin-bottom: 10pt;
            page-break-after: avoid;
        }}

        h4, h5, h6 {{
            font-size: 12pt;
            color: #888;
            margin-top: 12pt;
            margin-bottom: 8pt;
        }}

        p {{
            margin: 8pt 0;
            text-align: justify;
        }}

        ul, ol {{
            margin: 10pt 0;
            padding-left: 30pt;
        }}

        li {{
            margin: 6pt 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15pt 0;
            page-break-inside: auto;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 8pt;
            text-align: left;
        }}

        th {{
            background-color: #f5f5f5;
            font-weight: bold;
            color: #2C5F8D;
        }}

        code {{
            font-family: "Consolas", "Monaco", monospace;
            background-color: #f5f5f5;
            padding: 2pt 5pt;
            border-radius: 3pt;
            font-size: 10pt;
        }}

        pre {{
            background-color: #f5f5f5;
            padding: 12pt;
            border-radius: 5pt;
            overflow-x: auto;
            page-break-inside: auto;
        }}

        pre code {{
            background-color: transparent;
            padding: 0;
        }}

        blockquote {{
            border-left: 4px solid #4682B4;
            padding-left: 15pt;
            margin: 15pt 0;
            color: #666;
            font-style: italic;
        }}

        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 20pt 0;
        }}

        a {{
            color: #2C5F8D;
            text-decoration: none;
        }}

        strong {{
            color: #2C5F8D;
        }}
    </style>
</head>
<body>
    <div class="cover">
        <h1>史记知识库构造管线技能手册</h1>
        <div class="subtitle">SKILL 00-09 技术规范与实践指南</div>
        <div class="info">
            <p style="margin-top: 60pt; font-size: 14pt;"><strong>作者：鲍捷</strong></p>
            <p style="margin-top: 20pt; font-size: 11pt;">
                电子邮件：baojie@gmail.com<br>
                微信：baojiexigua<br>
                GitHub: @baojie
            </p>
            <p style="margin-top: 30pt; font-size: 10pt; color: #666;">
                文档在线目录：<br>
                <a href="https://github.com/baojie/shiji-kb/tree/main/skills" style="color: #2C5F8D;">
                    github.com/baojie/shiji-kb/tree/main/skills
                </a>
            </p>
            <p style="margin-top: 40pt; color: #999;">生成日期：2026-03-19</p>
            <p style="margin-top: 10pt; font-size: 10pt; color: #999;">完整知识库构造管线 · 从文本到知识图谱</p>
        </div>
    </div>

    <div class="toc">
        <h2>目录</h2>
        <ul>
            {''.join(toc_items)}
        </ul>
    </div>

    {''.join(sections)}
</body>
</html>
'''

    # 写入HTML文件
    print(f"\n正在写入HTML: {output_html}")
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"✓ HTML生成成功")

def generate_pdf_from_html(html_path, pdf_path):
    """从HTML生成PDF"""
    print(f"\n正在生成PDF: {pdf_path}")

    # PDF专用样式
    pdf_css = CSS(string='''
        @page {
            size: A4;
            margin: 2.5cm 2cm;

            @top-center {
                content: "史记知识库构造管线技能手册";
                font-size: 9pt;
                color: #999;
            }

            @bottom-center {
                content: "第 " counter(page) " 页";
                font-size: 9pt;
                color: #999;
            }
        }

        @page :first {
            @top-center {
                content: "";
            }
            @bottom-center {
                content: "";
            }
        }
    ''')

    try:
        HTML(filename=str(html_path)).write_pdf(
            str(pdf_path),
            stylesheets=[pdf_css]
        )

        # 显示文件大小
        file_size = Path(pdf_path).stat().st_size / 1024 / 1024
        print(f"✓ PDF生成成功！")
        print(f"  文件大小: {file_size:.2f} MB")
        print(f"  保存位置: {pdf_path}")

    except Exception as e:
        print(f"✗ PDF生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

def main():
    # 设置路径
    project_root = Path(__file__).parent.parent.parent.parent
    output_dir = Path(__file__).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    output_html = output_dir / "史记知识库构造管线技能手册.html"
    output_pdf = output_dir / "史记知识库构造管线技能手册.pdf"

    print("=" * 60)
    print("史记知识库 - 管线技能文档PDF生成器")
    print("=" * 60)

    # 读取文件
    skill_files = read_pipeline_skill_files()

    if len(skill_files) == 0:
        print("\n✗ 错误: 未找到任何SKILL文档")
        return 1

    # 生成HTML
    generate_combined_html(skill_files, output_html)

    # 生成PDF
    success = generate_pdf_from_html(output_html, output_pdf)

    print("\n" + "=" * 60)
    if success:
        print("✓ 全部完成！")
        print(f"  HTML: {output_html}")
        print(f"  PDF:  {output_pdf}")
    else:
        print("✗ PDF生成失败")
    print("=" * 60)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
