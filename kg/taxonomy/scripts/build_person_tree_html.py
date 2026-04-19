#!/usr/bin/env python3
"""
从 kg/taxonomy/person.ttl 生成 docs/kg/person_tree.html — 可交互的人物分类树。

输入：
  kg/taxonomy/person.ttl          — 130 类 + 1825 实例的 OWL/RDF 本体

输出：
  docs/kg/person_tree.html        — 原地覆盖（折叠树 + 搜索 + 计数）

用法：
  python kg/taxonomy/scripts/build_person_tree_html.py
"""

from __future__ import annotations

import html
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TTL = ROOT / "kg" / "taxonomy" / "person.ttl"
OUT = ROOT / "docs" / "kg" / "person_tree.html"

RE_CLASS = re.compile(
    r"^per:(\S+)\s+a\s+owl:Class\s*;\s*"
    r"(?:rdfs:subClassOf\s+per:(\S+)\s*;\s*)?"
    r'rdfs:label\s+"([^"]+)"@zh'
    r'(?:\s*;\s*:order\s+(\d+))?'
    r'\s*\.',
    re.MULTILINE,
)

RE_INSTANCE = re.compile(
    r'^per:(\S+)\s+a\s+per:(\S+)\s*;\s*'
    r'rdfs:label\s+"([^"]+)"@zh\s*'
    r'(?:;\s*:count\s+(\d+)\s*)?\.',
    re.MULTILINE,
)


# 顶层 9 大分支的推荐展示顺序（按《史记》叙事主线）
TOP_ORDER = ["王室", "臣", "策士", "诸子百家", "社会人物", "方术", "外邦", "虚构人物", "疑似误标"]

# 每个顶层分支的图标/配色（视觉层级辅助）
BRANCH_META = {
    "王室":   ("👑", "#a15c10", "#fff0d9", "royal"),
    "臣":    ("🏛️", "#5c3a8a", "#e4d6f2", "official"),
    "策士":   ("🎯", "#304a82", "#e1e8f6", "strategist"),
    "诸子百家": ("📜", "#355a22", "#e3eedc", "scholar"),
    "社会人物": ("⚔️", "#8a2020", "#f3dede", "social"),
    "方术":   ("🔮", "#6a2f82", "#ede4f2", "mystic"),
    "外邦":   ("🏞️", "#2f6060", "#d9ecee", "foreign"),
    "虚构人物": ("🎭", "#8a5a12", "#fbe7c8", "fictional"),
    "疑似误标": ("⚠️", "#a03030", "#fdecea", "mislabel"),
}


def parse_ttl(text: str):
    """返回 (classes_by_id, parent, label, instances_by_class)。

    classes_by_id : {class_id: label}
    parent        : {class_id: parent_class_id or None}
    instances_by_class : {class_id: [(label, count), ...]}
    """
    classes: dict[str, str] = {}
    parent: dict[str, str | None] = {}
    label: dict[str, str] = {}
    order: dict[str, int] = {}   # 类在同级中的时序编号

    for m in RE_CLASS.finditer(text):
        cid, pid, lbl, ord_ = m.group(1), m.group(2), m.group(3), m.group(4)
        classes[cid] = lbl
        label[cid] = lbl
        parent[cid] = pid  # 可能为 None（根）
        order[cid] = int(ord_) if ord_ else 99

    instances: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for m in RE_INSTANCE.finditer(text):
        _iid, cid, lbl, cnt = m.group(1), m.group(2), m.group(3), m.group(4)
        if cid in classes:
            instances[cid].append((lbl, int(cnt) if cnt else 0))

    # 按 count 降序
    for cid in instances:
        instances[cid].sort(key=lambda x: (-x[1], x[0]))

    return classes, parent, label, instances, order


def build_children(parent: dict[str, str | None]) -> dict[str, list[str]]:
    children: dict[str, list[str]] = defaultdict(list)
    for cid, pid in parent.items():
        if pid:
            children[pid].append(cid)
    return children


def compute_totals(
    root: str,
    children: dict[str, list[str]],
    instances: dict[str, list[tuple[str, int]]],
) -> dict[str, int]:
    """每个类的子树实例总数（含自身直接实例 + 所有后代）。"""
    total: dict[str, int] = {}

    def dfs(cid: str) -> int:
        n = len(instances.get(cid, []))
        for ch in children.get(cid, []):
            n += dfs(ch)
        total[cid] = n
        return n

    dfs(root)
    return total


