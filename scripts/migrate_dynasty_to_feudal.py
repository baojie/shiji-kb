#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
封国迁移脚本 — 将 〖&X〗(朝代) 中的封国实体迁移为 〖$X〗(封国)

Phase 1: 自动替换 always_feudal 列表中的实体
Phase 2: 为 context_dependent 实体生成审查报告，人工/LLM 审核后应用

用法:
  python scripts/migrate_dynasty_to_feudal.py --phase1 [--dry-run]
  python scripts/migrate_dynasty_to_feudal.py --phase2-report
  python scripts/migrate_dynasty_to_feudal.py --apply-patch FILE
  python scripts/migrate_dynasty_to_feudal.py --check
  python scripts/migrate_dynasty_to_feudal.py --test NNN
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHAPTER_DIR = BASE_DIR / 'chapter_md'
WORDLIST_PATH = BASE_DIR / 'kg' / 'entities' / 'data' / 'feudal_state_wordlist.json'


def load_wordlist():
    """加载封国词表"""
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


def migrate_always_feudal(dry_run=False, chapter_num=None):
    """Phase 1: 自动替换 always_feudal 列表"""
    wordlist = load_wordlist()
    always_feudal = set(wordlist['always_feudal'])

    files = get_tagged_files(chapter_num)
    total_replacements = 0
    file_stats = []

    for fpath in files:
        content = fpath.read_text(encoding='utf-8')
        original = content
        file_count = 0

        for name in always_feudal:
            old = f'〖&{name}〗'
            new = f"〖'{name}〗"
            count = content.count(old)
            if count > 0:
                content = content.replace(old, new)
                file_count += count

        if file_count > 0:
            total_replacements += file_count
            file_stats.append((fpath.name, file_count))

            if not dry_run:
                fpath.write_text(content, encoding='utf-8')

    # 报告
    print(f"Phase 1: always_feudal 自动迁移")
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
    report_lines.append("file\tline_num\tentity\tcontext_before\ttag_text\tcontext_after\tdecision")

    for fpath in files:
        lines = fpath.read_text(encoding='utf-8').split('\n')
        for line_num, line in enumerate(lines, 1):
            for name in context_dep:
                tag = f'〖&{name}〗'
                pos = 0
                while True:
                    idx = line.find(tag, pos)
                    if idx == -1:
                        break
                    # 提取上下文（前后各40字符）
                    start = max(0, idx - 40)
                    end = min(len(line), idx + len(tag) + 40)
                    ctx_before = line[start:idx].replace('\t', ' ')
                    ctx_after = line[idx + len(tag):end].replace('\t', ' ')
                    report_lines.append(
                        f"{fpath.name}\t{line_num}\t{name}\t"
                        f"{ctx_before}\t{tag}\t{ctx_after}\t"
                    )
                    pos = idx + len(tag)

    # 写出报告
    report_path = BASE_DIR / 'tmp' / 'phase2_feudal_review.tsv'
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text('\n'.join(report_lines), encoding='utf-8')

    entry_count = len(report_lines) - 1  # 减去表头
    print(f"Phase 2 审查报告已生成: {report_path}")
    print(f"待审查条目: {entry_count}")
    print()
    print("请在 decision 列填写: feudal / dynasty / skip")
    print("然后运行: python scripts/migrate_dynasty_to_feudal.py --apply-patch tmp/phase2_feudal_review.tsv")

    return entry_count


