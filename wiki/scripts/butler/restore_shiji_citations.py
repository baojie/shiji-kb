#!/usr/bin/env python3
"""
restore_shiji_citations.py — 恢复被 expand 操作删除的「## 史记引文」节。

扫描所有页面：
  - 当前版本缺少 ## 史记引文
  - 但历史版本中有 ## 史记引文
  → 从最近一个含此节的历史版本中提取，追加到当前页面（append-only）

用法：
    python3 wiki/scripts/butler/restore_shiji_citations.py [--dry-run] [--slug SLUG]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES = ROOT / 'wiki' / 'public' / 'pages'
HISTORY = ROOT / 'wiki' / 'public' / 'history'
EDIT_PAGE = ROOT / 'wiki' / 'scripts' / 'butler' / 'edit_page.py'


def extract_shiji_section(content: str) -> str | None:
    """从页面内容中提取 ## 史记引文 节（含标题行到下一个 ## 或文末）。"""
    lines = content.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if line.strip() == '## 史记引文':
            start = i
            break
    if start is None:
        return None

    end = len(lines)
    for i in range(start + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith('## ') or stripped == '---':
            end = i
            break

    section = ''.join(lines[start:end]).rstrip()
    return section


def find_prev_shiji_section(slug: str) -> str | None:
    """在历史记录中寻找最近一个含 ## 史记引文 的版本，返回该节内容。"""
    h_file = HISTORY / f'{slug}.json'
    if not h_file.exists():
        return None
    try:
        data = json.loads(h_file.read_text(encoding='utf-8'))
    except Exception:
        return None

    revs = data.get('revisions', [])
    # revs[0] is newest; skip it (that's the broken one)
    for rev in revs[1:]:
        content = rev.get('content', '')
        if '## 史记引文' in content:
            section = extract_shiji_section(content)
            if section:
                return section
    return None


def insert_before_related(content: str, section_text: str) -> str:
    """将 section_text 插入 ## 相关章节 之前，或追加到文末。"""
    lines = content.splitlines(keepends=True)
    insert_at = None
    for i, line in enumerate(lines):
        if line.strip() in ('## 相关章节', '## 相关'):
            insert_at = i
            break

    block = '\n' + section_text + '\n\n'

    if insert_at is not None:
        lines.insert(insert_at, block)
    else:
        # 追加到末尾
        lines.append(block)

    return ''.join(lines)


def process_slug(slug: str, dry_run: bool) -> str:
    """处理单个 slug，返回状态字符串。"""
    page_file = PAGES / f'{slug}.md'
    if not page_file.exists():
        return 'skip:no_page'

    current = page_file.read_text(encoding='utf-8')
    if '## 史记引文' in current:
        return 'skip:already_has'

    section = find_prev_shiji_section(slug)
    if not section:
        return 'skip:no_history'

    new_content = insert_before_related(current, section)

    if dry_run:
        print(f'[DRY] {slug}: would insert 史记引文 ({len(section)} chars)')
        return 'dry'

    # Write via temp file → edit_page.py
    tmp = Path(f'/tmp/restore_{slug}.md')
    tmp.write_text(new_content, encoding='utf-8')

    result = subprocess.run(
        [sys.executable, str(EDIT_PAGE), slug, str(tmp),
         '--summary', f'restore: 恢复被expand覆盖的史记引文节',
         '--author', 'butler'],
        capture_output=True, text=True
    )
    tmp.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f'  ✗ {slug}: {result.stderr.strip()}', file=sys.stderr)
        return 'fail'
    return 'restored'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='不实际写入，只报告')
    ap.add_argument('--slug', help='只处理指定 slug')
    ap.add_argument('--limit', type=int, default=0, help='最多处理 N 个页面（0=不限）')
    args = ap.parse_args()

    if args.slug:
        slugs = [args.slug]
    else:
        # 扫描所有历史文件，找 expand 后丢失 史记引文 的页面
        slugs = []
        for h_file in sorted(HISTORY.glob('*.json')):
            try:
                data = json.loads(h_file.read_text(encoding='utf-8'))
            except Exception:
                continue
            revs = data.get('revisions', [])
            if not revs:
                continue
            latest = revs[0]
            summary = latest.get('summary', '')
            # 只处理 expand 类操作
            if not ('expand stub' in summary or 'narrative' in summary.lower()):
                continue
            current_content = latest.get('content', '')
            if '## 史记引文' in current_content:
                continue
            prev_had = any('## 史记引文' in r.get('content', '') for r in revs[1:])
            if prev_had:
                slugs.append(h_file.stem)

    if args.limit > 0:
        slugs = slugs[:args.limit]

    print(f'待处理页面: {len(slugs)} 个', flush=True)
    counts = {'restored': 0, 'skip:already_has': 0, 'skip:no_history': 0,
              'skip:no_page': 0, 'fail': 0, 'dry': 0}

    for i, slug in enumerate(slugs):
        status = process_slug(slug, args.dry_run)
        counts[status] = counts.get(status, 0) + 1
        if status in ('restored', 'fail', 'dry'):
            print(f'[{i+1}/{len(slugs)}] {status}: {slug}', flush=True)

    print('\n=== 统计 ===')
    for k, v in counts.items():
        if v:
            print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