def render_instances(items: list[tuple[str, int]]) -> str:
    """把实例列表渲染为 .instance 芯片流。"""
    if not items:
        return ""
    chips = []
    for name, cnt in items:
        nm = html.escape(name)
        title = f"{nm}（出现 {cnt} 次）"
        chips.append(
            f'<span class="inst" data-name="{nm}" title="{title}">'
            f'{nm}<span class="inst-cnt">{cnt}</span></span>'
        )
    return f'<div class="inst-list">{"".join(chips)}</div>'


def render_node(
    cid: str,
    label_map: dict[str, str],
    children: dict[str, list[str]],
    instances: dict[str, list[tuple[str, int]]],
    totals: dict[str, int],
    depth: int,
    branch_css: str,
    order_map: dict[str, int] | None = None,
) -> str:
    lbl = html.escape(label_map[cid])
    sub_total = totals[cid]
    direct = len(instances.get(cid, []))
    # 优先按 :order 排序，order 相同时按人数降序
    def child_key(c):
        o = order_map.get(c, 99) if order_map else 99
        return (o, -totals[c], label_map[c])
    kids = sorted(children.get(cid, []), key=child_key)

    # 计数标签：直接 vs 子树
    if kids:
        if direct > 0:
            cnt_html = (
                f'<span class="cnt">{sub_total}<span class="cnt-sub"> 人</span></span>'
                f'<span class="cnt-direct" title="本类直接实例">本级 {direct}</span>'
            )
        else:
            cnt_html = f'<span class="cnt">{sub_total}<span class="cnt-sub"> 人</span></span>'
    else:
        cnt_html = f'<span class="cnt">{direct}<span class="cnt-sub"> 人</span></span>'

    # 默认展开前两层，深层折叠
    open_attr = " open" if depth < 2 else ""

    parts = [
        f'<details class="node d{depth} {branch_css}"{open_attr} data-label="{lbl}">',
        f'<summary><span class="lbl">{lbl}</span>{cnt_html}</summary>',
    ]

    # 先渲染子类（树枝）
    if kids:
        parts.append('<div class="children">')
        for ch in kids:
            parts.append(render_node(ch, label_map, children, instances, totals, depth + 1, branch_css, order_map))
        parts.append("</div>")

    # 再渲染本类的直接实例（叶子）
    if direct:
        parts.append(render_instances(instances[cid]))

    parts.append("</details>")
    return "".join(parts)


def render_top_branches(
    root: str,
    label_map: dict[str, str],
    children: dict[str, list[str]],
    instances: dict[str, list[tuple[str, int]]],
    totals: dict[str, int],
    order_map: dict[str, int] | None = None,
) -> str:
    """把根节点 人物 下的一级分支按 :order 排序渲染。"""
    top = children.get(root, [])
    # 优先按 :order，其次按 TOP_ORDER，最后按人数
    top_order_idx = {name: i for i, name in enumerate(TOP_ORDER)}
    def top_key(c):
        o = order_map.get(c, 99) if order_map else 99
        return (o, top_order_idx.get(label_map[c], 99), -totals[c])
    ordered = sorted(top, key=top_key)

    out = []
    for cid in ordered:
        lbl = label_map[cid]
        meta = BRANCH_META.get(lbl, ("•", "#444", "#eee", slug(lbl)))
        icon, _color, _bg, _key = meta
        css_key = f"br-{_key}"
        n = totals[cid]
        def child_key(c):
            o = order_map.get(c, 99) if order_map else 99
            return (o, -totals[c], label_map[c])
        kids = sorted(children.get(cid, []), key=child_key)

        out.append(f'<section class="top-branch {css_key}">')
        out.append(
            f'<header class="top-header">'
            f'<span class="top-icon">{icon}</span>'
            f'<span class="top-lbl">{html.escape(lbl)}</span>'
            f'<span class="top-cnt">{n} 人</span>'
            f'</header>'
        )
        out.append('<div class="top-body">')
        for ch in kids:
            out.append(render_node(ch, label_map, children, instances, totals, 0, css_key, order_map))
        # 顶层分支自身若也有直接实例（如"外邦"下可能有未归子国的），同样展出
        if instances.get(cid):
            out.append(render_instances(instances[cid]))
        out.append("</div>")
        out.append("</section>")

    return "".join(out)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()) or "x"