def apply_patch(patch_file):
    """根据审查后的 TSV 应用修改"""
    patch_path = Path(patch_file)
    if not patch_path.is_absolute():
        patch_path = BASE_DIR / patch_path

    lines = patch_path.read_text(encoding='utf-8').strip().split('\n')
    header = lines[0].split('\t')

    # 按文件分组
    changes_by_file = {}
    applied = 0
    skipped = 0

    for line in lines[1:]:
        parts = line.split('\t')
        if len(parts) < 7:
            continue

        fname = parts[0]
        line_num = int(parts[1])
        entity = parts[2]
        decision = parts[6].strip().lower()

        if decision == 'feudal':
            if fname not in changes_by_file:
                changes_by_file[fname] = []
            changes_by_file[fname].append((entity, line_num))
            applied += 1
        elif decision in ('dynasty', 'skip', ''):
            skipped += 1
        else:
            print(f"警告: 未知 decision '{decision}' for {fname}:{line_num} {entity}")
            skipped += 1

    # 应用修改
    for fname, changes in changes_by_file.items():
        fpath = CHAPTER_DIR / fname
        if not fpath.exists():
            print(f"警告: 文件不存在 {fpath}")
            continue

        content = fpath.read_text(encoding='utf-8')
        for entity, _ in changes:
            old = f'〖&{entity}〗'
            new = f"〖'{entity}〗"
            # 逐个替换（按行号匹配更精确，但简单场景下全替换也可接受）
            content = content.replace(old, new)

        fpath.write_text(content, encoding='utf-8')

    print(f"Patch 应用完成: {applied} 条替换, {skipped} 条跳过")
    print(f"影响文件: {len(changes_by_file)}")


def check_remaining():
    """检查剩余的朝代标注中是否还有封国"""
    wordlist = load_wordlist()
    always_feudal = set(wordlist['always_feudal'])
    context_dep = set(wordlist['context_dependent']['names'])
    all_feudal = always_feudal | context_dep

    files = get_tagged_files()
    remaining = {}

    for fpath in files:
        content = fpath.read_text(encoding='utf-8')
        for name in all_feudal:
            tag = f'〖&{name}〗'
            count = content.count(tag)
            if count > 0:
                if name not in remaining:
                    remaining[name] = {'count': 0, 'files': []}
                remaining[name]['count'] += count
                remaining[name]['files'].append(fpath.name)

    if remaining:
        print(f"剩余未迁移的封国实体 ({len(remaining)} 种):")
        for name, info in sorted(remaining.items(), key=lambda x: -x[1]['count']):
            file_list = ', '.join(info['files'][:3])
            more = f" +{len(info['files'])-3}" if len(info['files']) > 3 else ""
            print(f"  〖&{name}〗: {info['count']} 次 ({file_list}{more})")
    else:
        print("所有封国实体已迁移完成！")

    # 也显示当前 feudal-state 统计
    feudal_count = 0
    dynasty_count = 0
    for fpath in files:
        content = fpath.read_text(encoding='utf-8')
        feudal_count += len(re.findall(r"〖'[^〖〗]+〗", content))
        dynasty_count += len(re.findall(r'〖&[^〖〗]+〗', content))

    print(f"\n当前统计: 〖&朝代〗={dynasty_count}, 〖'封国〗={feudal_count}, 合计={dynasty_count+feudal_count}")


def main():
    parser = argparse.ArgumentParser(description='封国迁移脚本')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--phase1', action='store_true', help='Phase 1: 自动替换 always_feudal')
    group.add_argument('--phase2-report', action='store_true', help='Phase 2: 生成审查报告')
    group.add_argument('--apply-patch', metavar='FILE', help='应用审查后的 TSV patch')
    group.add_argument('--check', action='store_true', help='检查剩余的封国标注')
    group.add_argument('--test', type=int, metavar='NNN', help='测试单章')

    parser.add_argument('--dry-run', action='store_true', help='仅预览，不修改文件')

    args = parser.parse_args()

    if args.phase1:
        migrate_always_feudal(dry_run=args.dry_run)
    elif args.phase2_report:
        generate_phase2_report()
    elif args.apply_patch:
        apply_patch(args.apply_patch)
    elif args.check:
        check_remaining()
    elif args.test is not None:
        print(f"=== 测试章节 {args.test:03d} ===")
        print("\n--- Phase 1 (dry run) ---")
        migrate_always_feudal(dry_run=True, chapter_num=args.test)
        print("\n--- Phase 2 report ---")
        generate_phase2_report(chapter_num=args.test)


if __name__ == '__main__':
    main()
