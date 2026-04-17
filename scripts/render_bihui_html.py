#!/usr/bin/env python3
"""渲染《史记》避讳改字专题 HTML 页面。

读取 data/taboo_characters.json（由 scan_taboo_characters.py 产生），
生成 docs/special/bihui.html。
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from semantic_tags import render_tags_to_html

IN_JSON = ROOT / "data" / "taboo_characters.json"
OUT_HTML = ROOT / "docs" / "special" / "bihui.html"

CATEGORY_COLORS = {
    "秦皇讳": "#2c2c2c",
    "汉帝讳": "#c0392b",
    "家讳": "#8e44ad",
    "后讳·西汉宣帝": "#d35400",
    "后讳·东汉明帝": "#1abc9c",
    "后讳·东汉光武帝": "#f39c12",
    "后讳·东汉殇帝": "#7f8c8d",
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def render_rule(rule: dict) -> str:
    rule_id = rule["id"]
    category = rule["category"]
    cat_color = CATEGORY_COLORS.get(category, "#8b0000")
    taboo_for = rule["taboo_for"]
    taboo_char = rule["taboo_char"]
    replaced_by = rule["replaced_by"]
    scope = rule["scope"]
    confidence = rule["confidence"]
    sources = rule.get("sources", [])
    note = rule.get("note", "")

    conf_badge = (
        '<span class="badge badge-high">三家注/文献明证</span>'
        if confidence == "high"
        else '<span class="badge badge-suspected">学界存疑</span>'
    )

    out: list[str] = []
    out.append(f'<div class="rule" data-category="{esc(category)}" data-confidence="{confidence}">')
    out.append('  <div class="rule-header">')
    out.append(
        f'    <span class="rule-id" style="background:{cat_color}">{esc(rule_id)}</span>'
    )
    out.append(f'    <span class="rule-category">{esc(category)}</span>')
    out.append(
        f'    <span class="rule-title">{esc(taboo_for)}　'
        f'<span class="taboo-chars">讳「{esc(taboo_char)}」→ 改「{esc(replaced_by)}」</span></span>'
    )
    out.append(f"    {conf_badge}")
    out.append("  </div>")
    out.append('  <div class="rule-meta">')
    out.append(f'    <div><strong>生效范围：</strong>{esc(scope)}</div>')
    if note:
        out.append(f'    <div><strong>说明：</strong>{esc(note)}</div>')
    if sources:
        out.append("    <details class=\"sources\">")
        out.append(f"      <summary>文献证据（{len(sources)} 条）</summary>")
        out.append("      <ul>")
        for s in sources:
            out.append(f"        <li>{esc(s)}</li>")
        out.append("      </ul>")
        out.append("    </details>")
    out.append("  </div>")

    for pat in rule["patterns"]:
        form = pat["form"]
        orig = pat["original"]
        kind = pat["kind"]
        pnote = pat.get("note", "")
        occ = pat.get("occurrences", [])
        is_preserved = form == orig
        klass = "preserved" if is_preserved else "avoided"
        form_label = (
            f'本字：<code class="form">{esc(form)}</code>'
            if is_preserved
            else f'<code class="form">{esc(form)}</code> <span class="arrow">←</span> <code class="orig">{esc(orig)}</code>'
        )

        out.append(f'  <div class="pattern {klass}">')
        out.append('    <div class="pattern-header">')
        out.append(f"      <div class=\"pattern-form\">{form_label}</div>")
        out.append(f"      <div class=\"pattern-kind\">{esc(kind)}</div>")
        out.append(f"      <div class=\"pattern-count\">{len(occ)} 处</div>")
        out.append("    </div>")
        if pnote:
            out.append(f'    <div class="pattern-note">{esc(pnote)}</div>')

        if occ:
            out.append('    <table class="occ-table">')
            out.append("      <thead><tr><th>章</th><th>段</th><th>原文片段</th></tr></thead>")
            out.append("      <tbody>")
            for o in occ:
                ch_id = o["chapter_id"]
                ch_name = o["chapter_name"]
                para = o["para_id"]
                snippet = o["snippet"]
                # 先将标注符号转为带样式 span（〖@蒯通〗 → <span class="person">蒯通</span>）
                hl = render_tags_to_html(snippet)
                # 再对改字词组加高亮（<mark>）
                hl = hl.replace(form, f'<mark>{esc(form)}</mark>')
                ch_link = f"../chapters/{ch_id}_{ch_name}.html"
                out.append(
                    f'        <tr>'
                    f'<td class="ch"><a href="{esc(ch_link)}">{esc(ch_id)} {esc(ch_name)}</a></td>'
                    f'<td class="para">[{esc(para)}]</td>'
                    f'<td class="snippet">{hl}</td>'
                    f'</tr>'
                )
            out.append("      </tbody>")
            out.append("    </table>")
        else:
            out.append('    <div class="empty">（全书无匹配）</div>')

        out.append("  </div>")

    out.append("</div>")
    return "\n".join(out)


def main() -> None:
    data = json.loads(IN_JSON.read_text(encoding="utf-8"))
    rules = data["rules"]
    stats = data["_stats"]

    total_rules = stats["total_rules"]
    total_instances = stats["total_instances"]
    chapters_scanned = stats["chapters_scanned"]

    # per-category stats
    cat_stats: dict[str, dict] = {}
    for r in rules:
        c = r["category"]
        cat_stats.setdefault(c, {"count": 0, "instances": 0})
        cat_stats[c]["count"] += 1
        cat_stats[c]["instances"] += r["instance_count"]

    rules_html = "\n\n".join(render_rule(r) for r in rules)

    cat_filter_btns = '\n'.join(
        f'<button class="filter-btn" data-cat="{esc(c)}">{esc(c)} ({cat_stats[c]["instances"]})</button>'
        for c in cat_stats
    )

    page = f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>避讳改字专题 - 史记知识库</title>
    <link rel="stylesheet" href="../css/shiji-styles-v6.css">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family: "Source Han Serif SC", "Noto Serif SC", serif;
            line-height: 1.75; color:#333;
            background-color:#fdfaf6; padding:20px;
        }}
        .container {{
            max-width: 1100px; margin: 0 auto;
            background: white; padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align:center; color:#8b0000; font-size:2.5em;
            margin-bottom:10px;
            border-bottom: 3px double #8b0000; padding-bottom:20px;
        }}
        .subtitle {{
            text-align:center; color:#666; font-size:1.1em;
            margin-bottom:30px;
        }}
        .nav {{
            background:#f5f5f5; padding:12px; margin-bottom:30px;
            border-radius:5px; text-align:center;
        }}
        .nav a {{
            color:#8b4513; text-decoration:none;
            margin:0 15px; font-size:1.05em;
        }}
        .nav a:hover {{ text-decoration:underline; }}

        .stats {{
            background:#fff8dc; padding:20px; margin-bottom:25px;
            border-radius:5px; border-left:5px solid #8b0000;
        }}
        .stats h3 {{ color:#8b0000; margin-bottom:10px; font-size:1.15em; }}
        .stats ul {{
            list-style:none; display:flex; flex-wrap:wrap;
            gap:6px 24px;
        }}
        .stats li {{ font-size:0.95em; }}
        .stats li strong {{ color:#8b0000; }}

        .intro {{
            background:#f9f4e8; border:1px solid #e6d8a6;
            padding:18px 22px; margin-bottom:25px; border-radius:6px;
            font-size:0.95em; line-height:1.8; color:#4a3a1a;
        }}
        .intro strong {{ color:#8b0000; }}

        .filter-bar {{
            margin-bottom:25px; display:flex; flex-wrap:wrap;
            gap:8px; align-items:center;
        }}
        .filter-bar label {{ font-weight:bold; color:#555; margin-right:6px; }}
        .filter-btn {{
            padding:6px 12px; border:1px solid #c0b080;
            border-radius:4px; background:#fffef8; color:#555;
            cursor:pointer; font-size:0.88em; transition:all 0.2s;
        }}
        .filter-btn:hover {{ background:#f8f0d8; }}
        .filter-btn.active {{
            background:#8b0000; color:white; border-color:#8b0000;
        }}

        .rule {{
            margin-bottom:2.5em; border:1px solid #e6e0c0;
            border-radius:8px; background:#fffef8; overflow:hidden;
        }}
        .rule.hidden {{ display:none; }}
        .rule-header {{
            padding:14px 20px; display:flex; align-items:center;
            gap:12px; flex-wrap:wrap;
            background:linear-gradient(135deg, #f8f5e8, #fffef8);
            border-bottom:1px solid #e6e0c0;
        }}
        .rule-id {{
            display:inline-block; color:white;
            padding:3px 10px; border-radius:4px;
            font-weight:bold; font-size:0.85em;
            letter-spacing:0.5px;
        }}
        .rule-category {{
            color:#6b5b3a; font-size:0.9em;
        }}
        .rule-title {{
            flex:1; font-size:1.2em; color:#333; font-weight:bold;
        }}
        .rule-title .taboo-chars {{
            color:#8b0000; margin-left:6px; font-size:0.92em;
        }}
        .badge {{
            display:inline-block; padding:2px 8px;
            border-radius:3px; font-size:0.78em;
            font-weight:normal;
        }}
        .badge-high {{ background:#d4eada; color:#2d6a2d; }}
        .badge-suspected {{ background:#f5e3c0; color:#8b5a00; }}

        .rule-meta {{
            padding:12px 20px; background:#fffef8;
            border-bottom:1px solid #eee; font-size:0.9em;
            color:#555;
        }}
        .rule-meta div {{ margin-bottom:4px; }}
        .rule-meta details.sources {{
            margin-top:6px;
        }}
        .rule-meta details.sources summary {{
            cursor:pointer; color:#8b4513; font-weight:bold;
        }}
        .rule-meta details.sources ul {{
            margin-top:8px; padding-left:20px; color:#555;
        }}
        .rule-meta details.sources li {{
            margin-bottom:4px; font-size:0.88em;
        }}

        .pattern {{
            padding:14px 20px; border-bottom:1px solid #eee;
        }}
        .pattern:last-child {{ border-bottom:none; }}
        .pattern.preserved {{ background:#f6f9f6; }}
        .pattern-header {{
            display:flex; gap:16px; align-items:center;
            flex-wrap:wrap; margin-bottom:8px;
        }}
        .pattern-form {{
            font-size:1.1em; color:#333;
        }}
        .pattern-form .form {{
            color:#8b0000; font-weight:bold; font-size:1.1em;
            background:#fff0f0; padding:1px 6px; border-radius:3px;
        }}
        .pattern-form .orig {{
            color:#2d6a2d; font-weight:bold; font-size:1.05em;
            background:#f0faf0; padding:1px 6px; border-radius:3px;
        }}
        .pattern-form .arrow {{ color:#888; margin:0 4px; }}
        .pattern.preserved .pattern-form .form {{
            color:#2d6a2d; background:#f0faf0;
        }}
        .pattern-kind {{
            font-size:0.85em; color:#666;
            background:#e8e0c8; padding:2px 8px; border-radius:3px;
        }}
        .pattern-count {{
            margin-left:auto; color:#8b0000; font-weight:bold;
            font-size:0.92em;
        }}
        .pattern-note {{
            color:#666; font-size:0.88em; margin-bottom:10px;
            line-height:1.6; padding-left:6px;
            border-left:3px solid #e6d8a6;
        }}

        .occ-table {{
            width:100%; border-collapse:collapse;
            font-size:0.88em; margin-top:8px;
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
        .occ-table .snippet {{
            font-family:"Source Han Serif SC", serif;
            line-height:1.8; color:#333;
        }}
        /* 改字词组的黄底高亮 */
        .occ-table mark {{
            background:#fff068; color:#8b0000;
            padding:0 3px; font-weight:bold; border-radius:2px;
            box-shadow: 0 0 0 1px rgba(139,0,0,0.35);
        }}
        /* 覆盖 shiji-styles-v6.css 的 body 默认，避免影响本页布局 */
        body.container-reset {{
            max-width: none; line-height: 1.75;
        }}
        /* 在片段中让实体标注更紧凑 */
        .occ-table .snippet .person,
        .occ-table .snippet .place,
        .occ-table .snippet .official,
        .occ-table .snippet .identity,
        .occ-table .snippet .time,
        .occ-table .snippet .dynasty,
        .occ-table .snippet .feudal-state,
        .occ-table .snippet .institution,
        .occ-table .snippet .tribe,
        .occ-table .snippet .artifact,
        .occ-table .snippet .astronomy,
        .occ-table .snippet .mythical,
        .occ-table .snippet .biology,
        .occ-table .snippet .book,
        .occ-table .snippet .ritual,
        .occ-table .snippet .legal,
        .occ-table .snippet .concept,
        .occ-table .snippet .quantity,
        .occ-table .snippet .verb-military,
        .occ-table .snippet .verb-penalty,
        .occ-table .snippet .verb-political,
        .occ-table .snippet .verb-economic {{
            padding: 0 1px;
        }}
        /* 动词类（shiji-styles-v6.css 可能未完整定义，补充基本样式） */
        .occ-table .snippet .verb-military {{
            color: #b22222; border-bottom: 1px dotted rgba(178,34,34,0.5);
        }}
        .occ-table .snippet .verb-penalty {{
            color: #8b0000; border-bottom: 1px dotted rgba(139,0,0,0.5);
        }}
        .occ-table .snippet .verb-political {{
            color: #4682b4; border-bottom: 1px dotted rgba(70,130,180,0.5);
        }}
        .occ-table .snippet .verb-economic {{
            color: #2e8b57; border-bottom: 1px dotted rgba(46,139,87,0.5);
        }}
        .empty {{
            color:#999; font-style:italic;
            padding:10px 0 0 6px; font-size:0.9em;
        }}

        .footer {{
            text-align:center; margin-top:40px;
            padding-top:20px; border-top:1px solid #ddd;
            color:#999; font-size:0.9em;
        }}
        @media (max-width: 768px) {{
            .container {{ padding:20px 15px; }}
            h1 {{ font-size:1.8em; }}
            .rule-header {{ gap:8px; }}
            .pattern-header {{ gap:8px; }}
            .occ-table {{ font-size:0.82em; }}
            .occ-table th, .occ-table td {{ padding:5px 6px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>史记避讳改字专题</h1>
        <div class="subtitle">秦皇 · 汉帝 · 家讳 · 后讳 — 《史记》全书 130 篇改字实例</div>

        <div class="nav">
            <a href="special_index.html">&larr; 专项索引</a>
            <a href="../index.html">首页</a>
            <a href="shihao.html">谥号索引</a>
            <a href="jun_titles.html">君号索引</a>
            <a href="xingshi.html">姓氏宗族</a>
        </div>

        <div class="intro">
            <strong>何为避讳改字？</strong>古代为尊崇帝王、父祖之名，凡遇其名字，须以同义或同音之字替换。
            《史记》成书于西汉武帝朝，司马迁已避秦始皇、高祖、惠帝、文帝、景帝、武帝诸讳，并避其父司马谈家讳；
            后世传抄又陆续加入宣帝、光武、明帝、殇帝等讳，故今传本避讳字层层叠加。
            本专题即对这些改字逐条考释、定位至原文。
        </div>

        <div class="stats">
            <h3>统计概览</h3>
            <ul>
                <li><strong>避讳规则：</strong>{total_rules} 条</li>
                <li><strong>改字实例：</strong>{total_instances} 处</li>
                <li><strong>扫描章数：</strong>{chapters_scanned} 章</li>
                <li><strong>类别：</strong>{len(cat_stats)} 类（秦皇讳·汉帝讳·家讳·后讳）</li>
            </ul>
        </div>

        <div class="filter-bar">
            <label>按类别筛选：</label>
            <button class="filter-btn active" data-cat="ALL">全部 ({total_instances})</button>
            {cat_filter_btns}
        </div>

        <div class="rules-list">
{rules_html}
        </div>

        <div class="footer">
            <p>史记知识库 · 避讳改字专题</p>
            <p style="margin-top:6px;">
                数据源：<code>data/taboo_characters.json</code>　·
                扫描脚本：<code>scripts/scan_taboo_characters.py</code>　·
                规则表：<code>data/taboo_characters.rules.json</code>
            </p>
            <p style="margin-top:6px; color:#bbb; font-size:0.82em;">
                参考：陈垣《史讳举例》· 王彦坤《历代避讳字汇典》· 顾炎武《日知录·避讳》
            </p>
        </div>
    </div>

    <script>
        document.querySelectorAll('.filter-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const cat = btn.dataset.cat;
                document.querySelectorAll('.rule').forEach(r => {{
                    if (cat === 'ALL' || r.dataset.category === cat) {{
                        r.classList.remove('hidden');
                    }} else {{
                        r.classList.add('hidden');
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>
"""
    OUT_HTML.write_text(page, encoding="utf-8")
    print(f"[输出] {OUT_HTML.relative_to(ROOT)}")
    print(f"[统计] 规则 {total_rules} 条，实例 {total_instances} 处，类别 {len(cat_stats)}")


if __name__ == "__main__":
    main()
