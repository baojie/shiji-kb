#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 entity_index.json['feudal-state'] 的邦国信息和引文上下文批量导入 wiki。

- 无页面实体 (202): 用 add_page.py 新建页面
- 已有页面实体 (450): 用 edit_page.py 更新 ## 史记引文 节
- 仅别名实体 (9): 跳过

用法:
    python3 /tmp/import_feudal_state_wiki.py [--dry-run] [实体名]
"""

import html as htmllib
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT       = Path('/home/baojie/work/knowledge/shiji-kb')
CHAPTER_DIR = ROOT / 'chapter_md'
INDEX_JSON  = ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
PAGES_DIR   = ROOT / 'wiki' / 'public' / 'pages'
PAGES_JSON  = ROOT / 'wiki' / 'public' / 'pages.json'
ADD_PAGE    = ROOT / 'wiki' / 'scripts' / 'butler' / 'add_page.py'
EDIT_PAGE   = ROOT / 'wiki' / 'scripts' / 'butler' / 'edit_page.py'

MAX_SHOW    = 5
SNIPPET_LEN = 90
PARA_NUM_RE = re.compile(r'^\[(\d+(?:\.\d+)*)\]\s*')
ROW_ANC_RE  = re.compile(r'^\[r(\d+)\]\s*')

# ── 标注剥离 ─────────────────────────────────────────────────────────────────
def strip_tags(text: str) -> str:
    text = re.sub(r'〖[^〗|]+\|([^〗]+)〗', r'\1', text)
    text = re.sub(r'〖.([^〖〗]+)〗', r'\1', text)
    text = re.sub(r'⟦.([^⟦⟧]+)⟧', r'\1', text)
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
    """在 text 中将 entity 加粗（Markdown）。"""
    idx = text.find(entity)
    if idx < 0:
        return text
    return text[:idx] + f'**{entity}**' + text[idx + len(entity):]

# ── 段落索引 ─────────────────────────────────────────────────────────────────
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
                        row_text  = lines[idx_l].strip()
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

# ── 章节标题 ─────────────────────────────────────────────────────────────────
def chapter_title(chapter_id: str) -> str:
    parts = chapter_id.split('_', 1)
    return parts[1] if len(parts) > 1 else chapter_id

# ── 构建 ## 史记引文 节（Markdown） ──────────────────────────────────────────
def build_shiji_section(canonical: str, entry: dict, para_index: dict) -> str:
    refs  = entry['refs']   # [(chapter_id, para_num)]
    count = entry['count']
    aliases = [a for a in entry.get('aliases', []) if a != canonical]

    lines = ['## 史记引文', '']
    lines.append(f'《史记》中出现 **{count}** 处（标注符号：〖◆{canonical}〗）。')
    lines.append('')

    # 章节分布
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

    # 引文摘录
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

# ── 新页面内容 ────────────────────────────────────────────────────────────────
def new_page_content(canonical: str, entry: dict, para_index: dict) -> str:
    aliases = [a for a in entry.get('aliases', []) if a != canonical]
    alias_yaml = json.dumps(aliases, ensure_ascii=False) if aliases else '[]'

    front = f"""---
id: {canonical}
type: state
label: {canonical}
aliases: {alias_yaml}
tags: [邦国]
---"""

    shiji_sec = build_shiji_section(canonical, entry, para_index)

    body = f"""# {canonical}

出现于《史记》**{entry['count']}** 处。

{shiji_sec}
## 相关页面

