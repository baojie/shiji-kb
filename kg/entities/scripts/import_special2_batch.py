#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入专项索引 Round 2：
  - 谥号：    docs/special/shihao.html        → 73 页
  - 避讳：    data/taboo_characters.json      → 13 页
  - 典籍引文：data/citations.json             → 64 新页 + 追加现有书页
  - 姓氏：    docs/special/data/xingshi/xing_index.json → 5 新页
  - 君号：    docs/special/jun_titles.html    → 15 新页

用法:
    python3 kg/entities/scripts/import_special2_batch.py [--dry-run] [--force] [--only TYPE]
    TYPE: shihao | bihui | citations | xingshi | juntitles
"""

import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT      = Path('/home/baojie/work/knowledge/shiji-kb')
PAGES_DIR = ROOT / 'wiki' / 'public' / 'pages'

SHIHAO_HTML   = ROOT / 'docs' / 'special' / 'shihao.html'
BIHUI_JSON    = ROOT / 'data' / 'taboo_characters.json'
CITATIONS_JSON= ROOT / 'data' / 'citations.json'
XINGSHI_JSON  = ROOT / 'docs' / 'special' / 'data' / 'xingshi' / 'xing_index.json'
JUNTITLES_HTML= ROOT / 'docs' / 'special' / 'jun_titles.html'


# ─────────────────────────────────────────────────────────────────────────────
# 谥号
# ─────────────────────────────────────────────────────────────────────────────

def run_shihao(dry_run: bool, force: bool) -> tuple[int, int]:
    with open(SHIHAO_HTML, encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    created = skipped = 0
    for entry in soup.find_all(class_='shihao-entry'):
        char_el = entry.find(class_='shihao-char')
        if not char_el:
            continue
        char = char_el.get_text(strip=True).replace('▼', '').strip()
        slug = f'谥号·{char}'
        page_path = PAGES_DIR / f'{slug}.md'

        if page_path.exists() and not force:
            skipped += 1
            continue

        # 谥法含义
        meaning_el = entry.find(class_='shihao-meaning')
        meaning = ''
        if meaning_el:
            meaning = meaning_el.get_text(strip=True).replace('谥法：', '').replace('谥法:', '').strip()

        # 使用人数
        count_el = entry.find(class_='rank-count')
        count_text = count_el.get_text(strip=True) if count_el else ''
        total_m = re.search(r'共(\d+)人', count_text)
        total_count = int(total_m.group(1)) if total_m else 0

        # 按职级列出人物
        person_blocks = []
        for rank_group in entry.find_all(class_='rank-group'):
            h3 = rank_group.find('h3')
            rank_title = h3.get_text(strip=True) if h3 else ''
            # remove count from rank title
            rank_title = re.sub(r'\(\d+人\)', '', rank_title).strip()
            persons = []
            for person_el in rank_group.find_all(class_='person-item'):
                name_el = person_el.find(class_='person-name') or person_el.find('a')
                if not name_el:
                    name_el = person_el
                name = name_el.get_text(strip=True)
                chapter_el = person_el.find(class_='chapter-refs')
                chapters = chapter_el.get_text(strip=True) if chapter_el else ''
                if name:
                    persons.append((name, chapters))
            if persons:
                person_blocks.append((rank_title, persons))

        # 构建页面内容
        tags = json.dumps(['谥号', '史记', char], ensure_ascii=False)
        desc = json.dumps(meaning[:80] if meaning else f'《史记》中使用{char}谥号的人物', ensure_ascii=False)

        content = f"""---
id: {slug}
type: shihao
label: {slug}
aliases: ["{char}谥"]
tags: {tags}
shihao_char: "{char}"
featured: false
description: {desc}
---

# {slug}

**谥法**：{meaning}

《史记》中使用 **{char}** 谥号的人物共 **{total_count}** 人。

## 使用人物

