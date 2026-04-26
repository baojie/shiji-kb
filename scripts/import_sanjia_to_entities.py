#!/usr/bin/env python3
"""
import_sanjia_to_entities.py — 将三家注按锚点实体分发到对应的 wiki 页面。

算法：
1. 解析 chapter_md/NNN_*.tagged.md，建立"字符位置→最近实体"映射
2. 用 notes 的 before_context 在干净文本中定位锚点
3. 锚点处的最近实体即为 owner
4. 按 entity → notes 分组，追加到实体 wiki 页

无法定位实体的注释（章首总注、匹配失败等）→ 章节页 fallback

用法：
    python3 scripts/import_sanjia_to_entities.py           # 全部 130 章
    python3 scripts/import_sanjia_to_entities.py 001       # 只处理 001 章
    python3 scripts/import_sanjia_to_entities.py --dry-run 001  # 预览
    python3 scripts/import_sanjia_to_entities.py --stats 001    # 统计实体分布
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES_CACHE = ROOT / 'docs' / 'notes_cache'
CHAPTER_MD = ROOT / 'chapter_md'
PAGES = ROOT / 'wiki' / 'public' / 'pages'
EDIT_PAGE = ROOT / 'wiki' / 'scripts' / 'butler' / 'edit_page.py'
ADD_PAGE = ROOT / 'wiki' / 'scripts' / 'butler' / 'add_page.py'

# 只关注这些类型的实体（person, place, state, specific-title）
ENTITY_TYPES = set('@=&;')

SOURCE_LABELS = {'jijie': '集解', 'suoyin': '索隐', 'zhengyi': '正义'}


# ─────────────────────────────────────────────
# 1. 解析 tagged 文件，建立字符→实体映射
# ─────────────────────────────────────────────

def build_entity_map(tagged_text: str) -> tuple[str, dict[int, tuple[str, str]]]:
    """
    解析 tagged 文本，返回：
    - clean_text: 还原所有标注符号为纯文本
    - char_entity_map: {clean_pos: (entity_type, entity_name)}
      每个字符对应的"最近已见实体"

    tagged 格式规则：
    - 〖TYPE display|canonical〗 → 将 display 写入 clean text，实体 = canonical
    - 〖TYPE name〗              → 将 name 写入 clean text，实体 = name
    - 〘TYPE content〙           → content 写入 clean text（TYPE 是1个装饰字符）
    - ⟦TYPE content⟧            → content 写入 clean text
    - [N] / [N.N] / # 标题等  → 后处理剥除
    """
    clean_chars: list[str] = []
    last_entity: tuple[str, str] | None = None
    char_entity_map: dict[int, tuple[str, str]] = {}

    def add_chars(text: str, entity: tuple | None) -> None:
        for c in text:
            pos = len(clean_chars)
            if entity is not None:
                char_entity_map[pos] = entity
            clean_chars.append(c)

    # 按行处理，跳过 markdown 结构行（标题行 # 和分隔线 ---）
    # 行内的 [N] / [N.N] 前缀也需跳过
    # 这样 clean_chars 的位置与最终 clean_text 的位置完全对应

    LINE_NUM_RE = re.compile(r'^\[\d+[\.\d]*\]\s*')
    LIST_ITEM_RE = re.compile(r'^[\*\-]\s+')

    lines_raw = tagged_text.split('\n')
    for line_idx, line in enumerate(lines_raw):
        # 跳过 markdown 标题行
        stripped = line.strip()
        if stripped.startswith('#') or re.match(r'^-{3,}$', stripped):
            # 保留换行符以保持行偏移一致
            add_chars('\n', last_entity)
            continue

        # 去除行首 [N] / [N.N] 前缀
        m = LINE_NUM_RE.match(line)
        if m:
            line = line[m.end():]

        # 去除列表符号
        m2 = LIST_ITEM_RE.match(line)
        if m2:
            line = line[m2.end():]

        i = 0
        n_line = len(line)
        while i < n_line:
            ch = line[i]

            if ch == '〖':
                j = line.find('〗', i + 1)
                if j == -1:
                    add_chars(ch, last_entity)
                    i += 1
                    continue
                inner = line[i + 1:j]
                if inner:
                    type_ch = inner[0]
                    body = inner[1:]
                    parts = body.split('|', 1)
                    display = parts[0].strip()
                    canonical = parts[-1].strip()
                    if type_ch in ENTITY_TYPES:
                        last_entity = (type_ch, canonical)
                    add_chars(display, last_entity)
                i = j + 1

            elif ch == '〘':
                j = line.find('〙', i + 1)
                if j == -1:
                    add_chars(ch, last_entity)
                    i += 1
                    continue
                inner = line[i + 1:j]
                content = inner[1:] if len(inner) > 1 else inner
                add_chars(content, last_entity)
                i = j + 1

            elif ch == '⟦':
                j = line.find('⟧', i + 1)
                if j == -1:
                    add_chars(ch, last_entity)
                    i += 1
                    continue
                inner = line[i + 1:j]
                content = inner[1:] if len(inner) > 1 else inner
                add_chars(content, last_entity)
                i = j + 1

            elif ch in ('〙', '⟧'):
                i += 1

            else:
                add_chars(ch, last_entity)
                i += 1

        # 行末换行
        if line_idx < len(lines_raw) - 1:
            add_chars('\n', last_entity)

    raw_clean = ''.join(clean_chars)

    # 将 tagged 文件的半繁体 clean text 转为简体，与 notes_cache 对齐
    # opencc t2s 是 1:1 字符映射，不改变字符串长度，char_entity_map 位置不变
    try:
        from opencc import OpenCC
        _cc = OpenCC('t2s')
        clean = _cc.convert(raw_clean)
    except Exception:
        clean = raw_clean

    return clean, char_entity_map


def find_anchor_entity(
    note: dict,
    clean_text: str,
    char_entity_map: dict,
    window: int = 80,
) -> tuple[str, str] | None:
    """
    在 clean_text 中定位 note 的锚点，返回最近的实体 (type, name)。
    返回 None 表示无法定位。
    """
    bc = note.get('before_context', '')
    anchor = note.get('anchor_text', '')

    if not bc and not anchor:
        return None  # 章首总注，无实体

    # 去除 ... 前缀（before_context 最多 30 字，超出时截断）
    bc_clean = re.sub(r'^[\.…\[]+', '', bc).strip()

    # before_context 末尾即是 anchor_text，所以搜索整个 before_context
    # 若 before_context 太短（≤ 4字），用 anchor 定位会不准，加上 after_context
    search = bc_clean if len(bc_clean) >= 4 else bc_clean + note.get('after_context', '')[:6]
    if not search:
        return None

    # 在 clean_text 中搜索
    pos = clean_text.find(search)
    if pos == -1:
        # 尝试用后半段（10字）搜索
        search2 = bc_clean[-10:] if len(bc_clean) > 10 else bc_clean
        pos = clean_text.find(search2)
        if pos == -1:
            return None

    # 锚点位置 = pos + len(search) - len(anchor)
    anchor_pos = pos + len(search) - len(anchor)
    if anchor_pos < 0:
        anchor_pos = pos

    # 在 [anchor_pos - window, anchor_pos] 范围内找最近实体
    for p in range(anchor_pos, max(-1, anchor_pos - window), -1):
        if p in char_entity_map:
            return char_entity_map[p]

    return None


# ─────────────────────────────────────────────
# 2. 查找实体 wiki 页面
# ─────────────────────────────────────────────

_page_index: dict[str, Path] | None = None


def get_page_index() -> dict[str, Path]:
    global _page_index
    if _page_index is None:
        _page_index = {}
        for p in PAGES.glob('*.md'):
            slug = p.stem
            _page_index[slug] = p
    return _page_index


def find_entity_page(entity_name: str) -> Path | None:
    """查找实体对应的 wiki 页面（精确匹配 slug）。"""
    idx = get_page_index()
    p = idx.get(entity_name)
    if p is None:
        return None
    # 排除 redirect 页
    content = p.read_text(encoding='utf-8')
    if 'type: redirect' in content[:300]:
        # 尝试找 redirect 目标
        m = re.search(r'redirect_to:\s*(.+)', content)
        if m:
            target = m.group(1).strip().strip('"\'')
            return idx.get(target)
        return None
    return p


# ─────────────────────────────────────────────
# 3. 格式化单条注释
# ─────────────────────────────────────────────

def format_note_block(note: dict, chapter_ref: str) -> str:
    """将单条注释格式化为 wiki markdown 块。"""
    note_id = note.get('id', '')
    bc = note.get('before_context', '').lstrip('.…[').strip()
    anchor = note.get('anchor_text', '').strip()
    ac = note.get('after_context', '')[:20]
    items = note.get('items', [])

    # 上下文展示
    if bc or anchor:
        context = f'「……{bc[-15:]}**{anchor}**{ac}……」' if bc else f'「**{anchor}**{ac}」'
    else:
        context = '（篇首总注）'

    lines = [f'##### {note_id} · {context}（出自[[{chapter_ref}]]）', '']
    for item in items:
        label = SOURCE_LABELS.get(item['source'], item['label'])
        lines.append(f'> **【{label}】** {item["text"].strip()}')
        lines.append('>')
    if lines and lines[-1] == '>':
        lines.pop()
    lines.append('')
    return '\n'.join(lines)


def build_entity_sanjia_section(
    entity_name: str,
    notes_with_chapters: list[tuple[dict, str]],
) -> str:
    """构建要追加到实体页的三家注 markdown 内容。"""
    lines = [
        '## 三家注',
        '',
        f'以下是《史记》三家注中直接注释「{entity_name}」相关文字的条目。',
        '',
    ]
    # 按章节分组
    by_chapter: dict[str, list[dict]] = defaultdict(list)
    chapter_order: list[str] = []
    for note, chap in notes_with_chapters:
        if chap not in by_chapter:
            chapter_order.append(chap)
        by_chapter[chap].append(note)

    for chap in chapter_order:
        lines.append(f'#### 出自 [[{chap}]]')
        lines.append('')
        for note in by_chapter[chap]:
            note_id = note.get('id', '')
            bc = note.get('before_context', '').lstrip('.…[').strip()
            anchor = note.get('anchor_text', '').strip()
            ac = note.get('after_context', '')[:20]
            context = f'「……{bc[-15:]}**{anchor}**{ac}……」' if bc else '（篇首总注）'

            lines.append(f'##### {note_id} · {context}')
            lines.append('')
            for item in note.get('items', []):
                label = SOURCE_LABELS.get(item['source'], item['label'])
                lines.append(f'> **【{label}】** {item["text"].strip()}')
                lines.append('>')
            if lines and lines[-1] == '>':
                lines.pop()
            lines.append('')

    return '\n'.join(lines)


def append_notes_to_page(
    page_path: Path,
    entity_name: str,
    notes_with_chapters: list[tuple[dict, str]],
    dry_run: bool,
) -> str:
    """将三家注追加到页面，返回状态信息。"""
    content = page_path.read_text(encoding='utf-8')

    if '## 三家注' in content:
        # append-only: 已有节则跳过
        return f'[{entity_name}] 跳过：已有三家注节'

    new_section = build_entity_sanjia_section(entity_name, notes_with_chapters)
    new_content = content.rstrip() + '\n\n' + new_section + '\n'
    count = len(notes_with_chapters)

    if dry_run:
        return f'[{entity_name}] DRY-RUN: 追加 {count} 条注释 → {page_path.name}'

    slug = page_path.stem
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', encoding='utf-8', delete=False
    ) as tmp:
        tmp.write(new_content)
        tmp_path = tmp.name

    result = subprocess.run(
        [
            sys.executable, str(EDIT_PAGE),
            slug, tmp_path,
            '--summary', f'sanjia-entity: 追加三家注 {count} 条',
            '--author', 'butler',
        ],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    Path(tmp_path).unlink(missing_ok=True)

    if result.returncode != 0:
        return f'[{entity_name}] 错误: {result.stderr.strip()[:100]}'
    return f'[{entity_name}] 完成: {page_path.name}，{count} 条'


def create_entity_page(
    entity_name: str,
    entity_type: str,
    notes_with_chapters: list[tuple[dict, str]],
    dry_run: bool,
) -> str:
    """为无页面的实体新建 stub 页面。"""
    type_map = {'@': 'person', '=': 'place', '&': 'state', ';': 'role'}
    page_type = type_map.get(entity_type, 'person')
    count = len(notes_with_chapters)

    new_section = build_entity_sanjia_section(entity_name, notes_with_chapters)
    new_content = f"""---
