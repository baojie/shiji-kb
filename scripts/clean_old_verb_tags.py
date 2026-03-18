#!/usr/bin/env python3
"""
旧格式动词标注清理脚本 v3.2

功能：
1. 迁移核心词表动词：〖[斩〗 → ⟦◉斩⟧
2. 删除日常动词标注：〖[得〗 → 得
3. 保留刑罚制度名词：〖[斩首〗（2字+）
4. 生成审核报告：扩展词表和未知动词需人工审核

用法：
  python scripts/clean_old_verb_tags.py --dry-run        # 预览
  python scripts/clean_old_verb_tags.py --execute       # 执行
  python scripts/clean_old_verb_tags.py --report        # 仅生成报告
"""

import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
CHAPTER_DIR = BASE_DIR / 'chapter_md'
REPORT_DIR = BASE_DIR / 'doc/predicate'

# v3.2核心词表
MILITARY_VERBS = {
    '伐', '攻', '击', '袭', '侵',  # 进攻5
    '战', '破', '败', '灭', '围', '下', '拔', '克', '屠', '射',  # 交战10
    '虏', '禽', '捕', '获',  # 俘获4
    '追', '逐',  # 追击2
    '救', '取', '定', '降', '走', '奔', '收'  # 机动7
}

PENALTY_VERBS = {
    '杀', '诛', '斩', '弑', '族', '戮', '刺', '夷', '阬', '烹', '亨', '僇', '劫',  # 处决13
    '废', '囚', '执', '笞', '刑',  # 处罚5
    '赦', '绝',  # 赦免2
    '反', '亡', '死'  # 其他3
}

POLITICAL_VERBS = {'封', '立'}

CORE_VERBS = MILITARY_VERBS | PENALTY_VERBS | POLITICAL_VERBS

# 日常动词（应删除标注）
COMMON_VERBS = {
    '得', '归', '留', '行', '告', '教', '出', '来', '入', '过',
    '失', '置', '葬', '视', '学', '见', '闻', '食', '饮',
    '知', '思', '想', '与', '予', '给', '受', '舍', '弃',
    '生', '老', '病', '望', '观', '看', '察', '审'
}


class VerbCleaner:
    """动词标注清理器"""

    def __init__(self, chapter_file):
        self.chapter_file = chapter_file
        self.chapter_num = chapter_file.stem[:3]
        self.original_text = chapter_file.read_text(encoding='utf-8')
        self.cleaned_text = self.original_text
        self.changes = {
            'migrated': [],  # 迁移到新格式
            'removed': [],   # 删除标注
            'kept': [],      # 保留（制度名词）
            'review': []     # 需要人工审核
        }

    def clean(self):
        """执行清理"""
        text = self.original_text

        # 处理所有〖[content〗格式
        pattern = r'〖\[([^〗]+)〗'

        def replace_tag(match):
            full_match = match.group(0)
            content = match.group(1)

            # 处理消歧说明
            if '|' in content:
                verb, disambig = content.split('|', 1)
                verb = verb.strip()
            else:
                verb = content.strip()
                disambig = None

            # 1. 保留刑罚制度名词（2字及以上）
            if len(verb) >= 2:
                self.changes['kept'].append({
                    'original': full_match,
                    'type': '刑罚制度名词',
                    'content': content
                })
                return full_match

            # 2. 迁移核心词表动词
            if verb in CORE_VERBS:
                if verb in MILITARY_VERBS:
                    new_tag = f'⟦◈{verb}⟧' if not disambig else f'⟦◈{verb}|{disambig}⟧'
                    verb_type = '军事'
                elif verb in PENALTY_VERBS:
                    new_tag = f'⟦◉{verb}⟧' if not disambig else f'⟦◉{verb}|{disambig}⟧'
                    verb_type = '刑罚'
                else:  # POLITICAL_VERBS
                    new_tag = f'⟦○{verb}⟧' if not disambig else f'⟦○{verb}|{disambig}⟧'
                    verb_type = '政治'

                self.changes['migrated'].append({
                    'original': full_match,
                    'new': new_tag,
                    'verb': verb,
                    'type': verb_type
                })
                return new_tag

            # 3. 删除日常动词标注
            if verb in COMMON_VERBS:
                self.changes['removed'].append({
                    'original': full_match,
                    'verb': verb,
                    'type': '日常动词'
                })
                return verb  # 只保留动词本身

            # 4. 其他动词标记为需要人工审核
            self.changes['review'].append({
                'original': full_match,
                'verb': verb,
                'type': '未知动词'
            })
            return full_match  # 暂时保留

        # 执行替换
        self.cleaned_text = re.sub(pattern, replace_tag, text)

        return self.changes

    def get_summary(self):
        """获取统计摘要"""
        return {
            'chapter': self.chapter_num,
            'migrated': len(self.changes['migrated']),
            'removed': len(self.changes['removed']),
            'kept': len(self.changes['kept']),
            'review': len(self.changes['review'])
        }

    def save(self):
        """保存清理后的文件"""
        self.chapter_file.write_text(self.cleaned_text, encoding='utf-8')


