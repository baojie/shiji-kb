#!/usr/bin/env python3
"""
姓氏数据导入（append-only）

两项操作：
1. 为人物 wiki 页面追加 xing / shi / ming / zi frontmatter 字段
   （仅在字段缺失时写入，不覆盖已有值）
2. 为缺失的 {xing}姓.md 页面创建 xing 类型页面
   - 优先使用 xing_index.json 的详细数据
   - 其余使用 person_xingshi.json 的统计数据

数据来源：
  kg/entities/data/xing_index.json        — 11 大姓详细数据
  kg/entities/data/person_xingshi.json    — 2095 人的姓氏推理表

用法:
    python wiki/scripts/import_xingshi.py [--dry-run]
    python wiki/scripts/import_xingshi.py --dry-run --min-persons 5
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT      = Path(__file__).resolve().parents[2]
PAGES_DIR = ROOT / "wiki/public/pages"
KG_DIR    = ROOT / "kg"


# ── frontmatter 工具 ──────────────────────────────────────────────────────────

def yaml_str(s: str) -> str:
    if not s:
        return '""'
    if any(c in s for c in ':#[]{},&*!|>%@`"'):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def read_frontmatter_fields(text: str) -> set[str]:
    """返回 frontmatter 中已有的字段名集合。"""
    end = text.find("---", 3)
    if end < 0:
        return set()
    fm = text[3:end]
    return {m.group(1) for m in re.finditer(r"^(\w+):", fm, re.M)}


def insert_fields_after(text: str, after_key: str, new_fields: dict[str, str]) -> str:
    """在 frontmatter 中 after_key 所在行之后插入新字段（append-only）。"""
    end = text.find("---", 3)
    if end < 0:
        return text
    fm_body = text[3:end]
    lines = fm_body.split("\n")
    insert_after_idx = -1
    for i, line in enumerate(lines):
        if line.startswith(after_key + ":"):
            insert_after_idx = i
            break
    if insert_after_idx < 0:
        # 没找到 after_key，追加在 frontmatter 最后一个非空行之后
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                insert_after_idx = i
                break
    new_lines = [f"{k}: {v}" for k, v in new_fields.items()]
    lines = lines[:insert_after_idx + 1] + new_lines + lines[insert_after_idx + 1:]
    return "---" + "\n".join(lines) + text[end:]


# ── 人物页 xing/shi 注入 ──────────────────────────────────────────────────────

def inject_person_xingshi(
    person_data: dict,   # {name: {xing, shi, ming, zi, confidence, ...}}
    dry_run: bool,
) -> tuple[int, int]:
    """为已有人物页面注入缺失的 xing/shi/ming/zi 字段。"""
    updated = skipped = 0
    for name, v in person_data.items():
        page = PAGES_DIR / f"{name}.md"
        if not page.exists():
            continue
        text = page.read_text(encoding="utf-8")

        # 只处理 type: person 的页面
        if not re.search(r"^type:\s*person", text, re.M):
            continue

        existing = read_frontmatter_fields(text)
        new_fields: dict[str, str] = {}

        for field in ("xing", "shi", "ming", "zi"):
            val = v.get(field)
            if val and field not in existing:
                new_fields[field] = yaml_str(val)

        if not new_fields:
            skipped += 1
            continue

        new_text = insert_fields_after(text, "canonical_name", new_fields)
        if dry_run:
            print(f"  [PERSON] {name}: +{list(new_fields.keys())}")
        else:
            page.write_text(new_text, encoding="utf-8")
            print(f"  [PERSON] {name}: +{list(new_fields.keys())}")
        updated += 1

    return updated, skipped


# ── {xing}姓.md 页面生成 ──────────────────────────────────────────────────────

def persons_of_xing(xing: str, person_data: dict) -> list[str]:
    return [name for name, v in person_data.items() if v.get("xing") == xing]


def create_xing_page_full(xing: str, info: dict, person_data: dict) -> str:
    """使用 xing_index 详细数据生成完整 xing 页面。"""
    origin   = info.get("origin", "")
    ancestor = info.get("ancestor", "")
    states   = info.get("major_states", [])
    derived  = info.get("derived_shi", [])
    persons  = persons_of_xing(xing, person_data)

    state_links  = "、".join(f"[[{s}]]" for s in states)  if states  else "（待考）"
    derived_links = "、".join(f"[[{d}]]" for d in derived) if derived else "（待考）"

    persons_section = ""
    if persons:
        persons_section = (
            "\n## 史记中的人物\n\n"
            + "、".join(f"[[{p}]]" for p in sorted(persons)[:30])
            + (f"等共 {len(persons)} 人" if len(persons) > 30 else f"（共 {len(persons)} 人）")
            + "\n"
        )

    fm_lines = [
        "---",
        f"id: {xing}姓",
        "type: xing",
        f"label: {xing}姓",
        f'aliases: ["{xing}"]',
        f'tags: ["姓氏", "先秦", "{xing}"]',
        f"ancestor: {yaml_str(ancestor)}",
        f"description: {yaml_str(origin)}",
        "quality: basic",
        "auto_generated: true",
        "---",
    ]

    body = [
        f"# {xing}姓",
        "",
        f"**起源**：{origin}",
        "",
        f"**祖先**：[[{ancestor}]]" if ancestor else "",
        "",
        "## 主要封国",
        "",
        state_links,
        "",
        "## 衍生氏族",
        "",
        derived_links,
        "",
    ]
    if persons_section:
        body.append(persons_section)
    body.append("## 相关页面\n")

    return "\n".join(fm_lines) + "\n" + "\n".join(b for b in body)


def create_xing_page_stub(xing: str, person_data: dict) -> str:
    """为无 xing_index 记录的姓生成简单 stub 页面。"""
    persons = persons_of_xing(xing, person_data)
    cnt = len(persons)
    persons_links = "、".join(f"[[{p}]]" for p in sorted(persons)[:30])
    if cnt > 30:
        persons_links += f"等共 {cnt} 人"

    fm_lines = [
        "---",
        f"id: {xing}姓",
        "type: xing",
        f"label: {xing}姓",
        f'aliases: ["{xing}"]',
        f'tags: ["姓氏", "{xing}"]',
        f'description: "《史记》中使用此姓的人物共 {cnt} 位"',
        "quality: stub",
        "auto_generated: true",
        "---",
    ]

    body = [
        f"# {xing}姓",
        "",
        f"《史记》中使用 **{xing}** 姓的人物共 **{cnt}** 位。",
        "",
        "## 史记中的人物",
        "",
        persons_links,
        "",
        "## 相关页面",
        "",
    ]
    return "\n".join(fm_lines) + "\n" + "\n".join(body)


def build_xing_pages(
    xing_index: dict,
    person_data: dict,
    min_persons: int,
    dry_run: bool,
) -> int:
    """为缺失的 {xing}姓.md 创建页面。"""
    created = 0
    xings_full  = xing_index.get("xings", {})

    # 1. xing_index 中的大姓（详细数据）
    for xing, info in xings_full.items():
        page = PAGES_DIR / f"{xing}姓.md"
        if page.exists():
            continue
        content = create_xing_page_full(xing, info, person_data)
        if dry_run:
            print(f"  [NEW xing-full] {xing}姓  ({len(persons_of_xing(xing, person_data))}人)")
        else:
            page.write_text(content, encoding="utf-8")
            print(f"  [NEW xing-full] {xing}姓  ({len(persons_of_xing(xing, person_data))}人)")
        created += 1

    # 2. 其余高频姓（stub）
    # 统计所有姓的人物数
    xing_count: dict[str, int] = defaultdict(int)
    for v in person_data.values():
        if v.get("xing"):
            xing_count[v["xing"]] += 1

    for xing, cnt in sorted(xing_count.items(), key=lambda x: -x[1]):
        if xing in xings_full:
            continue  # 已在上面处理
        if cnt < min_persons:
            continue
        page = PAGES_DIR / f"{xing}姓.md"
        if page.exists():
            continue
        content = create_xing_page_stub(xing, person_data)
        if dry_run:
            print(f"  [NEW xing-stub] {xing}姓  ({cnt}人)")
        else:
            page.write_text(content, encoding="utf-8")
            print(f"  [NEW xing-stub] {xing}姓  ({cnt}人)")
        created += 1

    return created


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="姓氏数据导入（append-only）")
    parser.add_argument("--dry-run",     action="store_true")
    parser.add_argument("--min-persons", type=int, default=3,
                        help="stub xing 页面的最低人物数（默认 3）")
    args = parser.parse_args()

    print("加载数据…")
    with open(KG_DIR / "entities/data/xing_index.json", encoding="utf-8") as f:
        xing_index = json.load(f)
    with open(KG_DIR / "entities/data/person_xingshi.json", encoding="utf-8") as f:
        person_data = json.load(f)["persons"]

    print(f"  person_xingshi: {len(person_data)} 人")
    print(f"  xing_index: {len(xing_index['xings'])} 大姓")
    print()

    # ── 1. 注入人物 xing/shi ────────────────────────────────────────────────
    print("── 注入人物 frontmatter xing/shi/ming/zi ──")
    updated, skipped = inject_person_xingshi(person_data, args.dry_run)
    print(f"  完成：更新 {updated} 人，已有字段跳过 {skipped} 人\n")

    # ── 2. 创建 {xing}姓.md 页面 ────────────────────────────────────────────
    print(f"── 创建 {{xing}}姓.md 页面（min_persons={args.min_persons}）──")
    created = build_xing_pages(xing_index, person_data, args.min_persons, args.dry_run)
    print(f"  完成：新建 {created} 个 xing 页面\n")

    if args.dry_run:
        print("(dry-run 模式，未写入任何文件)")


if __name__ == "__main__":
    main()
