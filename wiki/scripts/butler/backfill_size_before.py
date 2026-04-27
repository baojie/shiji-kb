#!/usr/bin/env python3
"""
backfill_size_before.py — 为所有修订记录补全缺失的 size_before 字段。

处理三类文件：
  1. wiki/public/history/*.jsonl  (per-page 修订历史，JSONL 正序末行最新)
  2. wiki/public/recent.jsonl     (滚动窗口)
  3. wiki/logs/recent/*.jsonl     (归档批次)

JSONL 按时间正序存储（最旧在首行），revisions[i] 的 parent 是 revisions[i-1]。
第一版（最旧）没有 parent，size_before = 0。

用法:
    python3 wiki/scripts/butler/backfill_size_before.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HIST = ROOT / 'wiki/public/history'
RECENT = ROOT / 'wiki/public/recent.jsonl'
LOG_DIR = ROOT / 'wiki/logs/recent'


def backfill_file(path: Path, dry_run: bool) -> tuple[int, int]:
    """返回 (总修订数, 补全数)。处理 JSONL 格式（正序，末行最新）。"""
    lines = [ln for ln in path.read_text(encoding='utf-8').splitlines() if ln.strip()]
    if not lines:
        return 0, 0

    revs = [json.loads(ln) for ln in lines]
    # JSONL 正序（最旧在首行），revs[i] 的 parent 是 revs[i-1]
    changed = 0
    for i, rev in enumerate(revs):
        if 'size_before' in rev:
            continue
        parent_size = revs[i - 1].get('size', 0) if i > 0 else 0
        rev['size_before'] = parent_size
        changed += 1

    if changed and not dry_run:
        path.write_text(
            '\n'.join(json.dumps(r, ensure_ascii=False) for r in revs) + '\n',
            encoding='utf-8',
        )

    return len(revs), changed


def backfill_recent(rev_map: dict[str, int], dry_run: bool) -> tuple[int, int]:
    """为 recent.jsonl 的 entries 补全 size_before。"""
    if not RECENT.exists():
        return 0, 0

    raw_lines = RECENT.read_text(encoding='utf-8').splitlines()
    entries = []
    for ln in raw_lines:
        ln = ln.strip()
        if ln:
            entries.append(json.loads(ln))

    changed = 0
    for e in entries:
        if 'size_before' in e:
            continue
        rev_id = e.get('rev_id', '')
        if rev_id in rev_map:
            e['size_before'] = rev_map[rev_id]
            changed += 1

    if changed and not dry_run:
        RECENT.write_text(
            '\n'.join(json.dumps(e, ensure_ascii=False) for e in entries) + '\n',
            encoding='utf-8'
        )

    return len(entries), changed


def build_rev_map() -> dict[str, int]:
    """从已更新的 per-page history JSONL 建立 rev_id -> size_before 映射。"""
    rev_map: dict[str, int] = {}
    for f in HIST.glob('*.jsonl'):
        for ln in f.read_text(encoding='utf-8').splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                rev = json.loads(ln)
            except json.JSONDecodeError:
                continue
            rev_id = rev.get('rev_id', '')
            if rev_id and 'size_before' in rev:
                rev_map[rev_id] = rev['size_before']
    return rev_map


def backfill_jsonl(path: Path, rev_map: dict[str, int], dry_run: bool) -> tuple[int, int]:
    """为单个 .jsonl 归档文件补全 size_before。"""
    lines = path.read_text(encoding='utf-8').splitlines()
    changed = 0
    out_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            out_lines.append(line)
            continue
        entry = json.loads(line)
        if 'size_before' not in entry:
            rev_id = entry.get('rev_id', '')
            if rev_id in rev_map:
                entry['size_before'] = rev_map[rev_id]
                changed += 1
        out_lines.append(json.dumps(entry, ensure_ascii=False))
    if changed and not dry_run:
        path.write_text('\n'.join(out_lines) + '\n', encoding='utf-8')
    return len(lines), changed


def main() -> int:
    ap = argparse.ArgumentParser(description='为历史 revision 补全 size_before 字段')
    ap.add_argument('--dry-run', action='store_true', help='只统计，不写入')
    args = ap.parse_args()

    files = sorted(HIST.glob('*.jsonl'))
    print(f'扫描 {len(files)} 个 history JSONL...')

    total_revs = 0
    total_changed = 0
    for f in files:
        t, c = backfill_file(f, args.dry_run)
        total_revs += t
        total_changed += c

    print(f'per-page history: {total_revs} 条修订，补全 {total_changed} 条 size_before')

    print('建立 rev_id → size_before 映射...')
    rev_map = build_rev_map()
    print(f'  映射表 {len(rev_map)} 条')

    re_total, re_changed = backfill_recent(rev_map, args.dry_run)
    print(f'recent.jsonl: {re_total} 条 entries，补全 {re_changed} 条 size_before')

    jsonl_files = sorted(LOG_DIR.glob('recent.*.jsonl')) if LOG_DIR.exists() else []
    print(f'扫描 {len(jsonl_files)} 个 logs/recent/*.jsonl...')
    jl_total = 0
    jl_changed = 0
    for f in jsonl_files:
        t, c = backfill_jsonl(f, rev_map, args.dry_run)
        jl_total += t
        jl_changed += c
    print(f'logs/recent/*.jsonl: {jl_total} 条 entries，补全 {jl_changed} 条 size_before')

    if args.dry_run:
        print('[dry-run] 未写入任何文件')
    else:
        print('完成。')

    return 0


if __name__ == '__main__':
    sys.exit(main())