def process_all_chapters(dry_run=True):
    """处理所有章节"""
    results = []
    total_stats = Counter()

    for chapter_file in sorted(CHAPTER_DIR.glob("*.tagged.md")):
        cleaner = VerbCleaner(chapter_file)
        changes = cleaner.clean()
        summary = cleaner.get_summary()

        results.append({
            'cleaner': cleaner,
            'summary': summary,
            'changes': changes
        })

        for key in ['migrated', 'removed', 'kept', 'review']:
            total_stats[key] += summary[key]

        # 输出进度
        if summary['migrated'] + summary['removed'] + summary['review'] > 0:
            print(f"{summary['chapter']}: 迁移{summary['migrated']} 删除{summary['removed']} "
                  f"保留{summary['kept']} 审核{summary['review']}")

        # 保存（如果不是dry-run）
        if not dry_run:
            cleaner.save()

    return results, total_stats


def generate_report(results, total_stats):
    """生成清理报告"""
    report = []
    report.append("# 动词标注清理报告 v3.2\n")
    report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"**处理范围**: 001-130章（全部130章）\n\n")
    report.append("---\n\n")

    report.append("## 一、总体统计\n\n")
    report.append("| 操作类型 | 数量 | 说明 |\n")
    report.append("|---------|------|------|\n")
    report.append(f"| 迁移到新格式 | {total_stats['migrated']}处 | 核心词表动词 → ⟦TYPE动词⟧ |\n")
    report.append(f"| 删除标注 | {total_stats['removed']}处 | 日常动词 → 纯文本 |\n")
    report.append(f"| 保留不变 | {total_stats['kept']}处 | 刑罚制度名词（2字+） |\n")
    report.append(f"| 需要审核 | {total_stats['review']}处 | 扩展词表或未知动词 |\n\n")

    report.append("---\n\n")

    report.append("## 二、迁移详情\n\n")
    migrated_verbs = Counter()
    for result in results:
        for change in result['changes']['migrated']:
            migrated_verbs[change['verb']] += 1

    if migrated_verbs:
        report.append("| 动词 | 频次 | 类型 |\n")
        report.append("|-----|------|------|\n")
        for verb, count in migrated_verbs.most_common():
            verb_type = "◈军事" if verb in MILITARY_VERBS else "◉刑罚" if verb in PENALTY_VERBS else "○政治"
            report.append(f"| {verb} | {count}处 | {verb_type} |\n")
    else:
        report.append("无需迁移的核心词表动词。\n")

    report.append("\n---\n\n")

    report.append("## 三、删除详情\n\n")
    removed_verbs = Counter()
    for result in results:
        for change in result['changes']['removed']:
            removed_verbs[change['verb']] += 1

    if removed_verbs:
        report.append("| 动词 | 频次 | 原因 |\n")
        report.append("|-----|------|------|\n")
        for verb, count in removed_verbs.most_common(20):
            report.append(f"| {verb} | {count}处 | 日常动词，不符合标注范围 |\n")
    else:
        report.append("无日常动词需要删除。\n")

    report.append("\n---\n\n")

    report.append("## 四、需要人工审核的动词\n\n")
    review_verbs = Counter()
    for result in results:
        for change in result['changes']['review']:
            review_verbs[change['verb']] += 1

    if review_verbs:
        report.append(f"共{len(review_verbs)}个动词，{total_stats['review']}处标注需要人工审核。\n\n")
        report.append("| 动词 | 频次 | 建议 |\n")
        report.append("|-----|------|------|\n")
        for verb, count in review_verbs.most_common(30):
            report.append(f"| {verb} | {count}处 | 判断是否为历史事件核心动词 |\n")
    else:
        report.append("无需审核的动词。\n")

    return '\n'.join(report)


def main():
    parser = argparse.ArgumentParser(description='旧格式动词标注清理工具 v3.2')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改文件')
    parser.add_argument('--execute', action='store_true', help='执行清理')
    parser.add_argument('--report', action='store_true', help='仅生成报告')

    args = parser.parse_args()

    if not any([args.dry_run, args.execute, args.report]):
        args.dry_run = True  # 默认预览模式

    print("\n" + "="*80)
    print("动词标注清理工具 v3.2")
    print("="*80 + "\n")

    mode = "预览模式" if args.dry_run else "执行模式" if args.execute else "报告模式"
    print(f"运行模式: {mode}\n")

    # 处理所有章节
    results, total_stats = process_all_chapters(dry_run=args.dry_run or args.report)

    # 生成报告
    report_content = generate_report(results, total_stats)

    # 保存报告
    REPORT_DIR.mkdir(exist_ok=True, parents=True)
    report_file = REPORT_DIR / f"动词标注清理报告_v3.2_{datetime.now().strftime('%Y%m%d')}.md"
    report_file.write_text(report_content, encoding='utf-8')

    print(f"\n{'='*80}")
    print("清理完成")
    print(f"{'='*80}")
    print(f"迁移: {total_stats['migrated']}处")
    print(f"删除: {total_stats['removed']}处")
    print(f"保留: {total_stats['kept']}处")
    print(f"审核: {total_stats['review']}处")
    print(f"\n报告已保存: {report_file}")
    print(f"{'='*80}\n")

    if args.dry_run:
        print("💡 这是预览模式。使用 --execute 执行实际清理。")


if __name__ == "__main__":
    main()
