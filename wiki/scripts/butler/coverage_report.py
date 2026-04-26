#!/usr/bin/env python3
"""
coverage_report.py — W13 覆盖率报告与 gap 优先级队列生成

用法：
  python3 wiki/scripts/butler/coverage_report.py --summary           # 全局覆盖率概览
  python3 wiki/scripts/butler/coverage_report.py --chapter 087_李斯列传  # 单章详情
  python3 wiki/scripts/butler/coverage_report.py --gaps --top 30     # 输出 top gap 列表
  python3 wiki/scripts/butler/coverage_report.py --write-queue --max-new 20  # 写入 housekeeping_queue.md
  python3 wiki/scripts/butler/coverage_report.py --concepts          # 输出概念候选
"""

import re
import sys
import json
import argparse
from pathlib import Path
from datetime import date
from collections import defaultdict

SENTENCE_DIR = Path("wiki/logs/butler/sentence_index")
COVERAGE_DIR = Path("wiki/logs/butler/coverage_map")
SUMMARY_FILE = Path("wiki/logs/butler/coverage_summary.json")
QUEUE_FILE = Path("wiki/logs/butler/housekeeping_queue.md")
SEEDS_FILE = Path("wiki/data/concept_idiom_seeds.txt")

TODAY = date.today().isoformat()

# ─── 章节权重 ─────────────────────────────────────────────────────────────

CHAPTER_WEIGHTS = {}
for n in range(1, 13):
    CHAPTER_WEIGHTS[f"{n:03d}"] = 1.0   # 本纪
for n in range(13, 23):
    CHAPTER_WEIGHTS[f"{n:03d}"] = 0.3   # 表
for n in range(23, 31):
    CHAPTER_WEIGHTS[f"{n:03d}"] = 0.6   # 书
for n in range(31, 61):
    CHAPTER_WEIGHTS[f"{n:03d}"] = 0.9   # 世家
for n in range(61, 131):
    CHAPTER_WEIGHTS[f"{n:03d}"] = 0.8   # 列传


def chapter_weight(chapter_id: str) -> float:
    num = chapter_id.split("_")[0]
    return CHAPTER_WEIGHTS.get(num, 0.8)


def gap_score(unit: dict, chapter_id: str) -> float:
    """
    gap_score = chapter_weight × para_type_weight × text_density × entity_density
    """
    cw = chapter_weight(chapter_id)
    para = unit.get("para", "")
    ptw = 0.4 if para.startswith("r") else 1.0
    td = min(unit.get("len", 0) / 20.0, 1.0)
    # entity_density: 粗估（含常见实体关键字则+0.3/个，上限1.0）
    text = unit.get("text", "")
    # 简单估算：句中人名/地名标记密度（用汉字长度作代理）
    ed = min(len(text) / 60.0, 1.0)
    return round(cw * ptw * td * ed, 3)


# ─── 概念候选检测 ──────────────────────────────────────────────────────────

def load_idiom_seeds() -> set[str]:
    if SEEDS_FILE.exists():
        return {l.strip() for l in SEEDS_FILE.read_text(encoding="utf-8").splitlines() if l.strip()}
    return set()


CONCEPT_PATTERNS = [
    re.compile(r'譬如(.{2,8})矣'),
    re.compile(r'此所谓(.{2,10})也'),
    re.compile(r'犹(.{2,8})[也矣]'),
    re.compile(r'如(.{2,8})矣'),
]
MAXIM_RE = re.compile(r'[必皆无不莫不]')


def detect_concept(text: str, idiom_seeds: set[str]) -> dict | None:
    """检测句子中是否含可提炼的抽象概念，返回候选信息或 None。"""
    # 1. 成语种子匹配（精确，优先级最高）
    for seed in idiom_seeds:
        if seed in text:
            return {"label": seed, "pattern": "idiom-seed", "summary": text}

    # 2. 喻比句模式（明确使用比喻结构）
    for pat in CONCEPT_PATTERNS:
        m = pat.search(text)
        if m:
            label = m.group(1).strip("，。！？；：")
            if 2 <= len(label) <= 8:
                return {"label": label, "pattern": "simile", "summary": text}

    return None


# ─── 数据加载 ─────────────────────────────────────────────────────────────

