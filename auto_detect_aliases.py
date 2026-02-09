#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动检测人名别名候选，扩充 entity_aliases.json

策略：
1. 全名包含简称（如"秦庄襄王"包含"庄襄王"），且同章节出现
   - 只有当短名唯一映射到一个长名时才自动确认（避免歧义）
2. "帝X"和"X"的映射（殷商帝王专用模式）
3. 同姓候选仅供参考输出，不自动合并

安全措施：
- 过滤包含标记符号的垃圾条目
- 排除通用称谓（太后、太子、公子、夫人等）
- 歧义短名（映射到多个长名）不自动确认
"""

import re
import json
from pathlib import Path
from collections import defaultdict

CHAPTER_DIR = Path('chapter_md')
ALIAS_FILE = Path('entity_aliases.json')
PERSON_PATTERN = r'@([^@\n]+)@'

# 标记符号，含这些字符的不是合法人名
INVALID_CHARS = set('$&=%~*!?🌿，。、；：""''（）《》【】·')

# 通用称谓/职衔，不能作为别名（太泛泛，在不同章节指不同人）
GENERIC_TITLES = {
    '太后', '太子', '公子', '夫人', '将军', '丞相', '大夫',
    '皇后', '王后', '天子', '诸侯', '大王', '君', '臣',
    '太史', '太师', '太傅', '少傅', '御史', '舍人',
    '公主', '王孙', '世子',
}


def is_valid_name(name):
    """检查是否是合法的人名（纯汉字，无标记符号）"""
    if not name or len(name) < 2:
        return False
    for ch in name:
        if ch in INVALID_CHARS:
            return False
    # 检查是否全是汉字（允许少数非汉字如"·"已在INVALID_CHARS中排除）
    for ch in name:
        if not ('\u4e00' <= ch <= '\u9fff'):
            return False
    return True


def extract_persons_by_chapter():
    """提取每个章节中出现的人名集合"""
    chapter_persons = defaultdict(set)
    person_chapters = defaultdict(set)

    for fpath in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        chapter_id = fpath.stem.replace('.tagged', '')
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        for m in re.finditer(PERSON_PATTERN, content):
            name = m.group(1).strip()
            if is_valid_name(name):
                chapter_persons[chapter_id].add(name)
                person_chapters[name].add(chapter_id)

    return chapter_persons, person_chapters


def load_existing_aliases():
    """加载现有别名映射"""
    if not ALIAS_FILE.exists():
        return set(), {}
    with open(ALIAS_FILE, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    known = set()
    for canonical, aliases in raw.get('person', {}).items():
        known.add(canonical)
        for a in aliases:
            if a:
                known.add(a)
    return known, raw


def find_prefix_aliases(chapter_persons, person_chapters):
    """
    找全名包含简称的候选。
    关键改进：按短名分组，只有短名唯一对应一个长名才可自动确认。
    """
    all_names = set()
    for names in chapter_persons.values():
        all_names.update(names)

    # 按长度排序
    names_list = sorted(all_names, key=len, reverse=True)

    # 收集所有 (长名, 短名) 对
    raw_pairs = []  # (long_name, short_name, common_chapter_count)
    checked = set()
    for long_name in names_list:
        if len(long_name) < 3:
            continue
        for short_name in names_list:
            if len(short_name) < 2 or len(short_name) >= len(long_name):
                continue
            if short_name == long_name:
                continue
            pair = (long_name, short_name)
            if pair in checked:
                continue
            checked.add(pair)

            # 短名必须是合法人名
            if short_name in GENERIC_TITLES:
                continue

            # 检查包含关系
            if short_name not in long_name:
                continue

            # 检查是否同章节出现
            common_chapters = person_chapters[long_name] & person_chapters[short_name]
            if not common_chapters:
                continue

            raw_pairs.append((long_name, short_name, len(common_chapters)))

    # 按短名分组：短名 → [(长名, count), ...]
    short_to_longs = defaultdict(list)
    for long_name, short_name, count in raw_pairs:
        short_to_longs[short_name].append((long_name, count))

    # 分类：唯一映射 vs 歧义映射
    unique_pairs = []    # 可自动确认
    ambiguous = []       # 需人工确认

    for short_name, longs in short_to_longs.items():
        if len(longs) == 1:
            long_name, count = longs[0]
            unique_pairs.append((long_name, short_name, count))
        else:
            ambiguous.append((short_name, longs))

    return unique_pairs, ambiguous


def find_di_prefix_aliases(person_chapters):
    """找"帝X"和"X"的候选（殷商帝王模式）"""
    candidates = []
    for name in person_chapters:
        if name.startswith('帝') and len(name) >= 3 and is_valid_name(name):
            short = name[1:]
            if short in person_chapters and is_valid_name(short):
                # 确保短名不在 GENERIC_TITLES 中
                if short in GENERIC_TITLES:
                    continue
                common = person_chapters[name] & person_chapters[short]
                if common:
                    candidates.append((name, short, len(common)))
    return candidates


def find_surname_aliases(chapter_persons, person_chapters):
    """找共享姓氏的候选（仅供参考）"""
    candidates = []
    all_names = set()
    for names in chapter_persons.values():
        all_names.update(names)

    by_surname = defaultdict(list)
    for name in all_names:
        if is_valid_name(name) and len(name) >= 2:
            by_surname[name[0]].append(name)

    for surname, names in by_surname.items():
        if len(names) < 2:
            continue
        for i, n1 in enumerate(names):
            for n2 in names[i+1:]:
                if n1 == n2:
                    continue
                if len(n1) > 4 or len(n2) > 4:
                    continue
                # 排除已有包含关系的（由prefix策略处理）
                if n1 in n2 or n2 in n1:
                    continue
                common = person_chapters[n1] & person_chapters[n2]
                if not common:
                    continue
                candidates.append((n1, n2, len(common)))

    return candidates


def merge_into_aliases(existing_raw, confirmed_pairs):
    """将确认的别名对合并入现有 aliases 数据"""
    person_aliases = existing_raw.get('person', {})

    # 建立反向索引
    reverse = {}
    for canonical, aliases in person_aliases.items():
        reverse[canonical] = canonical
        for a in aliases:
            if a:
                reverse[a] = canonical

    for long_name, short_name in confirmed_pairs:
        canon_long = reverse.get(long_name)
        canon_short = reverse.get(short_name)

        if canon_long and canon_short:
            if canon_long == canon_short:
                continue  # 已合并
            continue  # 两个都有不同的规范名，跳过

        if canon_long:
            canonical = canon_long
            if short_name not in person_aliases.get(canonical, []):
                person_aliases.setdefault(canonical, []).append(short_name)
                reverse[short_name] = canonical
        elif canon_short:
            canonical = canon_short
            if long_name not in person_aliases.get(canonical, []):
                person_aliases.setdefault(canonical, []).append(long_name)
                reverse[long_name] = canonical
        else:
            person_aliases[long_name] = person_aliases.get(long_name, []) + [short_name]
            reverse[long_name] = long_name
            reverse[short_name] = long_name

    existing_raw['person'] = person_aliases
    return existing_raw


def main():
    print("=" * 60)
    print("自动检测人名别名候选（保守模式）")
    print("=" * 60)

    chapter_persons, person_chapters = extract_persons_by_chapter()
    known_aliases, existing_raw = load_existing_aliases()

    print(f"总人名数: {len(person_chapters)}")
    print(f"已知别名映射: {len(known_aliases)}")

    # 策略1: 全名包含简称（区分唯一/歧义）
    unique_pairs, ambiguous_pairs = find_prefix_aliases(chapter_persons, person_chapters)

    # 策略2: 帝X / X
    di_candidates = find_di_prefix_aliases(person_chapters)

    # 合并唯一映射和帝X候选
    auto_confirmed = []

    # 处理唯一映射的prefix候选
    for long_name, short_name, count in sorted(unique_pairs, key=lambda x: -x[2]):
        # 跳过已知别名
        if long_name in known_aliases and short_name in known_aliases:
            continue
        auto_confirmed.append((long_name, short_name))
        print(f"  [自动] {long_name} ← {short_name} (共{count}章)")

    # 处理帝X候选（也检查唯一性）
    di_short_names = defaultdict(list)
    for name, short, count in di_candidates:
        di_short_names[short].append((name, count))

    for short, longs in di_short_names.items():
        if len(longs) == 1:
            name, count = longs[0]
            if name in known_aliases and short in known_aliases:
                continue
            # 检查是否已在prefix中处理
            if any(ln == name and sn == short for ln, sn in auto_confirmed):
                continue
            auto_confirmed.append((name, short))
            print(f"  [帝X]  {name} ← {short} (共{count}章)")

    print(f"\n自动确认: {len(auto_confirmed)} 对")

    if auto_confirmed:
        updated = merge_into_aliases(existing_raw, auto_confirmed)
        with open(ALIAS_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated, f, ensure_ascii=False, indent=2)
        print(f"已更新 {ALIAS_FILE}")

    # 显示歧义候选（需人工确认）
    if ambiguous_pairs:
        print(f"\n歧义候选（短名对应多个长名，需人工选择）:")
        for short_name, longs in sorted(ambiguous_pairs, key=lambda x: -sum(c for _, c in x[1]))[:40]:
            longs_str = ", ".join(f"{ln}({c}章)" for ln, c in sorted(longs, key=lambda x: -x[1]))
            print(f"  ? {short_name} → {longs_str}")

    # 显示同姓候选
    surname_candidates = find_surname_aliases(chapter_persons, person_chapters)
    surname_new = []
    for n1, n2, count in surname_candidates:
        if n1 in known_aliases and n2 in known_aliases:
            continue
        surname_new.append((n1, n2, count))

    if surname_new:
        print(f"\n同姓候选（仅供参考，需人工确认）:")
        for n1, n2, count in sorted(surname_new, key=lambda x: -x[2])[:30]:
            print(f"  ? {n1} / {n2} (共{count}章)")


if __name__ == '__main__':
    main()
