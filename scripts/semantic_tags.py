#!/usr/bin/env python3
"""
语义标签统一处理模块

定义史记知识库中使用的语义标签标准，并提供统一的处理函数。

标签标准（v2.5，18类实体）：
- 〖@人名〗 - 历史人物、传说人物
- 〖=地名〗 - 城邑、山川、国名
- 〖;官职〗 - 正式任命的职衔、封号
- 〖#身份〗 - 社会角色、地位、血缘关系
- 〖%时间〗 - 年号纪年、月份
- 〖&氏族〗 - 宗族、家族、姓氏集团
- 〖◆邦国〗 - 统一王朝、诸侯国、外邦政权
- 〖^制度〗 - 典章制度、礼法规范
- 〖~族群〗 - 民族、部落
- 〖•器物〗 - 礼器、兵器
- 〖!天文〗 - 星象、历法
- 〖?神话〗 - 传说、神话事件
- 〖+生物〗 - 名词性生物
- 〖{典籍〗 - 古籍书名
- 〖:礼仪〗 - 礼仪制度、宗庙祭祀
- 〖[刑法〗 - 刑罚、法律条文
- 〖_思想〗 - 哲学概念、文体体裁
- 〖$数量〗 - 非时间性计量（军队/距离/重量/金额）

消歧格式：
- 〖@显示名|规范名〗 - 当显示名与规范名不同时使用
  例如：〖@台|吕台〗 → 显示"台"，实体标识为"吕台"
- ⟦◈动词|规范动作⟧ - 动词标注消歧
  例如：⟦◈伐|征伐⟧ → 显示"伐"，语义为"征伐"

核心函数：
- strip_markup(text) - 完整去除所有标注符号（与lint_text_integrity.py一致）
- remove_semantic_tags(text) - 灵活去除标注（支持保留Markdown结构）
- clean_text(text) - 快捷方式，去除所有标注返回纯文本
- render_tags_to_html(text) - 转换为HTML高亮显示

更新历史：
- 2026-04-05: 更新为完整的18类实体标注系统（v2.5）
- 2026-04-03: 同步lint_text_integrity.py中的最新标注去除逻辑，支持消歧语法
"""

import re
from typing import Dict, Tuple


# 标准语义标签定义（v2.5，18类实体完整系统）
# CSS类名与颜色与 render_shiji_html.py 和 docs/css/shiji-styles-v6.css 保持一致
SEMANTIC_TAG_TYPES = {
    '@': ('person', '人名', '#8B4513'),          # 褐色
    '=': ('place', '地名', '#A0522D'),           # 赭褐色
    ';': ('official', '官职', '#8B4513'),        # 褐色
    '#': ('identity', '身份', '#4682B4'),        # 钢青色
    '%': ('time', '时间', '#008B8B'),            # 深青色
    '&': ('dynasty', '氏族', '#9370DB'),         # 紫色（氏族使用dynasty类）
    '◆': ('feudal-state', '邦国', '#9370DB'),   # 紫色
    '^': ('institution', '制度', '#4682B4'),     # 钢青色
    '~': ('tribe', '族群', '#9370DB'),           # 紫色
    '•': ('artifact', '器物', '#CD853F'),        # 秘鲁色（橙褐）
    '!': ('astronomy', '天文', '#CD853F'),       # 秘鲁色（橙褐）
    '?': ('mythical', '神话', '#CD853F'),        # 秘鲁色（橙褐）
    '+': ('biology', '生物', '#CD853F'),         # 秘鲁色（橙褐）
    '{': ('book', '典籍', '#2F4F4F'),            # 深石板灰（墨绿）
    ':': ('ritual', '礼仪', '#4682B4'),          # 钢青色
    '[': ('legal', '刑法', '#4682B4'),           # 钢青色
    '_': ('concept', '思想', '#2F4F4F'),         # 深石板灰（墨绿）
    '$': ('quantity', '数量', '#2E8B57'),        # 海洋绿
}


# 旧版标签映射（已废弃，v2.5已全面统一为18类标准）
# 保留此定义仅用于历史兼容性参考
LEGACY_TAG_MAPPING = {}

# 实体标注前缀字符（所有支持的18类标记）
_ENTITY_PFX = r'[@=;#%&◆^\~•!\'+?{:\[_$]'


