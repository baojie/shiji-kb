#!/usr/bin/env python3
"""
扫描《史记》130篇 tagged.md 文件，基于触发短语识别散文候选（书信、诏令、策论、
奏疏/上书、檄文、议论）。

思路：
1. 触发短语列表（如 "乃上书曰"、"诏曰"、"报X书曰"）出现在某段，则把紧随其后
   的引号内容（全角 ""）或之后的段落块视为候选散文。
2. 以"去标注后纯文本字数"过滤：只保留 >= MIN_CHARS 的长篇。
3. 输出 TSV 与 Markdown 两份候选清单到 labs/planning/ 下，字段：
   章节号 | 类型 | 起段 | 止段 | 字数 | 触发短语 | 首句预览 | 建议标题

不修改任何 tagged.md 文件。
"""

from __future__ import annotations
import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict

ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = ROOT / "chapter_md"
OUT_DIR = ROOT / "labs" / "planning"

MIN_CHARS = 120  # 纯文本最短字数（过滤短诏/短对）

# 物品/文书类标记有时会包裹 "书"/"诏"/"疏" 等字（形如 〖•书〗）。
# 将这些字做成可选 tag-wrap 的子模式，避免触发正则被 〖〗 打断。
_SHU = r"(?:〖•)?书(?:〗)?"
_ZHAO = r"(?:〖•)?诏(?:〗)?"
_SHU_F = r"(?:〖•)?疏(?:〗)?"

# 类型 → 触发正则（段落中出现即视为候选起点）
TRIGGERS: list[tuple[str, str]] = [
    # 诏令
    ("诏令", rf"(?:乃)?下?{_ZHAO}(?:{_SHU})?曰"),
    ("诏令", rf"制(?:{_ZHAO}(?:御史|丞相|三公|[^。\n]{{0,8}})?)?曰"),
    ("诏令", rf"(?:有|乃){_ZHAO}(?:赐|报|答|问)[^。\n]{{0,20}}曰"),
    ("诏令", rf"手{_ZHAO}曰"),
    ("诏令", rf"制{_ZHAO}[^。\n]{{0,10}}"),
    ("诏令", rf"(?:於是|乃|遂)?上(?:乃)?(?:{_ZHAO}|下{_ZHAO})[^。\n]{{0,10}}曰"),
    # 奏疏/上书
    ("奏疏", rf"(?:乃|复|又|遂|从[^。\n]{{1,8}}中)?上{_SHU}(?:谏|言|曰)"),
    ("奏疏", rf"(?:乃|复)?上{_SHU_F}(?:谏|言)?曰"),
    ("奏疏", rf"奏(?:记|{_SHU}|议|{_SHU_F})?曰"),
    ("奏疏", r"(?:乃|遂)?上言曰"),
    # 书信（报/遗/与 X 书）
    ("书信", rf"(?:乃|遂|复)?(?:报|遗|遗以|与)[^。\n]{{0,25}}{_SHU}曰"),
    ("书信", rf"(?:乃|遂)?(?:遗|与)[^。\n]{{0,25}}{_SHU}[，。]"),
    # 书信（乃为书…遗X。书曰 — 如鲁连射聊城，跨段落）
    ("书信", rf"(?:乃|遂)?为{_SHU}[^\n]{{0,80}}遗[^。\n]{{0,20}}.{{0,20}}{_SHU}曰"),
    ("书信", rf"(?:乃|遂)?作{_SHU}[^。\n]{{0,40}}曰"),
    # 檄文
    ("檄文", rf"(?:乃|遂)?(?:移|为)?檄(?:文|{_SHU})?(?:告|谕|曰)"),
    ("檄文", r"谕[^。\n]{0,10}曰"),
    # 策论 / 议论（对策、论、议）
    ("策论", r"(?:乃|遂)?对(?:策)?曰"),
    ("议论", r"(?:贾生|贾谊|晁错|主父偃|徐乐|严安|董仲舒|邹阳)[^。\n]{0,30}曰"),
]

# 按章节章末"太史公曰"排除（那是论赞，另有索引）
TAISHIGONG_PAT = re.compile(r"^::: 太史公曰", re.MULTILINE)

PARA_HEADER = re.compile(r"^\[(\d+(?:\.\d+)*)\]\s*", re.MULTILINE)
TAG_PAT = re.compile(r"[〖⟦][^〗⟧]+[〗⟧]")
H2_PAT = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
BLOCK_FENCE = re.compile(r"^:::(?:\s+\S+)?\s*$", re.MULTILINE)


def strip_tags(text: str) -> str:
    return TAG_PAT.sub("", text)


@dataclass
class Candidate:
    chapter_num: str
    chapter_title: str
    type: str
    start_para: str
    end_para: str
    char_count: int
    trigger: str
    preview: str
    suggested_title: str
    section_heading: str  # 最近的 ## 标题


