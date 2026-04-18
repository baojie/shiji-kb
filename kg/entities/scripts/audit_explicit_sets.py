#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则静态审计：检查每个 EXPLICIT_* 白名单中的每一项，是否有原文/三家注证据支持。

方法：
  对每个 (name, cat) 组合，在 chapter_md + 三家注 中查找：
  - **正证据**（支持该 cat 的模式，如 "登 X" 支持 山脉）
  - **反证据**（暗示其它 cat 的模式）
  计算"支持度" = 正证据数 / (正 + 反)

疑似错归的条目：支持度 < 50% 或 正证据 = 0 且 反证据 > 0

输出：doc/entities/地名反思/第七轮_白名单审计.md
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / 'kg' / 'entities' / 'scripts'))
import classify_places as cp

CHAPTER_DIR = _ROOT / 'chapter_md'
SANJIA_FILE = _ROOT / 'corpus' / 'shiji' / '史记集解三家注索隐正义.txt'
OUT = _ROOT / 'doc' / 'entities' / '地名反思' / '第七轮_白名单审计.md'


# ─── 每个分类的特征模式（用于正反证据扫描）───
# 每条: (regex_with_X, score)—— score 越高信号越强
# 其中 {X} 在扫描时被 re.escape(name) 替换

CATEGORY_SIGNALS = {
    '山脉': [
        (r'(?:登|陟|望|封禅)〖=({X})〗', 3),
        (r'禅(?:于|乎)?〖=({X})〗', 3),
        (r'〖=({X})〗山', 2),
        (r'〖=({X})〗之[阳阴]', 2),
        (r'〖=({X})〗、[^〖〗]*?山', 1),
    ],
    '水域': [
        (r'(?:渡|济|涉|临|溯|游|泛)〖=({X})〗', 3),
        (r'出于〖=({X})〗', 2),
        (r'入(?:于)?〖=({X})〗', 2),
        (r'漕〖=({X})〗', 2),
        (r'〖=({X})〗水', 2),
    ],
    '关隘': [
        (r'守〖=({X})〗', 2),
        (r'〖=({X})〗(?:关|塞)', 2),
        (r'(?:出|过)〖=({X})〗', 1),
        (r'自〖=({X})〗以[东西南北]', 1),
    ],
    '建筑': [
        (r'祠(?:于)?〖=({X})〗', 2),
        (r'立[^〖〗]*?〖=({X})〗', 2),
        (r'起〖=({X})〗', 2),
        (r'造〖=({X})〗', 2),
        (r'〖=({X})〗(?:宫|殿|台|门|祠|庙)', 2),
    ],
    '城邑': [
        (r'(?:攻|取|拔|降|入|袭|围|屠|破|徇|下)〖=({X})〗', 3),
        (r'(?:都|徙都|居)〖=({X})〗', 3),
        (r'(?:城|筑)〖=({X})〗', 2),
        (r'战[^。]*?〖=({X})〗', 2),
        (r'〖=({X})〗[之]?城', 1),
    ],
    '县': [
        (r'〖=({X})〗县', 3),
        (r'〖=({X})〗(?:戴|康|懿|庄|哀|敬|文|武|孝|献|节|恭|简|共|平|穆|惠|景|成|桓|灵|元|宣|昭|襄|僖|悼|殇|幽|厉|愍|殷)?侯(?!国)', 2),
        (r'封[^。]{0,10}?为〖=({X})〗侯', 3),
        (r'(?:攻|取|拔)〖=({X})〗', 1),
    ],
    '郡': [
        (r'〖=({X})〗郡', 3),
        (r'治〖=({X})〗', 2),
        (r'〖=({X})〗〖;[^〖〗]*?太守', 3),
        (r'〖=({X})〗、[^〖〗]*?(?:二|三|四)郡', 3),
    ],
    '国家': [
        (r'(?:伐|攻|灭|朝|与)〖=({X})〗', 1),
        (r'〖=({X})〗(?:王|君|之师|之众)', 2),
        (r'〖=({X})〗人', 1),
    ],
    '区域': [
        (r'〖=({X})〗之(?:地|民|俗|人|众)', 2),
        (r'自〖=({X})〗以[东西南北]', 2),
        (r'至(?:于)?〖=({X})〗', 1),
    ],
    '陵墓': [
        (r'葬(?:于)?〖=({X})〗', 3),
        (r'〖=({X})〗冢', 3),
    ],
    '原野': [
        (r'(?:战|败)(?:于|於)?〖=({X})〗', 2),
        (r'〖=({X})〗(?:之野|之战|之役)', 3),
    ],
    '乡里': [
        (r'〖=({X})〗乡', 3),
        (r'〖=({X})〗里', 3),
        (r'〖=({X})〗亭', 3),
    ],
    '道桥': [
        (r'〖=({X})〗(?:道|桥|津|渡)', 3),
    ],
    '州': [
        (r'〖=({X})〗州', 3),
    ],
}


