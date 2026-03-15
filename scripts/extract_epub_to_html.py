#!/usr/bin/env python3
"""
将维基文库的《史记》和《史记三家注》epub提取为独立HTML文件。

用法：
    python scripts/extract_epub_to_html.py

输出：
    archive/wikisource_shiji/         — 史记130卷（每卷1个HTML）
    archive/wikisource_sanjia/        — 三家注130卷（每卷1个HTML）
    各目录下生成 index.html 目录页
"""

import zipfile
import re
import os
from pathlib import Path

# 章节名映射（卷号 → 章名）
CHAPTER_NAMES = {
    1: '五帝本紀', 2: '夏本紀', 3: '殷本紀', 4: '周本紀', 5: '秦本紀',
    6: '秦始皇本紀', 7: '項羽本紀', 8: '高祖本紀', 9: '呂太后本紀',
    10: '孝文本紀', 11: '孝景本紀', 12: '孝武本紀',
    13: '三代世表', 14: '十二諸侯年表', 15: '六國年表',
    16: '秦楚之際月表', 17: '漢興以來諸侯王年表', 18: '高祖功臣侯者年表',
    19: '惠景閒侯者年表', 20: '建元以來侯者年表', 21: '建元已來王子侯者年表',
    22: '漢興以來將相名臣年表',
    23: '禮書', 24: '樂書', 25: '律書', 26: '曆書', 27: '天官書',
    28: '封禪書', 29: '河渠書', 30: '平準書',
    31: '吳太伯世家', 32: '齊太公世家', 33: '魯周公世家', 34: '燕召公世家',
    35: '管蔡世家', 36: '陳杞世家', 37: '衛康叔世家', 38: '宋微子世家',
    39: '晉世家', 40: '楚世家', 41: '越王句踐世家', 42: '鄭世家',
    43: '趙世家', 44: '魏世家', 45: '韓世家', 46: '田敬仲完世家',
    47: '孔子世家', 48: '陳涉世家', 49: '外戚世家', 50: '楚元王世家',
    51: '荊燕世家', 52: '齊悼惠王世家', 53: '蕭相國世家', 54: '曹相國世家',
    55: '留侯世家', 56: '陳丞相世家', 57: '絳侯周勃世家', 58: '梁孝王世家',
    59: '五宗世家', 60: '三王世家',
    61: '伯夷列傳', 62: '管晏列傳', 63: '老子韓非列傳', 64: '司馬穰苴列傳',
    65: '孫子吳起列傳', 66: '伍子胥列傳', 67: '仲尼弟子列傳',
    68: '商君列傳', 69: '蘇秦列傳', 70: '張儀列傳',
    71: '樗里子甘茂列傳', 72: '穰侯列傳', 73: '白起王翦列傳',
    74: '孟子荀卿列傳', 75: '孟嘗君列傳', 76: '平原君虞卿列傳',
    77: '魏公子列傳', 78: '春申君列傳', 79: '范雎蔡澤列傳',
    80: '樂毅列傳', 81: '廉頗藺相如列傳', 82: '田單列傳',
    83: '魯仲連鄒陽列傳', 84: '屈原賈生列傳', 85: '呂不韋列傳',
    86: '刺客列傳', 87: '李斯列傳', 88: '蒙恬列傳',
    89: '張耳陳餘列傳', 90: '魏豹彭越列傳', 91: '黥布列傳',
    92: '淮陰侯列傳', 93: '韓信盧綰列傳', 94: '田儋列傳',
    95: '樊酈滕灌列傳', 96: '張丞相列傳', 97: '酈生陸賈列傳',
    98: '傅靳蒯成列傳', 99: '劉敬叔孫通列傳', 100: '季布欒布列傳',
    101: '袁盎鼂錯列傳', 102: '張釋之馮唐列傳', 103: '萬石張叔列傳',
    104: '田叔列傳', 105: '扁鵲倉公列傳', 106: '吳王濞列傳',
    107: '魏其武安侯列傳', 108: '韓長孺列傳', 109: '李將軍列傳',
    110: '匈奴列傳', 111: '衛將軍驃騎列傳', 112: '平津侯主父列傳',
    113: '南越列傳', 114: '東越列傳', 115: '朝鮮列傳',
    116: '西南夷列傳', 117: '司馬相如列傳', 118: '淮南衡山列傳',
    119: '循吏列傳', 120: '汲鄭列傳', 121: '儒林列傳',
    122: '酷吏列傳', 123: '大宛列傳', 124: '游俠列傳',
    125: '佞幸列傳', 126: '滑稽列傳', 127: '日者列傳',
    128: '龜策列傳', 129: '貨殖列傳', 130: '太史公自序',
}


