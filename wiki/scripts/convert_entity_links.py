#!/usr/bin/env python3
"""
convert_entity_links.py — 将 wiki 页面中指向实体索引 HTML 的外部链接转化为 wikilinks。

转化规则：

Pattern 1 (章节页实体列表，约 3095 条):
  [显示名](../entities/TYPE.html#entity-ID)
  → [[canonical|显示名]]  (若 ID 在 alias_index 且 canonical ≠ 显示名)
  → [[canonical]]          (若 ID 在 alias_index 且 canonical == 显示名)
  → [[ID|显示名]]          (若 ID 无 alias 且 显示名 ≠ ID)
  → [[ID]]                 (若 ID 无 alias 且 显示名 == ID)

Pattern 2 (实体页底部外部索引，约 474 条):
  *外部索引*: [xxx.html#NAME](../../docs/entities/TYPE.html#NAME)
  → 整行删除（wiki 页面即规范实体页，外链已无必要）

用法：
    python3 wiki/scripts/convert_entity_links.py --dry-run
    python3 wiki/scripts/convert_entity_links.py --dry-run --file 028_封禅书
    python3 wiki/scripts/convert_entity_links.py --apply
    python3 wiki/scripts/convert_entity_links.py --apply --pattern 1
    python3 wiki/scripts/convert_entity_links.py --apply --pattern 2
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGES_DIR = ROOT / "wiki/public/pages"
PAGES_JSON = ROOT / "wiki/public/pages.json"

# ---------- 正则 ----------

# Pattern 1: [显示名](../entities/TYPE.html#entity-ID)
P1_RE = re.compile(
    r'\[([^\]\n]+?)\]\(\.\./entities/\w+\.html#entity-([^\)\n]+?)\)'
)

# Pattern 2: *外部索引*: [xxx.html#NAME](../../docs/entities/TYPE.html#NAME)\n?
# 整行（含前置空格/星号到行尾）
P2_RE = re.compile(
    r'[ \t]*\*外部索引\*:[ \t]*\[[^\]\n]*\]\([^\)\n]*docs/entities/[^\)\n]*\)[ \t]*\n?'
)


def load_alias_index() -> dict[str, str]:
    if not PAGES_JSON.exists():
        return {}
    data = json.loads(PAGES_JSON.read_text(encoding="utf-8"))
    return data.get("alias_index", {})


def make_wikilink(entity_id: str, display: str, alias_index: dict[str, str]) -> str:
    """给定 entity_id 和显示名，返回最简 wikilink。"""
    canonical = alias_index.get(entity_id, entity_id)
    if canonical == display:
        return f"[[{canonical}]]"
    return f"[[{canonical}|{display}]]"


def convert_p1(content: str, alias_index: dict[str, str]) -> tuple[str, int]:
    """替换 Pattern 1，返回 (新内容, 替换数)。"""
    count = 0

    def replacer(m: re.Match) -> str:
        nonlocal count
        display = m.group(1)
        entity_id = m.group(2)
        count += 1
        return make_wikilink(entity_id, display, alias_index)

    new_content = P1_RE.sub(replacer, content)
    return new_content, count


def convert_p2(content: str) -> tuple[str, int]:
    """删除 Pattern 2 行，返回 (新内容, 删除数)。"""
    new_content, count = P2_RE.subn("", content)
    return new_content, count


def process_file(
    md_path: Path,
    alias_index: dict[str, str],
    pattern: str,
    dry_run: bool,
    verbose: bool = False,
) -> dict:
    """处理单个文件，返回统计字典。"""
    original = md_path.read_text(encoding="utf-8")
    content = original
    p1_count = p2_count = 0

    if pattern in ("1", "both"):
        content, p1_count = convert_p1(content, alias_index)
    if pattern in ("2", "both"):
        content, p2_count = convert_p2(content)

    total = p1_count + p2_count
    if total == 0:
        return {"p1": 0, "p2": 0}

    if verbose:
        print(f"  {md_path.name}: P1={p1_count} P2={p2_count}")

    if not dry_run and content != original:
        md_path.write_text(content, encoding="utf-8")

    return {"p1": p1_count, "p2": p2_count}


def show_diff_preview(md_path: Path, alias_index: dict[str, str], pattern: str, n: int = 5) -> None:
    """打印前 n 条替换预览。"""
    content = md_path.read_text(encoding="utf-8")
    shown = 0
    if pattern in ("1", "both"):
        for m in P1_RE.finditer(content):
            if shown >= n:
                break
            display, entity_id = m.group(1), m.group(2)
            wl = make_wikilink(entity_id, display, alias_index)
            print(f"    - [{display}](entity-{entity_id}) → {wl}")
            shown += 1
    if pattern in ("2", "both"):
        for m in P2_RE.finditer(content):
            if shown >= n:
                break
            print(f"    - (删除) {m.group(0)!r:.80s}")
            shown += 1


def main() -> int:
    ap = argparse.ArgumentParser(description="实体外链 → wikilink 转化工具")
    ap.add_argument("--apply", action="store_true", help="实际写入文件（默认仅 dry-run）")
    ap.add_argument("--dry-run", action="store_true", help="仅预览，不写文件（默认）")
    ap.add_argument("--pattern", choices=["1", "2", "both"], default="both",
                    help="转化哪种模式（默认: both）")
    ap.add_argument("--file", default=None,
                    help="只处理指定文件（不含 .md 后缀），用于测试")
    ap.add_argument("--preview-lines", type=int, default=3,
                    help="dry-run 时每文件预览的替换条数（默认 3）")
    args = ap.parse_args()

    dry_run = not args.apply  # 默认 dry-run

    alias_index = load_alias_index()
    print(f"alias_index 条目: {len(alias_index)}")
    print(f"模式: {'dry-run' if dry_run else 'APPLY'} | pattern={args.pattern}")
    print()

    if args.file:
        target = PAGES_DIR / f"{args.file}.md"
        if not target.exists():
            print(f"文件不存在: {target}")
            return 1
        files = [target]
    else:
        files = sorted(PAGES_DIR.glob("*.md"))

    total_p1 = total_p2 = total_files = 0

    for md_path in files:
        original = md_path.read_text(encoding="utf-8")
        # 快速检查是否有需要处理的内容
        has_p1 = "../entities/" in original and "#entity-" in original
        has_p2 = "*外部索引*:" in original
        if not has_p1 and not has_p2:
            continue

        stats = process_file(md_path, alias_index, args.pattern, dry_run, verbose=False)
        if stats["p1"] + stats["p2"] == 0:
            continue

        total_files += 1
        total_p1 += stats["p1"]
        total_p2 += stats["p2"]

        action = "预览" if dry_run else "转化"
        print(f"[{action}] {md_path.name}  P1={stats['p1']} P2={stats['p2']}")
        if dry_run and args.preview_lines > 0:
            show_diff_preview(md_path, alias_index, args.pattern, args.preview_lines)

    print()
    print(f"{'=' * 50}")
    print(f"涉及文件: {total_files}")
    print(f"Pattern 1 替换: {total_p1} 条（外链→wikilink）")
    print(f"Pattern 2 删除: {total_p2} 条（外部索引行）")
    print(f"合计: {total_p1 + total_p2} 处")
    if dry_run:
        print()
        print("⚠️  dry-run 模式，未写入文件。加 --apply 参数执行实际转化。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
