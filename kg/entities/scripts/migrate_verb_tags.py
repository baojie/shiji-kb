#!/usr/bin/env python3
"""
动词标注迁移脚本

功能：将旧格式〖[verb〗迁移到新格式⟦TYPE动词⟧

迁移规则：
1. 军事动词(17个): 〖[伐〗 → ⟦◈伐⟧
2. 刑罚动词(15个): 〖[杀〗 → ⟦◉杀⟧
3. 刑罚制度名词(2字+): 〖[斩首〗 保持不变

用法：
  python migrate_verb_tags.py --dry-run                    # 预览迁移
  python migrate_verb_tags.py --chapter 040                # 迁移040章
  python migrate_verb_tags.py --all                        # 迁移所有章节
  python migrate_verb_tags.py --all --backup               # 迁移前备份
  python migrate_verb_tags.py --type military              # 仅迁移军事动词
  python migrate_verb_tags.py --type penalty               # 仅迁移刑罚动词
"""

import re
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHAPTER_DIR = BASE_DIR / 'chapter_md'
BACKUP_DIR = BASE_DIR / 'backups' / f'verb_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

# 导入词表
from query_verbs_by_type import (
    MILITARY_VERBS, PENALTY_VERBS, PENALTY_NOUNS
)


def backup_file(file_path):
    """备份文件"""
    backup_path = BACKUP_DIR / file_path.name
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, backup_path)
    return backup_path


def migrate_verbs(text, verb_type='all'):
    """
    迁移动词标注

    Args:
        text: 原文本
        verb_type: 'military', 'penalty', 'all'

    Returns:
        (migrated_text, changes_dict)
    """
    changes = {
        'military': [],
        'penalty': [],
        'unchanged': []
    }

    # 查找所有旧格式〖[content〗
    pattern = r'〖\[([^〗]+)〗'

    def replace_verb(match):
        full_match = match.group(0)
        content = match.group(1)

        # 处理消歧说明
        if '|' in content:
            verb, disambig = content.split('|', 1)
            verb = verb.strip()
            disambig = disambig.strip()
        else:
            verb = content.strip()
            disambig = None

        # 判断动词类型
        if verb in MILITARY_VERBS and verb_type in ['military', 'all']:
            # 军事动词
            new_tag = f'⟦◈{verb}⟧' if not disambig else f'⟦◈{verb}|{disambig}⟧'
            changes['military'].append({
                'old': full_match,
                'new': new_tag,
                'verb': verb
            })
            return new_tag

        elif verb in PENALTY_VERBS and verb_type in ['penalty', 'all']:
            # 刑罚动词
            new_tag = f'⟦◉{verb}⟧' if not disambig else f'⟦◉{verb}|{disambig}⟧'
            changes['penalty'].append({
                'old': full_match,
                'new': new_tag,
                'verb': verb
            })
            return new_tag

        else:
            # 刑罚制度名词或其他，保持不变
            changes['unchanged'].append({
                'tag': full_match,
                'content': content,
                'reason': '刑罚制度名词或未分类' if len(verb) >= 2 else '未分类单字'
            })
            return full_match

    # 执行替换
    migrated_text = re.sub(pattern, replace_verb, text)

    return migrated_text, changes


