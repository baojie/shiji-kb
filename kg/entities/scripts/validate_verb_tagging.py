#!/usr/bin/env python3
"""
动词标注验证工具

功能：
1. 检查未分类的〖[〗标注
2. 发现可能的标注错误
3. 生成质量报告
4. 建议需要迁移的动词

用法：
  python validate_verb_tagging.py                           # 验证所有章节
  python validate_verb_tagging.py --chapter 040             # 验证指定章节
  python validate_verb_tagging.py --strict                  # 严格模式
  python validate_verb_tagging.py --report output.md        # 生成报告
"""

import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHAPTER_DIR = BASE_DIR / 'chapter_md'

# 导入词表
from query_verbs_by_type import (
    MILITARY_VERBS, PENALTY_VERBS, PENALTY_NOUNS, ALL_VERBS
)


def validate_chapter(chapter_file, strict=False):
    """验证单个章节的动词标注"""
    with open(chapter_file, 'r', encoding='utf-8') as f:
        text = f.read()

    issues = {
        'unclassified': [],  # 未分类的〖[〗
        'misplaced_noun': [],  # 误标为动词的名词
        'mixed_format': [],  # 混用新旧格式
        'missing_disambig': []  # 缺少消歧说明的歧义词
    }

    # 检查旧格式〖[〗
    pattern_old = r'〖\[([^〗]+)〗'
    for match in re.finditer(pattern_old, text):
        full_match = match.group(0)
        content = match.group(1)
        verb = content.split('|')[0].strip()

        # 检查是否已分类
        if verb not in ALL_VERBS and verb not in PENALTY_NOUNS:
            # 单字且不在词表中
            if len(verb) == 1:
                issues['unclassified'].append({
                    'tag': full_match,
                    'verb': verb,
                    'context': text[max(0, match.start()-20):match.end()+20]
                })
            # 多字但不在刑罚名词表中（可能是新词）
            elif len(verb) >= 2 and strict:
                issues['unclassified'].append({
                    'tag': full_match,
                    'verb': verb,
                    'context': text[max(0, match.start()-20):match.end()+20]
                })

        # 检查是否误标（名词标注为单字）
        if len(verb) >= 2 and verb in PENALTY_NOUNS:
            # 这是正确的刑罚名词
            pass
        elif len(verb) >= 2 and verb not in PENALTY_NOUNS:
            # 可能的新刑罚名词，或者误标
            if strict and any(c in verb for c in ['之', '于', '於', '以', '而']):
                # 包含虚词，可能误标
                issues['misplaced_noun'].append({
                    'tag': full_match,
                    'content': verb,
                    'reason': '包含虚词，可能不是刑罚名词'
                })

    # 检查新格式⟦TYPE动词⟧
    pattern_new = r'⟦([◈◉○◇])([^⟧|]+)(?:\|[^⟧]+)?⟧'
    new_verbs_count = len(re.findall(pattern_new, text))

    if new_verbs_count > 0:
        # 存在新格式，检查是否混用
        old_verb_count = len([m for m in re.finditer(pattern_old, text)
                             if re.match(pattern_old, m.group(0))])
        if old_verb_count > 0:
            issues['mixed_format'].append({
                'old_count': old_verb_count,
                'new_count': new_verbs_count
            })

    # 检查需要消歧的词（在strict模式下）
    if strict:
        ambiguous_verbs = {'取', '下', '定', '走', '反', '亡', '死'}
        for verb in ambiguous_verbs:
            pattern = rf'〖\[{verb}〗'
            for match in re.finditer(pattern, text):
                # 没有消歧说明
                issues['missing_disambig'].append({
                    'tag': match.group(0),
                    'verb': verb,
                    'context': text[max(0, match.start()-20):match.end()+20]
                })

    return {
        'chapter': chapter_file.stem,
        'issues': issues,
        'total_issues': sum(len(v) for v in issues.values())
    }


