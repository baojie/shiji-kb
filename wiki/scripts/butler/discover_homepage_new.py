#!/usr/bin/env python3
"""
discover_homepage_new.py — 扫描当前首页页面，找出尚未打上「首页精品」tag 的页面。

用法:
    python3 wiki/scripts/butler/discover_homepage_new.py

逻辑:
    1. 用与首页相同的评分规则，计算当前会出现在首页的页面集合
    2. 读取每个页面的 frontmatter，检查 tags 中是否包含「首页精品」
    3. 输出缺少此 tag 的页面，格式为 H21 housekeeping 队列条目

背景:
    进入首页的页面代表知识库的门面，应在 H21 升级后加上「首页精品」tag 作为认证标志。
    此脚本每 10 轮运行一次，确保新晋首页页面能及时进入 H21 升级队列。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES_JSON = ROOT / 'wiki/public/pages.json'
PAGES_DIR = ROOT / 'wiki/public/pages'

CAPS = {'person': 6, 'story': 4, 'sanwen': 3, 'overview': 2, 'concept': 2, 'chapter': 2}
SKIP = {'redirect', 'disambiguation', 'year', 'place', 'event', 'special', 'list', '侯国', 'skill'}
MAX_HOMEPAGE = 18
TARGET_TAG = '首页精品'

FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)


def get_homepage_pages(pages: dict) -> list[dict]:
    """用首页评分规则得出当前首页页面集合。只有 quality=premium 的页面可上首页。"""
    def score(p: dict) -> int:
        return p.get('quality_score') or 0

    all_pages = [{'id': k, **v} for k, v in pages.items()
                 if v.get('quality') == 'premium']
    all_pages.sort(key=score, reverse=True)

    counts: dict[str, int] = {}
    result = []
    for p in all_pages:
        if len(result) >= MAX_HOMEPAGE:
            break
        t = p.get('type', '')
        if t in SKIP or t not in CAPS:
            continue
        n = counts.get(t, 0)
        if n >= CAPS[t]:
            continue
        counts[t] = n + 1
        result.append(p)
    return result


def get_page_tags(slug: str) -> list[str]:
    """从页面 frontmatter 读取 tags 字段（支持内联 [a,b] 和多行 - item 格式）。"""
    path = PAGES_DIR / f'{slug}.md'
    if not path.exists():
        return []
    text = path.read_text(encoding='utf-8')
    m = FRONTMATTER_RE.match(text)
    if not m:
        return []
    fm = m.group(1)
    in_tags = False
    tags: list[str] = []
    for line in fm.splitlines():
        stripped = line.strip()
        if stripped.startswith('tags:'):
            val = stripped[5:].strip()
            if val.startswith('[') and val.endswith(']'):
                return [x.strip().strip('"\'') for x in val[1:-1].split(',') if x.strip()]
            in_tags = True
            continue
        if in_tags:
            if stripped.startswith('- '):
                tags.append(stripped[2:].strip().strip('"\''))
            elif stripped and not stripped.startswith(' ') and not stripped.startswith('-'):
                break
    return tags


def main() -> int:
    data = json.loads(PAGES_JSON.read_text(encoding='utf-8'))
    pages = data['pages']

    homepage_pages = get_homepage_pages(pages)
    needs_upgrade: list[dict] = []

    for p in homepage_pages:
        slug = p['id']
        tags = get_page_tags(slug)
        if TARGET_TAG not in tags:
            needs_upgrade.append({
                'slug': slug,
                'type': p.get('type', ''),
                'score': p.get('quality_score') or 0,
                'quality': p.get('quality', ''),
            })

    if not needs_upgrade:
        print(f'✓ 所有 {len(homepage_pages)} 个首页页面已有「{TARGET_TAG}」tag，无需处理。')
        return 0

    print(f'## discover_homepage_new · {len(needs_upgrade)} 个首页页面缺少「{TARGET_TAG}」tag\n')
    for p in needs_upgrade:
        print(
            f'- [ ] **H21** | [[{p["slug"]}]] | '
            f'新晋首页页面（type={p["type"]}, score={p["score"]}, quality={p["quality"]}），'
            f'需执行精品页升级并加 tag「{TARGET_TAG}」'
        )

    print(f'\n[discover_homepage_new] {len(needs_upgrade)} 页需要 H21 升级。', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
