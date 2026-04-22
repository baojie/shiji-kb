#!/usr/bin/env python3
"""
史记 Wiki v0 HTML 渲染器（单页版）

用法:
    python wiki/scripts/render_html.py <input.md> [<input.md> ...]
    python wiki/scripts/render_html.py wiki/public/pages/*.md

功能:
    1. 解析 YAML frontmatter
    2. 预处理 wikilink [[id]] / [[id|text]] → <a class="wikilink ...">
    3. Markdown → HTML (markdown-it-py)
    4. 套用最简 HTML 模板 + 内联 CSS
    5. 构建期断链检查 (扫描输入 MD 集合里的 id 作为白名单)

v0 约束:
    - 不处理 :::query 指令 (v1 Minimal 非语义版不含查询)
    - 不读 kg/ 数据, 不建索引
    - 输出到输入文件同目录下的 {stem}.html
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml
from markdown_it import MarkdownIt


# ---------- Frontmatter ----------

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class Page:
    path: Path
    meta: dict
    body: str

    @property
    def id(self) -> str:
        return self.meta.get("id", "")

    @property
    def label(self) -> str:
        return self.meta.get("label", self.path.stem)

    @property
    def aliases(self) -> list[str]:
        return self.meta.get("aliases") or []


def load_page(path: Path) -> Page:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return Page(path=path, meta={}, body=text)
    meta = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]
    return Page(path=path, meta=meta, body=body)


# ---------- Wikilink registry ----------

def build_registry(pages: list[Page]) -> dict[str, Page]:
    """
    构建 label/alias/id → Page 的查找表。
    冲突时首次命中优先, 次次命中进入警告列表由调用方打印。
    """
    reg: dict[str, Page] = {}
    conflicts: list[tuple[str, Page, Page]] = []
    for p in pages:
        keys = set()
        if p.id:
            keys.add(p.id)
        if p.label:
            keys.add(p.label)
        for a in p.aliases:
            keys.add(a)
        for k in keys:
            if k in reg and reg[k] is not p:
                conflicts.append((k, reg[k], p))
            else:
                reg[k] = p
    for k, first, dup in conflicts:
        print(f"[warn] wikilink key 冲突: '{k}' 已被 {first.id} 占用, "
              f"忽略 {dup.id}", file=sys.stderr)
    return reg


# ---------- Wikilink 替换 ----------

WIKILINK_RE = re.compile(r"\[\[([^\[\]|]+?)(?:\|([^\[\]]+?))?\]\]")


def resolve_wikilink(target: str, registry: dict[str, Page]) -> Page | None:
    """先按精确 id 找, 再按 label/alias 找。"""
    if target in registry:
        return registry[target]
    # 去掉可能的 type/ 前缀后按尾段再找一次
    if "/" in target:
        _, tail = target.split("/", 1)
        if tail in registry:
            return registry[tail]
    return None


# 占位符使用 Unicode 私用区字符, MD 不会转义/解读
PLACEHOLDER_OPEN = "\ue010"
PLACEHOLDER_CLOSE = "\ue011"
PLACEHOLDER_RE = re.compile(f"{PLACEHOLDER_OPEN}(\\d+){PLACEHOLDER_CLOSE}")


def protect_wikilinks(body: str) -> tuple[str, list[tuple[str, str | None]]]:
    """
    在 MD 渲染前把 [[...]] 替换为占位符, 避免表格 '|' 冲突及 MD 转义。
    返回: (替换后的 body, [(target, text|None), ...])
    """
    tokens: list[tuple[str, str | None]] = []

    def repl(m: re.Match) -> str:
        target = m.group(1).strip()
        text = m.group(2).strip() if m.group(2) else None
        tokens.append((target, text))
        return f"{PLACEHOLDER_OPEN}{len(tokens) - 1}{PLACEHOLDER_CLOSE}"

    new_body = WIKILINK_RE.sub(repl, body)
    return new_body, tokens


def expand_wikilinks(html: str, tokens: list[tuple[str, str | None]],
                     registry: dict[str, Page], self_page: Page,
                     broken: list[str]) -> str:
    """MD 渲染后把占位符替换成真实 <a> 标签。"""
    def repl(m: re.Match) -> str:
        idx = int(m.group(1))
        target, text = tokens[idx]
        display = text if text is not None else target
        # 未给显示文本且 target 含 type/slug, 只显示 slug
        if text is None and "/" in display:
            display = display.split("/", 1)[1]
        page = resolve_wikilink(target, registry)
        if page is None:
            broken.append(target)
            return (f'<a class="wikilink broken" '
                    f'data-target="{target}" '
                    f'title="未解析: {target}">{display}</a>')
        href = html_path_for(page, relative_to=self_page)
        cls = "wikilink self" if page is self_page else "wikilink resolved"
        return f'<a class="{cls}" href="{href}">{display}</a>'
    return PLACEHOLDER_RE.sub(repl, html)


def html_path_for(page: Page, relative_to: Page) -> str:
    """v0 所有页面都在同一目录, 直接输出 {stem}.html。"""
    return f"{page.path.stem}.html"


# ---------- Infobox (property table) ----------

INFOBOX_FIELDS = [
    ("label", "名称"),
    ("canonical_name", "规范名"),
    ("type", "类型"),
    ("birth_ce", "生"),
    ("death_ce", "卒"),
    ("tags", "标签"),
]


def render_infobox(page: Page) -> str:
    """
    从 frontmatter 提取可展示字段, 渲染右侧 infobox。
    缺字段自动跳过。
    """
    rows = []
    for key, label in INFOBOX_FIELDS:
        if key not in page.meta:
            continue
        v = page.meta[key]
        if v is None:
            continue
        if isinstance(v, list):
            v = " · ".join(str(x) for x in v)
        elif isinstance(v, int) and key in ("birth_ce", "death_ce"):
            v = f"前 {-v}" if v < 0 else str(v)
        rows.append(f"<tr><th>{label}</th><td>{v}</td></tr>")
    if page.aliases:
        rows.insert(1, f"<tr><th>别名</th><td>{' · '.join(page.aliases)}</td></tr>")
    if not rows:
        return ""
    return ('<aside class="infobox">'
            f'<h2>{page.label}</h2>'
            f'<table>{"".join(rows)}</table>'
            '</aside>')


# ---------- Markdown → HTML ----------

def make_md() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})
    md.enable("table")
    md.enable("strikethrough")
    return md


# ---------- HTML 模板 ----------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 史记 Wiki</title>
<style>{css}</style>
</head>
<body>
<nav class="topnav">
  <a href="index.html">史记 Wiki</a>
  <span class="crumb">{type_label} / {title}</span>
</nav>
<main class="page">
  {infobox}
  <article>
{body}
  </article>
</main>
<footer>
  <small>
    源文件: <code>{src}</code> ·
    生成时间: {generated}
    {broken_footer}
  </small>
</footer>
</body>
</html>
"""

