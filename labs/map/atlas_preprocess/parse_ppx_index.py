#!/usr/bin/env python3
"""
解析 ppx/memect 输出的 doc.md 文件，提取谭其骧地图集地名索引。

ppx输出格式示例:
  高氏（春秋）24-25 ④4
  长安（战国）43-44 ③9
  上蔡郡（战国）45-46 ④4

策略：
  以圆圈数字（①-⑩）为锚点，向前扫描获取 atlas、时期、地名。
"""

import re
import json
import os
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_OUT_DIR    = os.path.join(_SCRIPT_DIR, "output")   # symlink
PPX_DIR     = os.path.join(_OUT_DIR, "ppx_output")
OUT_JSON    = os.path.join(_OUT_DIR, "place_index_ppx.json")

CIRCLED_DIGITS = {
    "①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5,
    "⑥": 6, "⑦": 7, "⑧": 8, "⑨": 9, "⑩": 10,
}
CIRCLED_PAT = "[①②③④⑤⑥⑦⑧⑨⑩]"

PERIOD_KEYWORDS = {
    "夏": "Xia", "商": "Shang", "西周": "W_Zhou", "周": "W_Zhou",
    "春秋": "Spring_Autumn", "战国": "Warring_States", "先秦": "pre_Qin",
    "秦": "Qin", "西汉": "W_Han", "汉": "W_Han", "东汉": "E_Han",
    "两汉": "Both_Han",
}
# Longest period match first
PERIOD_RE = re.compile(r"(春秋|战国|西周|两汉|东汉|西汉|夏|商|周|秦|汉)")

# Atlas page: number(-|·|.)number, with possible backslash-escaped dashes
ATLAS_RE = re.compile(r"(\d{1,2})(?:\\?[-·.]|—)(\d{1,2})")
# Fallback: adjacent atlas page numbers with no dash (e.g. "3940" = "39-40")
# Match two adjacent 1-2 digit numbers that differ by 1 (validated in code)
ATLAS_NODASH_RE = re.compile(r"(\d{1,2})(\d{2})\b")

# Coordinate patterns:
#   circled_digit + optional brackets + col digit (vol1 main format)
#   （plain_digit）col_digit  (vol2 parenthesized format)
COORD_RE = re.compile(
    r"(?:"
    # pattern A: circled digit + col digit
    + r"[（(]?(" + CIRCLED_PAT + r")[）)（(]?\s*(\d{1,2})"
    # pattern B: (plain digit) col — parenthesized row 1-9
    + r"|[（(]([1-9])[）)]\s*(\d{1,2})"
    + r")"
)


def clean_text(text: str) -> str:
    """Remove markdown artifacts and normalize separators."""
    # Remove markdown escape backslashes before dashes
    text = text.replace("\\-", "-")
    text = text.replace("\\.", ".")
    # Replace full-width chars
    text = text.replace("·", "-").replace("—", "-").replace("–", "-")
    return text