def build_css() -> str:
    # 分支配色注入
    br_css = []
    for name, (_icon, color, bg, key) in BRANCH_META.items():
        br_css.append(f".br-{key} > .top-header {{ background: {bg}; color: {color}; border-color: {color}33; }}")
        br_css.append(f".node.br-{key} > summary .lbl {{ color: {color}; }}")
    br_css_s = "\n        ".join(br_css)

    return f"""
        body {{
            max-width: 1280px;
            margin: 0 auto;
            padding: 20px;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
            background-color: #faf8f0;
            color: #222;
            line-height: 1.55;
        }}
        h1 {{
            text-align: center;
            color: #2e5f5f;
            border-bottom: 3px solid #2e5f5f;
            padding-bottom: 12px;
            margin-bottom: 8px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            font-size: 0.95em;
            margin-bottom: 16px;
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 12px;
            color: #8B4513;
            text-decoration: none;
            font-size: 0.95em;
        }}
        .back-link:hover {{ text-decoration: underline; }}

        .auto-notice {{
            background: #fff8e1;
            border: 1px solid #f0c040;
            border-left: 5px solid #e6a800;
            border-radius: 6px;
            padding: 10px 18px;
            margin-bottom: 14px;
            font-size: 0.92em;
            color: #5a4000;
        }}
        .auto-notice b {{ color: #7a4f00; }}

        .intro {{
            background: #eef5f5;
            padding: 12px 18px;
            border-radius: 6px;
            border-left: 4px solid #4a7878;
            margin-bottom: 16px;
            font-size: 0.93em;
        }}
        .intro b {{ color: #2e5f5f; }}
        .intro code {{
            background: #fff;
            padding: 1px 5px;
            border-radius: 3px;
            border: 1px solid #ddd;
            font-size: 0.92em;
        }}
        .intro a {{ color: #8B4513; }}

        .toolbar {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            margin: 10px 0 18px;
            padding: 10px 14px;
            background: #fff;
            border: 1px solid #d8d2bf;
            border-radius: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        .toolbar input[type=search] {{
            flex: 1;
            min-width: 220px;
            padding: 6px 10px;
            border: 1px solid #c8c0a8;
            border-radius: 4px;
            font-size: 0.95em;
            font-family: inherit;
            background: #fdfcf5;
        }}
        .toolbar button {{
            padding: 6px 12px;
            border: 1px solid #c8c0a8;
            border-radius: 4px;
            background: #fdfcf5;
            color: #5a5032;
            font-size: 0.9em;
            cursor: pointer;
            font-family: inherit;
        }}
        .toolbar button:hover {{
            background: #f0e8c8;
            border-color: #b6a978;
        }}
        .toolbar .hit-info {{
            font-size: 0.85em;
            color: #666;
            margin-left: auto;
        }}

        /* ----- 顶层分支卡片 ----- */
        .top-branch {{
            margin: 14px 0;
            border: 1px solid #d8d2bf;
            border-radius: 8px;
            background: #fff;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .top-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px;
            font-size: 1.15em;
            font-weight: bold;
            border-bottom: 1px solid #e0dcc5;
            background: #f5ead0;
            color: #5a4418;
        }}
        .top-icon {{ font-size: 1.2em; }}
        .top-lbl {{ flex: 1; }}
        .top-cnt {{
            font-size: 0.82em;
            font-weight: normal;
            color: inherit;
            opacity: 0.85;
            padding: 2px 10px;
            border-radius: 10px;
            background: rgba(255,255,255,0.55);
        }}
        .top-body {{ padding: 10px 14px 14px; }}

        /* ----- 树节点 details/summary ----- */
        details.node {{
            margin: 4px 0 4px 0;
            padding-left: 0;
        }}
        details.node > summary {{
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            list-style: none;
            font-weight: 600;
            color: #3a4a58;
            display: flex;
            align-items: center;
            gap: 8px;
            position: relative;
        }}
        details.node > summary::-webkit-details-marker {{ display: none; }}
        details.node > summary::before {{
            content: "▶";
            display: inline-block;
            width: 12px;
            font-size: 0.7em;
            color: #9aa;
            transition: transform 0.12s;
            text-align: center;
        }}
        details.node[open] > summary::before {{ transform: rotate(90deg); }}
        details.node > summary:hover {{ background: #f0ebd8; }}
        details.node .lbl {{ font-weight: 600; }}
        details.node .cnt {{
            font-size: 0.78em;
            color: #4a7878;
            font-weight: 600;
            background: #e3eded;
            padding: 1px 8px;
            border-radius: 10px;
            white-space: nowrap;
        }}
        details.node .cnt-sub {{ font-weight: 400; opacity: 0.75; }}
        details.node .cnt-direct {{
            font-size: 0.72em;
            color: #8a6020;
            background: #fff4d6;
            padding: 1px 7px;
            border-radius: 10px;
            white-space: nowrap;
        }}

        details.node.d0 > summary {{ font-size: 1.05em; }}
        details.node.d1 > summary {{ font-size: 0.97em; padding-left: 4px; }}
        details.node.d2 > summary {{ font-size: 0.92em; }}
        details.node.d3 > summary {{ font-size: 0.9em; }}

        details.node .children {{
            margin-left: 16px;
            padding-left: 10px;
            border-left: 2px dashed #d8d2bf;
        }}

        /* ----- 实例芯片 ----- */
        .inst-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 6px 0 10px 22px;
            padding: 4px 0;
        }}
        .inst {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 2px 8px 2px 10px;
            background: #fdf7e6;
            border: 1px solid #e8dcba;
            border-radius: 12px;
            font-size: 0.86em;
            color: #4a3818;
            white-space: nowrap;
        }}
        .inst-cnt {{
            font-size: 0.78em;
            color: #a87c20;
            background: #fff;
            padding: 0 6px;
            border-radius: 8px;
            border: 1px solid #e0d4a0;
        }}

        /* ----- 搜索高亮 ----- */
        .inst.match {{
            background: #fff3b8;
            border-color: #d4a020;
            box-shadow: 0 0 0 2px #f4d882;
        }}
        details.node.match > summary .lbl {{
            background: #fff3b8;
            padding: 0 4px;
            border-radius: 2px;
        }}
        details.node.dimmed > summary {{ opacity: 0.35; }}
        .inst.dimmed {{ opacity: 0.35; }}

        /* ----- 分支配色 ----- */
        {br_css_s}

        .footer {{
            margin-top: 30px;
            padding-top: 14px;
            border-top: 1px solid #e0dcc5;
            color: #888;
            font-size: 0.85em;
        }}
        .footer code {{
            background: #fff;
            padding: 1px 5px;
            border-radius: 3px;
            border: 1px solid #ddd;
        }}
"""


