#!/usr/bin/env python3
"""
find_unlinked_entities.py — 扫描 wiki 页面正文，找出现了实体名但未加 [[]] 的位置。

输出：哪些页面含有最多"未链接实体"，优先处理高频实体、高质量页面。

用法:
    python3 wiki/scripts/butler/find_unlinked_entities.py
    python3 wiki/scripts/butler/find_unlinked_entities.py --max-pages 10 --max-entities 5
    python3 wiki/scripts/butler/find_unlinked_entities.py --write-queue   # 写入 housekeeping_queue.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGES_DIR = ROOT / "wiki/public/pages"
PAGES_JSON = ROOT / "wiki/public/pages.json"
QUEUE_FILE = ROOT / "wiki/logs/butler/housekeeping_queue.md"

# 类型过滤：只把这些类型的页面当作"实体"候选
ENTITY_TYPES = {"person", "place", "state", "concept"}

# 名字长度限制：太短（≤1字）容易误匹配，太长（>8字）通常不是裸名
MIN_NAME_LEN = 2
MAX_NAME_LEN = 8

# 质量权重：优先扫描这些质量的页面（作为"被扫描的宿主页"）
HOST_PRIORITY = {"featured": 3, "premium": 3, "standard": 2, "basic": 1, "stub": 0}


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("---", 3)
        return text[end + 3:] if end > 0 else text
    return text


def remove_wikilinks(text: str) -> str:
    """把 [[target|display]] 和 [[target]] 替换为 display/target，避免误判已链接的词。"""
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    return text


def build_entity_index(pages_data: dict) -> dict[str, dict]:
    """从 pages.json 提取所有有效实体名 → 元信息。"""
    entities = {}
    for name, info in pages_data["pages"].items():
        if info.get("type") not in ENTITY_TYPES:
            continue
        if not (MIN_NAME_LEN <= len(name) <= MAX_NAME_LEN):
            continue
        if "（" in name or name[0].isdigit():
            continue
        entities[name] = info
    return entities


def count_unlinked(body: str, entity_names: list[str], page_name: str,
                   entity_set: set[str]) -> list[tuple[str, int]]:
    """
    在 body 中找出哪些实体名出现了但未被 [[]] 包裹。
    返回 [(entity_name, count), ...] 按 count 降序。

    关键：避免子串误匹配——若「公孙」出现的地方紧跟的字形成更长的已知实体名
    （如「公孙弘」），则不计入未链接。
    """
    # 先把正文中已有链接的部分替换掉，避免干扰
    # 构建"已链接词"集合：[[X]] 或 [[X|Y]] 中的 X
    linked_targets = set(re.findall(r"\[\[([^\]|]+)", body))

    results = []
    for name in entity_names:
        if name == page_name:
            continue
        # 如果已经有链接，跳过
        if (f"[[{name}]]" in body or f"[[{name}|" in body or f"|{name}]]" in body):
            continue

        # 找出所有裸名出现位置
        count = 0
        for m in re.finditer(re.escape(name), body):
            start, end = m.start(), m.end()
            # 检查上下文：该出现是否在 [[ ]] 内
            before = body[max(0, start - 2):start]
            after = body[end:end + 1]
            if "[[" in before:
                continue  # 在链接内部
            # 检查是否是更长已知实体的子串
            # 向后扩展：name + 后续1-3字是否是已知实体
            is_substring = False
            for extra_len in range(1, 4):
                extended = body[start:end + extra_len]
                if extended in entity_set:
                    is_substring = True
                    break
            # 向前扩展：前1-2字 + name 是否是已知实体
            if not is_substring:
                for prefix_len in range(1, 3):
                    extended = body[max(0, start - prefix_len):end]
                    if extended in entity_set:
                        is_substring = True
                        break
            if not is_substring:
                count += 1

        if count > 0:
            results.append((name, count))

    results.sort(key=lambda x: -x[1])
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-pages", type=int, default=8,
                    help="最多报告几个宿主页（默认8）")
    ap.add_argument("--max-entities", type=int, default=5,
                    help="每个宿主页最多报告几个未链实体（默认5）")
    ap.add_argument("--min-entity-refs", type=int, default=3,
                    help="实体被引用次数的最低门槛，低于此跳过（默认3）")
    ap.add_argument("--host-types", nargs="+",
                    default=list(ENTITY_TYPES) + ["chapter", "overview", "event", "story"],
                    help="宿主页类型（被扫描的页面类型）")
    ap.add_argument("--write-queue", action="store_true",
                    help="将结果追加写入 housekeeping_queue.md（P1 区段）")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印，不写队列（搭配 --write-queue 使用）")
    args = ap.parse_args()

    if not PAGES_JSON.exists():
        print(f"✗ {PAGES_JSON} 不存在", file=sys.stderr)
        return 1

    pages_data = json.loads(PAGES_JSON.read_text(encoding="utf-8"))
    entity_index = build_entity_index(pages_data)

    # 全量实体名集合（用于子串检测）
    entity_set_all = set(entity_index.keys())

    # 按引用数过滤：低引用的实体不值得主动链接
    entity_names_filtered = [
        name for name, info in entity_index.items()
        if info.get("quality") not in ("stub",)  # stub 页本身内容少，链过去意义不大
    ]

    # 收集宿主页（被扫描对象）：按质量优先级排序
    host_pages = []
    for md_file in sorted(PAGES_DIR.glob("*.md")):
        name = md_file.stem
        info = pages_data["pages"].get(name, {})
        ptype = info.get("type", "")
        quality = info.get("quality", "basic")
        if ptype not in args.host_types:
            continue
        priority = HOST_PRIORITY.get(quality, 1)
        host_pages.append((priority, name, md_file, info))

    host_pages.sort(key=lambda x: -x[0])

    today = date.today().isoformat()
    found: list[tuple[str, list[tuple[str, int]], str]] = []  # (page, entities, quality)

    for priority, name, md_file, info in host_pages:
        if len(found) >= args.max_pages * 3:  # 多扫一些，再筛
            break
        try:
            raw = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        body = strip_frontmatter(raw)
        # 去掉代码块和引用块，避免误匹配
        body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
        body = re.sub(r"^>.*$", "", body, flags=re.MULTILINE)

        unlinked = count_unlinked(body, entity_names_filtered, name, entity_set_all)
        if not unlinked:
            continue

        quality = info.get("quality", "basic")
        found.append((name, unlinked[: args.max_entities], quality))

    # 按"最高频未链实体出现次数"排序，取 top N
    found.sort(key=lambda x: -max(cnt for _, cnt in x[1]))
    found = found[: args.max_pages]

    if not found:
        print("✓ 未发现需要链接化的实体（或所有高频实体已链接）")
        return 0

    print(f"# H2 词汇链接化候选（{today}）\n")
    queue_lines = []
    for page_name, entities, quality in found:
        top_entity, top_count = entities[0]
        desc_parts = [f"「{e}」×{c}" for e, c in entities]
        desc = "，".join(desc_parts)
        line = (
            f"- [ ] **H2** | [[{page_name}]] | "
            f"正文含未链实体：{desc} "
            f"（quality={quality}）→ 发现: {today} find_unlinked_entities"
        )
        print(line)
        queue_lines.append(line)

    print(f"\n共发现 {len(found)} 个宿主页需要链接化处理。", file=sys.stderr)

    if args.write_queue and not args.dry_run:
        queue_text = QUEUE_FILE.read_text(encoding="utf-8")
        # 找 P1 区段的插入点（第一个 ## P1 行后）
        p1_match = re.search(r"^## P1", queue_text, re.MULTILINE)
        if p1_match:
            insert_pos = queue_text.find("\n", p1_match.start()) + 1
            new_block = "\n".join(queue_lines) + "\n"
            queue_text = queue_text[:insert_pos] + new_block + queue_text[insert_pos:]
        else:
            queue_text += "\n## P1（H2 链接化 自动扫描）\n\n" + "\n".join(queue_lines) + "\n"
        QUEUE_FILE.write_text(queue_text, encoding="utf-8")
        print(f"✓ 已写入 {QUEUE_FILE.name}（{len(queue_lines)} 条）", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
