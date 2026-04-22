"""一次性迁移: 把 docs/wiki/pages/*.md 灌进 data/wiki/revisions/*.jsonl.

每个现有页面写入一条 author=migration 的初始修订。
若某页面已有任何 revision, 则跳过（幂等）。

用法:
  python scripts/wiki_init_revisions.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from wiki_revisions import (
    REPO_ROOT,
    append_revision,
    load_revisions,
)

PAGES_DIR = REPO_ROOT / "docs" / "wiki" / "pages"


def file_mtime_iso(path: Path) -> str:
    ts = path.stat().st_mtime
    dt = datetime.fromtimestamp(ts, timezone.utc).astimezone()
    return dt.replace(microsecond=0).isoformat()


def main() -> int:
    if not PAGES_DIR.exists():
        print(f"找不到 {PAGES_DIR}")
        return 1

    md_files = sorted(PAGES_DIR.glob("*.md"))
    if not md_files:
        print(f"{PAGES_DIR} 下无 .md 文件")
        return 1

    created = 0
    skipped = 0
    for md in md_files:
        page = md.stem
        if load_revisions(page):
            print(f"  跳过 {page} (已有修订)")
            skipped += 1
            continue
        content = md.read_text(encoding="utf-8")
        ts = file_mtime_iso(md)
        rev = append_revision(
            page=page,
            content=content,
            author="migration",
            summary="initial import from docs/wiki/pages/",
            timestamp_iso=ts,
        )
        print(f"  + {page}  rev_id={rev.rev_id}")
        created += 1

    print(f"\n完成: 新建 {created} 条, 跳过 {skipped} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
