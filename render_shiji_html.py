#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史记Markdown渲染器
将简洁标记的Markdown转换为带CSS样式的HTML

注意：本模块提供单个文件的转换功能。
批量生成所有章节请使用：python generate_all_chapters.py

标记语法：
- @人名@ -> <span class="person">人名</span>
- =地名= -> <span class="place">地名</span>
- $官职$ -> <span class="official">官职</span>
- %时间% -> <span class="time">时间</span>
- &朝代& -> <span class="dynasty">朝代</span>
- ^制度^ -> <span class="institution">制度</span>
- ~族群~ -> <span class="tribe">族群</span>
- *器物* -> <span class="artifact">器物</span>
- !天文! -> <span class="astronomy">天文</span>
- 〚神话〛 -> <span class="mythical">神话</span>
- 〘动植物〙 -> <span class="flora-fauna">动植物</span>
"""

import re
import sys
import os
import json
from pathlib import Path
from html import escape as html_escape

# 实体类型映射
# 注意：顺序至关重要！外层标记必须先于内层标记处理。
# 人名 @..@ 最常作为内层标注（如 $@安国君@$、$太子@安国君@$），
# 因此 @人名@ 放在最后，确保外层标记先转为<span>，内层再在其中匹配。
# 重要：** 必须在 * 之前处理，以避免冲突
# 排除 " 字符以避免匹配HTML属性
ENTITY_PATTERNS = [
    # ** 和 * 必须最先处理：韵文中 **粗体** 常包含实体标注（如 **...^制度^...**）
    (r'\*\*([^*<>"]+)\*\*', r'<strong>\1</strong>'),           # 加粗（必须在单*之前）
    (r'\*([^*<>"]+)\*', r'<span class="artifact" title="器物/书名">\1</span>'),  # 器物/礼器/书名
    # 实体标注：外层标记先于内层处理
    (r'\$([^$<>"]+)\$', r'<span class="official" title="官职">\1</span>'),  # 官职（常包裹人名）
    (r'=([^=<>"]+)=', r'<span class="place" title="地名">\1</span>'),       # 地名
    (r'%([^%<>"]+)%', r'<span class="time" title="时间">\1</span>'),        # 时间
    (r'&([^&<>"]+)&', r'<span class="dynasty" title="朝代/氏族">\1</span>'),     # 朝代
    (r'\^([^<>^"]+)\^', r'<span class="institution" title="制度">\1</span>'),  # 制度
    (r'~([^~<>"]+)~', r'<span class="tribe" title="族群">\1</span>'),       # 族群
    (r'〘([^〘〙<>"]+)〙', r'<span class="flora-fauna" title="动植物">\1</span>'),  # 动植物
    (r'!([^!<>"]+)!', r'<span class="astronomy" title="天文/历法">\1</span>'),   # 天文
    (r'〚([^〚〛<>"]+)〛', r'<span class="mythical" title="神话/传说">\1</span>'),  # 神话
    (r'@([^@<>"]+)@', r'<span class="person" title="人名">\1</span>'),      # 人名（最后处理，常为内层）
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
    'institution': 'institution.html',
    'tribe': 'tribe.html',
    'artifact': 'artifact.html',
    'astronomy': 'astronomy.html',
    'mythical': 'mythical.html',
    'flora-fauna': 'flora-fauna.html',
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

        # Step 1: 消歧（仅人名，章节级）
        resolved = entity_text
        disambiguated = False
        if css_class == 'person' and chapter_id:
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

    # 匹配最内层实体span: <span class="TYPE" title="LABEL">TEXT</span>
    # [^<]+ 确保只匹配不含子标签的最内层span
    text = re.sub(
        r'<span class="([^"]+)" title="[^"]*">([^<]+)</span>',
        _entity_link_replacer,
        text
    )
    return text


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

    # 安全网：清理残留的标注符号
    # 1. 紧邻<span>标签的裸字符（嵌套标注残留）
    text = re.sub(r'[\$@\^~\*!〘〙〚〛](?=<span[\s>])', '', text)
    text = re.sub(r'(?<=</span>)[\$@\^~\*!〘〙〚〛]', '', text)
    # 2. 清除残留的 $ 和 @（源数据中未配对的标注符号）
    #    这两个字符在古汉语中不出现，且不在生成的HTML属性中，可安全清除
    #    注意：不能清除 % = & ，因为它们在HTML中有合法用途
    text = text.replace('$', '').replace('@', '')

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


def markdown_to_html(md_file, output_file=None, css_file=None, prev_chapter=None, next_chapter=None, original_text_file=None):
    """
    将简洁标记的Markdown转换为HTML

    Args:
        md_file: 输入的Markdown文件路径
        output_file: 输出的HTML文件路径（可选，默认为同名.html）
        css_file: CSS文件路径（可选，默认为css/shiji-styles.css）
        prev_chapter: 上一章的文件名（可选）
        next_chapter: 下一章的文件名（可选）
        original_text_file: 原文txt文件的路径（可选）
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
    
    # 确定CSS文件路径
    if css_file is None:
        css_file = md_path.parent.parent / 'docs' / 'css' / 'shiji-styles.css'
    
    # 读取Markdown内容
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 规范化段落编号：将行首类似 [23.a] 或 [23a] 的编号替换为仅数字的 [23]
    # 只在行首进行替换以减少误伤其他中括号用法
    md_content = re.sub(r'(?m)^\[(\d+)(?:\.[a-zA-Z]+|[a-zA-Z]+)\]', r'[\1]', md_content)

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
        # 只做标注符号剥离（去掉 @=&^~*!$%〘〙〚〛 包裹符），保留纯文字
        _annotation_strip = re.compile(
            r'[@=\$%&\^~\*!]([^@=\$%&\^~\*!\n]{1,30}?)[@=\$%&\^~\*!]'
            r'|〘([^〘〙\n]{1,30}?)〙'
            r'|〚([^〚〛\n]{1,30}?)〛'
        )
        def strip_annotations(text):
            return _annotation_strip.sub(lambda m: m.group(1) or m.group(2) or m.group(3), text)

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

        # 标题 - 为h1标题添加原文链接
        if line.startswith('# '):
            flush_para()
            title_content = line[2:]
            if original_text_file:
                line = f'<h1>{title_content} <a href="{original_text_file}" class="original-text-link">原文</a></h1>'
            else:
                line = f'<h1>{title_content}</h1>'
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

        # 引用块 或 NOTE 块
        elif line.startswith('> '):
            flush_para()
            # NOTE 块语法:
            #   开始:  > [!NOTE] 或 > [!NOTE tag]
            #   显式结束: > [!ENDNOTE]
            m_start = re.match(r'^>\s*\[!NOTE(?:\s*[: ]\s*(?P<tag>[\w-]+))?\]\s*(?P<rest>.*)$', line)
            m_end = re.match(r'^>\s*\[!ENDNOTE\]\s*$', line)
            if m_end:
                if in_note:
                    html_lines.append('</div>')
                    in_note = False
                # if not in_note, ignore stray END marker
                continue
            if m_start:
                # 关闭普通 blockquote 若打开
                if in_blockquote:
                    html_lines.append('</blockquote>')
                    in_blockquote = False
                tag = m_start.group('tag')
                rest = m_start.group('rest') or ''
                classes = 'note-box'
                if tag:
                    # add semantic class
                    classes += f' note-{tag}'
                html_lines.append(f'<div class="{classes}">')
                heading = 'NOTE'
                if tag:
                    heading = f'{heading} — {tag}'
                html_lines.append(f'<h4>{heading}</h4>')
                in_note = True
                if rest:
                    html_lines.append(f'<p>{rest}</p>')
                continue
            else:
                if in_note:
                    # 如果正在 note 中但遇到普通引用行
                    content = line[2:]
                    if content.strip().startswith('- '):
                        # 这是列表项
                        if not in_list:
                            html_lines.append('<ul>')
                            in_list = True
                        html_lines.append(f'<li>{content.strip()[2:]}</li>')
                    else:
                        # 关闭列表（如果有）
                        if in_list:
                            html_lines.append('</ul>')
                            in_list = False
                        # 把它当作 note 内段落
                        html_lines.append(f'<p>{content}</p>')
                    continue
                if not in_blockquote:
                    html_lines.append('<blockquote>')
                    in_blockquote = True
                # 在 blockquote 中，检查是否是列表项
                content = line[2:]
                if content.strip().startswith('- '):
                    # 这是列表项
                    if not in_list:
                        html_lines.append('<ul>')
                        in_list = True
                    html_lines.append(f'<li>{content.strip()[2:]}</li>')
                else:
                    # 关闭列表（如果有）
                    if in_list:
                        html_lines.append('</ul>')
                        in_list = False
                    # 普通内容，添加 <br> 以保持诗歌格式
                    # 去掉 [NOTE] 标记（非 [!NOTE] 格式的注释标签）
                    content = re.sub(r'^\s*\[NOTE\]\s*', '', content)
                    if content.strip():  # 非空行
                        html_lines.append(content + '<br>')
                    else:
                        html_lines.append('')
                continue
        elif in_blockquote and not line.startswith('>'):
            # 关闭列表（如果有）
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append('</blockquote>')
            in_blockquote = False
        elif in_note and not line.startswith('>'):
            # 结束 note 区块
            # 关闭列表（如果有）
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append('</div>')
            in_note = False

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
    for entity_class in ['person', 'place', 'official', 'time', 'dynasty', 'institution', 'tribe', 'artifact', 'astronomy', 'mythical', 'quoted']:
        # 匹配嵌套的同类 span 并展平
        pattern = rf'<span class="{entity_class}">(<span class="{entity_class}">.*?</span>)</span>'
        while re.search(pattern, html_body):
            html_body = re.sub(pattern, r'\1', html_body)

    # 特殊语义调整：将已标注为人名但实际上为氏族的若干名称，转换为朝代/氏族样式
    CLAN_NAMES = [
        '高阳',
        '高辛',
    ]
    for cname in CLAN_NAMES:
        # 只替换被标注为 person 的情形，改为 dynasty
        html_body = re.sub(
            rf'<span class="person">({re.escape(cname)})</span>',
            rf'<span class="dynasty">\1</span>',
            html_body
        )

    # 后处理：注入年表数据（替换"（表略）"）
    if '<p>（表略）</p>' in html_body:
        # 从文件名推断章节编号
        chapter_prefix = md_path.stem.replace('.tagged', '')
        table_html_dir = md_path.parent.parent / 'docs' / 'table_html'
        if not table_html_dir.exists():
            table_html_dir = Path('docs/table_html')
        table_file = table_html_dir / f'{chapter_prefix}_table.html'
        if table_file.exists():
            with open(table_file, 'r', encoding='utf-8') as tf:
                table_content = tf.read()
            html_body = html_body.replace(
                '<p>（表略）</p>',
                table_content,
                1  # 只替换第一个
            )

    # 生成完整HTML
    # 计算CSS文件的相对路径（从输出HTML文件到CSS文件）
    try:
        # 使用 os.path.relpath 来计算相对路径，支持兄弟目录
        import os
        css_href = os.path.relpath(css_file, output_path.parent)
        # 计算chapter-nav.css的相对路径
        chapter_nav_css = os.path.relpath(str(Path(css_file).parent / 'chapter-nav.css'), output_path.parent)
        # 计算purple-numbers.js的相对路径
        purple_numbers_js = os.path.relpath(str(Path(css_file).parent.parent / 'js' / 'purple-numbers.js'), output_path.parent)
    except Exception:
        # 如果失败，使用简单的相对路径（假设标准目录结构）
        css_href = "../css/shiji-styles.css"
        chapter_nav_css = "../css/chapter-nav.css"
        purple_numbers_js = "../js/purple-numbers.js"

    # 生成导航栏HTML
    # 计算主页链接：如果输出在 docs/chapters/ 下则用 ../index.html
    index_path = Path('docs/index.html')
    try:
        home_href = os.path.relpath(str(index_path), str(output_path.parent))
    except Exception:
        home_href = "../index.html"
    nav_html = '<nav class="chapter-nav">\n'
    nav_html += f'    <a href="{home_href}" class="nav-home">回到主页</a>\n'
    if prev_chapter:
        nav_html += f'    <a href="{prev_chapter}" class="nav-prev">← 上一页</a>\n'
    if next_chapter:
        nav_html += f'    <a href="{next_chapter}" class="nav-next">下一页 →</a>\n'
    nav_html += '</nav>'

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{md_path.stem.replace('.tagged', '')}</title>
    <link rel="stylesheet" href="{css_href}">
    <link rel="stylesheet" href="{chapter_nav_css}">
    <script src="{purple_numbers_js}"></script>
