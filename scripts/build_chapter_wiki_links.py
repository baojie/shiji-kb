#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为每个章节 wiki 页（docs/wiki/pages/NNN_*.md）添加"主要实体"和"本章事件"两节。

数据来源：
  - 实体：chapter_md/NNN_*.tagged.md 中的 〖@〗〖=〗〖◆〗 标注
  - 事件：kg/events/data/NNN_*_事件索引.md 表格

运行：
    python scripts/build_chapter_wiki_links.py          # 全部130章
    python scripts/build_chapter_wiki_links.py 054      # 单章
    python scripts/build_chapter_wiki_links.py --dry-run # 预览
"""

import re
import sys
import os
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
TAGGED_DIR = ROOT / 'chapter_md'
EVENT_IDX_DIR = ROOT / 'kg' / 'events' / 'data'
WIKI_PAGES_DIR = ROOT / 'docs' / 'wiki' / 'pages'

# ---- 已有 wiki 页面的实体名称集合 ----
def get_wiki_page_names() -> set:
    names = set()
    for f in WIKI_PAGES_DIR.iterdir():
        if not f.name[0].isdigit() and f.suffix == '.md':
            names.add(f.stem)
    return names

WIKI_NAMES = get_wiki_page_names()

# ---- 从 tagged.md 提取实体 ----
PERSON_RE = re.compile(r'〖@([^〗|]+?)(?:\|([^〗]+?))?\〗')
PLACE_RE  = re.compile(r'〖=([^〗]+?)\〗')
DYN_RE    = re.compile(r'〖◆([^〗]+?)\〗')
ANNO_STRIP_RE = re.compile(r'〖[^〗]*?〗|〘[^〙]*?〙|⟦[^⟧]*?⟧')

TOP_PERSONS  = 12
TOP_PLACES   = 10
TOP_DYNASTIES = 6


def extract_entities(tagged_path: Path):
    text = tagged_path.read_text(encoding='utf-8')

    persons = []
    for m in PERSON_RE.finditer(text):
        canon = (m.group(2) or m.group(1)).strip()
        persons.append(canon)

    places = [m.group(1).strip() for m in PLACE_RE.finditer(text)]

    dynasties = [m.group(1).strip() for m in DYN_RE.finditer(text)]

    return (
        Counter(persons).most_common(TOP_PERSONS),
        Counter(places).most_common(TOP_PLACES),
        Counter(dynasties).most_common(TOP_DYNASTIES),
    )


# ---- 从事件索引 MD 提取事件 ----
def parse_event_row(line: str):
    """Parse a pipe-delimited event row: | id | name | type | time | place | persons | dynasty |"""
    if not line.startswith('|'):
        return None
    parts = [p.strip() for p in line.strip().strip('|').split('|')]
    if len(parts) < 6:
        return None
    eid = parts[0]
    if not re.match(r'^\d{3}-\d{3}$', eid):
        return None
    return parts  # [eid, name, etype, time, place, persons, ...]


def extract_events(chapter_no: str) -> list:
    """返回 [(event_id, name, etype, time, persons), ...]"""
    import glob as _glob
    pattern = str(EVENT_IDX_DIR / f'{chapter_no}_*_事件索引.md')
    files = _glob.glob(pattern)
    if not files:
        return []
    events = []
    for line in Path(files[0]).read_text(encoding='utf-8').splitlines():
        parts = parse_event_row(line)
        if not parts:
            continue
        eid, name, etype, time = parts[0], parts[1], parts[2], parts[3]
        persons_raw = parts[5] if len(parts) > 5 else ''
        # Extract person canonical names from 〖@名〗 or 〖@显示|规范〗
        person_names = []
        for pm in re.finditer(r'〖@([^〗|]+?)(?:\|([^〗]+?))?\〗', persons_raw):
            person_names.append((pm.group(2) or pm.group(1)).strip())
        persons_clean = ' / '.join(person_names) if person_names else ANNO_STRIP_RE.sub('', persons_raw).strip()
        events.append((eid, name, etype, time, persons_clean))
    return events


# ---- 格式化实体为 wikilink 或 HTML 链接 ----
def fmt_person(name: str) -> str:
    if name in WIKI_NAMES:
        return f'[[{name}]]'
    # link to entity index
    return f'[{name}](../entities/person.html#entity-{name})'


def fmt_place(name: str) -> str:
    return f'[{name}](../entities/place.html#entity-{name})'


def fmt_dynasty(name: str) -> str:
    return f'[{name}](../entities/dynasty.html#entity-{name})'


# ---- 事件名：知名事件有 wiki 页面 ----
def fmt_event_name(name: str) -> str:
    stripped = name.strip()
    if stripped in WIKI_NAMES:
        return f'[[{stripped}]]'
    return stripped


# ---- 构建新增节内容 ----
SECTION_MARKER = '<!-- auto: entities+events -->'
SECTION_END    = '<!-- /auto: entities+events -->'


def build_section(chapter_no: str, tagged_path: Path) -> str:
    persons, places, dynasties = extract_entities(tagged_path)
    events = extract_events(chapter_no)

    lines = [SECTION_MARKER, '']

    # 实体节
    lines.append('## 主要实体')
    lines.append('')

    if persons:
        person_links = ' · '.join(fmt_person(n) for n, _ in persons)
        lines.append(f'**人物**：{person_links}')
        lines.append('')

    if places:
        place_links = ' · '.join(fmt_place(n) for n, _ in places)
        lines.append(f'**地点**：{place_links}')
        lines.append('')

    if dynasties:
        dyn_links = ' · '.join(fmt_dynasty(n) for n, _ in dynasties)
        lines.append(f'**邦国**：{dyn_links}')
        lines.append('')

    # 事件节
    if events:
        lines.append('## 本章事件')
        lines.append('')
        lines.append('| 编号 | 事件 | 类型 | 时间 | 主要人物 |')
        lines.append('|------|------|------|------|---------|')
        for eid, name, etype, time, persons_str in events:
            # 清理时间字段中的标注符号
            time_clean = ANNO_STRIP_RE.sub('', time).strip()
            name_fmt = fmt_event_name(name)
            lines.append(f'| {eid} | {name_fmt} | {etype} | {time_clean} | {persons_str} |')
        lines.append('')

    lines.append(SECTION_END)
    return '\n'.join(lines)


# ---- 更新 wiki 页面 ----
def update_wiki_page(wiki_path: Path, section: str, dry_run: bool = False) -> bool:
    content = wiki_path.read_text(encoding='utf-8')

    # 移除旧的自动生成节
    if SECTION_MARKER in content:
        start = content.index(SECTION_MARKER)
        end_marker = SECTION_END
        if end_marker in content:
            end = content.index(end_marker) + len(end_marker)
            content = content[:start].rstrip() + '\n' + content[end:].lstrip('\n')
        else:
            content = content[:start].rstrip() + '\n'

    # 追加新节
    new_content = content.rstrip() + '\n\n' + section + '\n'

    if dry_run:
        print(f'[DRY-RUN] {wiki_path.name}:')
        print(section[:600])
        print('...')
        return True

    wiki_path.write_text(new_content, encoding='utf-8')
    return True


# ---- 主函数 ----
def main():
    dry_run = '--dry-run' in sys.argv
    chapter_filter = None
    for arg in sys.argv[1:]:
        if not arg.startswith('--') and re.match(r'^\d+$', arg):
            chapter_filter = arg.zfill(3)

    tagged_files = sorted(TAGGED_DIR.glob('*.tagged.md'))
    updated = 0
    skipped = 0

    for tagged_path in tagged_files:
        # e.g. 054_曹相国世家.tagged.md
        stem = tagged_path.stem.replace('.tagged', '')
        chapter_no = stem[:3]

        if chapter_filter and chapter_no != chapter_filter:
            continue

        # Find corresponding wiki page
        wiki_matches = list(WIKI_PAGES_DIR.glob(f'{chapter_no}_*.md'))
        if not wiki_matches:
            print(f'[SKIP] No wiki page for {chapter_no}')
            skipped += 1
            continue

        wiki_path = wiki_matches[0]
        section = build_section(chapter_no, tagged_path)

        update_wiki_page(wiki_path, section, dry_run)
        updated += 1
        if not dry_run:
            print(f'[OK] {wiki_path.name}')

    print(f'\n完成：更新 {updated} 章，跳过 {skipped} 章')


if __name__ == '__main__':
    main()
