#!/usr/bin/env python3
"""
批量生成 130 章节 stub 页 (type=chapter), 降低 wikilink 死链率.

源: chapter_md/NNN_章名.tagged.md
输出: wiki/public/pages/NNN_章名.md  (若已存在则跳过)

每页极简:
---
id: NNN_章名
type: chapter
label: 章名
chapter_no: NNN
aliases: ["章名", "NNN"]
tags: [体裁]  # 本纪/世家/列传/表/书
auto_generated: true
---

# NNN 章名

《史记》第 NNN 篇 · X体

*查看原文*: [chapter_md/NNN_章名.tagged.md](../../../chapter_md/NNN_章名.tagged.md)
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # shiji-kb/
CHAPTERS = REPO_ROOT / "chapter_md"
OUT_DIR = REPO_ROOT / "wiki" / "public" / "pages"

# 章号 -> 体裁 (《史记》体例)
#   1-12   本纪
#   13-22  表
#   23-30  书
#   31-60  世家
#   61-130 列传
def genre_of(n: int) -> str:
    if 1 <= n <= 12:
        return "本纪"
    if 13 <= n <= 22:
        return "表"
    if 23 <= n <= 30:
        return "书"
    if 31 <= n <= 60:
        return "世家"
    if 61 <= n <= 130:
        return "列传"
    return "篇"


TEMPLATE = """---
id: {pid}
type: chapter
label: {title}
chapter_no: {nn}
aliases: [{title}, {nn_raw}]
tags: [{genre}]
auto_generated: true
---

# {pid}

《史记》第 {n} 篇 · {genre}

*查看原文*: [{raw_name}](../../../chapter_md/{raw_name})
"""


def main() -> int:
    if not CHAPTERS.exists():
        print(f"[error] {CHAPTERS} 不存在", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    for md in sorted(CHAPTERS.glob("*.tagged.md")):
        stem = md.stem  # 001_五帝本纪.tagged → 001_五帝本纪
        stem = stem.replace(".tagged", "")
        if "_" not in stem:
            continue
        nn, title = stem.split("_", 1)
        try:
            n = int(nn)
        except ValueError:
            continue
        if not (1 <= n <= 130):
            continue

        pid = f"{nn}_{title}"
        out = OUT_DIR / f"{pid}.md"
        if out.exists():
            skipped += 1
            continue

        content = TEMPLATE.format(
            pid=pid,
            title=title,
            nn=nn,
            nn_raw=nn,
            n=n,
            genre=genre_of(n),
            raw_name=md.name,
        )
        out.write_text(content, encoding="utf-8")
        created += 1

    print(f"[ok] chapter stubs 新建 {created} 页, 已存在跳过 {skipped} 页")
    return 0


if __name__ == "__main__":
    sys.exit(main())
