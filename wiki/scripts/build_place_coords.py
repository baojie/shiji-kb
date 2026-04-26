#!/usr/bin/env python3
"""
从 pages/ 中所有有 coords 的页面提取坐标，生成轻量级 place_coords.json。
供 route-map 插件在前端查询地点坐标，不污染全局 pages.json。

用法:
    python wiki/scripts/build_place_coords.py wiki/public/pages \
        --out wiki/public/data/place_coords.json
"""

from __future__ import annotations
import argparse
import json
import re
import sys
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
    ap.add_argument("pages_root")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    root = Path(args.pages_root).resolve()
    out = Path(args.out) if args.out else root.parent / "data" / "place_coords.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    coords: dict[str, list] = {}
    total = 0
    for md in sorted(root.rglob("*.md")):
        try:
            meta = parse_frontmatter(md.read_text(encoding="utf-8"))
        except Exception:
            continue
        c = meta.get("coords")
        if not c or not isinstance(c, list) or len(c) < 2:
            continue
        lon, lat = float(c[0]), float(c[1])
        label = meta.get("label") or md.stem
        pid = meta.get("id") or md.stem
        # index by label, id, slug, and aliases
        for key in {label, pid, md.stem}:
            if key and key not in coords:
                coords[key] = [lon, lat]
        for alias in meta.get("aliases") or []:
            if alias and alias not in coords:
                coords[alias] = [lon, lat]
        total += 1

    out.write_text(json.dumps(coords, ensure_ascii=False, separators=(',', ':')),
                   encoding="utf-8")
    print(f"[ok] {total} 个地点, {len(coords)} 个键名 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
