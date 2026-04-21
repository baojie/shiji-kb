#!/usr/bin/env python3
"""半角引号 → 全角引号的作用域栈修复器。

核心规律（见 SKILL_01i §六）：
  【】夹注是独立的引号作用域。其内部引号对与外部独立计数。
  逐行重置 outer counter，限制单个语义 bug 的污染半径。

算法：
  - 遍历字符，维护一个 depth_stack（对应【】嵌套层级的计数器栈）
  - 遇到 "   在栈顶（若栈空则在 outer counter）累加
       偶索引 → 左引号 U+201C 或 U+2018
       奇索引 → 右引号 U+201D 或 U+2019
  - 遇到 \n 且栈空时 outer counter 归零（防止跨段错误传播）

输出：
  - 修改文件（默认）
  - 报告每类字符转换计数
  - 报告行级左右引号不平衡的行号（供人工补齐语义 bug）

用法：
  python scripts/curation/fix_quotes_scoped.py <path>             # 原位修改
  python scripts/curation/fix_quotes_scoped.py <path> --dry-run   # 只报告不改
  python scripts/curation/fix_quotes_scoped.py <path> --verify    # 只检查不平衡行

案例：《读史记十表》10 万字级底本，1426 个半角 " → 714 对全角，0 行不平衡。
"""

import argparse
import sys
from pathlib import Path

LEFT_D, RIGHT_D = '\u201c', '\u201d'  # " "
LEFT_S, RIGHT_S = '\u2018', '\u2019'  # ' '


def convert_scoped(text: str) -> tuple[str, dict]:
    """按【】作用域与行边界做引号转换。

    Returns:
        (转换后文本, 统计字典)
    """
    out = []
    out_d_idx = 0
    out_s_idx = 0
    depth_d: list[int] = []  # 双引号计数器栈
    depth_s: list[int] = []  # 单引号计数器栈

    n_dq_converted = 0
    n_sq_converted = 0

    for c in text:
        if c == '【':
            depth_d.append(0)
            depth_s.append(0)
            out.append(c)
        elif c == '】':
            if depth_d:
                depth_d.pop()
            if depth_s:
                depth_s.pop()
            out.append(c)
        elif c == '"':
            if depth_d:
                idx = depth_d[-1]
                out.append(LEFT_D if idx % 2 == 0 else RIGHT_D)
                depth_d[-1] = idx + 1
            else:
                out.append(LEFT_D if out_d_idx % 2 == 0 else RIGHT_D)
                out_d_idx += 1
            n_dq_converted += 1
        elif c == "'":
            if depth_s:
                idx = depth_s[-1]
                out.append(LEFT_S if idx % 2 == 0 else RIGHT_S)
                depth_s[-1] = idx + 1
            else:
                out.append(LEFT_S if out_s_idx % 2 == 0 else RIGHT_S)
                out_s_idx += 1
            n_sq_converted += 1
        elif c == '\n':
            out.append(c)
            if not depth_d:
                out_d_idx = 0
            if not depth_s:
                out_s_idx = 0
        else:
            out.append(c)

    new_text = ''.join(out)
    stats = {
        'dq_converted': n_dq_converted,
        'sq_converted': n_sq_converted,
        'dq_left': new_text.count(LEFT_D),
        'dq_right': new_text.count(RIGHT_D),
        'sq_left': new_text.count(LEFT_S),
        'sq_right': new_text.count(RIGHT_S),
    }
    return new_text, stats


def find_unbalanced_lines(text: str) -> list[tuple[int, int, int, str]]:
    """找出左右引号数量不等的行。

    Returns:
        list of (line_no, n_left, n_right, line_preview)
    """
    results = []
    for i, line in enumerate(text.split('\n'), start=1):
        l = line.count(LEFT_D)
        r = line.count(RIGHT_D)
        if l != r:
            preview = line[:60]
            results.append((i, l, r, preview))
    return results


def main():
    parser = argparse.ArgumentParser(
        description='引号作用域栈修复器（SKILL_01i §六）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('path', help='待处理的 Markdown / 文本文件')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='只报告统计，不写回文件',
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='只扫描不平衡行，不做转换（用于已修复文件的巡检）',
    )
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f'错误：文件不存在：{path}', file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding='utf-8')

    if args.verify:
        unbalanced = find_unbalanced_lines(text)
        if unbalanced:
            print(f'发现 {len(unbalanced)} 行左右引号不平衡：')
            for ln, l, r, preview in unbalanced:
                print(f'  L{ln}: 左{l} 右{r}  {preview}')
            sys.exit(2)
        print('全部行左右引号平衡 ✓')
        return

    # 转换
    new_text, stats = convert_scoped(text)
    unbalanced = find_unbalanced_lines(new_text)

    print(f'{path}:')
    print(f'  半角 " 转换: {stats["dq_converted"]} 个 '
          f'→ 左 {stats["dq_left"]}, 右 {stats["dq_right"]}, '
          f'diff={stats["dq_left"] - stats["dq_right"]}')
    print(f'  半角 \' 转换: {stats["sq_converted"]} 个 '
          f'→ 左 {stats["sq_left"]}, 右 {stats["sq_right"]}, '
          f'diff={stats["sq_left"] - stats["sq_right"]}')

    if unbalanced:
        print(f'  ⚠ 不平衡行: {len(unbalanced)}（多为语义漏闭，需人工补齐）')
        for ln, l, r, preview in unbalanced[:10]:
            print(f'    L{ln}: 左{l} 右{r}  {preview}')
        if len(unbalanced) > 10:
            print(f'    ... 另 {len(unbalanced) - 10} 行')
    else:
        print('  ✓ 所有行左右引号平衡')

    if not args.dry_run:
        path.write_text(new_text, encoding='utf-8')
        print(f'  已写回 {path}')
    else:
        print('  (--dry-run：未写回)')


if __name__ == '__main__':
    main()
