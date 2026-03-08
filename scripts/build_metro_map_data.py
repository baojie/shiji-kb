#!/usr/bin/env python3
"""
构建地铁线路图数据（全量版）

每个章节 = 一条线路，每个事件 = 一个站点。
事件按序排列：有CE年份的按年份定位，无年份的在相邻之间插值。
跨章互见事件 = 换乘站。

输出: app/metro/data/metro_map_data.json
"""

import json
import re
from collections import defaultdict
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVENTS_DIR = _PROJECT_ROOT / "kg" / "events"
RELATIONS_FILE = _PROJECT_ROOT / "kg" / "event_relations.json"
OUTPUT_DIR = _PROJECT_ROOT / "app" / "metro" / "data"

# ─── 章节分类与配色 ───

CHAPTER_GROUPS = {
    "本纪": {"range": range(1, 13), "colors": [
        "#c0392b", "#e74c3c", "#d35400", "#e67e22", "#f39c12",
        "#f1c40f", "#27ae60", "#2ecc71", "#1abc9c", "#16a085",
        "#2980b9", "#3498db",
    ]},
    "表": {"range": range(13, 23), "colors": [
        "#7f8c8d", "#95a5a6", "#7f8c8d", "#95a5a6", "#7f8c8d",
        "#95a5a6", "#7f8c8d", "#95a5a6", "#7f8c8d", "#95a5a6",
    ]},
    "书": {"range": range(23, 31), "colors": [
        "#8e44ad", "#9b59b6", "#8e44ad", "#9b59b6",
        "#8e44ad", "#9b59b6", "#8e44ad", "#9b59b6",
    ]},
    "世家": {"range": range(31, 61), "colors": [
        "#1a1a2e", "#16213e", "#0f3460", "#533483", "#e94560",
        "#2c3e50", "#34495e", "#1abc9c", "#16a085", "#27ae60",
        "#2ecc71", "#3498db", "#2980b9", "#9b59b6", "#8e44ad",
        "#e74c3c", "#c0392b", "#e67e22", "#d35400", "#f39c12",
        "#2c3e50", "#34495e", "#1abc9c", "#27ae60", "#2980b9",
        "#9b59b6", "#e74c3c", "#e67e22", "#f39c12", "#7f8c8d",
    ]},
    "列传": {"range": range(61, 131), "colors": None},  # auto-generate
}

# Generate colors for 列传
_PALETTE = [
    "#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51",
    "#606c38", "#283618", "#dda15e", "#bc6c25", "#4a4e69",
    "#22577a", "#38a3a5", "#57cc99", "#80ed99", "#c7f9cc",
    "#e63946", "#457b9d", "#1d3557", "#a8dadc", "#f1faee",
]


def get_chapter_color(ch_num):
    """根据章节号分配颜色"""
    for group_name, group_info in CHAPTER_GROUPS.items():
        if ch_num in group_info["range"]:
            colors = group_info["colors"]
            if colors is None:
                idx = (ch_num - group_info["range"].start) % len(_PALETTE)
                return _PALETTE[idx]
            idx = ch_num - group_info["range"].start
            return colors[idx % len(colors)]
    return "#666"


def get_chapter_group(ch_num):
    for group_name, group_info in CHAPTER_GROUPS.items():
        if ch_num in group_info["range"]:
            return group_name
    return "其他"


