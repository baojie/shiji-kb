#!/usr/bin/env python3
"""
检测分节标题位置错误

规则：分节标题（##、###）必须出现在顶级段落之前，不应该出现在二级、三级、四级段落之前。

顶级段落：[N]（如[1]、[4]、[10]）
非顶级段落：[N.M]、[N.M.K]、[N.M.K.L]（如[4.1]、[1.2.3]）

错误示例：
[4] 黄帝二十五子，其得姓者十四人。
### 后裔与世系    ← 错误！### 不应该在非顶级段落前
[4.1] 黄帝居轩辕之丘...

正确示例：
### 后裔与世系    ← 正确！### 在顶级段落前
[4] 黄帝二十五子，其得姓者十四人。
[4.1] 黄帝居轩辕之丘...
"""

import re
import sys
from pathlib import Path


def is_heading(line):
    """判断是否为标题行（##、###）"""
    stripped = line.strip()
    if stripped.startswith('# ['):  # 跳过带编号的一级标题
        return False
    if stripped.startswith('## ') or stripped.startswith('### '):
        return True
    return False


def get_heading_level(line):
    """获取标题级别（2或3）"""
    stripped = line.strip()
    if stripped.startswith('### '):
        return 3
    elif stripped.startswith('## '):
        return 2
    return 0


def is_paragraph_number(line):
    """判断是否为段落编号行"""
    stripped = line.strip()
    # 匹配 [N] 或 [N.M] 或 [N.M.K] 等
    match = re.match(r'\[(\d+(?:\.\d+)*)\]', stripped)
    return match


def is_top_level_paragraph(pn):
    """判断段落编号是否为顶级（如[1]、[4]，而非[4.1]）"""
    return '.' not in pn


def check_section_positions(file_path):
    """检查文件中的分节位置错误"""
    errors = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]

        # 如果当前行是标题
        if is_heading(line):
            heading_level = get_heading_level(line)
            heading_text = line.strip()
            heading_line_num = i + 1

            # 查找标题后的第一个段落编号（跳过空行）
            j = i + 1
            while j < len(lines):
                next_line = lines[j]

                # 跳过空行、分隔线、::: 标记
                if not next_line.strip() or next_line.strip() == '---' or next_line.strip().startswith(':::'):
                    j += 1
                    continue

                # 如果是段落编号
                match = is_paragraph_number(next_line)
                if match:
                    pn = match.group(1)
                    pn_line_num = j + 1

                    # 检查是否为非顶级段落
                    if not is_top_level_paragraph(pn):
                        errors.append({
                            'line': heading_line_num,
                            'heading': heading_text,
                            'heading_level': heading_level,
                            'paragraph': f'[{pn}]',
                            'paragraph_line': pn_line_num,
                            'error': f'{heading_level}级标题出现在非顶级段落[{pn}]之前'
                        })
                    break
                else:
                    # 如果遇到非段落编号的内容，停止查找
                    break

        i += 1

    return errors


def main():
    # 获取所有tagged.md文件
    chapter_dir = Path(__file__).parent.parent / 'chapter_md'
    tagged_files = sorted(chapter_dir.glob('*.tagged.md'))

    total_errors = 0
    files_with_errors = []

    print("=" * 80)
    print("分节位置检查报告")
    print("=" * 80)
    print()

    for file_path in tagged_files:
        errors = check_section_positions(file_path)

        if errors:
            total_errors += len(errors)
            files_with_errors.append((file_path.name, errors))

            print(f"【{file_path.name}】发现 {len(errors)} 处错误")
            print("-" * 80)

            for err in errors:
                print(f"  行 {err['line']}: {err['heading']}")
                print(f"    → 错误: {err['error']}")
                print(f"    → 位置: {err['heading']} (第{err['line']}行) → {err['paragraph']} (第{err['paragraph_line']}行)")
                print()

            print()

    # 汇总报告
    print("=" * 80)
    print("汇总")
    print("=" * 80)
    print(f"检查文件数: {len(tagged_files)}")
    print(f"有错误的文件数: {len(files_with_errors)}")
    print(f"错误总数: {total_errors}")
    print()

    if files_with_errors:
        print("有错误的文件列表:")
        for filename, errors in files_with_errors:
            print(f"  - {filename}: {len(errors)}处错误")
        print()
        return 1
    else:
        print("✓ 所有文件检查通过！")
        return 0


if __name__ == '__main__':
    sys.exit(main())
