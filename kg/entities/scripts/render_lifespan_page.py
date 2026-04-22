#!/usr/bin/env python3
"""从 person_lifespans_v2.json 生成 docs/special/lifespan.html。

页面特性
    - 按时代分组（五帝 / 夏 / 商 / 西周 / 春秋 / 战国 / 秦 / 西汉 / 不详）
    - 每行：姓名 · 生年区间 · 卒年区间 · 享年区间 · 置信度徽章 · 国/朝 · 证据链
    - 顶部：搜索框（人名过滤）+ 置信度筛选 + 统计卡片
    - 置信度色彩：exact=绿/high=蓝/medium=黄/low=灰/legend=紫

使用：
    python kg/entities/scripts/render_lifespan_page.py
"""
from __future__ import annotations

import html as html_mod
import json
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
INPUT_FILE = BASE_DIR / 'kg' / 'entities' / 'data' / 'person_lifespans_v2.json'
OUTPUT_FILE = BASE_DIR / 'docs' / 'special' / 'lifespan.html'

# 时代分期（按卒年，signed CE）
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
        if lo is None:
            if year <= hi:
                return name
        elif hi is None:
            if year > lo:
                return name
        elif lo < year <= hi:
            return name
    return '不详'


def fmt_year(y: int | None) -> str:
    if y is None:
        return '—'
    return f'前{-y}' if y < 0 else f'{y}'


def fmt_range(lo: int | None, hi: int | None) -> str:
    if lo is None and hi is None:
        return '—'
    if lo == hi:
        return fmt_year(lo)
    return f'{fmt_year(lo)} ~ {fmt_year(hi)}'


CONF_LABEL = {
    'exact':  ('精确',   '#0a7d0a'),
    'high':   ('高',     '#2e6cb8'),
    'medium': ('中',     '#b88a2e'),
    'low':    ('低',     '#888888'),
    'legend': ('传说',   '#8a4fb8'),
    'approximate': ('约', '#a68b2e'),
    'external': ('外源', '#666'),
}

# 置信度排序（与 infer_lifespans.py 同步）
CONF_RANK = {'low': 0, 'external': 1, 'approximate': 1, 'medium': 2, 'legend': 2, 'high': 3, 'exact': 4}


