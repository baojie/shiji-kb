#!/usr/bin/env python3
"""
修复Markdown容器语法标记：将 ：：： 改回 :::

问题：fix_all_halfwidth_symbols.py 将Markdown容器语法的 ::: 错误替换为 ：：：

Markdown容器语法：
:::
这是一个特殊块
:::

用途：用于创建提示框、警告框、折叠块等特殊容器
"""

from pathlib import Path


def fix_triple_colon(content: str) -> tuple[str, int]:
    """
    将行首的全角三冒号 ：：： 替换为半角 :::

    支持以下格式：
    - ：：：               (独立成行)
    - ：：： 标题文字      (容器标题)

    Args:
        content: 文件内容

    Returns:
        (修复后的内容, 修复数量)
    """
    lines = content.split('\n')
    fixed_count = 0
    new_lines = []

    for line in lines:
        stripped = line.strip()
        # 检查是否以全角三冒号开头（独立或带标题）
        if stripped.startswith('：：：'):
            # 替换行首的全角三冒号
            new_line = line.replace('：：：', ':::', 1)  # 只替换第一次出现
            new_lines.append(new_line)
            fixed_count += 1
        else:
            new_lines.append(line)

    return '\n'.join(new_lines), fixed_count


def fix_file(file_path: Path) -> int:
    """
    修复单个文件中的全角三冒号

    Returns:
        修复数量
    """
    content = file_path.read_text(encoding='utf-8')
    new_content, fixed_count = fix_triple_colon(content)

    # 只在有变化时写入
    if fixed_count > 0:
        file_path.write_text(new_content, encoding='utf-8')

    return fixed_count


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

    for file_path in tagged_files:
        fixed_count = fix_file(file_path)

        if fixed_count > 0:
            total_files_fixed += 1
            total_fixed += fixed_count
            print(f"✅ {file_path.name}: 修复 {fixed_count} 处")

    print("\n" + "=" * 60)
    print(f"📊 修复完成:")
    print(f"   - 修复文件数: {total_files_fixed}")
    print(f"   - 修复总数: {total_fixed}")
    print(f"\n💡 建议:")
    print(f"   1. 检查修改: git diff chapter_md/")
    print(f"   2. 如无误: git add chapter_md/*.tagged.md")


if __name__ == '__main__':
    main()
