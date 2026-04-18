#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把当前地名分类的全部 (name, category, confidence) 三元组导出为 CSV，
方便在表格软件里排序/过滤/统计。

输出：doc/entities/地名反思/置信度全量_本轮.csv

字段：
  name           地名
  category       分类（可能一个 name 多行，每行一 category）
  primary        是否主分类（True/False）
  confidence     置信度 (0.0-1.0)
  evidence_count 命中证据数
  evidence       命中规则拼接（分号分隔）
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / 'kg' / 'entities' / 'scripts'))
import classify_places as cp
import confidence_report as cr

INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
CATS_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'place_categories.json'
OUT_CSV = _ROOT / 'doc' / 'entities' / '地名反思' / '置信度全量_本轮.csv'


def main():
    index = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
    places = index['place']
    cats_data = json.loads(CATS_JSON.read_text(encoding='utf-8'))

    hints = cp.build_context_hints(places.keys())
    for nm, cs in cp.build_sanjia_hints(places.keys()).items():
        for c, n in cs.items():
            hints[nm][c] += n

    peer_groups = cp.build_peer_groups(places.keys())
    peer_map = defaultdict(set)
    for g in peer_groups:
        for n in g:
            peer_map[n].update(x for x in g if x != n)
    all_places = set(places.keys())

    rows = []
    for name, cats in cats_data.items():
        refs = places[name]['refs']
        ref_count = places[name]['count']
        for i, cat in enumerate(cats):
            primary = (i == 0)
            evidence = cr.score_evidence(name, cat, refs, hints,
                                         cp_mod=cp, all_places=all_places,
                                         peer_map_cache=peer_map)
            if evidence:
                max_conf = max(e[1] for e in evidence)
                summary = '; '.join(f'{e[0]}({e[1]:.2f})' for e in evidence)
            else:
                max_conf = 0.30
                summary = 'NO_EVIDENCE(仅间接)'
            rows.append({
                'name': name,
                'category': cat,
                'is_primary': 'Y' if primary else '',
                'confidence': round(max_conf, 2),
                'evidence_count': len(evidence),
                'ref_count': ref_count,
                'evidence': summary,
            })

    # 按 (category asc, confidence asc, name asc) 排序，便于按类别审阅
    rows.sort(key=lambda r: (r['category'], r['confidence'], r['name']))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'name', 'category', 'is_primary',
            'confidence', 'evidence_count', 'ref_count', 'evidence',
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f'写入: {OUT_CSV}')
    print(f'总 (name,cat) 组合: {len(rows)}')
    # 置信度档位统计
    bins = {'≥0.90': 0, '0.70-0.89': 0, '0.50-0.69': 0, '<0.50': 0}
    for r in rows:
        c = r['confidence']
        if c >= 0.90:   bins['≥0.90'] += 1
        elif c >= 0.70: bins['0.70-0.89'] += 1
        elif c >= 0.50: bins['0.50-0.69'] += 1
        else:           bins['<0.50'] += 1
    print('置信度分布:')
    for k, v in bins.items():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
