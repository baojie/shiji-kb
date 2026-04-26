#!/usr/bin/env python3
"""
战争索引导入脚本 - Append-Only

规则：
  1. 只追加 war_id / source_count 到 ::: meta 块（或新建 meta 块）
  2. 为多源战争追加 ## 各章节记载 节（仅在不存在时）
  3. 跳过 redirect 页面
  4. 绝不替换任何原有内容

用法：
    python3 scripts/import_war_index.py [--dry-run]
"""

import json
import re
import subprocess
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / 'wiki' / 'public' / 'pages'
WARS_JSON = ROOT / 'data' / 'wars.json'
KG_WARS_JSON = ROOT / 'kg' / 'events' / 'data' / 'wars.json'


def record_rev(slug: str, summary: str) -> None:
    subprocess.run(
        [sys.executable,
         str(ROOT / 'wiki' / 'scripts' / 'butler' / 'record_revision.py'),
         slug, '--summary', summary, '--author', 'butler'],
        capture_output=True,
    )


def clean_chapter_name(ch: str) -> str:
    """'005_秦本纪_事件索引' → '秦本纪'"""
    ch = ch.replace('_事件索引', '')
    parts = ch.split('_', 1)
    return parts[1] if len(parts) > 1 else ch


def add_war_id_to_meta(content: str, war_id: str, source_count: int) -> str:
    """在 ::: meta 块的关闭 ::: 前插入 war_id / source_count。"""
    # 匹配 ::: meta ... ::: 块（支持 ":::" 或 "::: meta"）
    def replace_meta(m: re.Match) -> str:
        block = m.group(0)
        # 在最后一行 ::: 前插入
        return re.sub(
            r'^(:::)\s*$',
            f'war_id: {war_id}\nsource_count: {source_count}\n:::',
            block,
            count=1,
            flags=re.MULTILINE,
        )

    return re.sub(r':::[ \t]*meta\b.*?^:::', replace_meta, content,
                  count=1, flags=re.DOTALL | re.MULTILINE)


def insert_meta_block_after_frontmatter(
    content: str, war_id: str, source_count: int,
    location: str, chapters: list[str],
) -> str:
    """在 frontmatter 结束后插入新的 ::: meta 块。"""
    # 找第二个 '---'（frontmatter 结束）
    first = content.find('---')
    if first == -1:
        return content
    second = content.find('\n---', first + 3)
    if second == -1:
        return content
    end_fm = second + 4  # 跳过 '\n---'，再跳过换行

    lines = ['', '::: meta', f'event_type: 战争', f'war_id: {war_id}',
             f'source_count: {source_count}']
    if location:
        lines.append(f'location: "{location}"')
    if chapters:
        lines.append(f'chapter: [{", ".join(chapters)}]')
    lines.append(':::')
    lines.append('')

    meta_str = '\n'.join(lines)
    return content[:end_fm] + meta_str + content[end_fm:]


def build_sources_section(descriptions: list[dict]) -> str:
    lines = ['\n\n## 各章节记载（战争索引导入）\n']
    for desc in descriptions:
        chap_name = clean_chapter_name(desc.get('chapter', ''))
        src_id = desc.get('source', '')
        lines.append(f'\n### {chap_name} ({src_id})\n')
        text = desc.get('text', '').strip()
        if text:
            lines.append(text + '\n')
    return ''.join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description='战争索引 append-only 导入')
    ap.add_argument('--dry-run', action='store_true', help='只预览，不写文件')
    args = ap.parse_args()

    wars = json.loads(WARS_JSON.read_text('utf-8'))
    kg_wars: dict[str, dict] = {
        w['war_id']: w
        for w in json.loads(KG_WARS_JSON.read_text('utf-8'))
    }

    updated = skipped = redirects = missing = 0

    for w in wars:
        name = w['war_name']
        war_id = w['war_id']
        source_count = w['source_count']
        page_path = PAGES / f'{name}.md'

        if not page_path.exists():
            print(f'  MISSING: {name}')
            missing += 1
            continue

        content = page_path.read_text('utf-8')

        if 'type: redirect' in content:
            redirects += 1
            continue

        new_content = content
        reasons = []

        # ── 1. 追加 war_id / source_count 到 meta 块 ──────────────────────
        if 'war_id:' not in content:
            if re.search(r':::[ \t]*meta\b', content):
                new_content = add_war_id_to_meta(new_content, war_id, source_count)
                reasons.append('add war_id to meta')
            else:
                # 无 meta 块 → 新建（从 kg_wars 取 location / chapters）
                kg = kg_wars.get(war_id, {})
                location = ', '.join(kg.get('location', []))
                chapters = [
                    clean_chapter_name(ch)
                    for ch in kg.get('chapters', w.get('chapters', []))
                ]
                new_content = insert_meta_block_after_frontmatter(
                    new_content, war_id, source_count, location, chapters
                )
                reasons.append('create meta block')

        # ── 2. 为多源战争追加 各章节记载 ─────────────────────────────────
        if source_count > 1 and '各章节记载' not in content:
            kg = kg_wars.get(war_id, {})
            descriptions = kg.get('descriptions', [])
            if descriptions:
                new_content = new_content.rstrip('\n') + build_sources_section(descriptions)
                reasons.append('add 各章节记载')

        if new_content != content:
            if args.dry_run:
                print(f'  DRY: {name} [{", ".join(reasons)}]')
            else:
                page_path.write_text(new_content, 'utf-8')
                record_rev(name, f'butler/import-war-index: {name} 追加战争元数据 ({war_id})')
                print(f'  UPDATED: {name} [{", ".join(reasons)}]')
            updated += 1
        else:
            skipped += 1

    print(f'\n{"DRY-RUN " if args.dry_run else ""}完成：'
          f'updated={updated}, skipped={skipped}, '
          f'redirects={redirects}, missing={missing}')


if __name__ == '__main__':
    main()
