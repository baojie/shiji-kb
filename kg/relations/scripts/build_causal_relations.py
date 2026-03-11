#!/usr/bin/env python3
"""
跨章事件因果关系推理管线

输入:
  - kg/events/data/*_事件索引.md        事件描述
  - kg/events/data/event_relations.json  现有关系（cross_ref / co_person）

输出:
  - kg/relations/causal_relations.json   跨章因果关系（含LLM推理文本）

用法:
  # 生成候选对并运行推理（默认全量）
  python build_causal_relations.py

  # 只生成候选对，不调用LLM（检查候选质量）
  python build_causal_relations.py --dry-run

  # 仅处理指定章节对
  python build_causal_relations.py --chapters 001 002 003

  # 续跑（跳过已有结果）
  python build_causal_relations.py --resume
"""

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import anthropic
import os

# 从 Claude Code 配置中读取 API 凭证
def _load_claude_credentials():
    settings_path = Path.home() / ".claude" / "settings.json"
    if settings_path.exists():
        import json as _json
        s = _json.loads(settings_path.read_text())
        env = s.get("env", {})
        if "ANTHROPIC_AUTH_TOKEN" in env and not os.environ.get("ANTHROPIC_API_KEY"):
            os.environ["ANTHROPIC_API_KEY"] = env["ANTHROPIC_AUTH_TOKEN"]
        if "ANTHROPIC_BASE_URL" in env and not os.environ.get("ANTHROPIC_BASE_URL"):
            os.environ["ANTHROPIC_BASE_URL"] = env["ANTHROPIC_BASE_URL"]

_load_claude_credentials()

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVENTS_DIR = _ROOT / "kg" / "events" / "data"
RELATIONS_FILE = _ROOT / "kg" / "events" / "data" / "event_relations.json"
OUTPUT_FILE = _ROOT / "kg" / "relations" / "causal_relations.json"

# ─── 事件描述加载 ───

def load_event_details() -> dict:
    """从130个事件索引.md中提取详细描述"""
    detail_pat = re.compile(
        r"### (\d{3}-\d{3}) (.+?)\n(.*?)(?=### \d{3}-\d{3}|\Z)", re.DOTALL
    )
    year_pat = re.compile(r"公元前(\d+)年")
    desc_pat = re.compile(r"\*\*事件描述\*\*[：:] (.+)")
    type_pat = re.compile(r"\*\*事件类型\*\*[：:] (.+)")
    people_pat = re.compile(r"\*\*主要人物\*\*[：:] (.+)")
    loc_pat = re.compile(r"\*\*地点\*\*[：:] (.+)")
    table_year_pat = re.compile(
        r"\|\s*(\d{3}-\d{3})\s*\|[^|]*\|[^|]*\|\s*[\[（]?(?:约)?公元前(\d+)年"
    )

    events = {}

    for fp in sorted(EVENTS_DIR.glob("*_事件索引.md")):
        ch_id = fp.stem.split("_")[0]
        ch_name = fp.stem.replace("_事件索引", "").replace(f"{ch_id}_", "")
        text = fp.read_text(encoding="utf-8")

        # Get years from overview table
        table_years = {}
        for m in table_year_pat.finditer(text):
            table_years[m.group(1)] = -int(m.group(2))

        for m in detail_pat.finditer(text):
            eid = m.group(1)
            name = m.group(2).strip()
            body = m.group(3)

            desc_m = desc_pat.search(body)
            type_m = type_pat.search(body)
            people_m = people_pat.search(body)
            loc_m = loc_pat.search(body)

            year = table_years.get(eid)

            events[eid] = {
                "id": eid,
                "name": name,
                "chapter": ch_id,
                "chapter_name": ch_name,
                "year": year,
                "type": type_m.group(1).strip() if type_m else "",
                "people": people_m.group(1).strip() if people_m else "",
                "location": loc_m.group(1).strip() if loc_m else "",
                "description": desc_m.group(1).strip() if desc_m else "",
            }

    print(f"加载事件详情: {len(events)} 个")
    return events


# ─── 候选对生成 ───

