#!/usr/bin/env python3
"""
修复 tagged.md 文件中的破损 @...@ 标记。

核心问题：@Title@PersonalName@ 三连@ — 封号/谥号与名字之间多了一个@。
修复策略分两层：
  Layer 1: $@X@Y@$ 模式 — $ 明确界定了实体边界，合并为 $@XY@$
  Layer 2: @X@Y@ 模式 — X+Y 在已知实体库中，合并为 @XY@
"""

import re
import json
import os
from pathlib import Path

# === 数据加载 ===
def load_known_entities():
    """从 entity_aliases.json 加载所有已知人名"""
    alias_path = Path(__file__).parent.parent / 'data' / 'entity_aliases.json'
    names = set()
    if alias_path.exists():
        with open(alias_path) as f:
            data = json.load(f)
        for entity_type, groups in data.items():
            for canonical, aliases in groups.items():
                names.add(canonical)
                for a in aliases:
                    names.add(a)
    return names

# === Layer 1: $@X@Y@$ 模式 ===
# $ 可以是 $ 或行首/行尾的上下文边界
DOLLAR_WRAP_RE = re.compile(r'\$@([^@$\n]+)@([^@$\n]+)@\$')

def find_dollar_wrap_merges(line):
    """找到 $@X@Y@$ 模式"""
    fixes = []
    for m in DOLLAR_WRAP_RE.finditer(line):
        text1, text2 = m.group(1), m.group(2)
        # text1+text2 应合理（不含标点等）
        combined = text1 + text2
        if len(combined) <= 12 and not any(c in combined for c in '，。、；：'):
            fixes.append({
                'start': m.start(),
                'end': m.end(),
                'old': m.group(0),
                'new': f'$@{combined}@$',
                'text1': text1,
                'text2': text2,
                'layer': 1,
            })
    return fixes


# === Layer 2: @Title@Name@ 不在 $ 内 ===
TITLE_SUFFIXES = ('王', '侯', '公', '伯', '君', '帝', '后', '将军', '丞相',
                  '太后', '夫人', '太子', '世子', '长公主', '公主',
                  '令尹', '司马', '太尉', '相国', '大夫', '将')

def is_clean_title(text):
    """判断 text 是否为干净的封号/谥号"""
    if not text or len(text) < 2 or len(text) > 8:
        return False
    for c in text:
        if not ('\u4e00' <= c <= '\u9fff'):
            return False
    return any(text.endswith(s) for s in TITLE_SUFFIXES)

def find_bare_triple_merges(line, known_entities):
    """找到 @Title@Name@ 模式：text1 是封号，text2 是已知人名"""
    fixes = []
    at_positions = [i for i, c in enumerate(line) if c == '@']
    if len(at_positions) < 3:
        return fixes

    i = 0
    while i < len(at_positions) - 2:
        p1, p2, p3 = at_positions[i], at_positions[i+1], at_positions[i+2]
        text1 = line[p1+1:p2]
        text2 = line[p2+1:p3]

        if not text1 or not text2:
            i += 1
            continue

        # 跳过已被 Layer 1 处理的（前面有$）
        if p1 > 0 and line[p1-1] == '$':
            i += 1
            continue

        # text1 是封号 + text2 是已知人名 → 合并
        if is_clean_title(text1) and text2 in known_entities:
            fixes.append({
                'start': p1,
                'end': p3 + 1,
                'old': line[p1:p3+1],
                'new': f'@{text1}{text2}@',
                'text1': text1,
                'text2': text2,
                'layer': 2,
            })
            i += 3
        # 合并形式本身是已知实体
        elif text1 + text2 in known_entities:
            fixes.append({
                'start': p1,
                'end': p3 + 1,
                'old': line[p1:p3+1],
                'new': f'@{text1}{text2}@',
                'text1': text1,
                'text2': text2,
                'layer': 2,
            })
            i += 3
        else:
            i += 1

    return fixes


# === Layer 3: $Title@@Name@$ 模式 — $@ 混用 ===
# $Title@ 应该是 $Title$，然后 @Name@ 是独立标记
DOUBLE_AT_RE = re.compile(r'\$([^@$\n]{1,6})@@([^@$\n]{1,6})@\$')

