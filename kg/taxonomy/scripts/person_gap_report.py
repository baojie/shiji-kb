#!/usr/bin/env python3
"""
人物分类树缺口分析 — entity_index.json vs person.ttl

功能：
  对比最新的 person 实体索引与已分类的 person.ttl，
  列出"在索引中、但尚未归入分类树"的人名，按出现次数分桶。

输出：
  - 控制台：桶统计 + Top 缺口
  - kg/taxonomy/person_gap_report.md：完整缺口清单（可用于增量分类）

用法：
  python kg/taxonomy/scripts/person_gap_report.py
  python kg/taxonomy/scripts/person_gap_report.py --min-count 5
  python kg/taxonomy/scripts/person_gap_report.py --output /tmp/gap.md
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from rdflib import Graph
from rdflib.namespace import OWL, RDF, RDFS

ROOT = Path(__file__).resolve().parents[3]
TTL = ROOT / "kg" / "taxonomy" / "person.ttl"
INDEX = ROOT / "kg" / "entities" / "data" / "entity_index.json"
ALIASES = ROOT / "kg" / "entities" / "data" / "entity_aliases.json"
DEFAULT_OUT = ROOT / "kg" / "taxonomy" / "person_gap_report.md"


def load_ttl_labels(ttl_path: Path) -> set[str]:
    g = Graph()
    g.parse(str(ttl_path), format="turtle")
    labels: set[str] = set()
    for s in g.subjects():
        if (s, RDF.type, OWL.Class) in g:
            continue
        for _, _, lbl in g.triples((s, RDFS.label, None)):
            labels.add(str(lbl))
    return labels


def load_person_index(index_path: Path) -> dict[str, int]:
    idx = json.loads(index_path.read_text(encoding="utf-8"))
    raw = idx["person"]
    out: dict[str, int] = {}
    for name, val in raw.items():
        if isinstance(val, dict):
            out[name] = val.get("count", 0)
        else:
            out[name] = int(val)
    return out


def load_canonical_set(aliases_path: Path) -> set[str]:
    """从 entity_aliases.json 返回所有 person canonical 名（用于反向映射缺口）"""
    data = json.loads(aliases_path.read_text(encoding="utf-8"))
    return {e["canonical"] for e in data.get("person", [])}


def bucket(count: int) -> str:
    if count >= 50: return ">=50"
    if count >= 20: return "20-49"
    if count >= 10: return "10-19"
    if count >= 5:  return "5-9"
    if count >= 2:  return "2-4"
    return "1"


BUCKET_ORDER = [">=50", "20-49", "10-19", "5-9", "2-4", "1"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-count", type=int, default=0,
                    help="只报告出现次数 >= N 的缺口（默认 0 = 全部）")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT,
                    help=f"输出 MD 路径（默认 {DEFAULT_OUT}）")
    args = ap.parse_args()

    ttl_labels = load_ttl_labels(TTL)
    index = load_person_index(INDEX)
    canonicals = load_canonical_set(ALIASES) if ALIASES.exists() else set()

    missing = {n: c for n, c in index.items() if n not in ttl_labels}
    extra = ttl_labels - set(index.keys())

    # 若 missing 名可通过 aliases 归到某个 canonical，则标记"别名缺口"
    alias_covered = {n for n in missing if n in canonicals}
    truly_new = {n: c for n, c in missing.items() if n not in alias_covered}

    # 桶统计
    counts = Counter(bucket(c) for c in truly_new.values())
    print(f"[索引] person: {len(index)}")
    print(f"[分类树] person.ttl 实例: {len(ttl_labels)}")
    print(f"[缺口] 在索引但未入树: {len(missing)}")
    print(f"  其中经别名可归: {len(alias_covered)}")
    print(f"  真实未分类: {len(truly_new)}")
    print(f"[疑似] TTL 中已无索引对应: {len(extra)}")
    print()
    print("按出现次数分桶（真实未分类）:")
    for b in BUCKET_ORDER:
        print(f"  {b:>6}: {counts[b]}")

    # 写 MD 报告
    lines: list[str] = []
    lines.append("# 人物分类树缺口报告")
    lines.append("")
    lines.append(f"- 索引 person 总数：**{len(index)}**")
    lines.append(f"- 分类树实例数：**{len(ttl_labels)}**")
    lines.append(f"- 缺口总数：**{len(missing)}**（其中 {len(alias_covered)} 可由别名归并，{len(truly_new)} 需新分类）")
    lines.append(f"- TTL 冗余（索引中已不存在）：**{len(extra)}**")
    lines.append("")
    lines.append("## 按出现次数分桶")
    lines.append("")
    lines.append("| 出现次数 | 缺口条目数 | 说明 |")
    lines.append("|---------|-----------|------|")
    bucket_note = {
        ">=50":  "高频：必须入树",
        "20-49": "高频：必须入树",
        "10-19": "中频：应入树",
        "5-9":   "中频：建议入树",
        "2-4":   "低频：择优入树",
        "1":     "极低频：可留待自动脚本批量归类",
    }
    for b in BUCKET_ORDER:
        lines.append(f"| {b} | {counts[b]} | {bucket_note[b]} |")
    lines.append("")

    # 按桶分组列出（>=5 的全列，其余只示例）
    for b in BUCKET_ORDER:
        items = [(n, c) for n, c in truly_new.items() if bucket(c) == b]
        items.sort(key=lambda x: (-x[1], x[0]))
        if not items:
            continue
        lines.append(f"## 出现次数 {b}（{len(items)} 条）")
        lines.append("")
        show_all = b in (">=50", "20-49", "10-19", "5-9")
        shown = items if show_all else items[:50]
        for n, c in shown:
            lines.append(f"- {n} ({c})")
        if not show_all and len(items) > len(shown):
            lines.append(f"- … 其余 {len(items) - len(shown)} 条未列出")
        lines.append("")

    # 别名可归并部分
    if alias_covered:
        lines.append("## 可由别名归并的缺口（无需新分类）")
        lines.append("")
        lines.append(f"共 {len(alias_covered)} 条。这些短名在 `entity_aliases.json` 中已有 canonical，")
        lines.append("只需确保 canonical 已在 TTL 中，别名显示由渲染层处理。")
        lines.append("")

    # TTL 冗余
    if extra:
        lines.append("## TTL 中的冗余实例（索引中已不存在）")
        lines.append("")
        lines.append(f"共 {len(extra)} 条。可能是规范名合并后的旧残留，建议审查后清理。")
        lines.append("")
        for name in sorted(extra)[:50]:
            lines.append(f"- {name}")
        if len(extra) > 50:
            lines.append(f"- … 其余 {len(extra) - 50} 条未列出")
        lines.append("")

    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n报告已写入: {args.output}")


if __name__ == "__main__":
    main()
