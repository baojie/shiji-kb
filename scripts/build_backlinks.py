#!/usr/bin/env python3
"""
build_backlinks.py — 构建 wiki 反向引用索引

扫描 wiki/public/pages/*.md，提取所有 [[wikilink]]，
生成 wiki/public/backlinks.json：
  { "目标页ID": [{"id": "来源页ID", "label": "...", "type": "..."}, ...] }

别名解析：用 pages.json 的 alias_index，与前端保持一致。

用法：
  python3 scripts/build_backlinks.py          # 构建并写入
  python3 scripts/build_backlinks.py --stats  # 额外打印统计信息
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent

PAGES_DIR    = PROJECT_ROOT / "wiki" / "public" / "pages"
PAGES_JSON   = PROJECT_ROOT / "wiki" / "public" / "pages.json"
OUT_FILE     = PROJECT_ROOT / "wiki" / "public" / "backlinks.json"

# 匹配 [[target]] 和 [[target|text]]，不匹配嵌套
_WIKILINK_RE = re.compile(r"\[\[([^\[\]|]+?)(?:\|[^\[\]]+?)?\]\]")


def load_registry() -> tuple[dict, dict]:
    """返回 (pages, alias_index)。"""
    reg = json.loads(PAGES_JSON.read_text(encoding="utf-8"))
    return reg["pages"], reg.get("alias_index", {})


def resolve(target: str, pages: dict, alias_index: dict) -> str | None:
    """将 wikilink 目标解析为规范 page ID，与 registry.js 逻辑一致。"""
    t = target.strip()
    if t in pages:
        return t
    if t in alias_index:
        return alias_index[t]
    if "/" in t:
        tail = t.split("/", 1)[1]
        if tail in pages:
            return tail
        if tail in alias_index:
            return alias_index[tail]
    return None


def extract_links(md_text: str) -> list[str]:
    """从 markdown 文本提取所有 wikilink target（原始形式，未解析）。"""
    # 跳过 frontmatter
    body = md_text
    if md_text.startswith("---"):
        end = md_text.find("\n---", 3)
        if end != -1:
            body = md_text[end + 4:]
    return _WIKILINK_RE.findall(body)


def build(verbose: bool = False) -> dict[str, list[dict]]:
    """返回 backlinks dict。"""
    pages, alias_index = load_registry()

    # backlinks[target_id] = list of source page entries (去重，按 id 排序)
    backlinks: dict[str, set[str]] = {}

    md_files = sorted(PAGES_DIR.glob("*.md"))
    if verbose:
        print(f"扫描 {len(md_files)} 个页面…")

    for md_path in md_files:
        source_id = md_path.stem
        if source_id not in pages:
            continue  # 不在注册表中的页面跳过

        md_text = md_path.read_text(encoding="utf-8")
        raw_links = extract_links(md_text)

        for raw in raw_links:
            target_id = resolve(raw, pages, alias_index)
            if target_id and target_id != source_id:
                backlinks.setdefault(target_id, set()).add(source_id)

    # 转为带元数据的列表，按 label 排序
    result: dict[str, list[dict]] = {}
    for target_id, sources in sorted(backlinks.items()):
        entries = []
        for src_id in sorted(sources):
            if src_id in pages:
                p = pages[src_id]
                entries.append({
                    "id":    src_id,
                    "label": p.get("label", src_id),
                    "type":  p.get("type", ""),
                })
        entries.sort(key=lambda x: x["label"])
        result[target_id] = entries

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="构建 wiki 反向引用索引")
    parser.add_argument("--stats", action="store_true", help="打印统计信息")
    args = parser.parse_args()

    backlinks = build(verbose=True)

    OUT_FILE.write_text(
        json.dumps(backlinks, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    total_links = sum(len(v) for v in backlinks.values())
    print(f"✅ 写入 {OUT_FILE.relative_to(PROJECT_ROOT)}")
    print(f"   覆盖 {len(backlinks)} 个被引用页，共 {total_links} 条反向链接")

    if args.stats:
        # Top 10 最多被引用的页面
        top = sorted(backlinks.items(), key=lambda x: -len(x[1]))[:10]
        print("\n被引用最多的页面（Top 10）：")
        for pid, srcs in top:
            print(f"  {pid}: {len(srcs)} 条")


if __name__ == "__main__":
    main()
