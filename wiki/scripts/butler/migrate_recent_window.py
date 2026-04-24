#!/usr/bin/env python3
"""
migrate_recent_window.py — 迁移 recent.json 到滚动窗口设计.

将所有 wiki/logs/recent/recent.N.json + recent.json 中的条目合并后：
  - 最近 WINDOW_SIZE 条保留在 recent.json（滚动窗口）
  - 较旧的条目重新打包到 wiki/logs/recent/recent.1.json ... recent.M.json
    （每档 ARCHIVE_BATCH 条，按时间从旧到新编号）

执行前会打印预览；加 --run 才真正写入。
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / 'wiki/public'
RECENT = PUBLIC / 'recent.json'
LOG_DIR = ROOT / 'wiki/logs/recent'

WINDOW_SIZE = 600
ARCHIVE_BATCH = 100


def load_entries():
    """读取所有条目，按时间升序（最旧在前）返回。"""
    files = sorted(
        LOG_DIR.glob('recent.*.json'),
        key=lambda p: int(p.stem.split('.')[1])
    )
    all_entries = []
    for f in files:
        d = json.loads(f.read_text(encoding='utf-8'))
        all_entries.extend(d.get('entries', []))

    if RECENT.exists():
        d = json.loads(RECENT.read_text(encoding='utf-8'))
        all_entries.extend(d.get('entries', []))

    return all_entries


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', action='store_true', help='真正写入（否则只预览）')
    args = ap.parse_args()

    all_entries = load_entries()
    total = len(all_entries)
    print(f'合并总条目数: {total}')

    # 分割：最旧的 (total - WINDOW_SIZE) 条 → 归档；最新 WINDOW_SIZE 条 → recent.json
    archive_entries = all_entries[:-WINDOW_SIZE] if total > WINDOW_SIZE else []
    window_entries = all_entries[-WINDOW_SIZE:] if total > WINDOW_SIZE else all_entries

    # 归档文件列表（每 ARCHIVE_BATCH 一档）
    archive_files = []
    for i in range(0, len(archive_entries), ARCHIVE_BATCH):
        batch = archive_entries[i:i + ARCHIVE_BATCH]
        archive_files.append(batch)

    rotations = len(archive_files)

    print(f'归档文件: {rotations} 个（各 ≤{ARCHIVE_BATCH} 条）')
    print(f'recent.json 滚动窗口: {len(window_entries)} 条（rotations={rotations}）')

    if not args.run:
        print('\n[预览模式] 加 --run 才真正写入。')
        return

    # 删除旧归档文件
    for old in LOG_DIR.glob('recent.*.json'):
        old.unlink()
        print(f'  删除旧归档: {old.name}')

    # 写新归档文件
    LOG_DIR.mkdir(exist_ok=True)
    for idx, batch in enumerate(archive_files, 1):
        out = LOG_DIR / f'recent.{idx}.json'
        out.write_text(
            json.dumps({'entries': batch}, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8'
        )
        print(f'  写入 wiki/logs/recent/recent.{idx}.json ({len(batch)} 条)')

    # 写新 recent.json
    RECENT.write_text(
        json.dumps({'entries': window_entries, 'rotations': rotations},
                   ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8'
    )
    print(f'✓ recent.json 重建完成: {len(window_entries)} 条, rotations={rotations}')


if __name__ == '__main__':
    main()
