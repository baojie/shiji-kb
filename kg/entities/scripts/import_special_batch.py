#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入专项索引到 wiki（直接写文件版）：
  - 太史公曰：docs/special/taishigongyue.json  → 126 页
  - 韵文：    data/yunwen.json                  → 139 页（已存在则跳过）
  - 散文：    docs/special/sanwen.json          → 130 页（已存在则跳过）

用法:
    python3 kg/entities/scripts/import_special_batch.py [--dry-run] [--force] [--only taishigongyue|yunwen|sanwen]
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT      = Path('/home/baojie/work/knowledge/shiji-kb')
PAGES_DIR = ROOT / 'wiki' / 'public' / 'pages'

TAISHIGONGYUE_JSON = ROOT / 'docs' / 'special' / 'taishigongyue.json'
YUNWEN_JSON        = ROOT / 'data' / 'yunwen.json'
SANWEN_JSON        = ROOT / 'docs' / 'special' / 'sanwen.json'

PARA_NUM_RE = re.compile(r'^\[(\d+(?:\.\d+)*)\]\s*', re.MULTILINE)


def strip_markup(text: str) -> str:
    text = re.sub(r'〖[^|〗]+\|([^〗]+)〗', r'\1', text)
    text = re.sub(r'〖.([^〖〗]+)〗', r'\1', text)
    text = re.sub(r'⟦.([^⟦⟧]+)⟧', r'\1', text)
    text = re.sub(r'〘[^〙]*?([^〙〘※#~%@=◆;^&*]{1,})〙', r'\1', text)
    text = re.sub(r'〘.([^〙]+)〙', r'\1', text)
    text = PARA_NUM_RE.sub('', text)
    text = re.sub(r'[〖〗⟦⟧〘〙]', '', text)
    text = text.replace('“', '').replace('”', '').strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def pn_from_content(content: str, chapter_num: str) -> str | None:
    m = re.match(r'^\[(\d+(?:\.\d+)?)\]', content.strip())
    if m:
        return f'（{chapter_num}-{m.group(1)}）'
    return None


def make_slug_with_seq(title: str, seq: int, total: int) -> str:
    if total <= 1:
        return title
    suffixes = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    suffix = suffixes[seq - 1] if seq - 1 < len(suffixes) else str(seq)
    return f'{title}（{suffix}）'


# ──────────────────────────────────────────────────────────────────────────────
# 太史公曰
# ──────────────────────────────────────────────────────────────────────────────

def build_taishigongyue_page(d: dict) -> tuple[str, str]:
    """返回 (slug, content)"""
    cnum   = d['chapter_num']
    ctitle = d['chapter_title']
    raw    = d['content']
    slug   = f'太史公曰·{ctitle}'

    pn = pn_from_content(raw, cnum)
    clean = strip_markup(raw)

    pn_field = f'\npn: "{pn}"' if pn else ''
    source_ref = f'《史记·{ctitle}》（{cnum}）'
    if pn:
        source_ref += f'，{pn}'

    chapter_slug = f'{cnum}_{ctitle}'

    content = f"""---
id: {slug}
type: taishigongyue
label: {slug}
aliases: []
tags: ["太史公曰", "史论", "史记", "{ctitle}"]
chapter_no: "{cnum}"
sources: ["{ctitle}"]{pn_field}
featured: false
---

# {slug}

出自{source_ref}。

## 原文

{clean}

## 相关章节

[[{chapter_slug}|{ctitle}]]
"""
    return slug, content


# ──────────────────────────────────────────────────────────────────────────────
# 韵文
# ──────────────────────────────────────────────────────────────────────────────

YUNWEN_TYPE_TAGS = {
    '赞':   ['赞', '韵文', '史记'],
    '诗歌': ['诗歌', '韵文', '史记'],
    '赋':   ['赋', '韵文', '史记'],
}


def build_yunwen_page(slug: str, d: dict) -> str:
    cnum   = d['chapter_num']
    ctitle = d['chapter_title']
    etype  = d['type']
    title  = d['title']
    raw    = d['content']

    pn = pn_from_content(raw, cnum)
    clean = strip_markup(raw)

    tags = YUNWEN_TYPE_TAGS.get(etype, ['韵文', '史记'])
    tags_yaml = json.dumps(tags, ensure_ascii=False)
    aliases_yaml = json.dumps([title], ensure_ascii=False) if slug != title else '[]'

    pn_field = f'\npn: "{pn}"' if pn else ''
    source_ref = f'《史记·{ctitle}》（{cnum}）'
    if pn:
        source_ref += f'，{pn}'

    chapter_slug = f'{cnum}_{ctitle}'

    # Format as verse (add > quoteblock per line)
    verse_lines = []
    for line in clean.split('\n'):
        line = line.strip()
        if line:
            verse_lines.append(f'> {line}')
        else:
            verse_lines.append('>')
    # clean trailing empty quote
    while verse_lines and verse_lines[-1] == '>':
        verse_lines.pop()
    verse = '\n'.join(verse_lines)

    return f"""---
id: {slug}
type: sanwen
label: {slug}
aliases: {aliases_yaml}
tags: {tags_yaml}
chapter_no: "{cnum}"
essay_type: {etype}
sources: ["{ctitle}"]{pn_field}
featured: false
---

# {slug}

出自{source_ref}。

## 原文

{verse}

## 相关章节

[[{chapter_slug}|{ctitle}]]
"""


