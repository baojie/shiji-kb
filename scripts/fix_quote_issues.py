#!/usr/bin/env python3
"""
批量修复引号格式问题
重新生成所有有问题的HTML文件
"""
import os
import subprocess
from pathlib import Path

def find_problematic_files():
    """查找所有有引号格式问题的HTML文件"""
    problematic = []
    pattern = 'class=<span class="quoted">'

    for html_file in Path('docs/chapters').glob('*.tagged.html'):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if pattern in content:
                    # 提取章节名（去掉.tagged后缀）
                    chapter_name = html_file.stem.replace('.tagged', '')
                    problematic.append(chapter_name)
        except Exception as e:
            print(f"  警告：无法读取 {html_file}: {e}")

    return sorted(problematic)

def regenerate_html(chapter_name):
    """重新生成指定章节的HTML"""
    md_file = f"chapter_md/{chapter_name}.tagged.md"

    if not Path(md_file).exists():
        print(f"  ⚠️  源文件不存在: {md_file}")
        return False

    # 使用generate_all_chapters.py中的逻辑
    from render_shiji_html import markdown_to_html

    # 提取章节编号
    chapter_num = int(chapter_name.split('_')[0])

    # 确定上一章和下一章
    prev_chapter = None
    next_chapter = None

    if chapter_num > 1:
        # 查找上一章文件
        prev_num = f"{chapter_num-1:03d}"
        prev_files = list(Path('chapter_md').glob(f'{prev_num}_*.tagged.md'))
        if prev_files:
            prev_chapter = prev_files[0].stem + '.html'

    if chapter_num < 130:
        # 查找下一章文件
        next_num = f"{chapter_num+1:03d}"
        next_files = list(Path('chapter_md').glob(f'{next_num}_*.tagged.md'))
        if next_files:
            next_chapter = next_files[0].stem + '.html'

    # 原文链接
    original_text = f"../original_text/{chapter_name}.txt"

    # 生成HTML
    output_file = f"docs/chapters/{chapter_name}.tagged.html"
    css_file = "docs/css/shiji-styles.css"

    try:
        markdown_to_html(
            md_file,
            output_file=output_file,
            css_file=css_file,
            prev_chapter=prev_chapter,
            next_chapter=next_chapter,
            original_text_file=original_text
        )
        return True
    except Exception as e:
        print(f"  ❌ 生成失败: {e}")
        return False

def main():
    print("正在查找有引号格式问题的文件...")
    problematic_files = find_problematic_files()

    if not problematic_files:
        print("✅ 没有发现引号格式问题！")
        return

    print(f"\n发现 {len(problematic_files)} 个文件需要修复：")
    for f in problematic_files[:10]:
        print(f"  - {f}")
    if len(problematic_files) > 10:
        print(f"  ... 还有 {len(problematic_files) - 10} 个文件")

    print(f"\n开始重新生成HTML文件...")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    for i, chapter_name in enumerate(problematic_files, 1):
        print(f"[{i}/{len(problematic_files)}] {chapter_name}")
        if regenerate_html(chapter_name):
            success_count += 1
        else:
            fail_count += 1

    print("=" * 60)
    print(f"\n✅ 修复完成！")
    print(f"   成功: {success_count} 个")
    if fail_count > 0:
        print(f"   失败: {fail_count} 个")

if __name__ == '__main__':
    main()
