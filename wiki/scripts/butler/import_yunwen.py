#!/usr/bin/env python3
"""
import_yunwen.py — 将 data/yunwen.json 中的所有韵文导入 wiki。

为每条韵文创建一个 wiki 页面（type: sanwen, essay_type: 赞/诗歌/赋）。
通过 add_page.py 写入（自动记录修订）。

用法:
    python3 wiki/scripts/butler/import_yunwen.py [--dry-run] [--max N]
"""

from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES_DIR = ROOT / "wiki/public/pages"
YUNWEN_JSON = ROOT / "data/yunwen.json"
ADD_PAGE = ROOT / "wiki/scripts/butler/add_page.py"

ESSAY_TYPE_TAGS = {
    "赞": ["赞", "韵文", "史记"],
    "诗歌": ["诗歌", "韵文", "史记"],
    "赋": ["赋", "韵文", "史记"],
}


def strip_markup(text: str) -> str:
    """去除标注符号，保留原文字符。类型前缀始终为单个符号字符。"""
    # 消歧语法：〖TYPE display|canonical〗 → display（保留显示文本）
    text = re.sub(r'〖.([^|〗]+)\|[^〗]+〗', r'\1', text)
    # 普通实体标注 〖TYPE text〗 → text（TYPE 为单字符）
    text = re.sub(r'〖.([^〗〖]+)〗', r'\1', text)
    # 动词标注 ⟦TYPE verb⟧ → verb
    text = re.sub(r'⟦.([^⟧]+)⟧', r'\1', text)
    # 成语标注 〘TYPE text〙 → text
    text = re.sub(r'〘.([^〙]+)〙', r'\1', text)
    # 段落号 [28] [29.1] → 去掉
    text = re.sub(r'^\[[\d.]+\]\s*', '', text, flags=re.MULTILINE)
    # 残余标注符号清理
    text = re.sub(r'[〖〗⟦⟧〘〙]', '', text)
    # 去掉首尾引号（全角左右双引号）
    text = text.replace('“', '').replace('”', '').strip()
    # 折叠多余空行为单空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 如无换行，在标点后加换行（适用短诗）
    if '\n' not in text:
        text = re.sub(r'([，。！？；])(?!\Z)', r'\1\n', text)
    return text.strip()


def extract_pn(content: str, chapter_num: str) -> str | None:
    """从内容的首行段落号提取 PN，格式 (NNN-M)。"""
    m = re.match(r'^\[(\d+(?:\.\d+)?)\]', content.strip())
    if m:
        return f"({chapter_num}-{m.group(1)})"
    return None


def make_slug(title: str, seq: int, total_same: int) -> str:
    """生成页面 slug。重复标题加（一）（二）区分。"""
    if total_same > 1:
        suffixes = ["一", "二", "三", "四", "五"]
        suffix = suffixes[seq - 1] if seq - 1 < len(suffixes) else str(seq)
        return f"{title}（{suffix}）"
    return title


def build_page(slug: str, d: dict, pn: str | None, clean_text: str) -> str:
    """构建 wiki 页面 markdown 文本。"""
    chapter_num = d["chapter_num"]
    chapter_title = d["chapter_title"]
    essay_type = d["type"]
    title = d["title"]
    tags = ESSAY_TYPE_TAGS.get(essay_type, ["韵文", "史记"])

    tags_yaml = "[" + ", ".join(tags) + "]"
    aliases_yaml = f'["{title}"]' if slug != title else "[]"

    pn_block = f"\npn: {pn}" if pn else ""

    chapter_slug = f"{chapter_num}_{chapter_title}"
    source_ref = f"《史记·{chapter_title}》（{chapter_num}）"
    if pn:
        source_ref += f"，{pn}"

    return f"""---
id: {slug}
type: sanwen
label: {slug}
aliases: {aliases_yaml}
tags: {tags_yaml}
chapter_no: "{chapter_num}"
essay_type: {essay_type}
sources: [{chapter_title}]{pn_block}
---

# {slug}

出自{source_ref}。

## 原文

{clean_text}

## 相关章节

[[{chapter_slug}]]
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写入")
    ap.add_argument("--max", type=int, default=999, help="最多处理 N 条")
    args = ap.parse_args()

    data = json.loads(YUNWEN_JSON.read_text(encoding="utf-8"))

    # 统计重复标题
    title_counts = Counter(d["title"] for d in data)
    title_seq: dict[str, int] = {}  # title → current seq

    created = 0
    skipped = 0

    for d in data:
        if created + skipped >= args.max:
            break

        title = d["title"]
        title_seq[title] = title_seq.get(title, 0) + 1
        seq = title_seq[title]
        slug = make_slug(title, seq, title_counts[title])

        page_path = PAGES_DIR / f"{slug}.md"
        if page_path.exists():
            print(f"[跳过] {slug}（已存在）")
            skipped += 1
            continue

        pn = extract_pn(d["content"], d["chapter_num"])
        clean = strip_markup(d["content"])
        page_md = build_page(slug, d, pn, clean)

        if args.dry_run:
            print(f"[预览] {slug}")
            print(page_md[:300])
            print("...")
            created += 1
            continue

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                         encoding="utf-8", delete=False) as f:
            f.write(page_md)
            tmp_path = f.name

        summary = f"butler/import-yunwen: 导入{d['type']}《{slug}》from {d['chapter_num']}_{d['chapter_title']}"
        result = subprocess.run(
            [sys.executable, str(ADD_PAGE), slug, tmp_path,
             "--summary", summary, "--author", "butler"],
            capture_output=True, text=True
        )
        Path(tmp_path).unlink(missing_ok=True)

        if result.returncode == 0:
            print(f"[✓] {slug}")
            created += 1
        else:
            print(f"[✗] {slug}: {result.stderr.strip()}")

    print(f"\n完成：创建 {created} 页，跳过 {skipped} 页")
    return 0


if __name__ == "__main__":
    sys.exit(main())
