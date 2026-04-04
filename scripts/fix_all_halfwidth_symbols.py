#!/usr/bin/env python3
"""
修复所有半角符号为全角符号

包括：
- 句号 . -> 。
- 冒号 : -> ：
- 逗号 , -> ，

用法：
    # 修复所有章节
    python scripts/fix_all_halfwidth_symbols.py

    # 只修复指定章节
    python scripts/fix_all_halfwidth_symbols.py 037 038 039
    python scripts/fix_all_halfwidth_symbols.py 001-010
    python scripts/fix_all_halfwidth_symbols.py 037-039 050

    # 运行测试
    python scripts/fix_all_halfwidth_symbols.py --test
"""

import argparse
import sys
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


def parse_chapter_spec(spec: str) -> list[int]:
    """
    解析章节参数，支持单个章节号或范围

    Args:
        spec: 章节参数，如 "037", "001-010", "037-039"

    Returns:
        章节号列表

    Examples:
        >>> parse_chapter_spec("037")
        [37]
        >>> parse_chapter_spec("001-003")
        [1, 2, 3]
        >>> parse_chapter_spec("037-039")
        [37, 38, 39]
    """
    if '-' in spec:
        # 范围格式: 001-010
        start, end = spec.split('-')
        start_num = int(start)
        end_num = int(end)
        return list(range(start_num, end_num + 1))
    else:
        # 单个章节: 037
        return [int(spec)]


def get_chapter_files(chapter_md_dir: Path, chapters: list[int] = None) -> list[Path]:
    """
    获取要处理的章节文件列表

    Args:
        chapter_md_dir: chapter_md 目录路径
        chapters: 要处理的章节号列表，None表示处理所有章节

    Returns:
        文件路径列表
    """
    if chapters is None:
        # 处理所有章节
        return sorted(chapter_md_dir.glob('*.tagged.md'))

    # 处理指定章节
    files = []
    for chapter_num in chapters:
        # 匹配格式: NNN_*.tagged.md
        pattern = f"{chapter_num:03d}_*.tagged.md"
        matches = list(chapter_md_dir.glob(pattern))
        if matches:
            files.extend(matches)
        else:
            print(f"⚠️  未找到章节 {chapter_num:03d}")

    return sorted(files)


def run_tests():
    """运行测试用例"""
    print("🧪 运行测试用例...")
    print("=" * 60)

    test_cases = [
        # (输入, 预期输出, 说明)
        ("这是句号.", "这是句号。", "句号替换"),
        ("标题: 内容", "标题： 内容", "冒号替换（保留空格）"),
        ("标题:内容", "标题：内容", "冒号替换（无空格）"),
        ("第一,第二,第三", "第一，第二，第三", "逗号替换"),
        ("〖◆宋〗", "〖◆宋〗", "标注内符号不变"),
        ("〖@人名〗说: 你好.", "〖@人名〗说： 你好。", "标注外符号替换（带空格）"),
        ("〖@人名〗说:你好.", "〖@人名〗说：你好。", "标注外符号替换（无空格）"),
        ("⟦◈攻⟧〖◆齐〗", "⟦◈攻⟧〖◆齐〗", "多种标注符号不变"),
        ("数字3.14159", "数字3.14159", "小数点保留"),
        ("时间12:30分", "时间12:30分", "时间冒号保留"),
        ("数量1,000,000个", "数量1,000,000个", "千分位逗号保留"),
        ("前面。〖◆齐〗后面.", "前面。〖◆齐〗后面。", "混合测试"),
        ('〖@微子〗说:"好."', '〖@微子〗说："好。"', "复杂标点混合"),
        (":::warning", ":::warning", "Markdown容器语法保留"),
    ]

    passed = 0
    failed = 0

    for i, (input_text, expected, description) in enumerate(test_cases, 1):
        result = fix_halfwidth_symbols(input_text)
        if result == expected:
            print(f"✅ 测试 {i}: {description}")
            passed += 1
        else:
            print(f"❌ 测试 {i}: {description}")
            print(f"   输入: {input_text}")
            print(f"   期望: {expected}")
            print(f"   实际: {result}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")

    return failed == 0


def main():
    """主函数：批量修复 tagged.md 文件"""
    parser = argparse.ArgumentParser(
        description='修复半角符号为全角符号',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                      # 修复所有章节
  %(prog)s 037 038 039          # 修复指定章节
  %(prog)s 001-010              # 修复章节范围
  %(prog)s 037-039 050          # 混合使用
  %(prog)s --test               # 运行测试
        """
    )
    parser.add_argument(
        'chapters',
        nargs='*',
        help='要修复的章节号或范围（如: 037, 001-010, 037-039）'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='运行测试用例'
    )

    args = parser.parse_args()

    # 运行测试模式
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    # 解析章节参数
    chapter_nums = None
    if args.chapters:
        chapter_nums = []
        for spec in args.chapters:
            try:
                chapter_nums.extend(parse_chapter_spec(spec))
            except ValueError as e:
                print(f"❌ 无效的章节参数: {spec}")
                sys.exit(1)
        chapter_nums = sorted(set(chapter_nums))  # 去重并排序

    # 获取文件列表
    chapter_md_dir = Path(__file__).parent.parent / 'chapter_md'

    if not chapter_md_dir.exists():
        print(f"❌ 目录不存在: {chapter_md_dir}")
        sys.exit(1)

    tagged_files = get_chapter_files(chapter_md_dir, chapter_nums)

    if not tagged_files:
        print("❌ 未找到任何匹配的 .tagged.md 文件")
        sys.exit(1)

    # 显示处理信息
    if chapter_nums:
        print(f"📁 将处理 {len(chapter_nums)} 个指定章节")
        print(f"   章节: {', '.join(f'{n:03d}' for n in chapter_nums)}")
    else:
        print(f"📁 将处理所有章节")
    print(f"   找到 {len(tagged_files)} 个文件")
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

    if total_files_fixed > 0:
        print(f"\n💡 建议:")
        print(f"   1. 运行验证脚本: python scripts/lint_symbol_conflicts.py")
        print(f"   2. 使用 git diff 检查修改是否正确")
        print(f"   3. 如无误，使用 git add 暂存变更")
    else:
        print(f"\n✅ 所有文件都已是全角符号，无需修复")


if __name__ == '__main__':
    main()
