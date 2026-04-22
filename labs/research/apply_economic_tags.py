"""
按 (line, 0-based col, char, type) 精确替换：将裸字 ch 替换为 ⟦◇ch⟧。

- 读取原文件、执行替换（从右到左以避免 col 漂移）、写回
- 替换前校验 line[col] == ch
- 校验 col 未处于任何已有标注内
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TAGGED_REGION = re.compile(r"〖[^〖〗]*?〗|⟦[^⟦⟧]*?⟧|〘[^〘〙]*?〙")


def in_tag(line: str, col: int) -> bool:
    for m in TAGGED_REGION.finditer(line):
        if m.start() <= col < m.end():
            return True
    return False


def apply(path: Path, edits: list[tuple[int, int, str]], dry: bool) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    # group by line
    by_line: dict[int, list[tuple[int, str]]] = {}
    for ln, col, ch in edits:
        by_line.setdefault(ln, []).append((col, ch))
    applied = 0
    errors: list[str] = []
    for ln, items in by_line.items():
        if ln - 1 >= len(lines):
            errors.append(f"L{ln}: 行号越界")
            continue
        line = lines[ln - 1]
        # 从右到左
        for col, ch in sorted(items, key=lambda x: -x[0]):
            if col >= len(line):
                errors.append(f"L{ln}:{col} 列越界 len={len(line)}")
                continue
            if line[col] != ch:
                errors.append(f"L{ln}:{col} 期望『{ch}』得到『{line[col]}』 ctx={line[max(0,col-5):col+6]!r}")
                continue
            if in_tag(line, col):
                errors.append(f"L{ln}:{col}『{ch}』已在标注内")
                continue
            line = line[:col] + f"⟦◇{ch}⟧" + line[col+1:]
            applied += 1
        lines[ln - 1] = line
    if errors:
        print("!! 发现错误:", file=sys.stderr)
        for e in errors:
            print("  ", e, file=sys.stderr)
    if not dry:
        path.write_text("\n".join(lines), encoding="utf-8")
        print(f"已写回 {path}，应用 {applied} 处")
    else:
        print(f"[dry-run] 将应用 {applied} 处，{path}")
    return len(errors)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--spec", required=True, help="每行: LINE COL CHAR")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    edits: list[tuple[int, int, str]] = []
    for ln_txt in Path(args.spec).read_text(encoding="utf-8").splitlines():
        ln_txt = ln_txt.strip()
        if not ln_txt or ln_txt.startswith("#"):
            continue
        parts = ln_txt.split()
        if len(parts) < 3:
            continue
        edits.append((int(parts[0]), int(parts[1]), parts[2]))
    errs = apply(Path(args.file), edits, args.dry)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
