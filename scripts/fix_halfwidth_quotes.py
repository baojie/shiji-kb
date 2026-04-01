#!/usr/bin/env python3
"""
修复 chapter_md 中的半角引号问题

根据 logs/symbol_conflicts_20260401.txt 检查报告，
将所有半角引号 " 替换为全角引号 " 或 "（根据上下文判断左右）
"""

import re
from pathlib import Path


def fix_quotes_in_line(line: str) -> str:
    """
    智能替换半角引号为全角引号

    规则：
    1. 双引号 " -> 全角 " 或 "
    2. 单引号 ' -> 全角 ' 或 '
    3. 判断左右：后面紧跟标点的为右引号，否则根据配对状态判断
    """
    # 使用Unicode码点定义字符
    HALFWIDTH_DOUBLE = chr(0x22)  # 半角双引号 "
    FULLWIDTH_DOUBLE_LEFT = chr(0x201C)  # 全角左双引号 "
    FULLWIDTH_DOUBLE_RIGHT = chr(0x201D)  # 全角右双引号 "

    HALFWIDTH_SINGLE = chr(0x27)  # 半角单引号 '
    FULLWIDTH_SINGLE_LEFT = chr(0x2018)  # 全角左单引号 '
    FULLWIDTH_SINGLE_RIGHT = chr(0x2019)  # 全角右单引号 '

    if HALFWIDTH_DOUBLE not in line and HALFWIDTH_SINGLE not in line:
        return line

    result = []
    double_quote_open = False  # 双引号是否开启
    single_quote_open = False  # 单引号是否开启

    # 定义判断字符集
    right_quote_followers = set('，。！？、；」』】〗)）]' + '\n' + ':')  # 右引号后面的字符
    left_quote_preceeders = set(' \t：，。！？、；「『【〖(（[]】') | {FULLWIDTH_DOUBLE_LEFT, FULLWIDTH_SINGLE_LEFT, ''}  # 左引号前面的字符

    for i, char in enumerate(line):
        prev_char = line[i-1] if i > 0 else ''
        next_char = line[i+1] if i < len(line) - 1 else ''

        # 处理双引号
        if char == HALFWIDTH_DOUBLE:
            # 优先根据后一个字符判断（右引号的特征更明确）
            if next_char in right_quote_followers:
                result.append(FULLWIDTH_DOUBLE_RIGHT)
                double_quote_open = False
            # 然后根据前一个字符判断
            elif prev_char in left_quote_preceeders:
                result.append(FULLWIDTH_DOUBLE_LEFT)
                double_quote_open = True
            # 最后根据配对状态判断
            elif not double_quote_open:
                result.append(FULLWIDTH_DOUBLE_LEFT)
                double_quote_open = True
            else:
                result.append(FULLWIDTH_DOUBLE_RIGHT)
                double_quote_open = False

        # 处理单引号
        elif char == HALFWIDTH_SINGLE:
            # 优先根据后一个字符判断
            if next_char in right_quote_followers or next_char == FULLWIDTH_DOUBLE_LEFT:
                result.append(FULLWIDTH_SINGLE_RIGHT)
                single_quote_open = False
            # 然后根据前一个字符判断
            elif prev_char in left_quote_preceeders or prev_char == FULLWIDTH_DOUBLE_LEFT:
                result.append(FULLWIDTH_SINGLE_LEFT)
                single_quote_open = True
            # 最后根据配对状态判断
            elif not single_quote_open:
                result.append(FULLWIDTH_SINGLE_LEFT)
                single_quote_open = True
            else:
                result.append(FULLWIDTH_SINGLE_RIGHT)
                single_quote_open = False

        else:
            result.append(char)

    return ''.join(result)


def fix_file(file_path: Path) -> tuple[int, list[str]]:
    """
    修复单个文件中的半角引号

    Returns:
        (修复数量, 修复详情列表)
    """
    HALFWIDTH_DOUBLE = chr(0x22)  # 半角双引号 "
    HALFWIDTH_SINGLE = chr(0x27)  # 半角单引号 '

    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    fixed_count = 0
    changes = []
    new_lines = []

    for line_no, line in enumerate(lines, 1):
        if HALFWIDTH_DOUBLE in line or HALFWIDTH_SINGLE in line:
            new_line = fix_quotes_in_line(line)
            if new_line != line:
                count_double = line.count(HALFWIDTH_DOUBLE)
                count_single = line.count(HALFWIDTH_SINGLE)
                count = count_double + count_single
                fixed_count += count
                changes.append(f"行{line_no}: {count}处（双引号{count_double}，单引号{count_single}）")
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if fixed_count > 0:
        file_path.write_text('\n'.join(new_lines), encoding='utf-8')

    return fixed_count, changes


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
    total_quotes_fixed = 0

    for file_path in tagged_files:
        fixed_count, changes = fix_file(file_path)

        if fixed_count > 0:
            total_files_fixed += 1
            total_quotes_fixed += fixed_count
            print(f"\n✅ {file_path.name}")
            print(f"   修复 {fixed_count} 处半角引号")
            for change in changes[:5]:  # 只显示前5条
                print(f"   - {change}")
            if len(changes) > 5:
                print(f"   ... 还有 {len(changes) - 5} 处")

    print("\n" + "=" * 60)
    print(f"📊 修复完成:")
    print(f"   - 修复文件数: {total_files_fixed}")
    print(f"   - 修复引号数: {total_quotes_fixed}")
    print(f"\n💡 建议:")
    print(f"   1. 运行验证脚本: python scripts/lint_symbol_conflicts.py")
    print(f"   2. 使用 git diff 检查修改是否正确")
    print(f"   3. 如无误，使用 git add 暂存变更")


if __name__ == '__main__':
    main()
