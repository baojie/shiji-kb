#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将包含 <span style="color: #xxxxxx; ...">...</span> 的 Markdown 转为简洁标记。
输出到同目录下的 *.tagged.md

用法: python tools/convert_spans_to_simple.py ../chapter_md/001_五帝本纪.md
"""
import re
import sys
from pathlib import Path

STYLE_MAP = {
    '#8B4513': ('person', '@', '@'),    # 人名
    '#B8860B': ('place', '#', '#'),     # 地名
    '#9370DB': ('dynasty', '&', '&'),   # 朝代/氏族（紫）
    '#8B0000': ('official', '$', '$'),  # 官职（深红）
    '#008B8B': ('time', '%', '%'),      # 时间/纪年（青）
    '#4682B4': ('institution', '^', '^'), # 制度（钢蓝）
    '#2F4F4F': ('tribe', '~', '~'),     # 族群（灰绿）
    '#CD853F': ('artifact', '*', '*'),  # 器物（赭）
    '#483D8B': ('astronomy', '!', '!'), # 天文/历法（暗蓝）
    '#8B008B': ('mythical', '?', '?'),  # 传说/神话（紫红）
}

SPAN_RE = re.compile(r'<span\s+style="([^"]+)">(.+?)</span>', re.DOTALL)


def replace_span(m):
    style = m.group(1)
    content = m.group(2)
    # try to find a color code in style
    for color, (cls, pre, post) in STYLE_MAP.items():
        if color.lower() in style.lower():
            # strip inner HTML if any (rare)
            text = re.sub(r'<[^>]+>', '', content)
            return f'{pre}{text}{post}'
    # fallback: remove span but keep content
    return re.sub(r'<[^>]+>', '', content)


def convert_file(src_path: Path):
    txt = src_path.read_text(encoding='utf-8')
    # replace spans
    out = SPAN_RE.sub(replace_span, txt)
    # remove any remaining style attributes (defensive)
    out = re.sub(r'<(/?)span[^>]*>', r'<\1span>', out)
    # also replace HTML strong tags with markdown bold
    out = re.sub(r'<strong>(.*?)</strong>', r'**\1**', out, flags=re.DOTALL)
    # clean up isolated html-escaped sequences if present
    out = out.replace('&nbsp;', ' ')
    out = out.replace('&lt;', '<').replace('&gt;', '>')
    # write output
    out_path = src_path.with_name(src_path.stem + '.tagged.md')
    out_path.write_text(out, encoding='utf-8')
    print(f'Converted: {src_path} -> {out_path}')
    return out_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: convert_spans_to_simple.py <markdown-file>')
        sys.exit(1)
    src = Path(sys.argv[1])
    if not src.exists():
        print('Source not found:', src)
        sys.exit(1)
    convert_file(src)
