#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《史记》实体标注统计报告（`doc/entities/实体标注统计/实体标注统计报告_v{版本}.md`）。

口径：直接扫描 chapter_md/*.tagged.md 中的 〖TYPE X〗 与 ⟦VERB X⟧ 标注。
  - 条目数：按消歧规范名（`|` 左侧）去重后的 distinct 计数，**不做别名合并**
  - 出现数：正则命中次数（每次标注计一次）

别名合并后的条目数由 kg/entities/scripts/build_entity_index.py 生成的
entity_index.json 提供，两套口径不同，数值不可直接比较。

用法：
    python scripts/generate_entity_stats_report.py --version v4.2
    python scripts/generate_entity_stats_report.py --version v4.2 --output /path/to/out.md
    python scripts/generate_entity_stats_report.py --stdout        # 只打印到 stdout，不写文件
    python scripts/generate_entity_stats_report.py --json stats.json  # 同时导出原始数据
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = ROOT / "chapter_md"
DEFAULT_OUT_DIR = ROOT / "doc" / "entities" / "实体标注统计"

NOUN_TYPES = {
    "@": "人名", "=": "地名", ";": "官职", "#": "身份",
    "%": "时间", "&": "氏族", "◆": "邦国", "^": "名物",
    "~": "族群", "•": "器物", "!": "天文", "?": "神话",
    "+": "生物", "{": "典籍", ":": "礼仪", "[": "刑法",
    "_": "思想", "$": "数量",
}
VERB_TYPES = {
    "◈": "军事动词", "◉": "刑罚动词", "○": "政治动词", "◇": "经济动词",
}

NOUN_PFX = "".join(re.escape(c) for c in NOUN_TYPES)
NOUN_RE = re.compile(rf"〖([{NOUN_PFX}])\s*([^〖〗|]*)(?:\|[^〖〗]*)?〗")
VERB_PFX = "".join(re.escape(c) for c in VERB_TYPES)
VERB_RE = re.compile(rf"⟦([{VERB_PFX}])\s*([^⟦⟧|]*)(?:\|[^⟦⟧]*)?⟧")


def scan_chapters(chapter_dir: Path) -> dict:
    noun_occ: dict[str, int] = defaultdict(int)
    noun_entries: dict[str, set[str]] = defaultdict(set)
    verb_occ: dict[str, int] = defaultdict(int)
    verb_entries: dict[str, set[str]] = defaultdict(set)

    files = sorted(f for f in chapter_dir.glob("*.tagged.md") if "backup" not in f.name)
    for f in files:
        text = f.read_text(encoding="utf-8")
        for m in NOUN_RE.finditer(text):
            marker, content = m.group(1), m.group(2).strip()
            noun_occ[marker] += 1
            if content:
                noun_entries[marker].add(content)
        for m in VERB_RE.finditer(text):
            marker, content = m.group(1), m.group(2).strip()
            verb_occ[marker] += 1
            if content:
                verb_entries[marker].add(content)

    return {
        "chapter_count": len(files),
        "noun": {
            m: {"label": NOUN_TYPES[m], "entries": len(noun_entries[m]), "occurrences": noun_occ[m]}
            for m in NOUN_TYPES
        },
        "verb": {
            m: {"label": VERB_TYPES[m], "entries": len(verb_entries[m]), "occurrences": verb_occ[m]}
            for m in VERB_TYPES
        },
    }


EXAMPLES = {
    "@": "〖@刘邦〗", "=": "〖=长安〗", ";": "〖;丞相〗", "#": "〖#天子〗",
    "%": "〖%三年〗", "&": "〖&姬〗", "◆": "〖◆汉〗", "^": "〖^郡县〗",
    "~": "〖~匈奴〗", "•": "〖•宝鼎〗", "!": "〖!岁星〗", "?": "〖?鬼神〗",
    "+": "〖+龙〗", "{": "〖{春秋〗", ":": "〖:宗庙〗", "[": "〖[腰斩〗",
    "_": "〖_仁义〗", "$": "〖$三万人〗",
    "◈": "⟦◈伐⟧", "◉": "⟦◉杀⟧", "○": "⟦○立⟧", "◇": "⟦◇赐⟧",
}


def render_report(stats: dict, version: str, today: str) -> str:
    noun = stats["noun"]
    verb = stats["verb"]
    chapter_count = stats["chapter_count"]

    total_noun_occ = sum(v["occurrences"] for v in noun.values())
    total_noun_entries = sum(v["entries"] for v in noun.values())
    total_verb_occ = sum(v["occurrences"] for v in verb.values())
    total_verb_entries = sum(v["entries"] for v in verb.values())
    grand_occ = total_noun_occ + total_verb_occ
    grand_entries = total_noun_entries + total_verb_entries

    noun_sorted = sorted(noun.items(), key=lambda kv: -kv[1]["occurrences"])
    verb_sorted = sorted(verb.items(), key=lambda kv: -kv[1]["occurrences"])
    top10 = sorted(
        [(v["label"], m, v["occurrences"]) for m, v in noun.items()]
        + [(v["label"], m, v["occurrences"]) for m, v in verb.items()],
        key=lambda t: -t[2],
    )[:10]

    lines: list[str] = []
    lines.append(f"# 《史记》知识库实体标注统计报告 {version}")
    lines.append("")
    lines.append(f"生成时间: {today}")
    lines.append(f"数据来源: {chapter_count} 章标注文本（chapter_md/*.tagged.md）")
    lines.append("生成依据: 直接扫描 〖TYPE X〗 与 ⟦VERB X⟧ 标注的条目数与出现次数")
    lines.append(f"生成脚本: `scripts/generate_entity_stats_report.py`")
    lines.append("")
    lines.append(f"## 一、名词实体统计（{len(NOUN_TYPES)} 类）")
    lines.append("")
    lines.append("| 类型 | 符号  | 条目数 | 出现数 | 占比（出现） | 示例 |")
    lines.append("| ---- | ----- | -----: | -----: | -----------: | ---- |")
    for m, v in noun_sorted:
        pct = 100 * v["occurrences"] / total_noun_occ if total_noun_occ else 0
        lines.append(
            f"| {v['label']} | 〖{m}〗 | {v['entries']:,} | {v['occurrences']:,} | {pct:.1f}% | {EXAMPLES.get(m, '')} |"
        )
    lines.append("")
    lines.append(f"**名词小计**：条目 {total_noun_entries:,} · 出现 {total_noun_occ:,}（100.0%）")
    lines.append("")
    lines.append(f"## 二、动词实体统计（{len(VERB_TYPES)} 类）")
    lines.append("")
    lines.append("| 类型 | 符号  | 条目数 | 出现数 | 占比（出现） | 示例 |")
    lines.append("| ---- | ----- | -----: | -----: | -----------: | ---- |")
    for m, v in verb_sorted:
        pct = 100 * v["occurrences"] / total_verb_occ if total_verb_occ else 0
        lines.append(
            f"| {v['label']} | ⟦{m}⟧ | {v['entries']:,} | {v['occurrences']:,} | {pct:.1f}% | {EXAMPLES.get(m, '')} |"
        )
    lines.append("")
    lines.append(f"**动词小计**：条目 {total_verb_entries:,} · 出现 {total_verb_occ:,}（100.0%）")
    lines.append("")
    lines.append("## 三、总体统计")
    lines.append("")
    lines.append("| 维度 | 条目数 | 出现数 | 类别 |")
    lines.append("| ---- | -----: | -----: | ---: |")
    lines.append(f"| 名词实体 | {total_noun_entries:,} | {total_noun_occ:,} | {len(NOUN_TYPES)} 类 |")
    lines.append(f"| 动词实体 | {total_verb_entries:,} | {total_verb_occ:,} | {len(VERB_TYPES)} 类 |")
    lines.append(
        f"| **总计** | **{grand_entries:,}** | **{grand_occ:,}** | **{len(NOUN_TYPES) + len(VERB_TYPES)} 类** |"
    )
    lines.append("")
    lines.append(f"章节数：{chapter_count} 章")
    avg_occ = grand_occ / chapter_count if chapter_count else 0
    avg_ent = grand_entries / chapter_count if chapter_count else 0
    lines.append(f"平均密度：约 {avg_occ:,.0f} 出现/章 · {avg_ent:,.0f} 条目/章（去重前聚合）")
    lines.append("")
    lines.append("## 四、Top 10 实体类型（按出现数）")
    lines.append("")
    lines.append("| 排名 | 类型 | 出现数 | 占比 |")
    lines.append("| ---: | ---- | -----: | ---: |")
    for i, (label, marker, occ) in enumerate(top10, 1):
        pct = 100 * occ / grand_occ if grand_occ else 0
        symbol = f"⟦{marker}⟧" if marker in VERB_TYPES else ""
        name = f"{label} {symbol}".strip() if symbol else label
        lines.append(f"| {i:>2} | {name:<16} | {occ:,} | {pct:.1f}% |")
    lines.append("")
    lines.append(f"## 五、{version} 版本更新")
    lines.append("")
    lines.append("> 本节由人工填写：与上一版的规模变化、重点类别变化、反思贡献、相关文档链接。")
    lines.append("> 参考：`doc/entities/实体标注统计/实体标注统计报告_v4.1.md`。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--version", default=None, help="报告版本号（如 v4.2）。默认用日期 v{YYMMDD}")
    parser.add_argument("--output", type=Path, default=None, help="输出路径（默认写入 doc/entities/实体标注统计/）")
    parser.add_argument("--stdout", action="store_true", help="只打印到 stdout，不写文件")
    parser.add_argument("--json", type=Path, default=None, help="同时导出原始数据 JSON")
    parser.add_argument("--chapter-dir", type=Path, default=CHAPTER_DIR, help="标注章节目录")
    args = parser.parse_args()

    today = datetime.date.today().strftime("%Y-%m-%d")
    version = args.version or f"v{datetime.date.today().strftime('%y%m%d')}"

    stats = scan_chapters(args.chapter_dir)
    report = render_report(stats, version, today)

    if args.stdout:
        sys.stdout.write(report)
    else:
        out = args.output or (DEFAULT_OUT_DIR / f"实体标注统计报告_{version}.md")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        try:
            rel = out.relative_to(ROOT)
        except ValueError:
            rel = out
        print(f"✓ 写入报告：{rel}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ 写入 JSON：{args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
