#!/usr/bin/env python3
"""
v2 校验：检查 labs/translation/*_白话.md 中的半角标点。
可选 --fix 自动替换为对应全角。

约束（SKILL_01h v2 规则 11）：译文所有标点一律全角。允许的半角：
- 数字相邻（如"1.0"）
- 英文缩写内部（罕见）
- URL / 代码

简化策略：报告所有半角 ,.;:!? '"()，若 --fix 则按上下文替换：
- `,` → `，`（若前后不都是数字）
- `.` → `。`（若前后不都是数字）
- `;` → `；`
- `:` → `：`（若前后不都是数字）
- `!` → `！`
- `?` → `？`
- `(` `)` → `（` `）`
- `'` `"` → 中文引号（需要配对分析）

运行：
    python scripts/lint_halfwidth_punct.py                # 报告
    python scripts/lint_halfwidth_punct.py --fix           # 修复
    python scripts/lint_halfwidth_punct.py 002 --fix       # 单章
"""

import re
import sys
from pathlib import Path

TARGET_DIR = Path('labs/translation')

# 半角→全角映射（非数字语境）
SIMPLE_MAP = {
    '，': '，',  # identity, 占位
    ',': '，',
    ';': '；',
    '!': '！',
    '?': '？',
    '(': '（',
    ')': '）',
}
# 依赖上下文的：. 和 :
# .  → 。 除非前后为数字
# :  → ： 除非前后为数字（冒号在 URL/时间）


def fix_line(line: str) -> tuple:
    """
    返回 (fixed_line, changes_count)。
    关键：跳过实体标注 〖...〗、⟦...⟧、〘...〙 内部（那里的 ; : ! ? 是 marker，不是标点）。
    """
    out = []
    n = 0
    L = len(line)
    # 预计算每个位置是否在标注内
    in_tag = [False] * L
    opens = {'〖': '〗', '⟦': '⟧', '〘': '〙'}
    stack = []  # list of closing chars
    for i, ch in enumerate(line):
        if stack:
            in_tag[i] = True
            if ch == stack[-1]:
                stack.pop()
        elif ch in opens:
            in_tag[i] = True
            stack.append(opens[ch])

    for i, ch in enumerate(line):
        if in_tag[i]:
            out.append(ch)
            continue
        if ch in SIMPLE_MAP and ch != '，':
            out.append(SIMPLE_MAP[ch])
            n += 1
        elif ch == ',':
            # 半角逗号一律全角
            out.append('，')
            n += 1
        elif ch == '.':
            prev = line[i - 1] if i > 0 else ''
            nxt = line[i + 1] if i + 1 < L else ''
            if prev.isdigit() and nxt.isdigit():
                out.append(ch)  # 数字小数点保留
            else:
                out.append('。')
                n += 1
        elif ch == ':':
            prev = line[i - 1] if i > 0 else ''
            nxt = line[i + 1] if i + 1 < L else ''
            if prev.isdigit() and nxt.isdigit():
                out.append(ch)  # 时间 12:30
            else:
                out.append('：')
                n += 1
        else:
            out.append(ch)
    return ''.join(out), n


def scan(path: Path, fix: bool):
    content = path.read_text()
    total_hw = sum(content.count(c) for c in ',.;:!?()')
    # count only problematic ones (not in numeric context for . :)
    if total_hw == 0:
        return 0, 0
    new_lines = []
    total_fixed = 0
    total_issues = 0
    for line in content.splitlines(keepends=True):
        # 跳过 YAML / 代码块 / 可疑行（含拼音、ascii 标注）简化处理
        new_line, n = fix_line(line)
        total_issues += n
        if fix:
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    if fix and total_issues > 0:
        path.write_text(''.join(new_lines))
        total_fixed = total_issues
    return total_issues, total_fixed


def main():
    args = sys.argv[1:]
    fix = '--fix' in args
    chapters = [a for a in args if a != '--fix']
    if chapters:
        files = []
        for ch in chapters:
            files += list(TARGET_DIR.glob(f'{ch.zfill(3)}_*_白话.md'))
    else:
        files = sorted(TARGET_DIR.glob('*_白话.md'))

    total_issues = total_fixed = n_files_touched = 0
    for f in files:
        issues, fixed = scan(f, fix)
        if issues > 0:
            n_files_touched += 1
            total_issues += issues
            total_fixed += fixed
            status = f'修复 {fixed}' if fix else f'{issues} 处'
            print(f'  {f.name}: {status}')

    action = '已修复' if fix else '发现'
    print(f'\n{action}半角标点：{total_issues} 处，共 {n_files_touched} 章 / {len(files)}')


if __name__ == '__main__':
    main()