def strip_markup(text: str) -> str:
    """
    去除全部语义标注符号，保留实体内容本身

    此函数与 lint_text_integrity.py 中的实现保持一致，用于标注文本完整性检查。

    参数:
        text: 包含标注的文本

    返回:
        去除所有标注符号后的纯文本
    """
    # 1. Markdown 标题行（不在原文中）
    text = re.sub(r'^#{1,6}.*$', '', text, flags=re.MULTILINE)

    # 2. ## 标题 区块（标注标题行 + 下方内容行，不在原文中）
    text = re.sub(r'^## 标题\n[^\n]*\n?', '', text, flags=re.MULTILINE)

    # 3. ::: 围栏块标记行（太史公曰 / 赞诗等）
    text = re.sub(r'^:::.*$', '', text, flags=re.MULTILINE)

    # 3. 行首引用符 "> "
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)

    # 4. 行首列表符 "- "（含缩进子列表 "  - "）
    text = re.sub(r'^\s*-\s', '', text, flags=re.MULTILINE)

    # 5. 段落编号 [1] [1.1] [1.1.2] 等
    text = re.sub(r'^\[\d+(?:\.\d+)*\]\s*', '', text, flags=re.MULTILINE)

    # 6a. 动词标注括号 → 保留内容（v3.0新增，支持消歧 ⟦◈伐|征伐⟧ → 伐）
    text = re.sub(r'⟦[◈◉○◇]([^⟦⟧|]*)(?:\|[^⟦⟧]*)?⟧', r'\1', text)

    # 6b. 名词实体标注括号 → 保留内容（支持内联消歧 〖@台|吕台〗 → 台）
    text = re.sub(rf'〖{_ENTITY_PFX}([^〖〗|]*)(?:\|[^〖〗]*)?〗', r'\1', text)
    text = re.sub(r'〖[^〗]*〗', '', text)   # 剩余残留

    # 7. 旧格式残留括号（已迁移至〖TYPE〗，仅保留〘〙兼容）
    text = re.sub(r'〘([^〘〙]*)〙', r'\1', text)

    # 8. 粗体 **content** -> content
    text = re.sub(r'\*\*([^*]*)\*\*', r'\1', text)

    # 9. Markdown 分隔线（--- 等）
    text = re.sub(r'^-{3,}\s*$', '', text, flags=re.MULTILINE)

    # 10. Markdown 表格分隔行（| --- | --- | 等，十表章节特有）
    text = re.sub(r'^\|[\s\-|]+\|?\s*$', '', text, flags=re.MULTILINE)

    return text


def remove_semantic_tags(text: str, normalize_legacy: bool = False, strip_markdown: bool = False) -> str:
    """
    移除语义标签，只保留显示文本

    参数:
        text: 包含语义标签的文本
        normalize_legacy: 是否先将旧版标签转换为新标准（默认False，直接移除）
        strip_markdown: 是否同时去除Markdown结构标记（标题、围栏块等）

    返回:
        移除标签后的纯文本

    示例:
        "〖@武王〗伐〖#纣〗" -> "武王伐纣"
        "〖@姬发|周武王〗" -> "姬发"
        "⟦◈伐|征伐⟧" -> "伐"
    """
    if not text:
        return text

    # 如果需要，先规范化旧版标签
    if normalize_legacy:
        text = normalize_legacy_tags(text)

    # 如果需要完整的标注去除（包含Markdown结构），直接使用 strip_markup()
    if strip_markdown:
        return strip_markup(text)

    # 否则，只去除语义标注符号（保留Markdown结构）
    # 处理动词标注括号 → 保留内容（支持消歧 ⟦◈伐|征伐⟧ → 伐）
    text = re.sub(r'⟦[◈◉○◇]([^⟦⟧|]*)(?:\|[^⟦⟧]*)?⟧', r'\1', text)

    # 处理名词实体标注括号 → 保留内容（支持消歧 〖@台|吕台〗 → 台）
    text = re.sub(rf'〖{_ENTITY_PFX}([^〖〗|]*)(?:\|[^〖〗]*)?〗', r'\1', text)

    # 清理剩余残留标注
    text = re.sub(r'〖[^〗]*〗', '', text)

    # 旧格式残留括号（已迁移至〖TYPE〗，仅保留〘〙兼容）
    text = re.sub(r'〘([^〘〙]*)〙', r'\1', text)

    # 清理残留的未闭合标签符号
    text = text.replace('〖◆', '').replace('〗', '')
    text = text.replace('⟦', '').replace('⟧', '')
    text = text.replace('〘', '').replace('〙', '')

    return text


def normalize_legacy_tags(text: str) -> str:
    """
    将旧版标签符号转换为新标准

    例如: 〖=长安〗 -> 〖#长安〗
    """
    if not text:
        return text

    for old_marker, new_marker in LEGACY_TAG_MAPPING.items():
        # 转换普通格式
        text = text.replace(f'〖{old_marker}', f'〖{new_marker}')
        # 转换消歧格式
        text = re.sub(
            f'〖{re.escape(old_marker)}\\s*([^〗]+)〗',
            f'〖{new_marker}\\1〗',
            text
        )

    return text


