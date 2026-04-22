"""把 data/wiki/revisions/*.jsonl 派生到 docs/wiki/.

输出:
  docs/wiki/pages/<page>.md            最新版本（覆写）
  docs/wiki/history/<page>.json        修订列表元数据
  docs/wiki/history/<page>/<rev_id>.md 每条历史版本全文
  docs/wiki/recent.json                全局最近 N 条修订（默认 50）

用法:
  python scripts/build_wiki_history.py
  python scripts/build_wiki_history.py --recent 100
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from wiki_revisions import (
    REPO_ROOT,
    list_pages,
    load_revisions,
)

PAGES_OUT = REPO_ROOT / "docs" / "wiki" / "pages"
HISTORY_OUT = REPO_ROOT / "docs" / "wiki" / "history"
RECENT_OUT = REPO_ROOT / "docs" / "wiki" / "recent.json"


def write_page_artifacts(page: str) -> list[dict]:
    """返回该页面修订列表的元数据 (按时间倒序), 顺便写出文件."""
    revs = load_revisions(page)
    if not revs:
        return []

    PAGES_OUT.mkdir(parents=True, exist_ok=True)
    page_history_dir = HISTORY_OUT / page
    page_history_dir.mkdir(parents=True, exist_ok=True)

    # 当前最新版 → docs/wiki/pages/<page>.md
    latest = revs[-1]
    (PAGES_OUT / f"{page}.md").write_text(latest.content, encoding="utf-8")

    # 每条历史版本全文 → docs/wiki/history/<page>/<rev_id>.md
    valid_rev_files = {f"{rev.rev_id}.md" for rev in revs}
    for rev in revs:
        out = page_history_dir / f"{rev.rev_id}.md"
        # 已存在的不重写（jsonl append-only, 内容固定）
        if not out.exists():
            out.write_text(rev.content, encoding="utf-8")
    # 删除孤儿 (jsonl 中已不存在的 rev md, 防御性处理)
    for f in page_history_dir.glob("*.md"):
        if f.name not in valid_rev_files:
            f.unlink()

    # 修订元数据（剥去 content，倒序）
    metas = []
    for rev in reversed(revs):
        metas.append({
            "rev_id": rev.rev_id,
            "timestamp": rev.timestamp,
            "author": rev.author,
            "summary": rev.summary,
            "parent_rev": rev.parent_rev,
            "content_hash": rev.content_hash,
            "size": len(rev.content.encode("utf-8")),
        })

    history_index = {
        "page": page,
        "latest_rev_id": latest.rev_id,
        "revision_count": len(revs),
        "revisions": metas,
    }
    (HISTORY_OUT / f"{page}.json").write_text(
        json.dumps(history_index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return metas


def cleanup_orphan_history(active_pages: set[str]) -> None:
    """删除 revisions/ 中已不存在的页面对应的 docs/wiki/history/ 残留."""
    if not HISTORY_OUT.exists():
        return
    for child in HISTORY_OUT.iterdir():
        name = child.name
        if child.is_dir() and name not in active_pages:
            shutil.rmtree(child)
        elif child.is_file() and name.endswith(".json"):
            if name[:-5] not in active_pages:
                child.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recent", type=int, default=50,
                        help="recent.json 中保留的最近修订数 (默认 50)")
    args = parser.parse_args()

    pages = list_pages()
    if not pages:
        print("data/wiki/revisions/ 下无修订文件; 是否先跑 wiki_init_revisions.py?")
        return 1

    HISTORY_OUT.mkdir(parents=True, exist_ok=True)

    all_recent: list[dict] = []
    for page in pages:
        metas = write_page_artifacts(page)
        for m in metas:
            all_recent.append({"page": page, **m})

    cleanup_orphan_history(set(pages))

    # 全局最近 N 条 (按 timestamp 降序)
    all_recent.sort(key=lambda r: r["timestamp"], reverse=True)
    RECENT_OUT.write_text(
        json.dumps({
            "limit": args.recent,
            "total_pages": len(pages),
            "entries": all_recent[: args.recent],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"写出 {len(pages)} 个页面, 全局共 {len(all_recent)} 条修订")
    print(f"  pages/   → {PAGES_OUT.relative_to(REPO_ROOT)}")
    print(f"  history/ → {HISTORY_OUT.relative_to(REPO_ROOT)}")
    print(f"  recent   → {RECENT_OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
