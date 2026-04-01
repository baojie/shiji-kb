#!/usr/bin/env python3
"""
修复嵌套标注

将嵌套的标注拍平为正确的形式。

常见模式：
1. 〖#〖#父〗子〗 → 〖#父子〗（父子、夫妇等复合词）
2. 〖;〖#夫〗人〗 → 〖;夫人〗（官职+人物类型）
3. 〖@司〖~马〗季主〗 → 〖@司马季主〗（人名+复姓）
4. 〖•〖~玉〗床〗 → 〖•玉床〗（物品+材质）
"""

import re
from pathlib import Path
from collections import defaultdict


def fix_nested_annotations(text: str) -> tuple[str, int, dict]:
    """
    修复文本中的嵌套标注

    Returns:
        (修复后的文本, 修复数量, 修复模式统计)
    """
    fixed_count = 0
    pattern_stats = defaultdict(int)

    # 模式1: 处理最常见的嵌套模式
    # 〖TYPE1 〖TYPE2 content2〗 content1〗 → 根据具体情况处理

    # 正则说明：
    # 〖 - 左标注符
    # ([#@=;$%&\'^~•!\'+?{:\[_]) - TYPE1（外层类型标记）
    # ([^〗]*?) - 外层前缀内容（非贪婪）
    # 〖 - 内层左标注符
    # ([#@=;$%&\'^~•!\'+?{:\[_]) - TYPE2（内层类型标记）
    # ([^〗]*?) - 内层内容
    # 〗 - 内层右标注符
    # ([^〗]*?) - 外层后缀内容
    # 〗 - 外层右标注符

    pattern = r'〖([#@=;$%&\'^~•!\'+?{:\[_])([^〗]*?)〖([#@=;$%&\'^~•!\'+?{:\[_])([^〗]*?)〗([^〗]*?)〗'

    def replace_func(match):
        nonlocal fixed_count, pattern_stats

        type1 = match.group(1)  # 外层类型
        prefix = match.group(2)  # 外层前缀
        type2 = match.group(3)  # 内层类型
        inner = match.group(4)  # 内层内容
        suffix = match.group(5)  # 外层后缀

        # 统计模式
        pattern_key = f'〖{type1}〖{type2}〗〗'
        pattern_stats[pattern_key] += 1
        fixed_count += 1

        # 规则1: 如果外层没有前缀和后缀，只有内层标注，则保留外层类型
        # 例如：〖^〖_仁义〗〗 → 〖^仁义〗（取外层类型）
        if not prefix and not suffix:
            return f'〖{type1}{inner}〗'

        # 规则2: 如果外层有前缀或后缀，将内层内容合并到外层
        # 例如：〖@司〖~马〗季主〗 → 〖@司马季主〗
        # 例如：〖;华阳〖#夫〗人〗 → 〖;华阳夫人〗
        combined_content = prefix + inner + suffix
        return f'〖{type1}{combined_content}〗'

    # 多次替换，直到没有嵌套为止（处理多层嵌套）
    max_iterations = 10
    for _ in range(max_iterations):
        new_text = re.sub(pattern, replace_func, text)
        if new_text == text:
            break
        text = new_text

    return text, fixed_count, dict(pattern_stats)


def fix_file(file_path: Path) -> tuple[int, dict]:
    """
    修复单个文件中的嵌套标注

    Returns:
        (修复数量, 修复模式统计)
    """
    content = file_path.read_text(encoding='utf-8')
    new_content, fixed_count, pattern_stats = fix_nested_annotations(content)

    # 只在有变化时写入
    if new_content != content:
        file_path.write_text(new_content, encoding='utf-8')

    return fixed_count, pattern_stats


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
    total_fixed = 0
    total_pattern_stats = defaultdict(int)

    for file_path in tagged_files:
        fixed_count, pattern_stats = fix_file(file_path)

        if fixed_count > 0:
            total_files_fixed += 1
            total_fixed += fixed_count

            for pattern, count in pattern_stats.items():
                total_pattern_stats[pattern] += count

            print(f"\n✅ {file_path.name}")
            print(f"   修复 {fixed_count} 处嵌套标注")

            # 显示前3个最常见的模式
            top_patterns = sorted(pattern_stats.items(), key=lambda x: x[1], reverse=True)[:3]
            for pattern, count in top_patterns:
                print(f"   - {pattern}: {count}处")

    print("\n" + "=" * 60)
    print(f"📊 修复完成:")
    print(f"   - 修复文件数: {total_files_fixed}")
    print(f"   - 修复总数: {total_fixed}")

    print(f"\n📈 嵌套模式统计（Top 10）:")
    top_patterns = sorted(total_pattern_stats.items(), key=lambda x: x[1], reverse=True)[:10]
    for pattern, count in top_patterns:
        print(f"   - {pattern}: {count}处")

    print(f"\n💡 建议:")
    print(f"   1. 运行验证脚本: python scripts/lint_symbol_conflicts.py chapter_md/*.tagged.md --check-types nested")
    print(f"   2. 使用 git diff 检查修改是否正确")
    print(f"   3. 如无误，使用 git add 暂存变更")


if __name__ == '__main__':
    main()
