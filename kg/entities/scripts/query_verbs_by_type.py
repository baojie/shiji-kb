#!/usr/bin/env python3
"""
动词标注查询工具

功能：
1. 统计各类动词频次
2. 按章节分析动词分布
3. 导出动词-实体关系
4. 生成动词使用报告

用法：
  python query_verbs_by_type.py --type military              # 统计军事动词
  python query_verbs_by_type.py --type penalty               # 统计刑罚动词
  python query_verbs_by_type.py --chapter 040                # 分析040章动词
  python query_verbs_by_type.py --export relations           # 导出动词关系
  python query_verbs_by_type.py --all --report               # 生成完整报告
"""

import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHAPTER_DIR = BASE_DIR / 'chapter_md'

# 动词词表（来自 verb_taxonomy.md v3.1）
MILITARY_VERBS = {
    # 进攻类 (5)
    '伐', '攻', '击', '袭', '侵',
    # 交战类 (10)
    '战', '破', '败', '灭', '围', '下', '拔', '克', '屠', '射',
    # 俘获类 (3)
    '虏', '捕', '获',
    # 追击类 (2)
    '追', '逐',
    # 机动类 (7)
    '救', '取', '定', '降', '走', '禽', '奔', '收'
}

PENALTY_VERBS = {
    # 处决类 (14)
    '杀', '诛', '斩', '弑', '族', '戮', '刺', '夷', '阬', '殛', '烹', '亨', '僇', '劫',
    # 处罚类 (5)
    '废', '囚', '执', '笞', '刑',
    # 赦免类 (2)
    '赦', '绝',
    # 其他类 (3)
    '反', '亡', '死'
}

POLITICAL_VERBS = {
    # 册封类 (2)
    '封', '立'
}

# 刑罚制度名词（2字及以上）
PENALTY_NOUNS = {
    '斩首', '坐法', '当斩', '当死', '弃市', '死罪', '大赦',
    '族灭', '自杀', '夷三族', '车裂', '腰斩', '五刑', '连坐',
    '肉刑', '城旦', '大辟', '赎为', '赦罪', '获罪', '引兵',
    '发兵', '伏诛', '诛灭', '击破', '刺杀', '自刭', '灭口',
    '收孥', '极刑', '反间', '追击', '起兵', '赦免', '请诛',
    '诛杀', '裂地', '聚兵', '饿死', '论死', '赦令', '赎罪',
    '系狱', '下狱', '三族', '三族之罪', '夺爵', '没入'
}

ALL_VERBS = MILITARY_VERBS | PENALTY_VERBS | POLITICAL_VERBS


def extract_old_format_verbs(text):
    """提取旧格式〖[verb〗的动词标注"""
    # 匹配 〖[内容〗 格式
    pattern = r'〖\[([^〗]+)〗'
    matches = re.findall(pattern, text)

    results = {
        'military': [],
        'penalty': [],
        'legal_noun': [],
        'unknown': []
    }

    for match in matches:
        # 去除可能的消歧说明
        verb = match.split('|')[0].strip()

        if verb in MILITARY_VERBS:
            results['military'].append(match)
        elif verb in PENALTY_VERBS:
            results['penalty'].append(match)
        elif verb in PENALTY_NOUNS or len(verb) >= 2:
            results['legal_noun'].append(match)
        else:
            results['unknown'].append(match)

    return results


def extract_new_format_verbs(text):
    """提取新格式⟦TYPE动词⟧的动词标注"""
    # 匹配 ⟦◈verb⟧ 或 ⟦◉verb⟧ 格式
    pattern = r'⟦([◈◉○◇])([^⟧|]+)(?:\|[^⟧]+)?⟧'
    matches = re.findall(pattern, text)

    results = {
        'military': [],  # ◈
        'penalty': [],   # ◉
        'politics': [],  # ○
        'economy': []    # ◇
    }

    type_map = {
        '◈': 'military',
        '◉': 'penalty',
        '○': 'politics',
        '◇': 'economy'
    }

    for type_symbol, verb in matches:
        verb_type = type_map.get(type_symbol)
        if verb_type:
            results[verb_type].append(verb)

    return results


def analyze_chapter(chapter_file):
    """分析单个章节的动词使用情况"""
    with open(chapter_file, 'r', encoding='utf-8') as f:
        text = f.read()

    old_verbs = extract_old_format_verbs(text)
    new_verbs = extract_new_format_verbs(text)

    return {
        'chapter': chapter_file.stem,
        'old_format': old_verbs,
        'new_format': new_verbs,
        'total_old': sum(len(v) for v in old_verbs.values()),
        'total_new': sum(len(v) for v in new_verbs.values())
    }


def analyze_all_chapters():
    """分析所有章节"""
    results = []

    for chapter_file in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        result = analyze_chapter(chapter_file)
        results.append(result)

    return results


