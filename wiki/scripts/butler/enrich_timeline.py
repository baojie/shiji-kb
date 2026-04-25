#!/usr/bin/env python3
"""
enrich_timeline.py — 给一个 wiki 人物页添加"生平大事"区.

策略:
    1. 取 wiki 页的 frontmatter canonical + aliases
    2. 找该人物 top chapter (from semantic.json chapters[0])
    3. 扫 kg/events/data/<chapter>_事件索引.md 表格
    4. 过滤"主要人物"含 canonical 或 alias 的行, 取前 8 行
    5. 若 wiki 页无"生平大事"区, 插入

动作名: add-event-timeline (W2 有, 这是执行实现)
用法:
    python3 wiki/scripts/butler/enrich_timeline.py <slug>
    python3 wiki/scripts/butler/enrich_timeline.py --top 5  # top 5 refs 批量
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES_DIR = ROOT / 'wiki/public/pages'
EVENTS_DIR = ROOT / 'kg/events/data'
SEMANTIC = ROOT / 'wiki/data/semantic.json'

FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
ROW_RE = re.compile(r'^\|\s*(\S+-\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|')


def parse_aliases(md_text):
    m = FRONTMATTER_RE.match(md_text)
    if not m:
        return []
    for line in m.group(1).splitlines():
        if line.startswith('aliases:'):
            val = line[8:].strip()
            if val.startswith('['):
                return [x.strip() for x in val[1:-1].split(',') if x.strip()]
    return []


def extract_events(chapter_slug, canonical, aliases):
    """从事件索引里抽该人物相关的事件.

    user-req-9 (2026-04-22): 严格匹配 〖@<name>〗 / 〖@<alias>|<canonical>〗,
    不再裸串匹配. 避免 "桓" 匹到"三桓"、"齐桓公" 这类误伤.
    """
    f = EVENTS_DIR / f'{chapter_slug}_事件索引.md'
    if not f.exists():
        return []
    text = f.read_text(encoding='utf-8')

    # 构建严格正则: 匹配 〖@N〗 其中 N == canonical,
    # 或 〖@X|canonical〗 其中消歧后 canonical 等于本人
    # 或 〖@alias〗 其中 alias 是 **长度 >= 2** 的别名 (单字太宽)
    patterns = []
    # canonical 完整名
    patterns.append(r'〖@' + re.escape(canonical) + r'(?:\|[^〗]+)?〗')
    # 消歧到本人: 〖@X|canonical〗
    patterns.append(r'〖@[^〗]+\|' + re.escape(canonical) + r'〗')
    # 别名: 只用 >= 2 字, 防止 "桓" 这种单字误匹
    for a in aliases:
        if len(a) >= 2:
            patterns.append(r'〖@' + re.escape(a) + r'(?:\|[^〗]+)?〗')
    combined = re.compile('|'.join(patterns))

    events = []
    for line in text.splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        ev_id, name, kind, when, where, people = (m.group(i) for i in range(1, 7))
        if combined.search(people):
            events.append({
                'id': ev_id, 'name': name.strip(),
                'time': when.strip(), 'where': where.strip(),
            })
    return events


def strip_annotations(s):
    """去 〖TYPE value〗 / 〖TYPE value|canonical〗 / ⟦TYPE verb⟧, 保留 value.
    TYPE 是单字符标记 (%, @, ;, =, ◆, ◇, ◈, ◉, ○, #, &, ^, [, •, $, _, !, {, +, ~, :, ?)."""
    def repl_noun(m):
        c = m.group(1)
        before_pipe = c.split('|', 1)[0]
        # 首字符 TYPE marker, 其余为 value
        return before_pipe[1:] if len(before_pipe) > 1 else before_pipe
    s = re.sub(r'〖([^〗]+)〗', repl_noun, s)
    s = re.sub(r'⟦([^⟧]+)⟧', repl_noun, s)
    return s


def clean_field(s):
    """清标注 + 去括号里仅剩分隔符的噪音."""
    s = strip_annotations(s)
    # 去方括号 [公元前...]
    s = re.sub(r'\[(.+?)\]', r'\1', s)
    # 归并多余空白
    s = re.sub(r'\s+', ' ', s).strip()
    # 空括号/仅分隔 ( 、 ) → 空
    if s in {'-', '—', '、', ',', '。', ''}:
        return ''
    return s


def build_timeline_section(events, max_n=8):
    events = events[:max_n]
    lines = ['## 生平大事 (自 kg 事件索引)', '']
    for e in events:
        t = clean_field(e['time'])
        w = clean_field(e['where'])
        name = clean_field(e['name'])
        parts = [t] if t else []
        parts.append(name)
        line = ' · '.join(parts)
        if w:
            line += f'（{w}）'
        line += f'  [`{e["id"]}`]'
        lines.append(f'- {line}')
    lines.append('')
    return '\n'.join(lines)


def enrich_one(slug):
    page = PAGES_DIR / f'{slug}.md'
    if not page.exists():
        return False, 'page not found'
    text = page.read_text(encoding='utf-8')
    if '## 生平大事' in text:
        return False, 'already has timeline'

    aliases = parse_aliases(text)

    # 找 top chapter
    semantic = json.loads(SEMANTIC.read_text(encoding='utf-8'))
    e = semantic['entities'].get(slug)
    if not e or not e.get('chapters'):
        return False, 'no chapter data'
    top_chapter = e['chapters'][0]['chapter']

    events = extract_events(top_chapter, slug, aliases)
    if not events:
        return False, f'no events in {top_chapter}'

    section = build_timeline_section(events)

    # 插到最后 (在 `*生卒依据*` 之前, 或末尾)
    if '*生卒依据*' in text:
        text = text.replace('*生卒依据*', section + '\n*生卒依据*', 1)
    else:
        text = text.rstrip() + '\n\n' + section

    page.write_text(text, encoding='utf-8')

    subprocess.run(
        [sys.executable,
         str(ROOT / 'wiki' / 'scripts' / 'butler' / 'record_revision.py'),
         slug,
         '--summary', f'add-event-timeline: {len(events)} events from {top_chapter}',
         '--author', 'butler'],
        capture_output=True, text=True
    )

    return True, f'added {len(events)} events from {top_chapter}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', nargs='?')
    ap.add_argument('--top', type=int, help='top N by refs 批量')
    args = ap.parse_args()

    slugs = []
    if args.top:
        semantic = json.loads(SEMANTIC.read_text(encoding='utf-8'))
        existing = {p.stem for p in PAGES_DIR.glob('*.md')}
        ranked = sorted(
            (e for e in semantic['entities'].values() if e['id'] in existing),
            key=lambda x: -x.get('total_refs', 0)
        )
        slugs = [e['id'] for e in ranked[:args.top]]
    elif args.slug:
        slugs = [args.slug]
    else:
        ap.error('需要 slug 或 --top N')

    for s in slugs:
        ok, msg = enrich_one(s)
        flag = '✓' if ok else '—'
        print(f'{flag} {s}: {msg}')


if __name__ == '__main__':
    main()
