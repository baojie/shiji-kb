#!/usr/bin/env python3
"""
重构步骤1：提取常量和模板字符串
提升 render_shiji_html.py 的可读性
"""

from pathlib import Path

def refactor_step1():
    """步骤1：提取常量定义"""

    source_file = Path('render_shiji_html.py')
    backup_file = Path('render_shiji_html.py.backup')

    # 备份原文件
    content = source_file.read_text(encoding='utf-8')
    backup_file.write_text(content, encoding='utf-8')
    print(f"✓ 已备份原文件到: {backup_file}")

    # 在导入语句后添加常量定义区
    constants_section = '''

# ========================================
# 常量定义区
# ========================================

# 正则表达式字符类（用于构建实体标注模式）
MARKER_CONTENT_PLAIN = r'[^〖〗<>"'         # 名词实体普通内容
MARKER_CONTENT_DISAMBIG = r'[^〖〗<>"|'     # 名词实体消歧内容
VERB_MARKER_CONTENT = r'[^⟦⟧'              # 动词实体内容

# HTML span模板（减少重复字符串）
SPAN_TEMPLATE = '<span class="{css_class}" title="{title}">{content}</span>'
SPAN_TEMPLATE_CANONICAL = '<span class="{css_class}" title="{title}" data-canonical="{canonical}">{content}</span>'

'''

    # 找到导入语句结束位置（在 import urllib.parse 之后）
    import_end = content.find('import urllib.parse\n') + len('import urllib.parse\n')

    # 插入常量定义
    new_content = content[:import_end] + constants_section + content[import_end:]

    source_file.write_text(new_content, encoding='utf-8')
    print("✓ 步骤1完成：已添加常量定义区")

    return True


if __name__ == '__main__':
    refactor_step1()
    print("\n请运行测试验证：python tests/test_render_shiji_html.py")