"""
        for rank_title, persons in person_blocks:
            if rank_title:
                content += f'**{rank_title}**（{len(persons)}人）：'
                refs = []
                for name, chapters in persons:
                    ref = f'[[{name}]]'
                    if chapters:
                        ref += f'{chapters}'
                    refs.append(ref)
                content += '、'.join(refs) + '\n\n'

        content += '## 相关页面\n\n'

        if dry_run:
            print(f'  [+] {slug} ({total_count}人)')
        else:
            page_path.write_text(content, encoding='utf-8')
        created += 1

    return created, skipped


# ─────────────────────────────────────────────────────────────────────────────
# 避讳
# ─────────────────────────────────────────────────────────────────────────────

def run_bihui(dry_run: bool, force: bool) -> tuple[int, int]:
    with open(BIHUI_JSON, encoding='utf-8') as f:
        d = json.load(f)

    rules = d.get('rules', [])
    created = skipped = 0

    for rule in rules:
        rule_id  = rule.get('id', '')
        category = rule.get('category', '')
        taboo_for= rule.get('taboo_for', '')
        taboo_char = rule.get('taboo_char', '')
        replaced_by = rule.get('replaced_by', '')
        scope    = rule.get('scope', '')
        confidence = rule.get('confidence', '')
        note     = rule.get('note', '')
        patterns = rule.get('patterns', [])
        sources  = rule.get('sources', [])
        instance_count = rule.get('instance_count', 0)

        # slug: 用 taboo_char 简化形式（去括号）
        plain_char = re.sub(r'（[^）]*）', '', taboo_char).strip()
        slug = f'避讳·{plain_char}（{taboo_for.split("·")[0]}）'
        page_path = PAGES_DIR / f'{slug}.md'

        if page_path.exists() and not force:
            skipped += 1
            continue

        tags = json.dumps(['避讳', '史记', category], ensure_ascii=False)
        desc = json.dumps(f'{taboo_for}讳"{plain_char}"，以"{replaced_by}"替代', ensure_ascii=False)

        # 出现例证
        pattern_lines = []
        for pat in patterns:
            form = pat.get('form', '')
            original = pat.get('original', '')
            kind = pat.get('kind', '')
            pat_note = pat.get('note', '')
            occ_count = pat.get('occurrence_count', 0)
            pattern_lines.append(f'- **{form}**（原作"{original}"，{kind}）：{pat_note}（共{occ_count}处）')

        source_lines = [f'- {s}' for s in sources]

        content = f"""---
id: {slug}
type: bihui
label: {slug}
aliases: []
tags: {tags}
bihui_id: "{rule_id}"
category: "{category}"
taboo_for: "{taboo_for}"
taboo_char: "{taboo_char}"
replaced_by: "{replaced_by}"
confidence: "{confidence}"
description: {desc}
featured: false
---

# {slug}

**讳主**：{taboo_for}
**讳字**：{taboo_char} → 改作 **{replaced_by}**
**范围**：{scope}
**说明**：{note}

《史记》中共出现 **{instance_count}** 处。

## 讳改形式

{chr(10).join(pattern_lines)}

"""
        if source_lines:
            content += '## 文献依据\n\n' + '\n'.join(source_lines) + '\n\n'
        content += '## 相关页面\n\n'

        if dry_run:
            print(f'  [+] {slug}')
        else:
            page_path.write_text(content, encoding='utf-8')
        created += 1

    return created, skipped


# ─────────────────────────────────────────────────────────────────────────────
# 典籍引文
# ─────────────────────────────────────────────────────────────────────────────

def run_citations(dry_run: bool, force: bool) -> tuple[int, int]:
    with open(CITATIONS_JSON, encoding='utf-8') as f:
        d = json.load(f)

    books = d.get('books', [])
    created = updated = skipped = 0

    for book in books:
        canonical = book.get('canonical', '')
        if not canonical:
            continue
        category = book.get('category', '')

        # parse citations and mentions from string if needed
        citations_raw = book.get('citations', [])
        if isinstance(citations_raw, str):
            try:
                citations_raw = json.loads(citations_raw)
            except Exception:
                citations_raw = []

        mentions_raw = book.get('mentions', [])
        if isinstance(mentions_raw, str):
            try:
                mentions_raw = json.loads(mentions_raw)
            except Exception:
                mentions_raw = []

        total_citations = len(citations_raw)
        total_mentions  = len(mentions_raw)

        slug = canonical
        page_path = PAGES_DIR / f'{slug}.md'

        if page_path.exists() and not force:
            # check if already has citation section
            existing = page_path.read_text(encoding='utf-8')
            if '## 史记引用' in existing:
                skipped += 1
                continue
            # append citation section
            section = build_citation_section(canonical, category, citations_raw, mentions_raw)
            anchor = '## 相关页面'
            if anchor in existing:
                new = existing[:existing.find(anchor)] + section + '\n' + existing[existing.find(anchor):]
            else:
                new = existing.rstrip('\n') + '\n\n' + section + '\n'
            if dry_run:
                print(f'  [✓] 更新 {canonical} (+引文)')
            else:
                page_path.write_text(new, encoding='utf-8')
            updated += 1
            continue

        if page_path.exists():
            skipped += 1
            continue

        # 新建
        section = build_citation_section(canonical, category, citations_raw, mentions_raw)
        tags = json.dumps(['典籍', category, '史记引用'], ensure_ascii=False)
        desc = json.dumps(f'《史记》中引用/提及的典籍，属{category}类', ensure_ascii=False)

        content = f"""---
