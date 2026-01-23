#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成所有章节的HTML文件，并添加导航链接
"""

from pathlib import Path
from render_shiji_html import markdown_to_html

# 定义章节列表（按顺序）
CHAPTERS = [
    '001_五帝本纪.tagged.md',
    '002_夏本纪.tagged.md',
    '003_殷本纪.tagged.md',
    '004_周本纪.tagged.md',
]

def generate_all_chapters():
    """生成所有章节的HTML文件"""
    input_dir = Path('chapter_md')
    output_dir = Path('chapter_md')
    css_file = Path('docs/css/shiji-styles.css')

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    print("开始生成章节HTML文件...")
    print("=" * 60)

    for i, chapter in enumerate(CHAPTERS):
        # 确定上一章和下一章
        prev_chapter = None
        next_chapter = None

        if i > 0:
            # 有上一章
            prev_chapter = CHAPTERS[i-1].replace('.md', '.html')

        if i < len(CHAPTERS) - 1:
            # 有下一章
            next_chapter = CHAPTERS[i+1].replace('.md', '.html')

        # 输入和输出文件路径
        input_file = input_dir / chapter
        output_file = output_dir / chapter.replace('.md', '.html')

        # 原文txt文件路径（相对于生成的HTML文件）
        # 从 chapter_md/*.html 到 docs/original_text/*.txt
        original_text_filename = chapter.replace('.tagged.md', '.txt')
        original_text_path = f'../docs/original_text/{original_text_filename}'

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

if __name__ == '__main__':
    generate_all_chapters()
