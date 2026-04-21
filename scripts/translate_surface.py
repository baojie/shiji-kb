#!/usr/bin/env python3
"""
白话译文 surface 翻译脚本

把白话 doc/translation/*_白话.md 中仍保留文言形式的 surface
（主要是 地名 `〖=〗` 和 时间 `〖%〗`）翻译为白话，
同时保留/同步规范名消歧。

原则：
- 规范名（`|` 右侧）一律不动，因为它是权威名称
- 仅替换 surface（`|` 左侧）
- 只处理"明确可安全翻译"的模式，避免误伤复合词
- `〖=江|长江〗` → `〖=长江|长江〗` 而不是 `〖=长江|江〗`（规范名保持）

使用：
    python scripts/translate_surface.py --all           # dry-run，打印建议
    python scripts/translate_surface.py --all --apply   # 写入
    python scripts/translate_surface.py 002 --apply
"""

import sys
import re
import argparse
from pathlib import Path


# 精确替换：完整 entity 匹配（surface 就是这一个字/词）
# key 是原 entity（含括号），value 是目标 entity（含括号）
EXACT_REPLACEMENTS = {
    # 地名：史记中单字河流名 → 白话全称
    '〖=江〗': '〖=长江〗',
    '〖=江|长江〗': '〖=长江|长江〗',
    '〖=河〗': '〖=黄河〗',
    '〖=河|黄河〗': '〖=黄河|黄河〗',
    '〖=淮〗': '〖=淮河〗',
    '〖=淮|淮河〗': '〖=淮河|淮河〗',
    '〖=济〗': '〖=济水〗',
    '〖=济|济水〗': '〖=济水|济水〗',
    '〖=汉〗': '〖=汉水〗',       # 仅限作为水名的孤立"汉"；若指汉朝会是 〖◆汉〗
    '〖=汉|汉水〗': '〖=汉水|汉水〗',
    '〖=洛〗': '〖=洛水〗',
    '〖=洛|洛水〗': '〖=洛水|洛水〗',
    '〖=渭〗': '〖=渭水〗',
    '〖=渭|渭水〗': '〖=渭水|渭水〗',
    '〖=泾〗': '〖=泾水〗',
    '〖=泾|泾水〗': '〖=泾水|泾水〗',
    '〖=泗〗': '〖=泗水〗',
    '〖=泗|泗水〗': '〖=泗水|泗水〗',
    '〖=沂〗': '〖=沂水〗',
    '〖=沂|沂水〗': '〖=沂水|沂水〗',

    # 天文：古代星名 → 现代行星名
    '〖!太白〗': '〖!金星|太白〗',
    '〖!荧惑〗': '〖!火星|荧惑〗',
    '〖!辰星〗': '〖!水星|辰星〗',
    '〖!岁星〗': '〖!木星|岁星〗',
    '〖!镇星〗': '〖!土星|镇星〗',
    '〖!填星〗': '〖!土星|填星〗',

    # 典籍：六经简称 → 全称
    '〖{诗〗': '〖{诗经|诗〗',
    '〖{书〗': '〖{尚书|书〗',
    '〖{易〗': '〖{易经|易〗',
    '〖{礼〗': '〖{礼记|礼〗',
    '〖{乐〗': '〖{乐经|乐〗',

    # 身份：文言专称 → 白话
    '〖#黔首〗': '〖#百姓|黔首〗',
    '〖#黎民〗': '〖#百姓|黎民〗',
    '〖#黎庶〗': '〖#百姓|黎庶〗',
    '〖#黔黎〗': '〖#百姓|黔黎〗',

    # 时间量词："岁" → "年"（仅限带 |时长 的明确时长语境）
    # 不处理"岁"指年龄的场景（那些不带 |时长 消歧）
}


