#!/usr/bin/env python3
"""
quote_page.py — 为 wiki 页面查找并补全史记引文

从实体标注文件（chapter_md/*.tagged.md）中找到实体标注的引用段落/行，
对比页面已有引文，输出可新增的候选引文。

年表类章节精确到行（rN），叙述类章节精确到段落。

用法（从仓库根运行）：
  python3 .claude/skills/quote/scripts/quote_page.py PAGE_ID
  python3 .claude/skills/quote/scripts/quote_page.py PAGE_ID --max 10
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if not (REPO_ROOT / "wiki").is_dir():
    for c in [Path.cwd(), Path.cwd().parent]:
        if (c / "wiki").is_dir() and (c / "chapter_md").is_dir():
            REPO_ROOT = c
            break

PAGES_DIR   = REPO_ROOT / "wiki" / "public" / "pages"
CHAPTER_DIR = REPO_ROOT / "chapter_md"
SENT_DIR    = REPO_ROOT / "wiki" / "logs" / "butler" / "sentence_index"

# ── 章节元数据 ────────────────────────────────────────────────────────────────

CHAPTER_META: dict[str, dict] = {}  # num_str -> {file, title, tagged}

def _load_chapter_meta():
    for p in sorted(SENT_DIR.glob("*.jsonl")):
        m = re.match(r"^(\d+)_(.+)\.jsonl$", p.name)
        if m:
            num, title = m.group(1), m.group(2)
            CHAPTER_META[num] = {
                "file":   p.name,
                "title":  title,
                "tagged": CHAPTER_DIR / f"{num}_{title}.tagged.md",
            }

# ── 标注去除（与 build_sentence_index 相同逻辑）─────────────────────────────

def strip_annotations(text: str) -> str:
    text = re.sub(r"〖[^\s〖〗]([^|〗]*)\|[^〗]*〗", r"\1", text)
    text = re.sub(r"〖[^\s〖〗]([^〗]*)〗", r"\1", text)
    text = re.sub(r"⟦[^\s⟦⟧]([^⟧]*)⟧", r"\1", text)
    text = re.sub(r"〘[^\s〘〙]([^〙]*)〙", r"\1", text)
    text = re.sub(r"[〖〗⟦⟧〘〙]", "", text)
    return text.strip()

# ── Frontmatter 解析 ──────────────────────────────────────────────────────────

def read_frontmatter(page_path: Path) -> dict:
    text = page_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip().strip('"\'')
    aliases_raw = fm.get("aliases", "[]")
    fm["_aliases"] = re.findall(r"[^\[\],\s][^\[\],]*", aliases_raw)
    pn_raw = fm.get("pn", "")
    fm["_pns"] = re.findall(r"\((\d+)-(\d+)\)", pn_raw)
    return fm


def find_page(page_id: str) -> Path | None:
    direct = PAGES_DIR / f"{page_id}.md"
    if direct.exists():
        return direct
    for p in PAGES_DIR.glob("*.md"):
        if p.stem == page_id:
            return p
    return None

# ── 已引 PN 提取 ──────────────────────────────────────────────────────────────

def extract_cited_pns(page_path: Path) -> set[tuple[str, str]]:
    """从页面正文提取已引用的 (chapter_num, para_or_row) 对。"""
    text = page_path.read_text(encoding="utf-8")
    cited: set[tuple[str, str]] = set()
    # (003-32)  (019-r85)  （全角括号）
    for m in re.finditer(r"[（(](\d{3})-(r?\d+)[）)]", text):
        cited.add((m.group(1), m.group(2)))
    # [PN:[N]] 格式
    for m in re.finditer(r"###\s+\S+\s+\((\d{3})-\d+\).*?\[PN:\[(\d+)\]\]", text):
        cited.add((m.group(1), m.group(2)))
    return cited

# ── 实体搜索模式 ──────────────────────────────────────────────────────────────

def build_patterns(fm: dict) -> list[re.Pattern]:
    page_type = fm.get("type", "")
    label     = fm.get("label", fm.get("id", ""))
    aliases   = fm.get("_aliases", [])
    all_names = list(dict.fromkeys([label] + aliases))

    patterns = []
    for name in all_names:
        if not name:
            continue
        esc = re.escape(name)
        if page_type == "place":
            patterns.append(re.compile(r"〖=" + esc + r"[^〗]*〗"))
        elif page_type == "person":
            patterns.append(re.compile(r"〖@[^|〗]*\|" + esc + r"〗"))
            patterns.append(re.compile(r"〖@" + esc + r"〗"))
        elif page_type == "state":
            patterns.append(re.compile(r"〖◆" + esc + r"〗"))
        elif page_type in ("role", "title"):
            patterns.append(re.compile(r"〖;" + esc + r"〗"))
        # story/event: no entity scan, only expand known PNs
    return patterns

# ── Tagged 文件扫描 ───────────────────────────────────────────────────────────

# 年表行：行以 |  [rN] 开头
_ROW_RE  = re.compile(r"^\|\s*\[r(\d+)\]")
# 普通段落：行以 [N] 开头（不在 | 内）
_PARA_RE = re.compile(r"^\[(\d+(?:\.\d+)?)\]")


def scan_tagged_file(tagged_path: Path, patterns: list[re.Pattern],
                     chapter_num: str) -> list[tuple[str, str]]:
    """
    扫描 tagged.md，返回匹配实体标注的 (chapter_num, para_or_row) 列表。
    - 年表行：para = "r85"
    - 普通段落：para = "14"
    """
    if not tagged_path.exists():
        return []
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    current_para: str | None = None

    for line in tagged_path.read_text(encoding="utf-8").splitlines():
        # 检测年表行标记
        rm = _ROW_RE.match(line)
        if rm:
            # 年表行：直接用 rN 作为 para key
            if any(p.search(line) for p in patterns):
                key = (chapter_num, f"r{rm.group(1)}")
                if key not in seen:
                    seen.add(key)
                    results.append(key)
            continue  # 年表行不更新 current_para

        # 检测普通段落标记
        pm = _PARA_RE.match(line)
        if pm:
            current_para = pm.group(1).split(".")[0]

        if current_para and any(p.search(line) for p in patterns):
            key = (chapter_num, current_para)
            if key not in seen:
                seen.add(key)
                results.append(key)

    return results

# ── 文本提取 ──────────────────────────────────────────────────────────────────

_sent_cache: dict[str, list[dict]] = {}

def _load_sents(chapter_num: str) -> list[dict]:
    if chapter_num not in _sent_cache:
        meta = CHAPTER_META.get(chapter_num)
        if not meta:
            _sent_cache[chapter_num] = []
            return []
        p = SENT_DIR / meta["file"]
        _sent_cache[chapter_num] = (
            [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
            if p.exists() else []
        )
    return _sent_cache[chapter_num]

_tagged_cache: dict[str, list[str]] = {}

def _load_tagged_lines(chapter_num: str) -> list[str]:
    if chapter_num not in _tagged_cache:
        meta = CHAPTER_META.get(chapter_num, {})
        tagged = meta.get("tagged")
        _tagged_cache[chapter_num] = (
            tagged.read_text(encoding="utf-8").splitlines()
            if tagged and tagged.exists() else []
        )
    return _tagged_cache[chapter_num]


MAX_PARA_LEN = 500  # 超过此长度的普通段落跳过（防止太史公赞等超长段）

def get_text(chapter_num: str, para_or_row: str) -> str:
    """
    返回段落或年表行的原文文本（去标注符号）。
    - r85 → 从 tagged 文件提取该行并去标注
    - 14  → 从句子索引拼接
    """
    if para_or_row.startswith("r"):
        row_num = para_or_row[1:]
        row_re = re.compile(r"^\|\s*\[r" + re.escape(row_num) + r"\](.*)$")
        for line in _load_tagged_lines(chapter_num):
            m = row_re.match(line)
            if m:
                raw = m.group(0)  # 完整行
                return strip_annotations(raw)
        return ""

    sents = _load_sents(chapter_num)
    target = [s for s in sents if s["para"].split(".")[0] == para_or_row]
    if not target:
        return ""
    text = "".join(s["text"] for s in sorted(target, key=lambda x: (x["para"], x["seq"])))
    # 过滤超长段落（整章年表头等）
    if len(text) > MAX_PARA_LEN:
        return ""
    return text


def chapter_label(chapter_num: str) -> str:
    return CHAPTER_META.get(chapter_num, {}).get("title", chapter_num)

# ── 排序键（支持 rN）─────────────────────────────────────────────────────────

def sort_key(item: tuple[tuple[str, str], str]) -> tuple[str, int, int]:
    (chap, para), _ = item
    if para.startswith("r"):
        return (chap, 1, int(para[1:]))  # 年表行排在普通段落后
    return (chap, 0, int(para))

# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="查找并补全页面史记引文")
    parser.add_argument("page_id", help="页面 ID")
    parser.add_argument("--max", type=int, default=20,
                        help="最多输出候选条数（默认 20）")
    args = parser.parse_args()

    _load_chapter_meta()

    page_path = find_page(args.page_id)
    if not page_path:
        print(f"✗ 未找到页面: {args.page_id}", file=sys.stderr)
        sys.exit(1)

    fm = read_frontmatter(page_path)
    label     = fm.get("label", args.page_id)
    page_type = fm.get("type", "")
    print(f"[quote] 页面: {label}  类型: {page_type}")

    cited = extract_cited_pns(page_path)
    print(f"  已引用 PN 数: {len(cited)}")

    candidates: dict[tuple[str, str], str] = {}

    # 一、展开已知 PN
    for chap, para in fm["_pns"]:
        if (chap, para) not in cited:
            t = get_text(chap, para)
            if t:
                candidates[(chap, para)] = t

    # 二、实体扫描
    patterns = build_patterns(fm)
    if patterns:
        for chap_num, meta in CHAPTER_META.items():
            for chap, para in scan_tagged_file(meta["tagged"], patterns, chap_num):
                key = (chap, para)
                if key not in cited and key not in candidates:
                    t = get_text(chap, para)
                    if t and len(t) > 5:
                        candidates[key] = t
    else:
        print(f"  类型 '{page_type}' 不做实体扫描，仅展开已知 PN")

    if not candidates:
        print("\n无新候选引文。")
        return

    sorted_cands = sorted(candidates.items(), key=sort_key)
    total = len(sorted_cands)
    print(f"\n找到 {total} 条候选引文（显示前 {min(args.max, total)} 条）：\n")
    print("=" * 60)

    for i, ((chap, para), text) in enumerate(sorted_cands[:args.max]):
        pn_str = f"({chap}-{para})"
        display = text if len(text) <= 200 else text[:200] + "……"
        print(f"[{i+1}] {chapter_label(chap)}  PN={pn_str}  ({len(text)}字)")
        print(f"    {display}")
        print()

    if total > args.max:
        print(f"（还有 {total - args.max} 条未显示，可用 --max 调大）")

    print("=" * 60)
    print("\n建议格式（复制到页面 史记引文 节，按页面主题取舍）：\n")
    for (chap, para), text in sorted_cands[:args.max]:
        wiki_link = f"[[{chap}_{chapter_label(chap)}|{chapter_label(chap)}]]"
        pn_str    = f"({chap}-{para})"
        display   = text if len(text) <= 150 else text[:150] + "……"
        print(f"> 出自 {wiki_link} {pn_str}：{display}")
        print()


if __name__ == "__main__":
    main()