def render():
    data = json.loads(INPUT_FILE.read_text(encoding='utf-8'))
    persons = data['persons']
    stats = data.get('_stats', {})

    # 按时代分组（以 death 中点为锚；若无则以 birth；再无归"不详"）
    buckets: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for name, v in persons.items():
        anchor = v.get('death_max') or v.get('birth_max')
        buckets[era_of(anchor)].append((name, v))

    # 排序：每组按 death_max 升序（无则 birth_max）
    for era, items in buckets.items():
        items.sort(key=lambda x: (
            x[1].get('death_max') if x[1].get('death_max') is not None else 10**9,
            x[1].get('birth_max') if x[1].get('birth_max') is not None else 10**9,
            x[0],
        ))

    # 组织展示顺序
    order = [e[0] for e in ERA_BOUNDS]

    lines: list[str] = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html lang="zh">')
    lines.append('<head>')
    lines.append('<meta charset="UTF-8">')
    lines.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append('<title>人物生卒年推理 - 史记知识库</title>')
    lines.append('<style>')
    lines.append(CSS)
    lines.append('</style>')
    lines.append('</head>')
    lines.append('<body>')
    lines.append('<div class="container">')

    # 顶部
    lines.append('<nav class="topnav">')
    lines.append('  <a href="../index.html">← 返回首页</a>')
    lines.append('  <a href="special_index.html">专项索引</a>')
    lines.append('  <a href="../entities/timeline.html">编年索引</a>')
    lines.append('</nav>')
    lines.append('<h1>人物生卒年推理</h1>')
    lines.append('<p class="subtitle">基于 SKILL 07a 方法论：合并 reign_periods + 文本模式（立X年卒 / 生X岁立 / 享年X岁） + 事件索引 + v1 外部数据，按证据强度输出区间估算</p>')

    # WIP 横幅
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))
    now_str = datetime.now(tz).strftime('%Y-%m-%d')
    lines.append('<div class="wip-banner">')
    lines.append('  <strong>⚠️ 进行中工作 (Work in Progress)</strong>')
    lines.append('  <p>本页为机器自动化挖掘的中间结果，<strong>推理逻辑尚未充分收敛，含有大量错误</strong>。'
                 '区间宽、置信度"低"的条目尤其可能失真；置信度"高"的条目也需逐一核对原文。')
    lines.append('  请勿作为学术引用，仅用于内部观察与迭代。</p>')
    lines.append(f'  <p class="wip-date">最后更新：{now_str}</p>')
    lines.append('</div>')

    # 简洁统计：人数 + 生/卒两条堆叠置信度条
    total = stats.get('total_persons', len(persons))
    birth_dist = stats.get('birth_confidence_distribution', {})
    death_dist = stats.get('death_confidence_distribution', {})
    src_dist = stats.get('source_distribution', {})

    def conf_bar(title: str, dist: dict) -> str:
        # 按置信度高→低排序
        order = ['high', 'medium', 'approximate', 'low', 'legend']
        segments = []
        for conf in order:
            if dist.get(conf):
                label, color = CONF_LABEL[conf]
                n = dist[conf]
                pct = n / total * 100
                segments.append((conf, label, color, n, pct))
        bar_html = ''.join(
            f'<span class="bar-seg" style="background:{c};width:{p:.1f}%" title="{lbl} {n} 人"></span>'
            for _, lbl, c, n, p in segments
        )
        legend_html = ' · '.join(
            f'<span style="color:{c}">{lbl} <b>{n}</b></span>'
            for _, lbl, c, n, _ in segments
        )
        return (
            f'<div class="conf-row">'
            f'<span class="conf-row-title">{title}</span>'
            f'<span class="conf-bar">{bar_html}</span>'
            f'<span class="conf-legend">{legend_html}</span>'
            f'</div>'
        )

    src_summary = ' · '.join(
        f'{src_zh} <b>{src_dist[k]}</b>'
        for k, src_zh in [('reign_periods', '十表'), ('event_index', '事件索引'),
                          ('text_pattern', '原文模式'), ('lifespans_v1', 'v1外部')]
        if k in src_dist
    )

    lines.append('<div class="stats-compact">')
    lines.append(f'  <div class="stat-total"><span class="stat-total-num">{total}</span><span class="stat-total-label">人</span></div>')
    lines.append('  <div class="stat-bars">')
    lines.append(f'    {conf_bar("卒年", death_dist)}')
    lines.append(f'    {conf_bar("生年", birth_dist)}')
    lines.append(f'    <div class="conf-row src-row"><span class="conf-row-title">来源</span><span class="src-summary">{src_summary}</span></div>')
    lines.append('  </div>')
    lines.append('</div>')

    # 筛选器
    lines.append('<div class="controls">')
    lines.append('  <input type="text" id="filter-name" placeholder="搜索姓名/别名/国名...">')
    lines.append('  <div class="conf-filters">')
    for conf in ('high', 'medium', 'low', 'legend'):
        label, color = CONF_LABEL[conf]
        lines.append(
            f'  <label class="conf-filter" style="--accent:{color}">'
            f'<input type="checkbox" data-conf="{conf}" checked>{label}</label>'
        )
    lines.append('  </div>')
    lines.append('</div>')

    # 表格（按时代分组）
    for era in order:
        items = buckets.get(era, [])
        if not items:
            continue
        safe = era
        lines.append(f'<section class="era-section" data-era="{safe}">')
        lines.append(f'<h2 class="era-heading">{html_mod.escape(era)}'
                     f'<span class="era-count">{len(items)} 人</span></h2>')
        lines.append('<table class="lifespan-table">')
        lines.append('<thead><tr>')
        lines.append('<th>姓名</th><th>生年（置信度）</th><th>卒年（置信度）</th><th>享年</th>'
                     '<th>国/朝</th><th>证据</th>')
        lines.append('</tr></thead>')
        lines.append('<tbody>')

        for name, v in items:
            conf = v.get('confidence', 'low')
            birth_conf = v.get('birth_confidence', conf)
            death_conf = v.get('death_confidence', conf)
            b_label, b_color = CONF_LABEL.get(birth_conf, (birth_conf, '#888'))
            d_label, d_color = CONF_LABEL.get(death_conf, (death_conf, '#888'))
            birth_cell = fmt_range(v.get('birth_min'), v.get('birth_max'))
            death_cell = fmt_range(v.get('death_min'), v.get('death_max'))
            age_cell = fmt_range(v.get('age_min'), v.get('age_max'))
            state = v.get('state', '—')
            evidence = v.get('evidence', [])
            ev_html = '<ul class="evidence-list">'
            for e in evidence:
                ev_html += f'<li>{html_mod.escape(e)}</li>'
            ev_html += '</ul>'

            # 搜索关键字（姓名 + 国 + 证据）
            search_kw = (name + ' ' + state + ' ' + ' '.join(evidence)).lower()

            # 筛选用：按"最大置信度"允许任一路通过
            filter_conf = max([birth_conf, death_conf], key=lambda c: CONF_RANK.get(c, 0))

            lines.append(
                f'<tr class="person-row" data-conf="{filter_conf}" '
                f'data-birth-conf="{birth_conf}" data-death-conf="{death_conf}" '
                f'data-search="{html_mod.escape(search_kw)}">'
            )
            lines.append(f'  <td class="name-cell"><strong>{html_mod.escape(name)}</strong></td>')
            # 生/卒 单元格内嵌小徽章
            lines.append(
                f'  <td class="year-cell">{html_mod.escape(birth_cell)}'
                f'<span class="conf-badge mini" style="background:{b_color}">{b_label}</span></td>'
            )
            lines.append(
                f'  <td class="year-cell">{html_mod.escape(death_cell)}'
                f'<span class="conf-badge mini" style="background:{d_color}">{d_label}</span></td>'
            )
            lines.append(f'  <td class="year-cell">{html_mod.escape(age_cell)}</td>')
            lines.append(f'  <td class="state-cell">{html_mod.escape(state)}</td>')
            lines.append(f'  <td class="evidence-cell">{ev_html}</td>')
            lines.append('</tr>')

        lines.append('</tbody></table>')
        lines.append('</section>')

    # 脚本
    lines.append('<script>' + JS + '</script>')

    lines.append('<footer>')
    lines.append('  <p>数据源：<code>kg/entities/data/person_lifespans_v2.json</code> ·'
                 ' 方法：<a href="https://github.com/baojie/shiji-kb/blob/main/skills/SKILL_07a_人物生卒年推断.md">SKILL 07a</a> · '
                 '生成脚本：<code>kg/entities/scripts/render_lifespan_page.py</code></p>')
    lines.append('</footer>')
    lines.append('</div>')
    lines.append('</body></html>')

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {OUTPUT_FILE}')
    print(f'  {total} persons, {len(buckets)} era groups')


