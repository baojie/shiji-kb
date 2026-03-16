#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身份迁移脚本 — 将 〖;X〗(官职) 和 @X@(人名) 中的身份实体迁移为 〖#X〗(身份)

Phase 1: 自动替换 always_identity 列表中的实体
Phase 2: 为 context_dependent 实体生成审查报告，人工/LLM 审核后应用
Phase 3: 扫描未标注文本中的新身份词（new_candidates）

用法:
  python scripts/migrate_official_to_identity.py --phase1 [--dry-run]
  python scripts/migrate_official_to_identity.py --phase2-report
  python scripts/migrate_official_to_identity.py --apply-patch FILE
  python scripts/migrate_official_to_identity.py --scan-new [--dry-run]
  python scripts/migrate_official_to_identity.py --check
  python scripts/migrate_official_to_identity.py --test NNN
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHAPTER_DIR = BASE_DIR / 'chapter_md'
WORDLIST_PATH = BASE_DIR / 'kg' / 'entities' / 'data' / 'identity_wordlist.json'

# 源标记 → 身份标记的映射
# 官职: 〖;X〗 → 〖#X〗
# 人名: @X@ → 〖#X〗
SOURCE_OFFICIAL = '〖;{}〗'
SOURCE_PERSON = '@{}@'
TARGET_IDENTITY = '〖#{}〗'

# 已标注实体的正则（用于排除已标注区域）
TAGGED_RE = re.compile(
    r'〖[;&\$\'^!~•\?\{\:\[\_][^〖〗\n]+〗'   # 新标注格式（v2.8）
    r'|@[^@\n]+@'                              # 人名旧格式
)


