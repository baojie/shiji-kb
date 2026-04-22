#!/usr/bin/env python3
"""
计算 wiki 知识量 (K) 度量并追加到 timeline.

设计思路 (butler v0, 可反思):
  K = Σ_page  page_k
  page_k = log2(1 + bytes) × (1 + links_density) × type_weight × quality_norm

分解:
  - bytes: pages/<id>.md 字节数 (含前言 + 散文)
  - links_density: 正文 wikilink 数 / (bytes/1000), 封顶 5.0
  - type_weight: person/event/place 1.0, topic 0.8, surface 0.5, 其他 0.6
  - quality_norm: max(1, quality_score / 30), 封顶 3.0

同时输出各 type 小计 + 链接命中率 + 修订累计 + featured 页数, 便于诊断.

附加维度 (非 K, 但对齐到同一 timestamp 记到 snapshot):
  - page_count / page_count_by_type
  - total_bytes
  - total_wikilinks / resolved_wikilinks (命中 alias_index)
  - total_revisions
  - featured_count

输出:
  wiki/data/knowledge_timeline.jsonl  (追加一行 snapshot)
  wiki/data/knowledge_latest.json     (最近一次完整结果)

用法:
  python wiki/scripts/compute_knowledge.py
"""
from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # wiki/
SITE_ROOT = ROOT / "public"
PAGES_DIR = SITE_ROOT / "pages"
REGISTRY = SITE_ROOT / "pages.json"
HISTORY_DIR = SITE_ROOT / "history"
DATA_DIR = ROOT / "data"  # wiki/data

TYPE_WEIGHT = {
    "person": 1.0,
    "event":  1.0,
    "place":  1.0,
    "state":  1.0,
    "topic":  0.8,
    "chapter": 0.4,  # chapter stub 体量虚低, 权重压缩避免淹没
    "surface": 0.5,
}

WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)


def compute() -> dict:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    pages = registry["pages"]
    alias_index = registry.get("alias_index", {})

    total_k = 0.0
    total_bytes = 0
    total_wl = 0
    resolved_wl = 0
    by_type_count: dict[str, int] = {}
    by_type_k: dict[str, float] = {}
    featured_count = 0
    total_revisions = 0
    top_pages: list[tuple[str, float]] = []

    for pid, entry in pages.items():
        if entry.get("type") == "special":
            continue  # Special: 页不计入 K
        md_path = SITE_ROOT / entry["path"]
        if not md_path.exists():
            continue
        text = md_path.read_text(encoding="utf-8")
        body = FRONTMATTER_RE.sub("", text, count=1)
        size = len(body.encode("utf-8"))
        total_bytes += size

        wl_matches = WIKILINK_RE.findall(body)
        page_wl = len(wl_matches)
        total_wl += page_wl
        for target in wl_matches:
            if target in alias_index or target in pages:
                resolved_wl += 1

        # 计算 page_k
        type_ = entry.get("type", "") or "topic"
        tw = TYPE_WEIGHT.get(type_, 0.6)
        qscore = entry.get("quality_score") or 0
        qnorm = min(max(1.0, qscore / 30.0), 3.0)
        dens_raw = page_wl / max(size / 1000.0, 0.1)
        dens = min(dens_raw, 5.0)
        page_k = math.log2(1 + size) * (1 + dens) * tw * qnorm

        total_k += page_k
        by_type_count[type_] = by_type_count.get(type_, 0) + 1
        by_type_k[type_] = by_type_k.get(type_, 0.0) + page_k
        if entry.get("featured"):
            featured_count += 1

        # revision count
        hist = HISTORY_DIR / f"{pid}.json"
        if hist.exists():
            try:
                h = json.loads(hist.read_text(encoding="utf-8"))
                total_revisions += h.get("revision_count", 1)
            except Exception:
                pass

        top_pages.append((pid, page_k))

    top_pages.sort(key=lambda kv: kv[1], reverse=True)

    snapshot = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "K": round(total_k, 2),
        "page_count": len(pages),
        "page_count_by_type": by_type_count,
        "k_by_type": {t: round(v, 2) for t, v in by_type_k.items()},
        "total_bytes": total_bytes,
        "total_wikilinks": total_wl,
        "resolved_wikilinks": resolved_wl,
        "link_hit_rate": round(resolved_wl / total_wl, 4) if total_wl else 0.0,
        "total_revisions": total_revisions,
        "featured_count": featured_count,
        "top10_pages": [
            {"pid": p, "k": round(k, 2)} for p, k in top_pages[:10]
        ],
    }
    return snapshot


def main() -> int:
    snapshot = compute()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "knowledge_latest.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    timeline = DATA_DIR / "knowledge_timeline.jsonl"
    with timeline.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")

    # 同步 public/data (供前端 fetch)
    public_data = SITE_ROOT / "data"
    public_data.mkdir(parents=True, exist_ok=True)
    (public_data / "knowledge_latest.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # 同步 timeline (只追加最新一条, 前端 sparkline 用)
    pub_tl = public_data / "knowledge_timeline.jsonl"
    with pub_tl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")

    print(f"[K] {snapshot['K']}  pages={snapshot['page_count']}  "
          f"featured={snapshot['featured_count']}  "
          f"links={snapshot['resolved_wikilinks']}/{snapshot['total_wikilinks']} "
          f"({snapshot['link_hit_rate']*100:.1f}%)  "
          f"revs={snapshot['total_revisions']}  "
          f"bytes={snapshot['total_bytes']}")
    print(f"[top3] " + ", ".join(
        f"{t['pid']}({t['k']})" for t in snapshot["top10_pages"][:3]
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
