#!/usr/bin/env python3
"""
构建 pages.json 注册表 (给浏览器端 wikilink 解析用)。

用法:
    python scripts/wiki/build_registry.py <pages_root> [--out <pages.json>]

扫描 <pages_root> 下所有 .md, 读 YAML frontmatter, 产出:

    {
      "pages": {
        "person/刘邦": {
          "type": "person",
          "label": "刘邦",
          "aliases": ["高祖", "沛公", ...],
          "path": "pages/person/刘邦.md"
        },
        ...
      },
      "alias_index": {
        "刘邦":   "person/刘邦",
        "高祖":   "person/刘邦",
        "沛公":   "person/刘邦",
        ...
      },
      "generated": "2026-04-22T09:20:00"
    }

冲突处理:
    alias_index 遇到重复键时保留首个并打印 warning, 避免误指。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pages_root", help="pages/ 目录所在根路径")
    ap.add_argument("--out", default=None,
                    help="输出 pages.json (默认: <pages_root>/../pages.json)")
    args = ap.parse_args()

    root = Path(args.pages_root).resolve()
    if not root.exists():
        print(f"[error] 目录不存在: {root}", file=sys.stderr)
        return 1
    site_root = root.parent  # 约定: pages/ 的父目录 = 站点根
    out = Path(args.out) if args.out else site_root / "pages.json"

    pages: dict[str, dict] = {}
    alias_index: dict[str, str] = {}
    alias_conflicts: list[tuple[str, str, str]] = []

    md_files = sorted(root.rglob("*.md"))
    for md in md_files:
        meta = parse_frontmatter(md.read_text(encoding="utf-8"))
        pid = meta.get("id")
        if not pid:
            # 如无 id, 按目录结构推导: pages/<type>/<slug>.md → <type>/<slug>
            rel = md.relative_to(root).with_suffix("")
            pid = rel.as_posix()
        entry = {
            "type": meta.get("type", ""),
            "label": meta.get("label", md.stem),
            "aliases": meta.get("aliases") or [],
            "tags": meta.get("tags") or [],
            "path": md.relative_to(site_root).as_posix(),
        }
        pages[pid] = entry

        # alias_index: 只收 label + aliases (不含 id; id 直接在 pages 里)
        for key in [entry["label"], *entry["aliases"]]:
            if not key:
                continue
            if key in alias_index and alias_index[key] != pid:
                alias_conflicts.append((key, alias_index[key], pid))
            else:
                alias_index[key] = pid

    for key, first, dup in alias_conflicts:
        print(f"[warn] 别名冲突: '{key}' → 保留 {first}, 忽略 {dup}",
              file=sys.stderr)

    # 若存在 wiki/data/semantic.json, 合并 total_refs / total_chapters / lifespan
    # 给首页卡片与搜索结果用. 路径: site_root/../data/semantic.json
    semantic_path = site_root.parent / "data" / "semantic.json"
    enriched = 0
    if semantic_path.exists():
        try:
            semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
            ents = semantic.get("entities", {})
            for pid, entry in pages.items():
                e = ents.get(pid)
                if not e:
                    continue
                if e.get("total_refs") is not None:
                    entry["total_refs"] = e["total_refs"]
                if e.get("total_chapters") is not None:
                    entry["total_chapters"] = e["total_chapters"]
                if e.get("lifespan"):
                    entry["lifespan"] = e["lifespan"]
                enriched += 1
            print(f"[enrich] {enriched} 页注入 semantic.json 数据")
        except Exception as exc:
            print(f"[warn] semantic.json 合并失败: {exc}", file=sys.stderr)

    # 计算 quality_score 用于首页 featured 动态排序.
    # 设计 (butler v0, 可反思调整):
    #   base = total_refs // 20 (0-30 分)
    #   + tag_bonus = min(len(tags), 4) * 2  (0-8)
    #   + rev_bonus = min(revision_count - 1, 5) * 3  (0-15, 鼓励多次编辑)
    #   + size_bonus = (size // 500) 到 max 10  (0-10, 越长越好)
    #   + manual_bonus = 5 (auto_generated != true)
    # 总分大概 0-70, featured 取高分前 N
    history_dir = site_root / "history"
    score_details = 0
    for pid, entry in pages.items():
        base = (entry.get("total_refs") or 0) // 20
        tag_bonus = min(len(entry.get("tags") or []), 4) * 2

        # 从 history/<pid>.json 读 revision_count 和 size
        rev_count = 1
        size = 0
        hist_json = history_dir / f"{pid}.json"
        if hist_json.exists():
            try:
                h = json.loads(hist_json.read_text(encoding="utf-8"))
                rev_count = h.get("revision_count", 1)
                if h.get("revisions"):
                    size = h["revisions"][0].get("size", 0)
            except Exception:
                pass
        rev_bonus = min(max(rev_count - 1, 0), 5) * 3
        size_bonus = min(size // 500, 10)

        # 是否手工精修
        md_path = root / entry["path"][len("pages/"):]
        manual_bonus = 5  # default 给予手写
        try:
            md_text = md_path.read_text(encoding="utf-8")
            if "auto_generated: true" in md_text:
                manual_bonus = 0
        except Exception:
            pass

        entry["quality_score"] = (
            base + tag_bonus + rev_bonus + size_bonus + manual_bonus
        )
        entry["_score_parts"] = {
            "base_refs": base, "tags": tag_bonus, "revs": rev_bonus,
            "size": size_bonus, "manual": manual_bonus,
        }
        score_details += 1
    print(f"[enrich] {score_details} 页计算了 quality_score")

    out.write_text(json.dumps({
        "pages": pages,
        "alias_index": alias_index,
        "generated": datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[ok] {len(pages)} 页 / {len(alias_index)} 别名 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
