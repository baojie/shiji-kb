#!/usr/bin/env python3
"""
构建 recent_changes SQLite 数据库。
从 wiki/logs/recent/recent.*.jsonl 读取全部变更记录。

用法：
    python3 db/build_recent.py
    cp db/recent.sqlite3 public/recent.sqlite3
"""

import sqlite3
import os
import json
import glob
import re

OUT      = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../wiki/public/data/recent.sqlite3")
)
CFG      = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../wiki/public/db-config-recent.json")
)
LOGS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../wiki/logs/recent")
)


def extract_action(summary: str) -> str:
    """从 summary 提取 action 前缀，如 'butler/add-pn'、'add-event-timeline'。"""
    if not summary:
        return "manual"
    m = re.match(r"^([^:：]{1,40}?)[:：]\s", summary)
    if m:
        return m.group(1).strip()
    return "manual"


def build():
    pattern = os.path.join(LOGS_DIR, "recent.*.jsonl")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"找不到 JSONL 文件：{pattern}")

    records = {}
    for f in files:
        with open(f, encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    rev_id = r.get("rev_id", "")
                    if rev_id and rev_id not in records:
                        records[rev_id] = r
                except Exception:
                    continue

    print(f"从 {len(files)} 个文件读取到 {len(records)} 条唯一变更记录")

    if os.path.exists(OUT):
        os.remove(OUT)

    conn = sqlite3.connect(OUT)
    c = conn.cursor()

    c.execute("PRAGMA page_size = 4096")
    c.execute("PRAGMA journal_mode = DELETE")

    c.execute("""
        CREATE TABLE recent_changes (
            rev_id     TEXT PRIMARY KEY,
            page       TEXT NOT NULL,
            timestamp  TEXT NOT NULL,
            date       TEXT NOT NULL,
            author     TEXT NOT NULL DEFAULT '',
            summary    TEXT NOT NULL DEFAULT '',
            action     TEXT NOT NULL DEFAULT 'manual',
            parent_rev TEXT NOT NULL DEFAULT '',
            size       INTEGER
        )
    """)

    rows = []
    for r in records.values():
        ts     = r.get("timestamp", "")
        date   = ts[:10] if len(ts) >= 10 else ""
        summary = r.get("summary", "") or ""
        action  = extract_action(summary)
        rows.append((
            r["rev_id"],
            r["page"],
            ts,
            date,
            r.get("author", "") or "",
            summary,
            action,
            r.get("parent_rev", "") or "",
            r.get("size"),
        ))

    # 按时间排序后插入，让 rowid 顺序有意义
    rows.sort(key=lambda x: x[2])
    c.executemany("INSERT INTO recent_changes VALUES (?,?,?,?,?,?,?,?,?)", rows)

    # 按 timestamp 倒序浏览（主查询）
    c.execute("CREATE INDEX idx_rc_ts     ON recent_changes (timestamp DESC)")
    # 按页名搜索
    c.execute("CREATE INDEX idx_rc_page   ON recent_changes (page, timestamp DESC)")
    # 按 author 过滤
    c.execute("CREATE INDEX idx_rc_author ON recent_changes (author, timestamp DESC)")
    # 按 action 过滤
    c.execute("CREATE INDEX idx_rc_action ON recent_changes (action, timestamp DESC)")
    # 按日期过滤（date 是 timestamp 前 10 字符）
    c.execute("CREATE INDEX idx_rc_date   ON recent_changes (date DESC, timestamp DESC)")

    conn.commit()
    c.execute("VACUUM")
    conn.close()

    size = os.path.getsize(OUT)
    print(f"写入 {OUT}  ({size:,} bytes，{len(rows)} 条记录)")

    with open(CFG, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["fileSize"] = size
    with open(CFG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"更新 {CFG}  (fileSize={size})")


if __name__ == "__main__":
    build()
