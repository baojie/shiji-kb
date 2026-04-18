#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 entity_index.json 直接渲染所有实体类别的 HTML 页面（person/place/official/...）。
跳过 chapter_md 扫描，比 build_entity_index.py 快得多；仅当无需重建索引时使用。
"""

import json
from pathlib import Path

import build_entity_index as bei


def main():
    with open(bei.INDEX_JSON, encoding='utf-8') as f:
        index = json.load(f)

    bei.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for type_key, _, css_class, label, filename in bei.ENTITY_TYPES:
        entries = index.get(type_key, {})
        if not entries:
            continue
        # 规范化 refs 为 tuple（generate_type_page 中会用到）
        for v in entries.values():
            if isinstance(v, dict) and 'refs' in v:
                v['refs'] = [tuple(r) for r in v['refs']]
        # time 类：过滤纯汉字数字
        import re as _re
        if type_key == 'time':
            NUM = _re.compile(r'^[零一二三四五六七八九十百千万亿两]+$')
            entries = {k: v for k, v in entries.items() if not NUM.match(k)}

        page_html = bei.generate_type_page(type_key, css_class, label, filename, entries)
        out = bei.OUTPUT_DIR / filename
        out.write_text(page_html, encoding='utf-8')
        print(f'已重建: {out} ({len(entries)} 条)')


if __name__ == '__main__':
    main()
