#!/usr/bin/env python3
"""
build_entity_concordance.py

扫描所有 chapter_md/NNN_*.tagged.md，收集每个实体在全书中的
所有出现（而非仅首次），生成完整索引（concordance）。

输出：docs/wiki/data/entity_concordance.json

数据结构：
{
  "generated": "...",
  "total_occurrences": 107235,
  "entity_count": 12370,
  "entities": {
    "黄帝": {
      "prefix": "@",
      "type_label": "人物",
      "has_page": true,
      "total": 150,
      "first_chapter": "001",
      "first_chapter_name": "五帝本纪",
      "occurrences": [["001","五帝本纪","1"], ...]
    },
    ...
  }
}
"""

import json
import re
import os
import sys
import glob
from datetime import datetime, timezone
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTER_DIR = os.path.join(REPO_ROOT, 'chapter_md')
PAGES_JSON  = os.path.join(REPO_ROOT, 'docs', 'wiki', 'pages.json')
OUTPUT_JSON = os.path.join(REPO_ROOT, 'docs', 'wiki', 'data', 'entity_concordance.json')

PREFIX_LABELS = {
    '@': '人物', '=': '地名', '~': '部族', '^': '制度',
    '•': '器物', '+': '动植物', '$': '数量', '!': '天文',
    '#': '身份', '&': '族群', ';': '官职', '◆': '邦国',
}
SKIP_PREFIXES = {'%', '_'}

ENTITY_RE = re.compile(
    r'〖([^〗\s|])([^〗|]*?)(?:\|([^〗]*))?〗'
)
PARA_RE = re.compile(r'^\[(\d+(?:\.\d+)*)\]')


REDIRECT_RE = re.compile(r'^redirect:\s*(.+)', re.MULTILINE)


def load_pages_json():
    with open(PAGES_JSON, encoding='utf-8') as f:
        data = json.load(f)
    alias_index = data.get('alias_index', {})
    pages = data.get('pages', {})
    pages_set = set(pages.keys())
    pages_dir = os.path.dirname(PAGES_JSON)
    # 构建 redirect 映射：从实际 markdown 文件中读取 redirect 字段
    redirect_map = {}
    for pid, p in pages.items():
        if p.get('type') in ('redirect', 'REDIRECT'):
            md_path = os.path.join(pages_dir, 'wiki', p.get('path', ''))
            if not os.path.exists(md_path):
                md_path = os.path.join(pages_dir, p.get('path', ''))
            try:
                with open(md_path, encoding='utf-8') as mf:
                    content = mf.read(500)
                m = REDIRECT_RE.search(content)
                if m:
                    redirect_map[pid] = m.group(1).strip()
            except (FileNotFoundError, OSError):
                pass
    return alias_index, pages_set, redirect_map


def extract_chapter_info(filename):
    m = re.match(r'^(\d+)_(.+?)\.tagged\.md$', os.path.basename(filename))
    return (m.group(1), m.group(2)) if m else (None, None)


def is_valid_name(name):
    if not name or not name.strip():
        return False
    stripped = re.sub(r'[\s　，。？！、：；""''「」『』【】《》〈〉·…—～()（）\-]', '', name)
    return len(stripped) > 0


def main():
    print('加载 pages.json ...')
    alias_index, pages_set, redirect_map = load_pages_json()

    # entity_data[canonical_name] = {
    #   prefix, type_label, has_page, occurrences: list of [ch_num, ch_name, para_id]
    # }
    entity_data = {}
    # 记录每个实体首次出现的全局顺序（用于排序）
    entity_first_order = {}
    global_order = 0

    files = sorted(glob.glob(os.path.join(CHAPTER_DIR, '*.tagged.md')))
    print(f'扫描 {len(files)} 个章节文件 ...')

    total_occurrences = 0

    for filepath in files:
        chapter_num, chapter_name = extract_chapter_info(filepath)
        if chapter_num is None:
            continue

        current_para = '0'
        with open(filepath, encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                m_para = PARA_RE.match(line)
                if m_para:
                    current_para = m_para.group(1)

                for m in ENTITY_RE.finditer(line):
                    prefix = m.group(1)
                    display_name = m.group(2).strip()
                    raw_canonical = m.group(3)

                    if prefix in SKIP_PREFIXES or prefix not in PREFIX_LABELS:
                        continue
                    if not is_valid_name(display_name):
                        continue

                    if raw_canonical and raw_canonical.strip():
                        canonical_name = raw_canonical.strip()
                    else:
                        canonical_name = alias_index.get(display_name, display_name)

                    canonical_name = canonical_name.strip()
                    if not is_valid_name(canonical_name):
                        continue

                    # 追踪 redirect（最多3跳，防止循环）
                    for _ in range(3):
                        target = redirect_map.get(canonical_name)
                        if target and target != canonical_name:
                            canonical_name = target
                        else:
                            break

                    # 以 (canonical_name, prefix) 为复合键——同名不同类型分开统计
                    key = (canonical_name, prefix)
                    if key not in entity_data:
                        entity_data[key] = {
                            'prefix': prefix,
                            'type_label': PREFIX_LABELS[prefix],
                            'has_page': canonical_name in pages_set,
                            'occurrences': [],
                        }
                        entity_first_order[key] = global_order
                        global_order += 1

                    entity_data[key]['occurrences'].append(
                        [chapter_num, chapter_name, current_para]
                    )
                    total_occurrences += 1

        print(f'  {chapter_num} {chapter_name}: 累计实体 {len(entity_data):,}, 出现 {total_occurrences:,}', end='\r')

    print()
    print(f'\n实体总数: {len(entity_data):,}')
    print(f'出现总次数: {total_occurrences:,}')

    # 添加统计字段，按首次出现顺序排序输出
    # key = (canonical_name, prefix)，输出时用 canonical_name 作 JSON key（若冲突加后缀）
    entities_out = {}
    used_names = {}
    for key in sorted(entity_data.keys(), key=lambda k: entity_first_order[k]):
        cname, prefix = key
        d = entity_data[key]
        occ = d['occurrences']
        # 若同名不同类型，JSON key 加类型后缀区分
        out_key = cname if cname not in used_names else f"{cname}（{d['type_label']}）"
        used_names[cname] = True
        entities_out[out_key] = {
            'canonical_name': cname,
            'prefix': d['prefix'],
            'type_label': d['type_label'],
            'has_page': d['has_page'],
            'total': len(occ),
            'first_rank': entity_first_order[key] + 1,
            'first_chapter': occ[0][0],
            'first_chapter_name': occ[0][1],
            'occurrences': occ,
        }

    output = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'total_occurrences': total_occurrences,
        'entity_count': len(entity_data),
        'entities': entities_out,
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

    size_mb = os.path.getsize(OUTPUT_JSON) / 1024 / 1024
    print(f'\n输出: {OUTPUT_JSON} ({size_mb:.1f} MB)')

    # 统计摘要
    from collections import Counter
    type_counts = Counter(d['type_label'] for d in entity_data.values())
    print('\n按类型分布:')
    for t, c in type_counts.most_common():
        print(f'  {t}: {c:,}')

    print('\nTop 10 出现最多实体:')
    top = sorted(entity_data.items(), key=lambda x: -len(x[1]['occurrences']))[:10]
    for (name, prefix), d in top:
        print(f'  {name} ({d["type_label"]}): {len(d["occurrences"]):,} 次')


if __name__ == '__main__':
    main()