JS_BLOCK = r"""
        (() => {
            const search = document.getElementById('search');
            const hitInfo = document.getElementById('hit-info');
            const btnExpand = document.getElementById('btn-expand');
            const btnCollapse = document.getElementById('btn-collapse');
            const btnReset = document.getElementById('btn-reset');
            const nodes = document.querySelectorAll('details.node');
            const insts = document.querySelectorAll('.inst');

            function clearMarks() {
                document.querySelectorAll('.match, .dimmed').forEach(el => {
                    el.classList.remove('match', 'dimmed');
                });
            }

            function doSearch(q) {
                clearMarks();
                q = (q || '').trim();
                if (!q) {
                    hitInfo.textContent = '';
                    return;
                }
                const terms = q.split(/\s+/).filter(Boolean);
                let classHits = 0, instHits = 0;

                nodes.forEach(n => {
                    const label = n.getAttribute('data-label') || '';
                    if (terms.every(t => label.includes(t))) {
                        n.classList.add('match');
                        classHits++;
                        // 向上打开所有祖先
                        let p = n.parentElement;
                        while (p) {
                            if (p.tagName === 'DETAILS') p.open = true;
                            p = p.parentElement;
                        }
                        n.open = true;
                    }
                });

                insts.forEach(i => {
                    const name = i.getAttribute('data-name') || '';
                    if (terms.every(t => name.includes(t))) {
                        i.classList.add('match');
                        instHits++;
                        let p = i.parentElement;
                        while (p) {
                            if (p.tagName === 'DETAILS') p.open = true;
                            p = p.parentElement;
                        }
                    }
                });

                hitInfo.textContent = `类 ${classHits} · 人 ${instHits}`;
            }

            let timer = null;
            search.addEventListener('input', e => {
                clearTimeout(timer);
                timer = setTimeout(() => doSearch(e.target.value), 160);
            });

            btnExpand.addEventListener('click', () => {
                nodes.forEach(n => { n.open = true; });
            });
            btnCollapse.addEventListener('click', () => {
                nodes.forEach(n => {
                    // 保留顶层分支的直接子类展开状态？一律折叠更干净
                    n.open = false;
                });
            });
            btnReset.addEventListener('click', () => {
                search.value = '';
                clearMarks();
                hitInfo.textContent = '';
                nodes.forEach(n => {
                    const d = parseInt(n.className.match(/\bd(\d)\b/)?.[1] || '0', 10);
                    n.open = d < 2;
                });
            });
        })();
"""


