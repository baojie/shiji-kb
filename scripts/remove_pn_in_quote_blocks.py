#!/usr/bin/env python3
"""
删除 ::: 引用块内部的所有Purple Numbers

用法：
    python scripts/remove_pn_in_quote_blocks.py <文件路径1> [文件路径2 ...]
"""

import re
import sys
from pathlib import Path


def remove_pn_in_quote_blocks(content: str) -> tuple[str, int]:
    """
    删除 ::: 引用块内部的Purple Numbers

    返回：(处理后的内容, 删除的PN数量)
    """
    lines = content.split('\n')
    result_lines = []
    in_quote_block = False
    removed_count = 0

    for line in lines:
        stripped = line.strip()

        # 检测引用块开始
        if stripped.startswith(':::'):
            in_quote_block = True
            result_lines.append(line)
            continue

        # 检测引用块结束
        if in_quote_block and stripped == ':::':
            in_quote_block = False
            result_lines.append(line)
            continue

        # 在引用块内部，检查是否为Purple Number
        if in_quote_block:
            # 匹配独立的Purple Number行（如 [31.1]、[32]）
            pn_pattern = r'^\[\d+(?:\.\d+)?\]\s*$'
            if re.match(pn_pattern, stripped):
                removed_count += 1
                continue  # 跳过这一行

            # 匹配行首的Purple Number（如 [31.1] "大王欲得...）
            line_with_pn_pattern = r'^(\[\d+(?:\.\d+)?\])\s+'
            match = re.match(line_with_pn_pattern, line)
            if match:
                # 删除Purple Number，保留其余内容
                pn_text = match.group(1)
                line = line[len(pn_text):].lstrip()
                removed_count += 1

        result_lines.append(line)

    return '\n'.join(result_lines), removed_count


def process_file(file_path: Path) -> tuple[bool, int]:
    """
    处理单个文件

    返回：(是否修改, 删除的PN数量)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        new_content, removed = remove_pn_in_quote_blocks(content)

        if removed > 0:
            file_path.write_text(new_content, encoding='utf-8')
            return True, removed
        else:
            return False, 0

    except Exception as e:
        print(f"✗ 处理文件 {file_path} 时出错: {e}", file=sys.stderr)
        return False, 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    print("=" * 70)
    print("删除 ::: 引用块内部的Purple Numbers")
    print("=" * 70)

    total_files = 0
    total_removed = 0

    for file_arg in sys.argv[1:]:
        file_path = Path(file_arg)

        if not file_path.exists():
            print(f"✗ 文件不存在: {file_path}")
            continue

        modified, removed = process_file(file_path)

        if modified:
            print(f"✓ {file_path.name}: 删除 {removed} 个编号")
            total_files += 1
            total_removed += removed
        else:
            print(f"  {file_path.name}: 无需修改")

    print("=" * 70)
    print(f"✓ 处理完成!")
    print(f"  修改文件数: {total_files}")
    print(f"  删除编号总数: {total_removed}")
    print("=" * 70)


if __name__ == '__main__':
    main()
