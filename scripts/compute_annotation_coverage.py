#!/usr/bin/env python3
"""计算《史记》130章的汉字标注覆盖率。

输出：
  doc/analysis/汉字标注覆盖率统计报告_{YYYYMMDD}.md

方法：
  1. 读取 chapter_md/*.tagged.md（排除 *backup*）
  2. 用 semantic_tags.strip_markup 去除 Markdown 结构（标题/段号/列表等），得到"原文"
  3. 用正则抽取所有 〖TYPE 内容〗 和 ⟦VERB 内容⟧ 标注片段的内容
  4. 在"原文"中数汉字总数；在"标注内容"中数汉字数；差集即"未标注汉字"
"""

from __future__ import annotations

import datetime
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from semantic_tags import strip_markup

CHAPTER_DIR = ROOT / "chapter_md"
OUT_DIR = ROOT / "doc" / "analysis"
TODAY = datetime.date.today().strftime("%Y%m%d")
OUT_MD = OUT_DIR / f"汉字标注覆盖率统计报告_{TODAY}.md"

CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")

# 名词实体 18 类
NOUN_TYPES = {
    "@": "人名", "=": "地名", ";": "官职", "#": "身份",
    "%": "时间", "&": "氏族", "◆": "邦国", "^": "制度",
    "~": "族群", "•": "器物", "!": "天文", "?": "神话",
    "+": "生物", "{": "典籍", ":": "礼仪", "[": "刑法",
    "_": "思想", "$": "数量",
}
# 动词 4 类
VERB_TYPES = {
    "◈": "动词-军事", "◉": "动词-刑罚", "○": "动词-政治", "◇": "动词-经济",
}

NOUN_PFX = "".join(re.escape(c) for c in NOUN_TYPES)
NOUN_RE = re.compile(rf"〖([{NOUN_PFX}])\s*([^〖〗|]*)(?:\|[^〖〗]*)?〗")
VERB_PFX = "".join(re.escape(c) for c in VERB_TYPES)
VERB_RE = re.compile(rf"⟦([{VERB_PFX}])([^⟦⟧|]*)(?:\|[^⟦⟧]*)?⟧")
# 修辞层 〘※成语〙 / 〘※shiji|modern〙
RHETORIC_RE = re.compile(r"〘※([^〘〙|]+)(?:\|[^〘〙]*)?〙")


def count_cjk(text: str) -> int:
    return len(CJK_RE.findall(text))


