#!/usr/bin/env python3
"""
将 hunterhug/china-history 仓库（https://github.com/hunterhug/china-history）中
《史记》130 篇的 *-段译.html 转换为 corpus/shiji/段译/NNN_章节名_段译.txt，
保留原文/白话段落对应关系。

源仓库本地路径：/home/baojie/work/thirdparty/china-history/史记/

源格式：
  <p>文言原文...</p>
  <p style="color:#967d63;">白话译文...</p>
  （交替出现）

目标格式：
  # NNN 章节名

  【原文】
  文言...

  【译文】
  白话...

  ---

  【原文】
  下一段...
  ...
"""

import re
import sys
from pathlib import Path

SOURCE_ROOT = Path('/home/baojie/work/thirdparty/china-history/史记')
OUTPUT_DIR = Path('corpus/shiji/段译')

# 章节分类 → (目录名, 起始编号)
CATEGORIES = [
    ('十二本纪', 0),
    ('十表',    12),
    ('八书',    22),
    ('三十世家', 30),
    ('七十列传', 60),
]

# 中文数字转阿拉伯数字
CN_DIGITS = {'〇': 0, '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
             '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}

def cn_to_int(s: str) -> int:
    """'第二十三章' → 23"""
    s = s.replace('第', '').replace('章', '').strip()
    if not s:
        return 0
    # 处理 X十Y 形式
    if '十' in s:
        parts = s.split('十', 1)
        tens = CN_DIGITS.get(parts[0], 1) if parts[0] else 1
        ones = CN_DIGITS.get(parts[1], 0) if parts[1] else 0
        return tens * 10 + ones
    # 单个数字
    return CN_DIGITS.get(s, 0)


def parse_duanyi_html(html: str):
    """解析段译 html，返回 [(原文, 译文), ...] 列表。"""
    # 先提取 <body> 到 </body>
    body_match = re.search(r'<body[^>]*>(.*)</body>', html, re.DOTALL)
    if body_match:
        body = body_match.group(1)
    else:
        body = html

    # 匹配所有 <p ...>内容</p>
    p_pattern = re.compile(r'<p([^>]*)>(.*?)</p>', re.DOTALL)
    paragraphs = []
    for m in p_pattern.finditer(body):
        attrs = m.group(1)
        content = m.group(2).strip()
        # 去除内嵌标签（<a>、<span>等）
        content = re.sub(r'<[^>]+>', '', content).strip()
        if not content:
            continue
        is_translation = 'color:#967d63' in attrs or 'color:#967D63' in attrs
        paragraphs.append((is_translation, content))

    # 过滤掉导航（首页/上一节/下一节/目录等）和标题（通常较短）
    filtered = []
    for is_trans, txt in paragraphs:
        if any(x in txt for x in ['首页', '上一节：', '下一节：', '目录']):
            continue
        filtered.append((is_trans, txt))

    # 将相邻的 (原文, 译文) 两两配对
    pairs = []
    i = 0
    while i < len(filtered):
        orig_is_trans, orig_txt = filtered[i]
        if orig_is_trans:
            # 开头是译文，跳过或记为单独译文
            pairs.append(('', orig_txt))
            i += 1
            continue
        # 查看下一段是否译文
        if i + 1 < len(filtered) and filtered[i + 1][0]:
            pairs.append((orig_txt, filtered[i + 1][1]))
            i += 2
        else:
            # 原文后面没紧跟译文（罕见），单独保存
            pairs.append((orig_txt, ''))
            i += 1
    return pairs


def get_chapter_filename(raw_name: str) -> str:
    """'第二章-夏本纪' → '夏本纪'（只取章节中文名）"""
    m = re.match(r'第(.+?)章[-—–](.+)', raw_name)
    return m.group(2).strip() if m else raw_name


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    failed = []

    for cat_dir, base in CATEGORIES:
        cat_path = SOURCE_ROOT / cat_dir
        if not cat_path.exists():
            print(f'[WARN] 目录不存在: {cat_path}')
            continue
        for f in sorted(cat_path.glob('*-段译.html')):
            stem = f.stem.replace('-段译', '')  # '第二章-夏本纪'
            # 抽取章号
            m = re.match(r'(第.+?章)[-—–]', stem)
            if not m:
                failed.append((f.name, '无法解析章号'))
                continue
            ch_in_cat = cn_to_int(m.group(1))
            ch_num = base + ch_in_cat
            if ch_num <= 0 or ch_num > 130:
                failed.append((f.name, f'章号越界: {ch_num}'))
                continue
            chapter_name = get_chapter_filename(stem)
            out_name = f'{ch_num:03d}_{chapter_name}_段译.txt'
            out_path = OUTPUT_DIR / out_name

            html = f.read_text(encoding='utf-8', errors='replace')
            pairs = parse_duanyi_html(html)

            lines = [f'# {ch_num:03d} {chapter_name}', '']
            for orig, trans in pairs:
                if orig:
                    lines.append('【原文】')
                    lines.append(orig)
                    lines.append('')
                if trans:
                    lines.append('【译文】')
                    lines.append(trans)
                    lines.append('')
                lines.append('---')
                lines.append('')
            out_path.write_text('\n'.join(lines), encoding='utf-8')
            total += 1

    print(f'生成 {total} 个文件到 {OUTPUT_DIR}')
    if failed:
        print(f'失败 {len(failed)} 个：')
        for n, r in failed:
            print(f'  {n}: {r}')


if __name__ == '__main__':
    main()
