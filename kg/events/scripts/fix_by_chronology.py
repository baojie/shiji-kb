#!/usr/bin/env python3
"""
用《中国历史大事年表》交叉修正事件索引中的年份标注。

注意：本脚本处理事件索引文件（kg/events/data/），这些文件使用 v2.1 格式
（〖@person〗, 〖;official〗, 〖%time〗 等 〖TYPE content〗 格式）。

策略：
1. 从年表提取：人物→活跃年份列表、特征事件→年份
2. 从person_lifespans.json获取人物生卒年
3. 对每个塌缩章节，综合以上信息为每个事件推断合理年份
4. 同时修改概览表和详情部分

用法：
    python fix_by_chronology.py --dry-run       # 仅报告
    python fix_by_chronology.py                  # 执行修改
    python fix_by_chronology.py 039 070          # 只处理指定章节
"""

import os
import re
import json
import sys
import glob
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EVENTS_DIR = os.path.join(BASE_DIR, "kg", "events", "data")
CHRONOLOGY = os.path.join(BASE_DIR, "kg", "chronology", "data", "中国历史大事年表.md")
LIFESPAN_FILE = os.path.join(BASE_DIR, "kg", "entities", "data", "person_lifespans.json")

# 章节大致时代范围（BCE），用于过滤不合理的匹配
CHAPTER_ERA = {
    "001": (3000, 2100), "002": (2200, 1600), "003": (1600, 1046), "004": (1100, 256),
    "005": (900, 207), "006": (259, 207), "007": (232, 202), "008": (256, 195),
    "009": (241, 180), "010": (203, 157), "011": (188, 141), "012": (156, 87),
    "013": (3000, 800), "014": (900, 450), "015": (500, 207), "016": (209, 202),
    "023": (3000, 100), "024": (3000, 100), "025": (3000, 100), "026": (3000, 100),
    "027": (3000, 100), "028": (3000, 87), "029": (3000, 87), "030": (200, 87),
    "031": (1100, 450), "032": (1100, 380), "033": (1100, 250), "034": (1100, 222),
    "035": (1100, 400), "036": (1100, 400), "037": (1100, 250), "038": (1100, 280),
    "039": (1100, 350), "040": (1100, 220), "041": (600, 300), "042": (800, 375),
    "043": (500, 222), "044": (500, 222), "045": (500, 230), "046": (700, 222),
    "047": (551, 479), "048": (240, 208), "049": (250, 100), "050": (220, 130),
    "051": (220, 150), "052": (220, 130), "053": (260, 193), "054": (260, 190),
    "055": (260, 186), "056": (250, 178), "057": (250, 160), "058": (200, 130),
    "059": (200, 100), "060": (150, 87), "061": (1100, 1000), "062": (750, 500),
    "063": (600, 230), "064": (600, 450), "065": (550, 370), "066": (600, 470),
    "067": (551, 400), "068": (400, 338), "069": (400, 280), "070": (400, 300),
    "081": (330, 230), "082": (320, 260), "083": (300, 150), "084": (340, 168),
    "085": (300, 208), "086": (600, 222), "087": (284, 208), "088": (260, 210),
    "089": (270, 200), "090": (240, 196), "091": (240, 196), "092": (240, 196),
    "093": (240, 195), "094": (240, 200), "095": (260, 170), "096": (260, 150),
    "097": (260, 170), "098": (260, 190), "099": (260, 190), "100": (250, 160),
    "101": (220, 140), "102": (220, 140), "103": (220, 100), "104": (220, 100),
    "105": (500, 150), "106": (220, 154), "107": (200, 130), "108": (200, 120),
    "109": (200, 100), "110": (300, 87), "111": (180, 100), "112": (180, 100),
    "113": (220, 87), "114": (220, 87), "115": (200, 87), "116": (200, 87),
    "117": (180, 117), "118": (200, 120), "119": (600, 100), "120": (200, 100),
    "121": (551, 87), "122": (200, 87), "123": (200, 87), "124": (200, 87),
    "125": (200, 87), "126": (500, 87), "127": (200, 87), "128": (3000, 87),
    "129": (800, 87), "130": (200, 87),
}