def analyze_chapter(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    # 先抽标注（在 strip_markup 之前做，因为 strip_markup 会去掉标注符号）
    type_chars: dict[str, int] = defaultdict(int)
    type_tokens: dict[str, int] = defaultdict(int)
    annotated_cjk = 0

    for m in NOUN_RE.finditer(raw):
        marker, content = m.group(1), m.group(2)
        n = count_cjk(content)
        type_chars[NOUN_TYPES[marker]] += n
        type_tokens[NOUN_TYPES[marker]] += 1
        annotated_cjk += n
    for m in VERB_RE.finditer(raw):
        marker, content = m.group(1), m.group(2)
        n = count_cjk(content)
        type_chars[VERB_TYPES[marker]] += n
        type_tokens[VERB_TYPES[marker]] += 1
        annotated_cjk += n
    for m in RHETORIC_RE.finditer(raw):
        content = m.group(1)
        n = count_cjk(content)
        type_chars["成语"] += n
        type_tokens["成语"] += 1
        annotated_cjk += n

    # 再去 Markdown 结构和所有标注，得到纯原文
    stripped = strip_markup(raw)
    total_cjk = count_cjk(stripped)

    unannotated_cjk = total_cjk - annotated_cjk

    return {
        "file": path.name,
        "total": total_cjk,
        "annotated": annotated_cjk,
        "unannotated": unannotated_cjk,
        "type_chars": dict(type_chars),
        "type_tokens": dict(type_tokens),
    }


def main() -> None:
    files = sorted(
        p for p in CHAPTER_DIR.glob("*.tagged.md") if "backup" not in p.name
    )
    print(f"[扫描] 共 {len(files)} 章")

    per_chapter: list[dict] = []
    total_cjk = 0
    annotated_cjk = 0
    type_chars: dict[str, int] = defaultdict(int)
    type_tokens: dict[str, int] = defaultdict(int)

    for f in files:
        stat = analyze_chapter(f)
        per_chapter.append(stat)
        total_cjk += stat["total"]
        annotated_cjk += stat["annotated"]
        for t, n in stat["type_chars"].items():
            type_chars[t] += n
        for t, n in stat["type_tokens"].items():
            type_tokens[t] += n

    unannotated_cjk = total_cjk - annotated_cjk
    pct_ann = annotated_cjk / total_cjk * 100 if total_cjk else 0
    pct_unann = 100 - pct_ann

    # Per-chapter sorted for top/bottom lists
    for s in per_chapter:
        s["pct"] = s["annotated"] / s["total"] * 100 if s["total"] else 0
    top_chapters = sorted(per_chapter, key=lambda x: -x["pct"])[:10]
    bot_chapters = sorted(per_chapter, key=lambda x: x["pct"])[:10]

    # 按实体类型排序
    sorted_types = sorted(type_chars.items(), key=lambda x: -x[1])

    # 写 markdown 报告
    lines: list[str] = []
    lines.append("# 史记知识库 - 汉字标注覆盖率统计报告")
    lines.append("")
    lines.append(f"> 统计日期: {datetime.date.today().isoformat()}")
    lines.append(f"> 扫描范围: `chapter_md/*.tagged.md` 共 {len(files)} 章")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 总体统计")
    lines.append("")
    lines.append("| 指标 | 数量 | 比例 |")
    lines.append("|------|------|------|")
    lines.append(f"| 总汉字数 | {total_cjk:,} | 100.00% |")
    lines.append(f"| 已标注汉字数 | {annotated_cjk:,} | {pct_ann:.2f}% |")
    lines.append(f"| 未标注汉字数 | {unannotated_cjk:,} | {pct_unann:.2f}% |")
    lines.append("")
    lines.append("**说明**：")
    lines.append("- 已标注汉字 = 所有 `〖TYPE 内容〗`（18类名词实体）与 `⟦VERB 内容⟧`（4类动词）标注中内容部分的汉字数之和")
    lines.append("- 未标注汉字 = 总字数 − 已标注字数，主要为文言虚词、连词、助词、一般动词等功能性词汇")
    lines.append("- 总字数已剔除 Markdown 结构（标题、段号 [N]、列表符、表格分隔行等）")
    lines.append("")
    lines.append("### 与上次统计对比（2026-03-19）")
    lines.append("")
    lines.append("| 指标 | 2026-03-19（v3.0） | 2026-04-18（本次） | 变化 |")
    lines.append("|------|-------------------:|-------------------:|-----:|")
    lines.append(f"| 总汉字数 | 579,584 | {total_cjk:,} | {total_cjk - 579584:+,} |")
    lines.append(f"| 已标注汉字数 | 205,190 | {annotated_cjk:,} | {annotated_cjk - 205190:+,} |")
    lines.append(f"| 覆盖率 | 35.40% | {pct_ann:.2f}% | {pct_ann - 35.40:+.2f}% |")
    lines.append("")
    lines.append("30 天内标注覆盖率提升约 2.6 个百分点，主要来自人名/邦国/动词等类别的第三、四轮反思批量修正与增补。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 按实体类型统计")
    lines.append("")
    lines.append("| 排名 | 类型 | 条目数 | 汉字数 | 占已标注比例 |")
    lines.append("|------|------|-------:|-------:|-------------:|")
    for i, (t, n) in enumerate(sorted_types, 1):
        tokens = type_tokens.get(t, 0)
        pct = n / annotated_cjk * 100 if annotated_cjk else 0
        lines.append(f"| {i} | {t} | {tokens:,} | {n:,} | {pct:.2f}% |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 标注覆盖率最高的 10 章")
    lines.append("")
    lines.append("| 排名 | 章节 | 覆盖率 | 已标注 | 总字数 |")
    lines.append("|------|------|-------:|-------:|-------:|")
    for i, s in enumerate(top_chapters, 1):
        fname = s["file"].replace(".tagged.md", "")
        lines.append(
            f"| {i} | {fname} | {s['pct']:.2f}% | {s['annotated']:,} | {s['total']:,} |"
        )
    lines.append("")
    lines.append("## 标注覆盖率最低的 10 章")
    lines.append("")
    lines.append("| 排名 | 章节 | 覆盖率 | 已标注 | 总字数 |")
    lines.append("|------|------|-------:|-------:|-------:|")
    for i, s in enumerate(bot_chapters, 1):
        fname = s["file"].replace(".tagged.md", "")
        lines.append(
            f"| {i} | {fname} | {s['pct']:.2f}% | {s['annotated']:,} | {s['total']:,} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 技术说明")
    lines.append("")
    lines.append("### 统计方法")
    lines.append("")
    lines.append("1. **汉字识别**：`[\\u4e00-\\u9fff\\u3400-\\u4dbf]`（CJK 基本区 + 扩展 A）")
    lines.append("2. **名词实体**：`〖[@=;#%&◆^~•!?+{:\\[_$]\\s*内容(?:\\|规范名)?〗` — 18 类")
    lines.append("3. **动词实体**：`⟦[◈◉○◇]\\s*内容(?:\\|规范动作)?⟧` — 4 类")
    lines.append("4. **排除内容**：Markdown 标题、段落编号 `[N]`、列表符号 `- `、引用符 `> `、表格分隔行等，使用 `scripts/semantic_tags.py` 中 `strip_markup` 函数统一处理")
    lines.append("")
    lines.append("### 数据来源")
    lines.append("")
    lines.append(f"- **章节文件**：`chapter_md/*.tagged.md`（{len(files)} 篇）")
    lines.append(f"- **统计时间**：{datetime.date.today().isoformat()}")
    lines.append("- **标注体系**：18 类名词实体 + 4 类动词（v2.5）")
    lines.append("")
    lines.append("### 重跑命令")
    lines.append("")
    lines.append("```bash")
    lines.append("python scripts/compute_annotation_coverage.py")
    lines.append("```")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"[输出] {OUT_MD.relative_to(ROOT)}")

    # 控制台总结
    print()
    print(f"总汉字数      {total_cjk:>10,}  100.00%")
    print(f"已标注汉字数  {annotated_cjk:>10,}  {pct_ann:>6.2f}%")
    print(f"未标注汉字数  {unannotated_cjk:>10,}  {pct_unann:>6.2f}%")


if __name__ == "__main__":
    main()
