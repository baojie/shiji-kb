#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术文章Markdown渲染器
将简洁标记的技术文章Markdown转换为带CSS样式的HTML
支持句子级排版、语义缩进等技术文章特定功能

基于史记渲染器修改，专用于 resources/publications/ 下的技术文章

标记语法：
- @人名@ -> <span class="person">人名</span>
- =地名= -> <span class="place">地名</span>
- $官职$ -> <span class="official">官职</span>
- %时间% -> <span class="time">时间</span>
- &朝代& -> <span class="dynasty">朝代</span>
- '封国 -> <span class="feudal-state">封国</span>
- ^制度^ -> <span class="institution">制度</span>
- ~族群~ -> <span class="tribe">族群</span>
- 〖•器物〗 -> <span class="artifact">器物</span>
- 〖!天文〗 -> <span class="astronomy">天文</span>
- 〖?神话〗 -> <span class="mythical">神话</span>
- 〖+生物〗 -> <span class="biology">生物</span>
- 〖{典籍〗 -> <span class="book">典籍</span>
- 〖:礼仪〗 -> <span class="ritual">礼仪</span>
- 〖[刑法〗 -> <span class="legal">刑法</span>
- 〖_思想〗 -> <span class="concept">思想</span>
"""

import re
import sys
import os
import json
from pathlib import Path
from html import escape as html_escape

# 实体类型映射（v2.1，2026-03-13）
# 新格式：10类对称符号改为 〖TYPE content〗 统一包裹
#   〖 开头，第一字符为类型标记，〗 结尾，无嵌套歧义
# 5类已迁移为〖TYPE〗格式（v2.8）：神话〖?〗/典籍〖{〗/礼仪〖:〗/刑法〖[〗/思想〖_〗
# 排除 " 字符以避免匹配HTML属性
ENTITY_PATTERNS = [
    (r'\*\*([^*<>"]+)\*\*', r'<strong>\1</strong>'),                               # 粗体（不变）
    # 技术文章动词标注（知识工程工作流）
    (r'⟦◆([^⟦⟧|]+)\|([^⟦⟧]+)⟧', r'<span class="verb-construct" title="构建动词：\2" data-canonical="\2">\1</span>'),  # 构建动词（消歧）
    (r'⟦◆([^⟦⟧]+)⟧', r'<span class="verb-construct" title="构建动词">\1</span>'),                                       # 构建动词
    (r'⟦◇([^⟦⟧|]+)\|([^⟦⟧]+)⟧', r'<span class="verb-process" title="处理动词：\2" data-canonical="\2">\1</span>'),    # 处理动词（消歧）
    (r'⟦◇([^⟦⟧]+)⟧', r'<span class="verb-process" title="处理动词">\1</span>'),                                         # 处理动词
    (r'⟦◎([^⟦⟧|]+)\|([^⟦⟧]+)⟧', r'<span class="verb-reason" title="推理动词：\2" data-canonical="\2">\1</span>'),     # 推理动词（消歧）
    (r'⟦◎([^⟦⟧]+)⟧', r'<span class="verb-reason" title="推理动词">\1</span>'),                                          # 推理动词
    (r'⟦◈([^⟦⟧|]+)\|([^⟦⟧]+)⟧', r'<span class="verb-apply" title="应用动词：\2" data-canonical="\2">\1</span>'),      # 应用动词（消歧）
    (r'⟦◈([^⟦⟧]+)⟧', r'<span class="verb-apply" title="应用动词">\1</span>'),                                           # 应用动词
    # 10类新格式：〖TYPE content〗
    (r'〖•([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'<span class="artifact"     title="器物：\2"       data-canonical="\2">\1</span>'),  # 器物（消歧）
    (r'〖•([^〖〗<>"]+)〗', r'<span class="artifact" title="器物">\1</span>'),     # 器物
    (r'〖;([^〖〗<>"|]+)\|([^〖〗<>"]+)〗',  r'<span class="official"    title="官职：\2"       data-canonical="\2">\1</span>'),  # 官职（消歧）
    (r'〖;([^〖〗<>"]+)〗',  r'<span class="official" title="官职">\1</span>'),    # 官职
    (r'〖=([^〖〗<>"|]+)\|([^〖〗<>"]+)〗',  r'<span class="place"       title="地名：\2"       data-canonical="\2">\1</span>'),  # 地名（消歧）
    (r'〖=([^〖〗<>"]+)〗',  r'<span class="place" title="地名">\1</span>'),       # 地名
    (r'〖%([^〖〗<>"|]+)\|([^〖〗<>"]+)〗',  r'<span class="time"        title="时间：\2"       data-canonical="\2">\1</span>'),  # 时间（消歧）
    (r'〖%([^〖〗<>"]+)〗',  r'<span class="time" title="时间">\1</span>'),        # 时间
    (r'〖&([^〖〗<>"|]+)\|([^〖〗<>"]+)〗',  r'<span class="dynasty"     title="氏族：\2"       data-canonical="\2">\1</span>'),  # 氏族（消歧）
    (r'〖&([^〖〗<>"]+)〗',  r'<span class="dynasty" title="氏族">\1</span>'),      # 氏族
    (r"〖'([^〖〗<>\"|]+)\|([^〖〗<>\"]+)〗", r'<span class="feudal-state" title="邦国：\2"     data-canonical="\2">\1</span>'),  # 邦国（消歧）
    (r"〖'([^〖〗<>\"]+)〗", r'<span class="feudal-state" title="邦国">\1</span>'), # 邦国
    (r'〖\^([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'<span class="institution" title="制度：\2"       data-canonical="\2">\1</span>'),  # 制度（消歧）
    (r'〖\^([^〖〗<>"]+)〗', r'<span class="institution" title="制度">\1</span>'),  # 制度
    (r'〖~([^〖〗<>"|]+)\|([^〖〗<>"]+)〗',  r'<span class="tribe"       title="族群：\2"       data-canonical="\2">\1</span>'),  # 族群（消歧）
    (r'〖~([^〖〗<>"]+)〗',  r'<span class="tribe" title="族群">\1</span>'),       # 族群
    (r'〖#([^〖〗<>"|]+)\|([^〖〗<>"]+)〗',  r'<span class="terminology" title="术语：\2"       data-canonical="\2">\1</span>'),  # 术语（消歧）
    (r'〖#([^〖〗<>"]+)〗',  r'<span class="terminology" title="术语">\1</span>'),  # 术语（技术文章）
    (r'〖※([^〖〗<>"|]+)\|([^〖〗<>"]+)〗',  r'<span class="profession" title="职业：\2"       data-canonical="\2">\1</span>'),  # 职业（消歧）
    (r'〖※([^〖〗<>"]+)〗',  r'<span class="profession" title="职业">\1</span>'),  # 职业（技术文章）
    (r'〖!([^〖〗<>"|]+)\|([^〖〗<>"]+)〗',  r'<span class="astronomy"   title="天文/历法：\2"  data-canonical="\2">\1</span>'),  # 天文（消歧）
    (r'〖!([^〖〗<>"]+)〗',  r'<span class="astronomy" title="天文/历法">\1</span>'), # 天文
    (r'〖@([^〖〗<>"|]+)\|([^〖〗<>"]+)〗',  r'<span class="person"      title="人名：\2"       data-canonical="\2">\1</span>'),  # 人名（消歧：显示|全名）
    (r'〖@([^〖〗<>"]+)〗',  r'<span class="person" title="人名">\1</span>'),      # 人名
    (r'〖\+([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'<span class="biology"     title="生物：\2"       data-canonical="\2">\1</span>'),  # 生物（消歧）
    (r'〖\+([^〖〗<>"]+)〗', r'<span class="biology" title="生物">\1</span>'),      # 生物
    (r'〖\$([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'<span class="quantity"    title="数量：\2"       data-canonical="\2">\1</span>'),  # 数量（消歧）
    (r'〖\$([^〖〗<>"]+)〗', r'<span class="quantity" title="数量">\1</span>'),    # 数量
    # 5类新格式（v2.8）
    (r'〖\?([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'<span class="mythical"    title="神话：\2"       data-canonical="\2">\1</span>'),  # 神话（消歧）
    (r'〖\?([^〖〗<>"]+)〗', r'<span class="mythical" title="神话/传说">\1</span>'),
    (r'〖\{([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'《<span class="book"        title="典籍：\2"       data-canonical="\2">\1</span>》'),  # 典籍（消歧）
    (r'〖\{([^〖〗<>"]+)〗', r'《<span class="book" title="典籍">\1</span>》'),
    (r'〖\|([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'《<span class="book"        title="典籍：\2"       data-canonical="\2">\1</span>》'),  # 典籍（技术文章格式，消歧）
    (r'〖\|([^〖〗<>"]+)〗', r'《<span class="book" title="典籍">\1</span>》'),  # 典籍（技术文章格式）
    (r'〖★([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'<span class="methodology" title="方法论：\2"     data-canonical="\2">\1</span>'),  # 方法论（消歧）
    (r'〖★([^〖〗<>"]+)〗', r'<span class="methodology" title="方法论">\1</span>'),  # 方法论（技术文章）
    (r'〖:([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'<span class="ritual"      title="礼仪：\2"       data-canonical="\2">\1</span>'),  # 礼仪（消歧）
    (r'〖:([^〖〗<>"]+)〗', r'<span class="ritual" title="礼仪">\1</span>'),
    (r'〖\[([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'<span class="legal"       title="刑法：\2"       data-canonical="\2">\1</span>'),  # 刑法（消歧）
    (r'〖\[([^〖〗<>"]+)〗', r'<span class="legal" title="刑法">\1</span>'),
    (r'〖_([^〖〗<>"|]+)\|([^〖〗<>"]+)〗', r'<span class="concept"     title="思想：\2"       data-canonical="\2">\1</span>'),  # 思想（消歧）
    (r'〖_([^〖〗<>"]+)〗', r'<span class="concept" title="思想">\1</span>'),
    # 旧格式兼容（v2.8前）
    (r'〖\?([^〖〗<>"]+)〗', r'<span class="mythical" title="神话/传说">\1</span>'),
    (r'〖\{([^〖〗<>"]+)〗', r'《<span class="book" title="典籍">\1</span>》'),
    (r'〖:([^〖〗<>"]+)〗', r'<span class="ritual" title="礼仪">\1</span>'),
    (r'〖\[([^〖〗<>"]+)〗', r'<span class="legal" title="刑法">\1</span>'),
    (r'〖_([^〖〗<>"]+)〗', r'<span class="concept" title="思想">\1</span>'),
]

# 引号内容模式（用于对话）
# 支持中文引号：""、''、「」、『』以及ASCII引号："、'
# 注意：使用负向后顾确保不匹配HTML属性中的引号（如 class="quoted"）
QUOTE_PATTERNS = [
    (r'[\u201c]([^\u201d<>]+)[\u201d]', r'<span class="quoted">"\1"</span>'),      # 中文双引号 " "
    (r'(?<!class=)[\u0022]([^\u0022<>]+)[\u0022]', r'<span class="quoted">"\1"</span>'),      # ASCII双引号 " " (排除HTML属性)
    (r'[\u2018]([^\u2019<>]+)[\u2019]', r'<span class="quoted">\'\1\'</span>'),    # 中文单引号 ' '
    # ASCII单引号：不处理，因为容易与嵌套引号冲突
    # (r'[\u0027]([^\u0027<>]+)[\u0027]', r'<span class="quoted">\'\1\'</span>'),    # ASCII单引号 ' '
    (r'「([^」<>]+)」', r'<span class="quoted">「\1」</span>'),    # 日式单引号
    (r'『([^』<>]+)』', r'<span class="quoted">『\1』</span>'),    # 日式双引号
]

# 段落编号模式
# 匹配 [数字] 或 [数字.数字] 或 [数字.数字.数字] 等格式
PARAGRAPH_NUMBER_PATTERN = r'\[(\d+(?:\.\d+)*)\]'

# --- 实体索引链接 ---
# 实体类CSS类 → 索引页文件名
_ENTITY_TYPE_FILES = {
    'person': 'person.html',
    'place': 'place.html',
    'official': 'official.html',
    'time': 'time.html',
    'dynasty': 'dynasty.html',
    'feudal-state': 'feudal-state.html',
    'institution': 'institution.html',
    'tribe': 'tribe.html',
    'identity': 'identity.html',
    'artifact': 'artifact.html',
    'astronomy': 'astronomy.html',
    'mythical': 'mythical.html',
    'biology': 'biology.html',
    'book': 'book.html',
    'ritual': 'ritual.html',
    'legal': 'legal.html',
    'concept': 'concept.html',
    'quantity': 'quantity.html',
    # 技术文章专用实体类型
    'terminology': 'terminology.html',
    'methodology': 'methodology.html',
    'profession': 'profession.html',
}

# 别名映射缓存（模块级，只加载一次）
_alias_reverse_map = None
# 消歧映射缓存（模块级，只加载一次）
_disambiguation_map = None
# 年份→公元映射缓存（模块级，只加载一次）
_year_ce_map = None
# 当前渲染的章节ID（由 markdown_to_html 设置，供 _add_entity_links 使用）
_current_chapter_id = None
# 当前段落ID（由 convert_entities 设置，供 _add_entity_links 使用）
_current_para_id = None

def _get_alias_reverse_map():
    """加载 entity_aliases.json，构建 {type: {surface → canonical}} 反向映射"""
    global _alias_reverse_map
    if _alias_reverse_map is not None:
        return _alias_reverse_map

    alias_file = Path(__file__).parent / 'kg' / 'entities' / 'data' / 'entity_aliases.json'
    _alias_reverse_map = {}
    if alias_file.exists():
        try:
            with open(alias_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            for etype, mappings in raw.items():
                _alias_reverse_map[etype] = {}
                for canonical, aliases in mappings.items():
                    _alias_reverse_map[etype][canonical] = canonical
                    for alias in aliases:
                        if alias:
                            _alias_reverse_map[etype][alias] = canonical
        except Exception:
            pass
    return _alias_reverse_map


def _get_disambiguation_map():
    """加载 disambiguation_map.json，返回 {chapter_id: {short_name: full_name}}"""
    global _disambiguation_map
    if _disambiguation_map is not None:
        return _disambiguation_map

    map_file = Path(__file__).parent / 'kg' / 'entities' / 'data' / 'disambiguation_map.json'
    _disambiguation_map = {}
    if map_file.exists():
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                _disambiguation_map = json.load(f)
        except Exception:
            pass
    return _disambiguation_map


def _get_year_ce_map():
    """加载 year_ce_map.json，返回 {chapter_id: {para_id: {surface: {ce_year, ruler, method}}}}"""
    global _year_ce_map
    if _year_ce_map is not None:
        return _year_ce_map

    map_file = Path(__file__).parent / 'kg' / 'year_ce_map.json'
    _year_ce_map = {}
    if map_file.exists():
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                _year_ce_map = json.load(f)
        except Exception:
            pass
    return _year_ce_map


def set_chapter_context(chapter_id):
    """设置当前章节ID，供消歧映射使用"""
    global _current_chapter_id
    _current_chapter_id = chapter_id


def _add_entity_links(text):
    """后处理：为实体 <span> 包裹 <a> 链接指向实体索引页

    只匹配最内层的实体span（文本中不含<的span），
    避免嵌套标注（如 $@安国君@$）产生嵌套 <a> 标签。

    消歧逻辑：对人名实体，先查 disambiguation_map（章节级短名→全名），
    再查 entity_aliases（别名→规范名），确定链接目标。
    对时间实体中的年份，查 year_ce_map 添加公元纪年tooltip并链接到编年索引。
    显示文本保持原文不变，仅链接指向消歧后的实体。
    """
    alias_map = _get_alias_reverse_map()
    disambig_map = _get_disambiguation_map()
    year_ce_map = _get_year_ce_map()
    chapter_id = _current_chapter_id
    para_id = _current_para_id

    def _entity_link_replacer(match):
        full_span = match.group(0)
        css_class = match.group(1)
        entity_text = match.group(2)

        filename = _ENTITY_TYPE_FILES.get(css_class)
        if not filename:
            return full_span

        # 时间实体：年份→公元纪年映射
        if css_class == 'time' and chapter_id and para_id:
            chapter_years = year_ce_map.get(chapter_id, {})
            para_years = chapter_years.get(para_id, {})
            year_info = para_years.get(entity_text)
            if year_info:
                ce_year = year_info.get('ce_year')
                ruler = year_info.get('ruler', '')
                ruler_key = year_info.get('ruler_key', '')
                if ce_year is not None:
                    if ce_year < 0:
                        tooltip = f'公元前{-ce_year}年（{ruler}{entity_text}）'
                    else:
                        tooltip = f'公元{ce_year}年（{ruler}{entity_text}）'
                    href = f"../entities/timeline.html#year-{ce_year}"
                    return f'<a href="{href}" class="entity-link" target="_blank" title="{html_escape(tooltip)}">{full_span}</a>'
                elif ruler_key:
                    tooltip = f'{ruler}{entity_text}'
                    href = f"../entities/timeline.html#ruler-{html_escape(ruler_key)}"
                    return f'<a href="{href}" class="entity-link" target="_blank" title="{html_escape(tooltip)}">{full_span}</a>'

        # Step 0: 内联消歧（data-canonical 属性，来自 〖@台|吕台〗 语法）
        inline_canonical = None
        canonical_match = re.search(r'data-canonical="([^"]+)"', full_span)
        if canonical_match:
            inline_canonical = canonical_match.group(1)

        # Step 1: 消歧（仅人名，章节级）— 内联消歧优先
        resolved = inline_canonical or entity_text
        disambiguated = inline_canonical is not None
        if not disambiguated and css_class == 'person' and chapter_id:
            chapter_disambig = disambig_map.get(chapter_id, {})
            if entity_text in chapter_disambig:
                resolved = chapter_disambig[entity_text]
                disambiguated = True

        # Step 2: 别名解析 → 规范名
        type_map = alias_map.get(css_class, {})
        canonical = type_map.get(resolved, resolved)

        href = f"../entities/{filename}#entity-{html_escape(canonical)}"

        # 消歧后：将内层span的title替换为"类型：全名"（浏览器显示最内层tooltip）
        if disambiguated:
            # 提取原始类型标签（如"人名"）
            title_match = re.search(r'title="([^"]*)"', full_span)
            type_label = title_match.group(1) if title_match else ''
            new_title = f'{type_label}：{html_escape(resolved)}' if type_label else html_escape(resolved)
            span_with_tooltip = re.sub(r'title="[^"]*"', f'title="{new_title}"', full_span, count=1)
            return f'<a href="{href}" class="entity-link" target="_blank">{span_with_tooltip}</a>'
        return f'<a href="{href}" class="entity-link" target="_blank">{full_span}</a>'

    # 匹配最内层实体span: <span class="TYPE" title="LABEL" [data-canonical="X"]>TEXT</span>
    # [^<]+ 确保只匹配不含子标签的最内层span
    text = re.sub(
        r'<span class="([^"]+)" title="[^"]*"(?: data-canonical="[^"]*")?>([^<]+)</span>',
        _entity_link_replacer,
        text
    )
    return text


def split_paragraph_to_sentences(para_text):
    """将段落分割为句子，添加语义缩进

    基于逻辑连接词（因果、递进、转折、条件）判断句子间关系，
    使用缩进表达逻辑层级。

    返回: HTML div 结构，包含 sentence-layout 和 sentence-indent-N 类
    """
    # 按句号、问号、感叹号分割句子
    sentences = re.split(r'([。！？])', para_text)
    # 重组：将标点符号附加到前一句
    combined = []
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            combined.append(sentences[i] + sentences[i+1])
    # 如果最后有剩余（无标点结尾）
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        combined.append(sentences[-1])

    if len(combined) <= 1:
        return para_text  # 单句段落不需要特殊处理

    # 逻辑关系词典（句首）
    logic_connectors = {
        'indent': ['因此', '所以', '由此', '从而', '因而', '故', '进而', '更进一步', '此外', '另外', '同时', '而且', '并且', '同样', '类似地'],
        'contrast': ['但是', '然而', '不过', '可是', '只是', '虽然', '尽管', '相反'],
        'condition': ['如果', '假如', '倘若', '若是', '若', '设若', '一旦', '当'],
    }

    # 分析每句的缩进级别
    result_parts = ['<p class="sentence-layout">']
    for i, sent in enumerate(combined):
        sent = sent.strip()
        if not sent:
            continue

        # 判断逻辑关系
        indent_level = 0
        for connector in logic_connectors['indent']:
            if sent.startswith(connector):
                indent_level = 1
                break

        # 转换实体标记
        sent_html = convert_entities(sent)
        result_parts.append(f'<span class="sentence-indent-{indent_level}">{sent_html}</span>')

    result_parts.append('</p>')
    return ''.join(result_parts)


def convert_entities(text):
    """转换实体标记为HTML标签

    注意：此函数应该只在纯文本行上调用，不应该在已经包含HTML标签的文本上调用
    """
    # 先处理引号内容（在实体标记之前）
    # 这样引号内的实体标记也会被正确处理
    # 注意：只处理外层引号，避免嵌套引号被重复处理
    # 优先处理双引号（中文和ASCII），然后处理单引号
    for pattern, replacement in QUOTE_PATTERNS:
        # 使用负向前瞻避免匹配已经在 span 标签内的引号
        text = re.sub(pattern, replacement, text)

    # 再处理实体标记
    for pattern, replacement in ENTITY_PATTERNS:
        text = re.sub(pattern, replacement, text)

    # 安全网：清理残留的标注符号（新格式下理论上不应出现）
    # 1. 紧邻<span>标签的裸 〖〗 字符
    text = re.sub(r'〖(?=<span[\s>])', '', text)
    text = re.sub(r'(?<=</span>)〗', '', text)
    # 2. 兼容旧格式残留（防万一）
    text = re.sub(r"[;\^~•!'_](?=<span[\s>])", '', text)
    text = re.sub(r"(?<=</span>)[;\^~•!'_]", '', text)

    # 最后处理段落编号（PN - Purple Numbers）
    # 将 [编号] 转换为可点击的锚点链接
    # 同时更新当前段落ID供年份映射使用
    global _current_para_id
    pn_match = re.search(r'(?<!["\'>])\[(\d+(?:\.\d+)*)\]', text)
    if pn_match:
        _current_para_id = pn_match.group(1)

    def pn_replacement(match):
        pn = match.group(1)
        pn_id = f"pn-{pn}"
        return f'<a href="#{pn_id}" id="{pn_id}" class="para-num" title="点击复制链接">{pn}</a>'

    text = re.sub(r'(?<!["\'>])\[(\d+(?:\.\d+)*)\]', pn_replacement, text)

    # 为实体添加索引链接
    text = _add_entity_links(text)

    return text


def markdown_to_html(md_file, output_file=None, css_file=None):
    """
    将简洁标记的技术文章Markdown转换为HTML

    Args:
        md_file: 输入的Markdown文件路径
        output_file: 输出的HTML文件路径（可选，默认为同名.html）
        css_file: CSS文件路径（可选，默认为同目录下的kg-tech-article-styles.css）
    """
    md_path = Path(md_file)

    # 设置章节上下文，供消歧映射使用
    # 从文件名提取章节ID（如 "004_周本纪.tagged.md" → "004"）
    chapter_id = md_path.stem.replace('.tagged', '')[:3]
    set_chapter_context(chapter_id)

    if not md_path.exists():
        print(f"错误：文件 {md_file} 不存在")
        return

    # 确定输出文件
    if output_file is None:
        output_file = md_path.with_suffix('.html')
    output_path = Path(output_file)
    
    # 确定CSS文件路径（技术文章：默认同目录下的 kg-tech-article-styles.css）
    if css_file is None:
        # 优先使用同目录下的技术文章CSS
        css_file = md_path.parent / 'kg-tech-article-styles.css'
        # 如果不存在，尝试使用docs/css下的备用CSS
        if not css_file.exists():
            css_file = md_path.parent.parent / 'docs' / 'css' / 'shiji-styles.css'
    
    # 读取Markdown内容
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 规范化段落编号：将行首类似 [23.a] 或 [23a] 的编号替换为仅数字的 [23]
    # 只在行首进行替换以减少误伤其他中括号用法
    md_content = re.sub(r'(?m)^\[(\d+)(?:\.[a-zA-Z]+|[a-zA-Z]+)\]', r'[\1]', md_content)

    # 获取文章日期（从文件修改时间）
    from datetime import datetime
    article_mtime = os.path.getmtime(md_path)
    article_date = datetime.fromtimestamp(article_mtime).strftime('%Y年%m月%d日')

    # 预处理：将Markdown表格块转换为HTML
    # 检测连续的 | ... | 行，转换为 <table class="shiji-table">
    # 全局行号计数器（跨表格累计，保证同一章内 anchor ID 唯一）
    _row_pn_counter = [0]

    def _convert_md_tables(text):
        """将Markdown表格语法转换为HTML表格"""
        lines = text.split('\n')
        result = []
        i = 0
        while i < len(lines):
            # 检测表格起始行：以 | 开头
            if lines[i].strip().startswith('|') and '|' in lines[i].strip()[1:]:
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                # 至少需要2行（表头 + 分隔行）才构成表格
                if len(table_lines) >= 2:
                    result.append(_md_table_to_html(table_lines))
                else:
                    result.extend(table_lines)
            else:
                result.append(lines[i])
                i += 1
        return '\n'.join(result)

    def _md_table_to_html(table_lines):
        """将Markdown表格行列表转换为HTML表格字符串

        输出为单行HTML（无换行），确保主循环将其视为 <div> 开头的块级元素，
        不会被 is_plain_text() 误判为段落文本。
        每个数据行自动添加 Purple Number 锚点列（行首），便于精确引用。
        """
        def parse_row(line):
            """解析 | cell1 | cell2 | ... | 为单元格列表"""
            stripped = line.strip()
            if stripped.startswith('|'):
                stripped = stripped[1:]
            if stripped.endswith('|'):
                stripped = stripped[:-1]
            return [cell.strip() for cell in stripped.split('|')]

        # 第一行为表头
        headers = parse_row(table_lines[0])
        # 第二行为分隔行（| --- | --- | ...），跳过
        data_start = 1
        if len(table_lines) > 1 and re.match(r'^[\s|:-]+$', table_lines[1].replace('-', '')):
            data_start = 2

        parts = ['<div class="shiji-table-wrapper">', '<table class="shiji-table">']
        # 表头：行号列（空白）+ 原始列；表头不做实体标注渲染（年号/国名等不应被标注样式干扰）
        # 只做标注符号剥离（去掉 〖TYPE〗 和 ⟦TYPE⟧ 包裹符），保留纯文字
        _annotation_strip = re.compile(
            r'〖[@=;%&\'^~•!#\+\$\?\{\:\[\_]([^〖〗\n]{1,30}?)〗|⟦[◈◉○◇]([^⟦⟧\n]{1,30}?)⟧'
        )
        def strip_annotations(text):
            # 匹配两种格式：〖TYPE内容〗 或 ⟦TYPE动词⟧
            # group(1) 为名词实体内容，group(2) 为动词内容
            return _annotation_strip.sub(lambda m: m.group(1) if m.group(1) else m.group(2), text)

        parts.append('<thead><tr>')
        parts.append('<th class="row-pn-col"></th>')
        for h in headers:
            parts.append(f'<th>{strip_annotations(h)}</th>')
        parts.append('</tr></thead>')
        # 数据行：从第一列读取 [rN] 标记并转为 Purple Number 锚点
        # 若无 [rN]，则自动生成（兜底，保证向后兼容）
        parts.append('<tbody>')
        for idx, row_line in enumerate(table_lines[data_start:]):
            row_class = 'even' if idx % 2 == 0 else 'odd'
            cells = parse_row(row_line)
            # 从第一列提取 [rN] 标记
            pn = None
            if cells:
                rn_match = re.match(r'^\s*\[r(\d+)\]\s*', cells[0])
                if rn_match:
                    pn = rn_match.group(1)
                    cells[0] = cells[0][rn_match.end():]
            if pn is None:
                _row_pn_counter[0] += 1
                pn = str(_row_pn_counter[0])
            pn_anchor = (
                f'<a href="#pn-r{pn}" id="pn-r{pn}" '
                f'class="para-num" title="点击复制链接">{pn}</a>'
            )
            parts.append(f'<tr class="{row_class}">')
            parts.append(f'<td class="row-pn-col">{pn_anchor}</td>')
            for cell in cells:
                parts.append(f'<td>{convert_entities(cell)}</td>')
            parts.append('</tr>')
        parts.append('</tbody></table></div>')
        return ''.join(parts)

    md_content = _convert_md_tables(md_content)

    # 基础的Markdown转HTML（简单版）
    html_lines = []
    in_blockquote = False
    in_note = False
    in_list = False
    para_buffer = []  # 累积连续行，合并为同一段落

    def flush_para():
        """将累积的连续行合并为一个 <p>，用 <br> 连接"""
        if para_buffer:
            html_lines.append('<p>' + '<br>\n'.join(para_buffer) + '</p>')
            para_buffer.clear()

    def is_plain_text(line):
        """判断行是否为普通文本（应累积为段落）"""
        return (line.strip()
                and not line.startswith('<h')
                and not line.startswith('<hr')
                and not line.startswith('<ul')
                and not line.startswith('<ol')
                and not line.startswith('<div'))

    for line in md_content.split('\n'):
        # 跳过已预转换的HTML块（如表格）的实体标记转换
        if line.startswith('<div class="shiji-table-wrapper">'):
            flush_para()
            html_lines.append(line)
            continue
        # 转换实体标记
        line = convert_entities(line)

        # 如果行仅为 '>'（可带空白），把它视为一个空换行分隔符（不渲染 '>'）
        # 将空行作为当前 blockquote 或 note 内的空段落，而不是关闭容器，
        # 以便把相邻的引用/注记合并为一个容器，减少碎片化的 <p></p>。
        if re.match(r'^\s*>\s*$', line):
            flush_para()
            if in_note:
                html_lines.append('<p></p>')
                continue
            if in_blockquote:
                html_lines.append('<p></p>')
                continue
            # 非引用上下文下的孤立 '>' 保持为页面空行
            html_lines.append('<p></p>')
            continue

        # 标题 - 为h1标题添加日期元数据
        if line.startswith('# '):
            flush_para()
            title_content = line[2:]
            # 技术文章不使用原文链接，而是添加日期
            line = f'<h1>{title_content}</h1>\n<div class="article-meta">发表于 {article_date}</div>'
        elif line.startswith('## '):
            flush_para()
            line = f'<h2>{line[3:]}</h2>'
        elif line.startswith('### '):
            flush_para()
            line = f'<h3>{line[4:]}</h3>'
        elif line.startswith('#### '):
            flush_para()
            line = f'<h4>{line[5:]}</h4>'
        elif line.startswith('##### '):
            flush_para()
            line = f'<h5>{line[6:]}</h5>'

        # 分隔线
        elif line.strip() == '---':
            flush_para()
            line = '<hr>'

        # ::: fenced div（语义标注块）
        elif line.startswith(':::'):
            flush_para()
            stripped = line.strip()
            if in_note:
                # 关闭 ::: — 结束语义块
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('</div>')
                in_note = False
            else:
                # 开启 ::: [tag] — 开始语义块
                tag = stripped[3:].strip()
                # 短标签（如"太史公曰""赞"）作为class/title；长文本作为内容
                if len(tag) <= 20 and '〖' not in tag:
                    # 短标签：用作CSS class和title
                    clean_tag = re.sub(r'[〖〗〔〕^@&=;~]', '', tag) if tag else ''
                    classes = 'note-box'
                    if clean_tag:
                        classes += f' note-{clean_tag}'
                    if tag:
                        html_lines.append(f'<div class="{classes}" title="{html_escape(tag)}">')
                    else:
                        html_lines.append(f'<div class="{classes}">')
                else:
                    # 长文本/含实体标注：作为div内容渲染
                    html_lines.append('<div class="note-box">')
                    if tag:
                        # 将tag内容作为段落文本处理（实体标注会在后续渲染中处理）
                        para_buffer.append(tag)
                in_note = True
            continue

        # 引用块（blockquote）
        elif line.startswith('> '):
            flush_para()
            if not in_blockquote:
                html_lines.append('<blockquote>')
                in_blockquote = True
            content = line[2:]
            if content.strip().startswith('- '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{content.strip()[2:]}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                content = re.sub(r'^\s*\[NOTE\]\s*', '', content)
                if content.strip():
                    html_lines.append(content + '<br>')
                else:
                    html_lines.append('')
            continue
        elif in_blockquote and not line.startswith('>'):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append('</blockquote>')
            in_blockquote = False

        # 列表
        elif line.strip().startswith('- '):
            flush_para()
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            line = f'<li>{line.strip()[2:]}</li>'
        elif in_list and not line.strip().startswith('- '):
            html_lines.append('</ul>')
            in_list = False

        # 段落：连续非空行合并为同一 <p>，用 <br> 连接
        elif is_plain_text(line):
            para_buffer.append(line)
            continue

        # 空行：结束当前段落
        elif not line.strip():
            flush_para()

        html_lines.append(line)

    # 关闭未闭合的标签
    flush_para()
    if in_blockquote:
        html_lines.append('</blockquote>')
    if in_list:
        html_lines.append('</ul>')
    
    html_body = '\n'.join(html_lines)

    # 后处理：长对话缩进 - 较长的引号内容另起一行，缩进两个汉字
    # 短引号（<=15字）保持内联
    def _indent_long_dialogue(m):
        open_q = m.group(1)   # 开始引号
        content = m.group(2)  # 对话内容
        close_q = m.group(3)  # 结束引号
        # 去掉HTML标签计算实际文本长度
        plain = re.sub(r'<[^>]+>', '', content)
        if len(plain) > 15:
            return f'<span class="dialogue quoted">{open_q}{content}{close_q}</span>'
        return m.group(0)
    # 匹配各种引号格式的 quoted span
    html_body = re.sub(
        r'<span class="quoted">(["\u201c\u300c\u300e])(.+?)(["\u201d\u300d\u300f])</span>',
        _indent_long_dialogue, html_body)

    # 后处理：韵文自动分行
    # 检测规整短句模式（如赞中的四字韵文），在句号后自动换行
    # 保持为同一段落，仅插入 <br> 换行
    def _auto_verse_linebreak(m):
        content = m.group(1)
        # 已有换行的段落不处理
        if '<br>' in content:
            return m.group(0)
        # 提取纯文本（去掉HTML标签）
        plain = re.sub(r'<[^>]+>', '', content)
        # 去掉段落编号前缀
        plain = re.sub(r'^\d+(?:\.\d+)*\s*', '', plain)
        # 统计句末标点
        endings = re.findall(r'[。！？]', plain)
        if len(endings) < 3:
            return m.group(0)
        # 按句分割
        sentences = re.split(r'[。！？]', plain)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) < 3:
            return m.group(0)
        # 平均句长须短（韵文特征）
        avg_len = sum(len(s) for s in sentences) / len(sentences)
        if avg_len > 12:
            return m.group(0)
        # 多数句子须含逗号（韵文: X，Y 对仗结构）
        comma_count = sum(1 for s in sentences if '，' in s or ',' in s)
        if comma_count < len(sentences) * 0.6:
            return m.group(0)
        # 多数句子须短（≤14字），排除夹杂长句的散文
        short_count = sum(1 for s in sentences if len(s) <= 14)
        if short_count < len(sentences) * 0.7:
            return m.group(0)
        # 确认为韵文：在每个句末标点后插入 <br>（最末除外）
        new_content = re.sub(r'([。！？])(?=.)', r'\1<br>\n', content)
        return f'<p>{new_content}</p>'

    html_body = re.sub(r'<p>(.*?)</p>', _auto_verse_linebreak, html_body, flags=re.DOTALL)

    # 后处理：展平嵌套的同类 span 标签
    # 例如: <span class="person"><span class="person">名字</span></span> -> <span class="person">名字</span>
    for entity_class in ['person', 'place', 'official', 'time', 'dynasty', 'institution', 'tribe', 'identity', 'artifact', 'astronomy', 'mythical', 'quoted', 'book', 'ritual', 'legal', 'concept', 'quantity', 'terminology', 'methodology', 'profession', 'verb-construct', 'verb-process', 'verb-reason', 'verb-apply']:
        # 匹配嵌套的同类 span 并展平
        pattern = rf'<span class="{entity_class}">(<span class="{entity_class}">.*?</span>)</span>'
        while re.search(pattern, html_body):
            html_body = re.sub(pattern, r'\1', html_body)

    # 技术文章不需要史记特定的语义调整（氏族名称转换、年表注入等）

    # 生成完整HTML
    # 计算CSS文件的相对路径（从输出HTML文件到CSS文件）
    try:
        # 使用 os.path.relpath 来计算相对路径，支持兄弟目录
        css_href = os.path.relpath(css_file, output_path.parent)
    except Exception:
        # 如果失败，使用同目录CSS
        css_href = "kg-tech-article-styles.css"

    # 技术文章不需要章节导航（独立文章模式）
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{md_path.stem.replace('.tagged', '')}</title>
    <link rel="stylesheet" href="{css_href}">
</head>
<body>
{html_body}
</body>
</html>
"""
    
    # 写入HTML文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"✓ 已生成: {output_path}")
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python render_tech_article.py <markdown文件> [输出文件] [css文件]")
        print("示例: python render_tech_article.py doc/publications/draft/从历史书中探索知识图谱.tagged.md")
        sys.exit(1)

    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    css_file = sys.argv[3] if len(sys.argv) > 3 else None

    markdown_to_html(md_file, output_file, css_file)
