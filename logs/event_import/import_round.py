#!/usr/bin/env python3
"""
事件导入执行器。每次调用处理队列中优先级最高的一批事件。
用法：python3 logs/event_import/import_round.py [--batch N] [--priority P0|P1|P3]
"""
import json, re, subprocess, sys, argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path('.').resolve()
PAGES = ROOT / 'wiki/public/pages'
LOG = ROOT / 'logs/event_import'

def clean_markup(s):
    if not s: return s
    s = re.sub(r'〖[^〗]*?([^〗|]{1,30})\|[^〗]*〗', r'\1', s)
    s = re.sub(r'〖[=@&;%*•◆+!~^_:#?.\/\[\]{]([^〗]*)〗', r'\1', s)
    s = re.sub(r'〖([^〗]*)〗', r'\1', s)
    return s.strip()

def record_rev(slug, summary):
    subprocess.run([sys.executable,
        str(ROOT / 'wiki/scripts/butler/record_revision.py'),
        slug, '--summary', summary, '--author', 'butler'],
        capture_output=True)

def get_event_detail(event_id):
    """Load full event data from kg/events/data MD file."""
    chap = event_id.split('-')[0]
    import glob
    files = glob.glob(str(ROOT / f'kg/events/data/{chap}_*_事件索引.md'))
    if not files:
        return None
    text = Path(files[0]).read_text('utf-8')
    if '## 详细事件记录' not in text:
        return None
    detail = text.split('## 详细事件记录', 1)[1]
    # find the specific event block
    m = re.search(r'### ' + re.escape(event_id) + r'\s+(.*?)(?=\n### |\Z)', detail, re.DOTALL)
    if not m:
        return None
    block = m.group(0)
    ev = {'event_id': event_id}
    for field, key in [
        ('事件类型','type'),('时间','time'),('地点','location'),
        ('主要人物','persons'),('事件描述','description'),
        ('原文引用','source_text'),('段落位置','paragraph'),
    ]:
        m2 = re.search(r'\*\*' + field + r'\*\*[：:]\s*(.*)', block)
        if m2:
            val = m2.group(1).strip().strip('"')
            ev[key] = clean_markup(val) if key in ('persons','location') else val
    return ev

def build_page_content(item, events_detail):
    gname = item['group_name']
    cross = item['cross_chapter']

    # Gather all descriptions, times, persons
    times = list({e.get('time','') for e in events_detail if e.get('time') and e.get('time') != '-'})
    persons_all = set()
    for e in events_detail:
        if e.get('persons') and e.get('persons') != '-':
            for p in re.split(r'[、，,]', e['persons']):
                p = p.strip()
                if p:
                    persons_all.add(p)
    chapters = list({e.get('chapter_title','') for e in events_detail if e.get('chapter_title')})

    # Use first description as main description
    main_desc = events_detail[0].get('description','') if events_detail else ''

    # Tags
    tags = ['史记', '事件'] + chapters[:3]
    tags_yaml = '[' + ', '.join(tags) + ']'

    # Date
    time_str = times[0] if times else ''

    # Build body
    lines = [
        f'---',
        f'id: "{gname}"',
        f'type: event',
        f'title: {gname}',
        f'description: {main_desc[:100]}',
        f'tags: {tags_yaml}',
        f'sources: [{", ".join(chapters)}]',
        f'event_ids: [{", ".join(e["event_id"] for e in events_detail)}]',
    ]
    if time_str:
        lines.append(f'date: "{time_str}"')
    lines += ['---', '', f'# {gname}', '']

    if main_desc:
        lines += [f'> {main_desc}', '']

    if persons_all:
        lines += [f'**主要人物**：' + '、'.join(sorted(persons_all)[:8]), '']

    if cross and len(events_detail) > 1:
        lines += ['## 各章节记载', '']
        for ev in events_detail:
            chap = ev.get('chapter_title', ev['event_id'])
            lines += [f'### {chap}', '']
            if ev.get('description'):
                lines += [ev['description'], '']
            if ev.get('source_text') and ev['source_text'] not in ('-', ''):
                orig = clean_markup(ev['source_text'])
                lines += ['**原文**：', '', f'> {orig}', '']
    else:
        ev = events_detail[0]
        if ev.get('description'):
            lines += ['## 事件经过', '', ev['description'], '']
        if ev.get('source_text') and ev['source_text'] not in ('-', ''):
            orig = clean_markup(ev['source_text'])
            lines += ['## 原文', '', f'> {orig}', '']

    return '\n'.join(lines) + '\n'

