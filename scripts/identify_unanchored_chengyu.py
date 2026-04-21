#!/usr/bin/env python3
"""
识别 史记成语典故.md 中存在、但未被章节 〘※〙 标注的条目（"悬空条目"）。

输出:
- 已标注（annotated in tagged files）
- 悬空但在原文中出现（stripped text 包含成语名 → 可以补标）
- 悬空且原文中不出现（summarized only，需要单独保存）
"""

import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHENGYU_MD = ROOT / "kg/vocabularies/data/史记成语典故.md"
CHAPTER_DIR = ROOT / "chapter_md"


def parse_chengyu_md(md_file):
    content = md_file.read_text(encoding='utf-8')
    entries = []
    current_chapter = None
    for line in content.split('\n'):
        line = line.strip()
        m = re.match(r'^###\s+(\d+)\s+', line)
        if m:
            current_chapter = m.group(1).zfill(3)
            continue
        if current_chapter and line.startswith('|') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 2 and parts[0] and parts[0] != '成语':
                name = parts[0]
                original = parts[1] if len(parts) > 1 else ''
                meaning = parts[2] if len(parts) > 2 else ''
                if any(c in name for c in ['/', '/']):
                    continue
                if name.startswith(('（', '(')):
                    continue
                entries.append((current_chapter, name, original, meaning))
    return entries


def strip_all_markup(text):
    """去除所有标注符号，返回纯文本"""
    t = text
    t = re.sub(r'〘※([^〘〙|]+)(?:\|[^〘〙]*)?〙', r'\1', t)
    t = re.sub(r'〖.([^〖〗|]+)(?:\|[^〖〗]*)?〗', r'\1', t)
    t = re.sub(r'⟦.([^⟦⟧|]+)(?:\|[^⟦⟧]*)?⟧', r'\1', t)
    return t


def main():
    entries = parse_chengyu_md(CHENGYU_MD)
    by_chap = {}
    for c, n, o, m in entries:
        by_chap.setdefault(c, []).append((n, o, m))

    annotated = []
    in_text_untagged = []
    summarized_only = []

    for chap_num in sorted(by_chap.keys()):
        files = list(CHAPTER_DIR.glob(f"{chap_num}_*.tagged.md"))
        if not files:
            continue
        content = files[0].read_text(encoding='utf-8')
        pure = strip_all_markup(content)

        for name, original, meaning in by_chap[chap_num]:
            tagged = f'〘※{name}' in content or f'〘※' in content and any(
                f'〘※{form}' in content for form in [name, name.replace('，', ',')]
            )
            # More precise: check all 〘※X|Y〙 or 〘※X〙
            has_tag = False
            for m in re.finditer(r'〘※([^〘〙|]+)(?:\|([^〘〙]+))?〙', content):
                shiji_form = m.group(1)
                modern = m.group(2)
                if modern == name or shiji_form == name:
                    has_tag = True
                    break

            if has_tag:
                annotated.append((chap_num, name, original, meaning))
            else:
                # 检查原文中是否直接出现 name
                if name in pure:
                    in_text_untagged.append((chap_num, name, original, meaning))
                else:
                    summarized_only.append((chap_num, name, original, meaning))

    print(f"总条目: {len(entries)}")
    print(f"  已标注: {len(annotated)}")
    print(f"  原文有但未标注: {len(in_text_untagged)}")
    print(f"  仅为概括（原文无直接对应）: {len(summarized_only)}")

    print("\n=== 原文中有但未标注（可补标）===")
    for c, n, o, m in in_text_untagged:
        print(f"  [{c}] {n}  | 原文: {o} | 释义: {m}")

    print("\n=== 仅为概括，无原文对应 ===")
    for c, n, o, m in summarized_only:
        print(f"  [{c}] {n}  | 原文: {o} | 释义: {m}")


if __name__ == '__main__':
    main()
