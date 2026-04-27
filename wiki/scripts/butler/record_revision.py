#!/usr/bin/env python3
"""
record_revision.py — 为 wiki/public/pages/<page>.md 写入一条修订记录.

用法:
    python3 wiki/scripts/butler/record_revision.py <slug> \
        [--summary "butler/<action>: ..."] \
        [--author butler]

产出:
    1. wiki/public/history/<slug>/<rev_id>.md   (内容副本)
    2. wiki/public/history/<slug>.json          (per-page 索引, 追加 entry)
    3. wiki/public/recent.jsonl                 (全局修订日志, 滚动窗口 JSONL，每行一条)
    4. wiki/logs/recent/recent.N.jsonl          (归档批次, 永久保留)

rev_id 格式: YYYYMMDD-HHMMSS-<sha256[:6]>  (北京时间)

butler 原子动作结束时应调用本脚本, 让 #?recent / #?history=<page> 视图可见.
"""

from __future__ import annotations

import argparse
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
LOG_DIR = ROOT / 'wiki/logs/recent'   # 归档批次目录

TZ_BJ = timezone(timedelta(hours=8))
TZ_UTC = timezone.utc


def iso_with_colon(dt):
    s = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
    if s.endswith('+0000'):
        return s[:-5] + 'Z'
    return s[:-2] + ':' + s[-2:]  # +0800 → +08:00


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
        now = datetime.now(TZ_UTC)  # 存 UTC，前端转本地时间

    rev_id = f'{now.strftime("%Y%m%d-%H%M%S")}-{sha[:6]}'
    ts_iso = iso_with_colon(now)

    # W5 v6 / user-req (2026-04-22): 不再写独立 rev .md 文件.
    # 内容 inlined 到 per-page JSON 的 revisions[].content 字段.
    # 文件数从每修订一文件 -> 每页一文件.

    # 更新 per-page
    page_json = HIST / f'{page}.json'
    if page_json.exists():
        data = json.loads(page_json.read_text(encoding='utf-8'))
    else:
        data = {'page': page, 'latest_rev_id': None,
                'revision_count': 0, 'revisions': []}

    # 去重: 若相同 content_hash 已是最新, 不重复记
    if data['revisions']:
        prev_hash = data['revisions'][0].get('content_hash', '')
        if prev_hash == f'sha256:{sha}':
            print(f'= {page} 内容与 latest 相同 (hash {sha[:6]}), 跳过')
            return 0

    parent_rev = data['latest_rev_id']
    size_after = len(content.encode('utf-8'))
    size_before = data['revisions'][0]['size'] if data['revisions'] else 0
    entry = {
        'rev_id': rev_id,
        'timestamp': ts_iso,
        'author': args.author,
        'summary': args.summary or f'{args.author} edit',
        'parent_rev': parent_rev,
        'content_hash': f'sha256:{sha}',
        'size_before': size_before,
        'size': size_after,
        'content': content,  # inlined
    }
    if args.action == 'delete':
        entry['action'] = 'delete'
    data['revisions'].insert(0, entry)
    data['latest_rev_id'] = rev_id
    data['revision_count'] = len(data['revisions'])
    if args.action == 'delete':
        data['deleted'] = True
        data['deleted_at'] = ts_iso
    page_json.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8'
    )

    # 3. 更新 recent.jsonl（滚动窗口：始终保留最近 WINDOW_SIZE 条；
    #    超出后把最旧的 ARCHIVE_BATCH 条移入 wiki/logs/recent/recent.N.jsonl 归档）
    WINDOW_SIZE = 1000    # recent.jsonl 最多存 1000 行（前端取其中最新 500）
    ARCHIVE_BATCH = 500   # 每次归档最旧的 500 条

    # 读取现有条目（每行一个 JSON 对象）
    if RECENT.exists():
        raw_lines = RECENT.read_text(encoding='utf-8').splitlines()
        entries = []
        for ln in raw_lines:
            ln = ln.strip()
            if ln:
                entries.append(json.loads(ln))
    else:
        entries = []

    # 追加新条目（不含 content 字段）
    new_entry = {'page': page, **{k: v for k, v in entry.items() if k != 'content'}}
    entries.append(new_entry)

    # 归档溢出：超过 WINDOW_SIZE 时把最旧的 ARCHIVE_BATCH 条移入 log/
    if len(entries) > WINDOW_SIZE:
        batch = entries[:ARCHIVE_BATCH]
        entries = entries[ARCHIVE_BATCH:]
        # 推断下一个归档编号
        LOG_DIR.mkdir(exist_ok=True)
        existing = [int(p.stem.split('.')[1]) for p in LOG_DIR.glob('recent.*.jsonl')
                    if p.stem.split('.')[1].isdigit()]
        rotations = max(existing) + 1 if existing else 1
        archive_lines = '\n'.join(json.dumps(e, ensure_ascii=False) for e in batch) + '\n'
        (LOG_DIR / f'recent.{rotations}.jsonl').write_text(archive_lines, encoding='utf-8')
        print(f'  [archive] {len(batch)} entries → wiki/logs/recent/recent.{rotations}.jsonl')

    # 回写滚动窗口（JSONL：每行一条）
    RECENT.write_text(
        '\n'.join(json.dumps(e, ensure_ascii=False) for e in entries) + '\n',
        encoding='utf-8'
    )

    verb = '(deleted)' if args.action == 'delete' else ''
    delta = size_after - size_before
    delta_str = f'+{delta}' if delta >= 0 else str(delta)
    print(f'✓ {page} rev={rev_id} size={size_before}→{size_after}({delta_str}) author={args.author} {verb}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
