#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 always_identity 词表中的 〖;X〗 标注批量改为 〖#X〗（身份类型）。
"""

import re
from pathlib import Path

ALWAYS_IDENTITY = [
    "天子", "太子", "太后", "夫人", "皇子", "皇后", "公主",
    "人臣", "功臣", "宦者", "贵人", "大臣", "美人", "帝王",
    "士大夫", "公卿", "先王", "将相", "皇帝", "陛下", "霸王",
    "卿相", "宠臣", "诸侯", "列侯", "少主", "皇太后", "皇太子",
    "长公主", "大长公主", "妃", "食客", "外戚",
]

# 构造替换模式：〖;天子〗 → 〖#天子〗（精确匹配，不误替换子串）
REPLACEMENTS = {f'〖;{w}〗': f'〖#{w}〗' for w in ALWAYS_IDENTITY}

def process_file(path: Path) -> int:
    text = path.read_text(encoding='utf-8')
    original = text
    count = 0
    for old, new in REPLACEMENTS.items():
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            count += n
    if count:
        path.write_text(text, encoding='utf-8')
    return count


def main():
    chapter_dir = Path('chapter_md')
    files = sorted(chapter_dir.glob('*.tagged.md'))
    total = 0
    changed_files = 0
    for f in files:
        n = process_file(f)
        if n:
            print(f"  {f.name}: {n}处")
            total += n
            changed_files += 1
    print(f"\n合计：{changed_files}个文件，{total}处 〖;〗→〖#〗（身份）")


if __name__ == '__main__':
    main()
