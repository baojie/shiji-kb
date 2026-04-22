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
    3. wiki/public/recent.json                  (全局最近, 追加 entry, 保 limit 条)

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
RECENT = PUBLIC / 'recent.json'

TZ_BJ = timezone(timedelta(hours=8))


def iso_with_colon(dt):
    s = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
    return s[:-2] + ':' + s[-2:]  # +0800 → +08:00


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('page', help='slug (without .md)')
    ap.add_argument('--summary', default='', help='修订说明')
    ap.add_argument('--author', default='butler')
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
            now = now.replace(tzinfo=TZ_BJ)
    else:
        now = datetime.now(TZ_BJ)

    rev_id = f'{now.strftime("%Y%m%d-%H%M%S")}-{sha[:6]}'
    ts_iso = iso_with_colon(now)

    # 1. 写副本
    rev_dir = HIST / page
    rev_dir.mkdir(parents=True, exist_ok=True)
    (rev_dir / f'{rev_id}.md').write_text(content, encoding='utf-8')

    # 2. 更新 per-page
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
    entry = {
        'rev_id': rev_id,
        'timestamp': ts_iso,
        'author': args.author,
        'summary': args.summary or f'{args.author} edit',
        'parent_rev': parent_rev,
        'content_hash': f'sha256:{sha}',
        'size': len(content.encode('utf-8')),
    }
    data['revisions'].insert(0, entry)
    data['latest_rev_id'] = rev_id
    data['revision_count'] = len(data['revisions'])
    page_json.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8'
    )

    # 3. 更新 recent.json
    if RECENT.exists():
        recent = json.loads(RECENT.read_text(encoding='utf-8'))
    else:
        recent = {'limit': 50, 'total_pages': 0, 'entries': []}

    recent['entries'].insert(0, {'page': page, **entry})

    # W5 v4 提案 11: recent.json 上限 500, 旧的月度归档
    ARCHIVE_LIMIT = 500
    if len(recent['entries']) > ARCHIVE_LIMIT:
        overflow = recent['entries'][ARCHIVE_LIMIT:]
        recent['entries'] = recent['entries'][:ARCHIVE_LIMIT]
        # 按月分卷归档
        archive_dir = PUBLIC / 'recent-archive'
        archive_dir.mkdir(exist_ok=True)
        for item in overflow:
            ym = item['timestamp'][:7]  # YYYY-MM
            arc = archive_dir / f'{ym}.json'
            if arc.exists():
                data = json.loads(arc.read_text(encoding='utf-8'))
            else:
                data = {'month': ym, 'entries': []}
            data['entries'].append(item)
            arc.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8')
    recent['total_pages'] = len({e['page'] for e in recent['entries']})
    recent['total_revisions'] = len(recent['entries'])
    RECENT.write_text(
        json.dumps(recent, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8'
    )

    print(f'✓ {page} rev={rev_id} size={len(content)} author={args.author}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
