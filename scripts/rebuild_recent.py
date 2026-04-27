#!/usr/bin/env python3
"""把 wiki/public/history/*.json 里尚未出现在 recent.jsonl 的页面补入 recent.jsonl。

每个页面只取最新一条 revision（revisions[0]）。按 timestamp 排序后追加到滚动窗口。
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "wiki/public"
HIST_DIR = PUBLIC / "history"
RECENT_PATH = PUBLIC / "recent.jsonl"

WINDOW_SIZE = 1000  # 与 record_revision.py 保持一致


def load_recent():
    if not RECENT_PATH.exists():
        return []
    entries = []
    for ln in RECENT_PATH.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            entries.append(json.loads(ln))
    return entries


def save_recent(entries):
    RECENT_PATH.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n",
        encoding="utf-8",
    )


def main():
    entries = load_recent()
    in_recent = {e["page"] for e in entries}

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
        entry.update({k: v for k, v in latest.items() if k != "content"})
        new_entries.append(entry)

    if not new_entries:
        print("没有需要补入的条目。")
        return

    # 按 timestamp 降序排序
    new_entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    # 合并：新条目追加到现有 recent，去重后按时间降序
    all_entries = entries + new_entries
    seen = {}
    deduped = []
    for e in all_entries:
        p = e["page"]
        if p not in seen or e.get("timestamp", "") > seen[p]:
            seen[p] = e.get("timestamp", "")
            deduped.append(e)

    deduped.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    # 保留最近 WINDOW_SIZE 条（超出部分丢弃，rebuild 脚本不做归档）
    save_recent(deduped[:WINDOW_SIZE])
    print(f"✓ 补入 {len(new_entries)} 个页面，recent.jsonl 现有 {min(len(deduped), WINDOW_SIZE)} 条")


if __name__ == "__main__":
    main()
