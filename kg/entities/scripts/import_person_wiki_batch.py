#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入人名到 wiki — 直接写文件版（跳过逐个 record_revision）

适用于大批量导入场景，完成后手动运行 build_registry.py 重建 pages.json。

用法:
    python3 kg/entities/scripts/import_person_wiki_batch.py [--dry-run] [--limit N]
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT        = Path('/home/baojie/work/knowledge/shiji-kb')
CHAPTER_DIR = ROOT / 'chapter_md'
INDEX_JSON  = ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
PERSON_CAT  = ROOT / 'kg' / 'entities' / 'data' / 'person_categories.json'
PAGES_DIR   = ROOT / 'wiki' / 'public' / 'pages'

MAX_SHOW    = 5
SNIPPET_LEN = 90
PARA_NUM_RE = re.compile(r'^\[(\d+(?:\.\d+)*)\]\s*')
ROW_ANC_RE  = re.compile(r'^\[r(\d+)\]\s*')


def strip_tags(text: str) -> str:
    text = re.sub(r'〖[^〗|]+\|([^〗]+)〗', r'\1', text)
    text = re.sub(r'〖.([^〖〗]+)〗', r'\1', text)
    text = re.sub(r'⟦.([^⟦⟧]+)⟧', r'\1', text)
    text = re.sub(r'〘([^〙]+)〙', r'\1', text)
    text = PARA_NUM_RE.sub('', text)
    text = ROW_ANC_RE.sub('', text)
    return text.strip()


def snippet(text: str, entity: str, maxlen: int = SNIPPET_LEN) -> str:
    idx = text.find(entity)
    if idx < 0:
        return text[:maxlen] + ('…' if len(text) > maxlen else '')
    half  = (maxlen - len(entity)) // 2
    start = max(0, idx - half)
    end   = min(len(text), idx + len(entity) + half)
    result = text[start:end]
    if start > 0: result = '…' + result
    if end < len(text): result = result + '…'
    return result


def highlight_md(text: str, entity: str) -> str:
    idx = text.find(entity)
    if idx < 0:
        return text
    return text[:idx] + f'**{entity}**' + text[idx + len(entity):]


def build_para_index(chapter_dir: Path) -> dict:
    index = {}
    for fpath in sorted(chapter_dir.glob('*.tagged.md')):
        chapter_id = fpath.stem.replace('.tagged', '')
        paras = {}
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        row_counter = 0
        row_anchors = {}
        i, n = 0, len(lines)
        while i < n:
            stripped = lines[i].strip()
            if stripped.startswith('|') and '|' in stripped[1:]:
                block = []
                j = i
                while j < n and lines[j].strip().startswith('|'):
                    block.append(j); j += 1
                if len(block) >= 2:
                    sep = lines[block[1]].strip().replace('-', '')
                    data_start = 2 if re.match(r'^[\s|:-]+$', sep) else 1
                    for idx_l in block[data_start:]:
                        row_text   = lines[idx_l].strip()
                        first_cell = row_text[1:].split('|', 1)[0] if row_text.startswith('|') else ''
                        m = re.match(r'^\s*\[r(\d+)\]\s*', first_cell)
                        if m:
                            rn = m.group(1)
                        else:
                            row_counter += 1; rn = str(row_counter)
                        row_anchors[idx_l] = f'r{rn}'
                i = j
            else:
                i += 1

        current_pn = None
        current_buf = []

        def flush():
            if current_pn and current_buf:
                paras[current_pn] = strip_tags(' '.join(current_buf))

        for idx_l, line in enumerate(lines):
            if idx_l in row_anchors:
                flush(); current_pn = None; current_buf = []
                paras[row_anchors[idx_l]] = strip_tags(lines[idx_l])
                continue
            m = PARA_NUM_RE.match(line)
            if m:
                flush()
                current_pn = m.group(1)
                current_buf = [line[m.end():].strip()] if line[m.end():].strip() else []
            elif current_pn and line.strip():
                current_buf.append(line.strip())

        flush()
        index[chapter_id] = paras
    return index


def chapter_title(chapter_id: str) -> str:
    parts = chapter_id.split('_', 1)
    return parts[1] if len(parts) > 1 else chapter_id


