#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成所有章节的HTML文件，并添加导航链接

主调用接口：
    python generate_all_chapters.py

功能：
1. 自动发现 chapter_md 目录下所有 .tagged.md 文件
2. 按文件名排序（章节编号）
3. 为每个章节生成 HTML 文件，包含上一章/下一章导航链接
4. 生成/更新 docs/index.html 索引页面
"""

from pathlib import Path
from render_shiji_html import markdown_to_html
import re


def extract_chapter_title(md_file):
    """从Markdown文件中提取章节标题（第一个 # 标题）"""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('# '):
                    title = line[2:].strip()
                    # 移除段落编号 [数字] 或 [数字.数字]
                    title = re.sub(r'^\[\d+(?:\.\d+)*\]\s*', '', title)
                    return title
    except Exception:
        pass
    # 如果无法提取，使用文件名
    return md_file.stem.replace('.tagged', '')


def generate_index_html(chapters, output_file='docs/index.html'):
    """生成索引页面 HTML

    注意：如果已存在详细设计的index.html（包含chapter-card样式），
    则跳过生成，避免覆盖精心设计的版本。
    如需重新生成简单版本，请先删除或重命名现有的index.html
    """
    print(f"\n生成索引页面: {output_file}")

    # 检查是否已存在详细设计的index.html
    output_path = Path(output_file)
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 检查是否包含详细设计的标志（chapter-card类）
            if 'chapter-card' in content or 'chapter-grid' in content:
                print("⚠️  检测到已存在详细设计的index.html，跳过生成以保护设计")
                print("   如需重新生成，请先备份或删除现有文件")
                return

    # 生成章节列表 HTML
    chapter_items = []
    for chapter_file in chapters:
        # 提取章节编号和标题
        chapter_name = chapter_file.stem.replace('.tagged', '')
        match = re.match(r'^(\d+)_(.+)$', chapter_name)
        if match:
            chapter_num = match.group(1)
            chapter_title = match.group(2)
        else:
            chapter_num = ''
            chapter_title = chapter_name

        # 生成 HTML 文件名
        html_filename = chapter_file.name.replace('.md', '.html')

        # 尝试从文件中提取更详细的标题
        full_title = extract_chapter_title(chapter_file)

        chapter_items.append(f'''        <li>
            <a href="chapters/{html_filename}">{chapter_num} {chapter_title}</a>
            <p>{full_title}</p>
        </li>''')

    chapter_list_html = '\n'.join(chapter_items)

    # 生成完整的 HTML
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>史记 - 知识库</title>
    <link rel="stylesheet" href="css/shiji-styles.css">
    <style>
        .chapter-list {{
            list-style: none;
            padding: 0;
        }}

        .chapter-list li {{
            margin: 20px 0;
            padding: 15px;
            background-color: #fffef0;
            border-left: 5px solid #8B4513;
            border-radius: 5px;
            transition: background-color 0.3s;
        }}

        .chapter-list li:hover {{
            background-color: #FFF8E1;
        }}

        .chapter-list a {{
            text-decoration: none;
            color: #8B0000;
            font-size: 1.2em;
            font-weight: 500;
        }}

        .chapter-list a:hover {{
            color: #8B4513;
        }}

        .intro {{
            background-color: #faf8ff;
            padding: 20px;
            border-radius: 5px;
            border: 1px solid #e6e0c0;
            margin: 30px 0;
        }}

        .intro h2 {{
            margin-top: 0;
            border: none;
            padding: 0;
        }}
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
{chapter_list_html}
    </ul>

    <hr>

    <footer style="text-align: center; color: #666; margin-top: 40px;">
        <p>史记知识库 | 命名实体标注版</p>
    </footer>
</body>
</html>
'''

    # 确保输出目录存在
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ 索引页面已生成: {output_path}")


def generate_all_chapters():
    """生成所有章节的HTML文件"""
    input_dir = Path('chapter_md')
    output_dir = Path('docs/chapters')  # 修改输出目录到docs/chapters
    css_file = Path('docs/css/shiji-styles.css')

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 自动发现所有 .tagged.md 文件并排序
    chapters = sorted(input_dir.glob('*.tagged.md'))

    if not chapters:
        print(f"错误: 在 {input_dir} 目录下未找到 .tagged.md 文件")
        return

    print("开始生成章节HTML文件...")
    print("=" * 60)
    print(f"发现 {len(chapters)} 个章节文件")

    for i, chapter_path in enumerate(chapters):
        chapter = chapter_path.name

        # 确定上一章和下一章
        prev_chapter = None
        next_chapter = None

        if i > 0:
            # 有上一章
            prev_chapter = chapters[i-1].name.replace('.md', '.html')

        if i < len(chapters) - 1:
            # 有下一章
            next_chapter = chapters[i+1].name.replace('.md', '.html')

        # 输入和输出文件路径
        input_file = chapter_path
        output_file = output_dir / chapter.replace('.md', '.html')

        # 原文txt文件路径（相对于生成的HTML文件）
        # 从 docs/chapters/*.html 到 docs/original_text/*.txt
        original_text_filename = chapter.replace('.tagged.md', '.txt')
        original_text_path = f'../original_text/{original_text_filename}'

        print(f"\n处理: {chapter}")
        print(f"  上一章: {prev_chapter if prev_chapter else '无'}")
        print(f"  下一章: {next_chapter if next_chapter else '无'}")
        print(f"  原文: {original_text_path}")

        # 生成HTML
        markdown_to_html(
            md_file=str(input_file),
            output_file=str(output_file),
            css_file=str(css_file),
            prev_chapter=prev_chapter,
            next_chapter=next_chapter,
            original_text_file=original_text_path
        )

    print("\n" + "=" * 60)
    print("所有章节生成完成！")

    # 生成索引页面
    print("\n" + "=" * 60)
    print("生成索引页面...")
    generate_index_html(chapters)

    # 运行HTML Linter检查生成的文件
    print("\n" + "=" * 60)
    print("运行质量检查...")
    print("=" * 60)

    import subprocess
    try:
        result = subprocess.run(
            ['python3', 'lint_html.py', 'docs/chapters/'],
            capture_output=True,
            text=True,
            timeout=60
        )

        # 显示检查结果摘要
        if result.returncode == 0:
            print("✅ HTML质量检查通过")
        else:
            print("⚠️  HTML质量检查发现问题，详细信息：")
            print(result.stdout)

    except subprocess.TimeoutExpired:
        print("⚠️  HTML质量检查超时")
    except FileNotFoundError:
        print("ℹ️  跳过质量检查（lint_html.py未找到）")
    except Exception as e:
        print(f"ℹ️  质量检查遇到问题: {e}")

    print("\n" + "=" * 60)
    print("全部完成！")

if __name__ == '__main__':
    generate_all_chapters()
