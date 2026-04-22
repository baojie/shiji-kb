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


def extract_events(chapter_slug, person_names):
    """从事件索引里抽该人物相关的事件"""
    f = EVENTS_DIR / f'{chapter_slug}_事件索引.md'
    if not f.exists():
        return []
    text = f.read_text(encoding='utf-8')
    events = []
    for line in text.splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        ev_id, name, kind, when, where, people = (m.group(i) for i in range(1, 7))
        # 检查 people 列含任一 person_name
        for pn in person_names:
            if pn and pn in people:
                events.append({
                    'id': ev_id, 'name': name.strip(),
                    'time': when.strip(), 'where': where.strip(),
                })
                break
    return events


def clean_tag(s):
    """去掉 〖@xxx〗 标注符号, 只留 inner."""
    return re.sub(r'〖[^〗]*?(?:\|([^〗]+))?〗', lambda m: m.group(1) or
                  re.sub(r'^[^|]+?', '', m.group(0).strip('〖〗')), s)


def build_timeline_section(events, max_n=8):
    events = events[:max_n]
    lines = ['## 生平大事 (自 kg 事件索引)', '']
    for e in events:
        # 清理标注
        where = re.sub(r'〖[^〗]+〗', '', e['where']).strip() or '—'
        time = re.sub(r'\[(.+?)\]', r'\1', e['time']).strip()
        lines.append(f"- {time} · {e['name']}（{where}）  [{e['id']}]")
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
    person_names = [slug] + aliases

    # 找 top chapter
    semantic = json.loads(SEMANTIC.read_text(encoding='utf-8'))
    e = semantic['entities'].get(slug)
    if not e or not e.get('chapters'):
        return False, 'no chapter data'
    top_chapter = e['chapters'][0]['chapter']

    events = extract_events(top_chapter, person_names)
    if not events:
        return False, f'no events in {top_chapter}'

    section = build_timeline_section(events)

    # 插到最后 (在 `*生卒依据*` 之前, 或末尾)
    if '*生卒依据*' in text:
        text = text.replace('*生卒依据*', section + '\n*生卒依据*', 1)
    else:
        text = text.rstrip() + '\n\n' + section

    page.write_text(text, encoding='utf-8')
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
