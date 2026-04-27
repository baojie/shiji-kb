#!/usr/bin/env python3
"""
build_wanted_pages.py — 扫描所有 wiki 页面的 wikilinks，找出"被链接但尚未创建"的页面。

输出：
  wiki/public/data/wanted_pages.json   机器可读，供 WantedPages 渲染
  （可选）覆盖写 WantedPages.md 的数据区块

用法：
    python3 wiki/scripts/build_wanted_pages.py
    python3 wiki/scripts/build_wanted_pages.py --top 100
    python3 wiki/scripts/build_wanted_pages.py --update-page   # 同时更新 WantedPages 页面
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGES_DIR = ROOT / "wiki/public/pages"
PAGES_JSON = ROOT / "wiki/public/pages.json"
OUT_JSON = ROOT / "wiki/public/data/wanted_pages.json"
SPECIAL_PAGE = PAGES_DIR / "WantedPages.md"

WIKILINK_RE = re.compile(r"\[\[([^\]|#][^\]|#]*)(?:\|[^\]]+)?\]\]")
# 跳过 Special: 前缀的链接
SKIP_PREFIXES = ("Special:", "Category:", "Help:")


def load_alias_index() -> dict[str, str]:
    """从 pages.json 加载 alias_index，alias → canonical page id。"""
    if not PAGES_JSON.exists():
        return {}
    data = json.loads(PAGES_JSON.read_text(encoding="utf-8"))
    return data.get("alias_index", {})


def scan_wikilinks() -> dict[str, list[str]]:
    """
    扫描所有 pages/*.md，提取 [[target]] 链接。
    返回：target → [source_page, ...] 的映射。
    """
    links: dict[str, list[str]] = {}
    for md_file in sorted(PAGES_DIR.glob("*.md")):
        page_id = md_file.stem
        content = md_file.read_text(encoding="utf-8")
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip()
            if any(target.startswith(p) for p in SKIP_PREFIXES):
                continue
            links.setdefault(target, [])
            if page_id not in links[target]:
                links[target].append(page_id)
    return links


def build_wanted(links: dict[str, list[str]],
                 alias_index: dict[str, str],
                 top: int = 200) -> list[dict]:
    """
    从链接目标中过滤出"尚不存在"的页面。
    判定规则：
      1. PAGES_DIR/<target>.md 不存在
      2. target 不在 alias_index（别名也算"已存在"）
    """
    existing_files = {f.stem for f in PAGES_DIR.glob("*.md")}

    wanted = []
    for target, sources in links.items():
        if target in existing_files:
            continue
        if target in alias_index:
            continue
        wanted.append({
            "id": target,
            "link_count": len(sources),
            "linked_from": sorted(sources),
        })

    wanted.sort(key=lambda x: (-x["link_count"], x["id"]))
    return wanted[:top]


def write_json(wanted: list[dict]) -> None:
    out = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(wanted),
        "items": wanted,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 写入 {OUT_JSON.relative_to(ROOT)}  ({len(wanted)} 条)")


SPECIAL_HEADER = """\
---
id: "WantedPages"
type: project
label: 想要的页面
canonical_name: "WantedPages"
tags: [系统页面, 维护]
---

# WantedPages — 想要的页面

被其他页面链接、但**尚未创建**的页面列表，按入链数从多到少排列。
数据由 [`build_wanted_pages.py`](../../scripts/build_wanted_pages.py) 自动生成，butler 每 20 轮刷新一次。

> 最后更新：{updated}　共 **{total}** 个待建页面

---

## Top 50 待建页面

| 排名 | 页面 | 入链数 | 来自哪些页面（前 5） |
|------|------|--------|----------------------|
"""

SPECIAL_FOOTER = """
---

## 说明

- **入链数**：有多少个现有页面包含指向该页的 `[[wikilink]]`
- **已有别名**：若目标已作为别名收录在 `pages.json` 中，则不会出现在此列表
- butler 的 `create-stub` 动作优先从本列表高排名项目中选取候选

## 相关页面

- [[Special:All]] — 所有特殊页面索引
- [[Special:知识量]] — 知识量统计

---

*本页为系统特殊页面（`Special:` 前缀），不计入 K 值。*
"""


def update_special_page(wanted: list[dict]) -> None:
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(wanted)

    rows = []
    for i, item in enumerate(wanted[:50], 1):
        page_id = item["id"]
        count = item["link_count"]
        sources = item["linked_from"][:5]
        src_str = "、".join(f"[[{s}]]" for s in sources)
        if len(item["linked_from"]) > 5:
            src_str += f" 等 {len(item['linked_from'])} 页"
        rows.append(f"| {i} | [[{page_id}]] | {count} | {src_str} |")

    content = (
        SPECIAL_HEADER.format(updated=updated, total=total)
        + "\n".join(rows)
        + SPECIAL_FOOTER
    )
    SPECIAL_PAGE.write_text(content, encoding="utf-8")
    print(f"✓ 更新 {SPECIAL_PAGE.relative_to(ROOT)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="构建 WantedPages 数据")
    ap.add_argument("--top", type=int, default=200, help="保留前 N 条（默认 200）")
    ap.add_argument("--update-page", action="store_true",
                    help="同时覆写 WantedPages.md")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印统计，不写文件")
    args = ap.parse_args()

    alias_index = load_alias_index()
    links = scan_wikilinks()
    wanted = build_wanted(links, alias_index, top=args.top)

    print(f"扫描完成：链接目标 {len(links)} 个，待建页面 {len(wanted)} 个")

    if args.dry_run:
        print("Top 20:")
        for item in wanted[:20]:
            print(f"  {item['id']:30s}  ← {item['link_count']} 页")
        return 0

    write_json(wanted)

    if args.update_page:
        update_special_page(wanted)

    return 0


if __name__ == "__main__":
    sys.exit(main())
