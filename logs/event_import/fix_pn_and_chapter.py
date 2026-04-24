#!/usr/bin/env python3
"""
Fix PN format + add chapter links to all event pages.
1. pn: "[9]"  →  pn: (028-9)
2. pn: 028-010:"[9]" | 033-029:"[23.7]"  →  pn: (028-9) | (033-23.7)
3. Add chapter: [封禅书] (or multi) to :::meta block
"""
import re, subprocess, sys, argparse
from pathlib import Path

ROOT = Path('.').resolve()
PAGES = ROOT / 'wiki/public/pages'

def record_rev(slug, summary):
    subprocess.run([sys.executable,
        str(ROOT / 'wiki/scripts/butler/record_revision.py'),
        slug, '--summary', summary, '--author', 'butler'],
        capture_output=True)

# Build chapter_id ('028') → label ('封禅书')
chap_map = {}
for f in sorted(PAGES.glob('[0-9][0-9][0-9]_*.md')):
    m = re.match(r'^(\d{3})_(.+)\.md$', f.name)
    if m:
        cid, label = m.group(1), m.group(2)
        txt = f.read_text('utf-8', errors='ignore')
        if 'type: chapter' in txt:
            chap_map[cid] = label


def strip_para(s):
    """[165.2]-[167.1] → 165.2-167.1 | [9] → 9 | r79 → r79"""
    s = s.strip().strip('"').strip("'")
    rng = re.match(r'^\[([^\]]+)\]-\[([^\]]+)\]$', s)
    if rng:
        return rng.group(1)   # take only start of range
    single = re.match(r'^\[([^\]]+)\]$', s)
    if single:
        return single.group(1)
    return s


def convert_pn(pn_val, event_ids):
    v = pn_val.strip().strip('"').strip("'")

    # Already converted: starts with (
    if v.startswith('('):
        return v

    # Multi-event: 028-010:"[9]" | 033-029:"[23.7]"
    if re.search(r'\d{3}-\d{3,4}:"', v):
        parts = []
        for seg in re.split(r'\s*\|\s*', v):
            seg = seg.strip()
            mm = re.match(r'(\d{3})-\d{3,4}:"?([^"]+)"?', seg)
            if mm:
                parts.append(f'({mm.group(1)}-{strip_para(mm.group(2))})')
            else:
                parts.append(seg)
        return ' | '.join(parts)

    # Single value
    if event_ids:
        cid = event_ids[0].split('-')[0]
        return f'({cid}-{strip_para(v)})'
    return v


def get_chapters(event_ids):
    seen, result = set(), []
    for eid in event_ids:
        cid = eid.split('-')[0]
        lbl = chap_map.get(cid)
        if lbl and lbl not in seen:
            seen.add(lbl)
            result.append(lbl)
    return result


def process(fpath, dry_run=False):
    content = fpath.read_text('utf-8')

    m_ids = re.search(r'^event_ids:\s*\[(.+)\]', content, re.MULTILINE)
    if not m_ids:
        return False

    event_ids = [x.strip() for x in m_ids.group(1).split(',')]

    meta_re = re.compile(r'^(::: meta\n)([\s\S]*?)(^:::[ \t]*$)', re.MULTILINE)
    meta_m = meta_re.search(content)
    if not meta_m:
        return False

    body = meta_m.group(2)
    changed = False

    # Fix pn line
    def fix_pn_line(lm):
        nonlocal changed
        new_val = convert_pn(lm.group(1), event_ids)
        if new_val != lm.group(1).strip().strip('"').strip("'"):
            changed = True
            return f'pn: {new_val}\n'
        return lm.group(0)

    new_body = re.sub(r'^pn: (.+)\n', fix_pn_line, body, flags=re.MULTILINE)

    # Add chapter if missing
    if 'chapter:' not in new_body:
        chapters = get_chapters(event_ids)
        if chapters:
            if len(chapters) == 1:
                chapter_val = f'[{chapters[0]}]'
            else:
                chapter_val = '[' + ', '.join(chapters) + ']'
            new_body += f'chapter: {chapter_val}\n'
            changed = True

    if not changed:
        return False

    new_content = (content[:meta_m.start(2)] + new_body +
                   content[meta_m.end(2):])
    if not dry_run:
        fpath.write_text(new_content, 'utf-8')
        record_rev(fpath.stem, 'butler/fix-pn: 修正PN格式 + 添加章节关联')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--sample', type=int, default=0, help='only process N pages')
    args = ap.parse_args()

    updated = skipped = errors = 0
    for fpath in sorted(PAGES.glob('*.md')):
        try:
            r = process(fpath, dry_run=args.dry_run)
            if r:
                updated += 1
                if updated % 500 == 0:
                    print(f'  进度: {updated}...')
            else:
                skipped += 1
        except Exception as e:
            errors += 1
            print(f'ERROR {fpath.stem}: {e}')
        if args.sample and updated >= args.sample:
            break

    print(f'完成: 更新={updated}, 跳过={skipped}, 错误={errors}')


if __name__ == '__main__':
    main()