def load_chapters():
    """把所有 tagged.md 拼成一个大字符串（内存折腾但简单）"""
    parts = []
    for chap in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        parts.append(chap.read_text(encoding='utf-8'))
    return '\n'.join(parts)


def scan_signals(name, corpus_text, sanjia_text):
    """返回 {cat: count} 表示该 name 在 corpus 中匹配到哪些 cat 的模式"""
    counts = defaultdict(int)
    for cat, patterns in CATEGORY_SIGNALS.items():
        for pat_tpl, weight in patterns:
            pat = pat_tpl.replace('{X}', re.escape(name))
            try:
                n = len(re.findall(pat, corpus_text))
            except re.error:
                continue
            if n:
                counts[cat] += n * weight
    # 三家注关键词（简洁匹配）
    sanjia_patterns = [
        (r'(?<![^。\s])' + re.escape(name) + r'[，、]\s*山\s*名', '山脉', 3),
        (r'(?<![^。\s])' + re.escape(name) + r'[，、]\s*水\s*名', '水域', 3),
        (r'(?<![^。\s])' + re.escape(name) + r'[，、]\s*县\s*名', '县', 3),
        (r'(?<![^。\s])' + re.escape(name) + r'[，、]\s*郡\s*名', '郡', 3),
        (r'(?<![^。\s])' + re.escape(name) + r'[，、]\s*邑\s*名', '城邑', 3),
        (r'(?<![^。\s])' + re.escape(name) + r'[，、]\s*国\s*名', '国家', 3),
        (r'(?<![^。\s])' + re.escape(name) + r'[，、]\s*乡\s*名', '乡里', 3),
        (r'(?<![^。\s])' + re.escape(name) + r'[，、]\s*湖\s*名', '水域', 3),
        (r'(?<![^。\s])' + re.escape(name) + r'[，、]\s*泽\s*名', '水域', 3),
    ]
    for pat, cat, weight in sanjia_patterns:
        try:
            n = len(re.findall(pat, sanjia_text))
            if n:
                counts[cat] += n * weight
        except re.error:
            pass
    return counts


def audit_set(set_name, items, expected_cat, corpus, sanjia):
    """返回 [(name, score, counts, rationale), ...]"""
    results = []
    for name in items:
        counts = scan_signals(name, corpus, sanjia)
        # 支持度：该 expected_cat 占所有命中的比例
        expected_score = counts.get(expected_cat, 0)
        other_score = sum(v for c, v in counts.items() if c != expected_cat)
        total = expected_score + other_score
        support = expected_score / total if total > 0 else None

        # 判定
        if total == 0:
            verdict = 'NO_EVIDENCE'   # 无任何证据
        elif expected_score == 0:
            verdict = 'CONTRADICTS'   # 全是反证据
        elif support < 0.40:
            verdict = 'WEAK_SUPPORT'
        else:
            verdict = 'OK'

        # 取反证据最多的 alternate cat
        alts = [(c, v) for c, v in counts.items() if c != expected_cat and v > 0]
        alts.sort(key=lambda x: -x[1])
        top_alt = alts[0] if alts else None

        results.append({
            'name': name,
            'expected': expected_cat,
            'support': support,
            'expected_score': expected_score,
            'top_alt': top_alt,
            'counts': dict(counts),
            'verdict': verdict,
        })
    return results