def generate_candidates(events: dict, only_chapters: list = None) -> list:
    """
    从现有关系中筛选跨章候选对：
    1. cross_ref: 同一事件被多章引用 → 高可信度因果候选
    2. co_person: 同一人物，时序在先的事件 → 中可信度
    """
    with open(RELATIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    rels = data["relations"]

    candidates = []
    seen = set()

    for r in rels:
        src = r.get("source") or r.get("from")
        tgt = r.get("target") or r.get("to")
        rtype = r.get("type", "")

        if not src or not tgt:
            continue
        if src not in events or tgt not in events:
            continue

        src_ch = src.split("-")[0]
        tgt_ch = tgt.split("-")[0]

        # 只要跨章
        if src_ch == tgt_ch:
            continue

        if only_chapters and src_ch not in only_chapters and tgt_ch not in only_chapters:
            continue

        # 确保时序：from 在 to 之前（或同年 cross_ref）
        yr_src = events[src]["year"] or 0
        yr_tgt = events[tgt]["year"] or 0

        if rtype == "cross_ref":
            # cross_ref 双向都有因果可能，取时序较早的为 source
            if yr_src > yr_tgt:
                src, tgt = tgt, src
            pair_key = (min(src, tgt), max(src, tgt), rtype)
        elif rtype in ("co_person", "co_location"):
            if yr_src == yr_tgt:
                continue  # 同年 co_person 不做因果推断
            if yr_src > yr_tgt:
                src, tgt = tgt, src
            pair_key = (src, tgt, rtype)
        else:
            continue

        if pair_key in seen:
            continue
        seen.add(pair_key)

        candidates.append({
            "source": src,
            "target": tgt,
            "base_type": rtype,
            "shared_people": r.get("shared_people", []),
            "confidence_hint": 0.8 if rtype == "cross_ref" else 0.5,
        })

    print(f"生成候选对: {len(candidates)} 个")
    print(f"  cross_ref: {sum(1 for c in candidates if c['base_type']=='cross_ref')}")
    print(f"  co_person: {sum(1 for c in candidates if c['base_type']=='co_person')}")
    print(f"  co_location: {sum(1 for c in candidates if c['base_type']=='co_location')}")
    return candidates


# ─── LLM 推理 ───

BATCH_SIZE = 12  # 每次调用处理的候选对数

SYSTEM_PROMPT = """你是中国史学专家，擅长《史记》研究。
你的任务是分析两个跨章节事件之间是否存在因果关系，并给出推理。

因果类型定义：
- direct_cause: 前事直接导致后事发生（充分条件）
- prerequisite: 前事是后事得以发生的必要前提（必要条件）
- background: 前事构成后事发生的历史背景或社会条件
- trigger: 前事成为后事的导火索（时间上紧密相连）
- consequence: 后事是前事的直接后果（从后果视角描述）
- precedent: 前事为后事提供历史先例或模板
- no_causal: 两事件无因果关系（仅共享人物/时期）

输出要求：严格按JSON格式，不要添加任何额外文字。"""

def build_batch_prompt(pairs: list, events: dict) -> str:
    items = []
    for i, c in enumerate(pairs):
        src = events[c["source"]]
        tgt = events[c["target"]]
        year_src = f"前{abs(src['year'])}年" if src['year'] else "年代不详"
        year_tgt = f"前{abs(tgt['year'])}年" if tgt['year'] else "年代不详"
        shared = "、".join(c["shared_people"]) if c["shared_people"] else "（无）"

        item = f"""[{i+1}]
事件A: {src['id']} 《{src['chapter_name']}》 {year_src} {src['name']}
  类型: {src['type']}  人物: {src['people']}
  描述: {src['description'][:120]}
事件B: {tgt['id']} 《{tgt['chapter_name']}》 {year_tgt} {tgt['name']}
  类型: {tgt['type']}  人物: {tgt['people']}
  描述: {tgt['description'][:120]}
共享人物: {shared}"""
        items.append(item)

    batch_text = "\n\n".join(items)
    return f"""分析以下{len(pairs)}对跨章节事件是否存在因果关系。

{batch_text}

请对每对事件输出JSON对象，格式为：
{{
  "results": [
    {{
      "index": 1,
      "has_causal": true,
      "causal_type": "direct_cause",
      "confidence": 0.85,
      "reasoning": "简要说明因果逻辑（1-2句话）"
    }},
    ...
  ]
}}

confidence范围0-1，has_causal=false时causal_type填"no_causal"，reasoning填无因果的原因。"""


def call_llm_batch(client, pairs: list, events: dict) -> list:
    """调用Claude API分析一批候选对"""
    prompt = build_batch_prompt(pairs, events)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # 提取JSON
    json_pat = re.search(r'\{.*\}', raw, re.DOTALL)
    if not json_pat:
        print(f"  WARNING: no JSON in response, raw: {raw[:100]}")
        return []

    try:
        parsed = json.loads(json_pat.group())
        return parsed.get("results", [])
    except json.JSONDecodeError as e:
        print(f"  WARNING: JSON parse error: {e}, raw: {raw[:200]}")
        return []


# ─── 主流程 ───

def run(dry_run: bool = False, only_chapters: list = None, resume: bool = False):
    events = load_event_details()
    candidates = generate_candidates(events, only_chapters)

    if dry_run:
        print("\n=== DRY RUN: 前20个候选对 ===")
        for c in candidates[:20]:
            src = events[c["source"]]
            tgt = events[c["target"]]
            yr_s = f"前{abs(src['year'])}年" if src['year'] else "?"
            yr_t = f"前{abs(tgt['year'])}年" if tgt['year'] else "?"
            print(f"  [{c['base_type']:12}] {c['source']}({yr_s} {src['name']}) "
                  f"→ {c['target']}({yr_t} {tgt['name']})")
        return

    # 加载已有结果（续跑模式）
    existing_pairs = set()
    existing_results = []
    if resume and OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            old = json.load(f)
        existing_results = old.get("relations", [])
        existing_pairs = {(r["source"], r["target"]) for r in existing_results}
        print(f"续跑: 已有 {len(existing_results)} 条结果，跳过已处理对")

    # 过滤未处理候选
    todo = [c for c in candidates if (c["source"], c["target"]) not in existing_pairs]
    print(f"待处理: {len(todo)} 对（共 {len(candidates)} 对）")

    client = anthropic.Anthropic()
    all_results = list(existing_results)

    batches = [todo[i:i+BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
    print(f"分 {len(batches)} 批处理，每批 {BATCH_SIZE} 对")
    print()

    causal_count = 0
    no_causal_count = 0
    error_count = 0

    for batch_i, batch in enumerate(batches):
        print(f"批次 {batch_i+1}/{len(batches)} ({len(batch)} 对)...", end=" ", flush=True)

        try:
            results = call_llm_batch(client, batch, events)
        except Exception as e:
            print(f"ERROR: {e}")
            error_count += len(batch)
            time.sleep(5)
            continue

        if len(results) != len(batch):
            print(f"WARNING: expected {len(batch)} results, got {len(results)}")

        for res in results:
            idx = res.get("index", 1) - 1
            if idx < 0 or idx >= len(batch):
                continue
            candidate = batch[idx]
            src = events[candidate["source"]]
            tgt = events[candidate["target"]]

            record = {
                "source": candidate["source"],
                "target": candidate["target"],
                "source_name": src["name"],
                "target_name": tgt["name"],
                "source_chapter": src["chapter_name"],
                "target_chapter": tgt["chapter_name"],
                "source_year": src["year"],
                "target_year": tgt["year"],
                "base_relation": candidate["base_type"],
                "has_causal": res.get("has_causal", False),
                "causal_type": res.get("causal_type", "no_causal"),
                "confidence": res.get("confidence", 0.0),
                "reasoning": res.get("reasoning", ""),
                "shared_people": candidate["shared_people"],
            }
            all_results.append(record)

            if res.get("has_causal"):
                causal_count += 1
                print(f"\n  ✓ {candidate['source']}→{candidate['target']}: "
                      f"{res['causal_type']} ({res.get('confidence',0):.2f}) "
                      f"{res.get('reasoning','')[:50]}")
            else:
                no_causal_count += 1

        print(f"OK (累计因果: {causal_count})")

        # 每批保存一次
        save_output(all_results)

        # Rate limiting
        if batch_i < len(batches) - 1:
            time.sleep(1)

    print()
    print(f"=== 完成 ===")
    print(f"因果关系: {causal_count}")
    print(f"无因果:   {no_causal_count}")
    print(f"错误:     {error_count}")
    print(f"输出:     {OUTPUT_FILE}")

    save_output(all_results)


def save_output(results: list):
    causal_only = [r for r in results if r.get("has_causal")]
    output = {
        "meta": {
            "total_pairs_analyzed": len(results),
            "causal_relations_found": len(causal_only),
            "method": "llm_reasoning",
            "model": "claude-sonnet-4-6",
        },
        "relations": results,
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


# ─── CLI ───

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="跨章事件因果关系推理")
    parser.add_argument("--dry-run", action="store_true", help="只显示候选对，不调用LLM")
    parser.add_argument("--chapters", nargs="+", help="只处理指定章节（如 001 002）")
    parser.add_argument("--resume", action="store_true", help="续跑，跳过已有结果")
    args = parser.parse_args()

    run(dry_run=args.dry_run, only_chapters=args.chapters, resume=args.resume)