def load_all_events_with_text():
    """加载所有事件，含原文引用和段落位置"""
    all_events = {}
    table_pat = re.compile(
        r"\|\s*([\d-]+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|"
    )

    for fp in sorted(EVENTS_DIR.glob("*_事件索引.md")):
        text = fp.read_text(encoding="utf-8")
        ch_id = fp.stem.split("_")[0]
        ch_name = fp.stem.replace("_事件索引", "").replace(f"{ch_id}_", "")

        # Parse overview table
        for m in table_pat.finditer(text):
            eid = m.group(1).strip()
            if not re.match(r"\d{3}-\d{3}", eid):
                continue

            ce = None
            ce_m = re.search(r"公元前(\d+)年", m.group(4))
            if ce_m:
                ce = -int(ce_m.group(1))

            people = re.findall(r"@([^@]+)@", m.group(6))
            people += re.findall(r"\$([^$]+)\$", m.group(6))
            locs = re.findall(r"=([^=]+)=", m.group(5))
            dynasties = re.findall(r"&([^&]+)&", m.group(7))

            all_events[eid] = {
                "id": eid,
                "chapter": ch_id,
                "chapter_name": ch_name,
                "name": m.group(2).strip(),
                "type": m.group(3).strip(),
                "time_raw": m.group(4).strip(),
                "ce_year": ce,
                "people": people,
                "locations": locs,
                "dynasties": dynasties,
                "description": "",
                "quote": "",
                "para_pos": "",
            }

        # Parse detail sections for description, quote, paragraph position
        detail_blocks = re.split(r"### (\d{3}-\d{3})", text)
        for i in range(1, len(detail_blocks) - 1, 2):
            eid = detail_blocks[i].strip()
            block = detail_blocks[i + 1]

            if eid not in all_events:
                continue

            desc_m = re.search(r"\*\*事件描述\*\*:\s*(.+?)(?:\n|$)", block)
            if desc_m:
                all_events[eid]["description"] = desc_m.group(1).strip()[:200]

            quote_m = re.search(r"\*\*原文引用\*\*:\s*(.+?)(?:\n|$)", block)
            if quote_m:
                raw_quote = quote_m.group(1).strip()
                # Strip annotation markers for clean display
                clean = re.sub(r"[@$&%=~*]", "", raw_quote).strip('"" ')
                all_events[eid]["quote"] = clean[:150]

            para_m = re.search(r"\*\*段落位置\*\*:\s*(.+?)(?:\n|$)", block)
            if para_m:
                all_events[eid]["para_pos"] = para_m.group(1).strip()

    return all_events


def build_chapter_line(ch_id, ch_name, events, ch_num):
    """构建一个章节的线路数据"""
    # Sort events by ID (which corresponds to narrative order)
    events.sort(key=lambda e: e["id"])

    # Interpolate positions for events without CE years
    # First, collect dated indices
    dated_indices = [(i, e["ce_year"]) for i, e in enumerate(events) if e["ce_year"] is not None]

    # Assign x_position to each event
    for i, e in enumerate(events):
        if e["ce_year"] is not None:
            e["x_pos"] = e["ce_year"]
        else:
            # Interpolate between nearest dated neighbors
            prev_dated = None
            next_dated = None
            for di, dy in dated_indices:
                if di <= i:
                    prev_dated = (di, dy)
                if di > i and next_dated is None:
                    next_dated = (di, dy)

            if prev_dated and next_dated:
                # Linear interpolation
                t = (i - prev_dated[0]) / (next_dated[0] - prev_dated[0])
                e["x_pos"] = prev_dated[1] + t * (next_dated[1] - prev_dated[1])
            elif prev_dated:
                # After last dated event: extrapolate +2 per event
                e["x_pos"] = prev_dated[1] + (i - prev_dated[0]) * 2
            elif next_dated:
                # Before first dated event: extrapolate -2 per event
                e["x_pos"] = next_dated[1] - (next_dated[0] - i) * 2
            else:
                # No dated events at all: use sequence position scaled to a default range
                e["x_pos"] = -500 + i * 5  # arbitrary placement

    stations = []
    for e in events:
        stations.append({
            "id": e["id"],
            "name": e["name"],
            "type": e["type"],
            "year": e["ce_year"],
            "x_pos": round(e["x_pos"], 1),
            "time_raw": e["time_raw"],
            "people": e["people"][:6],
            "locations": e["locations"][:4],
            "dynasties": e.get("dynasties", []),
            "description": e.get("description", ""),
            "quote": e.get("quote", ""),
            "para_pos": e.get("para_pos", ""),
            "chapter": e["chapter"],
            "chapter_name": e["chapter_name"],
        })

    return {
        "id": f"ch{ch_id}",
        "name": ch_name,
        "label": ch_name.replace("列传", "").replace("世家", "").replace("本纪", "")[:4],
        "color": get_chapter_color(ch_num),
        "group": get_chapter_group(ch_num),
        "chapter_id": ch_id,
        "stations": stations,
    }