def generate_frequency_report(results):
    """生成动词频次报告"""
    # 统计所有旧格式动词
    military_counter = Counter()
    penalty_counter = Counter()
    legal_counter = Counter()
    unknown_counter = Counter()

    for result in results:
        old = result['old_format']
        military_counter.update(old['military'])
        penalty_counter.update(old['penalty'])
        legal_counter.update(old['legal_noun'])
        unknown_counter.update(old['unknown'])

    print("=" * 60)
    print("动词频次统计报告（旧格式 〖[verb〗）")
    print("=" * 60)

    print("\n【军事动词】Top 20")
    print(f"{'动词':<10} {'频次':>8} {'占比':>8}")
    print("-" * 30)
    total_military = sum(military_counter.values())
    for verb, count in military_counter.most_common(20):
        pct = count / total_military * 100 if total_military > 0 else 0
        print(f"{verb:<10} {count:>8} {pct:>7.1f}%")
    print(f"\n总计: {total_military} 次")

    print("\n【刑罚动词】Top 20")
    print(f"{'动词':<10} {'频次':>8} {'占比':>8}")
    print("-" * 30)
    total_penalty = sum(penalty_counter.values())
    for verb, count in penalty_counter.most_common(20):
        pct = count / total_penalty * 100 if total_penalty > 0 else 0
        print(f"{verb:<10} {count:>8} {pct:>7.1f}%")
    print(f"\n总计: {total_penalty} 次")

    print("\n【刑罚制度名词】Top 20")
    print(f"{'名词':<15} {'频次':>8}")
    print("-" * 30)
    for noun, count in legal_counter.most_common(20):
        print(f"{noun:<15} {count:>8}")
    print(f"\n总计: {sum(legal_counter.values())} 次")

    if unknown_counter:
        print("\n【未分类词汇】Top 10")
        print(f"{'词汇':<15} {'频次':>8}")
        print("-" * 30)
        for word, count in unknown_counter.most_common(10):
            print(f"{word:<15} {count:>8}")
        print(f"\n总计: {sum(unknown_counter.values())} 次")

    print("\n" + "=" * 60)
    print(f"总体统计:")
    print(f"  军事动词: {total_military} 次")
    print(f"  刑罚动词: {total_penalty} 次")
    print(f"  刑罚制度: {sum(legal_counter.values())} 次")
    if unknown_counter:
        print(f"  未分类: {sum(unknown_counter.values())} 次")
    print("=" * 60)


def generate_chapter_report(results, chapter_num=None):
    """生成章节动词分布报告"""
    if chapter_num:
        results = [r for r in results if r['chapter'].startswith(f'{chapter_num:03d}_')]

    print("=" * 60)
    print("章节动词分布报告")
    print("=" * 60)

    print(f"\n{'章节':<30} {'军事':>6} {'刑罚':>6} {'制度':>6} {'总计':>6}")
    print("-" * 60)

    for result in results:
        chapter = result['chapter']
        old = result['old_format']

        mil_count = len(old['military'])
        pen_count = len(old['penalty'])
        leg_count = len(old['legal_noun'])
        total = mil_count + pen_count + leg_count

        if chapter_num is None and total < 10:
            continue  # 跳过动词较少的章节

        print(f"{chapter:<30} {mil_count:>6} {pen_count:>6} {leg_count:>6} {total:>6}")

    print("-" * 60)

    # 总计
    total_mil = sum(len(r['old_format']['military']) for r in results)
    total_pen = sum(len(r['old_format']['penalty']) for r in results)
    total_leg = sum(len(r['old_format']['legal_noun']) for r in results)
    grand_total = total_mil + total_pen + total_leg

    print(f"{'总计':<30} {total_mil:>6} {total_pen:>6} {total_leg:>6} {grand_total:>6}")
    print("=" * 60)


def export_verb_relations(results, output_file):
    """导出动词-实体关系到文件"""
    output_path = BASE_DIR / output_file

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 动词-实体关系导出\n\n")
        f.write("## 数据说明\n\n")
        f.write("本文件包含从《史记》标注文本中提取的动词及其上下文实体关系。\n\n")

        for result in results:
            chapter = result['chapter']
            chapter_file = CHAPTER_DIR / f"{chapter}.md"

            if not chapter_file.exists():
                continue

            with open(chapter_file, 'r', encoding='utf-8') as cf:
                text = cf.read()

            # 查找动词及其上下文（前后各20字）
            pattern = r'(.{0,20})〖\[([^〗]+)〗(.{0,20})'
            matches = re.finditer(pattern, text)

            chapter_verbs = []
            for match in matches:
                before, verb, after = match.groups()
                verb_clean = verb.split('|')[0].strip()

                if verb_clean in ALL_VERBS:
                    chapter_verbs.append({
                        'verb': verb_clean,
                        'context': f"{before}【{verb}】{after}"
                    })

            if chapter_verbs:
                f.write(f"\n## {chapter}\n\n")
                for item in chapter_verbs:
                    f.write(f"- `{item['verb']}`: {item['context']}\n")

    print(f"\n动词关系已导出到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='动词标注查询工具')
    parser.add_argument('--type', choices=['military', 'penalty', 'all'],
                        help='查询动词类型')
    parser.add_argument('--chapter', type=int, metavar='NNN',
                        help='分析指定章节（如 040）')
    parser.add_argument('--export', metavar='FILE',
                        help='导出动词关系到文件')
    parser.add_argument('--report', action='store_true',
                        help='生成完整报告')
    parser.add_argument('--all', action='store_true',
                        help='分析所有章节')

    args = parser.parse_args()

    # 分析章节
    if args.chapter:
        chapter_files = list(CHAPTER_DIR.glob(f'{args.chapter:03d}_*.tagged.md'))
        if not chapter_files:
            print(f"错误: 未找到章节 {args.chapter:03d}")
            sys.exit(1)
        results = [analyze_chapter(chapter_files[0])]
    else:
        results = analyze_all_chapters()

    # 执行查询
    if args.type:
        generate_frequency_report(results)

    if args.chapter or args.report:
        generate_chapter_report(results, args.chapter)

    if args.export:
        export_verb_relations(results, args.export)

    if not any([args.type, args.chapter, args.export, args.report]):
        print("请指定操作参数，使用 --help 查看帮助")
        sys.exit(1)


if __name__ == '__main__':
    main()