CSS = r"""
:root {
  --fg: #1a1a1a;
  --fg-muted: #666;
  --bg: #fafaf7;
  --bg-box: #f0ece0;
  --accent: #7a1f1f;
  --link: #1a5490;
  --link-broken: #c44;
  --border: #d8d2bf;
  --serif: "Noto Serif SC", "Source Han Serif SC", "Songti SC", serif;
  --sans: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: var(--serif);
  color: var(--fg);
  background: var(--bg);
  line-height: 1.75;
  font-size: 17px;
}
.topnav {
  padding: .6em 1.2em;
  background: #fff;
  border-bottom: 1px solid var(--border);
  font-family: var(--sans);
  font-size: 14px;
}
.topnav a { color: var(--accent); text-decoration: none; font-weight: 600; }
.topnav .crumb { margin-left: 1em; color: var(--fg-muted); }

.page {
  max-width: 900px;
  margin: 2em auto;
  padding: 0 1.2em;
  display: grid;
  grid-template-columns: 1fr;
  gap: 2em;
}
@media (min-width: 900px) {
  .page { grid-template-columns: minmax(0, 1fr) 260px; }
  .page > article { grid-column: 1; grid-row: 1; }
  .page > aside.infobox { grid-column: 2; grid-row: 1; }
}

article h1 {
  font-size: 2em;
  margin-top: 0;
  padding-bottom: .3em;
  border-bottom: 2px solid var(--accent);
  color: var(--accent);
}
article h2 {
  font-size: 1.35em;
  margin-top: 1.8em;
  padding-bottom: .2em;
  border-bottom: 1px solid var(--border);
}
article h3 {
  font-size: 1.1em;
  margin-top: 1.4em;
  color: var(--accent);
}
article p { margin: .7em 0; }
article ul, article ol { padding-left: 1.4em; }
article li { margin: .3em 0; }
article blockquote {
  margin: 1em 0;
  padding: .6em 1em;
  border-left: 3px solid var(--accent);
  background: var(--bg-box);
  color: var(--fg-muted);
  font-size: .95em;
}
article table {
  border-collapse: collapse;
  margin: 1em 0;
  font-size: .93em;
}
article th, article td {
  padding: .35em .8em;
  border: 1px solid var(--border);
  text-align: left;
}
article th { background: var(--bg-box); font-weight: 600; }
article hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 2em 0;
}
article em { color: var(--fg-muted); font-style: normal; }

aside.infobox {
  background: var(--bg-box);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1em;
  font-size: .9em;
  align-self: start;
}
aside.infobox h2 {
  margin: 0 0 .6em 0;
  font-size: 1.1em;
  padding-bottom: .3em;
  border-bottom: 1px solid var(--border);
  color: var(--accent);
}
aside.infobox table { width: 100%; border: none; margin: 0; }
aside.infobox th, aside.infobox td {
  border: none;
  padding: .25em .3em;
  vertical-align: top;
  background: transparent;
}
aside.infobox th { color: var(--fg-muted); font-weight: 500; width: 4.5em; }

.wikilink.resolved { color: var(--link); text-decoration: none; }
.wikilink.resolved:hover { text-decoration: underline; }
.wikilink.self { color: var(--fg); font-weight: 600; text-decoration: none; cursor: default; }
.wikilink.broken {
  color: var(--link-broken);
  text-decoration: underline dashed;
  cursor: help;
}

footer {
  max-width: 900px;
  margin: 3em auto 2em;
  padding: 1em 1.2em;
  color: var(--fg-muted);
  font-family: var(--sans);
  font-size: 12px;
  border-top: 1px solid var(--border);
}
footer code { background: var(--bg-box); padding: 1px 4px; border-radius: 2px; }
footer .broken-list { margin-top: .6em; }
footer .broken-list summary { cursor: pointer; color: var(--link-broken); }
footer .broken-list code { color: var(--link-broken); }
"""