def find_double_at_fixes(line):
    """找到 $X@@Y@$ 模式，修复为 $X$@Y@$"""
    fixes = []
    for m in DOUBLE_AT_RE.finditer(line):
        title, name = m.group(1), m.group(2)
        # 验证 title 和 name 是中文
        if all('\u4e00' <= c <= '\u9fff' for c in title + name):
            fixes.append({
                'start': m.start(),
                'end': m.end(),
                'old': m.group(0),
                'new': f'${title}$@{name}@$',
                'text1': title,
                'text2': name,
                'layer': 3,
            })
    return fixes


# === Layer 4: 奇数@行的三连@修复 ===
def find_odd_line_triple_fixes(line, known_entities):
    """对奇数@行，找到三连@中text2为已知实体的模式进行合并"""
    at_count = line.count('@')
    if at_count % 2 == 0 or at_count < 3:
        return []

    fixes = []
    at_positions = [i for i, c in enumerate(line) if c == '@']

    # 找三连@ groups
    candidates = []
    i = 0
    while i < len(at_positions) - 2:
        p1, p2, p3 = at_positions[i], at_positions[i+1], at_positions[i+2]
        text1 = line[p1+1:p2]
        text2 = line[p2+1:p3]

        if (text1 and text2 and
            len(text1) <= 8 and len(text2) <= 6 and
            all('\u4e00' <= c <= '\u9fff' for c in text2) and
            not any(c in text1 for c in '$&=%*^~，。、；：')):

            # text2 是已知实体 → 合并
            if text2 in known_entities:
                candidates.append({
                    'start': p1,
                    'end': p3 + 1,
                    'old': line[p1:p3+1],
                    'new': f'@{text1}{text2}@',
                    'text1': text1,
                    'text2': text2,
                    'layer': 4,
                    'priority': 1,
                })
            # text1+text2 看起来像 "X弟Y" / "X子Y" 等关系描述
            elif any(text1.endswith(r) for r in ('弟', '子', '母', '孙', '妻', '女')):
                candidates.append({
                    'start': p1,
                    'end': p3 + 1,
                    'old': line[p1:p3+1],
                    'new': f'@{text1}{text2}@',
                    'text1': text1,
                    'text2': text2,
                    'layer': 4,
                    'priority': 2,
                })
        i += 1

    # 如果只有一个候选，直接用
    if len(candidates) == 1:
        fixes.append(candidates[0])
    elif candidates:
        # 多个候选时，优先选 priority=1 的
        p1_cands = [c for c in candidates if c['priority'] == 1]
        if len(p1_cands) == 1:
            fixes.append(p1_cands[0])

    return fixes


# === Layer 5: 常见标记混用模式 ===
# Pattern A: $Name@ 应为 @Name@ — $ 误用为 @
# 出现在 $$Name@ 或句首 $Name@ 形式
DOLLAR_AS_AT_RE = re.compile(r'\$\$([^\u0040\$\n]{1,6})\u0040')

# Pattern B: @...弑其君Name@ → @...弑其君@Name@ (缺少@)
# "弑其君" 后面的人名应有自己的 @ 标记
KILL_LORD_RE = re.compile(r'(弑其[君主])([\u4e00-\u9fff]{1,4})\u0040')

# Pattern C: $内史X@ 类 — $Title+Name@ 应为 $Title$@Name@
TITLE_NAME_DOLLAR_AT_RE = re.compile(
    r'\$((?:内史|太史|大夫|丞相|将军|司马|太尉|御史|相国|令尹|太傅|少傅|郎中令|廷尉|'
    r'中尉|卫尉|太仆|宗正|少府|治粟内史|典客|奉常|太常|大行|中大夫|光禄大夫)'
    r'[\u4e00-\u9fff]{1,4})\u0040'
)

