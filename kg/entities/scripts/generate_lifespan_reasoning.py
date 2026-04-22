#!/usr/bin/env python3
"""从 person_lifespans_v2.json 生成每个人物的推理档案到 doc/lifespan_inference/。

文件结构
    doc/lifespan_inference/
        README.md                   -- 索引（按时代分组，附统计）
        {era}/{name}.md             -- 每个人物的推理档案
    其中 era ∈ {五帝, 夏, 商, 西周, 春秋, 战国, 秦, 楚汉, 西汉, 不详}
    name 取 v2 中的规范键（刘邦簇 → 高皇帝，梁孝王簇 → 梁孝王 等）

每篇档案字段
    - 基础：规范名、国/朝、生年区间、卒年区间、享年区间、置信度
    - 证据链：按来源归类，展示每条证据的文本/事件锚点
    - 方法参考：SKILL 07a 的相关方法

使用：
    python kg/entities/scripts/generate_lifespan_reasoning.py
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
INPUT_FILE = BASE_DIR / 'kg' / 'entities' / 'data' / 'person_lifespans_v2.json'
OUTPUT_DIR = BASE_DIR / 'doc' / 'lifespan_inference'

ERA_BOUNDS = [
    ('五帝', None, -2070),
    ('夏',   -2070, -1600),
    ('商',   -1600, -1046),
    ('西周', -1046, -771),
    ('春秋', -770, -476),
    ('战国', -475, -221),
    ('秦',   -221, -206),
    ('楚汉', -206, -202),
    ('西汉', -202, 9),
    ('不详', 9, None),
]


def era_of(year: int | None) -> str:
    if year is None:
        return '不详'
    for name, lo, hi in ERA_BOUNDS:
        if lo is None and year <= hi:
            return name
        if hi is None and year > lo:
            return name
        if lo is not None and hi is not None and lo < year <= hi:
            return name
    return '不详'


def fmt_year(y: int | None) -> str:
    if y is None:
        return '—'
    return f'公元前 {-y} 年' if y < 0 else f'公元 {y} 年'


def fmt_range(lo: int | None, hi: int | None) -> str:
    if lo is None and hi is None:
        return '—'
    if lo == hi:
        return fmt_year(lo)
    return f'{fmt_year(lo)} ~ {fmt_year(hi)}'


CONF_LABEL = {
    'exact': '精确',
    'high': '高',
    'medium': '中',
    'low': '低',
    'legend': '传说',
    'approximate': '约',
    'external': '外源',
}


def classify_evidence(ev: str) -> str:
    """把证据字符串按前缀分类。"""
    s = ev.lstrip()
    if s.startswith('十表'):
        return '十表 reign_periods'
    if s.startswith('事件索引'):
        return '事件索引（原文事件锚点）'
    if s.startswith('原文模式'):
        return '原文模式（正则扫描）'
    if s.startswith('v1 lifespans'):
        return 'v1 外部参考'
    if s.startswith('事件时间线') or s.startswith('· 约束'):
        return '事件时间线 + 常识约束'
    return '其他'


def reasoning_sections(entry: dict) -> list[tuple[str, list[str]]]:
    """拆证据链为 (分类, [证据行]) 列表，保持原顺序。
    "· 原文：..." 行跟随前一条证据所在的分组。"""
    groups: dict[str, list[str]] = defaultdict(list)
    order: list[str] = []
    last_group = None
    for ev in entry.get('evidence', []):
        stripped = ev.lstrip()
        if stripped.startswith('· 原文') and last_group:
            groups[last_group].append(ev)
            continue
        g = classify_evidence(ev)
        if g not in groups:
            order.append(g)
        groups[g].append(ev)
        last_group = g
    return [(g, groups[g]) for g in order]


def method_hints(entry: dict) -> list[str]:
    """根据证据出现的类型列出对应的 SKILL 07a 方法提示。"""
    hints = []
    evs = ' '.join(entry.get('evidence', []))
    if '生' in evs and ('岁立' in evs or '岁而立' in evs):
        hints.append('方法 3：年龄+事件锚点（生 X 岁立）')
    if '享年' in evs or '岁卒' in evs:
        hints.append('方法 3：年龄+事件锚点（享年 X 岁）')
    if '立' in evs and ('年卒' in evs or '年薨' in evs or '年崩' in evs):
        hints.append('方法 2：在位年数反推')
    if '事件索引' in evs and '生于' in evs:
        hints.append('方法 1：直接生年记载（事件索引 家族事件）')
    if '事件索引' in evs and '卒于' in evs:
        hints.append('方法 1：直接卒年记载（事件索引）')
    if '十表' in evs:
        hints.append('方法 2：十表在位年（reign_periods.json）')
    return hints


def slugify(name: str) -> str:
    """文件名用规范名本身，但去掉可能导致文件系统问题的字符。"""
    # 保留中文与常见字符；禁止 / \ : * ? " < > |
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def person_doc(name: str, entry: dict) -> str:
    birth_range = fmt_range(entry.get('birth_min'), entry.get('birth_max'))
    death_range = fmt_range(entry.get('death_min'), entry.get('death_max'))
    age_min, age_max = entry.get('age_min'), entry.get('age_max')
    if age_min is None and age_max is None:
        age_range = '—'
    elif age_min == age_max:
        age_range = f'{age_min} 岁'
    else:
        age_range = f'{age_min}–{age_max} 岁'
    birth_conf = CONF_LABEL.get(entry.get('birth_confidence', ''), entry.get('birth_confidence', ''))
    death_conf = CONF_LABEL.get(entry.get('death_confidence', ''), entry.get('death_confidence', ''))
    state = entry.get('state', '—')

    lines: list[str] = []
    lines.append(f'# {name}')
    lines.append('')
    lines.append('## 基础')
    lines.append('')
    lines.append(f'- **国/朝**：{state}')
    lines.append(f'- **生年**：{birth_range}（置信度：{birth_conf}）')
    lines.append(f'- **卒年**：{death_range}（置信度：{death_conf}）')
    lines.append(f'- **享年**：{age_range}')
    lines.append(f'- **数据来源**：{", ".join(entry.get("sources", []))}')
    lines.append('')

    # 证据链
    lines.append('## 证据链')
    lines.append('')
    sections = reasoning_sections(entry)
    if not sections:
        lines.append('（无明文证据，仅基于默认区间）')
    else:
        for group, evs in sections:
            lines.append(f'### {group}')
            lines.append('')
            for e in evs:
                lines.append(f'- {e}')
            lines.append('')

    # 方法参考
    hints = method_hints(entry)
    if hints:
        lines.append('## 方法（SKILL 07a）')
        lines.append('')
        for h in hints:
            lines.append(f'- {h}')
        lines.append('')

    # 结论
    lines.append('## 结论')
    lines.append('')
    conf_overall = CONF_LABEL.get(entry.get('confidence', ''), entry.get('confidence', ''))
    lines.append(
        f'- 综合：生 **{birth_range}**（{birth_conf}）'
        f' · 卒 **{death_range}**（{death_conf}）'
        f' · 总体 **{conf_overall}**'
    )
    sources_set = set(entry.get('sources', []))
    if 'reign_periods' in sources_set and 'event_index' in sources_set:
        lines.append('- 十表与事件索引互相印证')
    elif 'reign_periods' in sources_set:
        lines.append('- 以十表在位末年为卒年，生年按即位年回推 10–60 岁的宽区间')
    elif 'event_index' in sources_set and 'lifespans_v1' not in sources_set:
        lines.append('- 仅事件索引提供锚点，生/卒另一端尚未推定')
    if 'lifespans_v1' in sources_set:
        lines.append('- 合并了外部数据（维基/百度/学界估算）作为交叉验证')

    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append(f'*源数据：`kg/entities/data/person_lifespans_v2.json` · '
                 f'生成脚本：`kg/entities/scripts/generate_lifespan_reasoning.py`*')
    return '\n'.join(lines) + '\n'


def index_doc(persons_by_era: dict[str, list[tuple[str, dict]]], stats: dict) -> str:
    lines: list[str] = []
    lines.append('# 人物生卒年推理档案')
    lines.append('')
    lines.append('本目录记录每一位《史记》人物生卒年的推理过程。每个文件对应一位人物（取其规范名），')
    lines.append('内部按证据类型（十表 / 事件索引 / 原文模式 / v1 外部）分节展示。')
    lines.append('')
    lines.append('## 快速查阅')
    lines.append('')
    lines.append(f'- 可视化表格：[docs/special/lifespan.html](../../docs/special/lifespan.html)')
    lines.append(f'- 原始数据：[kg/entities/data/person_lifespans_v2.json](../../kg/entities/data/person_lifespans_v2.json)')
    lines.append(f'- 方法论：[skills/SKILL_07a_人物生卒年推断.md](../../skills/SKILL_07a_人物生卒年推断.md)')
    lines.append(f'- 生成脚本：[kg/entities/scripts/infer_lifespans.py](../../kg/entities/scripts/infer_lifespans.py) · '
                 f'[generate_lifespan_reasoning.py](../../kg/entities/scripts/generate_lifespan_reasoning.py)')
    lines.append('')

    # 统计
    total = stats.get('total_persons', 0)
    death_dist = stats.get('death_confidence_distribution', {})
    birth_dist = stats.get('birth_confidence_distribution', {})
    lines.append('## 统计')
    lines.append('')
    lines.append(f'- 人物总数：**{total}**')
    lines.append(f'- 卒年置信度：'
                 + ' · '.join(f'{CONF_LABEL.get(k,k)} {v}' for k, v in death_dist.items()))
    lines.append(f'- 生年置信度：'
                 + ' · '.join(f'{CONF_LABEL.get(k,k)} {v}' for k, v in birth_dist.items()))
    lines.append('')

    # 按时代索引
    lines.append('## 索引（按时代分组）')
    lines.append('')
    era_order = [e[0] for e in ERA_BOUNDS]
    for era in era_order:
        items = persons_by_era.get(era, [])
        if not items:
            continue
        lines.append(f'### {era}（{len(items)} 人）')
        lines.append('')
        for name, entry in items:
            death = fmt_range(entry.get('death_min'), entry.get('death_max'))
            birth = fmt_range(entry.get('birth_min'), entry.get('birth_max'))
            conf = CONF_LABEL.get(entry.get('confidence', ''), '')
            slug = slugify(name)
            lines.append(f'- [{name}]({era}/{slug}.md) — 生 {birth} / 卒 {death} ({conf})')
        lines.append('')

    return '\n'.join(lines) + '\n'


def main():
    data = json.loads(INPUT_FILE.read_text(encoding='utf-8'))
    persons = data['persons']
    stats = data.get('_stats', {})

    # 按时代分组
    persons_by_era: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for name, v in persons.items():
        anchor = v.get('death_max') or v.get('birth_max')
        persons_by_era[era_of(anchor)].append((name, v))
    for era, items in persons_by_era.items():
        items.sort(key=lambda x: (
            x[1].get('death_max') if x[1].get('death_max') is not None else 10**9,
            x[1].get('birth_max') if x[1].get('birth_max') is not None else 10**9,
            x[0],
        ))

    # 清理旧目录并重建
    if OUTPUT_DIR.exists():
        for sub in OUTPUT_DIR.iterdir():
            if sub.is_dir():
                for f in sub.iterdir():
                    f.unlink()
                sub.rmdir()
            else:
                sub.unlink()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 写 README
    (OUTPUT_DIR / 'README.md').write_text(index_doc(persons_by_era, stats), encoding='utf-8')

    # 写每人档案
    count = 0
    for era, items in persons_by_era.items():
        era_dir = OUTPUT_DIR / era
        era_dir.mkdir(exist_ok=True)
        for name, entry in items:
            slug = slugify(name)
            (era_dir / f'{slug}.md').write_text(person_doc(name, entry), encoding='utf-8')
            count += 1

    print(f'Wrote {count} person docs + README.md to {OUTPUT_DIR}')
    print(f'  Eras: {[(era, len(items)) for era, items in persons_by_era.items() if items]}')


if __name__ == '__main__':
    main()
