#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生物实体系统性反思扫描器

对130章检查：
1. 现有 〖+X〗 标注是否在词表内
2. 跨类型冲突（同一词既标〖+〗又标〚〛等）
3. 词表中的词在未标注文本中出现但未标注
4. 输出 TSV 报告

用法：
    python scripts/scan_biology_reflect.py
    python scripts/scan_biology_reflect.py --chapter 001
"""

import re
import json
import argparse
from pathlib import Path
from collections import defaultdict

CHAPTER_DIR = Path('chapter_md')
WORDLIST_FILE = Path('kg/biology/data/biology_wordlist.json')
OUTPUT_FILE = Path('doc/analysis/biology_scan_report.tsv')

# 标注模式
BIO_PATTERN = re.compile(r'〖\+([^〖〗\n]+)〗')

# 所有标注模式（用于检测跨类型冲突）
ALL_PATTERNS = {
    'person': re.compile(r'〖@([^〖〗\n]+)〗'),
    'place': re.compile(r'〖=([^〖〗\n]+)〗'),
    'official': re.compile(r'〖;([^〖〗\n]+)〗'),
    'time': re.compile(r'〖%([^〖〗\n]+)〗'),
    'dynasty': re.compile(r'〖&([^〖〗\n]+)〗'),
    'feudal-state': re.compile(r"〖'([^〖〗\n]+)〗"),
    'institution': re.compile(r'〖\^([^〖〗\n]+)〗'),
    'tribe': re.compile(r'〖~([^〖〗\n]+)〗'),
    'identity': re.compile(r'〖#([^〖〗\n]+)〗'),
    'artifact': re.compile(r'〖\*([^〖〗\n]+)〗'),
    'astronomy': re.compile(r'〖!([^〖〗\n]+)〗'),
    'quantity': re.compile(r'〖\$([^〖〗\n]+)〗'),
    'biology': BIO_PATTERN,
    'mythical': re.compile(r'〚([^〚〛\n]+)〛'),
    'book': re.compile(r'《([^《》\n]+)》'),
    'concept': re.compile(r'〔([^〔〕\n]+)〕'),
}

# 掩码用正则
ALL_ANNOT_RE = re.compile(
    r'〖[@=;%&\'^~\*!#\+\$][^〖〗\n]+?〗'
    r'|〚[^〛\n]+?〛'
    r'|《[^》\n]+?》'
    r'|〈[^〉\n]+?〉'
    r'|【[^】\n]+?】'
    r'|〔[^〕\n]+?〕'
)
PLACEHOLDER = '░'


def load_wordlist():
    """加载生物词表，返回所有词的集合"""
    with open(WORDLIST_FILE, encoding='utf-8') as f:
        data = json.load(f)

    all_words = set()
    for category, words in data.get('always_biology', {}).items():
        all_words.update(words)
    for category, items in data.get('context_dependent', {}).items():
        if isinstance(items, dict):
            all_words.update(items.keys())
    for category, words in data.get('new_candidates', {}).items():
        all_words.update(words)

    return all_words


def mask_annotations(text):
    """掩码所有标注区域"""
    result = list(text)
    for m in ALL_ANNOT_RE.finditer(text):
        for i in range(m.start(), m.end()):
            result[i] = PLACEHOLDER
    return ''.join(result)


def scan_chapter(fpath, wordlist):
    """扫描单章，返回发现列表"""
    text = fpath.read_text(encoding='utf-8')
    chapter = fpath.name.replace('.tagged.md', '')
    findings = []

    # 1. 检查现有〖+X〗标注是否在词表内
    bio_entities = set()
    for m in BIO_PATTERN.finditer(text):
        entity = m.group(1)
        bio_entities.add(entity)
        if entity not in wordlist:
            findings.append({
                'chapter': chapter,
                'type': 'unknown_bio',
                'entity': entity,
                'detail': f'标注了〖+{entity}〗但不在词表内',
                'context': text[max(0, m.start()-15):m.end()+15].replace('\n', '↵'),
            })

    # 2. 跨类型冲突
    all_entities_by_type = defaultdict(set)
    for etype, pattern in ALL_PATTERNS.items():
        for m in pattern.finditer(text):
            all_entities_by_type[etype].add(m.group(1))

    for entity in bio_entities:
        for etype, entities in all_entities_by_type.items():
            if etype == 'biology':
                continue
            if entity in entities:
                findings.append({
                    'chapter': chapter,
                    'type': 'cross_type',
                    'entity': entity,
                    'detail': f'同时标为 biology 和 {etype}',
                    'context': '',
                })

    # 3. 词表中的词在未标注文本中出现但未标注
    masked = mask_annotations(text)
    # 只检查 always_biology 层的词（按长度降序避免子串覆盖）
    with open(WORDLIST_FILE, encoding='utf-8') as f:
        data = json.load(f)
    always_words = set()
    for words in data.get('always_biology', {}).values():
        always_words.update(words)
    # 也加入 new_candidates
    for words in data.get('new_candidates', {}).values():
        always_words.update(words)

    sorted_words = sorted(always_words, key=len, reverse=True)
    # 只检查2字以上
    sorted_words = [w for w in sorted_words if len(w) >= 2]

    covered = set()
    for word in sorted_words:
        start = 0
        while True:
            idx = masked.find(word, start)
            if idx == -1:
                break
            start = idx + 1
            positions = set(range(idx, idx + len(word)))
            if positions & covered:
                continue
            if any(masked[i] == PLACEHOLDER for i in positions):
                continue
            # Found untagged occurrence
            ctx_s = max(0, idx - 15)
            ctx_e = min(len(text), idx + len(word) + 15)
            context = text[ctx_s:ctx_e].replace('\n', '↵')
            findings.append({
                'chapter': chapter,
                'type': 'untagged',
                'entity': word,
                'detail': f'词表词未标注',
                'context': context,
            })
            covered.update(positions)

    return findings


def main():
    parser = argparse.ArgumentParser(description='生物实体反思扫描')
    parser.add_argument('--chapter', metavar='NNN', help='只扫描指定章节')
    args = parser.parse_args()

    wordlist = load_wordlist()
    print(f'词表共 {len(wordlist)} 个词')

    if args.chapter:
        import glob
        files = sorted(Path(f).resolve() for f in
                       glob.glob(str(CHAPTER_DIR / f'{args.chapter}_*.tagged.md')))
    else:
        files = sorted(CHAPTER_DIR.glob('*.tagged.md'))

    print(f'扫描 {len(files)} 个文件...')

    all_findings = []
    for fpath in files:
        findings = scan_chapter(fpath, wordlist)
        if findings:
            all_findings.extend(findings)
            # 统计
            by_type = defaultdict(int)
            for f in findings:
                by_type[f['type']] += 1
            summary = ', '.join(f'{k}:{v}' for k, v in sorted(by_type.items()))
            print(f'  {fpath.name[:40]:40s} {summary}')

    # 写入报告
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('章节\t类型\t实体\t说明\t上下文\n')
        for item in all_findings:
            f.write(f'{item["chapter"]}\t{item["type"]}\t{item["entity"]}\t'
                    f'{item["detail"]}\t{item["context"]}\n')

    # 汇总
    by_type = defaultdict(int)
    for item in all_findings:
        by_type[item['type']] += 1

    print(f'\n汇总：')
    for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f'  {t}: {c}')
    print(f'  总计: {len(all_findings)}')
    print(f'报告已保存: {OUTPUT_FILE}')


if __name__ == '__main__':
    main()