def extract_entries_from_page(text: str, vol: str, source_name: str) -> list:
    """
    Extract place-name index entries from a single ppx doc.md page.
    Strategy: find each COORD (circled_digit + col), then scan backwards
    in tight windows: atlas within 30 chars, period within 60 chars before atlas,
    place name within 40 chars before period.
    """
    text = clean_text(text)
    entries = []

    for coord_m in COORD_RE.finditer(text):
        pos = coord_m.start()
        if coord_m.group(1):  # pattern A: circled digit
            row_char = coord_m.group(1)
            col_raw = coord_m.group(2)
            row = CIRCLED_DIGITS[row_char]
        else:                  # pattern B: parenthesized plain digit
            row = int(coord_m.group(3))
            col_raw = coord_m.group(4)

        # Accept col as-is if <= 12; if > 12, try the first digit only
        col = int(col_raw)
        if col > 12:
            if int(col_raw[0]) >= 1:
                col = int(col_raw[0])
            else:
                continue

        # Atlas: search in 30-char window immediately before coordinate
        atlas_win = text[max(0, pos - 30):pos]
        atlas_matches = list(ATLAS_RE.finditer(atlas_win))
        if atlas_matches:
            atlas_m = atlas_matches[-1]
            a1r, a2r = int(atlas_m.group(1)), int(atlas_m.group(2))
        else:
            # Fallback: look for adjacent page pair with no dash (e.g. "3940")
            nd_matches = list(ATLAS_NODASH_RE.finditer(atlas_win))
            found = False
            for m in reversed(nd_matches):
                a1t = int(m.group(1) + m.group(2)[:1])  # try parsing differently
                # More direct: concatenated string, try all splits
                s = m.group(0)
                # Try: first digit(s) + last two digits
                for split in range(1, len(s)):
                    a1t = int(s[:split])
                    a2t = int(s[split:])
                    if 1 <= a1t <= 70 and a2t == a1t + 1:
                        a1r, a2r = a1t, a2t
                        found = True
                        break
                if found:
                    atlas_m = m
                    break
            if not found:
                continue
        # Fix OCR truncation: "43-4" should be "43-44", "22-2" → "22-23"
        if a2r < a1r:
            a2_completed = (a1r // 10) * 10 + a2r
            if a2_completed > a1r:
                a2r = a2_completed
            else:
                continue  # can't fix
        atlas = f"{a1r}-{a2r}"
        atlas_abs = max(0, pos - 30) + atlas_m.start()

        # Period: search in 60-char window before atlas
        period_win = text[max(0, atlas_abs - 60):atlas_abs]
        period_matches = list(PERIOD_RE.finditer(period_win))
        if not period_matches:
            continue
        period_m = period_matches[-1]
        period = period_m.group(1)
        period_en = PERIOD_KEYWORDS.get(period, period)
        period_abs = max(0, atlas_abs - 60) + period_m.start()

        # Place name: last CJK sequence in 40-char window before period
        name_win = text[max(0, period_abs - 40):period_abs]
        name_win_clean = re.sub(r"[\d\s:：.;；！？\[\]（）()\-\\△~▲◆　]", " ", name_win)
        name_matches = list(re.finditer(r"[一-鿿㐀-䶿]{1,12}", name_win_clean))
        if not name_matches:
            continue
        name = name_matches[-1].group()
        # Strip trailing period keywords from name (OCR noise)
        for pk in sorted(PERIOD_KEYWORDS.keys(), key=len, reverse=True):
            if name.endswith(pk) and len(name) > len(pk):
                name = name[:-len(pk)]
                break
        # Filter: name must be at least 2 chars and not a period keyword itself
        if len(name) < 2 or name in PERIOD_KEYWORDS:
            continue
        # Filter: atlas page pair must be adjacent (differ 1-3)
        if a2r <= a1r or (a2r - a1r) > 3 or a1r < 1 or a2r > 120:
            continue

        entries.append({
            "name": name,
            "period": period,
            "period_en": period_en,
            "atlas": atlas,
            "row": row,
            "col": col,
            "vol": vol,
            "source_file": source_name,
        })

    return entries


def parse_all_ppx_output() -> list:
    all_entries = []
    out_dirs = sorted(Path(PPX_DIR).iterdir())

    for out_dir in out_dirs:
        if not out_dir.is_dir():
            continue
        md_path = out_dir / "doc.md"
        if not md_path.exists():
            continue

        stem = out_dir.name  # e.g. vol1_p077.png.out
        vol = "vol1" if "vol1" in stem else "vol2"

        text = md_path.read_text(encoding="utf-8")
        entries = extract_entries_from_page(text, vol, stem)
        all_entries.extend(entries)
        print(f"  {stem}: {len(entries)} 条")

    return all_entries


def save_index_json(entries: list) -> None:
    entries_sorted = sorted(entries, key=lambda e: e["name"])

    place_map: dict = {}
    for e in entries_sorted:
        name = e["name"]
        if name not in place_map:
            place_map[name] = []
        place_map[name].append({
            "period": e["period"],
            "atlas": e["atlas"],
            "row": e["row"],
            "col": e["col"],
            "vol": e["vol"],
        })

    # Deduplicate within each place
    for name in place_map:
        seen = set()
        deduped = []
        for loc in place_map[name]:
            key = (loc["period"], loc["atlas"], loc["row"], loc["col"])
            if key not in seen:
                seen.add(key)
                deduped.append(loc)
        place_map[name] = deduped

    output = {
        "total_entries": len(entries_sorted),
        "total_places": len(place_map),
        "entries": entries_sorted,
        "place_map": place_map,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 索引 JSON → {OUT_JSON}")
    print(f"  共 {len(entries_sorted)} 条，{len(place_map)} 个地名")


if __name__ == "__main__":
    print("解析 ppx OCR 输出...")
    entries = parse_all_ppx_output()
    print(f"\n合计 {len(entries)} 条原始条目")
    if entries:
        save_index_json(entries)
        # Print sample
        print("\n前10条样本：")
        for e in entries[:10]:
            print(f"  {e['name']}（{e['period']}）{e['atlas']} ←row{e['row']} col{e['col']}")