def parse_paragraphs(text: str) -> list[tuple[str, int, int]]:
    """返回 [(para_id, start_offset, end_offset), ...] 按文件顺序。"""
    matches = list(PARA_HEADER.finditer(text))
    paras = []
    for i, m in enumerate(matches):
        para_id = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        paras.append((para_id, start, end))
    return paras


def nearest_h2_before(text: str, offset: int) -> str:
    """找到 offset 之前最近的 ## 标题。"""
    last = ""
    for m in H2_PAT.finditer(text):
        if m.start() >= offset:
            break
        last = m.group(1).strip()
    return last


def in_fenced_block(text: str, offset: int) -> bool:
    """判断 offset 位置是否在 ::: xxx ... ::: 块内。"""
    fences = list(BLOCK_FENCE.finditer(text))
    depth = 0
    for f in fences:
        if f.start() >= offset:
            break
        depth ^= 1  # 简单切换：开/合
    return depth == 1


def extract_quoted_block(text: str, start: int) -> tuple[int, str] | None:
    """从 start 位置开始，找到紧随的全角左引号 " 并配对右引号 "，返回 (end, inner)。

    支持跨段落。若找不到返回 None。
    """
    lq = text.find("\u201c", start, start + 200)
    if lq < 0:
        return None
    # 配对（允许嵌套：记录层级）
    depth = 0
    i = lq
    while i < len(text):
        ch = text[i]
        if ch == "\u201c":
            depth += 1
        elif ch == "\u201d":
            depth -= 1
            if depth == 0:
                return i + 1, text[lq + 1 : i]
        i += 1
    return None


def find_paragraph_for_offset(paras: list[tuple[str, int, int]], offset: int) -> str:
    for pid, s, e in paras:
        if s <= offset < e:
            return pid
    return paras[-1][0] if paras else "?"


def suggest_title(section_heading: str, chapter_title: str, type_: str, preview: str) -> str:
    if section_heading and not re.fullmatch(r"\d+", section_heading):
        # 如果 H2 本身看起来像"谏逐客书"、"过秦论" 等，直接使用
        return section_heading
    return f"{chapter_title}·{type_}"


H2_TYPE_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("诏令", re.compile(r"诏(?!书志|书|献|书楼)|制诏|遗诏")),
    ("书信", re.compile(r"(?:^|[^曰])书$|书信|国书|回书|答书|谏书|书(?:谏|谕|对|曰)|遗.{0,3}书|射.{0,3}书")),
    ("策论", re.compile(r"过秦论|治安策|陈政事|削藩|论贵粟|论[^，。]{0,6}策|策$")),
    ("奏疏", re.compile(r"上书|上疏|奏议|奏请|上言|疏$|奏$")),
    ("议论", re.compile(r"^论|议$|辩$")),
    ("檄文", re.compile(r"檄|谕[^曰]{0,6}")),
]


def scan_h2_sections(text: str, chapter_num: str, chapter_title: str,
                     paras: list[tuple[str, int, int]],
                     seen_spans: list[tuple[int, int]]) -> list["Candidate"]:
    """基于 ## 标题识别散文段落。以 H2 为节起点，下一个 H2 为止。"""
    out: list[Candidate] = []
    h2s = list(H2_PAT.finditer(text))
    for i, m in enumerate(h2s):
        title = m.group(1).strip()
        matched_type = None
        for t, pat in H2_TYPE_PATTERNS:
            if pat.search(title):
                matched_type = t
                break
        if not matched_type:
            continue
        section_start = m.end()
        section_end = h2s[i + 1].start() if i + 1 < len(h2s) else len(text)
        # 跳过与 trigger 扫描重叠的区间
        if any(not (section_end <= a or section_start >= b) for a, b in seen_spans):
            continue
        body = text[section_start:section_end]
        pure = strip_tags(body)
        pure = re.sub(r"\[\d+(?:\.\d+)*\]\s*", "", pure)
        pure = re.sub(r"\s+", "", pure)
        pure = re.sub(r"^#+.*$", "", pure, flags=re.MULTILINE)
        cc = len(pure)
        if cc < MIN_CHARS:
            continue
        start_para = find_paragraph_for_offset(paras, section_start)
        end_para = find_paragraph_for_offset(paras, section_end - 1)
        seen_spans.append((section_start, section_end))
        out.append(Candidate(
            chapter_num=chapter_num,
            chapter_title=chapter_title,
            type=matched_type,
            start_para=start_para,
            end_para=end_para,
            char_count=cc,
            trigger=f"H2:{title}",
            preview=pure[:40],
            suggested_title=title,
            section_heading=title,
        ))
    return out


