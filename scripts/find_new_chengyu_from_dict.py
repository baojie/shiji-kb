#!/usr/bin/env python3
"""
从《中华成语大词典》的 7343 条词条中筛选出《史记》可能的新成语。

策略：
1. 加载词典词条名（已提取到 private/book/chengyu_dict_names.txt）
2. 加载各章节干净文本，建索引
3. 扫描每条词典成语是否在任何章节中出现
4. 排除：
   a. 已在 〘※〙 标注中的
   b. 已在 kg/vocabularies/data/史记成语典故.md 中的
5. 输出候选列表到 logs/chengyu_candidates_from_dict.txt

候选分三类：
- strong：4 字及以上，完全匹配
- medium：3 字，完全匹配（需人工审核是否固化）
- variant：与已知成语仅一字之差（可能是异形）
"""

import re
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
DICT_NAMES = ROOT / 'private/book/chengyu_dict_names.txt'
CHAPTER_DIR = ROOT / 'chapter_md'
SOURCE_MD = ROOT / 'kg/vocabularies/data/史记成语典故.md'
LOG = ROOT / 'logs/chengyu_candidates_from_dict.txt'


def strip_all_markup(text):
    t = text
    t = re.sub(r'〘※([^〘〙|]+)(?:\|[^〘〙]*)?〙', r'\1', t)
    t = re.sub(r'〖.([^〖〗|]+)(?:\|[^〖〗]*)?〗', r'\1', t)
    t = re.sub(r'⟦.([^⟦⟧|]+)(?:\|[^⟦⟧]*)?⟧', r'\1', t)
    return t


def parse_source_md():
    """返回所有已在源词表中的成语名"""
    known = set()
    for line in SOURCE_MD.read_text(encoding='utf-8').split('\n'):
        line = line.strip()
        if not line.startswith('|') or line.startswith('|---'):
            continue
        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) >= 2 and parts[0] and parts[0] != '成语':
            name = parts[0]
            # 处理斜杠、括号
            if name.startswith(('（', '(')):
                continue
            for sub in re.split(r'[/／]', name):
                known.add(sub.strip())
    return known


def main():
    dict_names = [n.strip() for n in DICT_NAMES.read_text().split('\n') if n.strip()]
    print(f'词典条目: {len(dict_names)}')

    known = parse_source_md()
    print(f'源表已收: {len(known)}')

    # 加载所有章节干净文本
    chapters = {}
    for f in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        stem = f.stem.replace('.tagged', '')
        m = re.match(r'(\d{3})_(.+)', stem)
        if not m:
            continue
        num = m.group(1)
        title = m.group(2)
        pure = strip_all_markup(f.read_text(encoding='utf-8'))
        chapters[num] = {'title': title, 'pure': pure}
    print(f'章节: {len(chapters)}')

    # 扫描候选
    candidates_by_type = {'strong': [], 'three_char': [], 'known_skip': 0}

    for idiom in dict_names:
        if idiom in known:
            candidates_by_type['known_skip'] += 1
            continue

        # 在各章节中搜索
        hits = []
        for num, c in chapters.items():
            idx = c['pure'].find(idiom)
            if idx >= 0:
                # 抽取小段上下文
                ctx_start = max(0, idx - 15)
                ctx_end = min(len(c['pure']), idx + len(idiom) + 15)
                ctx = c['pure'][ctx_start:ctx_end].replace('\n', ' ')
                hits.append((num, c['title'], ctx))
                break  # 命中一章就够

        if not hits:
            continue

        if len(idiom) >= 4:
            candidates_by_type['strong'].append((idiom, hits))
        elif len(idiom) == 3:
            candidates_by_type['three_char'].append((idiom, hits))

    # 输出
    lines = []
    lines.append(f'词典条目: {len(dict_names)}')
    lines.append(f'源表已收: {len(known)}（跳过 {candidates_by_type["known_skip"]}）')
    lines.append(f'新候选（4字+）: {len(candidates_by_type["strong"])}')
    lines.append(f'新候选（3字）: {len(candidates_by_type["three_char"])}')
    lines.append('')
    lines.append('=' * 60)
    lines.append(f'=== 4字及以上新候选（{len(candidates_by_type["strong"])} 条）===')
    lines.append('=' * 60)
    for idiom, hits in sorted(candidates_by_type['strong']):
        for num, title, ctx in hits:
            lines.append(f'[{num}] {idiom}  | ctx: ...{ctx}...')

    lines.append('')
    lines.append('=' * 60)
    lines.append(f'=== 3 字新候选（{len(candidates_by_type["three_char"])} 条，多为名词）===')
    lines.append('=' * 60)
    for idiom, hits in sorted(candidates_by_type['three_char']):
        for num, title, ctx in hits:
            lines.append(f'[{num}] {idiom}  | ctx: ...{ctx}...')

    LOG.write_text('\n'.join(lines), encoding='utf-8')
    print(f'写入 {LOG}')
    print(f'4字+ 新候选: {len(candidates_by_type["strong"])}')
    print(f'3 字新候选: {len(candidates_by_type["three_char"])}')


if __name__ == '__main__':
    main()
