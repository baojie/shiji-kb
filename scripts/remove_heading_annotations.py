#!/usr/bin/env python3
"""
去除Markdown标题行中的所有实体和动词标注，但保留标注内的文字内容

根据 SKILL_03a 原则零：Markdown结构性元素不参与标注
- 各级标题（# ## ### ####）整行不标注
- 清理标题中的所有 〖TYPE 内容〗 和 ⟦TYPE内容⟧ 标注，保留内容文字

正确示例：
  ## 司〖~马〗氏的家⟦◉族⟧世系  →  ## 司马氏的家族世系
  # [0] 〖@老子〗〖@韩非〗列传   →  # [0] 老子韩非列传

Usage:
    python scripts/remove_heading_annotations.py chapter_md/NNN_*.tagged.md
    python scripts/remove_heading_annotations.py chapter_md/*.tagged.md
"""

import re
import sys
from pathlib import Path


# 实体标注前缀字符
_ENTITY_PFX = r'[#@=;$%&^\~•!\'+?{:\[_]'


def strip_markup_from_heading(line: str) -> str:
    """
    从标题行中移除标注符号，但保留标注内的文字内容

    参考 lint_text_integrity.py 的 strip_markup() 函数

    Args:
        line: 标题行文本

    Returns:
        清理后的标题行（保留文字内容）
    """
    # 1. 动词标注括号 → 保留内容（支持消歧 ⟦◈伐|征伐⟧ → 伐）
    line = re.sub(r'⟦[◈◉○◇]([^⟦⟧|]*)(?:\|[^⟦⟧]*)?⟧', r'\1', line)

    # 2. 名词实体标注括号 → 保留内容（支持内联消歧 〖@台|吕台〗 → 台）
    line = re.sub(rf'〖{_ENTITY_PFX}([^〖〗|]*)(?:\|[^〖〗]*)?〗', r'\1', line)

    # 3. 剩余残留标注（理论上不应有，但为保险起见）
    line = re.sub(r'〖[^〗]*〗', '', line)

    return line


def process_file(filepath: Path) -> tuple[int, list[str]]:
    """
    处理单个文件，移除所有标题行中的标注但保留文字内容

    Args:
        filepath: 文件路径

    Returns:
        (修改的标题数量, 修改详情列表)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified_count = 0
    changes = []
    new_lines = []

    for i, line in enumerate(lines, 1):
        # 检查是否为标题行（以#开头，可能有前置空格）
        if re.match(r'^\s*#+\s', line):
            cleaned = strip_markup_from_heading(line)
            if cleaned != line:
                modified_count += 1
                # 截断显示，避免输出过长
                orig_display = line.strip()[:80]
                cleaned_display = cleaned.strip()[:80]
                if len(line.strip()) > 80:
                    orig_display += "..."
                if len(cleaned.strip()) > 80:
                    cleaned_display += "..."
                changes.append(f"  行{i}: {orig_display}")
                changes.append(f"     → {cleaned_display}")
                new_lines.append(cleaned)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if modified_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return modified_count, changes


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/remove_heading_annotations.py chapter_md/*.tagged.md")
        sys.exit(1)

    files = [Path(arg) for arg in sys.argv[1:]]

    total_files = 0
    total_modified = 0

    print("=== 清理标题标注（保留文字内容） ===\n")

    for filepath in sorted(files):
        if not filepath.exists():
            print(f"⚠️  文件不存在: {filepath}")
            continue

        count, changes = process_file(filepath)

        if count > 0:
            total_files += 1
            total_modified += count
            print(f"✓ {filepath.name}: 修改 {count} 个标题")
            if len(changes) <= 10:  # 显示前5个修改（每个占2行）
                for change in changes:
                    print(change)
            else:
                for change in changes[:6]:  # 显示前3个修改
                    print(change)
                print(f"  ... 还有 {count-3} 处修改")
            print()

    print("=== 汇总 ===")
    print(f"处理文件: {len(files)}")
    print(f"修改文件: {total_files}")
    print(f"修改标题: {total_modified}")


if __name__ == '__main__':
    main()