def clean_xhtml(content, is_sanjia=False):
    """清理epub xhtml为干净的HTML片段"""
    # 移除XML声明和DOCTYPE
    content = re.sub(r'<\?xml[^?]*\?>', '', content)
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content)

    # 提取<body>内容
    body_match = re.search(r'<body[^>]*>(.*)</body>', content, re.DOTALL)
    if body_match:
        body = body_match.group(1)
    else:
        body = content

    # 移除导航表格（ws-header class）
    body = re.sub(r'<table[^>]*class="[^"]*ws-header[^"]*"[^>]*>.*?</table>',
                  '', body, flags=re.DOTALL)

    # 移除维基提示框（ombox, mbox, sistersitebox）
    body = re.sub(r'<table[^>]*class="[^"]*(?:ombox|mbox|sistersitebox)[^"]*"[^>]*>.*?</table>',
                  '', body, flags=re.DOTALL)

    # 移除不可选择的div（包含维基百科链接框）
    body = re.sub(r'<div[^>]*user-select:\s*none[^>]*>.*?</div>',
                  '', body, flags=re.DOTALL)

    # 移除CDATA样式块
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)

    # 移除空的span（mw:FallbackId等）
    body = re.sub(r'<span[^>]*typeof="mw:FallbackId"[^>]*/>', '', body)

    # 移除section包裹但保留内容
    body = re.sub(r'</?section[^>]*>', '', body)

    # 移除data-mw-*属性（减少体积）
    body = re.sub(r'\s+data-mw-[a-z-]+="[^"]*"', '', body)

    # 移除about属性
    body = re.sub(r'\s+about="[^"]*"', '', body)

    # 移除typeof属性（保留有意义的）
    body = re.sub(r'\s+typeof="mw:(?:Transclusion|Extension/templatestyles|FallbackId)"', '', body)

    # 将XHTML自闭合span转为正常闭合（浏览器不识别自闭合span）
    body = re.sub(r'<span([^>]*)/>', r'<span\1></span>', body)

    # 移除display:inline-block+inline-size缩进span（导致后续内容被限制在2em宽度内）
    body = re.sub(r'<span[^>]*inline-size:\s*\d+em[^>]*></span>', '', body)

    # 移除透明隐藏文本（〈〉标记）
    body = re.sub(r'<span[^>]*color:transparent[^>]*>[^<]*</span>', '', body)

    # 清理空行
    body = re.sub(r'\n{3,}', '\n\n', body)

    # 移除前后空白
    body = body.strip()

    return body


def generate_chapter_html(body, title, css_path, prev_link=None, next_link=None, index_link='index.html'):
    """生成完整的HTML页面"""
    nav_parts = [f'<a href="{index_link}">目錄</a>']
    if prev_link:
        nav_parts.append(f'<a href="{prev_link}">← 上一卷</a>')
    if next_link:
        nav_parts.append(f'<a href="{next_link}">下一卷 →</a>')
    nav = '<nav class="chapter-nav">' + ' | '.join(nav_parts) + '</nav>'

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="{css_path}">
</head>
<body>
{nav}
{body}
{nav}
</body>
</html>
"""


def generate_css(is_sanjia=False):
    """生成维基文库风格的CSS"""
    css = """/* 维基文库《史记》样式 */