# ──────────────────────────────────────────────────────────────────────────────
# 散文
# ──────────────────────────────────────────────────────────────────────────────

SANWEN_TYPE_TAGS = {
    '议论': ['议论', '散文', '史记'],
    '奏议': ['奏议', '散文', '史记'],
    '诏令': ['诏令', '散文', '史记'],
    '书信': ['书信', '散文', '史记'],
    '对话': ['对话', '散文', '史记'],
    '杂文': ['杂文', '散文', '史记'],
}


def build_sanwen_page(slug: str, d: dict) -> str:
    cnum   = d['chapter_num']
    ctitle = d['chapter_title']
    etype  = d['type']
    title  = d['title']
    raw    = d['content']
    intro  = d.get('intro', '')

    pn = pn_from_content(raw, cnum)
    clean = strip_markup(raw)

    tags = SANWEN_TYPE_TAGS.get(etype, ['散文', '史记'])
    tags_yaml = json.dumps(tags, ensure_ascii=False)
    aliases_yaml = json.dumps([title], ensure_ascii=False) if slug != title else '[]'

    pn_field = f'\npn: "{pn}"' if pn else ''
    source_ref = f'《史记·{ctitle}》（{cnum}）'
    if pn:
        source_ref += f'，{pn}'

    desc_line = ''
    if intro:
        clean_intro = strip_markup(intro)
        desc_line = f'\ndescription: {json.dumps(clean_intro[:120], ensure_ascii=False)}'

    chapter_slug = f'{cnum}_{ctitle}'
    intro_block = f'\n{strip_markup(intro)}\n' if intro else ''

    return f"""---
id: {slug}
type: sanwen
label: {slug}
aliases: {aliases_yaml}
tags: {tags_yaml}
chapter_no: "{cnum}"
essay_type: {etype}
sources: ["{ctitle}"]{pn_field}{desc_line}
featured: false
---

# {slug}

出自{source_ref}。{intro_block}

## 原文

{clean}

## 相关章节

[[{chapter_slug}|{ctitle}]]
"""


# ──────────────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────────────

def run_taishigongyue(dry_run: bool, force: bool) -> tuple[int, int]:
    with open(TAISHIGONGYUE_JSON, encoding='utf-8') as f:
        data = json.load(f)
    created = skipped = 0
    for d in data:
        slug, content = build_taishigongyue_page(d)
        page_path = PAGES_DIR / f'{slug}.md'
        if page_path.exists() and not force:
            skipped += 1
            continue
        if dry_run:
            print(f'  [+] {slug}')
            created += 1
        else:
            page_path.write_text(content, encoding='utf-8')
            created += 1
    return created, skipped


def run_yunwen(dry_run: bool, force: bool) -> tuple[int, int]:
    with open(YUNWEN_JSON, encoding='utf-8') as f:
        data = json.load(f)
    title_counts = Counter(d['title'] for d in data)
    title_seq: dict[str, int] = {}
    created = skipped = 0
    for d in data:
        title = d['title']
        title_seq[title] = title_seq.get(title, 0) + 1
        seq = title_seq[title]
        slug = make_slug_with_seq(title, seq, title_counts[title])
        page_path = PAGES_DIR / f'{slug}.md'
        if page_path.exists() and not force:
            skipped += 1
            continue
        content = build_yunwen_page(slug, d)
        if dry_run:
            print(f'  [+] {slug}')
            created += 1
        else:
            page_path.write_text(content, encoding='utf-8')
            created += 1
    return created, skipped


def run_sanwen(dry_run: bool, force: bool) -> tuple[int, int]:
    with open(SANWEN_JSON, encoding='utf-8') as f:
        data = json.load(f)
    title_counts = Counter(d['title'] for d in data)
    title_seq: dict[str, int] = {}
    created = skipped = 0
    for d in data:
        title = d['title']
        title_seq[title] = title_seq.get(title, 0) + 1
        seq = title_seq[title]
        slug = make_slug_with_seq(title, seq, title_counts[title])
        page_path = PAGES_DIR / f'{slug}.md'
        if page_path.exists() and not force:
            skipped += 1
            continue
        content = build_sanwen_page(slug, d)
        if dry_run:
            print(f'  [+] {slug}')
            created += 1
        else:
            page_path.write_text(content, encoding='utf-8')
            created += 1
    return created, skipped


def main():
    dry_run = '--dry-run' in sys.argv
    force   = '--force' in sys.argv
    only    = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--only=')), None)
    if not only:
        for i, a in enumerate(sys.argv[1:]):
            if a == '--only' and i + 1 < len(sys.argv) - 1:
                only = sys.argv[i + 2]

    tasks = []
    if not only or only == 'taishigongyue':
        tasks.append(('太史公曰', run_taishigongyue))
    if not only or only == 'yunwen':
        tasks.append(('韵文', run_yunwen))
    if not only or only == 'sanwen':
        tasks.append(('散文', run_sanwen))

    total_created = total_skipped = 0
    for label, fn in tasks:
        print(f'处理 [{label}]…')
        c, s = fn(dry_run, force)
        print(f'  完成: 新建 {c}，跳过 {s}')
        total_created += c
        total_skipped += s

    print(f'\n全部完成: 新建 {total_created}，跳过 {total_skipped}')
    if not dry_run:
        print('\n下一步: python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json')


if __name__ == '__main__':
    main()
