#!/usr/bin/env python3
"""
修复动词标注嵌套问题

自动修复常见的嵌套错误:
1. 战国: 〖'⟦◈战⟧国〗 → 〖'战国〗
2. 人名破奴: 〖@⟦◈破⟧奴〗 → 〖@破奴〗
3. 官职游击将军: 〖;游⟦◈击⟧将军〗 → 〖;游击将军〗
4. 地名取虑: 〖=⟦◈取⟧虑〗 → 〖=取虑〗
5. 其他特定名词

用法:
  python fix_verb_nesting.py --dry-run          # 预览修复
  python fix_verb_nesting.py --all              # 修复所有章节
  python fix_verb_nesting.py --chapter 110      # 修复指定章节
"""

import re
import sys
import argparse
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHAPTER_DIR = BASE_DIR / 'chapter_md'

# 需要修复的模式
FIX_PATTERNS = [
    # (错误模式, 正确替换, 说明)
    (r'〖\'⟦◈战⟧国〗', r'〖\'战国〗', '战国是朝代名'),
    (r'〖%⟦◈战⟧国〗', r'〖%战国〗', '战国是时期名'),
    (r'〖@⟦◈破⟧奴〗', r'〖@破奴〗', '破奴是人名'),
    (r'〖@⟦◈破⟧石〗', r'〖@破石〗', '破石是人名'),
    (r'〖@赵⟦◈破⟧奴〗', r'〖@赵破奴〗', '赵破奴是人名'),
    (r'〖;将军赵⟦◈破⟧奴〗', r'〖;将军赵破奴〗', '将军赵破奴是官职+人名'),
    (r'〖;从骠侯⟦◈破⟧奴〗', r'〖;从骠侯破奴〗', '从骠侯破奴是官职+人名'),
    (r'〖;游⟦◈击⟧将军〗', r'〖;游击将军〗', '游击将军是官职名'),
    (r'〖;鹰⟦◈击⟧司〖~马〗', r'〖;鹰击司马〗', '鹰击司马是官职名'),
    (r'〖;益州⟦◉刺⟧史〗', r'〖;益州刺史〗', '益州刺史是官职名'),
    (r'〖=⟦◈取⟧虑〗', r'〖=取虑〗', '取虑是地名'),
    (r'〖{⟦◈伐⟧檀〗', r'〖{伐檀〗', '伐檀是诗经篇名'),
    (r'〖@武王⟦◈克⟧纣〗', r'〖@武王克纣〗', '武王克纣是人名+事件'),
]


def fix_chapter(chapter_file, dry_run=False):
    """修复单个章节"""
    with open(chapter_file, 'r', encoding='utf-8') as f:
        original_content = f.read()

    fixed_content = original_content
    fixes_made = Counter()

    # 应用所有修复模式
    for pattern, replacement, description in FIX_PATTERNS:
        matches = list(re.finditer(pattern, fixed_content))
        if matches:
            fixes_made[description] += len(matches)
            fixed_content = re.sub(pattern, replacement, fixed_content)

    # 统计结果
    result = {
        'chapter': chapter_file.stem,
        'fixes': dict(fixes_made),
        'total_fixes': sum(fixes_made.values()),
        'changed': fixed_content != original_content
    }

    # 写入文件
    if not dry_run and result['changed']:
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        result['status'] = '✅ 已修复'
    elif result['changed']:
        result['status'] = '📋 待修复'
    else:
        result['status'] = '✓ 无需修复'

    return result


def main():
    parser = argparse.ArgumentParser(description='修复动词标注嵌套问题')
    parser.add_argument('--chapter', type=int, metavar='NNN',
                        help='修复指定章节（如 110）')
    parser.add_argument('--all', action='store_true',
                        help='修复所有章节')
    parser.add_argument('--dry-run', action='store_true',
                        help='预览模式，不实际修改文件')

    args = parser.parse_args()

    # 收集章节
    if args.chapter:
        chapter_files = list(CHAPTER_DIR.glob(f'{args.chapter:03d}_*.tagged.md'))
        if not chapter_files:
            print(f"错误: 未找到章节 {args.chapter:03d}")
            sys.exit(1)
    elif args.all:
        chapter_files = sorted(CHAPTER_DIR.glob('*.tagged.md'))
    else:
        print("请指定 --chapter NNN 或 --all")
        sys.exit(1)

    # 执行修复
    mode_str = "预览" if args.dry_run else "修复"
    print(f"\n正在{mode_str} {len(chapter_files)} 个章节...")
    print()

    results = []
    total_fixes = 0

    for chapter_file in chapter_files:
        result = fix_chapter(chapter_file, args.dry_run)
        results.append(result)

        if result['total_fixes'] > 0:
            print(f"{result['status']} {result['chapter']}: {result['total_fixes']} 处修复")
            for desc, count in result['fixes'].items():
                print(f"   - {desc}: {count} 处")
            total_fixes += result['total_fixes']

    # 总结
    print()
    print("=" * 70)
    print(f"总计: {total_fixes} 处修复")

    fixed_chapters = sum(1 for r in results if r['changed'])
    print(f"涉及章节: {fixed_chapters}/{len(chapter_files)}")

    if args.dry_run and total_fixes > 0:
        print()
        print("💡 预览完成。移除 --dry-run 参数以执行实际修复。")
    elif total_fixes > 0:
        print()
        print("✅ 修复完成！建议再次运行 lint_verb_tagging.py 验证。")
    else:
        print()
        print("✅ 所有章节都没有嵌套问题！")

    print("=" * 70)


if __name__ == '__main__':
    main()
