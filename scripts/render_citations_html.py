#!/usr/bin/env python3
"""渲染《史记》引文索引 HTML 页面。

读取 data/citations.json（由 extract_citations.py 产生），
生成 docs/special/citations.html。
"""

from __future__ import annotations

import html
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from semantic_tags import render_tags_to_html  # 仅用于少数保留 HTML 输出的位置


def render_plain(text: str) -> str:
    """剥除所有 〖TYPE 内容〗 ⟦TYPE 内容⟧ 标注，返回纯文本（不产生 <span>）。"""
    import re
    def _unwrap(m):
        body = m.group(1)
        if "|" in body:
            body = body.split("|", 1)[0]
        return re.sub(r"^[@#&%_;\^+={*?$•◆○◈◉◇◆!\[\]~?]+\s*", "", body)
    text = re.sub(r"〖([^〖〗]*?)〗", _unwrap, text)
    text = re.sub(r"⟦([^⟦⟧]*?)⟧", _unwrap, text)
    return text

IN_JSON = ROOT / "data" / "citations.json"
OUT_HTML = ROOT / "docs" / "special" / "citations.html"

CATEGORY_COLORS = {
    "六经": "#8b0000",
    "诗经·篇类": "#b85450",
    "诗经·篇章": "#c0744e",
    "尚书·篇类": "#7a5230",
    "尚书·篇章": "#8b6742",
    "易经·篇章": "#4a6a8b",
    "经传": "#2d6a2d",
    "诸子": "#1d5d8b",
    "诸子·篇章": "#3e7ab5",
    "兵家": "#704214",
    "辞赋": "#6d2e8b",
    "史籍": "#444444",
    "史籍·自引": "#666666",
    "六艺旁": "#8b5a00",
    "其他": "#888888",
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def category_color(cat: str) -> str:
    return CATEGORY_COLORS.get(cat, "#555")


def render_row(it: dict, chap_link_base: str, highlight: str | None = None) -> str:
    ch_id = it["chapter_id"]
    ch_name = it["chapter_name"]
    para = it["para_id"]
    snippet = it.get("snippet", "")
    plain = render_plain(snippet)
    hl = esc(plain)
    if highlight:
        hl = hl.replace(esc(highlight), f'<mark>{esc(highlight)}</mark>')
    ch_link = f"{chap_link_base}{ch_id}_{ch_name}.html"
    quote = it.get("quote", "")
    trigger = it.get("trigger", "")
    quote_cell = ""
    if quote:
        quote_cell = f'<td class="quote">{esc(quote)}</td>'
    trigger_cell = f'<td class="trigger">{esc(trigger)}</td>' if trigger else ""
    extra_cells = ""
    if quote:
        extra_cells = trigger_cell + quote_cell
    return (
        f'<tr>'
        f'<td class="ch"><a href="{esc(ch_link)}">{esc(ch_id)} {esc(ch_name)}</a></td>'
        f'<td class="para">[{esc(para)}]</td>'
        f'{extra_cells}'
        f'<td class="snippet">{hl}</td>'
        f'</tr>'
    )


def render_book(book: dict, related: list[dict] | None = None) -> str:
    canonical = book["canonical"]
    category = book["category"]
    cit = book["citations"]
    mns = book["mentions"]
    concepts = book.get("concepts", [])
    titles_raw = sorted(set(book["titles_raw"]))
    color = category_color(category)
    total = len(cit) + len(mns)

    out = []
    out.append(f'<div class="cit-book" data-category="{esc(category)}" data-name="{esc(canonical)}">')
    out.append('  <div class="cit-book-header">')
    out.append(f'    <span class="cit-book-cat" style="background:{color}">{esc(category)}</span>')
    out.append(f'    <span class="cit-book-title">{esc(canonical)}</span>')
    if titles_raw and titles_raw != [canonical]:
        out.append(f'    <span class="cit-book-titles-raw">原始标签：{esc("、".join(titles_raw))}</span>')
    count_parts = [f'引 {len(cit)}', f'提 {len(mns)}']
    if concepts:
        count_parts.append(f'概念? {len(concepts)}')
    out.append(f'    <span class="cit-book-count">{" · ".join(count_parts)} · 共 {total}</span>')
    out.append('  </div>')

    # 相关篇目 cross-reference（诗经/尚书 主条目下列出篇类·篇章）
    if related:
        links = "、".join(
            f'<a href="#book-{esc(r["canonical"])}">{esc(r["canonical"])} ({len(r["citations"])+len(r["mentions"])})</a>'
            for r in related
        )
        out.append(f'  <div class="related-works"><strong>相关篇目：</strong>{links}</div>')

    if cit:
        out.append('  <div class="citations-block">')
        out.append('  <div class="section-title">引文（带原文引语）</div>')
        out.append('  <table class="occ-table">')
        out.append('    <thead><tr><th>章</th><th>段</th><th>触发</th><th>引语</th><th>上下文</th></tr></thead>')
        out.append('    <tbody>')
        for c in cit:
            out.append('      ' + render_row(c, '../chapters/'))
        out.append('    </tbody></table>')
        out.append('  </div>')
    if mns:
        out.append('  <div class="mentions-block">')
        out.append('  <div class="section-title">提及（仅书名出现，无引语）</div>')
        out.append('  <table class="occ-table mentions">')
        out.append('    <thead><tr><th>章</th><th>段</th><th>上下文</th></tr></thead>')
        out.append('    <tbody>')
        for m in mns:
            out.append('      ' + render_row(m, '../chapters/'))
        out.append('    </tbody></table>')
        out.append('  </div>')
    if concepts:
        out.append(f'  <details class="concepts-section">')
        out.append(f'    <summary>⚠️ 疑似概念（非书名引用）· {len(concepts)} 处</summary>')
        out.append(f'    <p class="concepts-note">以下 {canonical} 单字标签孤立出现，未伴随「曰/云」触发，亦不与其他典籍合用（如"诗书礼乐"），更可能指礼仪/乐制等抽象概念而非典籍本身。</p>')
        out.append('    <table class="occ-table mentions">')
        out.append('      <thead><tr><th>章</th><th>段</th><th>上下文</th></tr></thead>')
        out.append('      <tbody>')
        for co in concepts:
            out.append('        ' + render_row(co, '../chapters/'))
        out.append('      </tbody></table>')
        out.append('  </details>')
    out.append(f'<span id="book-{esc(canonical)}"></span>')
    out.append('</div>')
    return "\n".join(out)


def render_generic(group: dict) -> str:
    label = group["label"]
    entries = group["entries"]
    out = []
    out.append(f'<div class="generic-group" data-label="{esc(label)}">')
    out.append(f'  <h3>{esc(label)}曰／云（{len(entries)} 条）</h3>')
    out.append('  <table class="occ-table">')
    out.append('    <thead><tr><th>章</th><th>段</th><th>触发</th><th>引语</th></tr></thead>')
    out.append('    <tbody>')
    for it in entries:
        ch_id = it["chapter_id"]
        ch_name = it["chapter_name"]
        para = it["para_id"]
        trig = it.get("trigger", "")
        quote = it.get("quote", "") or render_plain(it.get("snippet", ""))
        ch_link = f'../chapters/{ch_id}_{ch_name}.html'
        quote_html = esc(quote) if quote else ''
        out.append(
            f'      <tr>'
            f'<td class="ch"><a href="{esc(ch_link)}">{esc(ch_id)} {esc(ch_name)}</a></td>'
            f'<td class="para">[{esc(para)}]</td>'
            f'<td class="trigger">{esc(trig)}</td>'
            f'<td class="quote">{quote_html}</td>'
            f'</tr>'
        )
    out.append('    </tbody></table>')
    out.append('</div>')
    return "\n".join(out)


def main() -> None:
    data = json.loads(IN_JSON.read_text(encoding="utf-8"))
    stats = data["stats"]
    books = data["books"]
    generic = data["generic"]

    # 按类别分组
    cat_groups: dict[str, list[dict]] = defaultdict(list)
    for b in books:
        cat_groups[b["category"]].append(b)

    cat_order = [
        "六经", "诗经·篇类", "诗经·篇章",
        "尚书·篇类", "尚书·篇章",
        "易经·篇章", "经传",
        "诸子", "诸子·篇章", "兵家", "辞赋", "六艺旁",
        "史籍", "史籍·自引", "其他",
    ]
    ordered_cats = [c for c in cat_order if c in cat_groups] + \
                   [c for c in cat_groups if c not in cat_order]

    # per-category 统计
    cat_stats = {}
    for c, bs in cat_groups.items():
        cit_n = sum(len(b["citations"]) for b in bs)
        mn_n = sum(len(b["mentions"]) for b in bs)
        cat_stats[c] = {"books": len(bs), "citations": cit_n, "mentions": mn_n}

    # 过滤按钮
    cat_btns = "\n".join(
        f'<button class="filter-btn" data-cat="{esc(c)}" style="border-color:{category_color(c)};">'
        f'{esc(c)} ({cat_stats[c]["citations"]+cat_stats[c]["mentions"]})</button>'
        for c in ordered_cats
    )

    # 建立主条目 → 篇目 cross-reference
    SHIJING_PARENTS = {"诗经"}
    SHANGSHU_PARENTS = {"尚书"}
    YIJING_PARENTS = {"易经"}
    related_map: dict[str, list[dict]] = {}
    for b in books:
        cat = b["category"]
        if cat.startswith("诗经·"):
            related_map.setdefault("诗经", []).append(b)
        elif cat.startswith("尚书·"):
            related_map.setdefault("尚书", []).append(b)
        elif cat.startswith("易经·"):
            related_map.setdefault("易经", []).append(b)

    # 典籍内容
    books_html_parts = []
    for c in ordered_cats:
        books_html_parts.append(f'<h2 class="cat-heading" id="cat-{esc(c)}" style="border-left-color:{category_color(c)};">{esc(c)}（{cat_stats[c]["books"]} 种 · 引 {cat_stats[c]["citations"]} · 提 {cat_stats[c]["mentions"]}）</h2>')
        for b in cat_groups[c]:
            related = related_map.get(b["canonical"])
            books_html_parts.append(render_book(b, related))
    books_html = "\n\n".join(books_html_parts)

    generic_html = "\n\n".join(render_generic(g) for g in generic)

    total_books = stats["total_books"]
    total_cit = stats["total_citations"]
    total_mn = stats["total_mentions"]
    total_concepts = stats.get("total_concepts", 0)
    total_generic = stats["total_generic"]
    chapters_touched = stats["chapters_touched"]
    chapters_scanned = stats["chapters_scanned"]

    page = f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>引文索引 - 史记知识库</title>
    <link rel="stylesheet" href="../css/shiji-styles-v6.css">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family: "Source Han Serif SC", "Noto Serif SC", serif;
            line-height: 1.75; color:#333;
            background-color:#fdfaf6; padding:20px;
        }}
        .container {{
            max-width: 1200px; margin: 0 auto;
            background: white; padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align:center; color:#8b0000; font-size:2.4em;
            margin-bottom:10px;
            border-bottom: 3px double #8b0000; padding-bottom:20px;
        }}
        .subtitle {{
            text-align:center; color:#666; font-size:1.05em;
            margin-bottom:28px;
        }}
        .nav {{
            background:#f5f5f5; padding:12px; margin-bottom:26px;
            border-radius:5px; text-align:center;
        }}
        .nav a {{
            color:#8b4513; text-decoration:none;
            margin:0 12px; font-size:1em;
        }}
        .nav a:hover {{ text-decoration:underline; }}

        .stats {{
            background:#fff8dc; padding:18px; margin-bottom:22px;
            border-radius:5px; border-left:5px solid #8b0000;
        }}
        .stats h3 {{ color:#8b0000; margin-bottom:8px; font-size:1.1em; }}
        .stats ul {{
            list-style:none; display:flex; flex-wrap:wrap;
            gap:6px 22px;
        }}
        .stats li {{ font-size:0.94em; }}
        .stats li strong {{ color:#8b0000; }}

        .intro {{
            background:#f9f4e8; border:1px solid #e6d8a6;
            padding:16px 20px; margin-bottom:22px; border-radius:6px;
            font-size:0.94em; line-height:1.8; color:#4a3a1a;
        }}
        .intro strong {{ color:#8b0000; }}
        .intro code {{
            background:#fff0dc; padding:1px 5px; border-radius:3px;
            color:#8b0000; font-size:0.9em;
        }}

        .filter-bar {{
            margin-bottom:22px; display:flex; flex-wrap:wrap;
            gap:8px; align-items:center;
        }}
        .filter-bar label {{ font-weight:bold; color:#555; margin-right:4px; }}
        .filter-btn {{
            padding:5px 10px; border:1px solid #c0b080;
            border-radius:4px; background:#fffef8; color:#555;
            cursor:pointer; font-size:0.85em; transition:all 0.2s;
        }}
        .filter-btn:hover {{ background:#f8f0d8; }}
        .filter-btn.active {{
            background:#8b0000; color:white; border-color:#8b0000 !important;
        }}

        .tabs {{
            display:flex; gap:6px; margin-bottom:20px;
            border-bottom:2px solid #d4c8a0;
        }}
        .tab-btn {{
            padding:10px 22px; background:#f0e8d0; border:none;
            border-radius:5px 5px 0 0; cursor:pointer;
            font-size:1em; color:#5a4a2a; font-weight:bold;
        }}
        .tab-btn.active {{ background:#8b0000; color:white; }}

        .tab-pane {{ display:none; }}
        .tab-pane.active {{ display:block; }}

        .search-input {{
            padding:6px 10px; border:1px solid #c0b080;
            border-radius:4px; font-size:0.9em;
            margin-left:auto; width:220px;
        }}

        .cat-heading {{
            color:#5a3a1a; font-size:1.35em; margin:32px 0 14px;
            padding:8px 14px; border-left:5px solid #8b0000;
            background:#f8f0e0; border-radius:0 4px 4px 0;
        }}

        .cit-book {{
            margin-bottom:1.8em; border:1px solid #e6e0c0;
            border-radius:6px; background:#fffef8; overflow:hidden;
        }}
        .cit-book.hidden {{ display:none; }}
        .cit-book-header {{
            padding:12px 18px; display:flex; align-items:center;
            gap:12px; flex-wrap:wrap;
            background:linear-gradient(135deg, #f8f5e8, #fffef8);
            border-bottom:1px solid #e6e0c0;
        }}
        .cit-book-cat {{
            display:inline-block; color:white;
            padding:2px 9px; border-radius:3px;
            font-size:0.82em; letter-spacing:0.5px;
        }}
        .cit-book-title {{
            font-size:1.15em; color:#333; font-weight:bold;
        }}
        .cit-book-titles-raw {{
            font-size:0.82em; color:#888;
        }}
        .cit-book-count {{
            margin-left:auto; color:#8b0000; font-weight:bold;
            font-size:0.88em; background:#fff0dc;
            padding:2px 10px; border-radius:3px;
        }}
        .section-title {{
            padding:8px 18px; background:#faf5e8;
            color:#5a4a2a; font-size:0.92em; font-weight:bold;
            border-bottom:1px solid #eee;
        }}

        .occ-table {{
            width:100%; border-collapse:collapse;
            font-size:0.88em;
        }}
        .occ-table th {{
            background:#f8f5e8; color:#5a4a2a;
            padding:6px 10px; text-align:left;
            border-bottom:2px solid #d4c8a0;
        }}
        .occ-table td {{
            padding:6px 10px; border-bottom:1px solid #eee;
            vertical-align:top;
        }}
        .occ-table tr:hover td {{ background:#fdfaf0; }}
        .occ-table .ch {{ white-space:nowrap; }}
        .occ-table .ch a {{ color:#8b4513; text-decoration:none; }}
        .occ-table .ch a:hover {{ text-decoration:underline; }}
        .occ-table .para {{ color:#999; white-space:nowrap; }}
        .occ-table .trigger {{
            color:#8b4513; font-weight:bold; white-space:nowrap;
            background:#fff0dc;
        }}
        .occ-table .quote {{
            color:#5a3a1a; max-width:380px;
        }}
        .occ-table .snippet {{
            font-family:"Source Han Serif SC", serif;
            line-height:1.8; color:#444;
        }}
        .occ-table mark {{
            background:#fff068; color:#8b0000;
            padding:0 3px; font-weight:bold; border-radius:2px;
        }}
        .mentions {{ background:#fafafa; }}
        .related-works {{
            padding:8px 18px; background:#f0f7ff;
            border-bottom:1px solid #d0e0f0; font-size:0.9em;
            color:#4a5a6a;
        }}
        .related-works a {{ color:#1d5d8b; margin:0 4px; text-decoration:none; }}
        .related-works a:hover {{ text-decoration:underline !important; }}
        .concepts-section {{
            margin:0; padding:0; border-top:1px dashed #d4c8a0;
        }}
        .concepts-section summary {{
            padding:10px 18px; background:#fff5e5;
            color:#8b5a00; cursor:pointer; font-size:0.92em;
            list-style:none;
        }}
        .concepts-section summary::before {{ content:"▸ "; color:#8b5a00; }}
        .concepts-section[open] summary::before {{ content:"▾ "; }}
        .concepts-note {{
            padding:10px 18px; background:#fffbf0;
            font-size:0.88em; color:#6a5a3a; line-height:1.7;
            border-bottom:1px solid #eee;
        }}
        /* 去除实体标注/章节链接的下划·波浪·点线装饰与斜体，仅保留颜色区分 */
        .occ-table,
        .occ-table *,
        .occ-table a,
        .occ-table .snippet .cit-book,
        .occ-table .snippet .mythical,
        .occ-table .snippet .biology,
        .occ-table .snippet .astronomy,
        .occ-table .snippet .artifact,
        .occ-table .snippet .ritual,
        .occ-table .snippet .place,
        .occ-table .snippet .person,
        .occ-table .snippet .concept,
        .occ-table .snippet .official,
        .occ-table .snippet .identity,
        .occ-table .snippet .time,
        .occ-table .snippet .tribe,
        .occ-table .snippet .dynasty,
        .occ-table .snippet .feudal-state,
        .occ-table .snippet .institution,
        .occ-table .snippet .legal,
        .occ-table .snippet .quantity,
        .occ-table .snippet .verb-military,
        .occ-table .snippet .verb-penalty,
        .occ-table .snippet .verb-political,
        .occ-table .snippet .verb-economic {{
            text-decoration: none !important;
            text-decoration-line: none !important;
            text-decoration-style: solid !important;
            text-decoration-thickness: 0 !important;
            text-underline-offset: 0 !important;
            border-bottom: 0 none transparent !important;
            background-image: none !important;
            background-color: transparent !important;
            font-style: normal !important;
        }}
        .occ-table a:hover {{ text-decoration: underline !important; }}

        .generic-group {{
            margin-bottom:1.8em; border:1px solid #e6e0c0;
            border-radius:6px; overflow:hidden;
        }}
        .generic-group h3 {{
            padding:10px 18px; background:#f8f5e8;
            color:#5a4a2a; font-size:1.05em;
            border-bottom:1px solid #d4c8a0;
        }}

        .footer {{
            text-align:center; margin-top:40px;
            padding-top:20px; border-top:1px solid #ddd;
            color:#999; font-size:0.88em;
        }}
        @media (max-width: 768px) {{
            .container {{ padding:20px 15px; }}
            h1 {{ font-size:1.7em; }}
            .cit-book-header {{ gap:8px; }}
            .occ-table {{ font-size:0.82em; }}
            .occ-table .quote {{ max-width:none; }}
            .search-input {{ width:100%; margin-left:0; margin-top:6px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>史记引文索引</h1>
        <div class="subtitle">《史记》对诗经·尚书·易经·春秋·经传·诸子·兵家·辞赋的引用与提及</div>

        <div class="nav">
            <a href="special_index.html">&larr; 专项索引</a>
            <a href="../index.html">首页</a>
            <a href="bihui.html">避讳改字</a>
            <a href="shihao.html">谥号索引</a>
            <a href="chengyu.html">成语典故</a>
        </div>

        <div class="intro">
            <strong>何为引文？</strong>《史记》成于西汉，司马迁博览群籍，行文间屡屡征引先秦典籍。
            本专题以原文中已标注的书名实体 <code>〖{{典籍〗</code> 为主要线索，分三级：
            <br>① <strong>引文</strong>：书名紧跟「曰/云」并附引语（最可靠，附具体诗句/文句）；
            <br>② <strong>提及</strong>：书名出现但无引语，或与其他书名合用（如「诗书礼乐」「六经」）；
            <br>③ <strong>疑似概念</strong>：单字 <code>礼</code> <code>乐</code> 孤立出现、无「曰/云」触发、未与其他书名合用者，
            本专题将其归入"疑似概念"折叠区以降低噪声（如"问礼于老子"中的"礼"实为礼仪概念而非《礼》经）。
            <br>另单列<strong>泛引</strong>：<code>语曰·谚曰·野语曰·鄙语曰</code>，系古语俗谚之传诵，难以归属具体典籍。
            <br>诗经、尚书的具体篇目（大雅·小雅·国风·关雎·康诰·甫刑…）在主条目下列出跨链。
        </div>

        <div class="stats">
            <h3>统计概览</h3>
            <ul>
                <li><strong>典籍种类：</strong>{total_books}（归一化后）</li>
                <li><label><input type="checkbox" id="toggle-cit" checked> <strong>引文：</strong>{total_cit} 条</label></li>
                <li><label><input type="checkbox" id="toggle-mn" checked> <strong>提及：</strong>{total_mn} 条</label></li>
                <li><strong>疑似概念：</strong>{total_concepts} 条（已折叠）</li>
                <li><strong>泛引：</strong>{total_generic} 条</li>
                <li><strong>涉及章数：</strong>{chapters_touched} / {chapters_scanned}</li>
            </ul>
        </div>

        <div class="tabs">
            <button class="tab-btn active" data-tab="books">典籍引用（{total_books} 种）</button>
            <button class="tab-btn" data-tab="generic">泛引 · 语谚（{total_generic} 条）</button>
        </div>

        <div id="tab-books" class="tab-pane active">
            <div class="filter-bar">
                <label>类别：</label>
                <button class="filter-btn active" data-cat="ALL">全部</button>
                {cat_btns}
                <input class="search-input" type="text" placeholder="书名关键字…" id="cit-book-search">
            </div>
            {books_html}
        </div>

        <div id="tab-generic" class="tab-pane">
            {generic_html}
        </div>

        <div class="footer">
            <p>史记知识库 · 引文索引</p>
            <p style="margin-top:6px;">
                数据源：<code>data/citations.json</code>　·
                扫描脚本：<code>scripts/extract_citations.py</code>　·
                渲染脚本：<code>scripts/render_citations_html.py</code>
            </p>
        </div>
    </div>

    <script>
        // Tab 切换
        document.querySelectorAll('.tab-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
            }});
        }});

        // 类别筛选
        document.querySelectorAll('.filter-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const cat = btn.dataset.cat;
                document.querySelectorAll('.cit-book').forEach(b => {{
                    if (cat === 'ALL' || b.dataset.category === cat) {{
                        b.classList.remove('hidden');
                    }} else {{
                        b.classList.add('hidden');
                    }}
                }});
                document.querySelectorAll('.cat-heading').forEach(h => {{
                    const id = h.id.replace('cat-', '');
                    if (cat === 'ALL' || cat === id) h.style.display = ''; else h.style.display = 'none';
                }});
            }});
        }});

        // 引文 / 提及 显隐切换
        const toggleCit = document.getElementById('toggle-cit');
        const toggleMn = document.getElementById('toggle-mn');
        function applyToggles() {{
            const showCit = toggleCit.checked;
            const showMn = toggleMn.checked;
            document.querySelectorAll('.citations-block').forEach(el => el.style.display = showCit ? '' : 'none');
            document.querySelectorAll('.mentions-block').forEach(el => el.style.display = showMn ? '' : 'none');
        }}
        toggleCit.addEventListener('change', applyToggles);
        toggleMn.addEventListener('change', applyToggles);

        // 书名搜索
        const searchInput = document.getElementById('cit-book-search');
        searchInput.addEventListener('input', () => {{
            const kw = searchInput.value.trim();
            document.querySelectorAll('.cit-book').forEach(b => {{
                if (!kw) {{ b.classList.remove('hidden'); return; }}
                const name = b.dataset.name || '';
                if (name.indexOf(kw) >= 0) b.classList.remove('hidden');
                else b.classList.add('hidden');
            }});
        }});
    </script>
</body>
</html>
"""
    OUT_HTML.write_text(page, encoding="utf-8")
    print(f"[输出] {OUT_HTML.relative_to(ROOT)}")
    print(f"[统计] 典籍 {total_books} 种 · 引文 {total_cit} · 提及 {total_mn} · 泛引 {total_generic} · 涉及 {chapters_touched} 章")


if __name__ == "__main__":
    main()
