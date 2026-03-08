#!/usr/bin/env python3
"""
史记事件关系提取脚本

从 kg/events/*_事件索引.md 中提取事件之间的各种关系：

自动计算:
  - co_person:    共同人物（两事件共享关键人物）
  - co_location:  共同地点（两事件共享地点）
  - concurrent:   并发（同一公元年份）
  - cross_ref:    跨章互见（不同章节记述同一事件）

LLM推理（章节内）:
  - sequel:       延续关系（A时间上直接导向B）
  - causal:       因果关系（A导致B发生）
  - part_of:      包含关系（A是B的子事件）
  - opposition:   对立关系（对立双方的行动）

使用方法:
    python3 scripts/extract_event_relations.py                   # 全流程
    python3 scripts/extract_event_relations.py --auto-only       # 仅自动计算
    python3 scripts/extract_event_relations.py --llm-only        # 仅LLM推理
    python3 scripts/extract_event_relations.py --chapters 007 008  # 指定章节
    python3 scripts/extract_event_relations.py --dry-run         # 预览

输出:
    kg/event_relations.json       — 所有关系
    kg/event_relations_summary.md — 关系统计摘要
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVENTS_DIR = _PROJECT_ROOT / "kg" / "events" / "data"
OUTPUT_JSON = _PROJECT_ROOT / "kg" / "events" / "data" / "event_relations.json"
OUTPUT_SUMMARY = _PROJECT_ROOT / "kg" / "events" / "data" / "event_relations_summary.md"

# ─── 事件解析 ───


def parse_event_file(filepath):
    """解析事件索引文件，提取结构化事件数据"""
    text = filepath.read_text(encoding="utf-8")
    chapter_id = filepath.stem.split("_")[0]
    chapter_name = filepath.stem.replace("_事件索引", "").replace(f"{chapter_id}_", "")

    events = []

    # 解析概览表
    table_pattern = re.compile(
        r"\|\s*([\d-]+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|"
    )

    for m in table_pattern.finditer(text):
        event_id = m.group(1).strip()
        if not re.match(r"\d{3}-\d{3}", event_id):
            continue

        name = m.group(2).strip()
        event_type = m.group(3).strip()
        time_field = m.group(4).strip()
        location_field = m.group(5).strip()
        people_field = m.group(6).strip()
        dynasty_field = m.group(7).strip()

        # 提取公元年
        ce_year = None
        ce_match = re.search(r"公元前(\d+)年", time_field)
        if ce_match:
            ce_year = -int(ce_match.group(1))
        else:
            ce_match = re.search(r"公元(\d+)年", time_field)
            if ce_match:
                ce_year = int(ce_match.group(1))

        # 提取地点标签
        locations = re.findall(r"=([^=]+)=", location_field)

        # 提取人物标签（@人物@ 和 $人物$）
        people = re.findall(r"@([^@]+)@", people_field)
        people += re.findall(r"\$([^$]+)\$", people_field)

        # 提取朝代标签
        dynasties = re.findall(r"&([^&]+)&", dynasty_field)

        events.append({
            "id": event_id,
            "chapter_id": chapter_id,
            "chapter_name": chapter_name,
            "name": name,
            "type": event_type,
            "time_raw": time_field,
            "ce_year": ce_year,
            "locations": locations,
            "people": people,
            "dynasties": dynasties,
        })

    return events


def load_all_events():
    """加载所有事件"""
    all_events = {}
    for f in sorted(EVENTS_DIR.glob("*_事件索引.md")):
        events = parse_event_file(f)
        for e in events:
            all_events[e["id"]] = e
    return all_events


# ─── 自动关系计算 ───


def compute_co_person(all_events, min_shared=2):
    """计算共同人物关系（至少共享 min_shared 个人物）

    只对跨章节事件计算，章节内由LLM处理。
    """
    relations = []
    event_ids = list(all_events.keys())

    # 建立人物 → 事件ID映射
    person_to_events = defaultdict(set)
    for eid, e in all_events.items():
        for p in e["people"]:
            person_to_events[p].add(eid)

    # 对跨章节的事件对，计算共享人物
    seen = set()
    for person, eids in person_to_events.items():
        eids = list(eids)
        for i in range(len(eids)):
            for j in range(i + 1, len(eids)):
                a, b = eids[i], eids[j]
                # 跨章节才计算
                if all_events[a]["chapter_id"] == all_events[b]["chapter_id"]:
                    continue
                pair = (min(a, b), max(a, b))
                if pair in seen:
                    continue
                seen.add(pair)

                shared = set(all_events[a]["people"]) & set(all_events[b]["people"])
                if len(shared) >= min_shared:
                    relations.append({
                        "type": "co_person",
                        "source": pair[0],
                        "target": pair[1],
                        "shared": sorted(shared),
                        "auto": True,
                    })

    return relations


def compute_co_location(all_events, min_shared=1):
    """计算共同地点关系（跨章节）"""
    relations = []

    # 建立地点 → 事件ID映射
    loc_to_events = defaultdict(set)
    for eid, e in all_events.items():
        for loc in e["locations"]:
            loc_to_events[loc].add(eid)

    # 对跨章节事件对，计算共享地点
    seen = set()
    for loc, eids in loc_to_events.items():
        eids = list(eids)
        for i in range(len(eids)):
            for j in range(i + 1, len(eids)):
                a, b = eids[i], eids[j]
                if all_events[a]["chapter_id"] == all_events[b]["chapter_id"]:
                    continue
                pair = (min(a, b), max(a, b))
                if pair in seen:
                    continue
                seen.add(pair)

                shared_loc = set(all_events[a]["locations"]) & set(all_events[b]["locations"])
                shared_ppl = set(all_events[a]["people"]) & set(all_events[b]["people"])
                # 共地点 + 至少1个共同人物 → 有意义的关联
                if shared_loc and shared_ppl:
                    relations.append({
                        "type": "co_location",
                        "source": pair[0],
                        "target": pair[1],
                        "shared_locations": sorted(shared_loc),
                        "shared_people": sorted(shared_ppl),
                        "auto": True,
                    })

    return relations


def compute_concurrent(all_events):
    """计算并发关系（同一公元年、跨章节）"""
    relations = []

    # 按公元年分组
    year_to_events = defaultdict(list)
    for eid, e in all_events.items():
        if e["ce_year"] is not None:
            year_to_events[e["ce_year"]].append(eid)

    seen = set()
    for year, eids in year_to_events.items():
        for i in range(len(eids)):
            for j in range(i + 1, len(eids)):
                a, b = eids[i], eids[j]
                if all_events[a]["chapter_id"] == all_events[b]["chapter_id"]:
                    continue
                pair = (min(a, b), max(a, b))
                if pair in seen:
                    continue
                seen.add(pair)

                shared_ppl = set(all_events[a]["people"]) & set(all_events[b]["people"])
                # 同年 + 共同人物 → 有意义
                if shared_ppl:
                    relations.append({
                        "type": "concurrent",
                        "source": pair[0],
                        "target": pair[1],
                        "ce_year": year,
                        "shared_people": sorted(shared_ppl),
                        "auto": True,
                    })

    return relations


def compute_cross_ref(all_events):
    """计算跨章互见关系（不同章节描述同一事件）

    策略：事件名称高度相似 + 共享≥2人物 + 同年（如有）
    """
    relations = []
    event_ids = list(all_events.keys())

    def name_similarity(a, b):
        """简单的名称相似度：共有字符比例"""
        sa, sb = set(a), set(b)
        if not sa or not sb:
            return 0
        intersection = sa & sb
        return len(intersection) / min(len(sa), len(sb))

    seen = set()
    for i in range(len(event_ids)):
        for j in range(i + 1, len(event_ids)):
            a, b = event_ids[i], event_ids[j]
            ea, eb = all_events[a], all_events[b]

            # 必须跨章节
            if ea["chapter_id"] == eb["chapter_id"]:
                continue

            pair = (min(a, b), max(a, b))
            if pair in seen:
                continue

            # 名称相似度
            sim = name_similarity(ea["name"], eb["name"])
            if sim < 0.6:
                continue

            # 共同人物
            shared_ppl = set(ea["people"]) & set(eb["people"])
            if len(shared_ppl) < 1:
                continue

            # 同年检查
            same_year = (
                ea["ce_year"] is not None
                and eb["ce_year"] is not None
                and ea["ce_year"] == eb["ce_year"]
            )

            # 名称高度相似（≥0.8）或 名称较相似+共同人物≥2+同年
            if sim >= 0.8 and shared_ppl:
                score = "high"
            elif sim >= 0.6 and len(shared_ppl) >= 2 and same_year:
                score = "medium"
            elif sim >= 0.6 and len(shared_ppl) >= 2:
                score = "medium"
            else:
                continue

            seen.add(pair)
            relations.append({
                "type": "cross_ref",
                "source": pair[0],
                "target": pair[1],
                "name_similarity": round(sim, 2),
                "shared_people": sorted(shared_ppl),
                "confidence": score,
                "auto": True,
            })

    return relations


def run_auto_extraction(all_events):
    """运行所有自动关系提取"""
    print("计算跨章互见关系 (cross_ref)...")
    cross_refs = compute_cross_ref(all_events)
    print(f"  → {len(cross_refs)} 条")

    print("计算共同人物关系 (co_person)...")
    co_persons = compute_co_person(all_events, min_shared=2)
    print(f"  → {len(co_persons)} 条")

    print("计算并发关系 (concurrent + 共同人物)...")
    concurrents = compute_concurrent(all_events)
    print(f"  → {len(concurrents)} 条")

    print("计算共地点+共人物关系 (co_location)...")
    co_locs = compute_co_location(all_events)
    print(f"  → {len(co_locs)} 条")

    return cross_refs + co_persons + concurrents + co_locs


# ─── LLM推理关系 ───


LLM_SYSTEM_PROMPT = """你是历史知识图谱专家。你的任务是分析同一篇章中的历史事件列表，识别事件之间的结构化关系。