# 正则替换：文言时间 surface → 白话
REGEX_RULES = [
    # 1) 时长"岁"→"年"（只在 |时长 语境下，surface 结尾为"岁"）
    (
        re.compile(r'〖%([^|〗]*?)岁(\|时长)〗'),
        r'〖%\1年\2〗',
    ),
    # 2) 〖%X岁〗 无消歧、但 X 为数字/量词 → 〖%X年〗
    #    只处理明确的"数+岁"组合，避免误伤"岁"单独（年龄）
    #    排除"万岁"（为祝颂语/永寿语义，非"一万年"）
    (
        re.compile(r'〖%([〇一二三四五六七八九十百千数]+)岁〗'),  # 去除 万
        r'〖%\1年〗',
    ),
    (
        re.compile(r'〖%([二三四五六七八九十百千数]+十数?|数|[一二三四五六七八九][百千])岁〗'),
        r'〖%\1年〗',
    ),
    # 3) "X馀Y" → "X多Y"（岁馀→一年多 之前 岁→年）
    (
        re.compile(r'〖%年馀(\|[^〗]+)?〗'),
        r'〖%一年多\1〗',
    ),
    (
        re.compile(r'〖%月馀(\|[^〗]+)?〗'),
        r'〖%一个多月\1〗',
    ),
    (
        re.compile(r'〖%日馀(\|[^〗]+)?〗'),
        r'〖%一天多\1〗',
    ),
    # 4) "X馀年/年/岁/日" → "X多年/天"
    (
        re.compile(r'〖%([〇一二三四五六七八九十百千万]+)有?馀年(\|[^〗]+)?〗'),
        r'〖%\1多年\2〗',
    ),
    (
        re.compile(r'〖%([〇一二三四五六七八九十百千万]+)有?馀日(\|[^〗]+)?〗'),
        r'〖%\1多天\2〗',
    ),
    (
        re.compile(r'〖%([〇一二三四五六七八九十百千万]+)有?馀岁(\|[^〗]+)?〗'),
        r'〖%\1多年\2〗',
    ),
    (
        re.compile(r'〖%([〇一二三四五六七八九十百千万]+)有?馀月(\|[^〗]+)?〗'),
        r'〖%\1多个月\2〗',
    ),
    # 5) 日量词：X日 → X天（仅数字前缀的明确天数）
    (
        re.compile(r'〖%([〇一二三四五六七八九十百千数]+)日(\|时长)?〗'),
        lambda m: f'〖%{m.group(1)}天{m.group(2) or ""}〗',
    ),
    # 6) 常用文言时间短语
    (re.compile(r'〖%明日(\|[^〗]+)?〗'), r'〖%第二天\1〗'),
    (re.compile(r'〖%终日(\|[^〗]+)?〗'), r'〖%整天\1〗'),
    (re.compile(r'〖%岁时(\|[^〗]+)?〗'), r'〖%每年按时\1〗'),
    (re.compile(r'〖%岁馀(\|[^〗]+)?〗'), r'〖%一年多\1〗'),
    (re.compile(r'〖%([〇一二三四五六七八九十百千万]+)有?馀世(\|[^〗]+)?〗'), r'〖%\1多代\2〗'),

    # 7) 地名变体：雒 → 洛（史记中 雒阳/雒邑/雒水 等皆为 洛 的古体）
    (re.compile(r'〖=(雒)([^〗|]*)(\|[^〗]+)?〗'), lambda m: f'〖=洛{m.group(2)}{m.group(3) or ""}〗'),
    (re.compile(r'〖=([^〗|]*?)雒([^〗|]*)(\|[^〗]+)?〗'), lambda m: f'〖={m.group(1)}洛{m.group(2)}{m.group(3) or ""}〗'),
]


def translate_file(path: Path, dry_run: bool = True):
    content = path.read_text()
    original = content
    changes = {}

    # 精确替换
    for old, new in EXACT_REPLACEMENTS.items():
        c = content.count(old)
        if c > 0:
            content = content.replace(old, new)
            changes[old + ' → ' + new] = c

    # 正则规则
    for pat, repl in REGEX_RULES:
        def _count_sub(m):
            key = m.group(0) + ' → ' + pat.sub(repl, m.group(0))
            changes[key] = changes.get(key, 0) + 1
            return pat.sub(repl, m.group(0))
        content = pat.sub(_count_sub, content)

    # 清理：实体标注紧跟着解释性括号 `〖T X|Y〗（Z）` 若 Z==X 或 Z==Y，去除 (Z)
    # 防止渲染出 "X（Y）（Z）" 冗余
    RAW_PAREN_PAT = re.compile(r'(〖[@=;%&◆^~•!?+#$:\[_\{]([^|〗]+)\|([^〗]+)〗)（([^）]+)）')
    def _strip_redundant_paren(m):
        tag, surface, canonical, paren = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
        if paren in (surface, canonical):
            changes['_strip_redundant_paren'] = changes.get('_strip_redundant_paren', 0) + 1
            return tag
        return m.group(0)
    content = RAW_PAREN_PAT.sub(_strip_redundant_paren, content)

    if not dry_run and content != original:
        path.write_text(content)

    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('chapters', nargs='*', help='章节号')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--apply', action='store_true', help='实际写入')
    args = ap.parse_args()

    if args.all:
        files = sorted(Path('doc/translation').glob('*_白话.md'))
    else:
        files = []
        for ch in args.chapters:
            ch = ch.zfill(3)
            files += list(Path('doc/translation').glob(f'{ch}_*_白话.md'))

    if not files:
        ap.print_help()
        sys.exit(1)

    total_file_changed = 0
    total_replacements = 0
    agg = {}
    for f in files:
        changes = translate_file(f, dry_run=not args.apply)
        if changes:
            total_file_changed += 1
            n = sum(changes.values())
            total_replacements += n
            for k, v in changes.items():
                agg[k] = agg.get(k, 0) + v

    print(f'{"已修改" if args.apply else "待修改"}文件: {total_file_changed} / {len(files)}')
    print(f'总替换数: {total_replacements}')
    print('\n主要替换分布：')
    for k, v in sorted(agg.items(), key=lambda x: -x[1])[:25]:
        print(f'  {v:5d}  {k}')


if __name__ == '__main__':
    main()
