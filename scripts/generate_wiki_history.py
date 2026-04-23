#!/usr/bin/env python3
"""为没有 history 文件的 wiki 页面批量生成初始 revision 记录。"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone, timedelta

PAGES_DIR = "wiki/public/pages"
HISTORY_DIR = "wiki/public/history"
TIMESTAMP = "2026-04-23T10:00:00+08:00"
AUTHOR = "butler"

TZ_CST = timezone(timedelta(hours=8))


def sha256_hex(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def make_rev_id(ts: str, h: str) -> str:
    # 格式：YYYYMMDD-HHMMSS-xxxxxx
    dt = datetime.fromisoformat(ts)
    date_part = dt.strftime("%Y%m%d-%H%M%S")
    return f"{date_part}-{h[:6]}"


def infer_summary(name: str, content: str) -> str:
    # 从内容推断摘要：取第一个非空标题行或描述
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return f"butler/ontology-import: {line[2:].strip()}"
        if line.startswith("description:"):
            desc = line.split(":", 1)[1].strip().strip('"').strip("'")
            if desc:
                return f"butler/ontology-import: {desc[:60]}"
    return f"butler/ontology-import: {name}"


def process():
    os.makedirs(HISTORY_DIR, exist_ok=True)
    created = []
    skipped = []

    for fname in sorted(os.listdir(PAGES_DIR)):
        if not fname.endswith(".md"):
            continue
        name = fname[:-3]
        hist_path = os.path.join(HISTORY_DIR, f"{name}.json")
        if os.path.exists(hist_path):
            skipped.append(name)
            continue

        page_path = os.path.join(PAGES_DIR, fname)
        with open(page_path, "r", encoding="utf-8") as f:
            content = f.read()

        size = len(content.encode("utf-8"))
        h = sha256_hex(content)
        rev_id = make_rev_id(TIMESTAMP, h)
        summary = infer_summary(name, content)

        record = {
            "page": name,
            "latest_rev_id": rev_id,
            "revision_count": 1,
            "revisions": [
                {
                    "rev_id": rev_id,
                    "timestamp": TIMESTAMP,
                    "author": AUTHOR,
                    "summary": summary,
                    "parent_rev": None,
                    "content_hash": f"sha256:{h}",
                    "size": size,
                    "content": content,
                }
            ],
        }

        with open(hist_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        created.append(name)

    print(f"新建 history: {len(created)} 个")
    print(f"已有 history（跳过）: {len(skipped)} 个")
    if created:
        print("\n新建列表：")
        for n in created:
            print(f"  {n}.json")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    process()
