#!/usr/bin/env python3
"""
record_revision.py — 为 wiki/public/pages/<page>.md 写入一条修订记录.

用法:
    python3 wiki/scripts/butler/record_revision.py <slug> \
        [--summary "butler/<action>: ..."] \
        [--author butler]

产出:
    1. wiki/public/history/<slug>.jsonl         (per-page 索引, JSONL 正序，末行最新, flock 保护)
    2. wiki/public/recent.jsonl                 (全局修订日志, 滚动窗口 JSONL，每行一条)
    3. wiki/logs/recent/recent.N.jsonl          (归档批次, 永久保留)

rev_id 格式: YYYYMMDD-HHMMSS-<sha256[:6]>  (北京时间)

butler 原子动作结束时应调用本脚本, 让 #?recent / #?history=<page> 视图可见.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / 'wiki/public'
PAGES = PUBLIC / 'pages'
HIST = PUBLIC / 'history'
RECENT = PUBLIC / 'recent.jsonl'
LOG_DIR = ROOT / 'wiki/logs/recent'

TZ_UTC = timezone.utc

WINDOW_SIZE = 1000   # recent.jsonl 最多存 1000 行
ARCHIVE_BATCH = 500  # 每次归档最旧的 500 条


def iso_utc(dt: datetime) -> str:
    s = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
    if s.endswith('+0000'):
        return s[:-5] + 'Z'
    return s[:-2] + ':' + s[-2:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('page', help='slug (without .md)')
    ap.add_argument('--summary', default='', help='修订说明')
    ap.add_argument('--author', default='butler')
    ap.add_argument('--action', default='edit',
                    choices=['edit', 'delete'],
                    help='edit（默认）或 delete（删除前调用，留快照）')
    ap.add_argument('--timestamp', default=None,
                    help='ISO 时间 (默认现在). 用于补录历史.')
    args = ap.parse_args()

    page = args.page
    src = PAGES / f'{page}.md'
    if not src.exists():
        print(f'✗ {src} 不存在', file=sys.stderr)
        return 1

    content = src.read_text(encoding='utf-8')
    sha = hashlib.sha256(content.encode('utf-8')).hexdigest()

    if args.timestamp:
        now = datetime.fromisoformat(args.timestamp)
        if now.tzinfo is None:
            now = now.replace(tzinfo=TZ_UTC)
        now = now.astimezone(TZ_UTC)
    else:
        now = datetime.now(TZ_UTC)

    rev_id = f'{now.strftime("%Y%m%d-%H%M%S")}-{sha[:6]}'
    ts_iso = iso_utc(now)

    # ── per-page history (JSONL 正序，末行最新，flock 排他锁) ────────────────
    HIST.mkdir(exist_ok=True)
    page_jsonl = HIST / f'{page}.jsonl'

    with page_jsonl.open('a+', encoding='utf-8') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        entries = []
        for ln in lines:
            try:
                entries.append(json.loads(ln))
            except json.JSONDecodeError:
                pass

        # 去重：末行（最新）content_hash 相同则跳过
        if entries and entries[-1].get('content_hash') == f'sha256:{sha}':
            print(f'= {page} 内容与 latest 相同 (hash {sha[:6]}), 跳过')
            return 0

        last = entries[-1] if entries else None
        parent_rev = last['rev_id'] if last else None
        size_before = last['size'] if last else 0
        size_after = len(content.encode('utf-8'))

        entry = {
            'rev_id': rev_id,
            'timestamp': ts_iso,
            'author': args.author,
            'summary': args.summary or f'{args.author} edit',
            'parent_rev': parent_rev,
            'content_hash': f'sha256:{sha}',
            'size_before': size_before,
            'size': size_after,
            'content': content,
        }
        if args.action == 'delete':
            entry['action'] = 'delete'

        fh.seek(0, 2)
        fh.write(json.dumps(entry, ensure_ascii=False) + '\n')

    # ── recent.jsonl（滚动窗口，超出后归档）────────────────────────────────
    RECENT.parent.mkdir(exist_ok=True)
    if RECENT.exists():
        raw_lines = RECENT.read_text(encoding='utf-8').splitlines()
        recent_entries = []
        for ln in raw_lines:
            ln = ln.strip()
            if ln:
                recent_entries.append(json.loads(ln))
    else:
        recent_entries = []

    new_entry = {'page': page, **{k: v for k, v in entry.items() if k != 'content'}}
    recent_entries.append(new_entry)

    if len(recent_entries) > WINDOW_SIZE:
        batch = recent_entries[:ARCHIVE_BATCH]
        recent_entries = recent_entries[ARCHIVE_BATCH:]
        LOG_DIR.mkdir(exist_ok=True)
        existing = [int(p.stem.split('.')[1]) for p in LOG_DIR.glob('recent.*.jsonl')
                    if p.stem.split('.')[1].isdigit()]
        rotations = max(existing) + 1 if existing else 1
        archive_lines = '\n'.join(json.dumps(e, ensure_ascii=False) for e in batch) + '\n'
        (LOG_DIR / f'recent.{rotations}.jsonl').write_text(archive_lines, encoding='utf-8')
        print(f'  [archive] {len(batch)} entries → wiki/logs/recent/recent.{rotations}.jsonl')

    RECENT.write_text(
        '\n'.join(json.dumps(e, ensure_ascii=False) for e in recent_entries) + '\n',
        encoding='utf-8',
    )

    delta = size_after - size_before
    delta_str = f'+{delta}' if delta >= 0 else str(delta)
    verb = ' (deleted)' if args.action == 'delete' else ''
    print(f'✓ {page} rev={rev_id} size={size_before}→{size_after}({delta_str}) author={args.author}{verb}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