</head>
<body>
{nav_html}
{html_body}
{nav_html}
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
        print("用法: python render_shiji_html.py <markdown文件> [输出文件] [css文件]")
        print("示例: python render_shiji_html.py chapter_md/001_五帝本纪.md")
        sys.exit(1)

    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    css_file = sys.argv[3] if len(sys.argv) > 3 else None

    # 自动推断前后章导航（避免单章渲染时丢失导航链接）
    # 扫描同目录下按文件名排序的所有 .tagged.md 文件
    from pathlib import Path as _Path
    _md_path = _Path(md_file)
    _siblings = sorted(_md_path.parent.glob('*.tagged.md'))
    _prev_chapter = None
    _next_chapter = None
    if len(_siblings) > 1:
        try:
            _idx = _siblings.index(_md_path.resolve())
        except ValueError:
            _idx = next((i for i, p in enumerate(_siblings) if p.name == _md_path.name), -1)
        if _idx > 0:
            _prev_name = _siblings[_idx - 1].stem.replace('.tagged', '')
            _prev_chapter = f'{_prev_name}.html'
        if _idx >= 0 and _idx < len(_siblings) - 1:
            _next_name = _siblings[_idx + 1].stem.replace('.tagged', '')
            _next_chapter = f'{_next_name}.html'

    # 自动推断原文链接（相对于输出 HTML 文件的路径）
    # 标准结构：chapter_md/NNN_章名.tagged.md → docs/original_text/NNN_章名.txt
    _stem = _md_path.stem.replace('.tagged', '')
    _output_path = _Path(output_file) if output_file else _Path('docs/chapters') / f'{_stem}.html'
    _original_txt = _output_path.parent.parent / 'original_text' / f'{_stem}.txt'
    _original_text_file = None
    if _original_txt.exists():
        import os as _os
        _original_text_file = _os.path.relpath(str(_original_txt), str(_output_path.parent))

    markdown_to_html(md_file, output_file, css_file,
                     prev_chapter=_prev_chapter, next_chapter=_next_chapter,
                     original_text_file=_original_text_file)
