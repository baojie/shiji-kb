"""
Smart mock for LocalModel.chat_json.

Simulates what a real Qwen3.5-2B would do:
- Mostly correct but with realistic 2B-model error patterns
- Round 1: introduces common mistakes
- Reflect loop: catches and fixes them
- skill_patch: appends rules based on error patterns
"""
from __future__ import annotations

import json
import re
from typing import Any


# ── Known people patterns ────────────────────────────────────────────────
KNOWN_PEOPLE = {
    "老张": ["老张"],
    "小李": ["小李"],
    "小王": ["小王"],
    "阿明": ["阿明"],
    "老赵": ["老赵"],
    "我妈": ["我妈", "妈"],
    "阿磊": ["阿磊"],
    "老四": ["老四"],
    "阿华": ["阿华"],
    "老板娘": ["老板娘"],
}

LOCATION_PATTERNS = [
    "公司", "地铁", "便利店", "饺子店", "串串店", "咖啡馆", "商场",
    "餐厅", "楼下", "家", "医院", "工位", "会议室", "百货公司", "早点铺",
]

EMOTION_WORDS = {
    "烦": "烦",  "困": "困", "高兴": "高兴", "累": "累",
    "兴奋": "兴奋", "担心": "担心", "开心": "开心", "充实": "充实",
    "好": "满足", "压力": "压力大",
}

ACTIVITY_PATTERNS = [
    "开会", "吃饭", "吃串串", "吃饺子", "喝咖啡", "改提案", "发消息",
    "买菜", "洗衣服", "收拾房间", "看书", "坐地铁", "出门",
    "找老赵", "整理", "做饭", "炒菜",
]

# Common 2B model errors we inject in round 1
INJECTED_ERRORS = {
    # Error type → (trigger_text, bad entity)
    "time_as_location": ("七点半", {"type": "location", "name": "七点半", "evidence": "七点半"}),
    "vague_pronoun":    ("他", {"type": "person", "name": "他", "evidence": "他"}),
    "unanchored_decision": ("可能", {"type": "decision", "name": "可能回来", "evidence": "可能"}),
    "duplicate_person": None,  # handled inline
}

_inject_done: set[str] = set()  # track which errors already injected this run


def mock_clean(lines: list[str]) -> dict:
    """Remove obvious filler words, preserve [不清晰] and structure."""
    cleaned = []
    fillers = re.compile(r"^(嗯|啊|哦|那个|然后|就是说|对对对|好好好)$")
    for line in lines:
        stripped = line.strip()
        if fillers.match(stripped):
            cleaned.append("")
        else:
            # remove leading fillers
            stripped = re.sub(r"^(嗯|啊|哦|那个)+\s*", "", stripped)
            cleaned.append(stripped)
    return {"cleaned": cleaned}


def mock_segment(lines: list[str], start_idx: int) -> dict:
    """Segment by transition words and blank lines."""
    SIGNALS = ["然后", "后来", "下午", "晚上", "早上", "中午", "出来以后",
               "散会", "回家", "吃完", "到了", "回来", "到公司"]
    segments = []
    seg_start = start_idx
    seg_lines_so_far = []

    for i, line in enumerate(lines):
        abs_i = start_idx + i
        seg_lines_so_far.append(line)

        is_signal = any(s in line for s in SIGNALS) and len(seg_lines_so_far) >= 5
        is_too_long = len(seg_lines_so_far) >= 28

        if (is_signal or is_too_long) and i < len(lines) - 1:
            # derive topic hint from content
            hint = _extract_hint(seg_lines_so_far)
            segments.append({"start": seg_start, "end": abs_i, "topic_hint": hint})
            seg_start = abs_i + 1
            seg_lines_so_far = []

    # last segment
    if seg_lines_so_far:
        hint = _extract_hint(seg_lines_so_far)
        segments.append({
            "start": seg_start,
            "end": start_idx + len(lines) - 1,
            "topic_hint": hint
        })

    return {"segments": segments}


def _extract_hint(lines: list[str]) -> str:
    for line in lines:
        for act in ACTIVITY_PATTERNS:
            if act in line:
                return act
        for loc in LOCATION_PATTERNS:
            if loc in line:
                return f"在{loc}"
    return "日常"


