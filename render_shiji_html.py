#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史记Markdown渲染器
将简洁标记的Markdown转换为带CSS样式的HTML

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
"""

import re
import sys
import os
from pathlib import Path

# 实体类型映射
# 注意：这些模式必须按照特定顺序应用，以避免相互干扰
# 使用负向前瞻和负向后顾来避免匹配HTML标签内的字符
# 重要：** 必须在 * 之前处理，以避免冲突
# 排除 " 字符以避免匹配HTML属性
ENTITY_PATTERNS = [
    (r'@([^@<>"]+)@', r'<span class="person" title="人名">\1</span>'),      # 人名
    (r'=([^=<>"]+)=', r'<span class="place" title="地名">\1</span>'),       # 地名
    (r'\$([^$<>"]+)\$', r'<span class="official" title="官职">\1</span>'),  # 官职
    (r'%([^%<>"]+)%', r'<span class="time" title="时间">\1</span>'),        # 时间
    (r'&([^&<>"]+)&', r'<span class="dynasty" title="朝代/氏族">\1</span>'),     # 朝代
    (r'\^([^<>^"]+)\^', r'<span class="institution" title="制度">\1</span>'),  # 制度
    (r'~([^~<>"]+)~', r'<span class="tribe" title="族群">\1</span>'),       # 族群
    (r'\*\*([^*<>"]+)\*\*', r'<strong>\1</strong>'),           # 加粗（保留Markdown，必须在单*之前）
    (r'\*([^*<>"]+)\*', r'<span class="artifact" title="器物/书名">\1</span>'),  # 器物/礼器/书名
    (r'!([^!<>"]+)!', r'<span class="astronomy" title="天文/历法">\1</span>'),   # 天文
    (r'\?([^?<>"]+)\?', r'<span class="mythical" title="神话/传说">\1</span>'),  # 神话
]

# 引号内容模式（用于对话）
# 只支持中文引号：""、''、「」、『』
# 注意：明确使用Unicode转义，不匹配ASCII引号（\u0022）
QUOTE_PATTERNS = [
    (r'[\u201c]([^\u201d<>]+)[\u201d]', r'<span class="quoted">"\1"</span>'),      # 中文双引号 " "
    (r'[\u2018]([^\u2019<>]+)[\u2019]', r'<span class="quoted">\'\1\'</span>'),    # 中文单引号 ' '
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
    for pattern, replacement in QUOTE_PATTERNS:
        text = re.sub(pattern, replacement, text)

    # 再处理实体标记
    for pattern, replacement in ENTITY_PATTERNS:
        text = re.sub(pattern, replacement, text)

    # 最后处理段落编号
    text = re.sub(r'(?<!["\'>])\[(\d+(?:\.\d+)*)\]', r'<span class="para-num">\1</span>', text)

    return text


def markdown_to_html(md_file, output_file=None, css_file=None):
    """
    将简洁标记的Markdown转换为HTML
    
    Args:
        md_file: 输入的Markdown文件路径
        output_file: 输出的HTML文件路径（可选，默认为同名.html）
        css_file: CSS文件路径（可选，默认为doc/shiji-styles.css）
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
    
    for line in md_content.split('\n'):
        # 转换实体标记
        line = convert_entities(line)

        # 如果行仅为 '>'（可带空白），把它视为一个空换行分隔符（不渲染 '>'）
        # 将空行作为当前 blockquote 或 note 内的空段落，而不是关闭容器，
        # 以便把相邻的引用/注记合并为一个容器，减少碎片化的 <p></p>。
        if re.match(r'^\s*>\s*$', line):
            if in_note:
                html_lines.append('<p></p>')
                continue
            if in_blockquote:
                html_lines.append('<p></p>')
                continue
            # 非引用上下文下的孤立 '>' 保持为页面空行
            html_lines.append('<p></p>')
            continue
        
        # 标题
        if line.startswith('# '):
            line = f'<h1>{line[2:]}</h1>'
        elif line.startswith('## '):
            line = f'<h2>{line[3:]}</h2>'
        elif line.startswith('### '):
            line = f'<h3>{line[4:]}</h3>'
        elif line.startswith('#### '):
            line = f'<h4>{line[5:]}</h4>'
        
        # 分隔线
        elif line.strip() == '---':
            line = '<hr>'
        
        # 引用块 或 NOTE 块
        elif line.startswith('> '):
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
                    # 如果正在 note 中但遇到普通引用行，把它当作 note 内段落
                    html_lines.append(f'<p>{line[2:]}</p>')
                    continue
                if not in_blockquote:
                    html_lines.append('<blockquote>')
                    in_blockquote = True
                # 在 blockquote 中，每行添加 <br> 以保持诗歌格式
                content = line[2:]
                if content.strip():  # 非空行
                    html_lines.append(content + '<br>')
                else:
                    html_lines.append('')
                continue
        elif in_blockquote and not line.startswith('>'):
            html_lines.append('</blockquote>')
            in_blockquote = False
        elif in_note and not line.startswith('>'):
            # 结束 note 区块
            html_lines.append('</div>')
            in_note = False
        
        # 列表
        elif line.strip().startswith('- '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            line = f'<li>{line.strip()[2:]}</li>'
        elif in_list and not line.strip().startswith('- '):
            html_lines.append('</ul>')
            in_list = False
        
        # 段落
        # 注意：包含段落编号的行也应该被包裹成 <p> 标签
        elif line.strip() and not line.startswith('<h') and not line.startswith('<hr') and not line.startswith('<ul') and not line.startswith('<ol') and not line.startswith('<div'):
            line = f'<p>{line}</p>'
        
        html_lines.append(line)
    
    # 关闭未闭合的标签
    if in_blockquote:
        html_lines.append('</blockquote>')
    if in_list:
        html_lines.append('</ul>')
    
    html_body = '\n'.join(html_lines)

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
    # compute a safe href for CSS: try relative path, else absolute path
    try:
        css_href = str(Path(css_file).relative_to(output_path.parent))
    except Exception:
        css_href = str(Path(css_file).resolve())

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{md_path.stem}</title>
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
        print("用法: python render_shiji_html.py <markdown文件> [输出文件] [css文件]")
        print("示例: python render_shiji_html.py chapter_md/001_五帝本纪.md")
        sys.exit(1)
    
    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    css_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    markdown_to_html(md_file, output_file, css_file)
