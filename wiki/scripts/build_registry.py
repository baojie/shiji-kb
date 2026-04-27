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
import math
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
META_BLOCK_RE  = re.compile(r"^::: meta\s*\n(.*?)^:::", re.MULTILINE | re.DOTALL)
WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

# Must match compute_knowledge.py
_TYPE_WEIGHT = {
    "person": 1.0, "event": 1.0, "place": 1.0, "state": 1.0,
    "topic": 0.8, "chapter": 0.4, "surface": 0.5,
}


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
        md_text = md.read_text(encoding="utf-8")
        meta = parse_frontmatter(md_text)
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
            "quality": meta.get("quality", ""),
            "image": meta.get("image") or (
                (meta.get("images") or [{}])[0].get("file") or None
            ),
            "path": md.relative_to(site_root).as_posix(),
        }
        if meta.get("essay_type"):
            entry["essay_type"] = meta["essay_type"]
        # event_type lives in ::: meta block, not frontmatter
        mb = META_BLOCK_RE.search(md_text)
        if mb:
            em = re.search(r'^event_type:\s*(.+)$', mb.group(1), re.MULTILINE)
            if em:
                entry["event_type"] = em.group(1).strip()
        if meta.get("jun_title"):
            entry["jun_title"] = True
        if meta.get("sources"):
            entry["sources"] = meta["sources"]
        pages[pid] = entry

        # alias_index: 收 slug(文件名) + id + label + aliases
        # 单字 alias 跳过: 太通用，冲突率极高，搜索几乎无用
        slug = md.stem  # 文件名去掉 .md
        for key in [slug, pid, entry["label"], *entry["aliases"]]:
            if not key:
                continue
            if len(str(key)) < 2:  # 单字跳过
                continue
            if key in alias_index and alias_index[key] != pid:
                alias_conflicts.append((key, alias_index[key], pid))
            else:
                alias_index[key] = pid

    for key, first, dup in alias_conflicts:
        print(f"[warn] 别名冲突: '{key}' → 保留 {first}, 忽略 {dup}",
              file=sys.stderr)

    # W5 v4 提案 12: 冲突别名输出到文件供反思查看
    if alias_conflicts:
        conflict_data = {
            "generated": datetime.now().isoformat(timespec="seconds"),
            "count": len(alias_conflicts),
            "note": "surface 被多个 pages 作为 alias, 只保留第一个.",
            "conflicts": [
                {"alias": k, "kept": f, "ignored": d}
                for (k, f, d) in alias_conflicts
            ],
        }
        conflict_out = site_root.parent / "data" / "alias_conflicts.json"
        conflict_out.parent.mkdir(parents=True, exist_ok=True)
        conflict_out.write_text(
            json.dumps(conflict_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

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
                    ls = e["lifespan"]
                    if ls.get("birth") is not None:
                        entry["birth_ce"] = ls["birth"]
                    if ls.get("death") is not None:
                        entry["death_ce"] = ls["death"]
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

        # 从 history/<pid>.jsonl 读 revision_count 和 size（末行最新）
        rev_count = 1
        size = 0
        hist_jsonl = history_dir / f"{pid}.jsonl"
        if hist_jsonl.exists():
            try:
                lines = [ln for ln in hist_jsonl.read_text(encoding="utf-8").splitlines() if ln.strip()]
                rev_count = len(lines) or 1
                if lines:
                    latest = json.loads(lines[-1])
                    size = latest.get("size", 0)
            except Exception:
                pass
        rev_bonus = min(max(rev_count - 1, 0), 5) * 3
        size_bonus = min(size // 500, 10)

        # 是否手工精修 + narrative_bonus (W5 v3 提案 8)
        md_path = root / entry["path"][len("pages/"):]
        manual_bonus = 5
        narrative_bonus = 0
        try:
            md_text = md_path.read_text(encoding="utf-8")
            if "auto_generated: true" in md_text:
                manual_bonus = 0
            # body 里检查散文段落
            body = md_text.split("---", 2)[-1] if md_text.startswith("---") else md_text
            if "<!-- stub:" in body:
                narrative_bonus -= 5  # stub 明确惩罚
            if "*生卒依据*" in body or "[^ref" in body:
                narrative_bonus += 3  # 有引证加分 (user-req-4)
            # 散文段 = 既不是空行, 不以 | 开头, 不以 # 开头, 不以 - 开头
            prose_paras = 0
            for block in body.split("\n\n"):
                b = block.strip()
                if not b:
                    continue
                first = b.splitlines()[0].lstrip()
                # 过滤各种非散文: 标题 / 表格 / 列表 / 链接行 / 注释 / 代码块 / 引用
                if first.startswith(("#", "|", "-", "*", "<", "```", "> ", "[[")):
                    continue
                if len(b) < 20:
                    continue
                prose_paras += 1
            if prose_paras >= 2:
                narrative_bonus += 8
        except Exception:
            pass

        entry["quality_score"] = (
            base + tag_bonus + rev_bonus + size_bonus + manual_bonus + narrative_bonus
        )

        # K score per page (formula mirrors compute_knowledge.py)
        try:
            body_bytes = len(body.encode("utf-8"))
            page_wl = len(WIKILINK_RE.findall(body))
            tw = _TYPE_WEIGHT.get(entry.get("type") or "", 0.6)
            qnorm = min(max(1.0, entry["quality_score"] / 30.0), 3.0)
            dens = min(page_wl / max(body_bytes / 1000.0, 0.1), 5.0)
            entry["k_score"] = round(math.log2(1 + body_bytes) * (1 + dens) * tw * qnorm, 1)
        except Exception:
            pass

        score_details += 1
    print(f"[enrich] {score_details} 页计算了 quality_score 和 k_score")

    out.write_text(json.dumps({
        "pages": pages,
        "alias_index": alias_index,
        "generated": datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, separators=(',', ':')), encoding="utf-8")

    print(f"[ok] {len(pages)} 页 / {len(alias_index)} 别名 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
