"""
经济动词标注预览 — 为指定章节输出候选字的每处裸字上下文，便于人工/Agent 决策。

用法:
    python labs/research/economic_verb_preview.py 030 [125 129 ...]
    python labs/research/economic_verb_preview.py 030 --chars 赐赏赂贡

输出 (stdout):
    # 030_平准书
    ## 赐 (共 N 处)
      [1] lineno=XX offset=YY  ...前文|赐|后文...
      ...
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TAGGED_REGION = re.compile(r"〖[^〖〗]*?〗|⟦[^⟦⟧]*?⟧|〘[^〘〙]*?〙")
STRUCTURAL_LINE = re.compile(r"^(##|#|\*\*|---|\|)")

# 19 字精简名单 + 需复核的歧义字
SHORTLIST = list("赐赏赂贡赋税买卖输纳铸借贷偿赎鬻粜籴贳")
AMBIGUOUS = list("夺献市遗予振")
DEFAULT_CHARS = SHORTLIST + AMBIGUOUS


def is_tagged(line: str, idx: int) -> bool:
    for m in TAGGED_REGION.finditer(line):
        if m.start() <= idx < m.end():
            return True
    return False


def scan_chapter(path: Path, chars: list[str]) -> None:
    print(f"\n# {path.stem}\n")
    text = path.read_text(encoding="utf-8")
    buckets: dict[str, list[tuple[int, int, str]]] = {c: [] for c in chars}
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip() or STRUCTURAL_LINE.match(line):
            continue
        for i, ch in enumerate(line):
            if ch in buckets and not is_tagged(line, i):
                start = max(0, i - 18)
                end = min(len(line), i + 19)
                ctx = line[start:i] + f"【{ch}】" + line[i+1:end]
                buckets[ch].append((lineno, i, ctx))
    for c in chars:
        rows = buckets[c]
        if not rows:
            continue
        print(f"## {c} (共 {len(rows)} 处)")
        for k, (ln, off, ctx) in enumerate(rows, 1):
            print(f"  [{k}] L{ln:3d}:{off:3d}  {ctx}")
        print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chapters", nargs="+", help="章节编号（如 030）")
    ap.add_argument("--chars", default=None, help="自定义字符串")
    ap.add_argument("--dir", default="chapter_md")
    args = ap.parse_args()
    chars = list(args.chars) if args.chars else DEFAULT_CHARS
    chapter_dir = Path(args.dir)
    for ch in args.chapters:
        files = list(chapter_dir.glob(f"{ch}_*.tagged.md"))
        if not files:
            print(f"未找到章节 {ch}", file=sys.stderr)
            continue
        scan_chapter(files[0], chars)


if __name__ == "__main__":
    main()
