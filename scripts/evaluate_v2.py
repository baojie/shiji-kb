#!/usr/bin/env python3
"""
Phase 6 评估：对同一章节 v1 (doc/translation/) vs v2 (doc/translation_v2/) 对比关键指标。

评估维度：
1. PN 对齐数 / 总数（两版本都须 100% 对齐）
2. 半角标点数（v2 应为 0）
3. 实体标注数（保持一致）
4. 文言动词残留：崩/立/卒/曰/毋/畔 等在译文的裸字频次
5. "礼记" 误译（含"礼记"但非消歧语法的）
6. 年龄语境"岁"保留数（"少X N岁" / "比X小N岁" 模式）
7. 与外部（hunterhug）的文本相似度（difflib）
8. 行数、字数对比

用法：python scripts/evaluate_v2.py 002 067
"""

import sys
import re
import json
from pathlib import Path
from difflib import SequenceMatcher

ALIGN_DIR = Path('data/translation_alignment')
V1_DIR = Path('doc/translation')
V2_DIR = Path('doc/translation_v2')

TAG_RE = re.compile(r'〖[@=;%&◆^~•!?+#$:\[_\{][^〖〗]*〗|⟦[○◈◉◇][^⟦⟧]*⟧|〘※[^〘〙]*〙')
DISAMBIG_RE = re.compile(r'〖[@=;%&◆^~•!?+#$:\[_\{]\s*([^|〗]+)\|([^〗]+)〗')


def strip_tags_preserve_surface(text: str) -> str:
    """Remove tag shells but keep surface text (first arg of disambig)."""
    text = re.sub(r'〖[@=;%&◆^~•!?+#$:\[_\{]\s*([^|〗]+)\|[^〗]+〗', r'\1', text)
    text = re.sub(r'⟦[○◈◉◇]([^|⟦⟧]+)\|[^⟦⟧]+⟧', r'\1', text)
    text = re.sub(r'〘※([^|〘〙]+)\|[^〘〙]+〙', r'\1', text)
    text = re.sub(r'〖[@=;%&◆^~•!?+#$:\[_\{]\s*([^〗]*)〗', r'\1', text)
    text = re.sub(r'⟦[○◈◉◇]([^⟦⟧]*)⟧', r'\1', text)
    text = re.sub(r'〘※([^〘〙]*)〙', r'\1', text)
    return text


def parse_pns(content: str) -> dict:
    """Parse PN-level translations from a _白话.md file."""
    result = {}
    pattern = re.compile(r'^##\s*\[(\d+(?:\.\d+)*)\][^\n]*\n((?:(?!^##).)*)', re.M | re.DOTALL)
    for m in pattern.finditer(content):
        result[m.group(1)] = m.group(2).strip()
    return result


def count_halfwidth_punct(text: str) -> int:
    """Count half-width punctuation OUTSIDE entity tags."""
    out = 0
    in_tag = False
    for ch in text:
        if ch in '〖⟦〘':
            in_tag = True
        elif ch in '〗⟧〙':
            in_tag = False
        elif not in_tag and ch in ',.;:!?()':
            out += 1
    return out


def count_classical_verbs(text_stripped: str) -> dict:
    """Count occurrences of classical verbs that v2 wants replaced."""
    patterns = {
        '崩': r'(?<![\w=])崩(?![\w=])',
        '薨': r'(?<![\w=])薨(?![\w=])',
        '卒': r'(?<![\w=])卒(?![\w=众])',
        '曰': r'(?<![\w])曰(?![\w])',
        '毋': r'(?<![\w])毋(?![\w])',
        '畔': r'(?<![\w])畔(?![\w])',
        '於是': r'於是',
        '乃': r'(?<![\w])乃(?![\w])',
    }
    return {k: len(re.findall(p, text_stripped)) for k, p in patterns.items()}


def count_lijii_errors(text: str) -> int:
    """Count '礼记' occurrences where it's NOT in 〖{礼记|礼〗 disambig."""
    # Total occurrences of 礼记 (with or without tags)
    total = text.count('礼记')
    # Occurrences in disambig context 〖{礼记|礼〗
    in_disambig = len(re.findall(r'〖\{礼记\|礼〗', text))
    return total - in_disambig


def count_age_context_sui(text: str) -> dict:
    """Count age context: 少X N岁 vs N年."""
    # Patterns: 比...小N岁/年, 少...N岁/年, 年N岁
    sui_age = len(re.findall(r'(?:比|小|长|少)[^，。；]{0,10}[〇一二三四五六七八九十百千\d]+岁', text))
    nian_age = len(re.findall(r'(?:比|小|长|少)[^，。；]{0,10}[〇一二三四五六七八九十百千\d]+年', text))
    return {'岁(年龄)': sui_age, '年(年龄-疑似错译)': nian_age}


