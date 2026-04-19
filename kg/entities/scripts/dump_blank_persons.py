#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出未分类 person 实体及其上下文（前后各 40 字），供人工反思。

用法：
  python dump_blank_persons.py           # 写入 doc/entities/人名反思/待反思_上下文.md
  python dump_blank_persons.py 第一轮     # 写入 第一轮_上下文.md
  python dump_blank_persons.py 第二轮     # 写入 第二轮_上下文.md
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
CAT_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'person_categories.json'
CHAPTER_DIR = _ROOT / 'chapter_md'
OUTPUT_DIR = _ROOT / 'doc' / 'entities' / '人名反思'

CONTEXT_WINDOW = 40


def extract_context(chap_content, canonical, max_snippets=3):
    """在 chapter_md 文件中查找 〖@canonical〗 的上下文。"""
    snippets = []
    # 允许内联消歧 〖@X|canonical〗 或纯 〖@canonical〗
    patterns = [
        re.escape(f'〖@{canonical}〗'),
        re.escape(f'|{canonical}〗'),
    ]
    for pat in patterns:
        for m in re.finditer(pat, chap_content):
            start = max(0, m.start() - CONTEXT_WINDOW)
            end = min(len(chap_content), m.end() + CONTEXT_WINDOW)
            snippet = chap_content[start:end].replace('\n', ' ')
            snippets.append(snippet)
            if len(snippets) >= max_snippets:
                return snippets
    return snippets


def main():
    round_tag = sys.argv[1] if len(sys.argv) > 1 else '待反思'

    with open(INDEX_JSON, encoding='utf-8') as f:
        index = json.load(f)
    persons = index['person']

    with open(CAT_JSON, encoding='utf-8') as f:
        categories = json.load(f)

    # 未分类 = 不在 categories 中的
    blank = {name: info for name, info in persons.items() if name not in categories}
    # 按引用数降序
    blank_sorted = sorted(blank.items(), key=lambda x: -x[1].get('count', 0))

    # 预加载常用章节内容
    chap_content_cache = {}

    lines = [
        f'# 人名未分类 {round_tag} 上下文',
        '',
        f'共 **{len(blank_sorted)}** 条未分类人名，按引用数降序列出前 200。',
        '',
        '| # | 人名 | 引用数 | 首次出现章节 | 上下文（前 3 次出现，前后 40 字）|',
        '|---|------|-------|------------|----------|',
    ]

    for i, (canonical, info) in enumerate(blank_sorted[:200], 1):
        refs = info.get('refs', [])
        count = info.get('count', 0)
        first_chap = refs[0][0] if refs else '-'
        snippets = []
        # 取该人名第一次出现的章节来抓上下文
        seen_chaps = set()
        for ref in refs:
            chap = ref[0]
            if chap in seen_chaps:
                continue
            seen_chaps.add(chap)
            if chap not in chap_content_cache:
                fpath = CHAPTER_DIR / f'{chap}.tagged.md'
                if fpath.exists():
                    chap_content_cache[chap] = fpath.read_text(encoding='utf-8')
                else:
                    chap_content_cache[chap] = ''
            content = chap_content_cache[chap]
            snips = extract_context(content, canonical, max_snippets=1)
            for s in snips:
                snippets.append(f'[{chap[:3]}] {s}')
            if len(snippets) >= 3:
                break

        snippet_str = '<br>'.join(snippets[:3]).replace('|', '\\|') if snippets else ''
        lines.append(f'| {i} | {canonical} | {count} | {first_chap} | {snippet_str} |')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f'{round_tag}_上下文.md'
    out_file.write_text('\n'.join(lines), encoding='utf-8')

    print(f'未分类: {len(blank_sorted)} 条', file=sys.stderr)
    print(f'写入 {out_file.relative_to(_ROOT)}', file=sys.stderr)


if __name__ == '__main__':
    main()
