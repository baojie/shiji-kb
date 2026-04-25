#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入所有实体类型到 wiki（person/event 除外，已由专项脚本处理）。

- 无页面实体: 新建 stub 页面（含 ## 史记引文 节）
- 已有页面: 仅追加 ## 史记引文 节（--force 则覆盖）

用法:
    python3 kg/entities/scripts/import_entities_wiki_batch.py [--dry-run] [--force] [--type TYPE]
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT        = Path('/home/baojie/work/knowledge/shiji-kb')
CHAPTER_DIR = ROOT / 'chapter_md'
INDEX_JSON  = ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
PAGES_DIR   = ROOT / 'wiki' / 'public' / 'pages'
DATA_DIR    = ROOT / 'kg' / 'entities' / 'data'

MAX_SHOW    = 5
SNIPPET_LEN = 90
PARA_NUM_RE = re.compile(r'^\[(\d+(?:\.\d+)*)\]\s*')
ROW_ANC_RE  = re.compile(r'^\[r(\d+)\]\s*')

# ── 跳过 person 和 event（已由专项脚本处理）
SKIP_TYPES = {'person', 'event'}

# ── 实体类型 → wiki frontmatter type
WIKI_TYPE = {
    'place':         'place',
    'official':      'official',
    'time':          'time',
    'dynasty':       'dynasty',
    'feudal-state':  'state',
    'institution':   'institution',
    'tribe':         'tribe',
    'identity':      'identity',
    'artifact':      'artifact',
    'astronomy':     'astronomy',
    'biology':       'biology',
    'quantity':      'quantity',
    'mythical':      'mythical',
    'book':          'book',
    'ritual':        'ritual',
    'legal':         'legal',
    'concept':       'concept',
    'verb-military': 'verb',
    'verb-penalty':  'verb',
    'verb-political':'verb',
    'verb-economic': 'verb',
}

# ── 实体类型 → 基础中文标签
BASE_TAG = {
    'place':         '地名',
    'official':      '官职',
    'time':          '时间',
    'dynasty':       '朝代',
    'feudal-state':  '邦国',
    'institution':   '制度',
    'tribe':         '族群',
    'identity':      '身份',
    'artifact':      '器物',
    'astronomy':     '天文',
    'biology':       '生物',
    'quantity':      '数量',
    'mythical':      '神话',
    'book':          '典籍',
    'ritual':        '礼仪',
    'legal':         '法律',
    'concept':       '概念',
    'verb-military': '军事动词',
    'verb-penalty':  '刑法动词',
    'verb-political':'政治动词',
    'verb-economic': '经济动词',
}

# ── 可用的 categories 文件（key = entity type）
CAT_FILES = {
    'place':        DATA_DIR / 'place_categories.json',
    'official':     DATA_DIR / 'official_categories.json',
    'feudal-state': DATA_DIR / 'feudal_state_categories.json',
    'identity':     DATA_DIR / 'identity_categories.json',
    'person':       DATA_DIR / 'person_categories.json',  # 备用，不实际用
}


def load_categories() -> dict:
    """按类型加载 categories，返回 {etype: {name: [cats]}}"""
    result = {}
    for etype, fpath in CAT_FILES.items():
        if fpath.exists():
            with open(fpath, encoding='utf-8') as f:
                result[etype] = json.load(f)
        else:
            result[etype] = {}
    return result


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


def chapter_num(chapter_id: str) -> str:
    return chapter_id.split('_')[0]


def pn_cite(chap: str, pn: str) -> str:
    return f'（{chapter_num(chap)}-{pn}）'


def build_shiji_section(canonical: str, entry: dict, para_index: dict) -> str:
    refs  = entry['refs']
    count = entry['count']

    lines = ['## 史记引文', '']
    lines.append(f'《史记》中出现 **{count}** 处。')
    lines.append('')

    by_chap = defaultdict(list)
    for chap, pn in refs:
        by_chap[chap].append(pn)

    lines.append('**章节分布：**')
    lines.append('')
    for chap in sorted(by_chap.keys()):
        pns   = by_chap[chap]
        title = chapter_title(chap)
        pn_str = '、'.join(pn_cite(chap, p) for p in pns[:8])
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
            lines.append(f'> 出自 [[{chap}|{title}]] {pn_cite(chap, pn)}：{snip_hl}')
            lines.append('>')
        if lines[-1] == '>':
            lines.pop()
        lines.append('')

    return '\n'.join(lines)