# ============================================================
# 从年表提取人物活跃年份
# ============================================================

def parse_chronology():
    """解析年表，返回：
    - person_years: {人名: [year_bce, ...]}  人物出现的年份
    - event_map: {关键词: [(year_bce, context), ...]}  事件的所有出现年份
    """
    with open(CHRONOLOGY, "r", encoding="utf-8") as f:
        content = f.read()

    person_years = defaultdict(list)
    event_map = defaultdict(list)

    non_names = {
        "是年", "此后", "从此", "因此", "匈奴", "南越", "东越", "西域",
        "不久", "其后", "当时", "朝鲜", "大宛", "月氏", "乌孙", "百越",
        "天下", "中原", "诸侯", "太子", "丞相", "将军", "大夫", "上卿",
        "同年", "次年", "前后", "左右", "以后", "以前", "之后", "之前",
        "自此", "于是", "所以", "然而", "虽然", "如果", "但是", "而且",
        "已经", "可能", "应该", "据说", "相传", "传说", "其中", "其他",
        "公子", "世子", "夫人", "王后", "皇后", "太后", "天子", "大王",
        "司马", "左传", "国语", "春秋", "竹书", "史记",
    }

    year_pattern = re.compile(r"^### 前(\d+)年", re.MULTILINE)
    matches = list(year_pattern.finditer(content))

    for i, m in enumerate(matches):
        year_bce = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        text = content[start:end].strip()
        if not text:
            continue

        # 提取特征事件（4字以上，更可靠）
        for pat in [
            r"([\u4e00-\u9fff]{2,8}之战)", r"([\u4e00-\u9fff]{2,6}之盟)",
            r"([\u4e00-\u9fff]{2,6}之围)", r"([\u4e00-\u9fff]{2,6}之祸)",
            r"([\u4e00-\u9fff]{2,6}之变)", r"([\u4e00-\u9fff]{2,6}之乱)",
            r"(三家分晋)", r"(共和行政)", r"(商鞅变法)", r"(胡服骑射)",
            r"(焚书坑儒)", r"(大泽乡起义)", r"(沙丘之变)", r"(沙丘之乱)",
        ]:
            for pm in re.finditer(pat, text):
                kw = pm.group(1)
                event_map[kw].append(year_bce)

        # 提取人名
        name_patterns = [
            r"([\u4e00-\u9fff]{2,4})(?:死|卒|自杀|被杀|病死|崩|薨)",
            r"([\u4e00-\u9fff]{2,4})(?:立|即位|践位|嗣位)",
            r"([\u4e00-\u9fff]{2,4})(?:伐|攻|破|灭|败|围|取|克|战)",
            r"([\u4e00-\u9fff]{2,4})(?:相|将|帅|率|领|守|治)",
            r"([\u4e00-\u9fff]{2,4})(?:奔|逃|出奔|出走|流亡|归|返)",
            r"([\u4e00-\u9fff]{2,4})(?:谏|谮|请|说|言|对)",
            r"(?:以|封|拜|任)([\u4e00-\u9fff]{2,4})(?:为)",
        ]

        for pat in name_patterns:
            for pm in re.finditer(pat, text):
                name = pm.group(1)
                if len(name) >= 2 and name not in non_names:
                    person_years[name].append(year_bce)

    # 去重并排序
    for name in person_years:
        person_years[name] = sorted(set(person_years[name]), reverse=True)
    for kw in event_map:
        event_map[kw] = sorted(set(event_map[kw]), reverse=True)

    return person_years, event_map


