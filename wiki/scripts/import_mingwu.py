#!/usr/bin/env python3
"""
名物实体导入脚本（append-only）

两种操作：
  1. 为 entity_index 中存在但 wiki 尚无页面的实体创建新页面
  2. 为有页面但缺少「史记引文」section 的页面追加该 section

支持的实体类型：artifact, official, institution, tribe, astronomy, biology, dynasty

用法:
    python wiki/scripts/import_mingwu.py [--dry-run] [--types artifact,official,...]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
PAGES_DIR   = ROOT / "wiki/public/pages"
CHAPTER_DIR = ROOT / "chapter_md"
KG_DIR      = ROOT / "kg"

# 类型 → 中文标签
# dynasty 已废弃：其内容已被 state（邦国）和 tribe（氏族/部族）覆盖，
# entity_index 中 dynasty 条目混杂了 state/tribe/place/person 等多种实体，
# 不应作为独立类型导入。
TYPE_LABEL = {
    "artifact":    "器物",
    "official":    "官职",
    "institution": "制度",
    "tribe":       "部族",
    "astronomy":   "天文",
    "biology":     "生物",
}

ALL_TYPES = list(TYPE_LABEL.keys())

MAX_EXCERPT = 5      # 最多展示的引文条数
CONTEXT_CHARS = 100  # 实体前后各取的字符数


# ── 章节标签缓存 ──────────────────────────────────────────────────────────────

def build_chapter_label_map() -> dict[str, str]:
    """返回 {chapter_id: label}，例如 {'001_五帝本纪': '五帝本纪'}"""
    label_map = {}
    for f in PAGES_DIR.glob("[0-9]*.md"):
        m = re.search(r"^label:\s*(.+)$", f.read_text(encoding="utf-8"), re.M)
        if m:
            label_map[f.stem] = m.group(1).strip()
    return label_map


# ── 章节文本加载 ──────────────────────────────────────────────────────────────

def strip_tags(text: str) -> str:
    text = re.sub(r"〖.([^〗]+)〗", r"\1", text)
    text = re.sub(r"⟦.([^⟧]+)⟧", r"\1", text)
    text = re.sub(r"〘※([^〙]+)〙", r"\1", text)
    text = re.sub(r"^\[\d+[\.\d]*\]\s*", "", text)
    # 去除残余的日期记号 |
    text = re.sub(r"[^|]+\|", "", text)
    return text.strip()


def load_chapters() -> dict[str, dict[str, str]]:
    """返回 {ch_num: {para_id: stripped_text}}"""
    chapters: dict[str, dict[str, str]] = {}
    for f in sorted(CHAPTER_DIR.glob("*.tagged.md")):
        m = re.match(r"^(\d+)_", f.name)
        if not m:
            continue
        ch_num = m.group(1)
        paras: dict[str, str] = {}
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip()
                pm = re.match(r"^\[(\d+[\.\d]*)\]\s*(.*)", line)
                if pm:
                    paras[pm.group(1)] = strip_tags(pm.group(2))
        chapters[ch_num] = paras
    return chapters


# ── 引文提取 ──────────────────────────────────────────────────────────────────

def extract_context(text: str, entity: str, ctx: int = CONTEXT_CHARS) -> str:
    """在 text 中找到 entity，返回前后 ctx 字符，entity 加粗。"""
    pos = text.find(entity)
    if pos < 0:
        # 找不到时直接截断
        return text[:ctx * 2] + ("…" if len(text) > ctx * 2 else "")
    start = max(0, pos - ctx)
    end   = min(len(text), pos + len(entity) + ctx)
    left  = ("…" if start > 0 else "") + text[start:pos]
    right = text[pos + len(entity):end] + ("…" if end < len(text) else "")
    return left + f"**{entity}**" + right


def build_refs_section(
    entity: str,
    refs: list[list[str]],
    chapters: dict[str, dict[str, str]],
    label_map: dict[str, str],
) -> str:
    """生成「史记引文」markdown section 文本。"""
    total = len(refs)

    # 按章节分组
    by_chapter: dict[str, list[str]] = defaultdict(list)
    for ch_name, para_id in refs:
        by_chapter[ch_name].append(para_id)

    # 章节分布
    dist_lines: list[str] = []
    for ch_name, pids in by_chapter.items():
        ch_num = ch_name[:3]
        label  = label_map.get(ch_name, ch_name)
        link   = f"[[{ch_name}|{label}]]"
        pn_strs = [f"（{ch_num}-{p}）" for p in pids]
        if len(pids) > 8:
            pn_strs = pn_strs[:8] + [f"等共 {len(pids)} 处"]
        dist_lines.append(f"- {link}：{'、'.join(pn_strs)}")

    dist_block = "\n".join(dist_lines)

    # 引文摘录（至多 MAX_EXCERPT 条）
    excerpts: list[str] = []
    for ch_name, para_id in refs[:MAX_EXCERPT]:
        ch_num = ch_name[:3]
        text   = chapters.get(ch_num, {}).get(para_id, "")
        if not text:
            continue
        label = label_map.get(ch_name, ch_name)
        ctx   = extract_context(text, entity)
        pn    = f"（{ch_num}-{para_id}）"
        excerpts.append(f"> 出自 [[{ch_name}|{label}]] {pn}：{ctx}")

    excerpt_block = "\n>\n".join(excerpts)
    if len(refs) == 1:
        header = "**引文摘录：**"
    else:
        shown = min(MAX_EXCERPT, len(excerpts))
        header = f"**引文摘录（共 {total} 处，下列仅示 {shown} 条）：**" if shown < total else "**引文摘录：**"

    parts = [
        f"## 史记引文\n",
        f"《史记》中出现 **{total}** 处。\n",
        "**章节分布：**\n",
        dist_block + "\n",
        header + "\n",
        excerpt_block,
    ]
    return "\n".join(parts)


def build_related_chapters(refs: list[list[str]], label_map: dict[str, str]) -> str:
    seen = []
    for ch_name, _ in refs:
        label = label_map.get(ch_name, ch_name)
        entry = f"[[{ch_name}|{label}]]"
        if ch_name not in [x[0] for x in refs[:refs.index([ch_name, _])]]:
            seen.append(entry)
    # deduplicate preserving order
    deduped = list(dict.fromkeys(seen))
    return "## 相关章节\n\n" + "\n".join(f"- {e}" for e in deduped)


# ── 新页面生成 ────────────────────────────────────────────────────────────────

def yaml_str(s: str) -> str:
    if any(c in s for c in ':#[]{},&*!|>%@`"'):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def create_page(
    entity: str,
    etype: str,
    refs: list[list[str]],
    chapters: dict[str, dict[str, str]],
    label_map: dict[str, str],
) -> str:
    total = len(refs)
    chinese_type = TYPE_LABEL.get(etype, etype)

    # sources 列表（去重，取章节 label）
    sources = list(dict.fromkeys(
        label_map.get(ch, ch) for ch, _ in refs
    ))
    sources_yaml = "[" + ", ".join(yaml_str(s) for s in sources[:6]) + "]"

    desc = f"《史记》中的{chinese_type}，出现于《史记》{total}处"

    fm_lines = [
        "---",
        f"id: {yaml_str(entity)}",
        f"type: {etype}",
        f"label: {yaml_str(entity)}",
        "aliases: []",
        f"canonical_name: {yaml_str(entity)}",
        f'tags: ["{chinese_type}"]',
        f'description: {yaml_str(desc)}',
        f"sources: {sources_yaml}",
        "quality: basic",
        "auto_generated: true",
        "---",
    ]
    frontmatter = "\n".join(fm_lines)

    refs_section    = build_refs_section(entity, refs, chapters, label_map)
    related_section = build_related_chapters(refs, label_map)

    return "\n".join([
        frontmatter,
        f"# {entity}",
        "",
        f"出现于《史记》**{total}** 处。",
        "",
        refs_section,
        "",
        related_section,
        "",
    ])


# ── 主逻辑 ───────────────────────────────────────────────────────────────────

def run(types: list[str], dry_run: bool) -> None:
    print("加载章节文本…")
    chapters = load_chapters()
    print(f"  已加载 {len(chapters)} 章")

    print("加载章节标签…")
    label_map = build_chapter_label_map()

    print("加载实体索引…")
    with open(KG_DIR / "entity_index.json", encoding="utf-8") as f:
        entity_index = json.load(f)

    created = appended = skipped = 0

    for etype in types:
        entities = entity_index.get(etype, {})
        print(f"\n── {etype}（{TYPE_LABEL[etype]}）：{len(entities)} 条 ──")

        for entity, v in entities.items():
            refs = v.get("refs", [])
            if not refs:
                continue
            # 过滤噪声：名字太短或出现次数太少的跳过
            if len(entity) < 2:
                continue
            count = v.get("count", len(refs))
            if count < 2 and len(entity) <= 3:
                continue
            page_path = PAGES_DIR / f"{entity}.md"

            if not page_path.exists():
                # 新建页面
                content = create_page(entity, etype, refs, chapters, label_map)
                if dry_run:
                    print(f"  [NEW]  {entity}")
                else:
                    page_path.write_text(content, encoding="utf-8")
                    print(f"  [NEW]  {entity}")
                created += 1

            else:
                # 已有页面 → 检查是否缺「史记引文」
                existing = page_path.read_text(encoding="utf-8")
                if "史记引文" in existing:
                    skipped += 1
                    continue

                # 追加 section（append-only）
                refs_section = build_refs_section(entity, refs, chapters, label_map)
                append_text  = "\n\n" + refs_section + "\n"
                if dry_run:
                    print(f"  [APPEND] {entity}")
                else:
                    with open(page_path, "a", encoding="utf-8") as fh:
                        fh.write(append_text)
                    print(f"  [APPEND] {entity}")
                appended += 1

    print(f"\n完成：新建 {created} 页，追加引文 {appended} 页，已有引文跳过 {skipped} 条")
    if dry_run:
        print("(dry-run 模式，未写入任何文件)")


def main():
    parser = argparse.ArgumentParser(description="名物实体导入（append-only）")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    parser.add_argument(
        "--types",
        default=",".join(ALL_TYPES),
        help=f"逗号分隔的类型列表，默认全部: {','.join(ALL_TYPES)}"
    )
    args = parser.parse_args()
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    run(types, args.dry_run)


if __name__ == "__main__":
    main()
