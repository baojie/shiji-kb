#!/usr/bin/env python3
"""
为 render_shiji_html.py 添加章节注释，提升可读性
这是最简单但最有效的可读性改进
"""

from pathlib import Path
import re

def add_section_comments():
    """在关键位置添加分隔注释"""

    source = Path('render_shiji_html.py')
    content = source.read_text(encoding='utf-8')

    replacements = [
        # 1. 模块头部改进
        (
            'import urllib.parse',
            '''import urllib.parse

# ========================================
# 配置与常量定义
# ========================================'''
        ),

        # 2. 引号模式部分
        (
            '# 引号内容模式（用于对话）',
            '''
# ========================================
# 引号内容模式（用于对话）
# ========================================'''
        ),

        # 3. 段落编号模式
        (
            '# 段落编号模式',
            '''
# ========================================
# 段落编号模式
# ========================================'''
        ),

        # 4. 实体索引链接部分
        (
            '# --- 实体索引链接 ---',
            '''
# ========================================
# 实体索引链接配置
# ========================================'''
        ),

        # 5. 辅助函数部分（在第一个 def 前）
        (
            'def _get_alias_reverse_map():',
            '''
# ========================================
# 辅助函数：数据加载
# ========================================

def _get_alias_reverse_map():'''
        ),

        # 6. 核心转换函数部分
        (
            'def convert_entities(text):',
            '''
# ========================================
# 核心转换函数
# ========================================

def convert_entities(text):'''
        ),

        # 7. 主函数部分
        (
            'def markdown_to_html(md_file,',
            '''
# ========================================
# 主函数：Markdown转HTML
# ========================================

def markdown_to_html(md_file,'''
        ),
    ]

    for old, new in replacements:
        if old in content:
            content = content.replace(old, new, 1)  # 只替换第一次出现
            print(f"✓ 已添加注释: {old[:30]}...")

    source.write_text(content, encoding='utf-8')
    print("\n✓ 完成：已添加章节注释")


def main():
    add_section_comments()
    print("\n请运行测试验证：python tests/test_render_shiji_html.py")


if __name__ == '__main__':
    main()
