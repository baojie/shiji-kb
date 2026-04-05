#!/usr/bin/env python3
"""
重构步骤2：简化 ENTITY_PATTERNS

将102行重复的正则模式，用辅助函数简化为更易维护的形式
"""

from pathlib import Path

# 新的 ENTITY_PATTERNS 定义（使用辅助函数生成）
NEW_PATTERNS_CODE = r'''# 实体类型映射（v3.0，2026-03）
# 名词实体（18类）：〖TYPE content〗 格式，TYPE为单字符标记（@=;%&◆^~#•!?+{:[]_$）
# 动词实体（4类）：⟦TYPE content⟧ 格式，TYPE为圆形符号（◈◉○◇）
# 消歧语法：〖TYPE 显示名|规范名〗 或 ⟦TYPE 显示名|规范名⟧

# 辅助函数：生成标准的实体标注模式对（消歧格式 + 普通格式）
def _make_noun_pattern(marker, css_class, title):
    """生成名词实体的模式对（消歧 + 普通）

    Args:
        marker: 标记符号（如 '@', '=', '◆'）
        css_class: CSS类名（如 'person', 'place'）
        title: 标题文本（如 '人名', '地名'）

    Returns:
        list: 包含2个元组的列表 [(消歧pattern, 消歧replacement), (普通pattern, 普通replacement)]
    """
    import re
    m = re.escape(marker)  # 转义特殊字符
    content_plain = r'[^〖〗<>"'
    content_disambig = r'[^〖〗<>"|'

    return [
        # 消歧格式：〖marker 显示名|规范名〗
        (
            rf'〖{m}({content_disambig}+)\|({content_plain}+)〗',
            rf'<span class="{css_class}" title="{title}：\2" data-canonical="\2">\1</span>'
        ),
        # 普通格式：〖marker content〗
        (
            rf'〖{m}({content_plain}+)〗',
            rf'<span class="{css_class}" title="{title}">\1</span>'
        ),
    ]


def _make_verb_pattern(marker, css_class, title):
    """生成动词实体的模式对（消歧 + 普通）

    Args:
        marker: 标记符号（如 '◈', '◉'）
        css_class: CSS类名（如 'verb-military'）
        title: 标题文本（如 '军事动词'）

    Returns:
        list: 包含2个元组的列表
    """
    content = r'[^⟦⟧'

    return [
        # 消歧格式：⟦marker 显示名|规范名⟧
        (
            rf'⟦{marker}({content}|)+\|({content}+)⟧',
            rf'<span class="{css_class}" title="{title}：\2" data-canonical="\2">\1</span>'
        ),
        # 普通格式：⟦marker content⟧
        (
            rf'⟦{marker}({content}+)⟧',
            rf'<span class="{css_class}" title="{title}">\1</span>'
        ),
    ]


# 构建 ENTITY_PATTERNS 列表
ENTITY_PATTERNS = [
    # ==== 基础Markdown ====
    (r'\*\*([^*<>"]+)\*\*', r'<strong>\1</strong>'),  # 粗体

    # ==== 动词实体（v3.0，优先处理） ====
    *_make_verb_pattern('◈', 'verb-military', '军事动词'),
    *_make_verb_pattern('◉', 'verb-penalty', '刑罚动词'),
    *_make_verb_pattern('○', 'verb-political', '政治动词'),  # 预留
    *_make_verb_pattern('◇', 'verb-economic', '经济动词'),   # 预留

    # ==== 名词实体（18类，按标注符号顺序） ====
    *_make_noun_pattern('•', 'artifact', '器物'),
    *_make_noun_pattern(';', 'official', '官职'),
    *_make_noun_pattern('=', 'place', '地名'),
    *_make_noun_pattern('%', 'time', '时间'),
    *_make_noun_pattern('&', 'dynasty', '氏族'),
    *_make_noun_pattern('◆', 'feudal-state', '邦国'),
    *_make_noun_pattern('^', 'institution', '制度'),
    *_make_noun_pattern('~', 'tribe', '族群'),
    *_make_noun_pattern('#', 'identity', '身份'),
    *_make_noun_pattern('!', 'astronomy', '天文/历法'),
    *_make_noun_pattern('@', 'person', '人名'),
    *_make_noun_pattern('+', 'biology', '生物'),
    *_make_noun_pattern('$', 'quantity', '数量'),
    *_make_noun_pattern('?', 'mythical', '神话/传说'),

    # ==== 特殊格式：典籍（自动添加书名号） ====
    (
        r'〖\{([^〖〗<>"|]+)\|([^〖〗<>"]+)〗',
        r'<span class="book" title="典籍：\2" data-canonical="\2">《\1》</span>'
    ),
    (
        r'〖\{([^〖〗<>"]+)〗',
        r'<span class="book" title="典籍">《\1》</span>'
    ),

    # ==== 其他名词实体 ====
    *_make_noun_pattern(':', 'ritual', '礼仪'),
    *_make_noun_pattern('[', 'legal', '刑法'),
    *_make_noun_pattern('_', 'concept', '思想'),
]
'''


def main():
    """执行重构"""
    source = Path('render_shiji_html.py')
    content = source.read_text(encoding='utf-8')

    # 找到 ENTITY_PATTERNS 定义的起始位置
    # 从注释行开始：# 实体类型映射（v3.0，2026-03）
    pattern_marker = '# 实体类型映射（v3.0，2026-03）'
    start_pos = content.find(pattern_marker)

    if start_pos == -1:
        print("错误：找不到 ENTITY_PATTERNS 定义")
        return False

    # 找到 ENTITY_PATTERNS = [ ... ] 的结束位置
    # 从 start_pos 开始查找
    list_start = content.find('ENTITY_PATTERNS = [', start_pos)
    if list_start == -1:
        print("错误：找不到 ENTITY_PATTERNS 列表开始")
        return False

    # 找到匹配的 ] (需要计数括号)
    bracket_count = 0
    i = list_start + len('ENTITY_PATTERNS = ')
    while i < len(content):
        if content[i] == '[':
            bracket_count += 1
        elif content[i] == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end_pos = i + 1
                break
        i += 1
    else:
        print("错误：找不到 ENTITY_PATTERNS 列表结束")
        return False

    # 替换整个 ENTITY_PATTERNS 定义（包括注释）
    new_content = content[:start_pos] + NEW_PATTERNS_CODE + '\n' + content[end_pos:]

    source.write_text(new_content, encoding='utf-8')
    print("✓ 重构完成：ENTITY_PATTERNS 已简化")
    print(f"  原始行数: ~102行")
    print(f"  新版行数: ~{len(NEW_PATTERNS_CODE.splitlines())}行")


if __name__ == '__main__':
    main()
    print("\n请运行测试验证：python tests/test_render_shiji_html.py")
