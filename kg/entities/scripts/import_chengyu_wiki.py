#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 docs/special/data/chengyu.json 的成语数据批量导入 wiki。

- 无页面成语: 新建专项成语页面
- 已有页面成语: 仅追加 ## 史记原文 节（append-only）
- 多章节出现的成语: 合并成一个页面，多处引用都列出

用法:
    python3 kg/entities/scripts/import_chengyu_wiki.py [--dry-run] [成语词条]
"""

import json
import re
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT      = Path('/home/baojie/work/knowledge/shiji-kb')
DATA_JSON = ROOT / 'docs' / 'special' / 'data' / 'chengyu.json'
PAGES_DIR = ROOT / 'wiki' / 'public' / 'pages'

# ── 标注剥离 ─────────────────────────────────────────────────────────────────
PARA_NUM_RE = re.compile(r'^\[(\d+(?:\.\d+)*)\]\s*')
ROW_ANC_RE  = re.compile(r'^\[r(\d+)\]\s*')

def strip_tags(text: str) -> str:
    """去除〖〗⟦⟧〘〙等标注符号，还原纯文本"""
    text = re.sub(r'〖[^〗|]+\|([^〗]+)〗', r'\1', text)
    text = re.sub(r'〖.([^〖〗]+)〗', r'\1', text)
    text = re.sub(r'⟦.([^⟦⟧]+)⟧', r'\1', text)
    text = re.sub(r'〘[※#~%@=◆;^&]?([^〙]+)〙', r'\1', text)
    text = PARA_NUM_RE.sub('', text)
    text = ROW_ANC_RE.sub('', text)
    # Remove markdown headers from context
    text = re.sub(r'^#{1,6}\s+.*$', '', text, flags=re.MULTILINE)
    # Remove list items markers
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r'\n+', ' ', text).strip()
    return text


def chapter_link(chapter_num: str, chapter_title: str) -> str:
    return f'[[{chapter_num}_{chapter_title}|{chapter_title}]]'


def build_shiji_section(chengyu: str, entries: list) -> str:
    """构建 ## 史记原文 节"""
    lines = ['## 史记原文', '']

    for entry in entries:
        cnum = entry['chapter_num']
        ctitle = entry['chapter_title']
        pn = entry.get('paragraph', '')
        original = entry.get('original', '')
        shiji_form = entry.get('shiji_form', '')
        context_raw = entry.get('context', '')

        # Clean context
        context = strip_tags(context_raw) if context_raw else ''
        # Truncate if too long
        if len(context) > 200:
            # Find the anchor position
            anchor = shiji_form or original
            idx = context.find(anchor)
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(context), idx + len(anchor) + 100)
                context = ('…' if start > 0 else '') + context[start:end] + ('…' if end < len(context) else '')
            else:
                context = context[:200] + '…'

        # Chapter link with pn-citation format （NNN-pn）
        chap_ref = f'[[{cnum}_{ctitle}|{ctitle}]]'
        pn_ref = f'（{cnum}-{pn}）' if pn else ''

        lines.append(f'出自 {chap_ref}{" " + pn_ref if pn_ref else ""}：')
        lines.append('')
        if original:
            orig_display = shiji_form if shiji_form else original
            lines.append(f'> **原文出处**：{orig_display}')
        if context:
            # Highlight the chengyu or original phrase in context
            anchor = shiji_form if shiji_form else original
            if anchor and anchor in context:
                context_hl = context.replace(anchor, f'**{anchor}**', 1)
            else:
                context_hl = context
            lines.append(f'> **上下文**：{context_hl}')
        lines.append('')

    return '\n'.join(lines)


