#!/usr/bin/env python3
"""
修复所有半角符号为全角符号

包括：
- 句号 . -> 。
- 冒号 : -> ：
- 逗号 , -> ，
"""

from pathlib import Path


def is_inside_tag(text: str, position: int) -> bool:
    """
    检查给定位置是否在标注符号内部

    标注符号格式：〖TYPE content〗 或 ⟦TYPE content⟧

    Args:
        text: 完整文本
        position: 要检查的位置索引

    Returns:
        True 如果在标注内部，False 否则
    """
    # 从position向前查找最近的标注开始符号
    last_open_square = text.rfind('〖', 0, position)
    last_open_round = text.rfind('⟦', 0, position)
    last_open = max(last_open_square, last_open_round)

    # 从position向前查找最近的标注结束符号
    last_close_square = text.rfind('〗', 0, position)
    last_close_round = text.rfind('⟧', 0, position)
    last_close = max(last_close_square, last_close_round)

    # 如果找到了开始符号，且在结束符号之后（或没有结束符号），则在标注内
    if last_open != -1 and last_open > last_close:
        return True

    return False


def fix_halfwidth_symbols(line: str) -> str:
    """
    替换半角标点符号为全角符号

    注意：
    1. 不替换数字中的小数点和时间格式中的冒号
    2. **不替换标注符号（〖〗⟦⟧）内部的符号**
    """
    # 定义替换映射
    replacements = {
        '.': '。',
        ':': '：',
        ',': '，',
    }

    result = []
    for i, char in enumerate(line):
        # ⚠️ 关键修复：检查是否在标注内部
        if is_inside_tag(line, i):
            # 标注内部保持原样，不进行替换
            result.append(char)
            continue

        if char == '.':
            # 检查是否是小数点（前后都是数字）
            prev_char = line[i-1] if i > 0 else ''
            next_char = line[i+1] if i < len(line) - 1 else ''
            if prev_char.isdigit() and next_char.isdigit():
                # 保留小数点
                result.append(char)
            else:
                # 替换为全角句号
                result.append('。')

        elif char == ':':
            # 检查是否是Markdown容器语法 ::: (三个连续冒号)
            # 向前看2个字符，向后看2个字符
            prev2 = line[max(0, i-2):i]
            next2 = line[i+1:min(len(line), i+3)]
            # 如果是 ::: 的一部分，保持原样
            if prev2 == '::' or next2 == '::' or (i > 0 and line[i-1] == ':' and i < len(line) - 1 and line[i+1] == ':'):
                result.append(char)
            # 检查是否是时间格式（如 12:30）
            elif line[i-1:i].isdigit() if i > 0 else False and (line[i+1:i+2].isdigit() if i < len(line) - 1 else False):
                # 保留时间冒号
                result.append(char)
            else:
                # 替换为全角冒号
                result.append('：')

        elif char == ',':
            # 检查是否是数字千分位（如 1,000）
            prev_char = line[i-1] if i > 0 else ''
            next_char = line[i+1] if i < len(line) - 1 else ''
            if prev_char.isdigit() and next_char.isdigit():
                # 保留千分位逗号
                result.append(char)
            else:
                # 替换为全角逗号
                result.append('，')

        else:
            result.append(char)

    return ''.join(result)


def fix_file(file_path: Path) -> tuple[int, dict]:
    """
    修复单个文件中的半角符号

    Returns:
        (总修复数量, 各类符号修复数量字典)
    """
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    # 统计修复前的符号数
    before_counts = {
        '.': content.count('.'),
        ':': content.count(':'),
        ',': content.count(','),
    }

    new_lines = []
    for line in lines:
        new_line = fix_halfwidth_symbols(line)
        new_lines.append(new_line)

    new_content = '\n'.join(new_lines)

    # 统计修复后的符号数
    after_counts = {
        '.': new_content.count('.'),
        ':': new_content.count(':'),
        ',': new_content.count(','),
    }

    # 计算实际修复数量
    fixed_counts = {
        '句号': before_counts['.'] - after_counts['.'],
        '冒号': before_counts[':'] - after_counts[':'],
        '逗号': before_counts[','] - after_counts[','],
    }

    total_fixed = sum(fixed_counts.values())

    # 只在有变化时写入
    if new_content != content:
        file_path.write_text(new_content, encoding='utf-8')

    return total_fixed, fixed_counts


def main():
    """主函数：批量修复所有 tagged.md 文件"""
    chapter_md_dir = Path(__file__).parent.parent / 'chapter_md'

    if not chapter_md_dir.exists():
        print(f"❌ 目录不存在: {chapter_md_dir}")
        return

    # 查找所有 .tagged.md 文件
    tagged_files = sorted(chapter_md_dir.glob('*.tagged.md'))

    if not tagged_files:
        print("❌ 未找到任何 .tagged.md 文件")
        return

    print(f"📁 找到 {len(tagged_files)} 个文件")
    print("=" * 60)

    total_files_fixed = 0
    total_counts = {'句号': 0, '冒号': 0, '逗号': 0}

    for file_path in tagged_files:
        total_fixed, fixed_counts = fix_file(file_path)

        if total_fixed > 0:
            total_files_fixed += 1
            for key in total_counts:
                total_counts[key] += fixed_counts[key]

            print(f"\n✅ {file_path.name}")
            print(f"   修复 {total_fixed} 处半角符号")
            details = []
            if fixed_counts['句号'] > 0:
                details.append(f"句号 {fixed_counts['句号']} 处")
            if fixed_counts['冒号'] > 0:
                details.append(f"冒号 {fixed_counts['冒号']} 处")
            if fixed_counts['逗号'] > 0:
                details.append(f"逗号 {fixed_counts['逗号']} 处")
            if details:
                print(f"   - {', '.join(details)}")

    print("\n" + "=" * 60)
    print(f"📊 修复完成:")
    print(f"   - 修复文件数: {total_files_fixed}")
    print(f"   - 修复符号总数: {sum(total_counts.values())}")
    for key, count in total_counts.items():
        if count > 0:
            print(f"     · {key}: {count} 处")
    print(f"\n💡 建议:")
    print(f"   1. 运行验证脚本: python scripts/lint_symbol_conflicts.py chapter_md/*.tagged.md --check-types halfwidth")
    print(f"   2. 使用 git diff 检查修改是否正确")
    print(f"   3. 如无误，使用 git add 暂存变更")


if __name__ == '__main__':
    main()
