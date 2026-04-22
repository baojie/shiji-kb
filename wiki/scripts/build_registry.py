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

    out.write_text(json.dumps({
        "pages": pages,
        "alias_index": alias_index,
        "generated": datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[ok] {len(pages)} 页 / {len(alias_index)} 别名 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
