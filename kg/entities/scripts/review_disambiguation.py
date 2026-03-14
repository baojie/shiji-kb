#!/usr/bin/env python3
"""实体消歧+别名反思审查工具 — 分析各章人名标注、消歧和别名状态。

用法:
  python kg/entities/scripts/review_disambiguation.py          # 分析全部130章
  python kg/entities/scripts/review_disambiguation.py 001      # 分析指定章
  python kg/entities/scripts/review_disambiguation.py 001-010  # 分析范围
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[3]
CHAPTER_DIR = ROOT / "chapter_md"
DM_PATH = ROOT / "kg/entities/data/disambiguation_map.json"
ALIAS_PATH = ROOT / "kg/entities/data/entity_aliases.json"

# 从disambiguate_names.py中提取RULER_DB
def load_ruler_db():
    """从disambiguate_names.py加载RULER_DB，提取所有歧义短名"""
    script = ROOT / "kg/entities/scripts/disambiguate_names.py"
    if not script.exists():
        return set()
    text = script.read_text()
    names = set()
    for m in re.finditer(r"\('([^']+)',\s*'[^']+'\)", text):
        names.add(m.group(1))
    return names


def load_alias_maps():
    """加载别名数据，构建双向映射"""
    aliases = json.loads(ALIAS_PATH.read_text())
    person_aliases = aliases.get('person', {})
    # canonical → [aliases]
    canon_to_aliases = {}
    # any_name → canonical
    name_to_canon = {}
    for canon, alias_list in person_aliases.items():
        canon_to_aliases[canon] = alias_list
        name_to_canon[canon] = canon
        for alias in alias_list:
            name_to_canon[alias] = canon
    return canon_to_aliases, name_to_canon


# 不需消歧的名称
SKIP_NAMES = {
    '黄帝', '炎帝', '孝文帝', '孝景帝', '孝武帝',
    '太后', '太公', '周公', '太子',
}

# 已知的常见误标模式（字在特定语境中非人名）
FALSE_POSITIVE_PATTERNS = [
    # (name, context_pattern, explanation)
    ('象', r'以.{0,2}〖@象〗天', '象=动词"效法"，非人名'),
    ('益', r'皆〖@益〗笃', '益=副词"更加"，非人名'),
    ('益', r'〖@益〗盛', '益=副词"更加"，非人名'),
    ('益', r'〖@益〗强', '益=副词"更加"，非人名'),
    ('益', r'〖@益〗弱', '益=副词"更加"，非人名'),
    ('益', r'日〖@益〗', '益=副词"更加"，非人名'),
]


def extract_person_tags(text):
    """提取所有〖@人名〗标记及其位置（v2.1格式）"""
    results = []
    for m in re.finditer(r'〖@([^〖〗\n]+)〗', text):
        results.append((m.group(1), m.start(), m.end()))
    return results


def find_false_positives(text, persons):
    """检测可能的误标"""
    issues = []
    for name, pos, end in persons:
        for fp_name, fp_pattern, fp_explain in FALSE_POSITIVE_PATTERNS:
            if name == fp_name:
                context = text[max(0, pos-10):min(len(text), end+10)]
                if re.search(fp_pattern, context):
                    line_num = text[:pos].count('\n') + 1
                    issues.append((name, line_num, context.strip(), fp_explain))
    return issues


def find_ambiguous_without_disambiguation(persons, chapter_id, dm, ambiguous_names):
    """找到出现了歧义短名但未在disambiguation_map中的情况"""
    chapter_dm = dm.get(chapter_id, {})
    missing = []
    for name, pos, end in persons:
        if name in ambiguous_names and name not in chapter_dm and name not in SKIP_NAMES:
            missing.append(name)
    return list(set(missing))


def find_alias_groups_in_chapter(name_counts, name_to_canon, canon_to_aliases):
    """找出章节中属于同一别名组的名称"""
    # 按canonical name分组
    groups = defaultdict(list)
    for name in name_counts:
        if name in name_to_canon:
            canon = name_to_canon[name]
            groups[canon].append((name, name_counts[name]))

    # 只返回有2+名称出现的组（即章内有别名关系）
    multi_groups = {}
    for canon, members in groups.items():
        if len(members) >= 2:
            multi_groups[canon] = members
    return multi_groups


def find_missing_alias_entries(name_counts, name_to_canon, canon_to_aliases):
    """找出章节中出现但不在别名系统中的名称对
    - 同一人物的不同称谓都出现了，但别名系统中没有关联
    """
    # 检查：名称出现在文本中但不在name_to_canon中的
    unknown_names = [n for n in name_counts if n not in name_to_canon]
    return unknown_names


def analyze_chapter(chapter_id, dm, ambiguous_names, name_to_canon, canon_to_aliases):
    """分析单章消歧+别名状态"""
    pattern = f"{chapter_id}_*.tagged.md"
    files = list(CHAPTER_DIR.glob(pattern))
    if not files:
        return None

    fpath = files[0]
    chapter_name = fpath.stem.replace('.tagged', '').split('_', 1)[1]
    text = fpath.read_text()

    persons = extract_person_tags(text)
    name_counts = Counter(name for name, _, _ in persons)
    unique_names = sorted(name_counts.keys())

    # 消歧分析
    ambiguous_found = [n for n in unique_names if n in ambiguous_names]
    chapter_dm = dm.get(chapter_id, {})
    missing_disambig = find_ambiguous_without_disambiguation(persons, chapter_id, dm, ambiguous_names)

    # 误标检测
    false_positives = find_false_positives(text, persons)

    # 幽灵条目（消歧映射中有但文本中不存在的）
    phantom_entries = []
    for name in chapter_dm:
        if name not in name_counts:
            phantom_entries.append((name, chapter_dm[name]))

    # 别名分析
    alias_groups = find_alias_groups_in_chapter(name_counts, name_to_canon, canon_to_aliases)
    unknown_names = find_missing_alias_entries(name_counts, name_to_canon, canon_to_aliases)

    return {
        'chapter_id': chapter_id,
        'chapter_name': chapter_name,
        'total_tags': len(persons),
        'unique_names': len(unique_names),
        'name_counts': name_counts,
        'ambiguous_found': ambiguous_found,
        'disambiguation_map': chapter_dm,
        'missing_disambig': missing_disambig,
        'false_positives': false_positives,
        'phantom_entries': phantom_entries,
        'alias_groups': alias_groups,
        'unknown_names': unknown_names,
    }


def format_report(result):
    """格式化单章报告"""
    r = result
    lines = []
    lines.append(f"### {r['chapter_id']} {r['chapter_name']}")
    lines.append(f"")
    lines.append(f"- 人名标记：{r['total_tags']}处，{r['unique_names']}个不同人名")

    # 消歧部分
    if r['ambiguous_found']:
        lines.append(f"- 歧义短名出现：{', '.join(r['ambiguous_found'])}")
    else:
        lines.append(f"- 歧义短名：无")

    if r['disambiguation_map']:
        dm_str = ', '.join(f"{k}→{v}" for k, v in r['disambiguation_map'].items())
        lines.append(f"- 当前消歧映射：{dm_str}")

    # 别名部分
    if r['alias_groups']:
        lines.append(f"- 别名组（章内多称谓）：")
        for canon, members in sorted(r['alias_groups'].items()):
            member_str = ', '.join(f"{n}({c})" for n, c in sorted(members, key=lambda x: -x[1]))
            lines.append(f"  - {canon}：{member_str}")

    if r['unknown_names']:
        lines.append(f"- 未入别名系统：{', '.join(sorted(r['unknown_names']))}")

    # 问题
    issues = []
    if r['missing_disambig']:
        issues.append(f"缺失消歧：{', '.join(r['missing_disambig'])}")
    if r['false_positives']:
        for name, line, ctx, explain in r['false_positives']:
            issues.append(f"误标(L{line})：〖@{name}〗 — {explain}")
    if r['phantom_entries']:
        for name, full in r['phantom_entries']:
            issues.append(f"幽灵条目：{name}→{full}（文本中无此标记）")

    if issues:
        lines.append(f"- 问题：")
        for issue in issues:
            lines.append(f"  - {issue}")
        lines.append(f"- 结论：需修正")
    else:
        lines.append(f"- 结论：正常")

    lines.append("")
    return '\n'.join(lines)


def main():
    dm = json.loads(DM_PATH.read_text())
    ambiguous_names = load_ruler_db()
    canon_to_aliases, name_to_canon = load_alias_maps()

    if not ambiguous_names:
        print("WARNING: 无法加载RULER_DB，歧义短名列表为空")
    else:
        print(f"已加载 {len(ambiguous_names)} 个歧义短名")
    print(f"已加载 {len(canon_to_aliases)} 个别名组，{len(name_to_canon)} 个名称映射")
    print()

    # 解析参数
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if '-' in arg and len(arg) == 7:  # 001-010
            start, end = arg.split('-')
            chapters = [f"{i:03d}" for i in range(int(start), int(end)+1)]
        else:
            chapters = [arg.zfill(3)]
    else:
        chapters = [f"{i:03d}" for i in range(1, 131)]

    # 分析
    all_results = []
    issues_count = 0
    for ch in chapters:
        result = analyze_chapter(ch, dm, ambiguous_names, name_to_canon, canon_to_aliases)
        if result:
            all_results.append(result)
            report = format_report(result)
            print(report)
            if result['missing_disambig'] or result['false_positives'] or result['phantom_entries']:
                issues_count += 1

    # 汇总
    if len(all_results) > 1:
        print("---")
        print(f"## 汇总")
        print(f"- 分析章节：{len(all_results)}")
        print(f"- 有问题章节：{issues_count}")
        total_ambig = sum(len(r['ambiguous_found']) for r in all_results)
        total_mapped = sum(len(r['disambiguation_map']) for r in all_results)
        total_alias_groups = sum(len(r['alias_groups']) for r in all_results)
        total_unknown = sum(len(r['unknown_names']) for r in all_results)
        print(f"- 歧义短名出现：{total_ambig}处")
        print(f"- 已有消歧映射：{total_mapped}条")
        print(f"- 章内别名组：{total_alias_groups}组")
        print(f"- 未入别名系统名称：{total_unknown}个")

        # 缺失消歧汇总
        all_missing = []
        for r in all_results:
            for name in r['missing_disambig']:
                all_missing.append((r['chapter_id'], name))
        if all_missing:
            print(f"\n### 缺失消歧明细")
            for ch, name in sorted(all_missing):
                print(f"  - {ch}: {name}")

        # 未入别名系统的高频名称
        unknown_counter = Counter()
        for r in all_results:
            for name in r['unknown_names']:
                unknown_counter[name] += 1
        if unknown_counter:
            print(f"\n### 未入别名系统的高频名称（出现在2+章）")
            for name, count in unknown_counter.most_common():
                if count >= 2:
                    print(f"  - {name}（{count}章）")


if __name__ == '__main__':
    main()