def merge_event_into_page(existing: str, events_detail: list, gname: str) -> str:
    """Add event_ids and any missing sections to existing page."""
    # Add event_ids to frontmatter if not present
    if 'event_ids:' not in existing:
        eids = ', '.join(e['event_id'] for e in events_detail)
        existing = re.sub(r'^(sources:.*)', r'\1\nevent_ids: [' + eids + ']',
                          existing, count=1, flags=re.MULTILINE)

    # Add 各章节记载 section if cross-chapter and not present
    if len(events_detail) > 1 and '## 各章节记载' not in existing:
        section_lines = ['\n\n## 各章节记载（kg/events 导入）\n']
        for ev in events_detail:
            chap = ev.get('chapter_title', ev['event_id'])
            section_lines.append(f'### {chap} ({ev["event_id"]})\n')
            if ev.get('description'):
                section_lines.append(ev['description'] + '\n')
        existing = existing.rstrip() + '\n' + '\n'.join(section_lines)

    return existing

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', type=int, default=50)
    ap.add_argument('--priority', default='P0')
    args = ap.parse_args()

    queue = json.loads((LOG / 'queue.json').read_text('utf-8'))
    items = queue['items']

    # Pick pending items of the right priority
    to_process = [it for it in items
                  if it['status'] == 'pending' and it['priority'] == args.priority]
    to_process = to_process[:args.batch]

    if not to_process:
        print(f'队列中没有待处理的 {args.priority} 项目')
        return

    print(f'本轮处理 {len(to_process)} 个 {args.priority} 事件组...')
    created = merged = 0

    for item in to_process:
        gname = item['group_name']
        eids = item['event_ids']

        # Load full event details
        events_detail = []
        for eid in eids:
            ev = get_event_detail(eid)
            if ev:
                # attach chapter info
                chap = eid.split('-')[0]
                chaps = json.loads((ROOT / 'logs/event_import/events_parsed.json').read_text('utf-8'))
                ev['chapter_title'] = chaps['chapters'].get(chap, chap)
                events_detail.append(ev)

        if not events_detail:
            item['status'] = 'skip_no_data'
            continue

        page_path = PAGES / f'{gname}.md'

        if page_path.exists():
            existing = page_path.read_text('utf-8')
            # If this is a redirect, follow it to the canonical page
            redirect_m = re.search(r'^target:\s*(.+)', existing, re.MULTILINE)
            if redirect_m:
                canonical = redirect_m.group(1).strip()
                canonical_path = PAGES / f'{canonical}.md'
                print(f'  REDIRECT: {gname} → {canonical}')
                if canonical_path.exists():
                    existing = canonical_path.read_text('utf-8')
                    new_content = merge_event_into_page(existing, events_detail, canonical)
                    if new_content != existing:
                        canonical_path.write_text(new_content, 'utf-8')
                        record_rev(canonical, f'butler/import-event: {canonical} 融入 kg/events 数据 via {gname} ({", ".join(eids)})')
                        print(f'  MERGE→canonical: {canonical}')
                        merged += 1
                    else:
                        print(f'  SKIP (no change): {canonical}')
                else:
                    print(f'  WARN: redirect target {canonical} not found')
                item['status'] = 'done_merged'
                continue
            # Normal merge into existing page (append, never replace)
            new_content = merge_event_into_page(existing, events_detail, gname)
            if new_content != existing:
                page_path.write_text(new_content, 'utf-8')
                record_rev(gname, f'butler/import-event: {gname} 融入 kg/events 数据 ({", ".join(eids)})')
                print(f'  MERGE: {gname}')
                merged += 1
            else:
                print(f'  SKIP (no change): {gname}')
            item['status'] = 'done_merged'
        else:
            # CREATE new page
            content = build_page_content(item, events_detail)
            page_path.write_text(content, 'utf-8')
            record_rev(gname, f'butler/import-event: {gname} 新建 ({", ".join(eids)})')
            print(f'  CREATE: {gname}')
            created += 1
            item['status'] = 'done_created'

    # Save updated queue
    queue['items'] = items
    (LOG / 'queue.json').write_text(json.dumps(queue, ensure_ascii=False, indent=2), 'utf-8')

    # Rebuild queue.md status summary
    done = sum(1 for it in items if it['status'].startswith('done'))
    pending = sum(1 for it in items if it['status'] == 'pending')
    print(f'\n本轮: 新建={created}, 融合={merged}')
    print(f'队列: done={done}, pending={pending}')

if __name__ == '__main__':
    main()