def evaluate_chapter(ch: str) -> dict:
    v1 = next(V1_DIR.glob(f'{ch}_*_白话.md'), None)
    v2 = next(V2_DIR.glob(f'{ch}_*_白话.md'), None)
    if not v1 or not v2:
        return {'chapter': ch, 'error': 'missing file'}

    v1_text = v1.read_text()
    v2_text = v2.read_text()
    v1_pns = parse_pns(v1_text)
    v2_pns = parse_pns(v2_text)

    # Hunterhug 对齐数据
    align = json.load(open(ALIGN_DIR / f'{ch}.json')) if (ALIGN_DIR / f'{ch}.json').exists() else None
    hh_map = {r['pn']: r['hunterhug'] for r in align['records']} if align else {}

    # 计算指标
    result = {
        'chapter': ch,
        'v1_pns': len(v1_pns),
        'v2_pns': len(v2_pns),
        'v1_lines': v1_text.count('\n'),
        'v2_lines': v2_text.count('\n'),
        'v1_chars': len(v1_text),
        'v2_chars': len(v2_text),
        'v1_halfwidth_punct': count_halfwidth_punct(v1_text),
        'v2_halfwidth_punct': count_halfwidth_punct(v2_text),
        'v1_lijii_error': count_lijii_errors(v1_text),
        'v2_lijii_error': count_lijii_errors(v2_text),
    }

    # 文言动词统计（基于去 tag 后的纯文本）
    v1_strip = strip_tags_preserve_surface(v1_text)
    v2_strip = strip_tags_preserve_surface(v2_text)
    result['v1_classical_verbs'] = count_classical_verbs(v1_strip)
    result['v2_classical_verbs'] = count_classical_verbs(v2_strip)
    result['v1_age_sui'] = count_age_context_sui(v1_strip)
    result['v2_age_sui'] = count_age_context_sui(v2_strip)

    # 与 hunterhug 相似度（只取两版本都有对应且 hh_map 有数据的 PN）
    v1_hh_sim = []
    v2_hh_sim = []
    for pn, hh_text in hh_map.items():
        if not hh_text: continue
        if pn in v1_pns:
            sim = SequenceMatcher(None, strip_tags_preserve_surface(v1_pns[pn]), hh_text).ratio()
            v1_hh_sim.append(sim)
        if pn in v2_pns:
            sim = SequenceMatcher(None, strip_tags_preserve_surface(v2_pns[pn]), hh_text).ratio()
            v2_hh_sim.append(sim)
    result['v1_hh_avg_similarity'] = round(sum(v1_hh_sim) / len(v1_hh_sim), 3) if v1_hh_sim else None
    result['v2_hh_avg_similarity'] = round(sum(v2_hh_sim) / len(v2_hh_sim), 3) if v2_hh_sim else None
    result['n_compared'] = len(v1_hh_sim)
    return result


def format_report(results: list) -> str:
    lines = ['# v1 vs v2 Phase 6 评估', '']
    for r in results:
        if 'error' in r:
            lines.append(f"## {r['chapter']} — {r['error']}")
            continue
        ch = r['chapter']
        lines.append(f'## {ch}')
        lines.append('')
        lines.append(f"| 指标 | v1 | v2 | Δ（v2−v1） |")
        lines.append('|------|----|----|-----------|')
        def row(label, v1v, v2v, better_direction='down'):
            if isinstance(v1v, (int, float)) and isinstance(v2v, (int, float)):
                delta = v2v - v1v
                arrow = ''
                if better_direction == 'down' and delta < 0: arrow = ' ✅'
                elif better_direction == 'up' and delta > 0: arrow = ' ✅'
                elif better_direction == 'down' and delta > 0: arrow = ' ⚠️'
                lines.append(f"| {label} | {v1v} | {v2v} | {delta:+}{arrow} |")
            else:
                lines.append(f"| {label} | {v1v} | {v2v} | — |")
        row('PN 数', r['v1_pns'], r['v2_pns'], 'none')
        row('行数', r['v1_lines'], r['v2_lines'], 'none')
        row('字符数', r['v1_chars'], r['v2_chars'], 'none')
        row('半角标点（越少越好）', r['v1_halfwidth_punct'], r['v2_halfwidth_punct'], 'down')
        row('"礼记"误译（越少越好）', r['v1_lijii_error'], r['v2_lijii_error'], 'down')
        row('与 hunterhug 平均相似度（越高越好）', r['v1_hh_avg_similarity'], r['v2_hh_avg_similarity'], 'up')
        lines.append('')
        lines.append('### 文言动词残留（越少越好）')
        lines.append('')
        lines.append(f"| 词 | v1 | v2 | Δ |")
        lines.append('|----|----|----|---|')
        for k in r['v1_classical_verbs']:
            v1v = r['v1_classical_verbs'][k]
            v2v = r['v2_classical_verbs'][k]
            delta = v2v - v1v
            arrow = ' ✅' if delta < 0 else (' ⚠️' if delta > 0 else '')
            lines.append(f"| {k} | {v1v} | {v2v} | {delta:+}{arrow} |")
        lines.append('')
        lines.append('### 年龄语境')
        lines.append('')
        lines.append(f"| 词 | v1 | v2 |")
        lines.append('|----|----|----|')
        for k in r['v1_age_sui']:
            lines.append(f"| {k} | {r['v1_age_sui'][k]} | {r['v2_age_sui'][k]} |")
        lines.append('')
        lines.append('---')
        lines.append('')
    return '\n'.join(lines)


def main():
    args = sys.argv[1:]
    if not args:
        chapters = sorted({f.stem.split('_')[0] for f in V2_DIR.glob('*_白话.md')})
    else:
        chapters = [a.zfill(3) for a in args]
    results = [evaluate_chapter(ch) for ch in chapters]
    report = format_report(results)
    Path('doc/translation_quality/eval').mkdir(parents=True, exist_ok=True)
    Path('doc/translation_quality/v2_evaluation.md').write_text(report)
    print(report)
    print(f'\n报告已写入 doc/translation_quality/v2_evaluation.md')


if __name__ == '__main__':
    main()