body {
    font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", serif;
    line-height: 2.0;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    background-color: #fdfdf8;
    color: #2c2c2c;
}
h1, h2 { color: #8B0000; }
h2 { border-left: 4px solid #8B4513; padding-left: 12px; margin-top: 2em; }
h3 { color: #8B4513; margin-top: 1.5em; }
p { margin: 1.5em 0; }
a { color: #3366cc; text-decoration: none; }
a:hover { text-decoration: underline; }
/* 维基链接（实体标注） */
a.extiw, a[rel="mw:WikiLink/Interwiki"] {
    color: #3366cc;
    border-bottom: 1px dotted #3366cc;
}
/* 导航 */
.chapter-nav {
    text-align: center;
    padding: 10px;
    margin: 10px 0;
    border-bottom: 1px solid #ddd;
    font-size: 0.9em;
}
.chapter-nav a { margin: 0 10px; }
/* 目录页 */
.toc-grid { column-count: 2; column-gap: 2em; }
.toc-section { break-inside: avoid; margin-bottom: 1em; }
.toc-section h3 { margin: 0.5em 0 0.3em; }
.toc-section ul { list-style: none; padding-left: 1em; margin: 0; }
.toc-section li { margin: 0.2em 0; }
/* 表格 */
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; vertical-align: top; }
th { background: #f5f0e0; }
/* 引用 */
blockquote { border-left: 3px solid #ccc; margin: 1em 0; padding-left: 1em; }
dl { margin: 0.5em 0; }
dd { margin-left: 2em; }
"""
    if is_sanjia:
        css += """
/* 三家注样式 */
/* 集解标签 */
span[style*="background-color: green"] {
    background-color: #2e7d32 !important;
    color: white !important;
    font-size: 0.8em;
    padding: 1px 4px;
    border-radius: 3px;
    font-weight: bold;
}
/* 集解内容 */
span[style*="color:green"] { color: #2e7d32 !important; font-size: 0.95em; }
/* 索隐标签 */
span[style*="background-color: deepPink"] {
    background-color: #c2185b !important;
    color: white !important;
    font-size: 0.8em;
    padding: 1px 4px;
    border-radius: 3px;
    font-weight: bold;
}
/* 索隐内容 */
span[style*="color:deeppink"] { color: #c2185b !important; font-size: 0.95em; }
/* 正义标签 */
span[style*="background-color: #966"] {
    background-color: #996666 !important;
    color: white !important;
    font-size: 0.8em;
    padding: 1px 4px;
    border-radius: 3px;
    font-weight: bold;
}
/* 人名下划线 */
span[style*="text-decoration: underline"][style*="text-decoration-style: solid"] {
    text-decoration: underline !important;
    text-decoration-color: #8B4513 !important;
    text-underline-offset: 3px !important;
}
/* 书名波浪线 */
span[style*="text-decoration-style: wavy"] {
    text-decoration: underline wavy !important;
    text-decoration-color: #4B0082 !important;
    text-underline-offset: 3px !important;
}
"""
    return css


def generate_index_html(chapters, title, css_path):
    """生成目录页HTML"""
    sections = [
        ('本紀', 1, 12),
        ('表', 13, 22),
        ('書', 23, 30),
        ('世家', 31, 60),
        ('列傳', 61, 130),
    ]

    toc_html = '<div class="toc-grid">\n'
    for sec_name, start, end in sections:
        toc_html += f'<div class="toc-section">\n<h3>{sec_name}</h3>\n<ul>\n'
        for num in range(start, end + 1):
            if num in chapters:
                fname, ch_name = chapters[num]
                toc_html += f'<li><a href="{fname}">卷{num:03d} {ch_name}</a></li>\n'
        toc_html += '</ul>\n</div>\n'
    toc_html += '</div>\n'

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="{css_path}">
</head>
<body>
<h1>{title}</h1>
<p>來源：<a href="https://zh.wikisource.org/">維基文庫</a></p>
{toc_html}
</body>
</html>
"""


def extract_epub(epub_path, output_dir, is_sanjia=False):
    """从epub提取所有章节为独立HTML文件"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 写入CSS
    css_name = 'styles.css'
    with open(output_path / css_name, 'w', encoding='utf-8') as f:
        f.write(generate_css(is_sanjia))

    z = zipfile.ZipFile(epub_path)

    # 找到所有章节文件（跳过c0目录页）
    xhtml_files = sorted([f for f in z.namelist()
                          if f.startswith('OPS/c') and f.endswith('.xhtml')
                          and not re.match(r'OPS/c0_', f)])

    chapters = {}  # num -> (filename, chapter_name)
    filenames = []  # 按顺序的文件名列表

    for xhtml in xhtml_files:
        # 提取卷号
        m = re.search(r'juan(\d+)', xhtml)
        if not m:
            continue
        num = int(m.group(1))

        content = z.read(xhtml).decode('utf-8')
        body = clean_xhtml(content, is_sanjia)

        ch_name = CHAPTER_NAMES.get(num, f'卷{num:03d}')
        fname = f'{num:03d}_{ch_name}.html'

        chapters[num] = (fname, ch_name)
        filenames.append((num, fname))

        print(f'  提取: 卷{num:03d} {ch_name}')

    # 生成带导航的HTML文件
    for i, (num, fname) in enumerate(filenames):
        xhtml = [f for f in xhtml_files if f'juan{num:03d}' in f][0]
        content = z.read(xhtml).decode('utf-8')
        body = clean_xhtml(content, is_sanjia)

        ch_name = CHAPTER_NAMES.get(num, f'卷{num:03d}')
        title = f'史記 卷{num:03d} {ch_name}'

        prev_link = filenames[i - 1][1] if i > 0 else None
        next_link = filenames[i + 1][1] if i < len(filenames) - 1 else None

        html = generate_chapter_html(body, title, css_name, prev_link, next_link)

        with open(output_path / fname, 'w', encoding='utf-8') as f:
            f.write(html)

    z.close()

    # 生成目录页
    index_title = '史記三家註（維基文庫）' if is_sanjia else '史記（維基文庫）'
    index_html = generate_index_html(chapters, index_title, css_name)
    with open(output_path / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f'  目錄: index.html')
    return len(chapters)


def main():
    base = Path(__file__).parent.parent / 'archive'

    # 史記
    shiji_epub = base / '史記.epub'
    if shiji_epub.exists():
        print(f'\n=== 提取《史記》===')
        n = extract_epub(shiji_epub, base / 'wikisource_shiji', is_sanjia=False)
        print(f'完成：{n} 卷 → archive/wikisource_shiji/')

    # 三家注
    sanjia_epub = base / '史記三家註.epub'
    if sanjia_epub.exists():
        print(f'\n=== 提取《史記三家註》===')
        n = extract_epub(sanjia_epub, base / 'wikisource_sanjia', is_sanjia=True)
        print(f'完成：{n} 卷 → archive/wikisource_sanjia/')


if __name__ == '__main__':
    main()
