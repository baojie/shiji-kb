#!/usr/bin/env python3
"""
规则 HT-01：018-021 侯者年表第一列"国名"一律归一为 〖◆X|X侯国〗。

覆盖情形：
- 裸字          留         → 〖◆留|留侯国〗
- 地名标注      〖=平阳〗   → 〖◆平阳|平阳侯国〗
- 人名错标      〖@信武〗   → 〖◆信武|信武侯国〗
- 职位错标      〖;冠军〗   → 〖◆冠军|冠军侯国〗
- 已是邦国      〖◆射阳〗   → 〖◆射阳|射阳侯国〗
- 已消歧        〖◆便|便侯国〗 → 不变（幂等）

只改写第一列（[rN] 之后、到第一个 "  |" 之前的内容），不动后续列。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "chapter_md/018_高祖功臣侯者年表.tagged.md",
    "chapter_md/019_惠景间侯者年表.tagged.md",
    "chapter_md/020_建元以来侯者年表.tagged.md",
    "chapter_md/021_建元已来王子侯者年表.tagged.md",
]

ROW_PATTERN = re.compile(
    r"^(\|[ \t]+\[r\d+\][ \t]+)(.*?)([ \t]+\|)",
    re.MULTILINE,
)

TAG_PATTERN = re.compile(r"^〖([^\s|〗])([^〗|]+)(?:\|([^〗]+))?〗$")


def normalize_first_cell(cell: str) -> tuple[str, str, str]:
    """返回 (规范化后的 cell, 原表面, 新规范名)。"""
    m = re.match(r"^(.*?)(。*)[ \t]*$", cell, re.DOTALL)
    body = m.group(1).rstrip() if m else cell.rstrip()
    trailing = m.group(2) if m else ""

    tag_m = TAG_PATTERN.match(body)
    if tag_m:
        surface = tag_m.group(2).strip()
    else:
        surface = body.strip()

    if not surface:
        return cell, "", ""

    canonical = f"{surface}侯国"
    new_tag = f"〖◆{surface}|{canonical}〗"
    return new_tag + trailing, surface, canonical


def process_file(path: Path, dry_run: bool = False) -> list[tuple[int, str, str]]:
    content = path.read_text(encoding="utf-8")
    changes: list[tuple[int, str, str]] = []

    line_offset = [0]
    for ch in content:
        line_offset.append(line_offset[-1] + (1 if ch == "\n" else 0))

    def replace(m: re.Match) -> str:
        prefix, cell, suffix = m.group(1), m.group(2), m.group(3)
        new_cell, surface, _ = normalize_first_cell(cell)
        if new_cell != cell:
            pos = m.start()
            line_no = content.count("\n", 0, pos) + 1
            changes.append((line_no, cell.strip(), new_cell.strip()))
        return prefix + new_cell + suffix

    new_content = ROW_PATTERN.sub(replace, content)
    if not dry_run and new_content != content:
        path.write_text(new_content, encoding="utf-8")
    return changes


def main() -> int:
    dry = "--dry-run" in sys.argv
    total = 0
    for rel in FILES:
        path = ROOT / rel
        changes = process_file(path, dry_run=dry)
        print(f"\n== {rel} ==  ({len(changes)} 条改动)")
        for line_no, old, new in changes[:10]:
            print(f"  L{line_no}: {old}  →  {new}")
        if len(changes) > 10:
            print(f"  ... 省略 {len(changes) - 10} 条")
        total += len(changes)
    print(f"\n合计：{total} 条改动" + ("（dry-run 未写盘）" if dry else "（已写回）"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
