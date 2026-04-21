#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仅重建 docs/entities/feudal-state.html。
直接从 entity_index.json + feudal_state_categories.json 渲染，跳过章节扫描。
"""

import json
from pathlib import Path

import build_entity_index as bei


def main():
    with open(bei.INDEX_JSON, encoding='utf-8') as f:
        index = json.load(f)
    states = index.get('feudal-state', {})
    for k, v in states.items():
        v['refs'] = [tuple(r) for r in v['refs']]
    for type_key, _, css_class, label, filename in bei.ENTITY_TYPES:
        if type_key == 'feudal-state':
            page_html = bei.generate_type_page(type_key, css_class, label, filename, states)
            out = bei.OUTPUT_DIR / filename
            with open(out, 'w', encoding='utf-8') as f:
                f.write(page_html)
            print(f'已重建: {out} ({len(states)} 条)')
            break


if __name__ == '__main__':
    main()
