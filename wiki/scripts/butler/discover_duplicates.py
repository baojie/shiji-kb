#!/usr/bin/env python3
"""
discover_duplicates.py — W10 内务整理：扫描标题相似的重复页面，
写入 housekeeping_queue.md 的 H1 条目。

检测策略（按优先级）：
  P0 — 相同前 N 字共享 + 行数差异 < 3x（内容可能重叠）
  P1 — 相同前 N 字但规模差异大（可能是 stub + 完整版）
  P2 — 关键词高度重叠（基于分词后 Jaccard）

假阳性过滤（不写入队列的情况）：
  - 规范页 type=person，冗余页均为 event/story/sanwen/stub → 人物+事件子页，跳过
  - 冗余页标题是系列（仅中间一字实体不同，如"张仪说X王"系列）→ 跳过
  - 冗余页均已是 type=redirect → 跳过

用法:
  python3 wiki/scripts/butler/discover_duplicates.py
  python3 wiki/scripts/butler/discover_duplicates.py --dry-run   # 只打印，不写队列
  python3 wiki/scripts/butler/discover_duplicates.py --min-prefix 2
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES_DIR = ROOT / "wiki/public/pages"
QUEUE_FILE = ROOT / "wiki/logs/butler/housekeeping_queue.md"

# 不参与重复检测的前缀（单字/常见歧义字）
SKIP_PREFIXES = {"A", "Special", "index"}

# 章节页前缀（数字开头）不参与
CHAPTER_PAT = re.compile(r"^\d{3}_")

# 分隔符：用于提取标题关键词
SPLIT_PAT = re.compile(r"[：:：\s\-–—·・]+")

# 人物页型
PERSON_TYPES = {"person"}
# 事件/子页型（不作为独立重复检测目标）
SUB_EVENT_TYPES = {"event", "story", "sanwen", "stub", "chapter"}
# 同主题系列词（出现在标题中间表示系列，不是重复）—— 常见的"X王"实体词
SERIES_TOKENS = {
    "楚王", "燕王", "赵王", "韩王", "齐王", "魏王", "秦王", "越王",
    "楚怀王", "宋王", "吴王", "梁王", "淮南王",
}


def read_frontmatter_type(slug: str) -> str:
    """读取页面 YAML frontmatter 中的 type 字段，返回小写字符串。"""
    md = PAGES_DIR / f"{slug}.md"
    try:
        text = md.read_text(encoding="utf-8")
    except Exception:
        return ""
    # 只读 frontmatter 块（第一个 --- 到第二个 ---）
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    fm = text[3:end]
    m = re.search(r"^type:\s*(\S+)", fm, re.MULTILINE)
    return m.group(1).strip('"\'').lower() if m else ""


def is_series_group(canonical: str, redundants: list[str]) -> bool:
    """
    检测是否为系列页组（如"张仪说X王连横"），而非真正重复。
    判据：所有冗余页标题与规范页只在某一 SERIES_TOKEN 位置不同。
    """
    for r in redundants:
        replaced = r
        for tok in SERIES_TOKENS:
            replaced = replaced.replace(tok, "〈X〉")
        canon_replaced = canonical
        for tok in SERIES_TOKENS:
            canon_replaced = canon_replaced.replace(tok, "〈X〉")
        # 去掉系列词后若两者仍相同，是真系列
        if replaced == canon_replaced:
            return True
    return False


def load_pages() -> dict[str, int]:
    """返回 {slug: 文件行数}，跳过章节页、Special 页和 redirect 页。"""
    result = {}
    for md in PAGES_DIR.glob("*.md"):
        slug = md.stem
        if CHAPTER_PAT.match(slug):
            continue
        if slug.startswith("Special"):
            continue
        page_type = read_frontmatter_type(slug)
        if page_type == "redirect":
            continue  # REDIRECT 页已处理过，不参与扫描
        try:
            lines = md.read_text(encoding="utf-8").count("\n")
        except Exception:
            lines = 0
        result[slug] = lines
    return result


def prefix_groups(pages: dict[str, int], min_len: int = 3) -> dict[str, list[str]]:
    """按标题前 min_len 个字符分组，返回有 2+ 成员的组。"""
    groups: dict[str, list[str]] = defaultdict(list)
    for slug in pages:
        key = slug[:min_len]
        if len(key) < min_len:
            continue
        groups[key].append(slug)
    return {k: v for k, v in groups.items() if len(v) >= 2}


def keyword_set(slug: str) -> set[str]:
    """把 slug 拆成关键词集合（按分隔符 + 每个汉字都算一个词）。"""
    parts = SPLIT_PAT.split(slug)
    words: set[str] = set()
    for p in parts:
        if not p:
            continue
        words.add(p)
        # 汉字逐字
        for ch in p:
            if "一" <= ch <= "鿿":
                words.add(ch)
    return words


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def score_group(slugs: list[str], pages: dict[str, int]) -> tuple[str, list[str]]:
    """选出组内最长的作为规范页，其余为冗余候选。"""
    by_lines = sorted(slugs, key=lambda s: pages.get(s, 0), reverse=True)
    return by_lines[0], by_lines[1:]


def already_in_queue(queue_text: str, slug: str) -> bool:
    return f"**{slug}**" in queue_text or f"`{slug}`" in queue_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-prefix", type=int, default=3, help="前缀最小长度（字符数）")
    ap.add_argument("--max-new", type=int, default=10, help="最多往队列写入 N 条")
    args = ap.parse_args()

    pages = load_pages()
    groups = prefix_groups(pages, min_len=args.min_prefix)

    today = date.today().isoformat()
    queue_text = QUEUE_FILE.read_text(encoding="utf-8") if QUEUE_FILE.exists() else ""

    new_entries: list[str] = []

    for prefix, slugs in sorted(groups.items(), key=lambda x: -len(x[1])):
        if len(new_entries) >= args.max_new:
            break

        canonical, redundants = score_group(slugs, pages)
        can_lines = pages.get(canonical, 0)

        # 进一步用 Jaccard 过滤：只留下与规范页关键词相似度 > 0.3 的
        can_kw = keyword_set(canonical)
        true_redundants = []
        for r in redundants:
            j = jaccard(can_kw, keyword_set(r))
            if j >= 0.3:
                true_redundants.append((r, pages.get(r, 0), j))

        if not true_redundants:
            continue

        # 过滤假阳性1：规范页是人物页，冗余页都是事件/子页 → 跳过
        can_type = read_frontmatter_type(canonical)
        red_types = {read_frontmatter_type(r) for r, _, _ in true_redundants}
        if can_type in PERSON_TYPES:
            if red_types <= SUB_EVENT_TYPES | PERSON_TYPES:
                continue  # 人物页 + 事件子页，不是重复

        # 过滤假阳性2：冗余列表中含人物页 → 人物页不能被合并进概念页
        if red_types & PERSON_TYPES:
            continue

        # 过滤假阳性3：所有页均为事件/子页且数量 >=3 → 很可能是事件系列，不是重复
        all_types = red_types | {can_type}
        if all_types <= SUB_EVENT_TYPES and len(true_redundants) >= 2:
            continue  # 同级事件系列，跳过（如"济北王反/兴居反/志徙菑川"）

        # 过滤假阳性5：冗余页标题全部以规范页标题为前缀（人物+活动模式）
        # 如 canonical=魏文侯, redundants=[魏文侯变法, 魏文侯礼贤, ...] → 跳过
        can_len = len(canonical)
        if all(r[:can_len] == canonical for r, _, _ in true_redundants):
            continue  # 规范页名是所有冗余页名的前缀 → 活动系列，不是重复

        # 过滤假阳性4：系列页（张仪说X王 等）→ 跳过
        if is_series_group(canonical, [r for r, _, _ in true_redundants]):
            continue

        # 跳过已在队列里的
        if already_in_queue(queue_text, canonical):
            continue

        # 优先级：冗余页越多、内容越接近 → P0
        priority = "P0" if len(true_redundants) >= 2 else "P1"

        lines_info = f"{can_lines}行"
        redundant_list = "\n".join(
            f"      - `{r}` ({rl}行, jaccard={j:.2f})"
            for r, rl, j in sorted(true_redundants, key=lambda x: -x[2])
        )
        entry = (
            f"- [ ] **H1** 融合重复页 → 规范页：`{canonical}` ({lines_info})\n"
            f"      冗余候选（读取后融合进规范页，改为 REDIRECT）：\n"
            f"{redundant_list}\n"
            f"      → 发现: {today} discover_duplicates 扫描\n"
        )

        new_entries.append((priority, entry))
        print(f"[{priority}] {canonical} ← {[r for r,_,_ in true_redundants]}")

    if not new_entries:
        print("未发现新的重复候选，队列无需更新。")
        return

    if args.dry_run:
        print("\n--- 将写入以下条目（dry-run，未实际写入）---")
        for p, e in new_entries:
            print(e)
        return

    # 写入队列：按优先级插入对应 section
    p0_entries = [e for p, e in new_entries if p == "P0"]
    p1_entries = [e for p, e in new_entries if p == "P1"]

    def insert_after_header(text: str, header: str, entries: list[str]) -> str:
        idx = text.find(header)
        if idx == -1:
            # section 不存在，追加
            text += f"\n{header}\n\n" + "".join(entries) + "\n"
            return text
        # 找到 header 后的第一个空行
        after = text.find("\n", idx) + 1
        return text[:after] + "\n" + "".join(entries) + text[after:]

    if p0_entries:
        queue_text = insert_after_header(queue_text, "## P0", p0_entries)
    if p1_entries:
        queue_text = insert_after_header(queue_text, "## P1", p1_entries)

    # 更新 "最后更新" 行
    queue_text = re.sub(r"最后更新: [\d\-]+", f"最后更新: {today}", queue_text)

    QUEUE_FILE.write_text(queue_text, encoding="utf-8")
    print(f"\n✓ 写入 {len(new_entries)} 条到 {QUEUE_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
