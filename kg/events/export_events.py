#!/usr/bin/env python3
"""
将章节事件索引 Markdown 转换为 JSON 和 CSV
用法: python3 export_events.py 007
      python3 export_events.py   ← 处理全部章节
输出: kg/events/data/<章节>_事件索引.json / .csv
"""
import json
import csv
import os
import re
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ─── 概览表解析 ────────────────────────────────────────────────────────────────

def parse_overview_table(text):
    """解析 ## 事件列表概览 下的 Markdown 表格，返回 list[dict]。"""
    rows = []
    in_section = False
    table_started = False
    header = []
    for line in text.splitlines():
        if "## 事件列表概览" in line:
            in_section = True
            continue
        if not in_section:
            continue
        stripped = line.strip()
        # 表格尚未开始时跳过空行
        if not stripped:
            if table_started:
                break   # 表格结束后的空行 → 停止
            continue
        # 分隔行
        if re.match(r"^\|[-: |]+\|$", stripped):
            continue
        if stripped.startswith("|"):
            table_started = True
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not header:
                header = cells
            else:
                rows.append(dict(zip(header, cells)))
        elif table_started:
            break   # 表格后遇到非表格行
    return rows


# ─── 详情区块解析 ──────────────────────────────────────────────────────────────

DETAIL_FIELDS = {
    "事件类型": "type",
    "时间": "time",
    "地点": "location",
    "主要人物": "persons",
    "涉及朝代": "dynasties",
    "事件描述": "description",
    "原文引用": "source_text",
    "段落位置": "paragraph",
    "年代推断": "date_note",
}

def parse_detail_blocks(text):
    """解析 ## 详细事件记录 后的所有 ### 区块，返回 dict[event_id → dict]。"""
    details = {}
    in_details = False
    current_id = None
    current = {}

    for line in text.splitlines():
        if "## 详细事件记录" in line:
            in_details = True
            continue
        if not in_details:
            continue

        # 新区块开始
        m = re.match(r"^### (\d{3}-\d{3})\s+(.*)", line)
        if m:
            if current_id:
                details[current_id] = current
            current_id = m.group(1)
            current = {"event_id": current_id, "event_name": m.group(2).strip()}
            continue

        if current_id is None:
            continue

        # 字段行: - **字段**: 值
        m = re.match(r"^-\s+\*\*(.+?)\*\*[：:]\s*(.*)", line)
        if m:
            key_cn = m.group(1).strip()
            val = m.group(2).strip()
            if key_cn in DETAIL_FIELDS:
                current[DETAIL_FIELDS[key_cn]] = val

    if current_id:
        details[current_id] = current

    return details


# ─── 合并 ─────────────────────────────────────────────────────────────────────

OVERVIEW_COL_MAP = {
    "事件ID":   "event_id",
    "事件名称": "event_name",
    "事件类型": "type",
    "时间":     "time",
    "地点":     "location",
    "主要人物": "persons",
    "朝代":     "dynasties",
}

def merge(overview_rows, detail_blocks):
    merged = []
    for row in overview_rows:
        eid = row.get("事件ID", "").strip()
        # 概览字段（中文键 → 英文键）
        event = {OVERVIEW_COL_MAP.get(k, k): v for k, v in row.items()}
        # 详情字段补充
        detail = detail_blocks.get(eid, {})
        for k, v in detail.items():
            if k not in event or not event[k]:
                event[k] = v
            elif k in ("description", "source_text", "paragraph", "date_note"):
                event[k] = v  # 详情版本更完整，优先
        merged.append(event)
    return merged


# ─── 输出 ─────────────────────────────────────────────────────────────────────

# 统一列顺序
CSV_COLUMNS = [
    "event_id", "event_name", "type", "time", "location",
    "persons", "dynasties", "description", "source_text",
    "paragraph", "date_note",
]

def write_json(events, chapter_id, title):
    path = os.path.join(DATA_DIR, f"{chapter_id}_事件索引.json")
    data = {
        "chapter_id": chapter_id,
        "title": title,
        "event_count": len(events),
        "events": events,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def write_csv(events, chapter_id):
    path = os.path.join(DATA_DIR, f"{chapter_id}_事件索引.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(events)
    return path


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def process_file(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 章节标题（第一行 # ）
    m = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    title = m.group(1).strip() if m else os.path.basename(md_path)

    # 章节 ID（文件名前三位数字）
    chapter_id = re.match(r"(\d{3})", os.path.basename(md_path)).group(1)

    overview = parse_overview_table(text)
    details  = parse_detail_blocks(text)
    events   = merge(overview, details)

    jp = write_json(events, chapter_id, title)
    cp = write_csv(events, chapter_id)
    print(f"✓ {title}: {len(events)} 事件 → {os.path.basename(jp)}, {os.path.basename(cp)}")


def main():
    if len(sys.argv) > 1:
        prefix = sys.argv[1].zfill(3)
        targets = [f for f in os.listdir(DATA_DIR)
                   if f.startswith(prefix) and f.endswith("_事件索引.md")]
    else:
        targets = [f for f in os.listdir(DATA_DIR) if f.endswith("_事件索引.md")]

    if not targets:
        print("未找到匹配的事件索引文件。")
        return

    for fn in sorted(targets):
        process_file(os.path.join(DATA_DIR, fn))


if __name__ == "__main__":
    main()