def load_wordlist():
    """加载身份词表"""
    with open(WORDLIST_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def get_tagged_files(chapter_num=None):
    """获取 tagged.md 文件列表"""
    if chapter_num:
        pattern = f'{chapter_num:03d}_*.tagged.md'
        files = sorted(CHAPTER_DIR.glob(pattern))
        if not files:
            print(f"未找到章节 {chapter_num:03d}")
            sys.exit(1)
        return files
    return sorted(CHAPTER_DIR.glob('*.tagged.md'))


def migrate_always_identity(dry_run=False, chapter_num=None):
    """Phase 1: 自动替换 always_identity 列表中的实体（从 official 和 person 迁移）"""
    wordlist = load_wordlist()
    always_identity = set(wordlist['always_identity'])
    exclude_person = set(wordlist.get('exclude', {}).get('keep_person', []))

    files = get_tagged_files(chapter_num)
    total_replacements = 0
    file_stats = []

    for fpath in files:
        content = fpath.read_text(encoding='utf-8')
        original = content
        file_count = 0

        for name in always_identity:
            # 从官职迁移: 〖;X〗 → 〖#X〗
            old_official = SOURCE_OFFICIAL.format(name)
            new_identity = TARGET_IDENTITY.format(name)
            count = content.count(old_official)
            if count > 0:
                content = content.replace(old_official, new_identity)
                file_count += count

            # 从人名迁移: @X@ → 〖#X〗（仅限不在 exclude 列表的词）
            if name not in exclude_person:
                old_person = SOURCE_PERSON.format(name)
                count2 = content.count(old_person)
                if count2 > 0:
                    content = content.replace(old_person, new_identity)
                    file_count += count2

        if file_count > 0:
            total_replacements += file_count
            file_stats.append((fpath.name, file_count))

            if not dry_run:
                fpath.write_text(content, encoding='utf-8')

    # 报告
    print(f"Phase 1: always_identity 自动迁移")
    print(f"{'[DRY RUN] ' if dry_run else ''}处理文件: {len(files)}")
    print(f"替换总数: {total_replacements}")
    print()

    if file_stats:
        print(f"有变更的文件 ({len(file_stats)}):")
        for fname, count in sorted(file_stats, key=lambda x: -x[1]):
            print(f"  {fname}: {count} 处")
    else:
        print("没有需要替换的内容")

    return total_replacements


def generate_phase2_report(chapter_num=None):
    """Phase 2: 为 context_dependent 实体生成 TSV 审查报告"""
    wordlist = load_wordlist()
    context_dep = wordlist['context_dependent']['names']

    files = get_tagged_files(chapter_num)
    report_lines = []
    report_lines.append("file\tline_num\tentity\tsource_type\tcontext_before\ttag_text\tcontext_after\tdecision")

    for fpath in files:
        lines = fpath.read_text(encoding='utf-8').split('\n')
        for line_num, line in enumerate(lines, 1):
            for name in context_dep:
                # 检查官职标记
                tag_official = SOURCE_OFFICIAL.format(name)
                _search_tag_in_line(line, tag_official, name, 'official',
                                    fpath.name, line_num, report_lines)

                # 检查人名标记
                tag_person = SOURCE_PERSON.format(name)
                _search_tag_in_line(line, tag_person, name, 'person',
                                    fpath.name, line_num, report_lines)

    # 写出报告
    report_path = BASE_DIR / 'tmp' / 'phase2_identity_review.tsv'
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text('\n'.join(report_lines), encoding='utf-8')

    entry_count = len(report_lines) - 1
    print(f"Phase 2 审查报告已生成: {report_path}")
    print(f"待审查条目: {entry_count}")
    print()
    print("请在 decision 列填写: identity / official / person / skip")
    print("然后运行: python scripts/migrate_official_to_identity.py --apply-patch tmp/phase2_identity_review.tsv")

    return entry_count


def _search_tag_in_line(line, tag, name, source_type, fname, line_num, report_lines):
    """在行内搜索标记并添加到报告"""
    pos = 0
    while True:
        idx = line.find(tag, pos)
        if idx == -1:
            break
        start = max(0, idx - 40)
        end = min(len(line), idx + len(tag) + 40)
        ctx_before = line[start:idx].replace('\t', ' ')
        ctx_after = line[idx + len(tag):end].replace('\t', ' ')
        report_lines.append(
            f"{fname}\t{line_num}\t{name}\t{source_type}\t"
            f"{ctx_before}\t{tag}\t{ctx_after}\t"
        )
        pos = idx + len(tag)


def apply_patch(patch_file):
    """根据审查后的 TSV 应用修改"""
    patch_path = Path(patch_file)
    if not patch_path.is_absolute():
        patch_path = BASE_DIR / patch_path

    lines = patch_path.read_text(encoding='utf-8').strip().split('\n')

    changes_by_file = {}
    applied = 0
    skipped = 0

    for line in lines[1:]:
        parts = line.split('\t')
        if len(parts) < 8:
            continue

        fname = parts[0]
        entity = parts[2]
        source_type = parts[3]
        decision = parts[7].strip().lower()

        if decision == 'identity':
            if fname not in changes_by_file:
                changes_by_file[fname] = []
            changes_by_file[fname].append((entity, source_type))
            applied += 1
        elif decision in ('official', 'person', 'skip', ''):
            skipped += 1
        else:
            print(f"警告: 未知 decision '{decision}' for {fname} {entity}")
            skipped += 1

    # 应用修改
    for fname, changes in changes_by_file.items():
        fpath = CHAPTER_DIR / fname
        if not fpath.exists():
            print(f"警告: 文件不存在 {fpath}")
            continue

        content = fpath.read_text(encoding='utf-8')
        for entity, source_type in changes:
            if source_type == 'official':
                old = SOURCE_OFFICIAL.format(entity)
            else:
                old = SOURCE_PERSON.format(entity)
            new = TARGET_IDENTITY.format(entity)
            content = content.replace(old, new)

        fpath.write_text(content, encoding='utf-8')

    print(f"Patch 应用完成: {applied} 条替换, {skipped} 条跳过")
    print(f"影响文件: {len(changes_by_file)}")


def scan_new_candidates(dry_run=False, chapter_num=None):
    """Phase 3: 扫描未标注文本中的新身份词（new_candidates）"""
    wordlist = load_wordlist()

    # 收集所有 new_candidates
    candidates = []
    for group_name, group_words in wordlist.get('new_candidates', {}).items():
        if group_name.startswith('_'):
            continue
        if isinstance(group_words, list):
            candidates.extend(group_words)

    # 按字数降序排列（贪心匹配）
    candidates.sort(key=lambda x: -len(x))

    files = get_tagged_files(chapter_num)
    report_lines = []
    report_lines.append("file\tline_num\tentity\tcontext_before\tword\tcontext_after\tgroup")

    total_found = 0

    for fpath in files:
        content = fpath.read_text(encoding='utf-8')
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # 获取未标注区域
            untagged_spans = _get_untagged_spans(line)

            for span_start, span_end in untagged_spans:
                span_text = line[span_start:span_end]

                for word in candidates:
                    pos = 0
                    while True:
                        idx = span_text.find(word, pos)
                        if idx == -1:
                            break

                        abs_idx = span_start + idx
                        ctx_start = max(0, abs_idx - 20)
                        ctx_end = min(len(line), abs_idx + len(word) + 20)
                        ctx_before = line[ctx_start:abs_idx].replace('\t', ' ')
                        ctx_after = line[abs_idx + len(word):ctx_end].replace('\t', ' ')

                        # 确定所属分组
                        group = _find_group(word, wordlist['new_candidates'])

                        report_lines.append(
                            f"{fpath.name}\t{line_num}\t{word}\t"
                            f"{ctx_before}\t{word}\t{ctx_after}\t{group}"
                        )
                        total_found += 1
                        pos = idx + len(word)

    # 写出报告
    report_path = BASE_DIR / 'tmp' / 'phase3_identity_new_candidates.tsv'
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text('\n'.join(report_lines), encoding='utf-8')

    print(f"Phase 3: 新身份词扫描")
    print(f"处理文件: {len(files)}")
    print(f"发现未标注身份词: {total_found}")
    print(f"报告: {report_path}")

    # 汇总统计
    from collections import Counter
    word_counts = Counter()
    for line in report_lines[1:]:
        parts = line.split('\t')
        if len(parts) >= 3:
            word_counts[parts[2]] += 1

    if word_counts:
        print(f"\n词频统计 (top 30):")
        for word, count in word_counts.most_common(30):
            print(f"  {word}: {count}")

    return total_found


def _get_untagged_spans(line):
    """返回行内未被标注覆盖的文本区间 [(start, end), ...]"""
    tagged_spans = [(m.start(), m.end()) for m in TAGGED_RE.finditer(line)]
    if not tagged_spans:
        return [(0, len(line))]

    spans = []
    prev_end = 0
    for start, end in sorted(tagged_spans):
        if prev_end < start:
            spans.append((prev_end, start))
        prev_end = max(prev_end, end)
    if prev_end < len(line):
        spans.append((prev_end, len(line)))
    return spans


def _find_group(word, candidates_dict):
    """查找词所属的分组名"""
    for group_name, group_words in candidates_dict.items():
        if group_name.startswith('_'):
            continue
        if isinstance(group_words, list) and word in group_words:
            return group_name
    return 'unknown'


def check_remaining():
    """检查 official/person 中是否还有残留身份词"""
    wordlist = load_wordlist()
    always_identity = set(wordlist['always_identity'])

    files = get_tagged_files()
    remaining = {}

    for fpath in files:
        content = fpath.read_text(encoding='utf-8')
        for name in always_identity:
            # 检查 official
            tag = SOURCE_OFFICIAL.format(name)
            count = content.count(tag)
            if count > 0:
                key = f'〖;{name}〗'
                if key not in remaining:
                    remaining[key] = {'count': 0, 'files': []}
                remaining[key]['count'] += count
                remaining[key]['files'].append(fpath.name)

            # 检查 person
            tag_p = SOURCE_PERSON.format(name)
            count_p = content.count(tag_p)
            if count_p > 0:
                key = f'@{name}@'
                if key not in remaining:
                    remaining[key] = {'count': 0, 'files': []}
                remaining[key]['count'] += count_p
                remaining[key]['files'].append(fpath.name)

    if remaining:
        print(f"剩余未迁移的身份实体 ({len(remaining)} 种):")
        for tag, info in sorted(remaining.items(), key=lambda x: -x[1]['count']):
            file_list = ', '.join(info['files'][:3])
            more = f" +{len(info['files'])-3}" if len(info['files']) > 3 else ""
            print(f"  {tag}: {info['count']} 次 ({file_list}{more})")
    else:
        print("所有身份实体已迁移完成！")

    # 当前统计
    identity_count = 0
    official_count = 0
    for fpath in get_tagged_files():
        content = fpath.read_text(encoding='utf-8')
        identity_count += len(re.findall(r'〖#[^〖〗]+〗', content))
        official_count += len(re.findall(r'〖;[^〖〗]+〗', content))

    print(f"\n当前统计: 〖;官职〗={official_count}, 〖#身份〗={identity_count}")


def main():
    parser = argparse.ArgumentParser(description='身份迁移脚本')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--phase1', action='store_true',
                       help='Phase 1: 自动替换 always_identity')
    group.add_argument('--phase2-report', action='store_true',
                       help='Phase 2: 生成 context_dependent 审查报告')
    group.add_argument('--apply-patch', metavar='FILE',
                       help='应用审查后的 TSV patch')
    group.add_argument('--scan-new', action='store_true',
                       help='Phase 3: 扫描未标注的新身份词')
    group.add_argument('--check', action='store_true',
                       help='检查剩余的身份标注')
    group.add_argument('--test', type=int, metavar='NNN',
                       help='测试单章')

    parser.add_argument('--dry-run', action='store_true',
                        help='仅预览，不修改文件')

    args = parser.parse_args()

    if args.phase1:
        migrate_always_identity(dry_run=args.dry_run)
    elif args.phase2_report:
        generate_phase2_report()
    elif args.apply_patch:
        apply_patch(args.apply_patch)
    elif args.scan_new:
        scan_new_candidates(dry_run=args.dry_run)
    elif args.check:
        check_remaining()
    elif args.test is not None:
        print(f"=== 测试章节 {args.test:03d} ===")
        print("\n--- Phase 1 (dry run) ---")
        migrate_always_identity(dry_run=True, chapter_num=args.test)
        print("\n--- Phase 2 report ---")
        generate_phase2_report(chapter_num=args.test)
        print("\n--- Phase 3 scan ---")
        scan_new_candidates(chapter_num=args.test)


if __name__ == '__main__':
    main()
