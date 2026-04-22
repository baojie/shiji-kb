#!/usr/bin/env python3
"""
migrate_history_to_json.py — 把 history/<slug>/<rev>.md 内容内联进 history/<slug>.json.

迁移前:
    wiki/public/history/曹参.json             (metadata only)
    wiki/public/history/曹参/20260422-*.md   (content per rev, 一堆小文件)

迁移后:
    wiki/public/history/曹参.json             (metadata + content 内联)
    [wiki/public/history/曹参/ 整个目录删除]

revisions[i] 字段增加:
    "content": <markdown 原文>
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HIST = ROOT / 'wiki/public/history'


def main() -> int:
    if not HIST.exists():
        print(f'✗ {HIST} 不存在', file=sys.stderr)
        return 1

    migrated = 0
    total_revs = 0
    for jsonf in sorted(HIST.glob('*.json')):
        slug = jsonf.stem
        rev_dir = HIST / slug
        if not rev_dir.is_dir():
            continue

        data = json.loads(jsonf.read_text(encoding='utf-8'))
        for rev in data.get('revisions', []):
            if 'content' in rev:
                continue  # already migrated
            rev_md = rev_dir / f'{rev["rev_id"]}.md'
            if not rev_md.exists():
                print(f'[warn] {slug}/{rev["rev_id"]}.md 不存在, 跳过', file=sys.stderr)
                continue
            rev['content'] = rev_md.read_text(encoding='utf-8')
            total_revs += 1
        jsonf.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8'
        )
        # 删除旧目录
        shutil.rmtree(rev_dir)
        migrated += 1
        print(f'✓ {slug}: {len(data.get("revisions",[]))} revs 内联, 目录已删')

    print(f'\n[done] {migrated} 页 / {total_revs} revs 内联')
    return 0


if __name__ == '__main__':
    sys.exit(main())