def scan_file(path: Path) -> list[Candidate]:
    stem = path.stem.replace(".tagged", "")
    m = re.match(r"(\d+)_(.+)", stem)
    if not m:
        return []
    chapter_num, chapter_title = m.group(1), m.group(2)
    text = path.read_text(encoding="utf-8")
    paras = parse_paragraphs(text)

    seen_spans: list[tuple[int, int]] = []
    candidates: list[Candidate] = []

    for type_, pattern in TRIGGERS:
        for tm in re.finditer(pattern, text):
            trig_end = tm.end()
            # 跳过"太史公曰" 块内的触发
            if in_fenced_block(text, tm.start()):
                continue

            # 先尝试配对引号
            quoted = extract_quoted_block(text, trig_end)
            if quoted:
                span_end, inner = quoted
                span_start = tm.start()
            else:
                # 没有立刻的引号，尝试把紧随的若干段纳入：从触发段末尾起，
                # 往后读直到遇到下一段以非引号/非"臣闻"类开头或段落数 >=4 时止
                span_start = tm.start()
                # 找触发所在段 index
                idx = None
                for i, (_, s, e) in enumerate(paras):
                    if s <= tm.start() < e:
                        idx = i
                        break
                if idx is None:
                    continue
                # 至多吸收当前段 + 后续 6 段
                last = min(idx + 6, len(paras) - 1)
                inner = text[paras[idx][1] : paras[last][2]]
                span_end = paras[last][2]

            pure = strip_tags(inner).strip()
            # 清理段号与空白
            pure = re.sub(r"\[\d+(?:\.\d+)*\]\s*", "", pure)
            pure = re.sub(r"\s+", "", pure)
            cc = len(pure)
            if cc < MIN_CHARS:
                continue

            # 去重：与已存候选区间重叠则跳过
            if any(not (span_end <= a or span_start >= b) for a, b in seen_spans):
                continue
            seen_spans.append((span_start, span_end))

            start_para = find_paragraph_for_offset(paras, span_start)
            end_para = find_paragraph_for_offset(paras, span_end - 1)
            heading = nearest_h2_before(text, span_start)
            preview = pure[:40]
            title = suggest_title(heading, chapter_title, type_, preview)

            candidates.append(
                Candidate(
                    chapter_num=chapter_num,
                    chapter_title=chapter_title,
                    type=type_,
                    start_para=start_para,
                    end_para=end_para,
                    char_count=cc,
                    trigger=tm.group(0),
                    preview=preview,
                    suggested_title=title,
                    section_heading=heading,
                )
            )

    # H2 标题扫描（补充触发器未命中的段落）
    candidates.extend(scan_h2_sections(text, chapter_num, chapter_title, paras, seen_spans))

    candidates.sort(key=lambda c: (c.chapter_num, c.start_para))
    return candidates


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_cands: list[Candidate] = []
    for f in sorted(CHAPTER_DIR.glob("*.tagged.md")):
        all_cands.extend(scan_file(f))

    # TSV
    tsv_path = OUT_DIR / "sanwen_candidates.tsv"
    with tsv_path.open("w", encoding="utf-8") as f:
        f.write(
            "章\t类型\t起段\t止段\t字数\t触发\t标题建议\t章内H2\t预览\n"
        )
        for c in all_cands:
            f.write(
                f"{c.chapter_num}\t{c.type}\t{c.start_para}\t{c.end_para}\t"
                f"{c.char_count}\t{c.trigger}\t{c.suggested_title}\t"
                f"{c.section_heading}\t{c.preview}\n"
            )

    # MD
    md_path = OUT_DIR / "sanwen_candidates.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# 散文候选清单（自动扫描，共 {len(all_cands)} 条）\n\n")
        f.write(
            "> 由 `scripts/scan_sanwen_candidates.py` 生成。\n> "
            f"阈值：纯文本 >= {MIN_CHARS} 字。\n> "
            "需人工审阅后再决定是否写入 tagged.md 的 ::: 块。\n\n"
        )
        by_type: dict[str, list[Candidate]] = {}
        for c in all_cands:
            by_type.setdefault(c.type, []).append(c)
        for t in ["诏令", "奏疏", "书信", "檄文", "策论", "议论"]:
            items = by_type.get(t, [])
            f.write(f"## {t}（{len(items)}）\n\n")
            for c in items:
                f.write(
                    f"- **{c.chapter_num} {c.chapter_title}** "
                    f"`[{c.start_para}-{c.end_para}]` "
                    f"{c.char_count}字 · 触发「{c.trigger}」\n"
                )
                if c.section_heading:
                    f.write(f"  - H2：{c.section_heading}\n")
                f.write(f"  - 建议标题：{c.suggested_title}\n")
                f.write(f"  - 预览：{c.preview}…\n\n")

    # JSON
    json_path = OUT_DIR / "sanwen_candidates.json"
    json_path.write_text(
        json.dumps([asdict(c) for c in all_cands], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 统计
    print(f"总计：{len(all_cands)} 候选")
    counts: dict[str, int] = {}
    for c in all_cands:
        counts[c.type] = counts.get(c.type, 0) + 1
    for t, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")
    print(f"\n输出：\n  {tsv_path}\n  {md_path}\n  {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
