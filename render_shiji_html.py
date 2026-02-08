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
- ?神话? -> <span class="mythical">神话</span>
- 🌿动植物🌿 -> <span class="flora-fauna">动植物</span>
"""

import re
import sys
import os
from pathlib import Path

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
    (r'🌿([^🌿<>"]+)🌿', r'<span class="flora-fauna" title="动植物">\1</span>'),  # 动植物
    (r'!([^!<>"]+)!', r'<span class="astronomy" title="天文/历法">\1</span>'),   # 天文
    (r'\?([^?<>"]+)\?', r'<span class="mythical" title="神话/传说">\1</span>'),  # 神话
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
    text = re.sub(r'[\$@\^~\*!?🌿](?=<span[\s>])', '', text)
    text = re.sub(r'(?<=</span>)[\$@\^~\*!?🌿]', '', text)
    # 2. 清除残留的 $ 和 @（源数据中未配对的标注符号）
    #    这两个字符在古汉语中不出现，且不在生成的HTML属性中，可安全清除
    #    注意：不能清除 % = & ，因为它们在HTML中有合法用途
    text = text.replace('$', '').replace('@', '')

    # 最后处理段落编号（PN - Purple Numbers）
    # 将 [编号] 转换为可点击的锚点链接
    def pn_replacement(match):
        pn = match.group(1)
        pn_id = f"pn-{pn}"
        return f'<a href="#{pn_id}" id="{pn_id}" class="para-num" title="点击复制链接">{pn}</a>'

    text = re.sub(r'(?<!["\'>])\[(\d+(?:\.\d+)*)\]', pn_replacement, text)

    return text


def markdown_to_html(md_file, output_file=None, css_file=None, prev_chapter=None, next_chapter=None, original_text_file=None):
    """
    将简洁标记的Markdown转换为HTML

    Args:
        md_file: 输入的Markdown文件路径
        output_file: 输出的HTML文件路径（可选，默认为同名.html）
        css_file: CSS文件路径（可选，默认为doc/shiji-styles.css）
        prev_chapter: 上一章的文件名（可选）
        next_chapter: 下一章的文件名（可选）
        original_text_file: 原文txt文件的路径（可选）
    """
    md_path = Path(md_file)
    
    if not md_path.exists():
        print(f"错误：文件 {md_file} 不存在")
        return
    
    # 确定输出文件
    if output_file is None:
        output_file = md_path.with_suffix('.html')
    output_path = Path(output_file)
    
    # 确定CSS文件路径
    if css_file is None:
        css_file = md_path.parent.parent / 'doc' / 'shiji-styles.css'
    
    # 读取Markdown内容
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 规范化段落编号：将行首类似 [23.a] 或 [23a] 的编号替换为仅数字的 [23]
    # 只在行首进行替换以减少误伤其他中括号用法
    md_content = re.sub(r'(?m)^\[(\d+)(?:\.[a-zA-Z]+|[a-zA-Z]+)\]', r'[\1]', md_content)
    
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
        css_href = "../doc/shiji-styles.css"
        chapter_nav_css = "../css/chapter-nav.css"
        purple_numbers_js = "../js/purple-numbers.js"

    # 生成导航栏HTML
    nav_html = '<nav class="chapter-nav">\n'
    nav_html += '    <a href="../docs/index.html" class="nav-home">回到主页</a>\n'
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
    <title>{md_path.stem}</title>
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
    
    markdown_to_html(md_file, output_file, css_file)
