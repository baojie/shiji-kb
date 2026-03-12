#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将十表（013-022章）事件索引中 `段落位置: 表（X）` 格式
更新为 `段落位置: r{N}` 格式，使事件能链接到对应表格行的 Purple Number。

匹配策略：
1. 从 MD 源文件解析各行（含 [rN] 标记），构建行号→行内容映射
2. 从 `表（X）` 提取关键词，在所有行列中模糊匹配
3. 找到唯一最佳匹配则更新；多个匹配取第一个；无匹配则保留原值

运行：
    python scripts/update_table_event_links.py           # 处理全部10章
    python scripts/update_table_event_links.py 020       # 只处理020章
    python scripts/update_table_event_links.py --dry-run # 预览不写入
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHAPTER_DIR = ROOT / 'chapter_md'
EVENTS_DIR = ROOT / 'kg' / 'events' / 'data'

TEN_TABLE_CHAPTERS = [
    '013', '014', '015', '016', '017',
    '018', '019', '020', '021', '022',
]


def strip_annotations(text: str) -> str:
    """去除标注符号，获取纯文字内容"""
    text = re.sub(r'[@=\$%&\^~\*!]([^@=\$%&\^~\*!\n]{0,40}?)[@=\$%&\^~\*!]', r'\1', text)
    text = re.sub(r'〘([^〘〙\n]{0,40}?)〙', r'\1', text)
    text = re.sub(r'〚([^〚〛\n]{0,40}?)〛', r'\1', text)
    return text


def parse_row_cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c.strip() for c in s.split('|')]


def build_row_map(md_path: Path) -> list[tuple[int, str, list[str]]]:
    """
    解析 MD 文件中的表格，返回 [(row_num, first_cell_plain, all_cells_plain), ...]
    """
    rows = []
    text = md_path.read_text(encoding='utf-8')
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if not (line.strip().startswith('|') and '|' in line.strip()[1:]):
            i += 1
            continue
        # 收集连续表格行
        table_lines = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            table_lines.append(lines[i].strip())
            i += 1
        if len(table_lines) < 2:
            continue
        # 跳过表头和分隔行
        data_start = 1
        if len(table_lines) > 1 and re.match(r'^[\s|:-]+$', table_lines[1].replace('-', '')):
            data_start = 2
        for row_line in table_lines[data_start:]:
            cells = parse_row_cells(row_line)
            if not cells:
                continue
            # 提取 [rN]
            m = re.match(r'^\s*\[r(\d+)\]\s*', cells[0])
            if not m:
                continue
            row_num = int(m.group(1))
            # 去掉 [rN] 后提取纯文本
            first_cell = strip_annotations(cells[0][m.end():]).strip(' \t。．')
            all_cells = [strip_annotations(c).strip() for c in cells]
            rows.append((row_num, first_cell, all_cells))
    return rows


def extract_search_terms(raw: str) -> list[str]:
    """
    从 `表（X）` 中提取关键词列表（按优先级从高到低）。
    例：
      "前350年" → ["前350", "350"]
      "长平条目" → ["长平"]
      "前209年九月" → ["前209", "209"]
      "多条目，元朔五年" → ["元朔五", "元朔"]
      "表" → []
    """
    # 去掉"条目"、"年"后缀
    s = raw.strip()
    s = re.sub(r'条目$', '', s)

    terms = []

    # 年份 "前NNN"
    m = re.search(r'前(\d+)', s)
    if m:
        terms.append(f'前{m.group(1)}')
        terms.append(m.group(1))
        return terms

    # 纯数字年份
    m = re.search(r'(\d+)', s)
    if m:
        terms.append(m.group(1))
        return terms

    # 多条目：提取逗号前的主词
    parts = re.split(r'[，,、]', s)
    for p in parts:
        p = p.strip()
        if p and p not in ('多', '多条目'):
            # 取前 4 个字
            terms.append(p[:4])
            if len(p) > 2:
                terms.append(p[:2])

    return [t for t in terms if t]


def find_row(search_terms: list[str], row_map: list[tuple]) -> int | None:
    """在行映射中查找第一个匹配的行号"""
    if not search_terms:
        return None
    for term in search_terms:
        if not term:
            continue
        matches = []
        for row_num, first_cell, all_cells in row_map:
            content = ' '.join(all_cells)
            if term in content:
                matches.append(row_num)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            # 优先找第一列匹配
            for row_num, first_cell, _ in row_map:
                if term in first_cell:
                    return row_num
            return matches[0]
    return None


def update_event_index(events_path: Path, row_map: list[tuple],
                       dry_run: bool = False) -> tuple[int, int]:
    """更新事件索引文件，返回 (updated, skipped)"""
    text = events_path.read_text(encoding='utf-8')
    lines = text.split('\n')
    new_lines = []
    updated = skipped = 0

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith('- **段落位置**'):
            new_lines.append(line)
            continue

        # 已经是 r{N} 格式 → 跳过
        if re.search(r'\br\d+\b', stripped):
            new_lines.append(line)
            continue

        # 已经是 [N.N] 格式的普通段落引用 → 跳过
        if re.search(r'\[\d+[\.\d]*\]', stripped):
            new_lines.append(line)
            continue

        # 提取 表（X） 或 单独"表"
        m = re.search(r'表（([^）]*)）|：\s*表\s*$', stripped)
        if not m:
            new_lines.append(line)
            continue

        inner = m.group(1) if m.group(1) is not None else ''
        terms = extract_search_terms(inner)
        row_num = find_row(terms, row_map)

        if row_num is not None:
            # 替换段落位置值
            indent = line[:len(line) - len(line.lstrip())]
            new_line = f'{indent}- **段落位置**: r{row_num}'
            new_lines.append(new_line)
            updated += 1
            if dry_run:
                print(f"  {events_path.name}: '{stripped}' → r{row_num} (terms={terms})")
        else:
            new_lines.append(line)
            skipped += 1
            if dry_run:
                print(f"  {events_path.name}: [NO MATCH] '{stripped}' (terms={terms})")

    if not dry_run and updated:
        events_path.write_text('\n'.join(new_lines), encoding='utf-8')

    return updated, skipped


def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    targets = [a for a in args if a != '--dry-run'] or TEN_TABLE_CHAPTERS

    total_updated = total_skipped = 0

    for prefix in targets:
        md_files = sorted(CHAPTER_DIR.glob(f'{prefix}_*.tagged.md'))
        ev_files = sorted(EVENTS_DIR.glob(f'{prefix}_*事件索引.md'))
        if not md_files or not ev_files:
            print(f'警告：未找到 {prefix} 的 MD 或事件索引文件')
            continue

        md_path = md_files[0]
        ev_path = ev_files[0]

        row_map = build_row_map(md_path)
        print(f'\n{prefix}: {len(row_map)} 行 → {ev_path.name}')

        upd, skip = update_event_index(ev_path, row_map, dry_run=dry_run)
        print(f'  更新 {upd} 条，跳过（无匹配） {skip} 条')
        total_updated += upd
        total_skipped += skip

    print(f'\n总计：更新 {total_updated} 条，跳过 {total_skipped} 条')


if __name__ == '__main__':
    main()
