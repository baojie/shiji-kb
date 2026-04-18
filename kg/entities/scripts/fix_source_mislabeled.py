#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从源头修正两类 place 标注错误：

1. 误标（非地名被误标为 〖=X〗）：移除 〖= 与 〗 标记，保留原文字符。
2. 待拆分（两地名连写）：将 〖=AB〗 拆成 〖=A〗〖=B〗。

安全约束（来自 CLAUDE.md）：
- 只修改标注 token（〖= 和 〗），绝不修改原文汉字
- 修改后的文件去除所有 tag 后应与原文字符串完全一致
- 默认 dry-run 只打印将要做的修改，加 --apply 才写回

用法：
  python3 fix_source_mislabeled.py             # dry-run
  python3 fix_source_mislabeled.py --apply     # 实际写回
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CATS_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'place_categories.json'
CHAPTER_DIR = _ROOT / 'chapter_md'

APPLY = '--apply' in sys.argv


def load_classifier_state():
    """加载分类脚本的各个白名单集合（用于 split 的子串参考）。"""
    # 通过 import 的方式获取已知 place 集合
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'classify_places',
        _ROOT / 'kg' / 'entities' / 'scripts' / 'classify_places.py',
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    cats = json.loads(CATS_JSON.read_text(encoding='utf-8'))
    mis_set = {n for n, v in cats.items() if '误标' in v}
    split_set = {n for n, v in cats.items() if '待拆分' in v}
    print(f'误标条目: {len(mis_set)}')
    print(f'待拆分条目: {len(split_set)}')

    # 加载 place names 集合用于拆分时验证
    all_places = set(cats.keys())
    # 计算每个待拆分名字的最佳拆分
    clf = load_classifier_state()
    split_map = {}  # name -> [part1, part2, ...]
    for name in split_set:
        parts = clf.split_into_known_places(name, all_places)
        if parts:
            split_map[name] = parts
    print(f'可确定拆分方案: {len(split_map)}/{len(split_set)}')

    # 扫描 chapter_md 并做替换
    total_mis = 0
    total_split = 0
    per_file_changes = defaultdict(list)
    mode_tag = 'APPLY' if APPLY else 'DRY-RUN'
    print(f'\n=== {mode_tag} ===')

    for chap in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        content = chap.read_text(encoding='utf-8')
        orig = content
        changes = []

        # 1) 误标：〖=X〗 → X
        for name in mis_set:
            pat = re.compile(r'〖=(' + re.escape(name) + r')(?:\|[^〖〗]+)?〗')
            n = 0

            def _repl_mis(m):
                nonlocal n
                n += 1
                return m.group(1)   # 只保留 name，丢弃标签

            content = pat.sub(_repl_mis, content)
            if n:
                changes.append(('误标', name, n))
                total_mis += n

        # 2) 待拆分：〖=AB〗 → 〖=A〗〖=B〗
        for name, parts in split_map.items():
            pat = re.compile(r'〖=(' + re.escape(name) + r')(?:\|[^〖〗]+)?〗')
            n = 0
            replacement = ''.join(f'〖={p}〗' for p in parts)

            def _repl_split(m):
                nonlocal n
                n += 1
                return replacement

            content = pat.sub(_repl_split, content)
            if n:
                changes.append(('待拆分→' + '+'.join(parts), name, n))
                total_split += n

        if changes:
            per_file_changes[chap.name] = changes
            if APPLY and content != orig:
                chap.write_text(content, encoding='utf-8')

    # 打印报告
    print()
    for fname, ch in sorted(per_file_changes.items()):
        print(f'{fname}:')
        for kind, name, n in ch:
            print(f'  [{kind}] {name} ×{n}')

    print(f'\n合计：误标移除 {total_mis} 处，待拆分 {total_split} 处')
    if not APPLY:
        print('(dry-run，未写入。加 --apply 执行)')


if __name__ == '__main__':
    main()
