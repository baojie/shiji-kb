#!/usr/bin/env python3
"""
对 place_index_ppx.json 进行反思纠错。

已发现的错误规律：
1. 图幅编号 OCR 偏移（19-20 vol1 → 20-21；42-44 vol2 → 42-43；19-21 → 19-20；6-7 → 7-8）
2. 超长名称（多条合并）→ 截取第一个有效分词
3. 名称末尾噪声字符（"汉水一"→"汉水"，"秦岭山心"→"秦岭山"）
4. 图幅差值过大（35-38, 79-80）→ 删除
5. 完全无法确定正确值（4-5）→ 删除
6. 时期-图幅不兼容（春秋/战国条目出现在夏/商图幅上）→ 删除
7. 同地名同时期同图幅重复坐标（OCR重复提取）→ 每组只保留第一条
"""

import json
import re
from pathlib import Path

_OUT_DIR = Path(__file__).parent / "output"   # symlink
IN_JSON  = str(_OUT_DIR / "place_index_ppx.json")
OUT_JSON = str(_OUT_DIR / "place_index_corrected.json")

# ── 从 manifest 加载有效图幅集 ──────────────────────────────────────────
def load_valid_atlas():
    valid = {}
    for vol, fname in [("vol1", "vol1_先秦_manifest.json"), ("vol2", "vol2_秦汉_manifest.json")]:
        mf = json.load(open(_OUT_DIR / fname, encoding="utf-8"))
        valid[vol] = set(m["atlas"] for m in mf)
    return valid

VALID_ATLAS = load_valid_atlas()

# ── 时期-图幅兼容性检查 ────────────────────────────────────────────────────
# 春秋/战国条目不应出现在夏/商图幅（这些地名在夏商时代尚不存在）
# 反之（夏/商条目在春秋/战国图幅上）是合法的历史注记，不删除
LATER_PERIOD_ON_EARLY_MAP = {
    "vol1": {
        "春秋": {"9-10", "11-12", "13-14"},   # 夏/商时期地图
        "战国": {"9-10", "11-12", "13-14"},   # 夏/商时期地图
    }
}

# ── 图幅修正规则 ─────────────────────────────────────────────────────────
# 格式：(vol, wrong_atlas) → (correct_atlas | None=删除)
ATLAS_FIX = {
    ("vol1", "19-20"): "20-21",    # vol1 无 19-20，最近邻 20-21
    ("vol2", "42-44"): "42-43",    # vol2 有 42-43，差值2→1
    ("vol2", "19-21"): "19-20",    # 多了个 1
    ("vol2", "6-7"):   "7-8",      # 偏移1
    ("vol1", "35-38"): None,       # 无法确定是 35-36 还是 37-38
    ("vol2", "79-80"): None,       # 完全无效
    ("vol2", "4-5"):   None,       # 无法确定 3-4 还是 5-6
}

# ── 名称清理规则 ─────────────────────────────────────────────────────────
# 末尾单字噪声（数字、标点、孤立单字）
TRAILING_NOISE_RE = re.compile(r"[一一]$")   # 孤立"一"尾缀
LONG_NAME_RE = re.compile(r"^([一-鿿㐀-䶿]{2,6})")  # 超长名取前6字前缀

# 已知应截断的名称
KNOWN_TRUNCATE = {
    "医无间山于微间": "医无间山",
    "能开获舆山人":   None,   # 完全乱码 → 删除
    "艇美遗遗之门":   None,
    "黄笼果灵制渠":   None,
    "汉水一":         "汉水",
    "秦岭山心":       "秦岭山",
    "人野泽一":       "人野泽",
    "高是山心":       None,   # OCR乱码 → 删除（末尾"心"无法修复）
    "青农水一东":     None,   # 乱码，"青农水"无意义 → 删除
    "武城东武城":     "武城", # 消歧注记被并入名称 → 截短
    "一部":           None,   # 索引章节标题，非地名 → 删除
}