def load_lifespans():
    if not os.path.exists(LIFESPAN_FILE):
        return {}
    with open(LIFESPAN_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    persons = raw.get("persons", raw)
    result = {}
    for name, info in persons.items():
        if name.startswith("_"):
            continue
        entry = {}
        if "birth" in info and info["birth"]:
            entry["birth_bce"] = abs(info["birth"])
        elif "birth_bce" in info:
            entry["birth_bce"] = info["birth_bce"]
        if "death" in info and info["death"]:
            entry["death_bce"] = abs(info["death"])
        elif "death_bce" in info:
            entry["death_bce"] = info["death_bce"]
        if entry:
            result[name] = entry
    return result


# ============================================================
# 解析事件索引
# ============================================================

def parse_overview_table(content):
    events = []
    table_pattern = re.compile(
        r"\|\s*([\d-]+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|"
    )
    for m in table_pattern.finditer(content):
        event_id = m.group(1).strip()
        event_name = m.group(2).strip()
        time_str = m.group(4).strip()
        if event_id == "事件ID" or not re.match(r"\d{3}-\d{3}", event_id):
            continue
        year_bce = None
        year_type = None
        precise = re.search(r"（公元前(\d+)年）", time_str)
        if precise:
            year_bce = int(precise.group(1))
            year_type = "precise"
        inferred = re.search(r"\[约公元前(\d+)年\]", time_str)
        if inferred and year_bce is None:
            year_bce = int(inferred.group(1))
            year_type = "inferred"
        persons = re.findall(r"〖@([^〖〗\n]+)〗", m.group(0))
        # 也提取〖;人名〗格式（官职/称号中的人名）
        persons += re.findall(r"〖;([^〖〗\n]+)〗", m.group(0))
        # 去重
        persons = list(dict.fromkeys(persons))
        events.append({
            "id": event_id, "name": event_name,
            "year_bce": year_bce, "year_type": year_type,
            "persons": persons,
        })
    return events


def detect_collapse(events):
    from collections import Counter
    inferred = [(i, e) for i, e in enumerate(events)
                if e.get("year_type") == "inferred" and e.get("year_bce")]
    if len(inferred) < 4:
        return None
    years = [e["year_bce"] for _, e in inferred]
    counter = Counter(years)
    most_common, count = counter.most_common(1)[0]
    if count / len(inferred) > 0.5:
        affected = [(i, e) for i, e in inferred if e["year_bce"] == most_common]
        return most_common, affected
    return None


# ============================================================
# 推断年份
# ============================================================

def infer_year(event, person_years_db, event_map, lifespans, chapter_events, chapter_id):
    """为事件推断年份。返回 (new_year, reason) 或 None"""
    event_name = event["name"]
    persons = event.get("persons", [])
    era = CHAPTER_ERA.get(chapter_id, (3000, 87))
    era_early, era_late = era

    def in_era(year, margin=50):
        return (era_late - margin) <= year <= (era_early + margin)

    # 策略1: 特征事件名匹配（要求年份在章节时代范围内）
    for kw, years in event_map.items():
        if len(kw) >= 3 and kw in event_name:  # 至少3字匹配
            # 找时代范围内的最佳匹配
            valid_years = [y for y in years if in_era(y)]
            if valid_years:
                best = valid_years[0]  # 取最早的（BCE最大）
                return best, f"年表事件匹配：{kw}=前{best}年"

    # 策略2: 死亡事件取人物去世年
    is_death = bool(re.search(r"崩|卒|死|薨|自杀|被杀|饿死", event_name))
    if is_death and persons:
        for p in persons[:2]:  # 前两个人物
            if p in lifespans and lifespans[p].get("death_bce"):
                year = lifespans[p]["death_bce"]
                if in_era(year):
                    return year, f"取{p}去世年（前{year}年）"

    # 策略3: 人物在年表中的活跃年份
    all_active = []
    matched_person = None
    for p in persons:
        if p in person_years_db:
            p_years = [y for y in person_years_db[p] if in_era(y)]
            if p_years:
                all_active.extend(p_years)
                if matched_person is None:
                    matched_person = p

    if all_active:
        sorted_years = sorted(all_active, reverse=True)
        # 取中位数
        median = sorted_years[len(sorted_years) // 2]
        return median, f"年表{matched_person}活跃中位年：前{median}年（{len(sorted_years)}条）"

    # 策略4: 人物生卒年
    if persons:
        for p in persons:
            if p in lifespans:
                ls = lifespans[p]
                b = ls.get("birth_bce")
                d = ls.get("death_bce")
                if b and d and in_era(b) and in_era(d):
                    mid = (b + d) // 2
                    return mid, f"{p}生卒中点：前{mid}年"
                elif d and in_era(d):
                    active = d + 15
                    if in_era(active):
                        return active, f"{p}去世前约15年活跃"

    # 策略5: 章节内线性插值（利用精确事件和已知不同年份的推断事件）
    anchors = [(i, e) for i, e in enumerate(chapter_events)
               if e.get("year_bce") and e.get("year_type") == "precise"]

    event_idx = next((i for i, e in enumerate(chapter_events) if e["id"] == event["id"]), None)
    if event_idx is not None and len(anchors) >= 2:
        before = [(i, e) for i, e in anchors if i < event_idx]
        after = [(i, e) for i, e in anchors if i > event_idx]

        if before and after:
            pi, pe = before[-1]
            ni, ne = after[0]
            span = ni - pi
            offset = event_idx - pi
            year_span = pe["year_bce"] - ne["year_bce"]
            if span > 0 and year_span > 0:
                interp = pe["year_bce"] - int(year_span * offset / span)
                if in_era(interp):
                    return interp, f"插值：{pe['id']}(前{pe['year_bce']}年)→{ne['id']}(前{ne['year_bce']}年)"
        elif before:
            _, pe = before[-1]
            if in_era(pe["year_bce"]):
                return pe["year_bce"], f"取前方锚点{pe['id']}(前{pe['year_bce']}年)"
        elif after:
            _, ne = after[0]
            if in_era(ne["year_bce"]):
                return ne["year_bce"], f"取后方锚点{ne['id']}(前{ne['year_bce']}年)"

    return None


# ============================================================
# 两轮推断：先推断有直接证据的，再用已推断结果作为新锚点
# ============================================================

def infer_all(events, person_years_db, event_map, lifespans, chapter_id):
    """两轮推断：第一轮用年表匹配，第二轮用已推断结果插值"""
    collapsed = detect_collapse(events)
    if not collapsed:
        return []

    collapsed_year, affected = collapsed
    affected_ids = {e["id"] for _, e in affected}

    # 第一轮：直接推断
    fixes_round1 = []
    for idx, event in affected:
        result = infer_year(event, person_years_db, event_map, lifespans, events, chapter_id)
        if result:
            new_year, reason = result
            if abs(new_year - event["year_bce"]) > 5:
                if 87 <= new_year <= 3000:
                    fixes_round1.append((idx, event["id"], event["year_bce"], new_year, reason))

    # 将第一轮结果注入events列表，作为第二轮的锚点
    events_copy = [dict(e) for e in events]
    for idx, eid, old, new, reason in fixes_round1:
        events_copy[idx]["year_bce"] = new
        events_copy[idx]["year_type"] = "inferred_fixed"

    # 第二轮：用更新后的事件列表做插值
    # 找到还没被修正的塌缩事件
    fixed_ids = {eid for _, eid, _, _, _ in fixes_round1}
    remaining = [(idx, e) for idx, e in affected if e["id"] not in fixed_ids]

    fixes_round2 = []
    for idx, event in remaining:
        # 用更新后的事件列表找前后锚点
        # 找前后最近的非塌缩年份事件
        before_anchor = None
        after_anchor = None

        for i in range(idx - 1, -1, -1):
            ec = events_copy[i]
            if ec.get("year_bce") and ec["year_bce"] != collapsed_year:
                before_anchor = (i, ec)
                break

        for i in range(idx + 1, len(events_copy)):
            ec = events_copy[i]
            if ec.get("year_bce") and ec["year_bce"] != collapsed_year:
                after_anchor = (i, ec)
                break

        era = CHAPTER_ERA.get(chapter_id, (3000, 87))
        era_early, era_late = era

        if before_anchor and after_anchor:
            pi, pe = before_anchor
            ni, ne = after_anchor
            # 检查锚点本身是否在时代范围内
            if not (era_late - 50 <= pe["year_bce"] <= era_early + 50):
                continue
            if not (era_late - 50 <= ne["year_bce"] <= era_early + 50):
                continue
            span = ni - pi
            offset = idx - pi
            year_span = pe["year_bce"] - ne["year_bce"]
            if span > 0:
                interp = pe["year_bce"] - int(year_span * offset / span)
                if era_late - 50 <= interp <= era_early + 50 and abs(interp - event["year_bce"]) > 5:
                    fixes_round2.append((idx, event["id"], event["year_bce"], interp,
                        f"二轮插值：{pe['id']}(前{pe['year_bce']}年)→{ne['id']}(前{ne['year_bce']}年)"))
        elif before_anchor:
            _, pe = before_anchor
            if not (era_late - 50 <= pe["year_bce"] <= era_early + 50):
                continue
            if abs(pe["year_bce"] - event["year_bce"]) > 5:
                fixes_round2.append((idx, event["id"], event["year_bce"], pe["year_bce"],
                    f"二轮取前锚{pe['id']}(前{pe['year_bce']}年)"))
        elif after_anchor:
            _, ne = after_anchor
            if not (era_late - 50 <= ne["year_bce"] <= era_early + 50):
                continue
            if abs(ne["year_bce"] - event["year_bce"]) > 5:
                fixes_round2.append((idx, event["id"], event["year_bce"], ne["year_bce"],
                    f"二轮取后锚{ne['id']}(前{ne['year_bce']}年)"))

    all_fixes = [(eid, old, new, reason) for _, eid, old, new, reason in fixes_round1 + fixes_round2]
    return all_fixes


# ============================================================
# 应用修正
# ============================================================

def apply_fixes(content, fixes):
    for event_id, old_year, new_year, reason in fixes:
        old_inferred = f"[约公元前{old_year}年]"
        new_inferred = f"[约公元前{new_year}年]"

        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if event_id in line:
                line = line.replace(old_inferred, new_inferred)
            new_lines.append(line)
        content = "\n".join(new_lines)

        detail_pattern = re.compile(
            rf"(### {re.escape(event_id)}\s+.+?\n(?:.*?\n)*?)(?=### \d{{3}}-\d{{3}}|\Z)",
            re.DOTALL
        )
        m = detail_pattern.search(content)
        if m:
            block = m.group(1)
            if "**年代推断**" in block:
                block = re.sub(
                    r"- \*\*年代推断\*\*:.*",
                    f"- **年代推断**: {reason}",
                    block
                )
            else:
                block = block.rstrip() + f"\n- **年代推断**: {reason}\n"
            content = content[:m.start()] + block + content[m.end():]

    return content


# ============================================================
# 主函数
# ============================================================

def main():
    dry_run = "--dry-run" in sys.argv
    target_chapters = [a.zfill(3) for a in sys.argv[1:] if a != "--dry-run"]

    print("解析年表...")
    person_years_db, event_map = parse_chronology()
    lifespans = load_lifespans()
    print(f"  年表人物：{len(person_years_db)}个，特征事件：{len(event_map)}个，生卒数据：{len(lifespans)}个")

    print(f"\n  特征事件（前15个）：")
    for kw in sorted(event_map.keys())[:15]:
        years = event_map[kw]
        print(f"    {kw}: {', '.join(f'前{y}年' for y in years)}")

    paths = sorted(glob.glob(os.path.join(EVENTS_DIR, "*_事件索引.md")))
    total_fixes = 0
    total_chapters = 0

    for path in paths:
        fname = os.path.basename(path).replace("_事件索引.md", "")
        chapter_id = fname.split("_")[0]

        if target_chapters and chapter_id not in target_chapters:
            continue

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        events = parse_overview_table(content)
        if not events:
            continue

        fixes = infer_all(events, person_years_db, event_map, lifespans, chapter_id)

        if fixes:
            collapse = detect_collapse(events)
            collapsed_year = collapse[0] if collapse else "?"
            affected_count = len(collapse[1]) if collapse else "?"
            total_chapters += 1
            print(f"\n{fname}: 塌缩到前{collapsed_year}年，修正{len(fixes)}/{affected_count}个事件")
            for eid, old, new, reason in fixes:
                print(f"  {eid}: 前{old}年 → 前{new}年 ({reason})")

            if not dry_run:
                content = apply_fixes(content, fixes)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  ✓ 已写入")

            total_fixes += len(fixes)

    print(f"\n{'='*60}")
    print(f"总计：{total_chapters}章、{total_fixes}个事件" + (" (dry-run)" if dry_run else ""))


if __name__ == "__main__":
    main()