id: {entity_name}
type: {page_type}
label: {entity_name}
aliases: [{entity_name}]
sources: []
tags: [史记]
auto_generated: true
quality: stub
---

# {entity_name}

{new_section}
"""

    if dry_run:
        return f'[{entity_name}] DRY-RUN: 新建页面 {entity_name}.md，含 {count} 条'

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', encoding='utf-8', delete=False
    ) as tmp:
        tmp.write(new_content)
        tmp_path = tmp.name

    result = subprocess.run(
        [
            sys.executable, str(ADD_PAGE),
            entity_name, tmp_path,
            '--summary', f'sanjia-entity: 新建实体页并导入三家注 {count} 条',
            '--author', 'butler',
        ],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    Path(tmp_path).unlink(missing_ok=True)

    if result.returncode != 0:
        return f'[{entity_name}] 错误(新建): {result.stderr.strip()[:100]}'
    return f'[{entity_name}] 完成（新建）: {entity_name}.md，{count} 条'


# ─────────────────────────────────────────────
# 4. 处理单章
# ─────────────────────────────────────────────

def find_tagged_file(num: str) -> Path | None:
    candidates = list(CHAPTER_MD.glob(f'{num}_*.tagged.md'))
    return candidates[0] if candidates else None


def find_chapter_page(num: str) -> Path | None:
    """找章节页（排除 redirect）。"""
    for p in sorted(PAGES.glob(f'{num}_*.md')):
        content = p.read_text(encoding='utf-8')
        if 'type: redirect' not in content[:300]:
            return p
    return None


def get_chapter_label(num: str) -> str:
    """从章节页获取章节名。"""
    p = find_chapter_page(num)
    if p:
        return p.stem  # e.g., "001_五帝本纪"
    return f'{num}_未知章节'


def process_chapter(
    num: str,
    dry_run: bool = False,
    stats_only: bool = False,
) -> dict:
    """
    处理单章，返回统计信息。
    """
    result = {'chapter': num, 'total': 0, 'mapped': 0, 'fallback': 0, 'entities': {}}

    notes_file = NOTES_CACHE / f'{num}-notes.json'
    if not notes_file.exists():
        return result

    with notes_file.open(encoding='utf-8') as f:
        notes_data = json.load(f)
    notes = notes_data.get('notes', [])
    if not notes:
        return result

    result['total'] = len(notes)
    chapter_label = get_chapter_label(num)

    tagged_file = find_tagged_file(num)
    if not tagged_file:
        # 无 tagged 文件，全部 fallback 到章节页
        result['fallback'] = len(notes)
        return result

    tagged_text = tagged_file.read_text(encoding='utf-8')
    clean_text, char_entity_map = build_entity_map(tagged_text)

    # 按实体分组 notes
    entity_notes: dict[tuple[str, str], list[dict]] = defaultdict(list)
    fallback_notes: list[dict] = []

    for note in notes:
        entity = find_anchor_entity(note, clean_text, char_entity_map)
        if entity:
            entity_notes[entity].append(note)
            result['mapped'] += 1
        else:
            fallback_notes.append(note)
            result['fallback'] += 1

    result['entities'] = {f'{t}{n}': len(ns) for (t, n), ns in entity_notes.items()}

    if stats_only:
        return result

    # 写入各实体页
    for (etype, ename), enotes in entity_notes.items():
        notes_with_chapters = [(n, chapter_label) for n in enotes]
        page = find_entity_page(ename)

        if page:
            msg = append_notes_to_page(page, ename, notes_with_chapters, dry_run)
        else:
            # 实体无对应页面：仅为 @ 和 = 类型创建 stub
            if etype in ('@', '=') and len(enotes) >= 2:
                msg = create_entity_page(ename, etype, notes_with_chapters, dry_run)
            else:
                msg = f'[{ename}] 跳过：无页面且注释少于2条'

        print(f'  {msg}')

    # Fallback：章节总注等写入章节页
    if fallback_notes:
        chapter_page = find_chapter_page(num)
        if chapter_page:
            content = chapter_page.read_text(encoding='utf-8')
            if '## 三家注' not in content:
                section = _build_fallback_section(fallback_notes)
                new_content = content.rstrip() + '\n\n' + section + '\n'
                if not dry_run:
                    slug = chapter_page.stem
                    with tempfile.NamedTemporaryFile(
                        mode='w', suffix='.md', encoding='utf-8', delete=False
                    ) as tmp:
                        tmp.write(new_content)
                        tmp_path = tmp.name
                    subprocess.run(
                        [
                            sys.executable, str(EDIT_PAGE),
                            slug, tmp_path,
                            '--summary', f'sanjia-fallback: 章节总注 {len(fallback_notes)} 条',
                            '--author', 'butler',
                        ],
                        capture_output=True, cwd=str(ROOT)
                    )
                    Path(tmp_path).unlink(missing_ok=True)
                print(f'  [{chapter_label}] fallback: {len(fallback_notes)} 条写入章节页')

    return result


def _build_fallback_section(notes: list[dict]) -> str:
    lines = [
        '## 三家注',
        '',
        '以下注释为章首总注或无法定位到具体实体的注释。',
        '',
    ]
    for note in notes:
        note_id = note.get('id', '')
        bc = note.get('before_context', '').lstrip('.…[').strip()
        anchor = note.get('anchor_text', '').strip()
        context = f'「……{bc[-15:]}**{anchor}**……」' if bc else '（篇首总注）'
        lines.append(f'#### {note_id} · {context}')
        lines.append('')
        for item in note.get('items', []):
            label = SOURCE_LABELS.get(item['source'], item['label'])
            lines.append(f'> **【{label}】** {item["text"].strip()}')
            lines.append('>')
        if lines and lines[-1] == '>':
            lines.pop()
        lines.append('')
    return '\n'.join(lines)


# ─────────────────────────────────────────────
# 5. 入口
# ─────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description='将三家注按实体分发到 wiki 页面')
    ap.add_argument('chapters', nargs='*', help='章节编号，不填则全部')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--stats', action='store_true', help='只打印统计，不写入')
    args = ap.parse_args()

    if args.chapters:
        nums = [c.zfill(3) for c in args.chapters]
    else:
        nums = sorted(
            p.stem.replace('-notes', '')
            for p in NOTES_CACHE.glob('*-notes.json')
            if 'index' not in p.stem
        )

    total_notes = 0
    total_mapped = 0
    total_fallback = 0

    for num in nums:
        print(f'\n── 第 {num} 章 ──')
        r = process_chapter(num, dry_run=args.dry_run, stats_only=args.stats)
        if r['total'] == 0:
            print('  （无数据）')
            continue
        pct = r['mapped'] * 100 // r['total'] if r['total'] else 0
        print(f'  总计 {r["total"]} 条：实体匹配 {r["mapped"]}（{pct}%），fallback {r["fallback"]}')
        if args.stats and r['entities']:
            top = sorted(r['entities'].items(), key=lambda x: -x[1])[:5]
            print(f'  实体 Top5: {top}')
        total_notes += r['total']
        total_mapped += r['mapped']
        total_fallback += r['fallback']

    print(f'\n═══ 汇总 ═══')
    pct = total_mapped * 100 // total_notes if total_notes else 0
    print(f'总注释: {total_notes}，实体匹配: {total_mapped}（{pct}%），fallback: {total_fallback}')


if __name__ == '__main__':
    main()
