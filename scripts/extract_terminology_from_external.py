#!/usr/bin/env python3
"""
Phase 4：从外部白话版本抽取"文言 surface → 白话 surface"的分布统计。

输入：data/translation_alignment/NNN.json（对齐记录）
     chapter_md/NNN_*.tagged.md（本库标注，用于确定原文 surface 与 marker）

算法：
  对每个 PN：
    - 提取本库 chapter_md 的所有实体 surface 和 marker
    - 在 hunterhug 白话和白话史记中，查找这些 surface 对应的白话形式
    - 简化：检查 surface 本身是否出现在外部译文（多数情况原形保留），
           若不出现则记为"可能被翻译为别的词"

输出：data/terminology_external.json
  {
    "@": {            # 人名
      "籍": {
        "ours_surface": ["羽（我们写的）"],  # 本库白话中对应 surface
        "hunterhug_hits": ["项羽", "项籍"],  # hunterhug 白话中出现的形式
        "baihua_hits":   ["项羽"],
        "hunterhug_absent": 0,              # hunterhug 中该原 surface 消失的 PN 数
        "total": 5                          # 总出现次数
      }
    },
    ...
  }

次输出：reports/terminology_audit.md  供人工审阅的审计报告
"""

import json
import re
from collections import defaultdict, Counter
from pathlib import Path

ALIGN_DIR = Path('data/translation_alignment')
CHAPTER_MD = Path('chapter_md')
OUTPUT_JSON = Path('data/terminology_external.json')
OUTPUT_AUDIT = Path('reports/terminology_audit.md')

ENTITY_PATTERN = re.compile(r'〖([@=;%&◆^~•!?+#$:\[_\{])([^|〗]+)(?:\|([^〗]+))?〗')
MARKER_NAME = {
    '@': '人名', '=': '地名', ';': '官职', '%': '时间',
    '&': '氏族', '◆': '邦国', '^': '制度', '~': '族群',
    '•': '器物', '!': '天文', '?': '神话', '+': '生物',
    '#': '身份', '$': '数量', '{': '典籍', ':': '礼仪',
    '[': '刑法', '_': '思想',
}


def extract_entities_per_pn(chapter_file: Path):
    """解析 tagged.md，返回 {pn: [(marker, surface, canonical), ...]}"""
    content = chapter_file.read_text()
    results = defaultdict(list)
    # 按 PN 切分
    parts = re.split(r'\[(\d+(?:\.\d+)*)\]\s*', content)
    for i in range(1, len(parts), 2):
        pn = parts[i]
        if pn == '0':
            continue
        body = parts[i + 1] if i + 1 < len(parts) else ''
        for m in ENTITY_PATTERN.finditer(body):
            marker, surface, canonical = m.group(1), m.group(2).strip(), m.group(3)
            if canonical:
                canonical = canonical.strip()
            results[pn].append((marker, surface, canonical))
    return results