CSS = """
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: "Source Han Serif SC", "Noto Serif SC", serif;
    background: linear-gradient(135deg, #fdfaf6 0%, #f5f1ec 100%);
    color: #333;
    line-height: 1.6;
    padding: 20px;
}
.container {
    max-width: 1280px;
    margin: 0 auto;
    background: white;
    padding: 40px;
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
h1 {
    color: #8b4513;
    border-bottom: 3px double #8b4513;
    padding-bottom: 16px;
    margin-top: 10px;
    text-align: center;
}
.subtitle {
    text-align: center;
    color: #666;
    font-size: 0.95em;
    margin: 0 auto 24px;
    max-width: 900px;
}
.topnav { padding: 12px 0; border-bottom: 1px solid #eee; margin-bottom: 20px; }
.topnav a {
    color: #8b4513;
    text-decoration: none;
    margin-right: 24px;
    font-size: 0.95em;
}
.topnav a:hover { text-decoration: underline; }

.wip-banner {
    background: #fff7e0;
    border-left: 5px solid #d4941e;
    padding: 14px 20px;
    margin: 0 0 24px;
    border-radius: 6px;
    color: #6b4b15;
    font-size: 0.93em;
    line-height: 1.5;
}
.wip-banner strong { color: #8b4513; font-size: 1em; }
.wip-banner p { margin: 6px 0 0; }
.wip-date { color: #a07730; font-size: 0.88em; margin-top: 8px !important; }

.stats-compact {
    display: flex;
    gap: 24px;
    align-items: center;
    background: #fdfaf6;
    border-left: 4px solid #8b4513;
    padding: 14px 20px;
    border-radius: 6px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}
.stat-total { display: flex; align-items: baseline; gap: 4px; min-width: 100px; }
.stat-total-num { font-size: 2.2em; font-weight: bold; color: #8b4513; line-height: 1; }
.stat-total-label { color: #999; font-size: 0.95em; }
.stat-bars { flex: 1; min-width: 420px; display: flex; flex-direction: column; gap: 6px; }
.conf-row { display: flex; align-items: center; gap: 12px; font-size: 0.85em; }
.conf-row-title { color: #666; min-width: 36px; font-weight: 600; }
.conf-bar {
    flex: 1 1 140px;
    min-width: 140px;
    max-width: 220px;
    height: 12px;
    border-radius: 6px;
    overflow: hidden;
    display: flex;
    background: #eee;
}
.conf-bar .bar-seg { display: inline-block; height: 100%; }
.conf-legend { color: #555; flex: 2; min-width: 240px; }
.conf-legend b { font-weight: 600; }
.src-row .src-summary { color: #555; }
.src-row .src-summary b { color: #8b4513; }

.controls {
    display: flex;
    gap: 16px;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
}
.controls input[type="text"] {
    flex: 1;
    min-width: 260px;
    padding: 10px 14px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 1em;
    font-family: inherit;
}
.conf-filters { display: flex; gap: 10px; flex-wrap: wrap; }
.conf-filter {
    --accent: #888;
    border: 1px solid var(--accent);
    color: var(--accent);
    padding: 4px 10px;
    border-radius: 14px;
    font-size: 0.88em;
    cursor: pointer;
    user-select: none;
}
.conf-filter input { margin-right: 4px; vertical-align: middle; }

.era-section { margin-bottom: 40px; }
.era-heading {
    color: #8b4513;
    border-bottom: 2px solid #8b4513;
    padding-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}
.era-count {
    font-size: 0.7em;
    color: #999;
    font-weight: normal;
}

.lifespan-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.93em;
}
.lifespan-table th {
    background: #f5f1ec;
    color: #8b4513;
    padding: 8px 10px;
    text-align: left;
    border-bottom: 2px solid #8b4513;
    font-weight: 600;
    white-space: nowrap;
}
.lifespan-table td {
    padding: 10px;
    border-bottom: 1px solid #eee;
    vertical-align: top;
}
.lifespan-table tr:hover { background: #fafafa; }

.name-cell { min-width: 90px; }
.year-cell { white-space: nowrap; font-family: "SF Mono", Consolas, monospace; font-size: 0.9em; }
.state-cell { color: #999; text-align: center; }
.conf-badge {
    display: inline-block;
    color: white;
    font-size: 0.78em;
    padding: 2px 10px;
    border-radius: 10px;
}
.conf-badge.mini {
    font-size: 0.7em;
    padding: 1px 6px;
    border-radius: 8px;
    margin-left: 6px;
    vertical-align: middle;
}
.evidence-cell { min-width: 280px; }
.evidence-list {
    margin: 0;
    padding-left: 18px;
    font-size: 0.86em;
    color: #555;
}
.evidence-list li { margin: 2px 0; }

.hidden { display: none !important; }

footer {
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid #eee;
    color: #999;
    font-size: 0.85em;
    text-align: center;
}
footer code {
    background: #f5f1ec;
    padding: 1px 5px;
    border-radius: 3px;
}
footer a { color: #8b4513; }

@media (max-width: 820px) {
    .container { padding: 20px; }
    .lifespan-table { font-size: 0.85em; }
    .evidence-cell { min-width: 180px; }
}
"""

