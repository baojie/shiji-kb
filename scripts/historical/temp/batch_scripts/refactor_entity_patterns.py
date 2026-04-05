#!/usr/bin/env python3
"""
重构 ENTITY_PATTERNS：改善正则表达式模式的可读性
- 提取重复的模式为辅助函数
- 添加清晰的注释分组
- 对齐格式以便阅读
"""

from pathlib import Path
import re

def generate_refactored_patterns():
    """生成重构后的 ENTITY_PATTERNS 定义代码"""

    code = '''# ========================================
# 实体标注模式定义（v3.0）
# ========================================

# 辅助函数：生成实体标注的正则模式和HTML替换
def _entity_pattern(marker_type, content_pattern, disambig_pattern, css_class, title_label, prefix='', suffix=''):
    """
    生成实体标注的模式对（用于消歧和普通两种格式）

    Args:
        marker_type: 标注符号（如 '@', '=', '◆'等）
        content_pattern: 内容匹配模式（如 r'[^〖〗<>"'）
        disambig_pattern: 消歧内容匹配模式（如 r'[^〖〗<>"|'）
        css_class: HTML class名
        title_label: title属性显示的标签（如"人名"）
        prefix: 内容前缀（如《）
        suffix: 内容后缀（如》）

    Returns:
        两个元组：(消歧格式模式, 普通格式模式)
    """
    # 转义特殊正则字符
    escaped_marker = re.escape(marker_type)

    # 消歧格式：〖TYPE 显示名|规范名〗
    disambig_regex = rf'〖{escaped_marker}({disambig_pattern}+)\\|({content_pattern}+)〗'
    disambig_html = (
        f'<span class="{css_class}" '
        f'title="{title_label}：\\2" '
        f'data-canonical="\\2">{prefix}\\1{suffix}</span>'
    )

    # 普通格式：〖TYPE content〗
    plain_regex = rf'〖{escaped_marker}({content_pattern}+)〗'
    plain_html = f'<span class="{css_class}" title="{title_label}">{prefix}\\1{suffix}</span>'

    return (disambig_regex, disambig_html), (plain_regex, plain_html)


def _verb_pattern(marker_symbol, css_class, title_label):
    """
    生成动词实体标注的模式对

    Args:
        marker_symbol: 动词标记符号（如 '◈', '◉'）
        css_class: HTML class名
        title_label: title属性显示的标签

    Returns:
        两个元组：(消歧格式模式, 普通格式模式)
    """
    content_pattern = r'[^⟦⟧'

    # 消歧格式：⟦SYMBOL 显示名|规范名⟧
    disambig_regex = rf'⟦{marker_symbol}({content_pattern}\\|)+\\|({content_pattern}+)⟧'
    disambig_html = (
        f'<span class="{css_class}" '
        f'title="{title_label}：\\2" '
        f'data-canonical="\\2">\\1</span>'
    )

    # 普通格式：⟦SYMBOL content⟧
    plain_regex = rf'⟦{marker_symbol}({content_pattern}+)⟧'
    plain_html = f'<span class="{css_class}" title="{title_label}">\\1</span>'

    return (disambig_regex, disambig_html), (plain_regex, plain_html)


# 标准正则字符类
CONTENT_PLAIN = r'[^〖〗<>"'        # 普通内容
CONTENT_DISAMBIG = r'[^〖〗<>"|'    # 消歧内容（含管道符）

# 实体类型映射（v3.0，2026-03）
# 名词实体（18类）：〖TYPE content〗 格式
# 动词实体（4类）：⟦TYPE content⟧ 格式
# 消歧语法：〖TYPE 显示名|规范名〗 或 ⟦TYPE 显示名|规范名⟧

ENTITY_PATTERNS = [
    # ==== 基础Markdown格式 ====
    (r'\\*\\*([^*<>"]+)\\*\\*', r'<strong>\\1</strong>'),  # 粗体

    # ==== 动词实体（v3.0，优先处理避免被名词模式匹配） ====
    *_verb_pattern('◈', 'verb-military', '军事动词'),   # 军事动词
    *_verb_pattern('◉', 'verb-penalty', '刑罚动词'),    # 刑罚动词
    *_verb_pattern('○', 'verb-political', '政治动词'),  # 政治动词（预留）
    *_verb_pattern('◇', 'verb-economic', '经济动词'),   # 经济动词（预留）

    # ==== 名词实体（18类） ====
    # 按标注符号顺序排列：•; = % & ◆ ^ ~ # ! @ + $ ? { : [ _

    # 器物
    *_entity_pattern('•', CONTENT_PLAIN, CONTENT_DISAMBIG, 'artifact', '器物'),
    # 官职
    *_entity_pattern(';', CONTENT_PLAIN, CONTENT_DISAMBIG, 'official', '官职'),
    # 地名
    *_entity_pattern('=', CONTENT_PLAIN, CONTENT_DISAMBIG, 'place', '地名'),
    # 时间
    *_entity_pattern('%', CONTENT_PLAIN, CONTENT_DISAMBIG, 'time', '时间'),
    # 氏族
    *_entity_pattern('&', CONTENT_PLAIN, CONTENT_DISAMBIG, 'dynasty', '氏族'),
    # 邦国
    *_entity_pattern('◆', CONTENT_PLAIN, CONTENT_DISAMBIG, 'feudal-state', '邦国'),
    # 制度
    *_entity_pattern('^', CONTENT_PLAIN, CONTENT_DISAMBIG, 'institution', '制度'),
    # 族群
    *_entity_pattern('~', CONTENT_PLAIN, CONTENT_DISAMBIG, 'tribe', '族群'),
    # 身份
    *_entity_pattern('#', CONTENT_PLAIN, CONTENT_DISAMBIG, 'identity', '身份'),
    # 天文/历法
    *_entity_pattern('!', CONTENT_PLAIN, CONTENT_DISAMBIG, 'astronomy', '天文/历法'),
    # 人名
    *_entity_pattern('@', CONTENT_PLAIN, CONTENT_DISAMBIG, 'person', '人名'),
    # 生物
    *_entity_pattern('+', CONTENT_PLAIN, CONTENT_DISAMBIG, 'biology', '生物'),
    # 数量
    *_entity_pattern('$', CONTENT_PLAIN, CONTENT_DISAMBIG, 'quantity', '数量'),
    # 神话/传说
    *_entity_pattern('?', CONTENT_PLAIN, CONTENT_DISAMBIG, 'mythical', '神话/传说'),
    # 典籍（特殊：自动添加书名号）
    *_entity_pattern('{', CONTENT_PLAIN, CONTENT_DISAMBIG, 'book', '典籍', prefix='《', suffix='》'),
    # 礼仪
    *_entity_pattern(':', CONTENT_PLAIN, CONTENT_DISAMBIG, 'ritual', '礼仪'),
    # 刑法
    *_entity_pattern('[', CONTENT_PLAIN, CONTENT_DISAMBIG, 'legal', '刑法'),
    # 思想
    *_entity_pattern('_', CONTENT_PLAIN, CONTENT_DISAMBIG, 'concept', '思想'),
]

'''
    return code


