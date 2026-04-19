#!/usr/bin/env python3
"""
向 docs/kg/person_tree.html 注入最新的人物分类计数（来自 person_categories.json）。

读取：
  kg/entities/data/person_categories.json     — {canonical: [cat,cat,...]}（主标在前）
  kg/entities/data/entity_index.json          — person 条目与出现次数
  docs/kg/person_tree.html                    — 现有模板（手写）

写入：
  docs/kg/person_tree.html                    — 原地更新

更新点：
  1. 每个 .cat-header 追加 <span class="count">(N 人)</span>（主标数）+ 任一标签数
  2. 顶层 branch（I-V / 元数据）追加合计
  3. root 行显示已分类总数
  4. intro 更新"尚未生成"提示为最新规模
  5. footer 标明重生脚本与数据来源

使用：
  python kg/taxonomy/scripts/rebuild_person_tree_html.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATEGORIES = ROOT / "kg" / "entities" / "data" / "person_categories.json"
INDEX = ROOT / "kg" / "entities" / "data" / "entity_index.json"
HTML = ROOT / "docs" / "kg" / "person_tree.html"


CSS_KEY_TO_CAT = {
    "cat-emperor": "帝王",
    "cat-ruler": "诸侯君主",
    "cat-consort": "后妃",
    "cat-prince": "宗室",
    "cat-chancellor": "将相",
    "cat-strategist": "谋臣策士",
    "cat-scholar": "学者文士",
    "cat-local": "地方官",
    "cat-swordsman": "刺客游侠",
    "cat-courtier": "近臣奇人",
    "cat-merchant": "货殖",
    "cat-foreign": "外邦",
    "cat-mythical": "上古神话",
    "cat-retainer": "家臣门客",
    "cat-commoner": "平民刑徒",
    "cat-mis": "误标",
    "cat-split": "待拆分",
    "cat-fictional": "虚构寓言",
}

# 顶层分组（I-V + 元数据）→ CSS 类列表
GROUPS = {
    "I. 君主与宗室": ["cat-emperor", "cat-ruler", "cat-consort", "cat-prince"],
    "II. 官僚与文人": ["cat-chancellor", "cat-strategist", "cat-scholar", "cat-local"],
    "III. 江湖与近臣": ["cat-swordsman", "cat-courtier", "cat-merchant"],
    "IV. 边陲与神话": ["cat-foreign", "cat-mythical"],
    "V. 底层与随从": ["cat-retainer", "cat-commoner"],
}


def load_counts() -> tuple[dict[str, int], dict[str, int], int]:
    """返回 (primary_count, any_count, total_classified)"""
    data = json.loads(CATEGORIES.read_text(encoding="utf-8"))
    primary: Counter[str] = Counter()
    any_label: Counter[str] = Counter()
    total = 0
    for _name, cats in data.items():
        if not cats:
            continue
        total += 1
        primary[cats[0]] += 1
        for c in cats:
            any_label[c] += 1
    return dict(primary), dict(any_label), total


def inject_cat_counts(html: str, primary: dict[str, int], any_label: dict[str, int]) -> str:
    """在每个 <span class="cat-key">cat-X</span> 后追加计数 span。

    格式：<span class="count">(主标 N · 任一 M)</span>
    若存量已有该追加（重跑场景），先剔除再重注入。
    """
    pattern = re.compile(
        r'(<span class="cat-key">(cat-[a-z]+)</span>)'
        r'(\s*<span class="count cat-count">[^<]*</span>)?'
    )

    def repl(m: re.Match) -> str:
        cat_key_span = m.group(1)
        css = m.group(2)
        cat = CSS_KEY_TO_CAT.get(css)
        if cat is None:
            return m.group(0)
        p = primary.get(cat, 0)
        a = any_label.get(cat, 0)
        extra = a - p
        if extra > 0:
            inner = f"主标 {p} · 共 {a} 人"
        else:
            inner = f"{p} 人" if p > 0 else "0"
        return f'{cat_key_span} <span class="count cat-count">({inner})</span>'

    return pattern.sub(repl, html)


def inject_branch_counts(html: str, primary: dict[str, int]) -> str:
    """更新顶层 branch 行，追加分组合计。"""
    def sum_group(keys: list[str]) -> int:
        return sum(primary.get(CSS_KEY_TO_CAT[k], 0) for k in keys)

    for label, keys in GROUPS.items():
        total = sum_group(keys)
        # 匹配 <div class="branch">I. 君主与宗室 <span class="count">(priority 1–4)</span></div>
        pattern = re.compile(
            r'(<div class="branch">' + re.escape(label) + r' <span class="count">\(priority [^<]+\)</span>)'
            r'(\s*<span class="count branch-count">[^<]*</span>)?'
            r'(\s*</div>)'
        )
        html = pattern.sub(
            lambda m, t=total: f'{m.group(1)} <span class="count branch-count">· {t} 人</span>{m.group(3)}',
            html,
            count=1,
        )
    return html


def inject_root(html: str, total: int) -> str:
    pattern = re.compile(
        r'(<div class="root">🌳 《史记》人物身份分类 \(16 主类 \+ 3 元数据类\))'
        r'(\s*<span class="count root-count">[^<]*</span>)?'
        r'(</div>)'
    )
    return pattern.sub(
        lambda m: f'{m.group(1)} <span class="count root-count">· 已分类 {total} 人</span>{m.group(3)}',
        html,
        count=1,
    )


def inject_intro_and_footer(html: str, total: int, primary: dict[str, int]) -> str:
    today = date.today().isoformat()
    sorted_cats = sorted(primary.items(), key=lambda x: -x[1])[:5]
    top5 = "、".join(f"{c}（{n}）" for c, n in sorted_cats)

    # intro 替换"尚未生成"这句
    new_intro_tail = (
        f'<br><br>'
        f'最新数据（{today}）：已分类 <b>{total}</b> 人，覆盖 <code>person_categories.json</code>。'
        f'前 5 大类：{top5}。'
        f'在<a href="../entities/person.html" style="color:#8B4513;">人名索引</a>可按类筛选实例。'
    )
    html = re.sub(
        r'<br><br>\s*人物实例数据 <code>person_categories\.json</code> 尚未生成；待 <code>classify_persons\.py</code> 跑通后，将在<a[^>]*>人名索引</a>按类筛选实例。',
        new_intro_tail,
        html,
        count=1,
    )
    # 若已是新版（重跑场景），再替换一次（保持内容最新）
    html = re.sub(
        r'<br><br>\s*最新数据（\d{4}-\d{2}-\d{2}）：已分类 <b>\d+</b> 人，覆盖 <code>person_categories\.json</code>。前 5 大类：[^<]+。在<a[^>]*>人名索引</a>可按类筛选实例。',
        new_intro_tail,
        html,
        count=1,
    )

    # footer
    new_footer = (
        f'规则来源：<code>skills/SKILL_03j_人名分类.md §一</code> · '
        f'实现：<code>kg/entities/scripts/classify_persons.py</code> · '
        f'维护：<code>skills/SKILL_06e_分类树总结.md</code> · '
        f'CSS：<code>docs/css/entity-index.css</code> 的 <code>.cat-*</code> 系列'
        f'<br>'
        f'数据：<code>kg/entities/data/person_categories.json</code>（{total} 人已分类） · '
        f'重生脚本：<code>kg/taxonomy/scripts/rebuild_person_tree_html.py</code> · '
        f'最后更新：{today}'
    )
    html = re.sub(
        r'规则来源：<code>skills/SKILL_03j_人名分类\.md §一</code> ·[\s\S]*?人物实例数据 <code>kg/entities/data/person_categories\.json</code> 尚未生成。',
        new_footer,
        html,
        count=1,
    )
    html = re.sub(
        r'规则来源：<code>skills/SKILL_03j_人名分类\.md §一</code> ·[\s\S]*?最后更新：\d{4}-\d{2}-\d{2}',
        new_footer,
        html,
        count=1,
    )
    return html


def inject_count_styles(html: str) -> str:
    """确保 .cat-count / .branch-count / .root-count 的 CSS 存在。"""
    if ".cat-count {" in html:
        return html
    block = """
        .cat-count {
            margin-left: 6px;
            font-size: 0.82em;
            color: #2e5f5f;
            font-weight: 600;
        }
        .branch-count {
            margin-left: 4px;
            font-size: 0.85em;
            color: #4a7878;
            font-weight: 600;
        }
        .root-count {
            margin-left: 8px;
            font-size: 0.7em;
            font-weight: 500;
            color: #4a7878;
        }
"""
    # 插入到 .branch .count 块之后
    anchor = ".branch .count {"
    pos = html.find(anchor)
    if pos < 0:
        return html
    close = html.find("}", pos)
    if close < 0:
        return html
    return html[:close + 1] + block + html[close + 1:]


def main() -> None:
    primary, any_label, total = load_counts()
    html = HTML.read_text(encoding="utf-8")

    html = inject_count_styles(html)
    html = inject_cat_counts(html, primary, any_label)
    html = inject_branch_counts(html, primary)
    html = inject_root(html, total)
    html = inject_intro_and_footer(html, total, primary)

    HTML.write_text(html, encoding="utf-8")
    print(f"updated: {HTML}")
    print(f"  total classified: {total}")
    print(f"  top categories: {sorted(primary.items(), key=lambda x: -x[1])[:5]}")


if __name__ == "__main__":
    main()
