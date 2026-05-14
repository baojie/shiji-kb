#!/usr/bin/env python3
"""发现《史记》未标注文字中的候选实体。

设计目标：
  回答"这章还有什么词应该标但没标"。做法是：
    1. 读 chapter_md/*.tagged.md
    2. 用 semantic_tags.strip_markup 剥离所有标注 → 得到纯未标文本
    3. 在未标文本上做 2–4 字 n-gram 频次统计
    4. 可选：用词表（如律历/名物常用词）交叉过滤，只输出命中词表的候选
    5. 输出按频次降序的 TSV/MD

互补定位（三个候选发现脚本）：
  - `scripts/scan_untagged_aliases.py`    — 扫 **已知实体**（在 entity_index 中）的漏标
  - `scripts/scan_sanwen_candidates.py`   — 扫 **散文候选**（按触发短语和长度）
  - `scripts/find_candidate_entities.py`  — 本脚本：扫 **未知候选实体**（按 n-gram 频次 + 词表）

用法：
    # 全书 2-4 gram，频次 >= 5
    python scripts/find_candidate_entities.py --all --min-freq 5

    # 单章，且只输出名物/律历候选
    python scripts/find_candidate_entities.py --chapter 027 --filter mingwu

    # 自定义词表
    python scripts/find_candidate_entities.py --all --filter-file mywords.txt

输出：
    data/candidates/{chapter_id}_candidates.tsv
    data/candidates/summary.md
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

CHAPTER_DIR = ROOT / "chapter_md"
OUT_DIR = ROOT / "doc" / "analysis" / "candidates"
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]+")

# 去除 Markdown 结构 + **完全抹掉**标注片段（包含内容，不保留），使得已标注
# 内容不会被当作未标注候选再次捕获。抹除时用换行替换，切断跨标注的 n-gram。
NOUN_TAG_RE = re.compile(r"〖[@=;#%&◆^~•!?+{:\[_$][^〖〗]*〗")
VERB_TAG_RE = re.compile(r"⟦[◈◉○◇][^⟦⟧]*⟧")
PARA_NUM_RE = re.compile(r"^\[\d+(?:\.\d+)*\]\s*", re.MULTILINE)
HEADER_RE = re.compile(r"^#{1,6}.*$", re.MULTILINE)
LIST_RE = re.compile(r"^\s*[-*]\s+", re.MULTILINE)
TABLE_SEP_RE = re.compile(r"^\|[\s\-|]+\|?\s*$", re.MULTILINE)
HR_RE = re.compile(r"^-{3,}\s*$", re.MULTILINE)


def extract_unannotated(text: str) -> str:
    """移除所有标注（含内容）和 Markdown 结构，返回仅剩的未标注纯文本。
    标注位置以换行占位，防止跨标注的 n-gram 伪合并。"""
    text = HEADER_RE.sub("", text)
    text = PARA_NUM_RE.sub("", text)
    text = LIST_RE.sub("", text)
    text = HR_RE.sub("", text)
    text = TABLE_SEP_RE.sub("", text)
    text = NOUN_TAG_RE.sub("\n", text)
    text = VERB_TAG_RE.sub("\n", text)
    return text

# 内置词表：典型名物候选（律历/制度/礼仪/五行五色五音/天文名物）
# 仅用于 --filter mingwu；用户可用 --filter-file 覆盖
MINGWU_KEYWORDS = {
    # 律历·历法
    "岁首", "正朔", "朔日", "望日", "晦日", "朔望", "上弦", "下弦",
    "夏正", "殷正", "周正", "秦正", "建寅", "建丑", "建子", "建亥",
    "春分", "秋分", "夏至", "冬至", "立春", "立夏", "立秋", "立冬",
    "闰月", "闰年", "节气", "二十四节气", "七政", "五纪",
    # 五行·阴阳·五色·五音·五方
    "五行", "五色", "五音", "五方", "五味", "五气", "五常", "五常",
    "阴阳", "阴气", "阳气", "太阴", "太阳",
    "宫商", "角徵羽", "黄锺", "大吕", "太簇",
    # 天文·名物制度
    "分野", "天道", "天命", "天数", "天意", "天变",
    "二十八宿", "三垣", "三光", "日月星辰",
    # 礼仪·封禅
    "郊祭", "郊祀", "封禅", "社稷", "宗庙", "明堂", "辟雍",
    "大祭", "禘祭", "尝祭", "祭天", "祭地",
    # 军制·爵制·刑名
    "车马", "干戈", "旌旗", "金鼓", "烽燧",
    "九品", "九锡", "三公", "九卿", "八佾",
    # 度量衡·钱币
    "权衡", "尺寸", "斗斛", "铢两",
}


def parse_chapter(path: Path) -> tuple[str, str]:
    """返回 (章节号, 未标注部分的纯文本 — 已标注内容完全移除)。"""
    m = re.match(r"^(\d{3})_(.+)\.tagged\.md$", path.name)
    chapter_id = m.group(1) if m else path.stem
    raw = path.read_text(encoding="utf-8")
    unannotated = extract_unannotated(raw)
    return chapter_id, unannotated


def ngrams(text: str, n: int) -> list[str]:
    """从 CJK 连续字段里抽 n-gram。"""
    grams: list[str] = []
    for m in CJK_RE.finditer(text):
        run = m.group()
        if len(run) < n:
            continue
        for i in range(len(run) - n + 1):
            grams.append(run[i : i + n])
    return grams


def collect_candidates(
    files: list[Path],
    n_values: tuple[int, ...] = (2, 3, 4),
    min_freq: int = 5,
    keyword_filter: set[str] | None = None,
) -> tuple[dict[str, dict], dict[str, Counter]]:
    """返回 (全局 gram -> {freq,chapters}, 每章 gram -> Counter)。"""
    global_freq: dict[str, dict] = defaultdict(lambda: {"freq": 0, "chapters": set()})
    per_chapter: dict[str, Counter] = {}

    for f in files:
        chapter_id, stripped = parse_chapter(f)
        ch_counter: Counter = Counter()
        for n in n_values:
            for g in ngrams(stripped, n):
                if keyword_filter is not None and g not in keyword_filter:
                    continue
                ch_counter[g] += 1
                global_freq[g]["freq"] += 1
                global_freq[g]["chapters"].add(chapter_id)
        # 章级过滤后再看阈值
        ch_counter = Counter({k: v for k, v in ch_counter.items() if v >= 1})
        per_chapter[chapter_id] = ch_counter

    # 全局阈值过滤
    global_freq = {
        k: v for k, v in global_freq.items() if v["freq"] >= min_freq
    }
    return global_freq, per_chapter


def first_context(chapter_text: str, term: str, radius: int = 20) -> str:
    idx = chapter_text.find(term)
    if idx < 0:
        return ""
    left = max(0, idx - radius)
    right = min(len(chapter_text), idx + len(term) + radius)
    return ("…" if left > 0 else "") + chapter_text[left:right] + ("…" if right < len(chapter_text) else "")


def write_outputs(
    global_freq: dict, per_chapter: dict[str, Counter], files: list[Path]
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 每章 TSV
    path_by_id = {re.match(r"^(\d{3})_", f.name).group(1): f for f in files}
    for chapter_id, counter in per_chapter.items():
        if not counter:
            continue
        f_path = path_by_id[chapter_id]
        _, stripped = parse_chapter(f_path)
        tsv_path = OUT_DIR / f"{chapter_id}_candidates.tsv"
        lines = ["候选词\t频次\t长度\t上下文"]
        for term, freq in counter.most_common():
            ctx = first_context(stripped, term).replace("\t", " ")
            lines.append(f"{term}\t{freq}\t{len(term)}\t{ctx}")
        tsv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 汇总 MD
    summary = OUT_DIR / "summary.md"
    lines = [
        "# 未标注候选实体发现",
        "",
        f"扫描章数：{len(files)} · 候选词数（全局去重）：{len(global_freq)}",
        "",
        "## 全局 TOP 50（按总频次降序）",
        "",
        "| 候选词 | 长度 | 总频次 | 覆盖章数 |",
        "|--------|----:|------:|--------:|",
    ]
    sorted_global = sorted(
        global_freq.items(), key=lambda x: (-x[1]["freq"], -len(x[0]))
    )
    for term, info in sorted_global[:50]:
        lines.append(f"| {term} | {len(term)} | {info['freq']} | {len(info['chapters'])} |")
    lines.append("")
    lines.append("## 逐章候选清单")
    lines.append("")
    for chapter_id in sorted(per_chapter):
        counter = per_chapter[chapter_id]
        if not counter:
            continue
        fname = path_by_id[chapter_id].name.replace(".tagged.md", "")
        lines.append(f"- [{fname}](candidates/{chapter_id}_candidates.tsv) — {len(counter)} 候选")
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[输出] {summary.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="发现未标注候选实体")
    ap.add_argument("--chapter", help="单章（如 027），缺省扫全书")
    ap.add_argument("--all", action="store_true", help="扫全部 130 章")
    ap.add_argument("--n", default="2,3,4", help="n-gram 长度，逗号分隔，默认 2,3,4")
    ap.add_argument("--min-freq", type=int, default=5, help="全局最小频次，默认 5")
    ap.add_argument(
        "--filter",
        choices=["none", "mingwu"],
        default="none",
        help="内置词表过滤：none=不过滤（纯频次）；mingwu=仅输出律历/名物/五行等典型词",
    )
    ap.add_argument(
        "--filter-file",
        help="自定义词表（每行一词），覆盖内置词表",
    )
    args = ap.parse_args()

    if not args.chapter and not args.all:
        ap.error("必须指定 --chapter 或 --all 之一")

    if args.chapter:
        matches = list(CHAPTER_DIR.glob(f"{args.chapter}_*.tagged.md"))
        files = [f for f in matches if "backup" not in f.name]
    else:
        files = sorted(
            f for f in CHAPTER_DIR.glob("*.tagged.md") if "backup" not in f.name
        )

    if not files:
        print("未找到匹配章节。")
        return

    n_values = tuple(int(x) for x in args.n.split(","))

    keyword_filter: set[str] | None = None
    if args.filter_file:
        keyword_filter = set(
            w.strip()
            for w in Path(args.filter_file).read_text(encoding="utf-8").splitlines()
            if w.strip() and not w.startswith("#")
        )
    elif args.filter == "mingwu":
        keyword_filter = MINGWU_KEYWORDS

    print(
        f"[扫描] {len(files)} 章 · n={n_values} · min-freq={args.min_freq} "
        f"· filter={'关键词表 ' + str(len(keyword_filter)) if keyword_filter else '无'}"
    )

    global_freq, per_chapter = collect_candidates(
        files, n_values, args.min_freq, keyword_filter
    )

    if keyword_filter is not None:
        # 词表过滤模式下，min_freq 的语义仍然是全局阈值；提示用户
        print(f"[结果] 命中词表并满足阈值的候选：{len(global_freq)} 条")
    else:
        print(f"[结果] 满足阈值的候选：{len(global_freq)} 条")

    write_outputs(global_freq, per_chapter, files)


if __name__ == "__main__":
    main()