def find_misc_fixes(line):
    """Layer 5: 修复常见标记混用"""
    fixes = []

    # Pattern A: $$Name@ → $@Name@
    for m in DOLLAR_AS_AT_RE.finditer(line):
        name = m.group(1)
        if all('\u4e00' <= c <= '\u9fff' for c in name):
            fixes.append({
                'start': m.start(),
                'end': m.end(),
                'old': m.group(0),
                'new': f'$@{name}@',
                'text1': '$→@',
                'text2': name,
                'layer': 5,
            })

    # Pattern B: 弑其君Name@ → 弑其君@Name@
    for m in KILL_LORD_RE.finditer(line):
        prefix, name = m.group(1), m.group(2)
        if all('\u4e00' <= c <= '\u9fff' for c in name):
            fixes.append({
                'start': m.start(),
                'end': m.end(),
                'old': m.group(0),
                'new': f'{prefix}@{name}@',
                'text1': prefix,
                'text2': name,
                'layer': 5,
            })

    return fixes


# === 破损检测 ===
SPECIAL_CHARS = set('$&=%*^~')
TAG_RE = re.compile(r'@([^@\n]+?)@')

def is_broken_capture(content):
    if any(c in content for c in SPECIAL_CHARS):
        return True
    if any(c in content for c in '，。、；：！？（）「」『』""'''):
        return True
    if len(content) > 8:
        return True
    return False

def count_broken_captures(line):
    return sum(1 for m in TAG_RE.finditer(line) if is_broken_capture(m.group(1)))


def apply_fixes_to_line(line, fixes):
    """从后向前应用修复"""
    for f in sorted(fixes, key=lambda x: x['start'], reverse=True):
        line = line[:f['start']] + f['new'] + line[f['end']:]
    return line


# === 主流程 ===
def scan_file(filepath, known_entities, fix=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    all_fixes = []
    modified_lines = list(lines)

    for line_no, line in enumerate(lines, 1):
        stripped = line.rstrip('\n')

        # Layer 1: $@X@Y@$ → $@XY@$
        l1_fixes = find_dollar_wrap_merges(stripped)
        test_line = apply_fixes_to_line(stripped, l1_fixes) if l1_fixes else stripped

        # Layer 2: @Title@KnownName@ → @TitleKnownName@
        l2_fixes = find_bare_triple_merges(test_line, known_entities)
        test_line = apply_fixes_to_line(test_line, l2_fixes) if l2_fixes else test_line

        # Layer 3: $Title@@Name@$ → $Title$@Name@$
        l3_fixes = find_double_at_fixes(test_line)
        test_line = apply_fixes_to_line(test_line, l3_fixes) if l3_fixes else test_line

        # Layer 4: odd-@ line triple-@ fix
        l4_fixes = find_odd_line_triple_fixes(test_line, known_entities)
        test_line = apply_fixes_to_line(test_line, l4_fixes) if l4_fixes else test_line

        # Layer 5: misc marker fixes
        l5_fixes = find_misc_fixes(test_line)
        test_line = apply_fixes_to_line(test_line, l5_fixes) if l5_fixes else test_line

        all_layer_fixes = l1_fixes + l2_fixes + l3_fixes + l4_fixes + l5_fixes
        for f in all_layer_fixes:
            all_fixes.append({
                'line': line_no,
                'type': f'layer{f["layer"]}_merge',
                'old': f['old'],
                'new': f['new'],
                'detail': f"{f['text1']} + {f['text2']}",
            })

        broken_count = count_broken_captures(test_line)
        if broken_count > 0:
            all_fixes.append({
                'line': line_no,
                'type': 'broken_remaining',
                'count': broken_count,
            })

    if fix:
        for line_no, line in enumerate(lines, 1):
            new_line = line
            # Apply layers sequentially, re-finding each on updated line
            l1 = find_dollar_wrap_merges(new_line.rstrip('\n'))
            if l1:
                new_line = apply_fixes_to_line(new_line, l1)
            l2 = find_bare_triple_merges(new_line.rstrip('\n'), known_entities)
            if l2:
                new_line = apply_fixes_to_line(new_line, l2)
            l3 = find_double_at_fixes(new_line.rstrip('\n'))
            if l3:
                new_line = apply_fixes_to_line(new_line, l3)
            l4 = find_odd_line_triple_fixes(new_line.rstrip('\n'), known_entities)
            if l4:
                new_line = apply_fixes_to_line(new_line, l4)
            l5 = find_misc_fixes(new_line.rstrip('\n'))
            if l5:
                new_line = apply_fixes_to_line(new_line, l5)
            modified_lines[line_no - 1] = new_line

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)

    return all_fixes


