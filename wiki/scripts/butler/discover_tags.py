#!/usr/bin/env python3
"""
discover_tags.py — 为 wiki 页推荐 tags.

用法:
    python3 wiki/scripts/butler/discover_tags.py
    python3 wiki/scripts/butler/discover_tags.py --slug 刘邦  # 只查一个

规则:
    - era:      按 frontmatter.birth_ce 落到 tags_vocabulary.era.ranges 区间
    - identity: 看 semantic.json 的 chapters top 分布, 各区间占比 ≥ 阈值即匹配
    - theme:    slug 或 canonical 落在 theme.seed 列表

输出: 每页推荐 tags 清单 (已有 tags 不重复推), 可直接入 queue.md 作 add-tag.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VOCAB = ROOT / 'wiki/data/tags_vocabulary.json'
SEMANTIC = ROOT / 'wiki/data/semantic.json'
PAGES_DIR = ROOT / 'wiki/public/pages'

FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)


def parse_frontmatter_simple(text):
    """轻量解析, 只取 tags / birth_ce."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith('tags:'):
            val = line[5:].strip()
            if val.startswith('[') and val.endswith(']'):
                items = [x.strip() for x in val[1:-1].split(',') if x.strip()]
                out['tags'] = items
        elif line.startswith('birth_ce:'):
            try:
                out['birth_ce'] = int(line[9:].strip())
            except ValueError:
                pass
        elif line.startswith('death_ce:'):
            try:
                out['death_ce'] = int(line[9:].strip())
            except ValueError:
                pass
    return out


def era_tag(birth_ce, death_ce, vocab_era):
    """v0.2 (W5 v3 提案 10): 优先 death_ce (政治生涯), fallback birth_ce."""
    target = death_ce if death_ce is not None else birth_ce
    if target is None:
        return None
    for r in vocab_era['_ranges']:
        if r['birth_min'] <= target <= r['birth_max']:
            return r['name']
    return None


def identity_tags(entity, vocab_identity):
    if not entity:
        return []
    chapters = entity.get('chapters', [])
    total = sum(c['count'] for c in chapters) or 1
    by_prefix_count = {}
    for c in chapters:
        ch = c['chapter']
        m = re.match(r'^(\d{3})_', ch)
        if not m:
            continue
        prefix = m.group(1)
        by_prefix_count[prefix] = by_prefix_count.get(prefix, 0) + c['count']

    out = []
    for rule in vocab_identity['_rules']:
        lo, hi = rule['chapter_prefix_range']
        covered = sum(v for p, v in by_prefix_count.items() if lo <= p <= hi)
        if covered / total >= rule['threshold']:
            out.append(rule['name'])
    return out


def theme_tags(slug, entity, vocab_theme_seed):
    out = []
    aliases = set([slug] + (entity.get('aliases', []) if entity else []))
    for theme, members in vocab_theme_seed.items():
        if aliases & set(members):
            out.append(theme)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', help='只查一个')
    ap.add_argument('--format', choices=['md', 'json'], default='md')
    args = ap.parse_args()

    vocab = json.loads(VOCAB.read_text(encoding='utf-8'))
    semantic = json.loads(SEMANTIC.read_text(encoding='utf-8'))
    entities = semantic['entities']

    slugs = [args.slug] if args.slug else [p.stem for p in PAGES_DIR.glob('*.md')]

    results = []
    for slug in slugs:
        p = PAGES_DIR / f'{slug}.md'
        if not p.exists():
            continue
        fm = parse_frontmatter_simple(p.read_text(encoding='utf-8'))
        current = set(fm.get('tags', []))
        entity = entities.get(slug)

        suggested = set()
        if e_tag := era_tag(fm.get('birth_ce'), fm.get('death_ce'), vocab['era']):
            suggested.add(e_tag)
        suggested.update(identity_tags(entity, vocab['identity']))
        suggested.update(theme_tags(slug, entity, vocab['theme']['_seed']))

        new = suggested - current
        if new:
            results.append({
                'slug': slug,
                'current': sorted(current),
                'suggested_new': sorted(new),
            })

    if args.format == 'json':
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f'## discover_tags · {len(results)} 页有新标签建议\n')
        for r in results:
            extras = ', '.join(r['suggested_new'])
            print(f'- [ ] {r["slug"]}: `add-tag` (+ {extras}) [P1]')
    print(f'\n[discover_tags] {len(results)} 页有新建议.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
