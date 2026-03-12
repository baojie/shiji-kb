#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为史记十表（013-022章）的 Markdown 源文件中的每个表格数据行，
在第一列首部插入 Purple Number 标记 [rN]（章内全局递增，跨表连续）。

运行：
    python scripts/add_table_row_pn.py          # 处理全部10章
    python scripts/add_table_row_pn.py 020       # 只处理020章
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHAPTER_DIR = ROOT / 'chapter_md'

TEN_TABLE_CHAPTERS = [
    '013', '014', '015', '016', '017',
    '018', '019', '020', '021', '022',
]


def parse_table_row(line: str) -> list[str]:
    """将 | a | b | c | 解析为单元格列表（保留首尾空格）"""
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return s.split('|')


def is_separator_row(line: str) -> bool:
    """判断是否为分隔行（| --- | --- | ...）"""
    return bool(re.match(r'^[\s|:-]+$', line.strip().replace('-', '')))


def already_has_row_pn(first_cell: str) -> bool:
    """检查第一列是否已有 [rN] 标记"""
    return bool(re.match(r'^\s*\[r\d+\]', first_cell))


def add_row_pn_to_file(md_path: Path, dry_run: bool = False) -> int:
    """处理单个文件，返回修改的行数"""
    text = md_path.read_text(encoding='utf-8')
    lines = text.split('\n')
    result = []
    counter = [0]  # 章内全局行号，跨表连续
    modified = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        # 检测表格起始行
        if line.strip().startswith('|') and '|' in line.strip()[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1

            if len(table_lines) < 2:
                result.extend(table_lines)
                continue

            # 确定表头行数和数据起始行
            data_start = 1
            if len(table_lines) > 1 and is_separator_row(table_lines[1]):
                data_start = 2

            # 表头和分隔行原样输出
            for j in range(data_start):
                result.append(table_lines[j])

            # 数据行：在第一列首部插入 [rN]
            for row_line in table_lines[data_start:]:
                cells = parse_table_row(row_line)
                if not cells:
                    result.append(row_line)
                    continue

                if already_has_row_pn(cells[0]):
                    # 已有标记，跳过（但仍计数）
                    existing = re.match(r'^\s*\[r(\d+)\]', cells[0])
                    if existing:
                        counter[0] = int(existing.group(1))
                    result.append(row_line)
                    continue

                counter[0] += 1
                n = counter[0]
                # 在第一列内容前插入 [rN]（保留原始前导空格）
                first_cell = cells[0]
                leading = ''
                stripped = first_cell.lstrip()
                leading = first_cell[:len(first_cell) - len(stripped)]
                cells[0] = f'{leading}[r{n}] {stripped}'

                # 重组行（保留原始边界 |）
                original = row_line.rstrip()
                has_trailing = original.endswith('|')
                new_row = '| ' + ' | '.join(cells) + (' |' if has_trailing else '')
                result.append(new_row)
                modified += 1
        else:
            result.append(line)
            i += 1

    new_text = '\n'.join(result)
    if new_text != text:
        if not dry_run:
            md_path.write_text(new_text, encoding='utf-8')
        print(f"  {'[dry-run] ' if dry_run else ''}修改 {modified} 行: {md_path.name}")
    else:
        print(f"  已跳过（无变更）: {md_path.name}")

    return modified


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else TEN_TABLE_CHAPTERS
    dry_run = '--dry-run' in targets
    if dry_run:
        targets = [t for t in targets if t != '--dry-run']
    if not targets:
        targets = TEN_TABLE_CHAPTERS

    total = 0
    for prefix in targets:
        matches = sorted(CHAPTER_DIR.glob(f'{prefix}_*.tagged.md'))
        if not matches:
            print(f"警告：未找到章节 {prefix}")
            continue
        for md_path in matches:
            n = add_row_pn_to_file(md_path, dry_run=dry_run)
            total += n

    print(f"\n完成。共修改 {total} 行表格数据行。")


if __name__ == '__main__':
    main()