TYPE_LABELS = {
    "person": "人名",
    "place": "地名",
    "state": "邦国",
    "official": "官职",
    "identity": "身份",
    "dynasty": "朝代",
    "event": "事件",
    "chapter": "章节",
    "topic": "主题",
    "meta": "元页",
}


def render_page(page: Page, registry: dict[str, Page], md: MarkdownIt) -> tuple[str, list[str]]:
    broken: list[str] = []
    # 先替换 wikilink 为占位符 (避开 MD 表格 '|' 冲突与转义)
    protected, tokens = protect_wikilinks(page.body)
    body_html = md.render(protected)
    body_html = expand_wikilinks(body_html, tokens, registry, page, broken)
    infobox = render_infobox(page)
    from datetime import datetime
    broken_footer = ""
    if broken:
        uniq = sorted(set(broken))
        items = "".join(f"<code>{b}</code>" for b in uniq)
        broken_footer = (f'<details class="broken-list"><summary>'
                         f'断链 {len(uniq)} 处</summary>{items}</details>')
    html = HTML_TEMPLATE.format(
        title=page.label,
        type_label=TYPE_LABELS.get(page.meta.get("type", ""), page.meta.get("type", "")),
        css=CSS,
        infobox=infobox,
        body=body_html,
        src=page.path.as_posix(),
        generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        broken_footer=broken_footer,
    )
    return html, broken


def build_index(pages: list[Page], out_dir: Path) -> None:
    """生成一个极简 index.html 列出所有页。"""
    items = []
    for p in sorted(pages, key=lambda x: x.id):
        href = f"{p.path.stem}.html"
        t = TYPE_LABELS.get(p.meta.get("type", ""), "")
        items.append(f'<li><span class="type-tag">{t}</span> '
                     f'<a href="{href}">{p.label}</a></li>')
    body = ('<h1>史记 Wiki (v0 原型)</h1>'
            f'<p>共 {len(pages)} 页。</p>'
            f'<ul class="page-list">{"".join(items)}</ul>')
    html = HTML_TEMPLATE.format(
        title="首页",
        type_label="首页",
        css=CSS + ".page-list { list-style: none; padding: 0; }"
              ".page-list li { padding: .3em 0; }"
              ".type-tag { display: inline-block; width: 3em; padding: 1px 6px;"
              "  margin-right: .6em; font-size: .8em; background: var(--bg-box);"
              "  color: var(--fg-muted); border-radius: 3px; text-align: center;"
              "  font-family: var(--sans); }",
        infobox="",
        body=body,
        src="(生成)",
        generated=__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
        broken_footer="",
    )
    (out_dir / "index.html").write_text(html, encoding="utf-8")


# ---------- Main ----------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="输入 .md 文件")
    ap.add_argument("--out-dir", default=None,
                    help="输出目录 (默认: 输入文件同目录)")
    args = ap.parse_args()

    inputs = [Path(p) for p in args.inputs]
    missing = [p for p in inputs if not p.exists()]
    if missing:
        for p in missing:
            print(f"[error] 文件不存在: {p}", file=sys.stderr)
        return 1

    pages = [load_page(p) for p in inputs]
    registry = build_registry(pages)
    md = make_md()

    out_dir = Path(args.out_dir) if args.out_dir else inputs[0].parent
    out_dir.mkdir(parents=True, exist_ok=True)

    total_broken = 0
    for page in pages:
        html, broken = render_page(page, registry, md)
        out_path = out_dir / f"{page.path.stem}.html"
        out_path.write_text(html, encoding="utf-8")
        total_broken += len(set(broken))
        print(f"[ok] {page.path.name} → {out_path}  (断链 {len(set(broken))})")

    build_index(pages, out_dir)
    print(f"[ok] index.html → {out_dir / 'index.html'}")
    print(f"共渲染 {len(pages)} 页, 累计唯一断链 {total_broken} 个。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