def new_page_content(chengyu: str, entries: list) -> str:
    """构建新成语页面内容"""
    # Use first entry as primary
    primary = entries[0]
    meaning = primary.get('meaning', '')
    chapter_titles = list(dict.fromkeys(e['chapter_title'] for e in entries))
    chapter_nums   = list(dict.fromkeys(e['chapter_num'] for e in entries))

    tags = ['史记', '成语', '典故'] + chapter_titles[:2]
    tags_yaml = json.dumps(tags, ensure_ascii=False)
    sources_yaml = json.dumps(chapter_titles, ensure_ascii=False)

    # Build description
    desc = meaning if meaning else f'出自《史记·{chapter_titles[0]}》的成语典故'

    front = f"""---
id: {chengyu}
type: chengyu
label: {chengyu}
aliases: []
tags: {tags_yaml}
sources: {sources_yaml}
description: {json.dumps(desc, ensure_ascii=False)}
featured: false
---"""

    shiji_sec = build_shiji_section(chengyu, entries)

    body = f"""# {chengyu}

**释义**：{meaning if meaning else '（待补充）'}

出自《史记》，见于{'、'.join(f'[[{n}_{t}|{t}]]' for n, t in zip(chapter_nums, chapter_titles))}。

{shiji_sec}
## 相关页面

"""
    return front + '\n\n' + body


def strip_shiji_section(content: str, section_title: str) -> str:
    """删除已有的指定 ## 节（用于 --force 覆盖）"""
    if section_title not in content:
        return content
    start = content.find(section_title)
    rest = content[start + len(section_title):]
    next_h2 = rest.find('\n## ')
    if next_h2 >= 0:
        return content[:start] + content[start + len(section_title) + next_h2 + 1:]
    return content[:start].rstrip('\n') + '\n'


def update_page_content(content: str, chengyu: str, entries: list,
                        force: bool = False) -> str:
    """在已有页面末尾追加史记原文节（append-only，--force 时覆盖）"""
    if '## 史记原文' in content:
        if not force:
            return content
        content = strip_shiji_section(content, '## 史记原文')
    section = build_shiji_section(chengyu, entries)
    anchor = '## 相关页面'
    if anchor in content:
        idx = content.find(anchor)
        return content[:idx] + section + '\n' + content[idx:]
    return content.rstrip('\n') + '\n\n' + section + '\n'


def main():
    dry_run = '--dry-run' in sys.argv
    force   = '--force' in sys.argv
    target  = next((a for a in sys.argv[1:] if not a.startswith('--')), None)

    print('1. 加载成语数据…')
    with open(DATA_JSON, encoding='utf-8') as f:
        raw = json.load(f)

    # Group by chengyu
    by_cy = defaultdict(list)
    for entry in raw:
        by_cy[entry['chengyu']].append(entry)

    print(f'   {len(by_cy)} 个成语，{len(raw)} 条记录')

    entries_to_process = {target: by_cy[target]} if target and target in by_cy else dict(by_cy)

    created = updated = skipped = 0

    for chengyu, entries in entries_to_process.items():
        # 含斜杠的复合成语（如"浑沌/穷奇/梼杌/饕餮"）用第一个词作 slug
        slug = chengyu.split('/')[0] if '/' in chengyu else chengyu
        page_path = PAGES_DIR / f'{slug}.md'

        if not page_path.exists():
            content = new_page_content(chengyu, entries)
            if dry_run:
                print(f'\n=== 新建: {chengyu} ===')
                print(content[:500])
            else:
                page_path.write_text(content, encoding='utf-8')
                print(f'[+] {chengyu} ({len(entries)}处)')
                created += 1
        else:
            old = page_path.read_text(encoding='utf-8')
            new = update_page_content(old, chengyu, entries, force=force)
            if new.strip() == old.strip():
                skipped += 1
                continue
            if dry_run:
                print(f'\n=== 更新: {chengyu} ===')
                idx = new.find('## 史记原文')
                print(new[idx:idx+400])
            else:
                page_path.write_text(new, encoding='utf-8')
                print(f'[✓] {chengyu}')
                updated += 1

    if not dry_run:
        print(f'\n完成: 新建 {created}，更新 {updated}，跳过 {skipped}')
        print('\n下一步: python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json')
    else:
        print(f'\n[dry-run] 完成预览')


if __name__ == '__main__':
    main()
