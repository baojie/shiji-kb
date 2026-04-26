#!/usr/bin/env python3
"""
undo_sanjia_chapter_pages.py — 从章节wiki页面中移除 ## 三家注 节。

用法：
    python3 scripts/undo_sanjia_chapter_pages.py           # 处理全部
    python3 scripts/undo_sanjia_chapter_pages.py --dry-run # 预览
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / 'wiki' / 'public' / 'pages'
EDIT_PAGE = ROOT / 'wiki' / 'scripts' / 'butler' / 'edit_page.py'


def remove_sanjia_section(content: str) -> str | None:
    """移除 ## 三家注 节及其后内容。返回 None 表示无需修改。"""
    marker = '\n\n## 三家注'
    idx = content.find(marker)
    if idx == -1:
        # 也尝试找顶格的 ## 三家注
        marker2 = '## 三家注'
        if content.startswith(marker2):
            return None  # 整个文件都是三家注，不应该出现
        idx2 = content.find('\n## 三家注')
        if idx2 == -1:
            return None
        return content[:idx2 + 1].rstrip() + '\n'
    return content[:idx].rstrip() + '\n'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    # 找所有章节页（NNN_*.md 格式）
    chapter_pages = sorted(PAGES.glob('[0-9][0-9][0-9]_*.md'))
    done = skipped = errors = 0

    for page in chapter_pages:
        content = page.read_text(encoding='utf-8')
        if '## 三家注' not in content:
            continue

        new_content = remove_sanjia_section(content)
        if new_content is None:
            print(f'[{page.name}] 跳过（无法处理）')
            skipped += 1
            continue

        if args.dry_run:
            orig_lines = len(content.splitlines())
            new_lines = len(new_content.splitlines())
            print(f'[{page.name}] DRY-RUN: {orig_lines} → {new_lines} 行')
            skipped += 1
            continue

        slug = page.stem
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', encoding='utf-8', delete=False
        ) as tmp:
            tmp.write(new_content)
            tmp_path = tmp.name

        result = subprocess.run(
            [
                sys.executable, str(EDIT_PAGE),
                slug, tmp_path,
                '--summary', 'sanjia-undo: 移除章节页三家注节（将改为实体页分发）',
                '--author', 'butler',
                '--allow-shrink',
            ],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        Path(tmp_path).unlink(missing_ok=True)

        if result.returncode != 0:
            print(f'[{page.name}] 错误: {result.stderr.strip()}')
            errors += 1
        else:
            print(f'[{page.name}] 完成：已移除三家注节')
            done += 1

    print(f'\n完成 {done}，跳过 {skipped}，错误 {errors}')


if __name__ == '__main__':
    main()