def main():
    # 累积 {marker: {surface: stats}}
    stats = defaultdict(lambda: defaultdict(lambda: {
        'total': 0,
        'hunterhug_kept': 0,      # hunterhug 白话中 surface 字面出现
        'hunterhug_absent': 0,    # hunterhug 有译文但 surface 字面消失（可能被翻译）
        'hunterhug_no_match': 0,  # hunterhug 对齐失败或空
        'baihua_kept': 0,
        'baihua_absent': 0,
        'baihua_no_match': 0,
        'canonical': '',          # 源标注的规范名（若有）
        'chapters': set(),        # 出现过的章节
    }))

    for align_file in sorted(ALIGN_DIR.glob('*.json')):
        data = json.load(open(align_file))
        ch = data['chapter']
        title = data['title']
        tagged = next(CHAPTER_MD.glob(f'{ch}_*.tagged.md'), None)
        if not tagged:
            continue
        entities_per_pn = extract_entities_per_pn(tagged)

        for rec in data['records']:
            pn = rec['pn']
            hh = rec.get('hunterhug', '')
            bh = rec.get('baihua', '')
            hh_conf = rec.get('hunterhug_conf', 0.0)

            for marker, surface, canonical in entities_per_pn.get(pn, []):
                bucket = stats[marker][surface]
                bucket['total'] += 1
                bucket['chapters'].add(f'{ch}')
                if canonical and not bucket['canonical']:
                    bucket['canonical'] = canonical

                # hunterhug 检查
                if hh and hh_conf >= 0.5:
                    if surface in hh:
                        bucket['hunterhug_kept'] += 1
                    else:
                        bucket['hunterhug_absent'] += 1
                else:
                    bucket['hunterhug_no_match'] += 1
                # 白话史记 检查
                if bh:
                    if surface in bh:
                        bucket['baihua_kept'] += 1
                    else:
                        bucket['baihua_absent'] += 1
                else:
                    bucket['baihua_no_match'] += 1

    # 序列化
    out = {}
    for marker, surfaces in stats.items():
        out[marker] = {}
        for surface, b in surfaces.items():
            out[marker][surface] = {
                'total': b['total'],
                'canonical': b['canonical'],
                'chapters': sorted(b['chapters']),
                'hunterhug_kept': b['hunterhug_kept'],
                'hunterhug_absent': b['hunterhug_absent'],
                'hunterhug_no_match': b['hunterhug_no_match'],
                'baihua_kept': b['baihua_kept'],
                'baihua_absent': b['baihua_absent'],
                'baihua_no_match': b['baihua_no_match'],
            }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    # 审计报告：找"外部倾向翻译"的 surface（absent 率高 = 外部没保留原字样）
    audit = ['# 术语审计（外部版本的翻译倾向）', '',
             '列出：外部白话中"原 surface 消失率"较高的实体——即译者倾向于把文言词翻译为白话。',
             '',
             'threshold: 字面消失率 >= 0.5 且出现次数 >= 3',
             '',
             '| 类 | surface | 规范名 | 总数 | hunterhug消失率 | 白话消失率 | 章节 |',
             '|----|---------|--------|------|----------------|-----------|------|']
    rows = []
    for marker, surfaces in out.items():
        for surface, b in surfaces.items():
            if b['total'] < 3:
                continue
            hh_denom = b['hunterhug_kept'] + b['hunterhug_absent']
            bh_denom = b['baihua_kept'] + b['baihua_absent']
            hh_absent_rate = b['hunterhug_absent'] / hh_denom if hh_denom else None
            bh_absent_rate = b['baihua_absent'] / bh_denom if bh_denom else None
            # 只关心至少一个有显著消失率的
            high = (hh_absent_rate and hh_absent_rate >= 0.5) or \
                   (bh_absent_rate and bh_absent_rate >= 0.5)
            if not high:
                continue
            rows.append((
                marker, surface, b['canonical'], b['total'],
                f'{hh_absent_rate:.0%}' if hh_absent_rate is not None else '-',
                f'{bh_absent_rate:.0%}' if bh_absent_rate is not None else '-',
                ','.join(b['chapters'][:5]) + ('...' if len(b['chapters']) > 5 else ''),
            ))
    # 按总数排序
    rows.sort(key=lambda r: -r[3])
    for r in rows[:200]:
        audit.append(f'| {MARKER_NAME.get(r[0], r[0])} | {r[1]} | {r[2] or "—"} | {r[3]} | {r[4]} | {r[5]} | {r[6]} |')
    OUTPUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_AUDIT.write_text('\n'.join(audit))

    print(f'已生成：{OUTPUT_JSON}')
    print(f'审计报告：{OUTPUT_AUDIT}')
    print(f'涉及 {sum(len(v) for v in out.values())} 个 (marker,surface) 对')
    print(f'高消失率候选：{len(rows)} 条')


if __name__ == '__main__':
    main()
