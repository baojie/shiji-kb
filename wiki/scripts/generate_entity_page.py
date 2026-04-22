#!/usr/bin/env python3
"""
从 wiki/data/semantic.json 批量生成实体 wiki 页面。

用法:
    python wiki/scripts/generate_entity_page.py <canonical> [<canonical> ...]
    python wiki/scripts/generate_entity_page.py --top 10
    python wiki/scripts/generate_entity_page.py --force <canonical>   # 覆盖已存在

生成字段 (MD):
    - YAML frontmatter (id/type/label/aliases/birth_ce/death_ce/tags)
    - 一句话统计 (出现 N 次, M 篇)
    - 基本属性表 (生卒/别名)
    - 章节分布 top 15 (wikilink 到章节页)
    - 自由撰写区占位 (待人工/LLM 填)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_DB = ROOT / 'wiki/data/semantic.json'
PAGES_DIR = ROOT / 'wiki/public/pages'

TOP_CHAPTERS = 15


def fmt_year(ce):
    if ce is None:
        return '?'
    return f'前 {-ce}' if ce < 0 else str(ce)


def format_lifespan(lifespan):
    if not lifespan:
        return None
    b = lifespan.get('birth')
    d = lifespan.get('death')
    if b is None and d is None:
        return None
    parts = []
    if b is not None:
        parts.append(fmt_year(b))
    else:
        parts.append('?')
    parts.append('—')
    if d is not None:
        parts.append(fmt_year(d))
    else:
        parts.append('?')
    # age
    age = None
    if isinstance(b, int) and isinstance(d, int):
        age = d - b
    note = lifespan.get('note')
    s = ' '.join(parts)
    if age is not None:
        s += f'（{age} 岁）'
    if note:
        s += f'（{note}）'
    return s


def yaml_scalar(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    # 中文/字母/数字直接写, 碰到冒号/井号等再加引号
    if any(c in s for c in ':#[]{},&*!|>%@`'):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def yaml_list(xs):
    return '[' + ', '.join(yaml_scalar(x) for x in xs) + ']'


def render_frontmatter(entity):
    canonical = entity['id']
    aliases = [a for a in entity.get('aliases', []) if a != canonical]
    lifespan = entity.get('lifespan') or {}
    lines = ['---']
    lines.append(f'id: {yaml_scalar(canonical)}')
    lines.append(f'type: {entity.get("type", "person")}')
    lines.append(f'label: {yaml_scalar(canonical)}')
    if aliases:
        lines.append(f'aliases: {yaml_list(aliases)}')
    lines.append(f'canonical_name: {yaml_scalar(canonical)}')
    if lifespan.get('birth') is not None:
        lines.append(f'birth_ce: {lifespan["birth"]}')
    if lifespan.get('death') is not None:
        lines.append(f'death_ce: {lifespan["death"]}')
    lines.append('tags: []')
    lines.append('auto_generated: true')
    lines.append('---')
    return '\n'.join(lines)


def render_body(entity):
    canonical = entity['id']
    label = canonical
    aliases = [a for a in entity.get('aliases', []) if a != canonical]
    lifespan = entity.get('lifespan') or {}
    total_refs = entity.get('total_refs', 0)
    total_chapters = entity.get('total_chapters', 0)
    chapters = entity.get('chapters', [])[:TOP_CHAPTERS]

    out = []
    out.append(f'# {label}')
    out.append('')
    if aliases:
        out.append(f'*别名*：{" · ".join(aliases)}')
        out.append('')

    life_s = format_lifespan(lifespan)
    intro_parts = []
    if life_s:
        intro_parts.append(f'生卒 {life_s}')
    intro_parts.append(f'《史记》中出现 **{total_refs}** 次，分布于 **{total_chapters}** 篇')
    out.append('。'.join(intro_parts) + '。')
    out.append('')
    out.append('---')
    out.append('')

    # 基本属性
    out.append('## 基本属性')
    out.append('')
    out.append('| 属性 | 值 |')
    out.append('| --- | --- |')
    if life_s:
        out.append(f'| 生卒 | {life_s} |')
    if aliases:
        out.append(f'| 别名 | {" · ".join(aliases)} |')
    out.append(f'| 总引用 | {total_refs} 次 |')
    out.append(f'| 覆盖章节 | {total_chapters} 篇 |')
    out.append('')
    out.append('---')
    out.append('')

    # 章节分布
    out.append('## 在史记中的分布')
    out.append('')
    if chapters:
        out.append(f'**重点章节**（按出现次数排序，top {len(chapters)}）：')
        out.append('')
        out.append('| 章节 | 次数 |')
        out.append('| --- | ---: |')
        for ch in chapters:
            cid = ch['chapter']
            # label = 去掉 NNN_ 前缀, 更易读
            disp = cid.split('_', 1)[1] if '_' in cid else cid
            out.append(f'| [[{cid}|{disp}]] | {ch["count"]} |')
        out.append('')
    else:
        out.append('*无章节数据*')
        out.append('')
    out.append('---')
    out.append('')

    # 自由撰写区
    out.append('<!-- 自由撰写区 (LLM 或人工填充) -->')
    out.append('')
    out.append('*本页由 `wiki/scripts/generate_entity_page.py` 自动生成。*')
    out.append('*属性表 / 章节分布由脚本维护；叙述段落待补。*')
    out.append('')
    return '\n'.join(out)


def generate_page(entity, force=False):
    canonical = entity['id']
    path = PAGES_DIR / f'{canonical}.md'
    if path.exists() and not force:
        print(f'[skip] {path.name} 已存在 (--force 覆盖)')
        return False

    content = render_frontmatter(entity) + '\n\n' + render_body(entity)
    path.write_text(content, encoding='utf-8')
    print(f'[ok] {path.name}  ({entity.get("total_refs", 0)} refs)')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='*', help='规范名')
    ap.add_argument('--top', type=int, help='取 top N by total_refs')
    ap.add_argument('--force', action='store_true', help='覆盖已存在')
    args = ap.parse_args()

    if not SEMANTIC_DB.exists():
        print(f'✗ 未找到 {SEMANTIC_DB}, 先运行 wiki/server/api/seed.js',
              file=sys.stderr)
        return 1

    data = json.loads(SEMANTIC_DB.read_text(encoding='utf-8'))
    entities = data['entities']

    names = list(args.names)
    if args.top:
        sorted_e = sorted(entities.values(),
                          key=lambda e: -e.get('total_refs', 0))
        names.extend(e['id'] for e in sorted_e[:args.top])

    if not names:
        print('未指定名字; 用位置参数或 --top N', file=sys.stderr)
        return 1

    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    created = 0
    for name in names:
        if name not in entities:
            print(f'[miss] {name} 不在数据库, 跳过', file=sys.stderr)
            continue
        if generate_page(entities[name], force=args.force):
            created += 1

    print(f'---')
    print(f'[done] 新增 {created} 页, 目标目录: {PAGES_DIR}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