JS = """
document.addEventListener('DOMContentLoaded', function() {
    var filterInput = document.getElementById('filter-name');
    var confCheckboxes = document.querySelectorAll('.conf-filter input[type=checkbox]');
    var rows = document.querySelectorAll('.person-row');
    var sections = document.querySelectorAll('.era-section');

    function apply() {
        var q = filterInput.value.trim().toLowerCase();
        var activeConfs = {};
        confCheckboxes.forEach(function(cb) {
            activeConfs[cb.dataset.conf] = cb.checked;
        });

        rows.forEach(function(row) {
            var keep = true;
            var rowConf = row.dataset.conf;
            if (rowConf in activeConfs && !activeConfs[rowConf]) keep = false;
            if (keep && q) {
                if (row.dataset.search.indexOf(q) === -1) keep = false;
            }
            row.classList.toggle('hidden', !keep);
        });

        sections.forEach(function(sec) {
            var visibleRows = sec.querySelectorAll('.person-row:not(.hidden)');
            sec.classList.toggle('hidden', visibleRows.length === 0);
            var countEl = sec.querySelector('.era-count');
            if (countEl) countEl.textContent = visibleRows.length + ' 人';
        });
    }

    filterInput.addEventListener('input', apply);
    confCheckboxes.forEach(function(cb) { cb.addEventListener('change', apply); });
});
"""


if __name__ == '__main__':
    render()
