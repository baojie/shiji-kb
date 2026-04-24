#!/usr/bin/env python3
"""
find_unsourced.py — 扫描缺少史记原文溯源的 wiki 页面，
用 find_pn_for_quote 在原文中查找 PN，输出可加入队列的建议。

策略：
  1. 找到没有 sources/event_ids/pn 字段的 person/concept/overview/skill 页面
  2. 对每个页面，用 canonical_name（≥3字）在 chapter_md/*.tagged.md 原文中匹配
  3. 返回匹配段落的 PN（章节号.段落号）和原文片段
  4. 输出建议的 pn、sources、引文文本

用法:
  python3 wiki/scripts/butler/find_unsourced.py
  python3 wiki/scripts/butler/find_unsourced.py --max 20 --min-chars 3
  python3 wiki/scripts/butler/find_unsourced.py --target 韩王成
  python3 wiki/scripts/butler/find_unsourced.py --write-queue  # 写入 housekeeping_queue
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES_DIR = ROOT / "wiki/public/pages"
QUEUE_FILE = ROOT / "wiki/logs/butler/housekeeping_queue.md"

# 把 scripts/ 加入路径，以便 import find_pn_for_quote
sys.path.insert(0, str(ROOT / "scripts"))
from find_pn_for_quote import load_index, find_pn  # noqa: E402

CHAPTER_PAT = re.compile(r"^\d{3}_")

# 页面类型：这些类型的页面应该有史记溯源
SOURCED_TYPES = {"person", "event", "concept", "overview", "skill", "story"}
# 不需要溯源的类型
SKIP_TYPES = {"redirect", "chapter", "special", "disambiguation", "侯国",
              "年表", "sanwen", "stub"}


def read_frontmatter(path: Path) -> dict:
    """读取 YAML frontmatter，返回 {key: raw_value} 字典。"""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm_text = text[3:end]
    result = {}
    for line in fm_text.splitlines():
        m = re.match(r'^(\w[\w_]*):\s*(.*)', line)
        if m:
            result[m.group(1)] = m.group(2).strip().strip('"\'')
    return result


def has_sourcing(path: Path) -> bool:
    """检查页面是否已有溯源字段。"""
    text = path.read_text(encoding="utf-8")
    return ("sources:" in text or "event_ids:" in text
            or "::: meta" in text or "pn:" in text)


def get_canonical_name(fm: dict, slug: str) -> str:
    """获取规范名称，优先 canonical_name > label > slug。"""
    name = fm.get("canonical_name") or fm.get("label") or slug
    return name.strip().strip('"\'').strip()


def load_pn_citations(name: str, index: list, min_chars: int = 3,
                      top_n: int = 5, min_score: float = 0.8) -> list[dict]:
    """
    在原文索引（chapter_md/*.tagged.md）中查找含 name 的段落。
    返回 [{pn, chapter_num, chapter_title, score, quote}]
    只返回 score >= min_score 的结果（默认 0.8，避免模糊误链）。
    """
    if len(name) < min_chars:
        return []

    raw = find_pn(name, index, top_n=top_n)
    results = []
    for score, entry in raw:
        if score < min_score:
            continue
        results.append({
            "pn": entry["pn"],
            "chapter_num": entry["chapter_num"],
            "chapter_title": entry["chapter_title"],
            "score": score,
            "quote": entry["text_raw"],
        })
    return results


def format_suggestion(slug: str, name: str, citations: list[dict]) -> str:
    """格式化一条建议输出。"""
    chapters = sorted({f"{c['chapter_num']}_{c['chapter_title']}" for c in citations})
    pns = [f"({c['chapter_num']}-{c['pn']})" for c in citations]
    lines = [
        f"\n## {slug}",
        f"  canonical_name: {name}",
        f"  建议 sources: [{', '.join(dict.fromkeys(c['chapter_title'] for c in citations))}]",
        f"  建议 pn: [{', '.join(pns)}]",
        f"  原文段落（≤3条）：",
    ]
    for c in citations[:3]:
        pn_label = f"({c['chapter_num']}-{c['pn']})"
        q = c["quote"][:120]
        lines.append(f"    {pn_label} [{c['score']:.2f}] > {q}…")
    return "\n".join(lines)


def format_queue_entry(slug: str, name: str, citations: list[dict]) -> str:
    """格式化 housekeeping_queue.md 的 H4 条目。"""
    from datetime import date
    today = date.today().isoformat()
    source_titles = sorted({c["chapter_title"] for c in citations})
    pns = [f"({c['chapter_num']}-{c['pn']})" for c in citations]
    quote_lines = ""
    for c in citations[:2]:
        pn_label = f"({c['chapter_num']}-{c['pn']})"
        q = c["quote"][:100]
        quote_lines += f"\n      原文 {pn_label}: > {q}…"
    return (
        f"- [ ] **H4** 溯源增补：`{slug}`\n"
        f"      建议 sources: [{', '.join(source_titles)}]\n"
        f"      建议 pn: [{', '.join(pns)}]"
        f"{quote_lines}\n"
        f"      → 发现: {today} find_unsourced 扫描\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=20, help="最多处理 N 个页面")
    ap.add_argument("--min-chars", type=int, default=3, help="canonical_name 最少字符数")
    ap.add_argument("--min-score", type=float, default=0.8, help="原文匹配最低分数（默认 0.8）")
    ap.add_argument("--top", type=int, default=5, help="每页最多返回 N 个 PN（默认 5）")
    ap.add_argument("--target", help="只处理指定 slug")
    ap.add_argument("--write-queue", action="store_true", help="写入 housekeeping_queue.md")
    ap.add_argument("--type", dest="page_type", help="只处理指定 type")
    ap.add_argument("--rebuild-index", action="store_true", help="强制重建原文索引缓存")
    args = ap.parse_args()

    print("[find_unsourced] 加载原文索引…", file=sys.stderr)
    index = load_index(force_rebuild=args.rebuild_index)

    processed = 0
    queue_entries = []

    targets = [PAGES_DIR / f"{args.target}.md"] if args.target else sorted(PAGES_DIR.glob("*.md"))

    for md_path in targets:
        if not md_path.name.endswith(".md"):
            continue
        slug = md_path.stem

        # 跳过章节页
        if CHAPTER_PAT.match(slug):
            continue

        fm = read_frontmatter(md_path)
        page_type = fm.get("type", "").strip('"\'').lower()

        if page_type in SKIP_TYPES:
            continue
        if page_type not in SOURCED_TYPES and not args.target:
            continue
        if args.page_type and page_type != args.page_type:
            continue

        # 跳过已有溯源的页面
        if has_sourcing(md_path) and not args.target:
            continue

        name = get_canonical_name(fm, slug)
        if len(name) < args.min_chars and not args.target:
            continue

        citations = load_pn_citations(name, index,
                                      min_chars=args.min_chars,
                                      top_n=args.top,
                                      min_score=args.min_score)
        if not citations and not args.target:
            continue

        print(format_suggestion(slug, name, citations))
        queue_entries.append((slug, name, citations))
        processed += 1

        if processed >= args.max and not args.target:
            break

    print(f"\n共找到 {len(queue_entries)} 个可溯源页面")

    if args.write_queue and queue_entries:
        queue_text = QUEUE_FILE.read_text(encoding="utf-8") if QUEUE_FILE.exists() else ""
        new_entries = ""
        skipped = 0
        for slug, name, citations in queue_entries:
            if f"`{slug}`" in queue_text:
                skipped += 1
                continue
            new_entries += format_queue_entry(slug, name, citations)

        if new_entries:
            header = "## P1（本周内处理）"
            idx = queue_text.find(header)
            if idx == -1:
                queue_text += f"\n### H4 溯源增补（find_unsourced 发现）\n\n{new_entries}"
            else:
                after = queue_text.find("\n", idx) + 1
                queue_text = (queue_text[:after]
                              + "\n### H4 溯源增补\n\n"
                              + new_entries
                              + queue_text[after:])
            QUEUE_FILE.write_text(queue_text, encoding="utf-8")
            print(f"✓ 写入 {len(queue_entries) - skipped} 条（跳过 {skipped} 条已在队列）")
        else:
            print("所有条目均已在队列中")


if __name__ == "__main__":
    main()
