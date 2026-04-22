#!/usr/bin/env python3
"""Mark chapters 009-012 and their stories as 'done' in catalog.json, and mirror."""
import json
import os

CATALOG_PRIMARY = '/home/baojie/work/knowledge/shiji-kb/data/stories/catalog.json'
CATALOG_MIRROR = '/home/baojie/work/knowledge/shiji-kb/docs/special/data/stories/catalog.json'

TARGET = {'009', '010', '011', '012'}

d = json.load(open(CATALOG_PRIMARY, encoding='utf-8'))

count_chapter = 0
count_stories = 0
for ch in d.get('chapters', []):
    if ch.get('chapter_num') in TARGET:
        ch['status'] = 'done'
        count_chapter += 1
        for s in ch.get('stories', []):
            s['status'] = 'done'
            count_stories += 1
        print(f"  marked {ch['chapter_num']} {ch.get('chapter_title')}: {len(ch.get('stories', []))} stories")

with open(CATALOG_PRIMARY, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
os.makedirs(os.path.dirname(CATALOG_MIRROR), exist_ok=True)
with open(CATALOG_MIRROR, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f"Total: {count_chapter} chapters, {count_stories} stories marked done.")
print(f"Saved: {CATALOG_PRIMARY}")
print(f"Saved: {CATALOG_MIRROR}")
