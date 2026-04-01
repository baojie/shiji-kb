#!/usr/bin/env python3
"""
修复标注内部被错误替换的全角符号

问题：fix_all_halfwidth_symbols.py 在替换半角符号为全角符号时，
      没有检查是否在标注符号（〖〗⟦⟧）内部，导致标注内的半角符号也被替换。

解决方案：
1. 将标注内的全角标点符号 ：，。；！？（）""''【】 改回半角 :,.;!?()""''[]
2. 确保只修改标注内部，不影响正文

标注铁律：标注符号内部必须使用半角标点符号
"""

import re
from pathlib import Path
from typing import Tuple


def fix_symbols_in_tag(match: re.Match) -> str:
    """
    将标注内的全角符号替换为半角符号

    标注格式：〖TYPE content〗 或 ⟦TYPE content⟧

    注意：TYPE 本身可能就是全角符号（如 〖：祭祀〗 中的 ：）
    """
    full_tag = match.group(0)
    tag_start = match.group(1)  # 〖 or ⟦
    tag_type = match.group(2)   # TYPE (如 : 或 @ 等，可能是全角)
    content = match.group(3)    # 标注内容
    tag_end = match.group(4)    # 〗 or ⟧

    # 定义全角到半角的映射
    fullwidth_to_halfwidth = {
        '：': ':',
        '，': ',',
        '。': '.',
        '；': ';',
        '！': '!',
        '？': '?',
        '（': '(',
        '）': ')',
        '\u201c': '"',  # " LEFT DOUBLE QUOTATION MARK
        '\u201d': '"',  # " RIGHT DOUBLE QUOTATION MARK
        '\u2018': "'",  # ' LEFT SINGLE QUOTATION MARK
        '\u2019': "'",  # ' RIGHT SINGLE QUOTATION MARK
        '【': '[',
        '】': ']',
    }

    # ⚠️ 修复 tag_type 中的全角符号
    fixed_tag_type = tag_type
    for fullwidth, halfwidth in fullwidth_to_halfwidth.items():
        fixed_tag_type = fixed_tag_type.replace(fullwidth, halfwidth)

    # 替换content中的全角符号
    fixed_content = content
    for fullwidth, halfwidth in fullwidth_to_halfwidth.items():
        fixed_content = fixed_content.replace(fullwidth, halfwidth)

    return f"{tag_start}{fixed_tag_type}{fixed_content}{tag_end}"


def fix_file_tags(file_path: Path) -> Tuple[int, list]:
    """
    修复文件中所有标注内的全角符号

    Returns:
        (修复数量, 修复详情列表)
    """
    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # 正则表达式匹配标注符号
    # 支持 〖TYPE content〗 和 ⟦TYPE content⟧ 两种格式
    tag_pattern = re.compile(r'([〖⟦])([^〖〗⟦⟧])([^〗⟧]+?)([〗⟧])')

    # 记录修复详情
    changes = []

    def replacement_with_logging(match):
        original = match.group(0)
        fixed = fix_symbols_in_tag(match)
        if original != fixed:
            # 记录具体修改
            changes.append({
                'original': original,
                'fixed': fixed,
                'position': match.start()
            })
        return fixed

    # 执行替换
    fixed_content = tag_pattern.sub(replacement_with_logging, content)

    # 只在有变化时写入
    if fixed_content != original_content:
        file_path.write_text(fixed_content, encoding='utf-8')
        return len(changes), changes
    else:
        return 0, []


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
    total_tags_fixed = 0
    all_changes = []

    for file_path in tagged_files:
        fixed_count, changes = fix_file_tags(file_path)

        if fixed_count > 0:
            total_files_fixed += 1
            total_tags_fixed += fixed_count
            all_changes.extend([(file_path.name, c) for c in changes])

            print(f"\n✅ {file_path.name}")
            print(f"   修复 {fixed_count} 处标注内的全角符号")

            # 显示前3个修复示例
            for i, change in enumerate(changes[:3], 1):
                print(f"   [{i}] {change['original']}")
                print(f"       → {change['fixed']}")

            if len(changes) > 3:
                print(f"   ... 还有 {len(changes) - 3} 处")

    print("\n" + "=" * 60)
    print(f"📊 修复完成:")
    print(f"   - 修复文件数: {total_files_fixed}")
    print(f"   - 修复标注数: {total_tags_fixed}")

    # 统计修复类型
    if all_changes:
        print(f"\n📋 修复详情统计:")

        # 统计最常见的修复类型
        symbol_counts = {}
        for _, change in all_changes:
            orig = change['original']
            fixed = change['fixed']
            # 提取被替换的符号
            for fullwidth in '：，。；！？（）\u201c\u201d\u2018\u2019【】':
                if fullwidth in orig and fullwidth not in fixed:
                    symbol_counts[fullwidth] = symbol_counts.get(fullwidth, 0) + 1

        for symbol, count in sorted(symbol_counts.items(), key=lambda x: -x[1]):
            print(f"   - {symbol}: {count} 处")

    print(f"\n💡 建议:")
    print(f"   1. 运行验证: python scripts/lint_text_integrity.py")
    print(f"   2. 检查修改: git diff chapter_md/")
    print(f"   3. 如无误: git add chapter_md/*.tagged.md")


if __name__ == '__main__':
    main()
