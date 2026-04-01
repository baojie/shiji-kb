#!/usr/bin/env python3
"""
修正已经被错误替换的全角引号

问题：之前的脚本将所有半角引号都替换成了全角左引号 "
解决：将错误的全角左引号 " 改为正确的全角右引号 "
"""

from pathlib import Path


def fix_quotes_in_line(line: str) -> str:
    """
    修正引号：将错误的全角左引号改为正确的全角右引号

    规则：
    1. 后面紧跟标点符号的 " 应该是右引号 "
    2. 前面紧跟冒号、标点的 " 应该是左引号 "
    3. 成对出现：第一个 " 保持左引号，第二个改为右引号 "
    """
    FULLWIDTH_LEFT = chr(0x201C)  # 全角左引号 "
    FULLWIDTH_RIGHT = chr(0x201D)  # 全角右引号 "

    if FULLWIDTH_LEFT not in line:
        return line

    result = []
    quote_open = False

    for i, char in enumerate(line):
        if char == FULLWIDTH_LEFT:
            # 判断是否应该是右引号
            next_char = line[i+1] if i < len(line) - 1 else ''

            # 如果后面是标点符号，应该是右引号
            if next_char in ('，', '。', '！', '？', '、', '；', '」', '』', '】', '〗', ')', '）', '', ']', '\n', ' ', '\t'):
                result.append(FULLWIDTH_RIGHT)
                quote_open = False
            # 否则，根据配对状态判断
            elif not quote_open:
                result.append(FULLWIDTH_LEFT)
                quote_open = True
            else:
                result.append(FULLWIDTH_RIGHT)
                quote_open = False
        elif char == FULLWIDTH_RIGHT:
            # 保持右引号
            result.append(FULLWIDTH_RIGHT)
            quote_open = False
        else:
            result.append(char)

    return ''.join(result)


def fix_file(file_path: Path) -> tuple[int, int, int]:
    """
    修正单个文件中的引号

    Returns:
        (修改前左引号数, 修改前右引号数, 修改行数)
    """
    FULLWIDTH_LEFT = chr(0x201C)
    FULLWIDTH_RIGHT = chr(0x201D)

    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    # 统计修改前的引号数
    before_left = content.count(FULLWIDTH_LEFT)
    before_right = content.count(FULLWIDTH_RIGHT)

    changed_lines = 0
    new_lines = []

    for line in lines:
        new_line = fix_quotes_in_line(line)
        if new_line != line:
            changed_lines += 1
        new_lines.append(new_line)

    new_content = '\n'.join(new_lines)

    # 统计修改后的引号数
    after_left = new_content.count(FULLWIDTH_LEFT)
    after_right = new_content.count(FULLWIDTH_RIGHT)

    # 只在有变化时写入
    if new_content != content:
        file_path.write_text(new_content, encoding='utf-8')

    return before_left, before_right, after_left, after_right, changed_lines


def main():
    """主函数：批量修正所有 tagged.md 文件"""
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
        before_left, before_right, after_left, after_right, changed_lines = fix_file(file_path)

        if changed_lines > 0:
            total_files_fixed += 1
            quotes_fixed = before_left - after_left
            total_quotes_fixed += quotes_fixed

            print(f"\n✅ {file_path.name}")
            print(f"   修改前: 左引号={before_left}, 右引号={before_right}")
            print(f"   修改后: 左引号={after_left}, 右引号={after_right}")
            print(f"   修改了 {changed_lines} 行，转换 {quotes_fixed} 个引号")

    print("\n" + "=" * 60)
    print(f"📊 修复完成:")
    print(f"   - 修复文件数: {total_files_fixed}")
    print(f"   - 转换引号数: {total_quotes_fixed} (左引号→右引号)")
    print(f"\n💡 建议:")
    print(f"   1. 运行验证脚本: python scripts/lint_symbol_conflicts.py")
    print(f"   2. 使用 git diff 检查修改是否正确")
    print(f"   3. 如无误，使用 git add 暂存变更")


if __name__ == '__main__':
    main()
