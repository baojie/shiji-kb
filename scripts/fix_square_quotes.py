#!/usr/bin/env python3
"""
修复直角引号为弯引号

将日文风格的直角引号替换为中文弯引号：
- 「 → "（左双引号）
- 」 → "（右双引号）
- 『 → '（左单引号）
- 』 → '（右单引号）

根据古籍标点规范，中文引号应使用弯引号，不使用直角引号。
"""

from pathlib import Path


def fix_square_quotes(text: str) -> str:
    """
    替换直角引号为弯引号

    直角引号主要用于日文，中文应使用弯引号。
    替换规则：
    - 「 (U+300C) → " (U+201C) 左双引号
    - 」 (U+300D) → " (U+201D) 右双引号
    - 『 (U+300E) → ' (U+2018) 左单引号
    - 』 (U+300F) → ' (U+2019) 右单引号
    """
    # 使用Unicode码点明确指定全角弯引号
    replacements = {
        '「': chr(0x201C),  # 左直角引号 → 左弯双引号 "
        '」': chr(0x201D),  # 右直角引号 → 右弯双引号 "
        '『': chr(0x2018),  # 左双直角引号 → 左弯单引号 '
        '』': chr(0x2019),  # 右双直角引号 → 右弯单引号 '
    }

    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)

    return result


def fix_file(file_path: Path) -> tuple[int, dict]:
    """
    修复单个文件中的直角引号

    Returns:
        (总修复数量, 各类引号修复数量字典)
    """
    content = file_path.read_text(encoding='utf-8')

    # 统计修复前的引号数
    before_counts = {
        '「': content.count('「'),
        '」': content.count('」'),
        '『': content.count('『'),
        '』': content.count('』'),
    }

    # 修复
    new_content = fix_square_quotes(content)

    # 统计修复后的引号数（应该都是0）
    after_counts = {
        '「': new_content.count('「'),
        '」': new_content.count('」'),
        '『': new_content.count('『'),
        '』': new_content.count('』'),
    }

    # 计算实际修复数量
    fixed_counts = {
        '左直角引号「': before_counts['「'] - after_counts['「'],
        '右直角引号」': before_counts['」'] - after_counts['」'],
        '左双直角『': before_counts['『'] - after_counts['『'],
        '右双直角』': before_counts['』'] - after_counts['』'],
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
    total_counts = {
        '左直角引号「': 0,
        '右直角引号」': 0,
        '左双直角『': 0,
        '右双直角』': 0,
    }

    for file_path in tagged_files:
        total_fixed, fixed_counts = fix_file(file_path)

        if total_fixed > 0:
            total_files_fixed += 1
            for key in total_counts:
                total_counts[key] += fixed_counts[key]

            print(f"\n✅ {file_path.name}")
            print(f"   修复 {total_fixed} 处直角引号")
            details = []
            for key, count in fixed_counts.items():
                if count > 0:
                    details.append(f"{key}: {count}处")
            if details:
                print(f"   - {', '.join(details)}")

    print("\n" + "=" * 60)
    print(f"📊 修复完成:")
    print(f"   - 修复文件数: {total_files_fixed}")
    print(f"   - 修复引号总数: {sum(total_counts.values())}")

    # 显示各类引号的修复统计
    for key, count in total_counts.items():
        if count > 0:
            print(f"     · {key}: {count} 处")

    print(f"\n💡 建议:")
    print(f"   1. 运行验证脚本: python scripts/lint_symbol_conflicts.py chapter_md/*.tagged.md --check-types square")
    print(f"   2. 使用 git diff 检查修改是否正确")
    print(f"   3. 如无误，使用 git add 暂存变更")


if __name__ == '__main__':
    main()
