#!/usr/bin/env python3
"""backfill_recent.py — 为未记录到 recent.jsonl 的页面补录修订历史。

扫描 wiki/public/pages/*.md，找出 mtime 晚于 recent.jsonl 最后一行时间戳的文件，
对每个文件调用 record_revision.py（使用文件的 mtime 作为 --timestamp）。

用法：
  python3 wiki/scripts/butler/backfill_recent.py [--dry-run]
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES = ROOT / 'wiki' / 'public' / 'pages'
RECENT = ROOT / 'wiki' / 'public' / 'recent.jsonl'
RECORD_REV = ROOT / 'wiki' / 'scripts' / 'butler' / 'record_revision.py'

TZ_CST = timezone(timedelta(hours=8))


def last_recent_ts() -> float:
    """返回 recent.jsonl 最后一行的 mtime（秒），用于比较。"""
    return RECENT.stat().st_mtime


def file_mtime_iso(p: Path) -> str:
    """返回文件 mtime 的 ISO-8601 字符串（UTC）。"""
    ts = p.stat().st_mtime
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='只打印，不写入')
    args = ap.parse_args()

    cutoff = last_recent_ts()
    cutoff_dt = datetime.fromtimestamp(cutoff, tz=timezone.utc)
    print(f'[backfill] recent.jsonl 截止时间: {cutoff_dt.astimezone(TZ_CST).strftime("%Y-%m-%d %H:%M:%S")} CST')

    candidates = sorted(
        (p for p in PAGES.glob('*.md') if p.stat().st_mtime > cutoff),
        key=lambda p: p.stat().st_mtime,
    )
    print(f'[backfill] 发现 {len(candidates)} 个需要补录的文件')

    for md in candidates:
        slug = md.stem
        ts = file_mtime_iso(md)
        print(f'  {"[DRY]" if args.dry_run else "[REC]"} {slug}  ({ts})')
        if args.dry_run:
            continue
        result = subprocess.run(
            [sys.executable, str(RECORD_REV), slug,
             '--summary', 'butler/backfill: 补录缺失修订记录',
             '--author', 'butler',
             '--timestamp', ts],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f'       ✓ {result.stdout.strip()}')
        else:
            print(f'       ✗ {result.stderr.strip()}', file=sys.stderr)


if __name__ == '__main__':
    main()
