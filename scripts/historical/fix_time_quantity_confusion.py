#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复时间与数量标注混淆问题

问题：一些数量词被错误标注为时间类型 〖%X〗，应改为数量类型 〖$X〗
例如：〖%千石〗 → 〖$千石〗
     〖%二百蹄〗 → 〖$二百蹄〗

检测规则：
1. 含有数量单位字（蹄、足、石、章、畦、里、步、亩等）的应为数量
2. 纯地理方位词（东、西、南、北等）不应标注为时间
3. 不含时间特征字的应重新评估

用法：
  python scripts/fix_time_quantity_confusion.py --dry-run    # 预览
  python scripts/fix_time_quantity_confusion.py              # 执行修复
"""

import re
import argparse
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = PROJECT_ROOT / 'chapter_md'

# 时间特征字
TIME_CHARS = set('年月日岁世元载春夏秋冬子丑寅卯辰巳午未申酉戌亥甲乙丙丁戊己庚辛壬癸朝夜晨暮旦昏时刻初中后前至今')

# 数量单位字（明确的量词）
QUANTITY_UNIT_CHARS = set('蹄足石章畦里步亩顷丈尺寸斤两钱贯匹驷双辈篇卷社车马人户家郡')

# 排除词（虽然含数量字，但确实是时间或其他类型）
EXCLUDE_WORDS = {
    '战国',  # 历史时期
    '国中', '国家', '郡国',  # 地名/政治概念
}

# 地理方位字
GEO_DIRECTION_CHARS = set('东西南北方向')


def should_be_quantity(text):
    """判断是否应该是数量类型"""
    # 排除特殊词
    if text in EXCLUDE_WORDS:
        return False

    # 包含明确的数量单位
    if any(c in QUANTITY_UNIT_CHARS for c in text):
        return True
    return False


def should_be_time(text):
    """判断是否应该是时间类型"""
    # 必须包含时间特征字
    return any(c in TIME_CHARS for c in text)


def fix_chapter(file_path, dry_run=True):
    """修复单章的时间/数量标注混淆"""
    content = file_path.read_text(encoding='utf-8')

    # 查找所有时间标注
    time_pattern = re.compile(r'〖%([^〗]+)〗')
    fixes = []

    for match in time_pattern.finditer(content):
        entity_text = match.group(1)

        # 判断是否应该改为数量
        if should_be_quantity(entity_text):
            if not should_be_time(entity_text):
                # 明确是数量，不是时间
                fixes.append({
                    'pos': match.start(),
                    'old': match.group(0),
                    'new': f'〖${entity_text}〗',
                    'reason': '含数量单位'
                })

    if not fixes:
        return 0, []

    # 从后往前替换（避免偏移问题）
    fixes.sort(key=lambda x: x['pos'], reverse=True)

    if not dry_run:
        result = content
        for fix in fixes:
            result = result.replace(fix['old'], fix['new'], 1)
        file_path.write_text(result, encoding='utf-8')

    return len(fixes), fixes


def main():
    parser = argparse.ArgumentParser(description='修复时间与数量标注混淆')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不实际修改文件')
    parser.add_argument('--chapter', help='指定章节编号（如 129）')
    args = parser.parse_args()

    if args.chapter:
        files = list(CHAPTER_DIR.glob(f'{args.chapter}_*.tagged.md'))
    else:
        files = sorted(CHAPTER_DIR.glob('*.tagged.md'))

    if not files:
        print('未找到匹配的标注文件')
        return

    print(f"{'='*60}")
    print(f"{'预览模式' if args.dry_run else '修复模式'}：检查 {len(files)} 个文件")
    print(f"{'='*60}\n")

    total_fixes = 0
    affected_chapters = 0
    all_fixes_by_entity = defaultdict(int)

    for file_path in files:
        count, fixes = fix_chapter(file_path, dry_run=args.dry_run)

        if count > 0:
            affected_chapters += 1
            total_fixes += count
            chapter_name = file_path.stem.replace('.tagged', '')

            print(f"📄 {chapter_name}: {count} 处修复")

            # 统计每个实体的修复次数
            entity_counts = defaultdict(int)
            for fix in fixes:
                # 提取实体文本
                entity = fix['old'].replace('〖%', '').replace('〗', '')
                entity_counts[entity] += 1
                all_fixes_by_entity[entity] += 1

            # 显示前5个
            for entity, cnt in sorted(entity_counts.items(), key=lambda x: -x[1])[:5]:
                print(f"  - 〖%{entity}〗 → 〖${entity}〗 ({cnt}次)")

            if len(entity_counts) > 5:
                print(f"  ... 及其他 {len(entity_counts) - 5} 种")
            print()

    print(f"{'='*60}")
    print(f"总计：{total_fixes} 处修复，涉及 {affected_chapters} 个章节")
    print(f"{'='*60}\n")

    if total_fixes > 0:
        print("🔝 Top 20 修复频次：\n")
        for entity, count in sorted(all_fixes_by_entity.items(), key=lambda x: -x[1])[:20]:
            print(f"  {entity:20s} {count:3d} 次")

        if args.dry_run:
            print(f"\n✅ 预览完成。使用 --no-dry-run 执行实际修复")
        else:
            print(f"\n✅ 修复完成！")
    else:
        print("✅ 未发现需要修复的标注")


if __name__ == '__main__':
    main()
