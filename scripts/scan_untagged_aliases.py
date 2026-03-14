#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
已知实体别名补标扫描（归一化）

目标：确保 entity_index.json 中所有已知实体的正名和别名，
      在全文未标注文字中的出现均得到标注。

逻辑：
  1. 加载 entity_index.json（含所有类型：person/place/official/...）
  2. 对每章，在未标注文字中搜索已知词（按字数降序贪心匹配，防止子串重复覆盖）
  3. 输出建议标注 TSV 到 doc/analysis/patch/NNN_别名补标.tsv

字段（TSV）：
  章节    正名    别名    位置    句法框架类型    匹配模式    上下文    实体类型

用法：
  python scripts/scan_untagged_aliases.py --chapter 055
  python scripts/scan_untagged_aliases.py --all
  python scripts/scan_untagged_aliases.py --all --types person place official
  python scripts/scan_untagged_aliases.py --all --min-len 2 --min-freq 3
"""

import re
import json
import glob
import argparse
from pathlib import Path
from collections import defaultdict

CHAPTER_DIR = Path('chapter_md')
PATCH_DIR   = Path('doc/analysis/patch')
ENTITY_INDEX = Path('kg/entities/data/entity_index.json')

# 实体类型 → 标注符号
TYPE_TO_SYMBOL = {
    'person':    ('@', '@'),
    'place':     ('=', '='),
    'official':  ('$', '$'),
    'time':      ('%', '%'),
    'dynasty':   ('&', '&'),
    'institution': ('^', '^'),
    'tribe':     ('~', '~'),
    'artifact':  ('*', '*'),
    'astronomy': ('!', '!'),
    'mythical':  ('〚', '〛'),
    'biology': ('〖+', '〗'),
}

# 中文类型名（用于 TSV 输出）
TYPE_ZH = {
    'person': '人名', 'place': '地名', 'official': '官职',
    'time': '时间', 'dynasty': '朝代', 'institution': '制度',
    'tribe': '族群', 'artifact': '器物', 'astronomy': '天文',
    'mythical': '神话', 'biology': '生物',
}

# 已有标注的检测正则
ALL_ANNOT_RE = re.compile(
    r'@[^@\n]+?@|=[^=\n]+?=|\$[^\$\n]+?\$|%[^%\n]+?%|&[^&\n]+?&'
    r'|\^[^\^\n]+?\^|~[^~\n]+?~|\*[^\*\n]+?\*|![^!\n]+?!'
    r'|〚[^〛\n]+?〛'
)

PLACEHOLDER = '░'
CHINESE_CHAR_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
# 纯数字词过滤：全由汉字数词组成的词（如"二十"、"八十一"）不做实体匹配
# 理由：这类词在史记各处作数量/分母出现，误报率接近100%
_NUMERAL_RE = re.compile(r'^[零一二三四五六七八九十百千万亿两]+$')

# 高歧义词黑名单：这些词虽在 entity_index 中，但作为独立词出现时误报率极高
# 原因：同时也是高频虚词/称谓/语法结构，无法凭字面区分
SKIP_WORDS = frozenset({
    # 人名误报：这些实为称谓/语法结构（"天子之X"中的"子之"、"公子XX"的"公子"等）
    '子之',   # 燕臣子之，但"天子之德""父子之怒"中大量误报
    '公子',   # 称谓，非具体人名
    '大王',   # 称谓，非具体人名
    '太后',   # 称谓，非具体人名
    '王后',   # 称谓，非具体人名
    '将军',   # 官职兼称谓，单独出现应标 $将军$ 而非 @将军@
    '而立',   # "三十而立"，非人名
    # 官职/称谓误报：这些是泛称，几乎所有出现都已在文中适当标注或不必标
    '太子',   # 官职称谓，entity_index 有具体太子别名时才用正名
    '诸侯',   # 泛称，全文数百次出现大部分不需补标
    '大臣',   # 泛称
    '使者',   # 泛称
    '君王',   # 泛称
    '至于',   # 介词/连词，非官职
    '陛下',   # 称谓，非官职条目
    # 地名误报：泛指概念词而非具体地理名称
    '天下',   # 概念词，非具体地名（应标 〔思想〕，由 tag_new_entity_types.py 处理）
    # 时间/数量误报：数量词被误分类为时间实体
    '一人',   # 数量词
    '四人',   # 数量词
    '十馀',   # 数量词
    '万里',   # 距离词
    '日夜',   # 副词（"日夜不停"），而非时间点
})


def load_entity_index(types_filter: list = None) -> dict:
    """
    加载实体索引，返回 {词: (正名, 类型)} 映射。
    types_filter 为 None 时加载所有类型。
    """
    with open(ENTITY_INDEX, encoding='utf-8') as f:
        data = json.load(f)

    word_map = {}  # {词: (正名, 实体类型)}

    for cat, entries in data.items():
        if types_filter and cat not in types_filter:
            continue
        if not isinstance(entries, dict):
            continue
        for canonical, info in entries.items():
            if not isinstance(info, dict):
                continue
            aliases = info.get('aliases', [])
            all_names = set([canonical] + aliases)
            for name in all_names:
                name = name.strip()
                if not name:
                    continue
                # 黑名单：高歧义词跳过
                if name in SKIP_WORDS:
                    continue
                # 纯数字词跳过（二十/八十一等在各种数量表达式中误报率极高）
                if _NUMERAL_RE.match(name):
                    continue
                # 已在 word_map 中的词不覆盖（保留首次出现的类型）
                if name not in word_map:
                    word_map[name] = (canonical, cat)

    return word_map


def mask_annotations(text: str) -> str:
    result = list(text)
    for m in ALL_ANNOT_RE.finditer(text):
        for i in range(m.start(), m.end()):
            result[i] = PLACEHOLDER
    return ''.join(result)


def scan_chapter(fpath: Path, word_map: dict,
                 min_len: int = 2, min_freq: int = 1) -> list:
    """
    扫描单章，返回建议列表。
    每条：{chapter, canonical, word, pos, context, entity_type_en, entity_type_zh}
    """
    text = fpath.read_text(encoding='utf-8')
    masked = mask_annotations(text)

    chapter = fpath.name.replace('.tagged.md', '')

    # 收集未标注区域中各词的出现次数（先统计，再过滤低频词）
    candidates = defaultdict(list)  # {(word, canonical, type): [pos, ...]}

    # 按词长降序排列，确保长词优先匹配
    sorted_words = sorted(word_map.keys(), key=len, reverse=True)
    # 过滤：只保留符合 min_len 的词
    sorted_words = [w for w in sorted_words if len(w) >= min_len]

    # 已覆盖位置（防止长词和短词重复覆盖同一字符）
    covered = set()

    for word in sorted_words:
        canonical, cat = word_map[word]
        search_start = 0
        while True:
            idx = masked.find(word, search_start)
            if idx == -1:
                break
            search_start = idx + 1

            # 检查是否已被覆盖（之前的长词匹配了这个位置）
            positions = set(range(idx, idx + len(word)))
            if positions & covered:
                continue

            # 确认掩码中这些位置没有 PLACEHOLDER（即未被标注）
            if any(masked[i] == PLACEHOLDER for i in positions):
                continue

            # 记录
            ctx_s = max(0, idx - 10)
            ctx_e = min(len(text), idx + len(word) + 10)
            context = text[ctx_s:ctx_e].replace('\n', '↵')

            key = (word, canonical, cat)
            candidates[key].append({
                'pos': idx,
                'context': context,
            })
            covered.update(positions)

    # 过滤：低于 min_freq 的不建议
    suggestions = []
    for (word, canonical, cat), occurrences in candidates.items():
        if len(occurrences) < min_freq:
            continue
        type_zh = TYPE_ZH.get(cat, cat)
        for occ in occurrences:
            suggestions.append({
                'chapter': chapter,
                'canonical': canonical,
                'word': word,
                'pos': occ['pos'],
                'frame_type': '词表匹配',
                'pattern': word,
                'context': occ['context'],
                'entity_type': type_zh,
            })

    suggestions.sort(key=lambda x: x['pos'])
    return suggestions


def write_tsv(out: Path, suggestions: list):
    with open(out, 'w', encoding='utf-8') as f:
        f.write('章节\t正名\t词\t位置\t框架类型\t匹配模式\t上下文\t实体类型\n')
        for s in suggestions:
            f.write(f'{s["chapter"]}\t{s["canonical"]}\t{s["word"]}\t'
                    f'{s["pos"]}\t{s["frame_type"]}\t{s["pattern"]}\t'
                    f'{s["context"]}\t{s["entity_type"]}\n')


def run_chapter(chapter_id: str, word_map: dict, min_len: int, min_freq: int):
    pattern = str(CHAPTER_DIR / f'{chapter_id}_*.tagged.md')
    files = glob.glob(pattern)
    if not files:
        print(f'[ERROR] 未找到章节 {chapter_id}')
        return

    fpath = Path(files[0])
    print(f'扫描：{fpath.name}')
    suggestions = scan_chapter(fpath, word_map, min_len, min_freq)

    if not suggestions:
        print('  无建议。')
        return

    print(f'  发现 {len(suggestions)} 条建议（去重后词种数：'
          f'{len(set(s["word"] for s in suggestions))}）：')

    # 按词分组显示 TOP
    by_word = defaultdict(list)
    for s in suggestions:
        by_word[s['word']].append(s)
    for word, items in sorted(by_word.items(), key=lambda x: -len(x[1]))[:20]:
        canonical = items[0]['canonical']
        etype = items[0]['entity_type']
        print(f'  {etype}  [{canonical}]→{word}  {len(items)}处'
              f'  示例：「{items[0]["context"]}」')

    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    chapter = fpath.name.replace('.tagged.md', '')
    out = PATCH_DIR / f'{chapter}_别名补标.tsv'
    write_tsv(out, suggestions)
    print(f'  已保存：{out}')


def run_all(word_map: dict, min_len: int, min_freq: int):
    files = sorted(CHAPTER_DIR.glob('*.tagged.md'))
    print(f'共 {len(files)} 章，开始扫描...')
    PATCH_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    for i, fpath in enumerate(files, 1):
        suggestions = scan_chapter(fpath, word_map, min_len, min_freq)
        if suggestions:
            chapter = fpath.name.replace('.tagged.md', '')
            out = PATCH_DIR / f'{chapter}_别名补标.tsv'
            write_tsv(out, suggestions)
            total += len(suggestions)
            print(f'  [{i:3d}] {fpath.name[:35]:35s}  {len(suggestions):4d} 条', flush=True)

    print(f'\n✅ 合计 {total} 条别名补标建议，已保存到 {PATCH_DIR}/')


def main():
    parser = argparse.ArgumentParser(description='已知实体别名补标扫描')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--chapter', metavar='NNN')
    group.add_argument('--all', action='store_true')
    parser.add_argument('--types', nargs='+',
                        choices=list(TYPE_TO_SYMBOL.keys()),
                        help='只扫描指定类型（默认全部）')
    parser.add_argument('--min-len', type=int, default=2,
                        help='词最小长度（默认2，过滤单字）')
    parser.add_argument('--min-freq', type=int, default=1,
                        help='章节内最少出现次数（默认1）')
    args = parser.parse_args()

    print(f'加载实体索引（类型：{args.types or "全部"}）...')
    word_map = load_entity_index(args.types)
    print(f'  共 {len(word_map)} 个词条')

    if args.chapter:
        run_chapter(args.chapter, word_map, args.min_len, args.min_freq)
    else:
        run_all(word_map, args.min_len, args.min_freq)


if __name__ == '__main__':
    main()
