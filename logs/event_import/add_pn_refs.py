#!/usr/bin/env python3
"""
为所有含 event_ids 的 wiki 页面批量补全原始事件元数据：
  - frontmatter: paragraph_refs, event_type, location
  - 各章节记载 section headers 加 (event_id) 和 PN 链接
  - 多个事件时全部继承

用法：python3 logs/event_import/add_pn_refs.py [--dry-run] [--batch N]
"""
import json, re, subprocess, sys, argparse
from pathlib import Path

ROOT = Path('.').resolve()
PAGES = ROOT / 'wiki/public/pages'
EVENTS_JSON = ROOT / 'logs/event_import/events_parsed.json'


def record_rev(slug, summary):
    subprocess.run([sys.executable,
        str(ROOT / 'wiki/scripts/butler/record_revision.py'),
        slug, '--summary', summary, '--author', 'butler'],
        capture_output=True)


def pn_anchor(pn_str):
    """First PN anchor from '[165.2]-[167.1]' → '165.2', or 'r79' → 'r79'."""
    if not pn_str or pn_str in ('-', ''):
        return None
    m = re.match(r'\[([^\]]+)\]', pn_str)
    return m.group(1) if m else pn_str.strip('[]')


def build_paragraph_refs_yaml(event_ids, events_by_id):
    lines = []
    for eid in event_ids:
        ev = events_by_id.get(eid)
        if ev and ev.get('paragraph') and ev['paragraph'] not in ('-', ''):
            lines.append(f'  {eid}: "{ev["paragraph"]}"')
    return ('paragraph_refs:\n' + '\n'.join(lines) + '\n') if lines else ''


def enrich_frontmatter(content, event_ids, events_by_id):
    """Add paragraph_refs, event_type, location to frontmatter if missing."""
    changes = []

    all_types = [events_by_id[e]['type'] for e in event_ids
                 if e in events_by_id and events_by_id[e].get('type') not in (None, '-', '')]
    all_locs  = [events_by_id[e]['location'] for e in event_ids
                 if e in events_by_id and events_by_id[e].get('location') not in (None, '-', '')]

    insert_lines = ''

    if 'paragraph_refs:' not in content:
        pn_yaml = build_paragraph_refs_yaml(event_ids, events_by_id)
        if pn_yaml:
            insert_lines += pn_yaml
            changes.append('paragraph_refs')

    if 'event_type:' not in content and all_types:
        dominant = max(set(all_types), key=all_types.count)
        insert_lines += f'event_type: {dominant}\n'
        changes.append('event_type')

    if 'location:' not in content and all_locs:
        locs_unique = list(dict.fromkeys(all_locs))[:3]
        loc_val = '、'.join(locs_unique)
        insert_lines += f'location: "{loc_val}"\n'
        changes.append('location')

    if insert_lines:
        content = re.sub(r'^---\s*$', insert_lines + '---',
                         content, count=1, flags=re.MULTILINE)

    return content, changes


def enrich_section_headers(content, event_ids, events_by_id):
    """
    Update ### 章节名 and ### 章节名 (event_id) headers to include
    event_id, event_type, and PN link.
    """
    # Build mapping: chapter_title → events (for this page's event_ids)
    chap_to_events = {}
    for eid in event_ids:
        ev = events_by_id.get(eid)
        if ev:
            ct = ev.get('chapter_title', '')
            if ct not in chap_to_events:
                chap_to_events[ct] = []
            chap_to_events[ct].append(ev)

    changed = False
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        # Pattern A: ### 章节名 (event_id) [optional extra] — already has event_id
        mA = re.match(r'^### ([^(\n]+) \(([0-9]{3}-[0-9]{3,4})\)(.*)', line)
        # Pattern B: ### 章节名 — no event_id
        mB = re.match(r'^### ([^(\[P\n][^\n]*)$', line) if not mA else None

        if mA:
            chap_title = mA.group(1).strip()
            eid = mA.group(2).strip()
            rest = mA.group(3).strip()
            ev = events_by_id.get(eid)
            if ev and 'PN:' not in rest and 'pn-' not in rest:
                pn_str = ev.get('paragraph', '')
                anchor = pn_anchor(pn_str)
                chap_id = ev.get('chapter_id', '')
                etype = ev.get('type', '')
                etype_str = f' [{etype}]' if etype and etype != '-' else ''
                if anchor and chap_id:
                    pn_link = f'[PN:{pn_str}](../chapters/{chap_id}_{chap_title}.html#pn-{anchor})'
                elif pn_str and pn_str != '-':
                    pn_link = f'PN:{pn_str}'
                else:
                    pn_link = ''
                new_line = f'### {chap_title} ({eid}){etype_str}' + (f' {pn_link}' if pn_link else '')
                new_lines.append(new_line)
                changed = True
                continue

        elif mB:
            chap_title = mB.group(1).strip()
            evs = chap_to_events.get(chap_title, [])
            if evs:
                ev = evs[0]
                eid = ev['event_id']
                pn_str = ev.get('paragraph', '')
                anchor = pn_anchor(pn_str)
                chap_id = ev.get('chapter_id', '')
                etype = ev.get('type', '')
                etype_str = f' [{etype}]' if etype and etype != '-' else ''
                if anchor and chap_id:
                    pn_link = f'[PN:{pn_str}](../chapters/{chap_id}_{chap_title}.html#pn-{anchor})'
                elif pn_str and pn_str != '-':
                    pn_link = f'PN:{pn_str}'
                else:
                    pn_link = ''
                new_line = f'### {chap_title} ({eid}){etype_str}' + (f' {pn_link}' if pn_link else '')
                new_lines.append(new_line)
                changed = True
                continue

        new_lines.append(line)

    return '\n'.join(new_lines), changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--batch', type=int, default=0)
    args = ap.parse_args()

    data = json.loads(EVENTS_JSON.read_text('utf-8'))
    events_by_id = {e['event_id']: e for e in data['events']}

    updated = skipped = 0
    for fpath in sorted(PAGES.glob('*.md')):
        slug = fpath.stem
        content = fpath.read_text('utf-8')

        m = re.search(r'^event_ids:\s*\[(.+)\]', content, re.MULTILINE)
        if not m:
            continue

        event_ids = [x.strip() for x in m.group(1).split(',')]

        content, fm_changes = enrich_frontmatter(content, event_ids, events_by_id)
        content, hdr_changed = enrich_section_headers(content, event_ids, events_by_id)

        if not fm_changes and not hdr_changed:
            skipped += 1
            continue

        if not args.dry_run:
            fpath.write_text(content, 'utf-8')
            record_rev(slug, f'butler/add-pn: 补全PN+元数据 ({", ".join(fm_changes)})')

        updated += 1
        if updated % 300 == 0:
            print(f'  进度: {updated} 页已更新...')
        if args.batch and updated >= args.batch:
            break

    print(f'完成：更新={updated}, 跳过={skipped}')


if __name__ == '__main__':
    main()
