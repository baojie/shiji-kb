#!/usr/bin/env python3
"""将 person_lifespan_events.json 中的明确生卒年人物同步追加为
史记编年表.md 末尾的附录章节，使用 AUTO-GENERATED 标记区块以便重复执行时替换。

幂等规则：
    - 查找 `<!-- AUTO-GENERATED: LIFESPAN_APPENDIX ... -->` 与对应结束标记
    - 若找到，替换区块；否则在文件末尾追加
    - 不触碰现有手写正文

使用：
    python kg/chronology/scripts/sync_chronology_md.py
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE_DIR = Path(__file__).resolve().parents[3]
EVENTS_FILE = BASE_DIR / 'kg' / 'chronology' / 'data' / 'person_lifespan_events.json'
TARGET_FILE = BASE_DIR / 'kg' / 'chronology' / 'data' / '史记编年表.md'

BEGIN_MARK = '<!-- AUTO-GENERATED: LIFESPAN_APPENDIX (do not edit; regenerate via kg/chronology/scripts/sync_chronology_md.py) -->'
END_MARK = '<!-- END AUTO-GENERATED: LIFESPAN_APPENDIX -->'


def century_label(year: int) -> str:
    """-551 -> '前6世纪'；100 -> '1世纪'；-100 -> '前1世纪'。"""
    if year < 0:
        c = (-year - 1) // 100 + 1
        return f'前{c}世纪'
    return f'{year // 100 + 1}世纪'


def century_order_key(label: str) -> tuple:
    if label.startswith('前'):
        n = int(label.removeprefix('前').removesuffix('世纪'))
        return (0, -n)
    n = int(label.removesuffix('世纪'))
    return (1, n)


def fmt_year(year: int) -> str:
    return f'前{-year}年' if year < 0 else f'{year}年'


def build_appendix() -> str:
    data = json.loads(EVENTS_FILE.read_text(encoding='utf-8'))
    persons = data['persons_included']

    # 按卒年分世纪，世纪内按卒年升序、再按生年升序
    by_century = defaultdict(list)
    for p in persons:
        by_century[century_label(p['death'])].append(p)

    for cent, group in by_century.items():
        group.sort(key=lambda x: (x['death'], x['birth']))

    # 世纪按时间先后排序
    centuries = sorted(by_century.keys(), key=century_order_key)

    lines: list[str] = []
    lines.append(BEGIN_MARK)
    lines.append('')
    lines.append('## 附录：主要人物生卒年')
    lines.append('')
    lines.append(f'> 本附录由 `kg/chronology/scripts/sync_chronology_md.py` 从 `kg/entities/data/person_lifespans.json` 自动同步，')
    lines.append('> 共收录 **{}** 位《史记》人物（仅含明确纪年条目；"传说"/"约"类已排除）。'.format(len(persons)))
    lines.append('> 本附录与 `docs/entities/timeline.html` 中的"生/卒"标记同源，共同支撑编年检索。')
    lines.append('')

    for cent in centuries:
        group = by_century[cent]
        lines.append(f'### {cent}（{len(group)} 人）')
        lines.append('')
        lines.append('| 生卒年 | 主要人物 | 别名 | 享年 |')
        lines.append('|--------|---------|------|------|')
        for p in group:
            aliases = [a for a in p['aliases'] if a != p['name']]
            alias_field = '、'.join(aliases) if aliases else '—'
            lifespan = p['death'] - p['birth']
            period = f'{fmt_year(p["birth"])} — {fmt_year(p["death"])}'
            lines.append(f'| {period} | {p["name"]} | {alias_field} | {lifespan} 岁 |')
        lines.append('')

    # 生成时间戳（北京时区）
    tz = timezone(timedelta(hours=8))
    ts = datetime.now(tz).strftime('%Y-%m-%d %H:%M %z')
    lines.append('---')
    lines.append('')
    lines.append(f'*附录同步时间：{ts}｜源数据：`kg/entities/data/person_lifespans.json`*')
    lines.append('')
    lines.append(END_MARK)
    return '\n'.join(lines)


def sync(target: Path, appendix: str) -> str:
    text = target.read_text(encoding='utf-8')
    pattern = re.compile(
        re.escape(BEGIN_MARK) + r'.*?' + re.escape(END_MARK),
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub(appendix, text)
        action = 'replaced existing appendix'
    else:
        # 追加：确保与前文留一个空行
        if not text.endswith('\n'):
            text += '\n'
        if not text.endswith('\n\n'):
            text += '\n'
        new_text = text + appendix + '\n'
        action = 'appended new appendix'
    target.write_text(new_text, encoding='utf-8')
    return action


def main():
    appendix = build_appendix()
    action = sync(TARGET_FILE, appendix)
    print(f'{TARGET_FILE}: {action}')


if __name__ == '__main__':
    main()
