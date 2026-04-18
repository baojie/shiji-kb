#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仅重建 docs/entities/place.html。
直接从 entity_index.json + place_categories.json 渲染，跳过章节扫描。
"""

import json
from pathlib import Path

import build_entity_index as bei


def main():
    with open(bei.INDEX_JSON, encoding='utf-8') as f:
        index = json.load(f)
    places = index.get('place', {})
    # 统一 refs 为 tuple，匹配 generate_type_page 预期
    for k, v in places.items():
        v['refs'] = [tuple(r) for r in v['refs']]
    # 查找 place 对应的 css_class / label / filename
    for type_key, _, css_class, label, filename in bei.ENTITY_TYPES:
        if type_key == 'place':
            page_html = bei.generate_type_page(type_key, css_class, label, filename, places)
            out = bei.OUTPUT_DIR / filename
            with open(out, 'w', encoding='utf-8') as f:
                f.write(page_html)
            print(f'已重建: {out} ({len(places)} 条)')
            break


if __name__ == '__main__':
    main()