def migrate_chapter(chapter_file, verb_type='all', dry_run=False, backup=True):
    """迁移单个章节"""

    with open(chapter_file, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # 执行迁移
    migrated_text, changes = migrate_verbs(original_text, verb_type)

    # 统计变化
    total_changes = len(changes['military']) + len(changes['penalty'])

    result = {
        'chapter': chapter_file.stem,
        'changes': changes,
        'total_changes': total_changes,
        'unchanged': len(changes['unchanged']),
        'success': False
    }

    if total_changes == 0:
        result['message'] = '无需迁移'
        return result

    if dry_run:
        result['message'] = f'预览：{total_changes}处变更'
        return result

    # 备份
    if backup:
        backup_path = backup_file(chapter_file)
        result['backup'] = str(backup_path)

    # 写入新内容
    try:
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(migrated_text)
        result['success'] = True
        result['message'] = f'成功迁移{total_changes}处'
    except Exception as e:
        result['message'] = f'写入失败: {e}'

    return result


def generate_migration_report(results, output_file=None):
    """生成迁移报告"""
    report_lines = []

    report_lines.append("=" * 70)
    report_lines.append("动词标注迁移报告")
    report_lines.append("=" * 70)
    report_lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 统计总体情况
    total_chapters = len(results)
    success_chapters = sum(1 for r in results if r['success'])
    total_military = sum(len(r['changes']['military']) for r in results)
    total_penalty = sum(len(r['changes']['penalty']) for r in results)
    total_unchanged = sum(r['unchanged'] for r in results)

    report_lines.append(f"\n## 总体统计\n")
    report_lines.append(f"处理章节数: {total_chapters}")
    report_lines.append(f"成功迁移: {success_chapters}")
    report_lines.append(f"军事动词: {total_military} 处")
    report_lines.append(f"刑罚动词: {total_penalty} 处")
    report_lines.append(f"保持不变: {total_unchanged} 处")
    report_lines.append(f"总迁移数: {total_military + total_penalty} 处")

    # 词频统计
    military_counter = Counter()
    penalty_counter = Counter()

    for result in results:
        for change in result['changes']['military']:
            military_counter[change['verb']] += 1
        for change in result['changes']['penalty']:
            penalty_counter[change['verb']] += 1

    if military_counter:
        report_lines.append(f"\n## 军事动词迁移统计\n")
        report_lines.append(f"{'动词':<8} {'迁移次数':>10} {'新格式':<15}")
        report_lines.append("-" * 40)
        for verb, count in military_counter.most_common():
            report_lines.append(f"{verb:<8} {count:>10} ⟦◈{verb}⟧")
        report_lines.append(f"\n小计: {sum(military_counter.values())} 处")

    if penalty_counter:
        report_lines.append(f"\n## 刑罚动词迁移统计\n")
        report_lines.append(f"{'动词':<8} {'迁移次数':>10} {'新格式':<15}")
        report_lines.append("-" * 40)
        for verb, count in penalty_counter.most_common():
            report_lines.append(f"{verb:<8} {count:>10} ⟦◉{verb}⟧")
        report_lines.append(f"\n小计: {sum(penalty_counter.values())} 处")

    # 章节详情（显示有变更的前20章）
    changed_results = [r for r in results if r['total_changes'] > 0]
    changed_results.sort(key=lambda x: x['total_changes'], reverse=True)

    if changed_results:
        report_lines.append(f"\n## 章节迁移详情 (Top 20)\n")
        report_lines.append(f"{'章节':<35} {'军事':>6} {'刑罚':>6} {'总计':>6} {'状态':<10}")
        report_lines.append("-" * 70)

        for result in changed_results[:20]:
            chapter = result['chapter']
            mil_count = len(result['changes']['military'])
            pen_count = len(result['changes']['penalty'])
            total = result['total_changes']
            status = '✅ 成功' if result['success'] else '❌ 失败'

            report_lines.append(f"{chapter:<35} {mil_count:>6} {pen_count:>6} {total:>6} {status:<10}")

    # 保持不变的内容统计
    unchanged_samples = []
    for result in results[:5]:  # 只取前5章的样本
        unchanged_samples.extend(result['changes']['unchanged'][:3])

    if unchanged_samples:
        report_lines.append(f"\n## 保持不变的标注示例\n")
        for i, item in enumerate(unchanged_samples[:10], 1):
            report_lines.append(f"{i}. {item['tag']} - {item['reason']}")

    # 备份信息
    if results and results[0].get('backup'):
        report_lines.append(f"\n## 备份信息\n")
        report_lines.append(f"备份目录: {BACKUP_DIR}")
        report_lines.append(f"备份文件数: {success_chapters}")

    report_lines.append("\n" + "=" * 70)
    report_lines.append("迁移完成")
    report_lines.append("=" * 70)

    # 输出报告
    report_text = '\n'.join(report_lines)

    if output_file:
        output_path = BASE_DIR / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"\n迁移报告已保存到: {output_path}")

    print(report_text)


def main():
    parser = argparse.ArgumentParser(description='动词标注迁移工具')
    parser.add_argument('--chapter', type=int, metavar='NNN',
                        help='迁移指定章节（如 040）')
    parser.add_argument('--all', action='store_true',
                        help='迁移所有章节')
    parser.add_argument('--type', choices=['military', 'penalty', 'all'],
                        default='all',
                        help='迁移类型（默认: all）')
    parser.add_argument('--dry-run', action='store_true',
                        help='预览模式，不实际修改文件')
    parser.add_argument('--backup', action='store_true', default=True,
                        help='迁移前备份文件（默认开启）')
    parser.add_argument('--no-backup', dest='backup', action='store_false',
                        help='不备份文件')
    parser.add_argument('--report', metavar='FILE',
                        help='生成报告并保存到文件')

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

    # 确认操作
    if not args.dry_run and args.all:
        print(f"\n⚠️  即将迁移 {len(chapter_files)} 个章节的动词标注")
        print(f"类型: {args.type}")
        print(f"备份: {'是' if args.backup else '否'}")

        confirm = input("\n确认继续? (yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消")
            sys.exit(0)

    # 执行迁移
    mode_str = "预览" if args.dry_run else "迁移"
    print(f"\n正在{mode_str} {len(chapter_files)} 个章节...")

    results = []
    for i, chapter_file in enumerate(chapter_files, 1):
        result = migrate_chapter(chapter_file, args.type, args.dry_run, args.backup)
        results.append(result)

        if result['total_changes'] > 0:
            status = "📋" if args.dry_run else ("✅" if result['success'] else "❌")
            print(f"{status} [{i}/{len(chapter_files)}] {result['chapter']}: {result['message']}")

    # 生成报告
    print("\n")
    generate_migration_report(results, args.report)

    # 提示下一步
    if args.dry_run:
        print("\n💡 预览完成。移除 --dry-run 参数以执行实际迁移。")
    elif args.backup:
        print(f"\n💾 原文件已备份到: {BACKUP_DIR}")
        print("   如需回滚，请从备份目录复制回来。")


if __name__ == '__main__':
    main()