id: {canonical}
type: book
label: {canonical}
aliases: []
tags: {tags}
book_category: "{category}"
description: {desc}
featured: false
---

# {canonical}

{category}典籍，《史记》中共引用 **{total_citations}** 次，提及 **{total_mentions}** 次。

{section}
## 相关页面

"""
        if dry_run:
            print(f'  [+] 新建 {canonical}（引{total_citations}次，提{total_mentions}次）')
        else:
            page_path.write_text(content, encoding='utf-8')
        created += 1

    return created + updated, skipped


def build_citation_section(canonical: str, category: str,
                            citations: list, mentions: list) -> str:
    lines = ['## 史记引用', '']
    if citations:
        lines.append(f'**直接引文**（{len(citations)}处）：')
        lines.append('')
        for c in citations[:5]:
            cnum = c.get('chapter_id', '')
            cname = c.get('chapter_name', '')
            pn = c.get('para_id', '')
            snippet = c.get('snippet', '')
            if snippet:
                snippet = re.sub(r'〖[^〗|]+\|([^〗]+)〗', r'\1', snippet)
                snippet = re.sub(r'〖.([^〖〗]+)〗', r'\1', snippet)
                snippet = re.sub(r'[〖〗⟦⟧〘〙]', '', snippet)
                snippet = snippet[:80]
            ref = f'（{cnum}-{pn}）' if cnum and pn else ''
            lines.append(f'> 出自 [[{cnum}_{cname}|{cname}]] {ref}：{snippet}')
            lines.append('>')
        if lines[-1] == '>':
            lines.pop()
        lines.append('')
    if mentions:
        lines.append(f'**提及**（{len(mentions)}处）：出现于 '
                     + '、'.join(f'[[{m["chapter_id"]}_{m["chapter_name"]}|{m["chapter_name"]}]]'
                                 for m in mentions[:8])
                     + ('等' if len(mentions) > 8 else ''))
        lines.append('')
    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 姓氏
# ─────────────────────────────────────────────────────────────────────────────

def run_xingshi(dry_run: bool, force: bool) -> tuple[int, int]:
    with open(XINGSHI_JSON, encoding='utf-8') as f:
        d = json.load(f)

    xings = d.get('xings', {})
    created = skipped = 0

    for xing, info in xings.items():
        slug = f'{xing}姓'
        page_path = PAGES_DIR / f'{slug}.md'

        if page_path.exists() and not force:
            skipped += 1
            continue

        origin = info.get('origin', '')
        ancestor = info.get('ancestor', '')
        major_states = info.get('major_states', [])
        derived_shi = info.get('derived_shi', [])

        tags = json.dumps(['姓氏', '先秦', xing], ensure_ascii=False)
        desc = json.dumps(origin[:80] if origin else f'先秦{xing}姓', ensure_ascii=False)

        states_links = '、'.join(f'[[{s}]]' for s in major_states[:12])
        shi_links    = '、'.join(f'[[{s}]]' for s in derived_shi[:12])
        if len(derived_shi) > 12:
            shi_links += f'等共{len(derived_shi)}个'

        content = f"""---