def render_tags_to_html(text: str, normalize_legacy: bool = False) -> str:
    """
    将语义标签转换为HTML span标签（保留标注，用于高亮显示）

    参数:
        text: 包含语义标签的文本
        normalize_legacy: 已废弃，保留仅为兼容性（v2.5已统一标准）

    返回:
        转换后的HTML文本

    示例:
        "〖@武王〗" -> '<span class="person" title="人名">武王</span>'
        "〖@台|吕台〗" -> '<span class="person" title="人名">台</span>'
        "〖◆汉〗" -> '<span class="feudal-state" title="邦国">汉</span>'

    注意:
        CSS类名与 docs/css/shiji-styles-v6.css 保持一致，
        直接使用类名（如 "person"），不添加 "entity" 前缀
    """
    if not text:
        return text

    # 处理消歧格式: 〖TYPE显示名|规范名〗 -> HTML（只显示"显示名"）
    for marker, (css_class, title, color) in SEMANTIC_TAG_TYPES.items():
        # 消歧格式（优先处理）
        pattern = f'〖{re.escape(marker)}\\s*([^|〗]+)\\|[^〗]+〗'
        replacement = f'<span class="{css_class}" title="{title}">\\1</span>'
        text = re.sub(pattern, replacement, text)

    # 处理普通格式: 〖TYPE文本〗 -> HTML
    for marker, (css_class, title, color) in SEMANTIC_TAG_TYPES.items():
        pattern = f'〖{re.escape(marker)}\\s*([^〗]+)〗'
        replacement = f'<span class="{css_class}" title="{title}">\\1</span>'
        text = re.sub(pattern, replacement, text)

    # 处理动词标注 → 渲染为 HTML span
    VERB_TYPES = {
        '◈': ('verb-military', '军事动词'),
        '◉': ('verb-penalty', '刑罚动词'),
        '○': ('verb-political', '政治动词'),
        '◇': ('verb-economic', '经济动词'),
    }
    for marker, (css_class, title) in VERB_TYPES.items():
        # ⟦◈动词⟧ 格式（含消歧 ⟦◈显示|规范⟧）
        text = re.sub(
            rf'⟦{re.escape(marker)}([^⟦⟧|]*)(?:\|[^⟦⟧]*)?⟧',
            rf'<span class="{css_class}" title="{title}">\1</span>',
            text
        )
        # 〖◉动词〗 格式（翻译文件中使用）
        text = re.sub(
            rf'〖{re.escape(marker)}\s*([^〖〗|]*)(?:\|[^〖〗]*)?〗',
            rf'<span class="{css_class}" title="{title}">\1</span>',
            text
        )

    # 清理残留的未闭合标签符号
    text = text.replace('〗', '').replace('⟦', '').replace('⟧', '')

    return text


def get_entity_css_path() -> str:
    """
    返回统一的CSS文件路径（相对于项目根目录）

    所有HTML生成脚本应该使用 docs/css/shiji-styles-v6.css
    而不是自己生成CSS样式

    返回:
        CSS文件的相对路径
    """
    return 'docs/css/shiji-styles-v6.css'


def get_entity_css_styles() -> str:
    """
    返回实体标注的统一CSS样式（已废弃）

    ⚠️ 废弃警告：不要使用此函数生成内联CSS
    应该使用 get_entity_css_path() 获取外部CSS文件路径
    并在HTML中通过 <link> 标签引用 docs/css/shiji-styles-v6.css

    保留此函数仅为向后兼容，返回简化的基础样式
    """
    css = """
        /* ⚠️ 警告：应使用外部CSS文件 docs/css/shiji-styles-v6.css */
        /* 以下为简化样式，仅用于测试 */
        .entity {
            padding: 0 2px;
            border-radius: 2px;
            cursor: default;
        }
"""

    for marker, (css_class, title, color) in SEMANTIC_TAG_TYPES.items():
        css += f"""
        .{css_class} {{
            color: {color};
            border-bottom: 1px solid {color};
        }}
"""

    return css