def load_relations():
    with open(RELATIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["relations"]


def find_transfers(lines_data, relations, all_events):
    """找到换乘站（所有跨线关系）"""
    event_to_lines = defaultdict(set)
    for line in lines_data:
        for s in line["stations"]:
            event_to_lines[s["id"]].add(line["id"])

    transfers = []
    seen = set()

    # Include all cross-line relation types
    cross_types = {"cross_ref", "co_person", "co_location", "concurrent"}

    for r in relations:
        if r["type"] not in cross_types:
            continue
        src, tgt = r["source"], r["target"]
        src_lines = event_to_lines.get(src, set())
        tgt_lines = event_to_lines.get(tgt, set())
        if src_lines and tgt_lines and src_lines != tgt_lines:
            pair = tuple(sorted([src, tgt]))
            if pair in seen:
                continue
            seen.add(pair)
            src_e = all_events.get(src, {})
            transfers.append({
                "events": [src, tgt],
                "lines": sorted(src_lines | tgt_lines),
                "name": src_e.get("name", "?"),
                "type": r["type"],
                "year": src_e.get("ce_year"),
                "shared_people": r.get("shared_people", []),
            })

    return transfers


def main():
    print("加载事件数据（含原文）...")
    all_events = load_all_events_with_text()
    print(f"  {len(all_events)} 个事件")

    print("加载关系数据...")
    relations = load_relations()
    print(f"  {len(relations)} 条关系")

    # Group events by chapter
    ch_events = defaultdict(list)
    ch_names = {}
    for e in all_events.values():
        ch_events[e["chapter"]].append(e)
        ch_names[e["chapter"]] = e["chapter_name"]

    # Build lines for all chapters
    lines_data = []
    for ch_id in sorted(ch_events.keys()):
        ch_num = int(ch_id)
        line = build_chapter_line(ch_id, ch_names[ch_id], ch_events[ch_id], ch_num)
        lines_data.append(line)

    print(f"  {len(lines_data)} 条线路, {sum(len(l['stations']) for l in lines_data)} 个站点")

    # Transfers
    print("计算换乘站...")
    transfers = find_transfers(lines_data, relations, all_events)
    print(f"  {len(transfers)} 个换乘站")

    # Build chains index
    chains = []
    for r in relations:
        if r["type"] in ("sequel", "causal", "part_of", "opposition"):
            chains.append({
                "type": r["type"],
                "source": r.get("source", ""),
                "target": r.get("target", ""),
                "reason": r.get("reason", ""),
            })

    # Global x range
    all_x = [s["x_pos"] for l in lines_data for s in l["stations"]]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "meta": {
            "title": "史记事件地铁图",
            "subtitle": "Historical Events Metro Map of Shiji",
            "total_lines": len(lines_data),
            "total_stations": sum(len(l["stations"]) for l in lines_data),
            "total_transfers": len(transfers),
            "x_range": [min(all_x), max(all_x)] if all_x else [0, 0],
            "groups": ["本纪", "表", "书", "世家", "列传"],
        },
        "lines": lines_data,
        "transfers": transfers,
        "chains": chains,
    }

    output_path = OUTPUT_DIR / "metro_map_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Stats by group
    for grp in ["本纪", "表", "书", "世家", "列传"]:
        grp_lines = [l for l in lines_data if l["group"] == grp]
        grp_stations = sum(len(l["stations"]) for l in grp_lines)
        print(f"  {grp}: {len(grp_lines)} 线路, {grp_stations} 站点")

    print(f"\n输出: {output_path}")
    print(f"总计: {output['meta']['total_lines']} 线路, {output['meta']['total_stations']} 站点, {len(transfers)} 换乘")


if __name__ == "__main__":
    main()