## 需要识别的关系类型

1. **sequel（延续）**: 事件A在时间上直接导向事件B，B是A的后续发展
   - 例：008-008陈胜起义 → 008-009起兵沛县（陈胜起义激发了刘邦起兵）

2. **causal（因果）**: 事件A是事件B的直接原因
   - 例：007-015项羽斩宋义 → 007-016怀王拜项羽上将（杀宋义后被拜为上将）

3. **part_of（包含）**: 事件A是事件B的组成部分/子事件
   - 例：007-062四面楚歌别虞 part_of 007-061垓下之围（楚歌是垓下之围的一部分）

4. **opposition（对立）**: 两事件代表对立双方各自的行动
   - 例：008-046荥阳相持 opposition 007-051项羽拔荥阳（汉楚双方在荥阳对峙）

## 输出格式

输出JSON数组，每个元素：
```json
{"type": "sequel|causal|part_of|opposition", "source": "事件ID", "target": "事件ID", "reason": "简短说明"}
```

## 规则
- source→target 表示方向：sequel/causal中source在前，part_of中source是子事件
- 只识别明确的、有意义的关系，不要过度关联
- sequel 只针对直接后续，不是跳跃式的
- 每章通常有10-30条关系，不要遗漏重要的因果链
- reason 用10字以内说明关系依据
"""


def build_chapter_prompt(events):
    """构建单章的LLM提示"""
    lines = []
    for e in events:
        time_str = e["time_raw"] if e["time_raw"] != "-" else "无明确时间"
        people_str = "、".join(e["people"][:5]) if e["people"] else "无"
        loc_str = "、".join(e["locations"][:3]) if e["locations"] else "无"
        lines.append(
            f"- {e['id']} {e['name']} [{e['type']}] 时间:{time_str} 地点:{loc_str} 人物:{people_str}"
        )

    chapter_id = events[0]["chapter_id"]
    chapter_name = events[0]["chapter_name"]
    event_list = "\n".join(lines)

    return f"""请分析《史记·{chapter_name}》（第{chapter_id}篇）中以下{len(events)}个事件之间的关系：