def main():
    print('加载 corpus...')
    corpus = load_chapters()
    sanjia = SANJIA_FILE.read_text(encoding='utf-8') if SANJIA_FILE.exists() else ''

    # 要审计的集合
    audit_targets = [
        ('EXPLICIT_REGION',       cp.EXPLICIT_REGION,       '区域'),
        ('EXPLICIT_WATER',        cp.EXPLICIT_WATER,        '水域'),
        ('EXPLICIT_PLAIN',        cp.EXPLICIT_PLAIN,        '原野'),
        ('EXPLICIT_MOUNTAIN',     cp.EXPLICIT_MOUNTAIN,     '山脉'),
        ('EXPLICIT_PASS',         cp.EXPLICIT_PASS,         '关隘'),
        ('EXPLICIT_BUILDING',     cp.EXPLICIT_BUILDING,     '建筑'),
        ('EXPLICIT_TOMB',         cp.EXPLICIT_TOMB,         '陵墓'),
        ('EXPLICIT_NATION',       cp.EXPLICIT_NATION,       '国家'),
        ('EXPLICIT_ANCIENT_CITY', cp.EXPLICIT_ANCIENT_CITY, '城邑'),
        ('EXPLICIT_FICTIONAL',    cp.EXPLICIT_FICTIONAL,    '虚构'),
        ('EXPLICIT_NON_PLACE',    cp.EXPLICIT_NON_PLACE,    '误标'),
        ('HAN_VASSAL_KINGDOMS',   cp.HAN_VASSAL_KINGDOMS,   '郡'),
        # 注：KNOWN_HAN_XIAN/HANSHU_XIAN 太大，按需单独审
    ]

    all_results = {}
    for set_name, items, expected_cat in audit_targets:
        if not items:
            continue
        print(f'审计 {set_name} ({len(items)} 条)...')
        results = audit_set(set_name, items, expected_cat, corpus, sanjia)
        all_results[set_name] = results

    # 生成报告
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = ['# 第七轮 · 白名单静态审计报告', '']
    lines.append(f'> 对 {len(audit_targets)} 个 EXPLICIT_* 集合 + HAN_VASSAL_KINGDOMS 做证据对齐审计。')
    lines.append('> **NO_EVIDENCE** = 完全无证据；**CONTRADICTS** = 全是反证据；**WEAK_SUPPORT** = 支持度<40%；**OK** = 通过')
    lines.append('')

    summary_rows = []
    for set_name, results in all_results.items():
        total = len(results)
        verdicts = defaultdict(int)
        for r in results:
            verdicts[r['verdict']] += 1
        summary_rows.append((set_name, total, verdicts))
        lines.append(f'## {set_name} (总 {total})')
        lines.append('')
        lines.append(f'- OK: {verdicts["OK"]} · NO_EVIDENCE: {verdicts["NO_EVIDENCE"]} · CONTRADICTS: {verdicts["CONTRADICTS"]} · WEAK_SUPPORT: {verdicts["WEAK_SUPPORT"]}')
        lines.append('')
        # 列出非 OK 的（按 verdict 优先级）
        order = {'CONTRADICTS': 0, 'WEAK_SUPPORT': 1, 'NO_EVIDENCE': 2, 'OK': 3}
        flagged = [r for r in results if r['verdict'] != 'OK']
        flagged.sort(key=lambda r: (order[r['verdict']], -(r['top_alt'][1] if r['top_alt'] else 0)))
        if not flagged:
            lines.append('_（全部通过）_')
            lines.append('')
            continue
        for r in flagged[:100]:   # 每个 set 最多展示 100 条
            alt_str = f"→ 建议 **{r['top_alt'][0]}**(score={r['top_alt'][1]})" if r['top_alt'] else '(无反证据)'
            support_str = f"{r['support']:.0%}" if r['support'] is not None else 'N/A'
            lines.append(f'- `{r["name"]}` [{r["verdict"]}] support={support_str} {alt_str}')
            if r['counts']:
                ctx = ', '.join(f'{c}:{v}' for c, v in sorted(r['counts'].items(), key=lambda x: -x[1])[:4])
                lines.append(f'  - 全部命中: {ctx}')
        lines.append('')

    # 开头补 summary 表
    summary_table = ['## 概览', '', '| 集合 | 总数 | OK | NO_EV | CONTRAD | WEAK |', '|------|------|-----|-------|---------|------|']
    for set_name, total, v in summary_rows:
        summary_table.append(f'| {set_name} | {total} | {v["OK"]} | {v["NO_EVIDENCE"]} | {v["CONTRADICTS"]} | {v["WEAK_SUPPORT"]} |')
    summary_table.append('')
    lines = lines[:4] + summary_table + lines[4:]

    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print(f'\n报告: {OUT}')


if __name__ == '__main__':
    main()
