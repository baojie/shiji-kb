"""
经济动词候选词扫描 — 试探性

目的：在全部 130 章 *.tagged.md 中，统计候选经济动词在**裸字**（未被任何 〖〗/⟦⟧/〘〙 包围）位置的出现频次，并输出上下文样本。

用法:
    python labs/research/economic_verb_scan.py [--samples N] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# 候选经济动词（单字，分组）
CANDIDATES = {
    "赏赐给予": ["赐", "赏", "予", "遗", "与"],
    "进献贡纳": ["贡", "献", "纳", "输"],
    "贿赂": ["贿", "赂"],
    "赋税敛征": ["赋", "税", "敛", "征"],
    "买卖贸易": ["买", "卖", "鬻", "贩", "市", "贸", "易", "籴", "粜"],
    "借贷": ["借", "贷", "贳"],
    "铸币": ["铸"],
    "积散致富": ["积", "散", "致", "富", "贫"],
    "赎救济": ["赎", "赈", "振", "偿", "酬"],
    "没夺": ["没", "夺"],
}

# 所有候选字（去重）
ALL_CHARS = sorted({c for chars in CANDIDATES.values() for c in chars})

# 已标注区块：〖...〗、⟦...⟧、〘...〙（非贪婪）
TAGGED_REGION = re.compile(r"〖[^〖〗]*?〗|⟦[^⟦⟧]*?⟧|〘[^〘〙]*?〙")

# 区块/标题/表格分隔行
STRUCTURAL_LINE = re.compile(r"^(##|#|\*\*|---|\|)")


def strip_tagged(line: str) -> tuple[str, list[tuple[int, int]]]:
    """返回：去除标注后的裸文本 + 每个裸字符在原行中的索引映射

    实际上：我们只想统计原行中**不在**任何标注括号内的字符。
    """
    mask = [True] * len(line)
    for m in TAGGED_REGION.finditer(line):
        for i in range(m.start(), m.end()):
            mask[i] = False
    return line, mask


def scan_file(path: Path, samples_per_char: int = 3) -> dict:
    """扫描一个 tagged.md 文件。返回 {char: {"count": n, "samples": [...]}}"""
    result: dict[str, dict] = defaultdict(lambda: {"count": 0, "samples": []})
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip() or STRUCTURAL_LINE.match(line):
            continue
        _, mask = strip_tagged(line)
        for i, ch in enumerate(line):
            if ch in ALL_CHARS and mask[i]:
                entry = result[ch]
                entry["count"] += 1
                if len(entry["samples"]) < samples_per_char:
                    # 取字前后各 12 字窗口
                    start = max(0, i - 12)
                    end = min(len(line), i + 13)
                    snippet = line[start:end]
                    entry["samples"].append({
                        "chapter": path.stem,
                        "line": lineno,
                        "ctx": snippet,
                    })
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=3, help="每字每章保留样本数")
    ap.add_argument("--out", type=str, default=None, help="输出 JSON 路径")
    ap.add_argument("--dir", type=str,
                    default="chapter_md", help="tagged.md 目录")
    args = ap.parse_args()

    chapter_dir = Path(args.dir)
    files = sorted(chapter_dir.glob("*.tagged.md"))
    if not files:
        print(f"未找到 tagged.md 文件：{chapter_dir}", file=sys.stderr)
        sys.exit(1)

    # 全局聚合：{char: {"total": n, "by_chapter": {ch: n}, "samples": [..]}}
    aggregate: dict[str, dict] = {c: {"total": 0, "by_chapter": {}, "samples": []}
                                  for c in ALL_CHARS}

    for f in files:
        per_file = scan_file(f, samples_per_char=args.samples)
        ch_id = f.stem.split("_", 1)[0]
        for ch, info in per_file.items():
            aggregate[ch]["total"] += info["count"]
            aggregate[ch]["by_chapter"][ch_id] = info["count"]
            # 只保留全局前 N 个样本（最多 args.samples * 5）
            cap = args.samples * 5
            remain = cap - len(aggregate[ch]["samples"])
            if remain > 0:
                aggregate[ch]["samples"].extend(info["samples"][:remain])

    # 打印汇总
    print("# 经济动词候选扫描报告\n")
    print(f"扫描章节数：{len(files)}\n")
    for group_name, chars in CANDIDATES.items():
        print(f"\n## {group_name}\n")
        print("| 字 | 总频次 | 出现章节数 | Top 5 章节 (频次) |")
        print("|----|-------:|-----------:|-------------------|")
        for c in chars:
            info = aggregate[c]
            total = info["total"]
            by_ch = info["by_chapter"]
            n_ch = sum(1 for v in by_ch.values() if v > 0)
            top5 = sorted(by_ch.items(), key=lambda x: -x[1])[:5]
            top5_s = ", ".join(f"{k}({v})" for k, v in top5 if v > 0)
            print(f"| {c} | {total} | {n_ch} | {top5_s} |")

    # 样本
    print("\n\n# 样本（每字最多展示 5 条）\n")
    for c in ALL_CHARS:
        info = aggregate[c]
        if info["total"] == 0:
            continue
        print(f"\n## 『{c}』 总频次 {info['total']}\n")
        for s in info["samples"][:5]:
            print(f"- [{s['chapter']}:{s['line']}] ...{s['ctx']}...")

    if args.out:
        Path(args.out).write_text(
            json.dumps(aggregate, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n\nJSON 写入：{args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