def clean_name(name: str) -> str | None:
    # 直接映射
    if name in KNOWN_TRUNCATE:
        return KNOWN_TRUNCATE[name]
    # 末尾单字噪声
    name = TRAILING_NOISE_RE.sub("", name)
    # 超长（>6字）：截取前6字
    if len(name) > 6:
        m = LONG_NAME_RE.match(name)
        if m:
            name = m.group(1)
        else:
            return None
    return name if len(name) >= 2 else None


def fix_entry(e: dict) -> dict | None:
    """返回修正后的条目，None 表示删除。"""
    e = dict(e)
    vol, atlas = e["vol"], e["atlas"]
    valid = VALID_ATLAS[vol]

    # 1. 图幅修正
    if atlas not in valid:
        key = (vol, atlas)
        if key in ATLAS_FIX:
            corrected = ATLAS_FIX[key]
            if corrected is None:
                return None
            e["atlas"] = corrected
            e["note"] = e.get("note", []) + [f"atlas_corrected:{atlas}→{corrected}"]
        else:
            return None   # 未知错误 → 删除

    # 2. 名称清理
    name = clean_name(e["name"])
    if name is None:
        return None
    if name != e["name"]:
        e["note"] = e.get("note", []) + [f"name_cleaned:{e['name']}→{name}"]
        e["name"] = name

    # 3. 时期-图幅兼容性
    bad_atlases = LATER_PERIOD_ON_EARLY_MAP.get(vol, {}).get(e["period"], set())
    if e["atlas"] in bad_atlases:
        return None

    # 4. col 范围（保守上限 12）
    if e["col"] > 12 or e["col"] < 1:
        return None
    if e["row"] > 10 or e["row"] < 1:
        return None

    return e


def run():
    data = json.load(open(IN_JSON, encoding="utf-8"))
    orig_entries = data["entries"]

    fixed_entries = []
    removed = 0
    corrected_atlas = 0
    corrected_name = 0

    for e in orig_entries:
        fe = fix_entry(e)
        if fe is None:
            removed += 1
        else:
            if "note" in fe:
                for n in fe["note"]:
                    if n.startswith("atlas_corrected"):
                        corrected_atlas += 1
                    if n.startswith("name_cleaned"):
                        corrected_name += 1
            fixed_entries.append(fe)

    # ── 同地名同时期同图幅去重（只保留第一条，其余为 OCR 重复提取）──────────
    dedup_seen: set = set()
    deduped_entries = []
    coord_dedup_removed = 0
    for e in fixed_entries:
        key = (e["name"], e["period"], e["atlas"], e["vol"])
        if key not in dedup_seen:
            dedup_seen.add(key)
            deduped_entries.append(e)
        else:
            coord_dedup_removed += 1
    fixed_entries = deduped_entries

    # 重建 place_map
    place_map: dict = {}
    for e in fixed_entries:
        name = e["name"]
        if name not in place_map:
            place_map[name] = []
        loc = {k: e[k] for k in ["period", "atlas", "row", "col", "vol"]}
        place_map[name].append(loc)

    # 去重（含 vol，防止不同册的同名同坐标条目重复）
    for name in place_map:
        seen = set()
        deduped = []
        for loc in place_map[name]:
            key = (loc["vol"], loc["period"], loc["atlas"], loc["row"], loc["col"])
            if key not in seen:
                seen.add(key)
                deduped.append(loc)
        place_map[name] = deduped

    output = {
        "total_entries": len(fixed_entries),
        "total_places": len(place_map),
        "entries": fixed_entries,
        "place_map": place_map,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"原始条目:     {len(orig_entries)}")
    print(f"删除:         {removed}")
    print(f"坐标去重删除: {coord_dedup_removed}")
    print(f"图幅修正:     {corrected_atlas}")
    print(f"名称修正:     {corrected_name}")
    print(f"最终条目:     {len(fixed_entries)}")
    print(f"唯一地名:     {len(place_map)}")
    print(f"✓ 输出 → {OUT_JSON}")


if __name__ == "__main__":
    run()
