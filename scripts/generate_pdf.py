#!/usr/bin/env python3
"""
生成太史公曰PDF文档
从HTML生成高质量PDF，保留实体标注的颜色和格式
"""

import sys
from pathlib import Path
from weasyprint import HTML, CSS

def generate_pdf(html_path, output_path):
    """
    从HTML生成PDF

    Args:
        html_path: 输入HTML文件路径
        output_path: 输出PDF文件路径
    """
    print(f"正在读取HTML文件: {html_path}")

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

        /* 保留实体标注颜色 */
        .entity {
            font-weight: 500;
        }

        .entity.person { color: #c00; }
        .entity.place { color: #080; }
        .entity.office { color: #660; }
        .entity.time { color: #06c; }
        .entity.object { color: #c0c; }
        .entity.book { color: #900; }
        .entity.clan { color: #c60; }
        .entity.state { color: #009; }
        .entity.event { color: #690; }
        .entity.identity { color: #939; }
        .entity.biology { color: #060; }
    ''')

    print(f"正在生成PDF: {output_path}")
    HTML(filename=str(html_path)).write_pdf(
        str(output_path),
        stylesheets=[pdf_css]
    )

    print(f"✓ PDF生成成功: {output_path}")
    file_size = Path(output_path).stat().st_size / 1024 / 1024
    print(f"  文件大小: {file_size:.2f} MB")

def main():
    # 设置路径
    project_root = Path(__file__).parent.parent
    html_path = project_root / "docs/special/taishigongyue.html"
    output_path = project_root / "docs/special/taishigongyue.pdf"

    if not html_path.exists():
        print(f"错误: HTML文件不存在: {html_path}")
        return 1

    try:
        generate_pdf(html_path, output_path)
        return 0
    except Exception as e:
        print(f"错误: PDF生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
