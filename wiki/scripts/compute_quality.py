#!/usr/bin/env python3
"""
计算并写入每个 wiki 页面的 quality 标签（stub/basic/standard/featured/premium）。

质量五级标准：
  stub     - 存根：有 stub 注释 / 内容 < 100 字 / 无 h2 节且内容 < 300 字
  basic    - 基础：内容 < 500 字 或（节 < 2 且 PN < 2）
  standard - 标准：有内容有结构，但无配图或引注不足
  featured - 精品：有图 + ≥3 PN 或 ≥5 引文行 + ≥3 节 + 散文 ≥ 200 字
  premium  - 旗舰：有图 + ≥5 节 + 散文 ≥ 1000 字 + （PN ≥ 10 或引文 ≥ 10 或散文 ≥ 2500）

用法：
  python3 wiki/scripts/compute_quality.py              # 更新所有页面
  python3 wiki/scripts/compute_quality.py --dry-run    # 只统计，不写文件
  python3 wiki/scripts/compute_quality.py <slug>       # 只处理单个页面
"""

import re
import sys
import argparse
from pathlib import Path
from collections import Counter

PAGES_DIR = Path("wiki/public/pages")

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
PN_RE = re.compile(r"（\d{3}-\d+）")
QUALITY_VALUES = ("stub", "basic", "standard", "featured", "premium")


def compute_quality(text: str) -> str:
    m = FM_RE.match(text)
    meta_str = m.group(0) if m else ""
    content = text[m.end():] if m else text

    content_len = len(content.strip())
    has_stub = "<!-- stub:" in text
    pn_count = len(PN_RE.findall(content))
    has_image = "image:" in meta_str or "images:" in meta_str
    sections = len(re.findall(r"^## ", content, re.MULTILINE))
    quote_lines = sum(1 for l in content.split("\n") if l.startswith("> "))
    prose_paras = [
        p.strip() for p in content.split("\n\n")
        if len(p.strip()) >= 50
        and not p.strip().startswith((">", "-", "#", "|", "!", "::"))
    ]
    prose_len = sum(len(p) for p in prose_paras)

    # stub
    if has_stub or content_len < 100 or (sections == 0 and content_len < 300):
        return "stub"

    # basic
    if content_len < 500 or (sections < 2 and pn_count < 2):
        return "basic"

    # premium（先判断，避免后续条件误判）
    if (has_image and sections >= 5 and prose_len >= 1000
            and (pn_count >= 10 or quote_lines >= 10 or prose_len >= 2500)):
        return "premium"

    # featured
    if (has_image and sections >= 3
            and (pn_count >= 3 or quote_lines >= 5)
            and prose_len >= 200):
        return "featured"

    return "standard"


def update_frontmatter_quality(text: str, quality: str) -> str:
    """在 frontmatter 中写入或替换 quality 字段，同时移除 featured: true。"""
    m = FM_RE.match(text)
    if not m:
        return text

    fm = m.group(1)
    rest = text[m.end():]

    # 移除旧 quality 行和 featured 行
    fm = re.sub(r"^quality:.*\n?", "", fm, flags=re.MULTILINE)
    fm = re.sub(r"^featured:.*\n?", "", fm, flags=re.MULTILINE)

    # 在 frontmatter 末尾追加 quality
    fm = fm.rstrip("\n") + f"\nquality: {quality}\n"

    return f"---\n{fm}---\n{rest}"


def process_page(path: Path, dry_run: bool) -> tuple[str, str]:
    """返回 (old_quality, new_quality)。"""
    text = path.read_text(encoding="utf-8")

    # 读取当前 quality
    old_m = re.search(r"^quality:\s*(\S+)", text, re.MULTILINE)
    old_quality = old_m.group(1) if old_m else "none"

    new_quality = compute_quality(text)

    if not dry_run and new_quality != old_quality:
        new_text = update_frontmatter_quality(text, new_quality)
        path.write_text(new_text, encoding="utf-8")

    return old_quality, new_quality


def main():
    parser = argparse.ArgumentParser(description="Compute and write quality tags")
    parser.add_argument("slugs", nargs="*", help="Only process these slugs")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print stats without writing files")
    args = parser.parse_args()

    if args.slugs:
        paths = []
        for s in args.slugs:
            p = PAGES_DIR / f"{s}.md"
            if p.exists():
                paths.append(p)
            else:
                print(f"[warn] 未找到: {s}", file=sys.stderr)
    else:
        paths = sorted(PAGES_DIR.glob("*.md"))

    stats = Counter()
    changed = Counter()

    for path in paths:
        old_q, new_q = process_page(path, args.dry_run)
        stats[new_q] += 1
        if old_q != new_q:
            changed[f"{old_q}→{new_q}"] += 1

    total = sum(stats.values())
    mode = "[dry-run]" if args.dry_run else "[updated]"
    print(f"{mode} 共处理 {total} 页")
    for q in QUALITY_VALUES:
        n = stats.get(q, 0)
        print(f"  {q:10} {n:6d}  ({n/total*100:.1f}%)")

    if changed:
        print(f"\n变更（{sum(changed.values())} 页）：")
        for k, v in sorted(changed.items(), key=lambda x: -x[1])[:20]:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