def build_shiji_section(canonical: str, entry: dict, para_index: dict) -> str:
    refs  = entry['refs']
    count = entry['count']

    lines = ['## 史记引文', '']
    lines.append(f'《史记》中出现 **{count}** 处（标注符号：〖@{canonical}〗）。')
    lines.append('')

    by_chap = defaultdict(list)
    for chap, pn in refs:
        by_chap[chap].append(pn)

    lines.append('**章节分布：**')
    lines.append('')
    for chap in sorted(by_chap.keys()):
        pns   = by_chap[chap]
        title = chapter_title(chap)
        pn_str = '、'.join(f'§{p}' for p in pns[:8])
        if len(pns) > 8:
            pn_str += f' 等共 {len(pns)} 处'
        lines.append(f'- [[{chap}|{title}]]：{pn_str}')
    lines.append('')

    snippets = []
    per_chap = defaultdict(int)
    for chap, pn in refs:
        if per_chap[chap] >= 2:
            continue
        text = para_index.get(chap, {}).get(pn, '')
        if not text:
            continue
        snip = snippet(text, canonical)
        snip_hl = highlight_md(snip, canonical)
        snippets.append((chap, pn, snip_hl))
        per_chap[chap] += 1
        if len(snippets) >= MAX_SHOW:
            break

    if snippets:
        showing = len(snippets)
        note = f'（共 {count} 处，下列仅示 {showing} 条）' if count > showing else ''
        lines.append(f'**引文摘录{note}：**')
        lines.append('')
        for chap, pn, snip_hl in snippets:
            title = chapter_title(chap)
            lines.append(f'> 出自 [[{chap}|{title}]] §{pn}：{snip_hl}')
            lines.append('>')
        if lines[-1] == '>':
            lines.pop()
        lines.append('')

    return '\n'.join(lines)


def new_page_content(canonical: str, entry: dict, para_index: dict,
                     categories: list) -> str:
    aliases = [a for a in entry.get('aliases', []) if a != canonical]
    alias_yaml = json.dumps(aliases, ensure_ascii=False) if aliases else '[]'
    tags_yaml = json.dumps(categories, ensure_ascii=False) if categories else '[]'

    front = f"""---
id: {canonical}
type: person
label: {canonical}
aliases: {alias_yaml}
canonical_name: {canonical}
tags: {tags_yaml}
featured: false
---"""

    shiji_sec = build_shiji_section(canonical, entry, para_index)

    body = f"""# {canonical}

出现于《史记》**{entry['count']}** 处。

{shiji_sec}
## 相关页面

"""
    return front + '\n\n' + body


def update_page_content(content: str, canonical: str, entry: dict,
                        para_index: dict) -> str:
    if '## 史记引文' in content:
        return content
    section = build_shiji_section(canonical, entry, para_index)
    anchor = '## 相关页面'
    if anchor in content:
        idx = content.find(anchor)
        return content[:idx] + section + '\n' + content[idx:]
    return content.rstrip('\n') + '\n\n' + section + '\n'


def main():
    dry_run = '--dry-run' in sys.argv
    limit = None
    for arg in sys.argv[1:]:
        if arg.startswith('--limit='):
            limit = int(arg.split('=')[1])
        elif arg == '--limit' and sys.argv.index(arg) + 1 < len(sys.argv):
            limit = int(sys.argv[sys.argv.index(arg) + 1])

    print('1. 加载数据…')
    with open(INDEX_JSON, encoding='utf-8') as f:
        idx = json.load(f)
    person_index = idx.get('person', {})

    with open(PERSON_CAT, encoding='utf-8') as f:
        person_cats = json.load(f)

    print('2. 构建段落索引…')
    para_index = build_para_index(CHAPTER_DIR)
    total_paras = sum(len(v) for v in para_index.values())
    print(f'   {len(para_index)} 章节，{total_paras} 段落')

    created = updated = skipped = 0
    count = 0

    for canonical, entry in person_index.items():
        if limit and count >= limit:
            break

        page_path = PAGES_DIR / f'{canonical}.md'

        if not page_path.exists():
            # 新建
            categories = person_cats.get(canonical, [])
            content = new_page_content(canonical, entry, para_index, categories)
            if dry_run:
                print(f'[+] 新建: {canonical} ({entry["count"]}处) {categories}')
            else:
                page_path.write_text(content, encoding='utf-8')
                print(f'[+] {canonical} ({entry["count"]}处) {categories}')
                created += 1
        else:
            # 更新已有页面
            old = page_path.read_text(encoding='utf-8')
            new = update_page_content(old, canonical, entry, para_index)
            if new.strip() == old.strip():
                skipped += 1
                continue
            if dry_run:
                print(f'[✓] 更新: {canonical} ({entry["count"]}处)')
            else:
                page_path.write_text(new, encoding='utf-8')
                print(f'[✓] {canonical} ({entry["count"]}处)')
                updated += 1

        count += 1

    if dry_run:
        print(f'\n[dry-run] 将新建/更新共 {count} 个页面，已完成: {skipped} 跳过')
    else:
        print(f'\n完成: 新建 {created}，更新 {updated}，跳过 {skipped}')
        print('\n下一步: python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json')


if __name__ == '__main__':
    main()
