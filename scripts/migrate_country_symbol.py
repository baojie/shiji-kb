#!/usr/bin/env python3
"""
邦国标注符号迁移脚本：〖' → 〖◆

将所有章节中的邦国标注符号从半角单引号 ' (U+0027) 替换为黑菱形 ◆ (U+25C6)

用法：
    python scripts/migrate_country_symbol.py --test 037 038    # 测试模式，只处理指定章节
    python scripts/migrate_country_symbol.py --dry-run         # 预览所有更改
    python scripts/migrate_country_symbol.py                   # 执行替换
"""

import argparse
import sys
from pathlib import Path


def migrate_country_symbol(content: str) -> tuple[str, int]:
    """
    替换邦国标注符号：〖' → 〖◆

    Args:
        content: 文件内容

    Returns:
        (新内容, 替换数量)
    """
    # 旧符号：〖' (〖 + 半角单引号)
    old_marker = '〖' + chr(0x0027)  # 〖'

    # 新符号：〖◆ (〖 + 黑菱形)
    new_marker = '〖' + chr(0x25C6)  # 〖◆

    # 统计替换数量
    count = content.count(old_marker)

    # 执行替换
    new_content = content.replace(old_marker, new_marker)

    return new_content, count


def process_file(file_path: Path, dry_run: bool = False) -> dict:
    """
    处理单个文件

    Returns:
        处理结果字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    new_content, count = migrate_country_symbol(original_content)

    result = {
        'file': file_path.name,
        'count': count,
        'changed': count > 0
    }

    # 非dry-run模式且有更改时写入文件
    if not dry_run and count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        result['written'] = True
    else:
        result['written'] = False

    return result


def get_chapter_files(chapter_md_dir: Path, test_chapters: list = None) -> list[Path]:
    """
    获取要处理的章节文件

    Args:
        chapter_md_dir: chapter_md 目录
        test_chapters: 测试模式的章节号列表（如 [37, 38]）

    Returns:
        文件路径列表
    """
    if test_chapters:
        files = []
        for chapter_num in test_chapters:
            pattern = f"{chapter_num:03d}_*.tagged.md"
            matches = list(chapter_md_dir.glob(pattern))
            if matches:
                files.extend(matches)
            else:
                print(f"⚠️  未找到章节 {chapter_num:03d}")
        return sorted(files)
    else:
        return sorted(chapter_md_dir.glob('*.tagged.md'))


def main():
    parser = argparse.ArgumentParser(
        description='邦国标注符号迁移：〖\' → 〖◆',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --test 037 038           # 测试模式：只处理037和038章
  %(prog)s --dry-run                # 预览所有更改，不实际修改文件
  %(prog)s                          # 执行替换所有章节
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式：显示更改但不写入文件'
    )
    parser.add_argument(
        '--test',
        nargs='*',
        metavar='CHAPTER',
        help='测试模式：只处理指定章节（如 037 038 039）'
    )

    args = parser.parse_args()

    # 获取文件列表
    chapter_md_dir = Path(__file__).parent.parent / 'chapter_md'

    if not chapter_md_dir.exists():
        print(f"❌ 目录不存在: {chapter_md_dir}")
        sys.exit(1)

    # 解析测试章节
    test_chapters = None
    if args.test is not None:
        if len(args.test) == 0:
            print("❌ --test 需要指定章节号")
            sys.exit(1)
        try:
            test_chapters = [int(c) for c in args.test]
        except ValueError:
            print("❌ 章节号必须是数字")
            sys.exit(1)

    files = get_chapter_files(chapter_md_dir, test_chapters)

    if not files:
        print("❌ 未找到任何匹配的 .tagged.md 文件")
        sys.exit(1)

    # 显示模式
    mode_str = "预览模式" if args.dry_run else ("测试模式" if test_chapters else "执行模式")
    print(f"📁 {mode_str}")
    if test_chapters:
        print(f"   测试章节: {', '.join(f'{n:03d}' for n in test_chapters)}")
    print(f"   找到 {len(files)} 个文件")
    print("=" * 60)

    # 处理文件
    results = []
    total_count = 0

    for file_path in files:
        result = process_file(file_path, dry_run=args.dry_run)
        results.append(result)

        if result['count'] > 0:
            total_count += result['count']
            status = "预览" if args.dry_run else ("✅ 已替换" if result['written'] else "跳过")
            print(f"{status}: {result['file']}")
            print(f"         替换 {result['count']} 处 〖' → 〖◆")

    # 统计
    changed_count = sum(1 for r in results if r['changed'])

    print("\n" + "=" * 60)
    print(f"📊 统计:")
    print(f"   - 处理文件数: {len(results)}")
    print(f"   - 有更改文件: {changed_count}")
    print(f"   - 替换总数: {total_count}")

    if args.dry_run:
        print(f"\n💡 这是预览模式，未实际修改文件")
        print(f"   移除 --dry-run 参数以执行替换")
    elif test_chapters:
        print(f"\n💡 这是测试模式，只处理了指定章节")
        print(f"   移除 --test 参数以处理所有章节")
    elif total_count > 0:
        print(f"\n✅ 替换完成！")
        print(f"\n💡 建议:")
        print(f"   1. 运行验证: python scripts/lint_text_integrity.py")
        print(f"   2. 检查差异: git diff chapter_md/*.tagged.md | head -100")
        print(f"   3. 如无误，提交: git add chapter_md/*.tagged.md && git commit")
    else:
        print(f"\n✅ 所有文件都已使用新符号，无需替换")


if __name__ == '__main__':
    main()