def load_chapter_data(chapter_stem: str) -> tuple[list[dict], list[dict]]:
    """加载单章的 sentence_index 和 coverage_map，返回 (units, covs)。"""
    si_file = SENTENCE_DIR / (chapter_stem + ".jsonl")
    cm_file = COVERAGE_DIR / (chapter_stem + ".jsonl")
    if not si_file.exists() or not cm_file.exists():
        return [], []
    units = [json.loads(l) for l in si_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    covs = [json.loads(l) for l in cm_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    return units, covs


def iter_all_chapters() -> list[str]:
    return sorted(p.stem for p in SENTENCE_DIR.glob("*.jsonl"))


# ─── 子命令实现 ───────────────────────────────────────────────────────────

def cmd_summary():
    if not SUMMARY_FILE.exists():
        print("❌ 尚未生成 coverage_summary.json，请先运行 build_coverage_map.py")
        return
    s = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
    total = s["total"]
    covered = s["covered"]
    rate = round(covered / total * 100, 1) if total else 0

    print(f"\n{'='*55}")
    print(f"  史记全文覆盖率报告  ({s.get('updated', TODAY)})")
    print(f"{'='*55}")
    print(f"  总句子数:    {total:>8,}")
    print(f"  已覆盖:      {covered:>8,}  ({rate}%)")
    print(f"  quote 覆盖:  {s.get('quote',0):>8,}")
    print(f"  para 覆盖:   {s.get('para',0):>8,}")
    print(f"  entity 覆盖: {s.get('entity',0):>8,}")
    print(f"  gap (缺口):  {s.get('gap',0):>8,}  ({round(s.get('gap',0)/total*100,1) if total else 0}%)")
    print(f"{'='*55}")

    chapters = s.get("chapters", {})
    if chapters:
        ranked = sorted(chapters.items(), key=lambda x: x[1].get("coverage_rate", 0))
        print("\n  覆盖率最低10章（最需补全）：")
        for ch, st in ranked[:10]:
            bar = "█" * int(st["coverage_rate"] / 5) + "░" * (20 - int(st["coverage_rate"] / 5))
            print(f"    {ch:<30s} {bar} {st['coverage_rate']:>5.1f}%  gap={st.get('gap',0)}")
        print("\n  覆盖率最高10章：")
        for ch, st in ranked[-10:]:
            bar = "█" * int(st["coverage_rate"] / 5) + "░" * (20 - int(st["coverage_rate"] / 5))
            print(f"    {ch:<30s} {bar} {st['coverage_rate']:>5.1f}%")


def cmd_chapter(chapter_arg: str):
    stem = next((p.stem for p in SENTENCE_DIR.glob("*.jsonl") if chapter_arg in p.stem), None)
    if not stem:
        print(f"❌ 未找到章节: {chapter_arg}")
        return
    units, covs = load_chapter_data(stem)
    cov_map = {c["sid"]: c for c in covs}
    sid_to_unit = {u["sid"]: u for u in units}

    total = len(units)
    by_type: dict[str, int] = defaultdict(int)
    for c in covs:
        by_type[c["cover_type"]] += 1

    covered = total - by_type["gap"]
    rate = round(covered / total * 100, 1) if total else 0
    print(f"\n  {stem}  覆盖率 {rate}%  ({covered}/{total})")
    print(f"  quote={by_type['quote']}  para={by_type['para']}  entity={by_type['entity']}  gap={by_type['gap']}")
    print()

    gaps = [(cov_map[u["sid"]], u) for u in units if cov_map.get(u["sid"], {}).get("cover_type") == "gap"]
    scored = sorted(gaps, key=lambda x: gap_score(x[1], stem), reverse=True)
    print(f"  Top gap 句（按优先级排序）：")
    for cov, u in scored[:20]:
        sc = gap_score(u, stem)
        prio = "P1" if sc >= 0.6 else ("P2" if sc >= 0.3 else "P3")
        print(f"  [{prio} {sc:.2f}] {u['sid']}  「{u['text'][:35]}」")


def cmd_gaps(top: int):
    """跨所有章节，输出 top gap 句（按 gap_score 排序）。"""
    all_gaps = []
    for stem in iter_all_chapters():
        units, covs = load_chapter_data(stem)
        sid_to_unit = {u["sid"]: u for u in units}
        for c in covs:
            if c["cover_type"] == "gap":
                u = sid_to_unit.get(c["sid"])
                if u:
                    sc = gap_score(u, stem)
                    all_gaps.append((sc, stem, u))

    all_gaps.sort(key=lambda x: x[0], reverse=True)
    print(f"\n  全局 Top {top} gap 句（共 {len(all_gaps):,} 个缺口）\n")
    for sc, stem, u in all_gaps[:top]:
        prio = "P1" if sc >= 0.6 else ("P2" if sc >= 0.3 else "P3")
        print(f"  [{prio} {sc:.3f}] {u['sid']}")
        print(f"           「{u['text'][:60]}」")


def cmd_concepts():
    """检测所有 gap 句中的概念候选。"""
    idiom_seeds = load_idiom_seeds()
    candidates = []
    for stem in iter_all_chapters():
        units, covs = load_chapter_data(stem)
        sid_to_unit = {u["sid"]: u for u in units}
        for c in covs:
            u = sid_to_unit.get(c["sid"])
            if not u:
                continue
            hit = detect_concept(u["text"], idiom_seeds)
            if hit:
                hit["sid"] = u["sid"]
                hit["chapter"] = stem
                hit["covered"] = c["cover_type"] != "gap"
                candidates.append(hit)

    print(f"\n  概念候选：{len(candidates)} 条\n")
    for c in candidates:
        status = "✅已覆盖" if c["covered"] else "❌gap"
        print(f"  {status} [{c['pattern']}] {c['sid']}")
        print(f"    label=「{c['label']}」")
        print(f"    原文: 「{c['summary'][:60]}」")
        print()


def cmd_write_queue(max_new: int):
    """将高分 gap 写入 housekeeping_queue.md（H13 条目）。"""
    idiom_seeds = load_idiom_seeds()

    # 读取已有队列，避免重复
    existing = set()
    if QUEUE_FILE.exists():
        content = QUEUE_FILE.read_text(encoding="utf-8")
        existing = set(re.findall(r'`(\d{3}_[^.]+\.\S+)`', content))

    all_gaps: list[tuple[float, str, dict]] = []
    concept_candidates: list[dict] = []

    for stem in iter_all_chapters():
        units, covs = load_chapter_data(stem)
        sid_to_unit = {u["sid"]: u for u in units}
        for c in covs:
            if c["cover_type"] != "gap":
                continue
            u = sid_to_unit.get(c["sid"])
            if not u or u["sid"] in existing:
                continue
            sc = gap_score(u, stem)
            if sc >= 0.3:  # 只写 P1/P2
                all_gaps.append((sc, stem, u))
            # 概念检测（独立于 gap_score）
            hit = detect_concept(u["text"], idiom_seeds)
            if hit and u["sid"] not in existing:
                hit.update({"sid": u["sid"], "chapter": stem, "score": sc})
                concept_candidates.append(hit)

    all_gaps.sort(key=lambda x: x[0], reverse=True)
    top_gaps = all_gaps[:max_new]
    top_concepts = concept_candidates[:10]  # 概念候选最多10条

    if not top_gaps and not top_concepts:
        print("  没有新的 gap 需要写入（可能已全部在队列中）")
        return

    # 构建新条目
    lines = [
        f"\n\n<!-- W13 自动写入 {TODAY} -->\n",
        "## H13 句子缺口（W13 扫描结果）\n\n",
    ]

    # P1 条目
    p1 = [(sc, stem, u) for sc, stem, u in top_gaps if sc >= 0.6]
    p2 = [(sc, stem, u) for sc, stem, u in top_gaps if 0.3 <= sc < 0.6]

    if p1:
        lines.append(f"### P1 优先（gap_score ≥ 0.6）\n\n")
        for sc, stem, u in p1:
            lines.append(
                f"- [ ] **H13** 句子缺口: `{u['sid']}`\n"
                f"      文本: 「{u['text'][:60]}」（{u['len']}字）\n"
                f"      → 建议动作: 建页或补引文\n"
                f"      → 发现于: W13 扫描 {TODAY}, gap_score={sc}\n\n"
            )

    if p2:
        lines.append(f"### P2 积压（gap_score 0.3–0.6）\n\n")
        for sc, stem, u in p2[:15]:  # P2 最多15条
            lines.append(
                f"- [ ] **H13** 句子缺口: `{u['sid']}`\n"
                f"      文本: 「{u['text'][:60]}」（{u['len']}字）\n"
                f"      → gap_score={sc}\n\n"
            )

    # 概念候选条目
    if top_concepts:
        lines.append("### 概念新建候选（concept-candidate）\n\n")
        for hit in top_concepts:
            lines.append(
                f"- [ ] **H13** 概念新建: `{hit['sid']}` → concept页「{hit['label']}」\n"
                f"      原文: 「{hit['summary'][:60]}」\n"
                f"      触发模式: {hit['pattern']}\n"
                f"      → 建议动作: create-concept-page 「{hit['label']}」（含原文引文+哲学内涵）\n"
                f"      → 发现于: W13 概念检测 {TODAY}\n\n"
            )

    # 追加到队列文件
    with open(QUEUE_FILE, "a", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"  ✅ 写入 housekeeping_queue.md:")
    print(f"     P1 gap 条目: {len(p1)}")
    print(f"     P2 gap 条目: {min(len(p2), 15)}")
    print(f"     概念候选:    {len(top_concepts)}")


# ─── 入口 ─────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="W13 覆盖率报告工具")
    p.add_argument("--summary", action="store_true", help="全局覆盖率概览")
    p.add_argument("--chapter", type=str, help="单章详情（如 087 或 087_李斯列传）")
    p.add_argument("--gaps", action="store_true", help="输出 top gap 列表")
    p.add_argument("--top", type=int, default=30, help="输出 top N 条（默认30）")
    p.add_argument("--concepts", action="store_true", help="输出概念候选")
    p.add_argument("--write-queue", action="store_true", help="写入 housekeeping_queue.md")
    p.add_argument("--max-new", type=int, default=20, help="最多写入多少条（默认20）")
    args = p.parse_args()

    if args.summary:
        cmd_summary()
    elif args.chapter:
        cmd_chapter(args.chapter)
    elif args.gaps:
        cmd_gaps(args.top)
    elif args.concepts:
        cmd_concepts()
    elif args.write_queue:
        cmd_write_queue(args.max_new)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