def main():
    import argparse
    parser = argparse.ArgumentParser(description='修复tagged.md中的破损@标记')
    parser.add_argument('--scan', action='store_true', help='仅扫描，不修复')
    parser.add_argument('--fix', action='store_true', help='应用修复')
    parser.add_argument('--chapter', type=str, help='指定章节号')
    parser.add_argument('--summary', action='store_true', help='仅显示汇总')
    args = parser.parse_args()

    known_entities = load_known_entities()
    print(f"已加载 {len(known_entities)} 个已知实体名")

    chapter_dir = Path(__file__).parent.parent.parent.parent / 'chapter_md'

    if args.chapter:
        files = sorted(chapter_dir.glob(f'{args.chapter}_*.tagged.md'))
    else:
        files = sorted(chapter_dir.glob('*_*.tagged.md'))

    totals = {'l1': 0, 'l2': 0, 'l3': 0, 'l4': 0, 'l5': 0, 'broken': 0}
    chapter_stats = []

    for f in files:
        chapter = f.name[:3]
        fixes = scan_file(f, known_entities, fix=args.fix)

        counts = {}
        for layer in [1, 2, 3, 4, 5]:
            counts[f'l{layer}'] = len([x for x in fixes if x['type'] == f'layer{layer}_merge'])
        broken = [x for x in fixes if x['type'] == 'broken_remaining']
        counts['broken'] = sum(x['count'] for x in broken)
        total_fixes = sum(counts[f'l{i}'] for i in [1,2,3,4,5])

        if total_fixes or counts['broken']:
            chapter_stats.append((chapter, f.stem[4:], counts))
            for k in totals:
                totals[k] += counts.get(k, 0)

            if not args.summary:
                print(f"\n=== {f.name} ===")
                for layer in [1, 2, 3, 4, 5]:
                    layer_fixes = [x for x in fixes if x['type'] == f'layer{layer}_merge']
                    if layer_fixes:
                        labels = {1: '$@X@Y@$', 2: 'Title+Known', 3: '$X@@Y@$', 4: 'OddLine', 5: 'MiscFix'}
                        print(f"  {labels[layer]} ({len(layer_fixes)}):")
                        for t in layer_fixes:
                            print(f"    L{t['line']}: {t['old']} → {t['new']}")
                if counts['broken']:
                    print(f"  剩余破损: {counts['broken']}")

    total_fixes = sum(totals[f'l{i}'] for i in [1,2,3,4,5])
    print(f"\n{'='*50}")
    print(f"总计: {len(chapter_stats)} 章")
    print(f"  L1 $@X@Y@$: {totals['l1']}")
    print(f"  L2 Title+Known: {totals['l2']}")
    print(f"  L3 $X@@Y@$: {totals['l3']}")
    print(f"  L4 OddLine: {totals['l4']}")
    print(f"  L5 MiscFix: {totals['l5']}")
    print(f"  合计修复: {total_fixes}")
    print(f"  剩余破损: {totals['broken']}")

    if args.summary and chapter_stats:
        print(f"\n{'章节':<6} {'名称':<20} {'L1':>4} {'L2':>4} {'L3':>4} {'L4':>4} {'L5':>4} {'破损':>5}")
        print('-' * 60)
        for ch, name, c in sorted(chapter_stats, key=lambda x: sum(x[2].values()), reverse=True):
            print(f"{ch:<6} {name:<20} {c['l1']:>4} {c['l2']:>4} {c['l3']:>4} {c['l4']:>4} {c['l5']:>4} {c['broken']:>5}")

    if args.fix:
        print(f"\n已应用 {total_fixes} 处修复")


if __name__ == '__main__':
    main()
