#!/usr/bin/env python3
"""扫描《史记》130 章，抽取对外部典籍（诗经、尚书、易经等）的引用。

两种来源：
  1. 书名实体标签 `〖{书名〗` —— 项目已系统标注 598 处。
     - 后接「曰/云」并带引文 → citation（引文）
     - 否则 → mention（提及）
  2. 未标注但属于惯用引文触发词：语曰、谚曰、野语曰、鄙语曰 → generic（泛引）

输出：
  - data/citations.json  结构化数据
  - data/citations.md    Markdown 版
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = ROOT / "chapter_md"
OUT_JSON = ROOT / "data" / "citations.json"
OUT_MD = ROOT / "data" / "citations.md"

PARA_RE = re.compile(r"^\[([0-9r][0-9.]*)\]")
CHAPTER_FNAME_RE = re.compile(r"^(\d{3})_(.+)\.tagged\.md$")

BOOK_TAG_RE = re.compile(r"〖\{([^〖〗|]+?)(?:\|[^〖〗]+)?〗")

GENERIC_TRIGGERS = [
    ("野语", r"野语[曰云]"),
    ("鄙语", r"鄙语[曰云]"),
    ("语", r"(?<![札私上下])语[曰云]"),
    ("谚", r"谚[曰云]"),
]
GENERIC_RE = [(label, re.compile(pat)) for label, pat in GENERIC_TRIGGERS]

SNIPPET_RADIUS = 40
QUOTE_OPENERS = "\u201c\u2018"
QUOTE_CLOSERS = "\u201d\u2019"


CANONICAL = {
    "诗": ("诗经", "六经"),
    "书": ("尚书", "六经"),
    "尚书": ("尚书", "六经"),
    "易": ("易经", "六经"),
    "春秋": ("春秋", "六经"),
    "礼": ("礼经", "六经"),
    "乐": ("乐经", "六经"),
    "六经": ("六经", "六经"),
    "诗书": ("诗·书(合称)", "六经"),
    "雅颂": ("雅颂(合称)", "六经"),
    "国风": ("诗经·国风", "诗经·篇类"),
    "大雅": ("诗经·大雅", "诗经·篇类"),
    "小雅": ("诗经·小雅", "诗经·篇类"),
    "颂": ("诗经·颂", "诗经·篇类"),
    "风": ("诗经·风", "诗经·篇类"),
    "关雎": ("诗经·关雎", "诗经·篇章"),
    "甘棠": ("诗经·甘棠", "诗经·篇章"),
    "南风": ("诗经·南风", "诗经·篇章"),
    "商": ("诗经·商颂", "诗经·篇类"),
    "齐": ("诗经·齐风", "诗经·篇类"),
    "乾坤": ("易经·乾坤", "易经·篇章"),
    "传": ("春秋传(泛指)", "经传"),
    "大传": ("春秋大传", "经传"),
    "春秋大传": ("春秋大传", "经传"),
    "国语": ("国语", "经传"),
    "周书": ("周书", "尚书·篇类"),
    "秦记": ("秦记", "史籍"),
    "禹本纪": ("禹本纪", "史籍"),
    "史记": ("史记(他称)", "史籍"),
    "本纪": ("史记·本纪(自引)", "史籍·自引"),
    "世家": ("史记·世家(自引)", "史籍·自引"),
    "老子": ("老子", "诸子"),
    "孟子": ("孟子", "诸子"),
    "司马法": ("司马法", "兵家"),
    "太公兵法": ("太公兵法", "兵家"),
    "兵法": ("兵法", "兵家"),
    "十三篇": ("孙子十三篇", "兵家"),
    "五蠹": ("韩非子·五蠹", "诸子·篇章"),
    "孤愤": ("韩非子·孤愤", "诸子·篇章"),
    "说难": ("韩非子·说难", "诸子·篇章"),
    "离骚": ("楚辞·离骚", "辞赋"),
    "子虚": ("子虚赋", "辞赋"),
    "大人赋": ("大人赋", "辞赋"),
    "孝经": ("孝经", "六艺旁"),
}


def list_chapters() -> List[Path]:
    files = []
    for f in sorted(CHAPTER_DIR.glob("*.tagged.md")):
        if "backup" in f.name or "_backup_" in f.name:
            continue
        if CHAPTER_FNAME_RE.match(f.name):
            files.append(f)
    return files


def parse_chapter(path: Path):
    m = CHAPTER_FNAME_RE.match(path.name)
    chapter_id = m.group(1)
    chapter_name = m.group(2)
    lines = []
    current_para = "0"
    with path.open(encoding="utf-8") as f:
        raw_lines = f.read().split("\n")
    # 先扫一遍记录段号
    tmp = []
    for lineno, line in enumerate(raw_lines, 1):
        stripped = line.lstrip()
        m2 = PARA_RE.match(stripped)
        if m2:
            current_para = m2.group(1)
        tmp.append((current_para, lineno, line))
    # 为每行附带「段落其余文本」(用于跨行引文抽取)
    # 同一 para 内，从当前行起拼接后续物理行（到下一个段号或空行）
    result = []
    for i, (para, lineno, line) in enumerate(tmp):
        # 收集同 para 内后续最多 4 行
        extra_parts = []
        for j in range(i + 1, min(i + 5, len(tmp))):
            npara, _, nline = tmp[j]
            if npara != para or not nline.strip():
                break
            extra_parts.append(nline)
        para_tail = "\n".join(extra_parts)
        result.append((para, lineno, line, para_tail))
    return chapter_id, chapter_name, result


def classify_book(title: str) -> Tuple[str, str]:
    if title in CANONICAL:
        return CANONICAL[title]
    if re.fullmatch(r"[一二三四五六七八九十百]+", title):
        return (title, "其他")
    sub_shangshu = {
        "甘誓", "胤征", "五子之歌", "夏小正", "汤征", "女鸠女房", "汤誓", "典宝",
        "夏社", "汤诰", "咸有一德", "明居", "伊训", "肆命", "徂后", "太甲训",
        "沃丁", "咸艾", "太戊", "盘庚", "高宗肜日", "训", "太誓", "武成",
        "大诰", "归禾", "嘉禾", "酒诰", "梓材", "召诰", "洛诰", "多士",
        "无佚", "君奭", "多方", "立政", "顾命", "康王之诰", "毕命", "吕刑",
        "甫刑", "文侯之命", "费誓", "秦誓", "微子", "微子之命", "康诰", "帝诰",
        "分殷之器物",
    }
    if title in sub_shangshu:
        return (f"尚书·{title}", "尚书·篇章")
    return (title, "其他")


_LEADING_PUNCT = "：: \t\u201c\u201d\u2018\u2019\u300c\u300d\"'，、"


def _trim_quote(text: str) -> str:
    text = text.replace("\n", "").strip()
    while text and text[0] in _LEADING_PUNCT:
        text = text[1:]
    while text and text[-1] in _LEADING_PUNCT:
        text = text[:-1]
    return text


def extract_quote_after(line: str, pos: int, extra: str = "") -> str:
    """从 pos 位置起，尝试提取引文。若当前行未闭合引号则拼接 extra 续查。返回去标签后的纯文本。"""
    tail = line[pos:]
    combined = tail + ("\n" + extra if extra else "")
    m_opener = re.search(r"[\u201c\u2018]", combined)
    if m_opener and m_opener.start() <= 6:
        opener_idx = m_opener.start()
        opener = combined[opener_idx]
        closer = "\u201d" if opener == "\u201c" else "\u2019"
        end = combined.find(closer, opener_idx + 1)
        if end > 0:
            return _trim_quote(strip_tags(combined[opener_idx + 1:end]))
    # 无引号：取下一句（到句号/分号/问号/感叹号）
    m_end = re.search(r"[。；？！]", combined)
    if m_end:
        return _trim_quote(strip_tags(combined[:m_end.start()]))
    return _trim_quote(strip_tags(combined[:80]))


def strip_tags(text: str) -> str:
    def _unwrap(match: re.Match) -> str:
        body = match.group(1)
        if "|" in body:
            body = body.split("|", 1)[0]
        return re.sub(r"^[@#&%_;\^+={*?$•◆○◈◉◇◆!\[\]~?]+\s*", "", body)
    text = re.sub(r"〖([^〖〗]*?)〗", _unwrap, text)
    text = re.sub(r"⟦([^⟦⟧]*?)⟧", _unwrap, text)
    return text


def make_snippet(line: str, start: int, end: int, radius: int = SNIPPET_RADIUS) -> str:
    left = max(0, start - radius)
    right = min(len(line), end + radius)
    prefix = "…" if left > 0 else ""
    suffix = "…" if right < len(line) else ""
    return prefix + strip_tags(line[left:right]) + suffix


def has_quote_trigger(line: str, tag_end: int) -> Tuple[bool, int]:
    """判断 `〖{书〗` 之后短距离内是否紧跟『曰/云』。
    返回 (是否触发, 触发词结束位置)。"""
    window = line[tag_end:tag_end + 2]
    m = re.match(r"[曰云]", window)
    if m:
        return True, tag_end + m.end()
    return False, tag_end


AMBIGUOUS_SINGLE = {"礼", "乐"}  # 易与概念混淆的单字书名


def _has_other_book_nearby(line: str, span: tuple[int, int], radius: int = 25) -> bool:
    """span ±radius 范围内是否存在另一 〖{书名〗 标签（构成 诗书礼乐 等合用语）。"""
    s, e = span
    window_start = max(0, s - radius)
    window_end = min(len(line), e + radius)
    window = line[window_start:window_end]
    count = len(list(BOOK_TAG_RE.finditer(window)))
    return count >= 2


# 明确的概念语境关键字（出现则强制归为概念）
CONCEPT_VERBS = ("行", "问", "习", "好", "修", "脩", "作", "相", "革", "简", "责", "违", "成",
                 "知", "拜", "立", "执", "用", "守", "过", "废", "坏", "崇", "讲", "议", "审",
                 "叙", "导", "明", "明其", "以", "无", "非", "不", "不知", "失", "其", "之", "至")
# 书名语境关键字（出现则非概念）
BOOK_VERBS = ("焚", "烧", "放弃", "学", "读", "诵", "论", "传", "著", "编", "序", "六经", "春秋",
              "诗书", "诗书礼乐", "藏")


def _is_probable_concept(title: str, line: str, span: tuple[int, int], triggered: bool) -> bool:
    """判断此 〖{礼〗/〖{乐〗 是否更可能作为抽象礼仪/乐制概念使用。"""
    if title not in AMBIGUOUS_SINGLE:
        return False
    if triggered:
        return False
    start, end = span
    before = line[max(0, start - 8):start]
    after = line[end:end + 8]
    # 明确书名语境关键字
    if any(k in before or k in after for k in BOOK_VERBS):
        return False
    # 紧邻其他书名合用（〖{诗〗〖{书〗〖{礼〗〖{乐〗）
    if _has_other_book_nearby(line, span):
        return False
    # 前一字为概念动词（行礼·问礼·好礼·修礼等）
    if before and before[-1] in ("行", "问", "习", "好", "修", "脩", "拜", "立", "执", "用",
                                  "革", "简", "责", "成", "废", "知", "议", "叙", "导",
                                  "明", "失", "至", "其", "之", "守", "崇", "讲", "违", "为",
                                  "不", "无", "非", "作", "相", "以"):
        return True
    # 后一字为概念动词或结构词
    if after and after[0] in ("成", "坏", "毕", "亦", "也", "矣", "遂", "节", "废", "义"):
        return True
    # 若单独出现（无曰云、无合用、无书名动词、无概念动词）— 默认概念
    return True


def scan_book_tags(chapters):
    by_book = defaultdict(lambda: {"citations": [], "mentions": [], "concepts": []})
    for chapter_id, chapter_name, lines in chapters:
        for para_id, lineno, line, para_tail in lines:
            for m in BOOK_TAG_RE.finditer(line):
                title = m.group(1)
                span = (m.start(), m.end())
                item = {
                    "chapter_id": chapter_id,
                    "chapter_name": chapter_name,
                    "para_id": para_id,
                    "line_no": lineno,
                    "snippet": make_snippet(line, m.start(), m.end()),
                }
                triggered, after = has_quote_trigger(line, m.end())
                if triggered:
                    item["trigger"] = line[m.end():after]
                    item["quote"] = extract_quote_after(line, after, para_tail)
                    by_book[title]["citations"].append(item)
                elif _is_probable_concept(title, line, span, triggered):
                    by_book[title]["concepts"].append(item)
                else:
                    by_book[title]["mentions"].append(item)
    return by_book


def scan_generic(chapters):
    out = defaultdict(list)
    for chapter_id, chapter_name, lines in chapters:
        for para_id, lineno, line, para_tail in lines:
            for label, pat in GENERIC_RE:
                for m in pat.finditer(line):
                    quote = extract_quote_after(line, m.end(), para_tail)
                    out[label].append({
                        "chapter_id": chapter_id,
                        "chapter_name": chapter_name,
                        "para_id": para_id,
                        "line_no": lineno,
                        "trigger": m.group(0),
                        "quote": quote,
                        "snippet": make_snippet(line, m.start(), m.end()),
                    })
            # 去重：野语曰 同时匹配 语曰，下一循环过滤
    # 去重：同一 (chapter, lineno, para) 内，野语/鄙语优先于 语
    for key in ("语",):
        kept = []
        taken = {(x["chapter_id"], x["line_no"], x["snippet"]) for lb in ("野语", "鄙语") for x in out.get(lb, [])}
        for item in out[key]:
            key_tuple = (item["chapter_id"], item["line_no"], item["snippet"])
            if any(item["snippet"] == t[2] and item["chapter_id"] == t[0] and item["line_no"] == t[1] for t in taken):
                continue
            kept.append(item)
        out[key] = kept
    return out


def build_output(chapters):
    by_book_raw = scan_book_tags(chapters)
    generic = scan_generic(chapters)

    # 汇总为按 canonical 名聚合
    by_canonical = {}
    for title, data in by_book_raw.items():
        canonical, category = classify_book(title)
        key = canonical
        if key not in by_canonical:
            by_canonical[key] = {
                "canonical": canonical,
                "category": category,
                "titles_raw": [],
                "citations": [],
                "mentions": [],
                "concepts": [],
            }
        by_canonical[key]["titles_raw"].append(title)
        for c in data["citations"]:
            c["title_raw"] = title
            by_canonical[key]["citations"].append(c)
        for mm in data["mentions"]:
            mm["title_raw"] = title
            by_canonical[key]["mentions"].append(mm)
        for co in data.get("concepts", []):
            co["title_raw"] = title
            by_canonical[key]["concepts"].append(co)

    # 排序：citations 多者在前
    books = sorted(
        by_canonical.values(),
        key=lambda x: (-len(x["citations"]) - len(x["mentions"]), x["canonical"]),
    )

    total_citations = sum(len(b["citations"]) for b in books)
    total_mentions = sum(len(b["mentions"]) for b in books)
    total_concepts = sum(len(b["concepts"]) for b in books)
    total_generic = sum(len(v) for v in generic.values())
    unique_books = len(books)
    chapters_touched = set()
    for b in books:
        for it in b["citations"] + b["mentions"]:
            chapters_touched.add(it["chapter_id"])
    for lst in generic.values():
        for it in lst:
            chapters_touched.add(it["chapter_id"])

    return {
        "stats": {
            "total_books": unique_books,
            "total_citations": total_citations,
            "total_mentions": total_mentions,
            "total_concepts": total_concepts,
            "total_generic": total_generic,
            "chapters_touched": len(chapters_touched),
            "chapters_scanned": len(chapters),
        },
        "books": books,
        "generic": [
            {"label": label, "entries": entries, "count": len(entries)}
            for label, entries in sorted(generic.items(), key=lambda x: -len(x[1]))
        ],
    }


def render_markdown(data: dict) -> str:
    s = data["stats"]
    buf = []
    buf.append("# 史记引文索引\n")
    buf.append("本专题收录《史记》全书对外部典籍（诗经、尚书、易经、春秋、经传、诸子、兵家、辞赋等）的引用与提及，以及『语曰/谚曰/野语/鄙语』等泛引。\n")
    buf.append("## 统计概览\n")
    buf.append(f"- **引用典籍数（归一化）**：{s['total_books']}")
    buf.append(f"- **引文条数（含引文内容）**：{s['total_citations']}")
    buf.append(f"- **提及条数（仅提及书名）**：{s['total_mentions']}")
    buf.append(f"- **泛引条数（语/谚/野语/鄙语）**：{s['total_generic']}")
    buf.append(f"- **涉及章数**：{s['chapters_touched']} / {s['chapters_scanned']}\n")

    cat_groups = defaultdict(list)
    for b in data["books"]:
        cat_groups[b["category"]].append(b)

    buf.append("## 目录（按类别）\n")
    buf.append("| 类别 | 典籍 | 引文数 | 提及数 |")
    buf.append("|------|------|------:|------:|")
    for cat in sorted(cat_groups.keys()):
        for b in cat_groups[cat]:
            buf.append(f"| {cat} | {b['canonical']} | {len(b['citations'])} | {len(b['mentions'])} |")
    buf.append("")

    for cat in sorted(cat_groups.keys()):
        buf.append(f"## {cat}\n")
        for b in cat_groups[cat]:
            titles = "、".join(sorted(set(b["titles_raw"])))
            buf.append(f"### {b['canonical']}（原始标签：{titles}）\n")
            if b["citations"]:
                buf.append(f"**引文（{len(b['citations'])} 条）**\n")
                buf.append("| 章 | 段 | 引语 | 上下文 |")
                buf.append("|----|----|------|--------|")
                for c in b["citations"]:
                    quote = (c.get("quote") or "").replace("|", "\\|")
                    snip = c["snippet"].replace("|", "\\|")
                    ch = f"{c['chapter_id']} {c['chapter_name']}"
                    buf.append(f"| {ch} | [{c['para_id']}] | {quote} | {snip} |")
                buf.append("")
            if b["mentions"]:
                buf.append(f"**提及（{len(b['mentions'])} 条）**\n")
                buf.append("| 章 | 段 | 上下文 |")
                buf.append("|----|----|--------|")
                for mm in b["mentions"]:
                    snip = mm["snippet"].replace("|", "\\|")
                    ch = f"{mm['chapter_id']} {mm['chapter_name']}"
                    buf.append(f"| {ch} | [{mm['para_id']}] | {snip} |")
                buf.append("")
            buf.append("")

    buf.append("## 泛引（语·谚·野语·鄙语）\n")
    for g in data["generic"]:
        buf.append(f"### {g['label']}曰／云（{g['count']} 条）\n")
        buf.append("| 章 | 段 | 触发 | 引语 |")
        buf.append("|----|----|------|------|")
        for it in g["entries"]:
            quote = (it.get("quote") or "").replace("|", "\\|")
            ch = f"{it['chapter_id']} {it['chapter_name']}"
            buf.append(f"| {ch} | [{it['para_id']}] | {it['trigger']} | {quote} |")
        buf.append("")

    buf.append("---\n")
    buf.append("## 数据与脚本\n")
    buf.append("- 结构化数据：`data/citations.json`")
    buf.append("- 扫描脚本：`scripts/extract_citations.py`")
    buf.append("- 渲染脚本：`scripts/render_citations_html.py`")
    buf.append("- HTML 页面：`docs/special/citations.html`\n")
    return "\n".join(buf)


def main():
    chapter_paths = list_chapters()
    chapters = [parse_chapter(p) for p in chapter_paths]
    data = build_output(chapters)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_markdown(data), encoding="utf-8")
    s = data["stats"]
    print(f"扫描 {s['chapters_scanned']} 章 / 涉及 {s['chapters_touched']} 章")
    print(f"典籍 {s['total_books']} 种 · 引文 {s['total_citations']} 条 · 提及 {s['total_mentions']} 条 · 泛引 {s['total_generic']} 条")
    print(f"输出：{OUT_JSON}")
    print(f"输出：{OUT_MD}")


if __name__ == "__main__":
    main()