def mock_extract(text: str, inject_errors: bool = True) -> dict:
    """Extract entities, optionally with realistic 2B mistakes."""
    entities = []
    seen_names: set[str] = set()

    # persons
    for canonical, patterns in KNOWN_PEOPLE.items():
        for p in patterns:
            if p in text and canonical not in seen_names:
                entities.append({"type": "person", "name": canonical, "evidence": p})
                seen_names.add(canonical)
                break

    # locations
    for loc in LOCATION_PATTERNS:
        if loc in text:
            entities.append({"type": "location", "name": loc, "evidence": loc})

    # activities
    for act in ACTIVITY_PATTERNS:
        if act in text:
            entities.append({"type": "activity", "name": act, "evidence": act})

    # emotions
    for word, label in EMOTION_WORDS.items():
        if word in text:
            entities.append({"type": "emotion", "name": label, "evidence": word})

    # decisions (look for 决定/打算/准备)
    for m in re.finditer(r"(决定|打算|准备|要去|要做)[^，。\n]{2,15}", text):
        entities.append({
            "type": "decision",
            "name": m.group(0)[:15],
            "evidence": m.group(0)
        })

    # questions
    for m in re.finditer(r"(不知道|不确定|不清楚)[^，。\n]{2,20}", text):
        entities.append({
            "type": "question",
            "name": m.group(0)[:20],
            "evidence": m.group(0)
        })

    # ── Inject realistic 2B errors ────────────────────────────────────
    if inject_errors:
        # Error 1: time word treated as location
        if "time_as_location" not in _inject_done:
            for tw in ["七点半", "三点", "十点", "九点", "下午两点"]:
                if tw in text:
                    entities.append({
                        "type": "location",
                        "name": tw,
                        "evidence": tw,
                    })
                    _inject_done.add("time_as_location")
                    break

        # Error 2: lone pronoun tagged as person
        if "vague_pronoun" not in _inject_done and "他说" in text:
            entities.append({"type": "person", "name": "他", "evidence": "他说"})
            _inject_done.add("vague_pronoun")

        # Error 3: unanchored decision (模糊意图)
        if "unanchored_decision" not in _inject_done:
            if "可能" in text and "decision" not in [e["type"] for e in entities]:
                entities.append({
                    "type": "decision",
                    "name": "可能回来",
                    "evidence": "可能",
                })
                _inject_done.add("unanchored_decision")

        # Error 4: missing emotion evidence (bare label, no word)
        if "no_evidence_emotion" not in _inject_done and "很好" in text:
            entities.append({
                "type": "emotion",
                "name": "良好",
                "evidence": "",   # ← empty evidence, should be caught by check 8
            })
            _inject_done.add("no_evidence_emotion")

    return {"entities": entities}


def mock_track_persons(persons: list[dict]) -> dict:
    """Simple alias grouping."""
    groups: dict[str, dict] = {}
    for p in persons:
        name = p["name"]
        if name in ("他", "她", "它"):
            # try to merge with most recent named person in same segment
            continue
        canon = name
        if canon not in groups:
            groups[canon] = {"canonical_name": canon, "aliases": [canon], "evidence": "相同名称"}
        else:
            if name not in groups[canon]["aliases"]:
                groups[canon]["aliases"].append(name)
    return {"groups": list(groups.values())}


def mock_reflect(text: str, entities: list[dict]) -> dict:
    """Check entity list against text, return realistic errors."""
    errors = []

    # check 1: missed persons
    for canonical, patterns in KNOWN_PEOPLE.items():
        mentioned = any(p in text for p in patterns)
        already_tagged = any(
            e["type"] == "person" and e["name"] == canonical
            for e in entities
        )
        if mentioned and not already_tagged:
            errors.append({"check_id": 1, "detail": f"遗漏person：{canonical}"})

    # check 2: time word as location
    for tw in ["七点半", "八点", "九点", "十点", "三点", "两点", "五点",
               "下午", "早上", "晚上"]:
        bad = [e for e in entities if e["type"] == "location" and e["name"] == tw]
        if bad:
            errors.append({"check_id": 2, "detail": f"时间词'{tw}'被错标为location"})

    # check 5: vague decisions
    for e in entities:
        if e["type"] == "decision":
            ev = e.get("evidence", "")
            vague = any(v in ev for v in ["可能", "也许", "不知道", "想一想"])
            if vague:
                errors.append({
                    "check_id": 5,
                    "detail": f"'{ev}'是不确定表达，不是已决定事项"
                })

    # check 7: lone pronouns
    for e in entities:
        if e["type"] == "person" and e["name"] in ("他", "她", "它"):
            errors.append({"check_id": 7, "detail": f"'{e['name']}'是模糊代词，不应作为独立person"})

    # check 8: empty evidence
    for e in entities:
        if not e.get("evidence", "").strip():
            errors.append({
                "check_id": 8,
                "detail": f"实体'{e['name']}'的evidence为空"
            })

    return {"pass": len(errors) == 0, "errors": errors}


# ── Dispatcher ────────────────────────────────────────────────────────────

def dispatch(prompt: str, system: str) -> Any:
    """Route to appropriate mock based on SKILL name in system prompt."""
    if "SKILL-清洗" in system:
        data = json.loads(prompt)
        return mock_clean(data["lines"])

    if "SKILL-分割" in system:
        data = json.loads(prompt)
        return mock_segment(data["lines"], data.get("line_start_idx", 0))

    if "SKILL-实体提取" in system:
        data = json.loads(prompt)
        # Inject errors only on first pass (before skill is patched)
        inject = "禁止把时间词" not in system  # if patched, fewer errors
        return mock_extract(data["text"], inject_errors=inject)

    if "SKILL-人物追踪" in system:
        data = json.loads(prompt)
        return mock_track_persons(data.get("persons", []))

    if "SKILL-反思" in system:
        data = json.loads(prompt)
        return mock_reflect(data["text"], data.get("entities", []))

    return {"error": "unmatched_skill", "system_prefix": system[:60]}
