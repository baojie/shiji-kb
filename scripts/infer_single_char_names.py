#!/usr/bin/env python3
"""推断tagged.md中单字人名的全名映射，并可批量应用内联消歧语法。

用法：
  python scripts/infer_single_char_names.py              # 推断001-010
  python scripts/infer_single_char_names.py 007 008 009   # 推断指定章节
  python scripts/infer_single_char_names.py --apply        # 推断+应用001-010

策略：
1. 在同章中找所有多字人名〖@XY〗，末字=单字名 → XY是候选全名
2. 候选唯一→直接映射；多候选→取出现最多的
3. 排除"单字即全名"列表（舜、尧、禹等远古人物）
"""

import re
import json
import sys
from pathlib import Path
from collections import defaultdict

# 单字即全名（不需要内联消歧）
CANONICAL_SINGLE = set(
    '舜尧禹鲧启桀纣汤契稷益羿浞'  # 远古/夏商
    '龙夔垂倕弃挚羲和胤象'          # 五帝/夏时期
)

PERSON_RE = re.compile(r'〖@([^〖〗\n|]+)〗')


def infer_mappings(file_path):
    """推断单字名→全名映射"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    names = PERSON_RE.findall(content)
    name_counts = defaultdict(int)
    for n in names:
        n = n.strip()
        name_counts[n] += 1

    single_chars = {n for n in name_counts if len(n) == 1
                    and '\u4e00' <= n <= '\u9fff'
                    and n not in CANONICAL_SINGLE}
    multi_names = {n for n in name_counts if len(n) >= 2}

    mappings = {}
    ambiguous = {}
    no_match = {}

    for char in sorted(single_chars):
        # 候选：末字或首字匹配
        cands = list({n for n in multi_names
                      if n[-1] == char or (len(n) == 2 and n[0] == char)})
        if len(cands) == 1:
            mappings[char] = cands[0]
        elif len(cands) > 1:
            cands.sort(key=lambda n: -name_counts.get(n, 0))
            ambiguous[char] = cands
            mappings[char] = cands[0]
        else:
            no_match[char] = name_counts[char]

    return mappings, ambiguous, no_match, name_counts


def apply_mappings(file_path, mappings):
    """将映射应用到文件：〖@X〗 → 〖@X|全名〗"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    count = 0
    for char, full in mappings.items():
        old = f'〖@{char}〗'
        new = f'〖@{char}|{full}〗'
        n = content.count(old)
        if n > 0:
            content = content.replace(old, new)
            count += n

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return count


def main():
    do_apply = '--apply' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    chapters = args if args else [f'{i:03d}' for i in range(1, 11)]

    all_results = {}

    for ch in chapters:
        files = list(Path('chapter_md').glob(f'{ch}_*.tagged.md'))
        if not files:
            continue
        f = files[0]
        mappings, ambiguous, no_match, counts = infer_mappings(f)

        if mappings or no_match:
            print(f'\n=== {ch} {f.stem.replace(".tagged", "")} ===')
            if mappings:
                print(f'  映射 ({len(mappings)}):')
                for char, full in sorted(mappings.items()):
                    mark = ' ⚠多候选' if char in ambiguous else ''
                    print(f'    〖@{char}〗→〖@{char}|{full}〗 ×{counts[char]}{mark}')
            if ambiguous:
                print(f'  多候选详情:')
                for char, cands in sorted(ambiguous.items()):
                    chosen = mappings[char]
                    print(f'    {char}: 选{chosen}(×{counts.get(chosen,0)}), 备选{[c for c in cands if c!=chosen]}')
            if no_match:
                print(f'  无匹配 ({len(no_match)}):')
                for char, cnt in sorted(no_match.items(), key=lambda x: -x[1]):
                    print(f'    〖@{char}〗 ×{cnt}')

            all_results[ch] = mappings

            if do_apply and mappings:
                applied = apply_mappings(f, mappings)
                print(f'  ✅ 已应用 {applied} 处替换')

    out = Path('/tmp/single_char_name_mappings.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f'\n映射保存: {out}')


if __name__ == '__main__':
    main()