"""
    return front + '\n\n' + body

# ── 更新已有页面（append-only：仅在无 ## 史记引文 时才追加） ─────────────────
def update_page_content(content: str, canonical: str, entry: dict, para_index: dict) -> str:
    # 严格 append-only：已有 ## 史记引文 节则不改动，避免丢失原有内容
    if '## 史记引文' in content:
        return content
    section = build_shiji_section(canonical, entry, para_index)
    # 插在 ## 相关页面 前，或末尾
    anchor = '## 相关页面'
    if anchor in content:
        idx = content.find(anchor)
        return content[:idx] + section + '\n' + content[idx:]
    return content.rstrip('\n') + '\n\n' + section + '\n'

# ── 调用 butler 脚本 ──────────────────────────────────────────────────────────
def run_add_page(canonical: str, page_content: str) -> bool:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md',
                                     encoding='utf-8', delete=False) as f:
        f.write(page_content); tmp = f.name
    result = subprocess.run(
        [sys.executable, str(ADD_PAGE), canonical, tmp,
         '--summary', f'butler/import-feudal-state: 新建邦国页面 {canonical}',
         '--author', 'butler'],
        capture_output=True, text=True)
    Path(tmp).unlink(missing_ok=True)
    if result.returncode != 0:
        print(f'  [!] add_page 错误: {result.stderr.strip()[:200]}')
    return result.returncode == 0

def run_edit_page(canonical: str, new_content: str) -> bool:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md',
                                     encoding='utf-8', delete=False) as f:
        f.write(new_content); tmp = f.name
    result = subprocess.run(
        [sys.executable, str(EDIT_PAGE), canonical, tmp,
         '--summary', f'butler/import-feudal-state: 更新史记引文 {canonical}',
         '--author', 'butler'],
        capture_output=True, text=True)
    Path(tmp).unlink(missing_ok=True)
    if result.returncode != 0:
        print(f'  [!] edit_page 错误: {result.stderr.strip()[:200]}')
    return result.returncode == 0

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    dry_run = '--dry-run' in sys.argv
    target  = next((a for a in sys.argv[1:] if not a.startswith('--')), None)

    print('1. 加载数据…')
    with open(INDEX_JSON, encoding='utf-8') as f:
        idx = json.load(f)
    fs_index = idx.get('feudal-state', {})

    with open(PAGES_JSON, encoding='utf-8') as f:
        pdata = json.load(f)
    direct_pages = set(pdata['pages'].keys())
    alias_index  = set(pdata.get('alias_index', {}).keys())
    all_wiki     = direct_pages | alias_index

    print('2. 构建段落索引…')
    para_index = build_para_index(CHAPTER_DIR)
    total_paras = sum(len(v) for v in para_index.values())
    print(f'   {len(para_index)} 章节，{total_paras} 段落')

    entities = {target: fs_index[target]} if target and target in fs_index \
               else fs_index

    created = updated = skipped = errors = 0

    for canonical, entry in entities.items():
        if canonical in alias_index and canonical not in direct_pages:
            skipped += 1
            continue  # 仅别名，跳过

        is_new = canonical not in all_wiki
        page_path = PAGES_DIR / f'{canonical}.md'

        if is_new:
            # 新建页面
            content = new_page_content(canonical, entry, para_index)
            if dry_run:
                print(f'\n=== 新建: {canonical} ({entry["count"]}处) ===')
                print(content[:600])
                created += 1
                continue
            ok = run_add_page(canonical, content)
            if ok:
                created += 1
                print(f'[+] {canonical} ({entry["count"]}处)')
            else:
                errors += 1
        else:
            # 更新已有页面
            if not page_path.exists():
                skipped += 1
                continue
            old = page_path.read_text(encoding='utf-8')
            new = update_page_content(old, canonical, entry, para_index)
            if new.strip() == old.strip():
                skipped += 1
                continue
            if dry_run:
                print(f'\n=== 更新: {canonical} ({entry["count"]}处) ===')
                idx_sec = new.find('## 史记引文')
                print(new[idx_sec:idx_sec + 600])
                updated += 1
                continue
            ok = run_edit_page(canonical, new)
            if ok:
                updated += 1
                print(f'[✓] {canonical} ({entry["count"]}处)')
            else:
                errors += 1

    print(f'\n完成: 新建 {created}，更新 {updated}，跳过 {skipped}，错误 {errors}')

if __name__ == '__main__':
    main()
