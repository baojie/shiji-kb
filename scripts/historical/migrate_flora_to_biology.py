#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移标注符号：〘X〙 → 〖+X〗（动植物→生物）

扫描 chapter_md/*.tagged.md，将独立的〘〙括号替换为统一的〖+〗格式。
不修改 chapter_md_backup/ 目录。

用法：
    python scripts/migrate_flora_to_biology.py --dry-run   # 预览
    python scripts/migrate_flora_to_biology.py              # 执行
"""

import re
import sys
from pathlib import Path

CHAPTER_DIR = Path('chapter_md')
PATTERN = re.compile(r'〘([^〘〙\n]+)〙')
REPLACEMENT = r'〖+\1〗'


def migrate_file(fpath: Path, dry_run: bool = True) -> int:
    """迁移单个文件，返回替换次数"""
    text = fpath.read_text(encoding='utf-8')
    count = len(PATTERN.findall(text))
    if count == 0:
        return 0

    if dry_run:
        for m in PATTERN.finditer(text):
            print(f'  {fpath.name}: 〘{m.group(1)}〙 → 〖+{m.group(1)}〗')
        return count

    new_text = PATTERN.sub(REPLACEMENT, text)
    fpath.write_text(new_text, encoding='utf-8')
    return count


def main():
    dry_run = '--dry-run' in sys.argv

    if not CHAPTER_DIR.exists():
        print(f'错误：{CHAPTER_DIR} 不存在')
        sys.exit(1)

    files = sorted(CHAPTER_DIR.glob('*.tagged.md'))
    print(f'扫描 {len(files)} 个文件...' + (' (预览模式)' if dry_run else ''))

    total = 0
    changed_files = 0
    for fpath in files:
        count = migrate_file(fpath, dry_run)
        if count > 0:
            total += count
            changed_files += 1
            if not dry_run:
                print(f'  ✓ {fpath.name}: {count} 处替换')

    print(f'\n{"预览" if dry_run else "完成"}：{changed_files} 个文件，{total} 处替换')
    if dry_run:
        print('执行替换请去掉 --dry-run 参数')


if __name__ == '__main__':
    main()