def new_page_content(canonical: str, etype: str, entry: dict,
                     para_index: dict, categories: list) -> str:
    aliases = [a for a in entry.get('aliases', []) if a != canonical]
    alias_yaml = json.dumps(aliases, ensure_ascii=False) if aliases else '[]'

    base_tag = BASE_TAG.get(etype, etype)
    tags = [base_tag] + [c for c in categories if c != base_tag]
    tags_yaml = json.dumps(tags, ensure_ascii=False)
    wiki_type = WIKI_TYPE.get(etype, etype)

    front = f"""---
id: {canonical}
type: {wiki_type}
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


def strip_shiji_section(content: str) -> str:
    if '## 史记引文' not in content:
        return content
    start = content.find('## 史记引文')
    rest = content[start + 6:]
    next_h2 = rest.find('\n## ')
    if next_h2 >= 0:
        return content[:start] + content[start + 6 + next_h2 + 1:]
    return content[:start].rstrip('\n') + '\n'


def update_page_content(content: str, canonical: str, etype: str,
                        entry: dict, para_index: dict,
                        force: bool = False) -> str:
    if '## 史记引文' in content:
        if not force:
            return content
        content = strip_shiji_section(content)
    section = build_shiji_section(canonical, entry, para_index)
    anchor = '## 相关页面'
    if anchor in content:
        idx = content.find(anchor)
        return content[:idx] + section + '\n' + content[idx:]
    return content.rstrip('\n') + '\n\n' + section + '\n'


def entity_slug(name: str) -> str:
    """处理含 | 或 / 的复合实体名，取第一段作为文件名"""
    if '|' in name:
        return name.split('|')[0]
    if '/' in name:
        return name.split('/')[0]
    return name


def main():
    dry_run     = '--dry-run' in sys.argv
    force       = '--force' in sys.argv
    target_type = next((a.split('=')[1] if '=' in a else sys.argv[sys.argv.index(a) + 1]
                        for a in sys.argv[1:] if a.startswith('--type')), None)

    print('1. 加载数据…')
    with open(INDEX_JSON, encoding='utf-8') as f:
        idx = json.load(f)

    all_cats = load_categories()

    print('2. 构建段落索引…')
    para_index = build_para_index(CHAPTER_DIR)
    total_paras = sum(len(v) for v in para_index.values())
    print(f'   {len(para_index)} 章节，{total_paras} 段落')

    types_to_process = {target_type: idx[target_type]} if target_type else {
        etype: entries for etype, entries in idx.items()
        if etype not in SKIP_TYPES
    }

    total_created = total_updated = total_skipped = 0

    for etype, entities in types_to_process.items():
        cats_map = all_cats.get(etype, {})
        created = updated = skipped = 0

        print(f'\n3. 处理 [{etype}] {len(entities)} 条…')
        for canonical, entry in entities.items():
            slug = entity_slug(canonical)
            # skip invalid slugs
            if not slug.strip() or slug.strip('-') == '':
                skipped += 1
                continue

            page_path = PAGES_DIR / f'{slug}.md'
            categories = cats_map.get(canonical, cats_map.get(slug, []))

            if not page_path.exists():
                content = new_page_content(canonical, etype, entry, para_index, categories)
                if dry_run:
                    print(f'  [+] 新建: {canonical} ({entry["count"]}处)')
                else:
                    page_path.write_text(content, encoding='utf-8')
                    created += 1
            else:
                old = page_path.read_text(encoding='utf-8')
                new = update_page_content(old, canonical, etype, entry, para_index, force=force)
                if new.strip() == old.strip():
                    skipped += 1
                    continue
                if dry_run:
                    print(f'  [✓] 更新: {canonical}')
                else:
                    page_path.write_text(new, encoding='utf-8')
                    updated += 1

        print(f'   [{etype}] 完成: 新建 {created}，更新 {updated}，跳过 {skipped}')
        total_created += created
        total_updated += updated
        total_skipped += skipped

    if not dry_run:
        print(f'\n全部完成: 新建 {total_created}，更新 {total_updated}，跳过 {total_skipped}')
        print('\n下一步: python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/pages.json')
    else:
        print(f'\n[dry-run] 预计新建 {total_created}+，更新 {total_updated}+')


if __name__ == '__main__':
    main()
