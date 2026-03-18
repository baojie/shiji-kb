#!/usr/bin/env python3
"""
动词自动标注工具

功能：基于核心词表对章节进行第一轮动词标注

规则：
1. 只标注核心词表中的动词
2. 避免在已标注的名词实体内部标注
3. 避免在制度名词中标注单字动词
4. 保守策略：疑似歧义的不标注

用法：
  python auto_annotate_verbs.py --chapter 002        # 标注002章
  python auto_annotate_verbs.py --range 002-010      # 标注002-010章
  python auto_annotate_verbs.py --all                # 标注所有章节
  python auto_annotate_verbs.py --dry-run            # 预览模式
"""

import re
import sys
import argparse
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHAPTER_DIR = BASE_DIR / 'chapter_md'

# 导入词表
from query_verbs_by_type import (
    MILITARY_VERBS, PENALTY_VERBS, POLITICAL_VERBS
)

# 所有动词
ALL_VERBS = MILITARY_VERBS | PENALTY_VERBS | POLITICAL_VERBS


def get_verb_type(verb):
    """获取动词类型符号"""
    if verb in MILITARY_VERBS:
        return '◈'
    elif verb in PENALTY_VERBS:
        return '◉'
    elif verb in POLITICAL_VERBS:
        return '○'
    return None


def is_inside_entity(text, pos):
    """检查位置是否在已标注的实体内部"""
    # 向前查找最近的〖或⟦
    left_bracket_pos = -1
    for i in range(pos - 1, -1, -1):
        if text[i] in '〖⟦':
            left_bracket_pos = i
            break

    # 如果找到了左括号，检查是否有对应的右括号
    if left_bracket_pos >= 0:
        bracket_type = text[left_bracket_pos]
        close_bracket = '〗' if bracket_type == '〖' else '⟧'

        # 在pos之后查找对应的右括号
        for i in range(pos, min(pos + 50, len(text))):
            if text[i] == close_bracket:
                # 如果找到闭合括号，说明pos在实体内部
                return True

    return False


def annotate_verbs(text, dry_run=False):
    """
    自动标注动词

    Args:
        text: 原文本
        dry_run: 是否为预览模式

    Returns:
        (annotated_text, stats)
    """
    stats = Counter()
    result = text

    # 对每个动词进行标注
    for verb in sorted(ALL_VERBS, key=len, reverse=True):  # 先处理长的词
        verb_type = get_verb_type(verb)
        if not verb_type:
            continue

        # 构建标注格式
        new_tag = f'⟦{verb_type}{verb}⟧'

        # 查找所有未标注的动词
        pattern = re.escape(verb)

        # 避免重复标注
        if new_tag in result:
            continue

        # 遍历所有匹配位置
        offset = 0
        while True:
            match = re.search(pattern, result[offset:])
            if not match:
                break

            pos = offset + match.start()

            # 检查是否在实体内部
            if is_inside_entity(result, pos):
                offset = pos + len(verb)
                continue

            # 检查前后字符，避免误标
            before_char = result[pos-1] if pos > 0 else ''
            after_char = result[pos+len(verb)] if pos+len(verb) < len(result) else ''

            # 跳过复合词中的动词（如"战国"、"游击将军"等，这些已经是实体标注）
            # 但允许标注"伐之"、"杀〖@某人〗"等情况

            # 如果后面紧跟实体标注或常见虚词，可以标注
            if after_char in '〖⟦之而于於以其':
                pass  # 允许标注
            # 如果前后都是汉字，且verb是单字，需要谨慎
            elif len(verb) == 1 and before_char and after_char:
                if '\u4e00' <= before_char <= '\u9fff' and '\u4e00' <= after_char <= '\u9fff':
                    # 跳过（可能是复合词）
                    offset = pos + len(verb)
                    continue

            # 执行替换
            if not dry_run:
                result = result[:pos] + new_tag + result[pos+len(verb):]
                offset = pos + len(new_tag)
            else:
                offset = pos + len(verb)

            # 统计
            stats[verb] += 1

    return result, stats


def process_chapter(chapter_file, dry_run=False):
    """处理单个章节"""
    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()

    annotated, stats = annotate_verbs(content, dry_run)

    if not dry_run and stats:
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(annotated)

    return stats


def main():
    parser = argparse.ArgumentParser(description='动词自动标注工具')
    parser.add_argument('--chapter', help='章节编号（如002）')
    parser.add_argument('--range', help='章节范围（如002-010）')
    parser.add_argument('--all', action='store_true', help='处理所有章节')
    parser.add_argument('--dry-run', action='store_true', help='预览模式（不修改文件）')

    args = parser.parse_args()

    # 确定要处理的章节
    chapters = []

    if args.chapter:
        chapter_file = CHAPTER_DIR / f"{args.chapter}_*.tagged.md"
        chapters = list(CHAPTER_DIR.glob(f"{args.chapter}_*.tagged.md"))
    elif args.range:
        start, end = args.range.split('-')
        start_num = int(start)
        end_num = int(end)
        for i in range(start_num, end_num + 1):
            chapters.extend(CHAPTER_DIR.glob(f"{i:03d}_*.tagged.md"))
    elif args.all:
        chapters = sorted(CHAPTER_DIR.glob("*.tagged.md"))
    else:
        print("请指定 --chapter, --range 或 --all")
        return

    if not chapters:
        print("未找到匹配的章节")
        return

    print(f"{'[预览模式] ' if args.dry_run else ''}准备处理 {len(chapters)} 个章节...")
    print()

    total_stats = Counter()
    processed = 0

    for chapter_file in chapters:
        stats = process_chapter(chapter_file, args.dry_run)
        if stats:
            processed += 1
            total_stats += stats
            print(f"✅ {chapter_file.name}: {sum(stats.values())}处动词")
            for verb, count in stats.most_common(10):
                verb_type = get_verb_type(verb)
                print(f"   {verb_type}{verb}: {count}次")

    print()
    print("="*60)
    print(f"总计: 处理了{processed}个章节，标注了{sum(total_stats.values())}处动词")
    print()

    if total_stats:
        print("Top 20 动词:")
        for verb, count in total_stats.most_common(20):
            verb_type = get_verb_type(verb)
            print(f"  {verb_type}{verb}: {count}次")


if __name__ == '__main__':
    main()