{event_list}

请输出这些事件之间的 sequel、causal、part_of、opposition 关系（JSON数组）。"""


def call_llm_for_chapter(client, events):
    """调用LLM分析单章事件关系"""
    prompt = build_chapter_prompt(events)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system=LLM_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text

    # 提取JSON
    json_match = re.search(r"\[[\s\S]*\]", text)
    if json_match:
        try:
            relations = json.loads(json_match.group())
            # 标记为LLM推理
            for r in relations:
                r["auto"] = False
            return relations, response.usage.input_tokens, response.usage.output_tokens
        except json.JSONDecodeError:
            print(f"    JSON解析失败")
            return [], 0, 0
    return [], 0, 0


def run_llm_extraction(all_events, chapter_ids=None):
    """运行LLM关系推理"""
    try:
        import anthropic
    except ImportError:
        print("需要 anthropic 包: pip install anthropic")
        return []

    client = anthropic.Anthropic()

    # 按章节分组
    chapters = defaultdict(list)
    for e in all_events.values():
        chapters[e["chapter_id"]].append(e)

    if chapter_ids:
        chapters = {k: v for k, v in chapters.items() if k in chapter_ids}

    # 按事件ID排序每章
    for ch_id in chapters:
        chapters[ch_id].sort(key=lambda e: e["id"])

    all_relations = []
    total_in, total_out = 0, 0

    # 只处理有≥3个事件的章节
    valid_chapters = {k: v for k, v in chapters.items() if len(v) >= 3}
    print(f"\n将对 {len(valid_chapters)} 个章节进行LLM关系推理...")

    for idx, (ch_id, events) in enumerate(sorted(valid_chapters.items())):
        ch_name = events[0]["chapter_name"]
        print(f"  [{idx+1}/{len(valid_chapters)}] {ch_id} {ch_name} ({len(events)}个事件)...", end=" ", flush=True)

        relations, tok_in, tok_out = call_llm_for_chapter(client, events)
        total_in += tok_in
        total_out += tok_out

        # 验证事件ID存在
        valid_ids = {e["id"] for e in events}
        valid_relations = []
        for r in relations:
            if r.get("source") in valid_ids and r.get("target") in valid_ids:
                valid_relations.append(r)

        all_relations.extend(valid_relations)
        print(f"{len(valid_relations)} 条关系")

    print(f"\nLLM推理完成: {len(all_relations)} 条关系, tokens: {total_in}+{total_out}")
    return all_relations


# ─── 输出 ───


def save_results(all_events, relations):
    """保存关系结果"""
    # 保存JSON
    output = {
        "meta": {
            "total_events": len(all_events),
            "total_relations": len(relations),
        },
        "relations": relations,
    }

    # 统计
    type_counts = defaultdict(int)
    auto_count = 0
    llm_count = 0
    for r in relations:
        type_counts[r["type"]] += 1
        if r.get("auto"):
            auto_count += 1
        else:
            llm_count += 1

    output["meta"]["by_type"] = dict(type_counts)
    output["meta"]["auto_count"] = auto_count
    output["meta"]["llm_count"] = llm_count

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n关系数据已保存: {OUTPUT_JSON}")

    # 生成摘要
    summary_lines = [
        "# 史记事件关系统计",
        "",
        f"- 总事件数: {len(all_events)}",
        f"- 总关系数: {len(relations)}",
        f"- 自动计算: {auto_count}",
        f"- LLM推理: {llm_count}",
        "",
        "## 关系类型分布",
        "",
        "| 类型 | 说明 | 数量 |",
        "|------|------|------|",
    ]

    type_labels = {
        "cross_ref": "跨章互见",
        "co_person": "共同人物",
        "co_location": "共同地点",
        "concurrent": "并发事件",
        "sequel": "延续关系",
        "causal": "因果关系",
        "part_of": "包含关系",
        "opposition": "对立关系",
    }

    for t, label in type_labels.items():
        count = type_counts.get(t, 0)
        summary_lines.append(f"| {t} | {label} | {count} |")

    # 跨章互见的具体例子（前20条）
    cross_refs = [r for r in relations if r["type"] == "cross_ref"]
    if cross_refs:
        summary_lines += [
            "",
            "## 跨章互见（示例）",
            "",
            "| 事件A | 事件B | 相似度 | 共同人物 |",
            "|-------|-------|--------|---------|",
        ]
        for r in sorted(cross_refs, key=lambda x: -x.get("name_similarity", 0))[:30]:
            ea = all_events.get(r["source"], {})
            eb = all_events.get(r["target"], {})
            name_a = f"{r['source']} {ea.get('name', '?')}"
            name_b = f"{r['target']} {eb.get('name', '?')}"
            sim = r.get("name_similarity", "?")
            ppl = "、".join(r.get("shared_people", [])[:3])
            summary_lines.append(f"| {name_a} | {name_b} | {sim} | {ppl} |")

    summary_text = "\n".join(summary_lines) + "\n"
    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"关系摘要已保存: {OUTPUT_SUMMARY}")

    return output


# ─── 主流程 ───


def main():
    args = sys.argv[1:]

    dry_run = "--dry-run" in args
    auto_only = "--auto-only" in args
    llm_only = "--llm-only" in args

    chapter_ids = None
    if "--chapters" in args:
        idx = args.index("--chapters")
        chapter_ids = set(args[idx + 1:])

    # 加载事件
    print("加载所有事件...")
    all_events = load_all_events()
    print(f"  → {len(all_events)} 个事件")

    if dry_run:
        # 按章统计
        ch_counts = defaultdict(int)
        for e in all_events.values():
            ch_counts[e["chapter_id"]] += 1
        for ch, cnt in sorted(ch_counts.items()):
            name = next(
                (e["chapter_name"] for e in all_events.values() if e["chapter_id"] == ch),
                "?",
            )
            print(f"  {ch} {name}: {cnt} 个事件")
        return

    relations = []

    # 自动计算
    if not llm_only:
        print("\n=== 自动关系计算 ===")
        auto_rels = run_auto_extraction(all_events)
        relations.extend(auto_rels)

    # LLM推理
    if not auto_only:
        print("\n=== LLM关系推理 ===")
        llm_rels = run_llm_extraction(all_events, chapter_ids)
        relations.extend(llm_rels)

    # 去重
    seen = set()
    unique_relations = []
    for r in relations:
        key = (r["type"], r.get("source", ""), r.get("target", ""))
        if key not in seen:
            seen.add(key)
            unique_relations.append(r)

    # 保存
    result = save_results(all_events, unique_relations)
    print(f"\n完成! 共 {result['meta']['total_relations']} 条关系")


if __name__ == "__main__":
    main()