def generate_validation_report(results, output_file=None):
    """生成验证报告"""
    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append("动词标注验证报告")
    report_lines.append("=" * 60)

    # 统计总体情况
    total_chapters = len(results)
    chapters_with_issues = sum(1 for r in results if r['total_issues'] > 0)
    total_issues = sum(r['total_issues'] for r in results)

    report_lines.append(f"\n总体统计:")
    report_lines.append(f"  验证章节数: {total_chapters}")
    report_lines.append(f"  有问题章节: {chapters_with_issues}")
    report_lines.append(f"  问题总数: {total_issues}")

    # 问题类型统计
    unclassified_count = sum(len(r['issues']['unclassified']) for r in results)
    misplaced_count = sum(len(r['issues']['misplaced_noun']) for r in results)
    mixed_count = sum(len(r['issues']['mixed_format']) for r in results)
    disambig_count = sum(len(r['issues']['missing_disambig']) for r in results)

    report_lines.append(f"\n问题类型分布:")
    report_lines.append(f"  未分类词汇: {unclassified_count}")
    report_lines.append(f"  误标名词: {misplaced_count}")
    report_lines.append(f"  格式混用: {mixed_count}")
    report_lines.append(f"  缺少消歧: {disambig_count}")

    # 收集所有未分类词汇
    unclassified_verbs = Counter()
    for result in results:
        for issue in result['issues']['unclassified']:
            unclassified_verbs[issue['verb']] += 1

    if unclassified_verbs:
        report_lines.append(f"\n未分类词汇Top 20:")
        report_lines.append(f"{'词汇':<10} {'频次':>8} {'建议分类':<15}")
        report_lines.append("-" * 40)

        for verb, count in unclassified_verbs.most_common(20):
            # 简单判断可能的分类
            suggestion = "待人工审核"
            if verb in ['虏', '禽', '执', '捕', '擒']:
                suggestion = "军事动词（俘获类）"
            elif verb in ['封', '立', '废', '黜', '放']:
                suggestion = "政治动词"
            elif verb in ['赐', '赂', '贿', '献', '贡']:
                suggestion = "经济动词"

            report_lines.append(f"{verb:<10} {count:>8} {suggestion:<15}")

    # 详细问题列表（仅显示前10个有问题的章节）
    report_lines.append(f"\n问题章节详情（前10个）:")
    report_lines.append("-" * 60)

    problem_chapters = [r for r in results if r['total_issues'] > 0]
    problem_chapters.sort(key=lambda x: x['total_issues'], reverse=True)

    for result in problem_chapters[:10]:
        chapter = result['chapter']
        issues = result['issues']
        total = result['total_issues']

        report_lines.append(f"\n【{chapter}】 - {total}个问题")

        if issues['unclassified']:
            report_lines.append(f"  未分类词汇({len(issues['unclassified'])}): " +
                              ", ".join(set(i['verb'] for i in issues['unclassified'][:5])))

        if issues['misplaced_noun']:
            report_lines.append(f"  误标名词({len(issues['misplaced_noun'])}): " +
                              ", ".join(i['content'][:10] for i in issues['misplaced_noun'][:3]))

        if issues['mixed_format']:
            report_lines.append(f"  格式混用: 旧格式{issues['mixed_format'][0]['old_count']}个, " +
                              f"新格式{issues['mixed_format'][0]['new_count']}个")

        if issues['missing_disambig']:
            report_lines.append(f"  缺少消歧({len(issues['missing_disambig'])}): " +
                              ", ".join(set(i['verb'] for i in issues['missing_disambig'][:5])))

    # 迁移建议
    report_lines.append(f"\n\n迁移建议:")
    report_lines.append("=" * 60)

    # 统计需要迁移的动词
    from query_verbs_by_type import extract_old_format_verbs

    all_military = []
    all_penalty = []

    for result in results:
        chapter_file = CHAPTER_DIR / f"{result['chapter']}.md"
        if not chapter_file.exists():
            chapter_file = CHAPTER_DIR / f"{result['chapter']}.tagged.md"
        if chapter_file.exists():
            with open(chapter_file, 'r', encoding='utf-8') as f:
                text = f.read()
            old_verbs = extract_old_format_verbs(text)
            all_military.extend(old_verbs['military'])
            all_penalty.extend(old_verbs['penalty'])

    report_lines.append(f"\n1. 军事动词迁移:")
    report_lines.append(f"   需要迁移: {len(all_military)} 处")
    report_lines.append(f"   格式: 〖[伐〗 → ⟦◈伐⟧")
    report_lines.append(f"   词表: {', '.join(sorted(MILITARY_VERBS))}")

    report_lines.append(f"\n2. 刑罚动词迁移:")
    report_lines.append(f"   需要迁移: {len(all_penalty)} 处")
    report_lines.append(f"   格式: 〖[杀〗 → ⟦◉杀⟧")
    report_lines.append(f"   词表: {', '.join(sorted(PENALTY_VERBS))}")

    report_lines.append(f"\n3. 刑罚制度名词:")
    report_lines.append(f"   保持不变，继续使用 〖[名词〗")

    report_lines.append("\n" + "=" * 60)

    # 输出报告
    report_text = '\n'.join(report_lines)

    if output_file:
        output_path = BASE_DIR / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"\n验证报告已保存到: {output_path}")
    else:
        print(report_text)


def main():
    parser = argparse.ArgumentParser(description='动词标注验证工具')
    parser.add_argument('--chapter', type=int, metavar='NNN',
                        help='验证指定章节（如 040）')
    parser.add_argument('--strict', action='store_true',
                        help='严格模式（检查更多问题）')
    parser.add_argument('--report', metavar='FILE',
                        help='生成报告并保存到文件')

    args = parser.parse_args()

    # 收集章节
    if args.chapter:
        chapter_files = list(CHAPTER_DIR.glob(f'{args.chapter:03d}_*.tagged.md'))
        if not chapter_files:
            print(f"错误: 未找到章节 {args.chapter:03d}")
            sys.exit(1)
    else:
        chapter_files = sorted(CHAPTER_DIR.glob('*.tagged.md'))

    # 验证
    print(f"正在验证 {len(chapter_files)} 个章节...")
    results = []
    for chapter_file in chapter_files:
        result = validate_chapter(chapter_file, strict=args.strict)
        results.append(result)

    # 生成报告
    generate_validation_report(results, args.report)


if __name__ == '__main__':
    main()
