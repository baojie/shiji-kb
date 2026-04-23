#!/usr/bin/env python3
"""把 wiki/public/history/*.json 里尚未出现在 recent.json 的页面补入 recent.json。

每个页面只取最新一条 revision（revisions[0]）。按 timestamp 排序后插入。
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "wiki/public"
HIST_DIR = PUBLIC / "history"
RECENT_PATH = PUBLIC / "recent.json"

ARCHIVE_LIMIT = 500

def main():
    # 读取 recent.json
    if RECENT_PATH.exists():
        recent = json.loads(RECENT_PATH.read_text(encoding="utf-8"))
    else:
        recent = {"limit": ARCHIVE_LIMIT, "total_pages": 0, "entries": []}

    in_recent = {e["page"] for e in recent["entries"]}

    # 收集缺失页面的最新 revision
    new_entries = []
    for hist_file in sorted(HIST_DIR.glob("*.json")):
        page = hist_file.stem
        if page in in_recent:
            continue
        try:
            data = json.loads(hist_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  跳过 {hist_file.name}: {e}")
            continue
        revs = data.get("revisions", [])
        if not revs:
            continue
        latest = revs[0]  # revisions[0] 是最新
        entry = {"page": page}
        entry.update(latest)
        new_entries.append(entry)

    if not new_entries:
        print("没有需要补入的条目。")
        return

    # 按 timestamp 降序排序
    new_entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    # 合并：新条目插到现有 recent 前面（更新的在前）
    # 但现有的 recent 已有 500 条，要按时间合并
    all_entries = new_entries + recent["entries"]
    # 去重（同一 page 保留最新 timestamp）
    seen = {}
    deduped = []
    for e in all_entries:
        p = e["page"]
        if p not in seen:
            seen[p] = True
            deduped.append(e)

    # 按 timestamp 降序
    deduped.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    # 归档超出部分（保留最新 500）
    recent["entries"] = deduped[:ARCHIVE_LIMIT]
    recent["total_pages"] = len({e["page"] for e in recent["entries"]})
    recent["total_revisions"] = len(recent["entries"])

    RECENT_PATH.write_text(
        json.dumps(recent, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"✓ 补入 {len(new_entries)} 个页面，recent.json 现有 {len(recent['entries'])} 条")


if __name__ == "__main__":
    main()
