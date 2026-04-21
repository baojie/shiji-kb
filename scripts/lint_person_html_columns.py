#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lint: 校验 docs/entities/person.html 的 4 列结构完整性。

人名索引页为 4 列（surface | 规范名 | 标签 | 出处），若被误写为 3 列即退化。
本脚本在 CI / pre-commit 中运行，以独立防线守卫。

校验点：
  1) 必须包含 'entry-canonical' 字符串
  2) 'entry-canonical' 列数 == 'entity-entry' 行数（不漏任何一行）
  3) 'entity-entry' >= 5000（避免空/截断写入）
  4) 同时验证 entry-left / entry-category / entry-right 也与 entity-entry 对齐

用法：
    python scripts/lint_person_html_columns.py
    python scripts/lint_person_html_columns.py --path docs/entities/person.html

退出码：
    0 = 通过
    1 = 失败（输出错误详情到 stderr）

历史教训：
    2026-04-20 commit 21abcf33 修复 build_entity_index.main() 循环 ENTITY_TYPES 时
    对 person 误走 generate_type_page 导致的 3 列退化。
"""

import argparse
import sys
from pathlib import Path


def lint(path: Path) -> list[str]:
    if not path.exists():
        return [f"文件不存在: {path}"]
    html = path.read_text(encoding='utf-8')
    errors: list[str] = []

    n_entry = html.count('class="entity-entry"')
    n_left = html.count('class="entry-left"')
    n_canon = html.count('class="entry-canonical"')
    n_cat = html.count('class="entry-category"')
    n_right = html.count('class="entry-right"')

    if 'entry-canonical' not in html:
        errors.append("缺少 entry-canonical 列 —— 已退化为 3 列模板")

    if n_entry < 5000:
        errors.append(f"条目数异常偏少: entity-entry={n_entry} (<5000)，可能空/截断写入")

    for name, count in (
        ('entry-left', n_left),
        ('entry-canonical', n_canon),
        ('entry-category', n_cat),
        ('entry-right', n_right),
    ):
        if count != n_entry:
            errors.append(
                f"列行数不一致: entity-entry={n_entry}, {name}={count} "
                f"(缺 {n_entry - count} 行)"
            )

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    default_path = Path(__file__).resolve().parent.parent / 'docs' / 'entities' / 'person.html'
    ap.add_argument('--path', type=Path, default=default_path,
                    help=f'person.html 路径（默认: {default_path}）')
    args = ap.parse_args()

    errors = lint(args.path)
    if errors:
        print(f"✗ {args.path}", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"✓ {args.path} — 4 列结构完整性校验通过")
    return 0


if __name__ == '__main__':
    sys.exit(main())