id: {slug}
type: xing
label: {slug}
aliases: ["{xing}"]
tags: {tags}
ancestor: "{ancestor}"
description: {desc}
featured: false
---

# {slug}

**起源**：{origin}

**祖先**：[[{ancestor}]]

## 主要封国

{states_links if states_links else '（待补充）'}

## 衍生氏族

{shi_links if shi_links else '（待补充）'}

## 相关页面

"""
        if dry_run:
            print(f'  [+] {slug}')
        else:
            page_path.write_text(content, encoding='utf-8')
        created += 1

    return created, skipped


# ─────────────────────────────────────────────────────────────────────────────
# 君号
# ─────────────────────────────────────────────────────────────────────────────

def run_juntitles(dry_run: bool, force: bool) -> tuple[int, int]:
    with open(JUNTITLES_HTML, encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    created = skipped = 0
    seen = set()

    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) < 4:
            continue

        jun_title_el = cells[0]
        # skip if it's a header-like cell
        if not jun_title_el.get('class') and 'jun-title' not in str(jun_title_el.get('class', [])):
            if 'jun-title' not in str(jun_title_el):
                continue

        jun_title = jun_title_el.get_text(strip=True)
        if not jun_title or jun_title in seen:
            continue
        seen.add(jun_title)

        # extract fields based on column count
        real_name = cells[1].get_text(strip=True) if len(cells) > 1 else ''
        # some rows have state, some don't (秦国 rows)
        if len(cells) >= 6:
            state  = cells[2].get_text(strip=True)
            period = cells[3].get_text(strip=True)
            desc   = cells[4].get_text(strip=True)
            chap_el= cells[5].find('a')
            chapter= chap_el['href'].split('/')[-1].replace('.html', '') if chap_el else ''
        elif len(cells) >= 5:
            state  = ''
            period = cells[2].get_text(strip=True)
            desc   = cells[3].get_text(strip=True)
            chap_el= cells[4].find('a')
            chapter= chap_el['href'].split('/')[-1].replace('.html', '') if chap_el else ''
        else:
            continue

        slug = jun_title
        page_path = PAGES_DIR / f'{slug}.md'

        if page_path.exists() and not force:
            skipped += 1
            continue

        tags_list = ['君号', '封君']
        if state:
            tags_list.append(state)
        tags = json.dumps(tags_list, ensure_ascii=False)
        aliases = json.dumps([real_name], ensure_ascii=False) if real_name and real_name != '不详' else '[]'

        chap_link = f'[[{chapter}]]' if chapter else ''
        state_line = f'\n**邦国**：{state}' if state else ''

        content = f"""---
id: {slug}
type: jun
label: {slug}
aliases: {aliases}
tags: {tags}
real_name: "{real_name}"
period: "{period}"
featured: false
---

# {slug}

**本名**：{real_name}
**时代**：{period}{state_line}

{desc}

## 相关章节

{chap_link}

## 相关页面

"""
        if dry_run:
            print(f'  [+] {slug}（{real_name}，{period}）')
        else:
            page_path.write_text(content, encoding='utf-8')
        created += 1

    return created, skipped


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    dry_run = '--dry-run' in sys.argv
    force   = '--force' in sys.argv
    only    = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--only=')), None)

    tasks = []
    if not only or only == 'shihao':
        tasks.append(('谥号', run_shihao))
    if not only or only == 'bihui':
        tasks.append(('避讳', run_bihui))
    if not only or only == 'citations':
        tasks.append(('典籍引文', run_citations))
    if not only or only == 'xingshi':
        tasks.append(('姓氏', run_xingshi))
    if not only or only == 'juntitles':
        tasks.append(('君号', run_juntitles))

    total_created = total_skipped = 0
    for label, fn in tasks:
        print(f'处理 [{label}]…')
        c, s = fn(dry_run, force)
        print(f'  完成: 新建/更新 {c}，跳过 {s}')
        total_created += c
        total_skipped += s

    print(f'\n全部完成: 新建/更新 {total_created}，跳过 {total_skipped}')
    if not dry_run:
        print('\n下一步: python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json')


if __name__ == '__main__':
    main()