def main():
    """执行重构"""
    source_file = Path('render_shiji_html.py')

    if not source_file.exists():
        print("错误：找不到 render_shiji_html.py")
        return False

    content = source_file.read_text(encoding='utf-8')

    # 找到 ENTITY_PATTERNS 定义的起始和结束位置
    pattern_start = content.find('ENTITY_PATTERNS = [')
    if pattern_start == -1:
        print("错误：找不到 ENTITY_PATTERNS 定义")
        return False

    # 找到对应的 ] 结束位置（需要匹配括号）
    bracket_count = 0
    i = pattern_start + len('ENTITY_PATTERNS = [') - 1
    while i < len(content):
        if content[i] == '[':
            bracket_count += 1
        elif content[i] == ']':
            bracket_count -= 1
            if bracket_count == 0:
                pattern_end = i + 1
                break
        i += 1
    else:
        print("错误：找不到 ENTITY_PATTERNS 结束位置")
        return False

    # 生成新代码
    new_patterns_code = generate_refactored_patterns()

    # 替换旧代码
    # 需要从注释开始的位置替换（包括 "# 实体类型映射"）
    comment_start = content.rfind('#', 0, pattern_start)
    # 回退到行首
    while comment_start > 0 and content[comment_start - 1] != '\n':
        comment_start -= 1

    new_content = content[:comment_start] + new_patterns_code + content[pattern_end:]

    # 写回文件
    source_file.write_text(new_content, encoding='utf-8')
    print("✓ 重构完成：ENTITY_PATTERNS 已优化")
    print("\n请运行测试验证：python tests/test_render_shiji_html.py")

    return True


if __name__ == '__main__':
    main()
