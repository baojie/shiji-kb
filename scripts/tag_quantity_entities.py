#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数量实体自动标注脚本

从 quantity_wordlist.json 读取词表，在130章标注文件中自动标注数量实体 〖$X〗。

逻辑：
  1. 掩码已有标注区域（所有17种现有标注）
  2. 掩码标题行（# 开头）
  3. 按词表长度降序匹配（避免子串覆盖）
  4. always_quantity 直接标注
  5. 输出统计报告

用法：
  python scripts/tag_quantity_entities.py --chapter 087    # 单章预览
  python scripts/tag_quantity_entities.py --all --dry-run  # 全量预览
  python scripts/tag_quantity_entities.py --all             # 全量执行
"""

import re
import json
import argparse
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = PROJECT_ROOT / 'chapter_md'
WORDLIST_FILE = PROJECT_ROOT / 'kg' / 'quantity' / 'data' / 'quantity_wordlist.json'

# 已有标注的检测正则（覆盖全部18种）
ALL_ANNOT_RE = re.compile(
    r'〖[@=;%&\'^~\*!#\+\$][^〖〗\n]+?〗'
    r'|〚[^〛\n]+?〛'
    r'|《[^》\n]+?》'
    r'|〈[^〉\n]+?〉'
    r'|【[^】\n]+?】'
    r'|〔[^〕\n]+?〕'
)

NUM_PREFIX_CHARS = set('零一二三四五六七八九十百千万亿两数几')


def load_wordlist():
    """加载数量词表，返回按长度降序排列的词列表"""
    with open(WORDLIST_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    words = set()
    always = data.get('always_quantity', {})
    for category, word_list in always.items():
        for w in word_list:
            words.add(w)

    # 按长度降序排列（避免子串覆盖）
    return sorted(words, key=len, reverse=True)


def tag_line(line, words, stats):
    """对单行文本进行数量标注

    策略：在原文上直接操作，但先识别已有标注的span区间，
    匹配时跳过这些区间。从后往前插入标注避免偏移问题。
    """
    # 跳过标题行和空行
    if line.startswith('#') or not line.strip():
        return line

    # 找出所有已有标注的区间 [(start, end), ...]
    protected = []
    for m in ALL_ANNOT_RE.finditer(line):
        protected.append((m.start(), m.end()))

    def is_protected(pos, length):
        """检查 [pos, pos+length) 是否与任何已有标注重叠"""
        for ps, pe in protected:
            if not (pos + length <= ps or pos >= pe):
                return True
        return False

    # 按词表匹配（长词优先），收集匹配位置
    matches = []  # [(start, end, word)]
    matched_ranges = []  # 已匹配的区间

    def overlaps_matched(pos, length):
        for ms, me in matched_ranges:
            if not (pos + length <= ms or pos >= me):
                return True
        return False

    for word in words:
        start = 0
        while True:
            pos = line.find(word, start)
            if pos == -1:
                break

            wlen = len(word)

            # 检查是否在已有标注区域内
            if is_protected(pos, wlen):
                start = pos + 1
                continue

            # 检查是否与已匹配区域重叠
            if overlaps_matched(pos, wlen):
                start = pos + 1
                continue

            # 检查前方是否紧跟数词（避免拆分更大的数量表达）
            if pos > 0:
                prev_char = line[pos - 1]
                if prev_char in NUM_PREFIX_CHARS:
                    # 但如果前一个字符本身在标注内，则允许
                    if not is_protected(pos - 1, 1):
                        start = pos + 1
                        continue

            matches.append((pos, pos + wlen, word))
            matched_ranges.append((pos, pos + wlen))
            stats[word] += 1

            start = pos + 1

    if not matches:
        return line

    # 从后往前插入标注（避免偏移问题）
    matches.sort(key=lambda x: x[0], reverse=True)
    result = line
    for ms, me, word in matches:
        result = result[:ms] + f'〖${word}〗' + result[me:]

    return result


def process_chapter(chapter_file, words, dry_run=False):
    """处理单章"""
    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    stats = defaultdict(int)
    new_lines = []

    for line in lines:
        new_line = tag_line(line, words, stats)
        new_lines.append(new_line)

    total = sum(stats.values())
    chapter_name = chapter_file.stem.replace('.tagged', '')

    if total > 0:
        print(f"  {chapter_name}: {total} 处标注 ({len(stats)} 种表达)")
        if not dry_run:
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))

    return stats


def main():
    parser = argparse.ArgumentParser(description='数量实体自动标注')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--chapter', type=str, help='章节编号（如 087）')
    group.add_argument('--all', action='store_true', help='处理全部章节')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不写入文件')
    args = parser.parse_args()

    words = load_wordlist()
    print(f"词表加载完成：{len(words)} 个词条")

    if args.chapter:
        files = sorted(CHAPTER_DIR.glob(f'{args.chapter}_*.tagged.md'))
    else:
        files = sorted(CHAPTER_DIR.glob('*.tagged.md'))

    if not files:
        print("未找到匹配的标注文件")
        return

    print(f"{'预览模式' if args.dry_run else '标注模式'}：处理 {len(files)} 个文件\n")

    global_stats = defaultdict(int)
    chapter_count = 0

    for f in files:
        stats = process_chapter(f, words, dry_run=args.dry_run)
        if sum(stats.values()) > 0:
            chapter_count += 1
        for k, v in stats.items():
            global_stats[k] += v

    total = sum(global_stats.values())
    print(f"\n{'='*50}")
    print(f"总计：{total} 处标注，{len(global_stats)} 种表达，{chapter_count} 章涉及")

    if global_stats:
        print(f"\nTop 20 高频表达：")
        for word, count in sorted(global_stats.items(), key=lambda x: -x[1])[:20]:
            print(f"  {word}: {count}")


if __name__ == '__main__':
    main()
