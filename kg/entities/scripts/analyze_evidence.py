#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 place_evidence_bundles.json 中挖掘"分类信号"并交叉验证当前分类。

信号类型：
  - 三家注关键词命中：X县/X山/X水/X国/X邑/X塞/X泽 等自带类型说明
  - 共现官职：X太守/X守/X令/X丞/X尉 等
  - 动词触发：渡X/攻X/封于X/葬于X 等（已有 L3，这里看是否覆盖）
  - 共现制度：关X 是关隘 / 塞X / 苑X 等

输出：
  doc/entities/地名反思/第三轮_证据分析.md —— 按"疑似误分类"优先排序
"""

import json
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUNDLES = _ROOT / 'kg' / 'entities' / 'data' / 'place_evidence_bundles.json'
CATS_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'place_categories.json'
OUT = _ROOT / 'doc' / 'entities' / '地名反思' / '第三轮_证据分析.md'

# 三家注关键词 → 推定类别
SANJIA_TYPE_MARKERS = [
    (r'县名', '县'),
    (r'[古今]县', '县'),
    (r'山名', '山脉'),
    (r'山也', '山脉'),
    (r'水名', '水域'),
    (r'泽名', '水域'),
    (r'水也', '水域'),
    (r'泽也', '水域'),
    (r'湖名', '水域'),
    (r'郡名', '郡'),
    (r'郡也', '郡'),
    (r'故国', '国家'),
    (r'国名', '国家'),
    (r'国也', '国家'),
    (r'乡名', '乡里'),
    (r'邑名', '城邑'),
    (r'邑也', '城邑'),
    (r'关名', '关隘'),
    (r'塞也', '关隘'),
    (r'塞名', '关隘'),
    (r'之塞', '关隘'),
    (r'苑', '建筑'),
    (r'台也', '建筑'),
    (r'宫也', '建筑'),
    (r'冢也', '陵墓'),
    (r'葬', '陵墓'),    # 弱信号
]

# 共现官职 → 类别
OFFICIAL_MARKERS = [
    (r'太守|郡守', '郡'),
    (r'内史', '郡'),
    (r'尹', '郡'),
    (r'县令|县长|县丞|县尉|邑令', '县'),
    (r'都尉', '郡'),
    (r'亭长', '乡里'),
    (r'乡[长啬]?夫', '乡里'),
]


def detect_signals(name, bundle):
    """返回该 name 的建议类别 Counter，以及证据链描述"""
    suggestions = Counter()
    rationale = []

    # 1. 三家注关键词扫描
    for mention in bundle.get('sanjia_mentions', []):
        # 去掉【X】标记后在 mention 周围检查 markers
        after_idx = mention.find('】')
        if after_idx < 0:
            continue
        suffix = mention[after_idx+1:]   # 名字后的内容
        prefix = mention[:after_idx]
        for pat, cat in SANJIA_TYPE_MARKERS:
            if re.search(pat, suffix[:15]) or re.search(pat, prefix[-15:]):
                suggestions[cat] += 2   # 三家注权重较高
                rationale.append(f'三家注"{pat}": {mention[:60]}...')
                break

    # 2. 共现官职扫描
    for tag_key, cnt in bundle.get('cooccur_tags', {}).items():
        if not tag_key.startswith('官职:'):
            continue
        officer = tag_key.split(':', 1)[1]
        for pat, cat in OFFICIAL_MARKERS:
            if re.search(pat, officer):
                suggestions[cat] += min(cnt, 2)
                rationale.append(f'同句官职"{officer}" ×{cnt}')
                break

    # 3. 共现地名：如果本条在"X、Y郡" 或 "X郡" 中
    # 已被 build_context_hints 的 MULTI_JUN 覆盖，这里从 context_windows 里再确认
    for ctx in bundle.get('context_windows', []):
        if re.search(rf'【{re.escape(name)}】郡', ctx):
            suggestions['郡'] += 3
            rationale.append(f'直称 X郡: {ctx[:60]}...')
        if re.search(rf'【{re.escape(name)}】侯', ctx) and not re.search(rf'【{re.escape(name)}】侯国', ctx):
            suggestions['县'] += 1
            rationale.append(f'X侯: {ctx[:60]}...')
        # 山的特殊模式：X山 / 登X / 禅X
        if re.search(rf'【{re.escape(name)}】之[山阳]', ctx):
            suggestions['山脉'] += 1
            rationale.append(f'X之山/阳: {ctx[:60]}...')

    return suggestions, rationale


def main():
    bundles = json.loads(BUNDLES.read_text(encoding='utf-8'))
    cats = json.loads(CATS_JSON.read_text(encoding='utf-8'))

    # 分析所有 bundle
    suspect = []   # 疑似误分类
    confirm = 0
    no_signal = 0
    for name, b in bundles.items():
        suggestions, rationale = detect_signals(name, b)
        current = cats.get(name, [])
        primary = current[0] if current else ''
        if not suggestions:
            no_signal += 1
            continue
        top_cat, top_score = suggestions.most_common(1)[0]
        if top_cat in current:
            confirm += 1
            continue
        # 建议类别不在当前分类中：疑似误分类
        suspect.append((name, primary, current, top_cat, top_score, rationale))

    # 按 score 倒序
    suspect.sort(key=lambda x: -x[4])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        '# 第三轮 · 证据分析（基于证据包）',
        '',
        f'从 {len(bundles)} 个低置信度 place 证据包中，基于三家注关键词 / 共现官职 / 上下文模式提炼出分类信号。',
        '',
        f'- 建议类别**已在当前分类中**（确认）：**{confirm}** 条',
        f'- 建议类别**不在当前分类中**（疑似误分类）：**{len(suspect)}** 条',
        f'- 无证据信号：**{no_signal}** 条',
        '',
        '## 疑似误分类（按证据强度降序）',
        '',
    ]
    for name, primary, current, new_cat, score, rationale in suspect[:200]:
        lines.append(f'### `{name}` 当前=[{"/".join(current)}] → 建议追加 **{new_cat}** (score={score})')
        for r in rationale[:3]:
            lines.append(f'  - {r}')
        lines.append('')
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print(f'写入: {OUT}')
    print(f'确认 {confirm} / 疑似 {len(suspect)} / 无信号 {no_signal}')


if __name__ == '__main__':
    main()
