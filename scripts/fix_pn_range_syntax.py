#!/usr/bin/env python3
"""
扫描并修复 wiki 页面中错误的 PN 范围格式。

错误格式：(031-41.1-41.4)  — 括号内用连字符连接多个段号
正确格式：(031-41.1) (41.4) — 每个段号独立括号，第二个省略章节前缀

用法：
    python3 scripts/fix_pn_range_syntax.py          # 仅扫描，不修改
    python3 scripts/fix_pn_range_syntax.py --fix    # 扫描并修复
"""

import re
import sys
from pathlib import Path

PAGES_DIR = Path("wiki/public/pages")

# 匹配 (NNN-X.Y-Z.W) 或 (NNN-X.Y-Z.W-A.B) 等多段连字符格式
# 章节号：3位数字；段号：数字（可含小数点）
PN_RANGE_RE = re.compile(
    r'\((\d{3})-(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))+\)'
)


def fix_pn_range(m: re.Match) -> str:
    """将 (031-41.1-41.4) 替换为 (031-41.1) (41.4)"""
    full = m.group(0)
    chapter = m.group(1)
    # 提取括号内所有段号（去掉首尾括号后按连字符切分，第一个是章节号）
    inner = full[1:-1]  # 去掉括号
    parts = inner.split('-')
    # parts[0] 是章节号，parts[1:] 是各段号（可能含小数点，所以按第一个非纯数字再分）
    # 重新解析：章节 = parts[0]，其余按实际分组
    # 由于小数点存在，简单 split('-') 可能把 "41.1" 拆成 "41.1" 正确，但要注意
    # 实际例子：031-41.1-41.4 → ['031', '41.1', '41.4']
    chapter_part = parts[0]
    seg_parts = parts[1:]
    fixed = f'({chapter_part}-{seg_parts[0]})' + ''.join(f' ({s})' for s in seg_parts[1:])
    return fixed


def scan_file(path: Path, fix: bool = False) -> list[tuple[int, str, str]]:
    """扫描单个文件，返回 [(行号, 原文, 修复后)] 列表"""
    text = path.read_text(encoding='utf-8')
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if PN_RANGE_RE.search(line):
            fixed_line = PN_RANGE_RE.sub(fix_pn_range, line)
            if fixed_line != line:
                hits.append((i, line.strip(), fixed_line.strip()))
    return hits


def process_all(fix: bool = False):
    pages = sorted(PAGES_DIR.glob("*.md"))
    total_hits = 0
    total_files = 0

    for path in pages:
        hits = scan_file(path, fix=fix)
        if not hits:
            continue
        total_files += 1
        total_hits += len(hits)
        print(f"\n{'[修复]' if fix else '[发现]'} {path.name}")
        for lineno, orig, fixed in hits:
            print(f"  行{lineno}: {orig}")
            if fix:
                print(f"       → {fixed}")

    if fix and total_hits > 0:
        # 实际写入修复
        for path in pages:
            text = path.read_text(encoding='utf-8')
            new_text = PN_RANGE_RE.sub(fix_pn_range, text)
            if new_text != text:
                path.write_text(new_text, encoding='utf-8')

    print(f"\n{'修复' if fix else '扫描'}完成：{total_files} 个文件，{total_hits} 处{'已修复' if fix else '待修复'}")
    if not fix and total_hits > 0:
        print("运行 --fix 参数以自动修复。")


if __name__ == '__main__':
    do_fix = '--fix' in sys.argv
    process_all(fix=do_fix)