def build_html(tree_html: str, stats: dict) -> str:
    today = date.today().isoformat()
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>人物分类树 - 史记知识库</title>
    <style>{build_css()}</style>
</head>
<body>
    <a href="index.html" class="back-link">← 返回知识图谱</a>
    <h1>👤 人物分类树</h1>
    <div class="subtitle">
        Person Taxonomy — {stats['classes']} 类 · {stats['instances']} 人 · 数据源 <code>kg/taxonomy/person.ttl</code>
    </div>

    <div class="auto-notice">
        ⚠️ <b>本页面由 AI Agent 自动生成</b>，存在大量已知缺陷与错误（分类偏差、别名混淆、人物误标等），将通过持续反思循环逐步纠正，不代表最终结果。
    </div>

    <div class="intro">
        《史记》<b>person 实体分类树</b>，按"<b>王室 · 臣 · 策士 · 诸子百家 · 社会人物 · 方术 · 外邦 · 虚构人物 · 疑似误标</b>"9 大分支组织，每类附子树实例数（<span class="cnt" style="margin:0 2px;">N 人</span>）与本类直接实例数（<span class="cnt-direct">直 N</span>）。叶节点展示人物芯片（数字 = 全文出现次数）。
        <br>
        另见：SKILL_03j 的<a href="../entities/person.html">扁平 16 类人名索引</a>。
    </div>

    <div class="toolbar">
        <input id="search" type="search" placeholder="🔍 搜索类别或人名（空格分隔多关键字）" autocomplete="off" spellcheck="false">
        <button id="btn-expand" type="button">展开全部</button>
        <button id="btn-collapse" type="button">全部折叠</button>
        <button id="btn-reset" type="button">重置</button>
        <span id="hit-info" class="hit-info"></span>
    </div>

    <div class="tree-root">
        {tree_html}
    </div>

    <div class="footer">
        数据源：<code>kg/taxonomy/person.ttl</code>（{stats['classes']} 类 · {stats['instances']} 人） ·
        生成脚本：<code>kg/taxonomy/scripts/build_person_tree_html.py</code> ·
        最后更新：{today}
        <br>
        规则文档：<code>skills/SKILL_03j_人名分类.md</code> ·
        Markdown 版：<code>kg/taxonomy/person_taxonomy.md</code>
    </div>

    <script>{JS_BLOCK}</script>
</body>
</html>
"""


def main() -> None:
    text = TTL.read_text(encoding="utf-8")
    classes, parent, label_map, instances, order_map = parse_ttl(text)

    # 根：人物（无 parent 或 parent 不在 classes 中）
    roots = [cid for cid in classes if parent.get(cid) is None]
    if "人物" in classes:
        root = "人物"
    elif roots:
        root = roots[0]
    else:
        raise SystemExit("no root class found")

    children = build_children(parent)
    totals = compute_totals(root, children, instances)

    tree_html = render_top_branches(root, label_map, children, instances, totals, order_map)

    stats = {
        "classes": len(classes),
        "instances": sum(len(v) for v in instances.values()),
    }

    out = build_html(tree_html, stats)
    OUT.write_text(out, encoding="utf-8")
    print(f"✓ wrote {OUT}")
    print(f"  classes   = {stats['classes']}")
    print(f"  instances = {stats['instances']}")
    print(f"  root '{label_map[root]}' subtree total = {totals[root]}")
    top_branches = sorted(children.get(root, []), key=lambda c: -totals[c])
    for c in top_branches:
        print(f"    {label_map[c]:8s} {totals[c]:4d} 人")


if __name__ == "__main__":
    main()