def extract_entities(text: str, normalize_legacy: bool = False) -> Dict[str, list]:
    """
    从文本中提取所有实体

    参数:
        text: 包含语义标签的文本
        normalize_legacy: 已废弃，保留仅为兼容性（v2.5已统一标准）

    返回:
        按类型分组的实体列表
        例如: {'person': ['武王', '纣'], 'place': ['朝歌'], 'state': ['汉', '楚']}
    """
    if not text:
        return {}

    entities = {}

    for marker, (css_class, title, color) in SEMANTIC_TAG_TYPES.items():
        # 提取消歧格式中的规范名
        pattern = f'〖{re.escape(marker)}\\s*[^|〗]+\\|([^〗]+)〗'
        canonical_names = re.findall(pattern, text)

        # 提取普通格式
        pattern = f'〖{re.escape(marker)}\\s*([^|〗]+)〗'
        display_names = re.findall(pattern, text)

        if canonical_names or display_names:
            entities[css_class] = list(set(canonical_names + display_names))

    return entities


# 便捷函数
def clean_text(text: str, strip_markdown: bool = False) -> str:
    """
    移除所有语义标签，返回纯文本（快捷方式）

    参数:
        text: 包含语义标签的文本
        strip_markdown: 是否同时去除Markdown结构
    """
    return remove_semantic_tags(text, normalize_legacy=True, strip_markdown=strip_markdown)


def html_with_highlights(text: str) -> str:
    """转换为带高亮的HTML（快捷方式）"""
    return render_tags_to_html(text, normalize_legacy=True)


def test_markup_removal():
    """
    测试标注去除函数的正确性

    验证所有标注去除函数能正确处理：
    1. 基本标注格式 〖TYPE内容〗
    2. 消歧格式 〖TYPE显示名|规范名〗
    3. 动词标注 ⟦TYPE动词⟧
    4. 动词消歧 ⟦TYPE动词|规范动作⟧
    """
    test_cases = [
        # (输入, 期望输出, 描述)
        ('〖@武王〗伐〖@纣〗', '武王伐纣', '基本人名标注'),
        ('〖@姬发|周武王〗伐商', '姬发伐商', '人名消歧：保留显示名'),
        ('〖=长安〗城', '长安城', '地名标注'),
        ('〖;丞相〗上奏', '丞相上奏', '官职标注'),
        ('〖#天子〗驾崩', '天子驾崩', '身份标注'),
        ('〖%元〗年', '元年', '时间标注'),
        ('〖&嬴氏〗后裔', '嬴氏后裔', '氏族标注'),
        ('〖◆汉〗灭〖◆秦〗', '汉灭秦', '邦国标注'),
        ('〖^郡县制〗', '郡县制', '制度标注'),
        ('〖~匈奴〗入侵', '匈奴入侵', '族群标注'),
        ('〖•九鼎〗', '九鼎', '器物标注'),
        ('〖!岁星〗出现', '岁星出现', '天文标注'),
        ('〖?黄帝〗传说', '黄帝传说', '神话标注'),
        ('〖+龙〗飞', '龙飞', '生物标注'),
        ('〖{春秋〗记载', '春秋记载', '典籍标注'),
        ('〖:祭祀〗礼仪', '祭祀礼仪', '礼仪标注'),
        ('〖[腰斩〗之刑', '腰斩之刑', '刑法标注'),
        ('〖_仁义〗思想', '仁义思想', '思想标注'),
        ('〖$三万人〗', '三万人', '数量标注'),
        ('⟦◈伐|征伐⟧商', '伐商', '动词消歧'),
        ('〖@樊哙〗⟦◈从⟧〖@高祖〗', '樊哙从高祖', '混合标注'),
    ]

    print('=' * 60)
    print('语义标注去除函数测试')
    print('=' * 60)

    all_passed = True

    for i, (input_text, expected, description) in enumerate(test_cases, 1):
        # 测试 strip_markup()
        result1 = strip_markup(input_text)
        # 测试 clean_text()
        result2 = clean_text(input_text)
        # 测试 remove_semantic_tags() 不带strip_markdown
        result3 = remove_semantic_tags(input_text, normalize_legacy=True, strip_markdown=False)

        # 所有三个函数应该产生相同的结果（对于纯文本输入）
        passed = (result1 == expected and result2 == expected and result3 == expected)
        status = '✓' if passed else '✗'

        if not passed:
            all_passed = False

        print(f'\n测试 {i}: {description}')
        print(f'{status} 输入: {input_text}')
        print(f'  期望: {expected}')
        if result1 != expected:
            print(f'  strip_markup()         : {result1} ✗')
        if result2 != expected:
            print(f'  clean_text()           : {result2} ✗')
        if result3 != expected:
            print(f'  remove_semantic_tags() : {result3} ✗')

    print('\n' + '=' * 60)
    if all_passed:
        print('✓ 所有测试通过！')
    else:
        print('✗ 部分测试失败，请检查上述输出')
    print('=' * 60)

    return all_passed


if __name__ == '__main__':
    # 运行测试
    import sys
    success = test_markup_removal()
    sys.exit(0 if success else 1)
