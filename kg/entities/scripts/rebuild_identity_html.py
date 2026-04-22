#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仅重建 docs/entities/identity.html。
直接从 entity_index.json + identity_categories.json 渲染，跳过章节扫描。
"""

import json

import build_entity_index as bei


def main():
    with open(bei.INDEX_JSON, encoding='utf-8') as f:
        index = json.load(f)
    identities = index.get('identity', {})
    for k, v in identities.items():
        v['refs'] = [tuple(r) for r in v['refs']]
    for type_key, _, css_class, label, filename in bei.ENTITY_TYPES:
        if type_key == 'identity':
            page_html = bei.generate_type_page(type_key, css_class, label, filename, identities)
            out = bei.OUTPUT_DIR / filename
            with open(out, 'w', encoding='utf-8') as f:
                f.write(page_html)
            print(f'已重建: {out} ({len(identities)} 条)')
            break


if __name__ == '__main__':
    main()
