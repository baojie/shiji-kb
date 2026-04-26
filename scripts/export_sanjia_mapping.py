#!/usr/bin/env python3
"""
export_sanjia_mapping.py — 输出三家注分发记录。

重跑 import_sanjia_to_entities 的映射逻辑（不写入 wiki），
生成 docs/sanjia_mapping.md 和 data/sanjia_mapping.jsonl。

用法：
    python3 scripts/export_sanjia_mapping.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from import_sanjia_to_entities import (
    build_entity_map, find_anchor_entity,
    find_entity_page, get_chapter_label, find_chapter_page,
    NOTES_CACHE, CHAPTER_MD, ENTITY_TYPES,
)

OUTPUT_MD   = ROOT / 'labs' / 'sanjia' / 'sanjia_mapping.md'
OUTPUT_JSONL = ROOT / 'labs' / 'sanjia' / 'sanjia_mapping.jsonl'


def get_sanjia_created_pages() -> set[str]:
    """从 history 文件中找出本次 sanjia 新建的页面 slug 集合。"""
    hist_dir = ROOT / 'wiki' / 'public' / 'history'
    created = set()
    for hf in hist_dir.glob('*.json'):
        try:
            data = json.loads(hf.read_text(encoding='utf-8'))
            revisions = data if isinstance(data, list) else data.get('revisions', [])
            for rev in revisions:
                if 'sanjia-entity: 新建' in rev.get('summary', ''):
                    created.add(hf.stem)
                    break
        except Exception:
            pass
    return created


def get_all_nums() -> list[str]:
    return sorted(
        p.stem.replace('-notes', '')
        for p in NOTES_CACHE.glob('*-notes.json')
        if 'index' not in p.stem
    )


def run() -> None:
    nums = get_all_nums()
    created_pages = get_sanjia_created_pages()
    print(f'本次新建页面: {len(created_pages)} 个')

    # ── JSONL 输出 ──────────────────────────────────────────────────
    jsonl_lines: list[str] = []

    # ── Markdown 输出 ───────────────────────────────────────────────
    md_lines: list[str] = [
        '# 三家注分发记录',
        '',
        '本文档记录《史记》三家注每一条的分发目标。',
        '- **entity_page**: 注释被写入已有实体 wiki 页面',
        '- **entity_page (新建)**: 注释被写入本次新建的实体页面 ⭐',
        '- **fallback**: 无法定位实体，写入章节页',
        '- **no_page**: 实体存在但无对应 wiki 页面（注释<2条，已跳过）',
        '',
        '| 章节 | 注释ID | 锚点上下文 | 目标页面 | 状态 |',
        '|------|--------|-----------|---------|------|',
    ]

    total = mapped = fallback = no_page = created_count = 0

    for num in nums:
        notes_file = NOTES_CACHE / f'{num}-notes.json'
        if not notes_file.exists():
            continue
        with notes_file.open(encoding='utf-8') as f:
            notes_data = json.load(f)
        notes = notes_data.get('notes', [])
        if not notes:
            continue

        chapter_label = get_chapter_label(num)

        tagged_files = list(CHAPTER_MD.glob(f'{num}_*.tagged.md'))
        if tagged_files:
            clean_text, char_entity_map = build_entity_map(
                tagged_files[0].read_text(encoding='utf-8')
            )
        else:
            clean_text, char_entity_map = '', {}

        chapter_page = find_chapter_page(num)
        chapter_slug = chapter_page.stem if chapter_page else chapter_label

        for note in notes:
            note_id = note.get('id', '')
            bc = note.get('before_context', '').lstrip('.…[').strip()
            anchor = note.get('anchor_text', '').strip()
            context = f'……{bc[-12:]}**{anchor}**……' if bc else '（篇首总注）'
            total += 1

            entity = find_anchor_entity(note, clean_text, char_entity_map) if clean_text else None

            is_new = False
            if entity:
                etype, ename = entity
                page = find_entity_page(ename)
                if page:
                    target = page.stem
                    is_new = target in created_pages
                    status = 'entity_page'
                    mapped += 1
                    if is_new:
                        created_count += 1
                else:
                    target = f'（无页面：{ename}）'
                    status = 'no_page'
                    no_page += 1
            else:
                target = chapter_slug
                status = 'fallback'
                fallback += 1

            # JSONL
            jsonl_lines.append(json.dumps({
                'chapter': chapter_label,
                'note_id': note_id,
                'anchor': anchor,
                'before_context': bc,
                'entity': (entity[1] if entity else None),
                'entity_type': (entity[0] if entity else None),
                'target_page': target,
                'status': status,
                'page_created': is_new,
            }, ensure_ascii=False))

            # Markdown
            ctx_md = context.replace('|', '｜')
            if status == 'no_page':
                target_md = target
                status_md = status
            else:
                target_md = f'[[{target}]]'
                status_md = 'entity_page (新建) ⭐' if is_new else status
            md_lines.append(
                f'| {chapter_label} | {note_id} | {ctx_md} | {target_md} | {status_md} |'
            )

    # 统计摘要
    md_summary = [
        '',
        '## 统计摘要',
        '',
        f'- 总注释数：**{total}**',
        f'- 成功分发到实体页：**{mapped}**（{mapped*100//total if total else 0}%）',
        f'  - 其中写入**本次新建**页面：**{created_count}** 条（涉及 {len(created_pages)} 个新建页面）',
        f'- Fallback 到章节页：**{fallback}**（{fallback*100//total if total else 0}%）',
        f'- 实体无对应页面（跳过）：**{no_page}**（{no_page*100//total if total else 0}%）',
        '',
        '## 本次新建的实体页面',
        '',
        '以下页面在本次三家注导入过程中新建（原先不存在）：',
        '',
    ] + [f'- [[{slug}]]' for slug in sorted(created_pages)] + ['']
    # 把摘要插到表格前
    insert_pos = md_lines.index('| 章节 | 注释ID | 锚点上下文 | 目标页面 | 状态 |')
    for i, line in enumerate(md_summary):
        md_lines.insert(insert_pos + i, line)

    # 写入文件
    OUTPUT_MD.write_text('\n'.join(md_lines) + '\n', encoding='utf-8')
    OUTPUT_JSONL.write_text('\n'.join(jsonl_lines) + '\n', encoding='utf-8')

    print(f'✓ {OUTPUT_MD}  （{len(md_lines)} 行）')
    print(f'✓ {OUTPUT_JSONL}  （{total} 条记录）')
    print(f'  entity_page={mapped}  fallback={fallback}  no_page={no_page}')


if __name__ == '__main__':
    run()
