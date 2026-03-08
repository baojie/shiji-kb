#!/usr/bin/env python3
"""
批量修正事件索引中"单锚点塌缩"导致的年份错误。

修正策略：
1. 读取 reign_periods.json 和 person_lifespans.json
2. 对每个事件，通过事件中的人物和原文线索推断合理年份
3. 同时更新概览表和详情部分

用法：
    python batch_fix_collapsed_dates.py --dry-run    # 仅报告，不修改
    python batch_fix_collapsed_dates.py              # 执行修改
    python batch_fix_collapsed_dates.py 039 070      # 只处理指定章节
"""

import os
import re
import json
import sys
import glob
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EVENTS_DIR = os.path.join(BASE_DIR, "kg", "events", "data")
REIGN_FILE = os.path.join(BASE_DIR, "kg", "chronology", "data", "reign_periods.json")
LIFESPAN_FILE = os.path.join(BASE_DIR, "kg", "entities", "data", "person_lifespans.json")

# ============================================================
# 加载参考数据
# ============================================================

def load_reign_periods():
    with open(REIGN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("rulers", {}), data.get("eras", {}), data.get("aliases", {})

def load_lifespans():
    if not os.path.exists(LIFESPAN_FILE):
        return {}
    with open(LIFESPAN_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # 兼容两种格式：
    # 格式A: {"persons": {"黄帝": {"birth": -2717, "death": -2599}}}
    # 格式B: {"黄帝": {"birth_bce": 2717, "death_bce": 2599}}
    persons = raw.get("persons", raw)
    result = {}
    for name, info in persons.items():
        if name.startswith("_"):
            continue
        entry = {}
        if "birth_bce" in info:
            entry["birth_bce"] = info["birth_bce"]
        elif "birth" in info and info["birth"]:
            entry["birth_bce"] = abs(info["birth"])
        if "death_bce" in info:
            entry["death_bce"] = info["death_bce"]
        elif "death" in info and info["death"]:
            entry["death_bce"] = abs(info["death"])
        if entry:
            result[name] = entry
    return result

# ============================================================
# 检测单锚点塌缩
# ============================================================

def detect_collapse(events):
    """检测是否存在单锚点塌缩，返回 (collapsed_year, affected_events) 或 None"""
    from collections import Counter

    inferred = [(i, e) for i, e in enumerate(events)
                if e.get("year_type") == "inferred" and e.get("year_bce")]

    if len(inferred) < 5:
        return None

    years = [e["year_bce"] for _, e in inferred]
    counter = Counter(years)
    most_common, count = counter.most_common(1)[0]

    if count / len(inferred) > 0.6:
        affected = [(i, e) for i, e in inferred if e["year_bce"] == most_common]
        return most_common, affected

    return None


# ============================================================
# 从事件详情提取人物和纪年线索
# ============================================================

def parse_event_details(content):
    """解析事件索引的详情部分，返回 {event_id: {persons, time_hints, description}} """
    details = {}
    current_id = None
    current = {}

    for line in content.split("\n"):
        # 新事件开始
        m = re.match(r"### (\d{3}-\d{3})\s+(.+)", line)
        if m:
            if current_id:
                details[current_id] = current
            current_id = m.group(1)
            current = {"name": m.group(2), "persons": [], "time_hints": [], "description": ""}
            continue

        if current_id:
            # 人物
            persons = re.findall(r"@(\w+?)@", line)
            current["persons"].extend(persons)

            # 时间线索（%N年% 格式）
            for th in re.finditer(r"%(.+?)%", line):
                current["time_hints"].append(th.group(1))

            # 描述
            if line.startswith("- **事件描述**:"):
                current["description"] = line

    if current_id:
        details[current_id] = current

    return details


# ============================================================
# 推断合理年份
# ============================================================

def infer_year(event, details, rulers, lifespans, chapter_events):
    """尝试为一个事件推断更合理的年份。
    返回 (new_year, reason) 或 None"""

    event_id = event["id"]
    detail = details.get(event_id, {})
    persons = list(set(event.get("persons", []) + detail.get("persons", [])))

    # 策略1：人物生卒年
    if persons and lifespans:
        birth_years = []
        death_years = []
        for p in persons:
            if p in lifespans:
                ls = lifespans[p]
                if "birth_bce" in ls and ls["birth_bce"]:
                    birth_years.append(ls["birth_bce"])
                if "death_bce" in ls and ls["death_bce"]:
                    death_years.append(ls["death_bce"])

        if birth_years or death_years:
            # 死亡事件用去世年
            is_death = bool(re.search(r"崩|卒|死|薨|自杀|被杀", event.get("name", "")))
            if is_death and death_years:
                # 取主要人物（第一个）的去世年
                main_person = persons[0]
                if main_person in lifespans and lifespans[main_person].get("death_bce"):
                    year = lifespans[main_person]["death_bce"]
                    return year, f"取{main_person}去世年（前{year}年）"

            # 非死亡事件用生卒交集中点
            latest_birth = max(birth_years) if birth_years else None
            earliest_death = min(death_years) if death_years else None

            if latest_birth and earliest_death:
                midpoint = (latest_birth + earliest_death) // 2
                return midpoint, f"人物生卒交集中点：前{midpoint}年"
            elif latest_birth:
                # 出生后20-40年活跃
                active = latest_birth - 30
                return active, f"取{persons[0]}出生后约30年活跃期"
            elif earliest_death:
                # 去世前20年活跃
                active = earliest_death + 20
                return active, f"取{persons[0]}去世前约20年活跃期"

    # 策略2：利用章节内精确纪年事件做线性插值
    precise_events = [(i, e) for i, e in enumerate(chapter_events)
                      if e.get("year_type") == "precise" and e.get("year_bce")]
    if len(precise_events) >= 2:
        # 找前后最近的精确纪年
        event_idx = next((i for i, e in enumerate(chapter_events) if e["id"] == event_id), None)
        if event_idx is not None:
            before = [(i, e) for i, e in precise_events if i < event_idx]
            after = [(i, e) for i, e in precise_events if i > event_idx]

            if before and after:
                prev_idx, prev_e = before[-1]
                next_idx, next_e = after[0]
                # 线性插值
                span = next_idx - prev_idx
                offset = event_idx - prev_idx
                year_span = prev_e["year_bce"] - next_e["year_bce"]
                interp = prev_e["year_bce"] - int(year_span * offset / span)
                if abs(interp - event["year_bce"]) > 10:
                    return interp, f"线性插值：前锚{prev_e['id']}(前{prev_e['year_bce']}年)→后锚{next_e['id']}(前{next_e['year_bce']}年)"
            elif before:
                _, prev_e = before[-1]
                if abs(prev_e["year_bce"] - event["year_bce"]) > 10:
                    return prev_e["year_bce"], f"取前方最近锚点{prev_e['id']}(前{prev_e['year_bce']}年)"

    return None


# ============================================================
# 解析概览表
# ============================================================

def parse_overview_table(content):
    """解析概览表中的事件"""
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
        if inferred:
            if year_bce is None:
                year_bce = int(inferred.group(1))
                year_type = "inferred"

        persons = re.findall(r"@(\w+?)@", m.group(0))

        events.append({
            "id": event_id,
            "name": event_name,
            "year_bce": year_bce,
            "year_type": year_type,
            "persons": persons,
        })

    return events


# ============================================================
# 应用修正
# ============================================================

def apply_fixes(content, fixes):
    """将修正应用到文件内容。fixes: [(event_id, old_year, new_year, reason), ...]"""
    for event_id, old_year, new_year, reason in fixes:
        # 替换概览表中的年份
        old_inferred = f"[约公元前{old_year}年]"
        new_inferred = f"[约公元前{new_year}年]"

        # 只替换该事件所在行（通过event_id定位）
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if event_id in line:
                line = line.replace(old_inferred, new_inferred)
                # 也替换详情部分的时间行
                if line.startswith("- **时间**:"):
                    line = line.replace(old_inferred, new_inferred)
            new_lines.append(line)
        content = "\n".join(new_lines)

        # 更新或添加年代推断行
        # 在详情的 event_id 区块中查找
        detail_pattern = re.compile(
            rf"(### {re.escape(event_id)}\s+.+?\n(?:.*?\n)*?)(?=### \d{{3}}-\d{{3}}|\Z)",
            re.DOTALL
        )
        m = detail_pattern.search(content)
        if m:
            block = m.group(1)
            # 替换或添加年代推断行
            if "**年代推断**" in block:
                block = re.sub(
                    r"- \*\*年代推断\*\*:.*",
                    f"- **年代推断**: {reason}",
                    block
                )
            else:
                # 在块末尾添加
                block = block.rstrip() + f"\n- **年代推断**: {reason}\n"
            content = content[:m.start()] + block + content[m.end():]

    return content


# ============================================================
# 主函数
# ============================================================

def main():
    dry_run = "--dry-run" in sys.argv
    target_chapters = [a.zfill(3) for a in sys.argv[1:] if a != "--dry-run"]

    print("加载参考数据...")
    rulers, eras, aliases = load_reign_periods()
    lifespans = load_lifespans()
    print(f"  君主：{len(rulers)}条，年号：{len(eras)}条，人物寿命：{len(lifespans)}条")

    paths = sorted(glob.glob(os.path.join(EVENTS_DIR, "*_事件索引.md")))
    total_fixes = 0

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

        collapse = detect_collapse(events)
        if not collapse:
            continue

        collapsed_year, affected = collapse
        details = parse_event_details(content)

        fixes = []
        for idx, event in affected:
            result = infer_year(event, details, rulers, lifespans, events)
            if result:
                new_year, reason = result
                if abs(new_year - event["year_bce"]) > 10:  # 只修正偏差>10年的
                    fixes.append((event["id"], event["year_bce"], new_year, reason))

        if fixes:
            print(f"\n{fname}: 塌缩到前{collapsed_year}年，可修正{len(fixes)}/{len(affected)}个事件")
            for eid, old, new, reason in fixes:
                print(f"  {eid}: 前{old}年 → 前{new}年 ({reason})")

            if not dry_run:
                content = apply_fixes(content, fixes)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  ✓ 已写入文件")

            total_fixes += len(fixes)

    print(f"\n{'='*60}")
    print(f"总计：{total_fixes}个修正" + (" (dry-run)" if dry_run else ""))


if __name__ == "__main__":
    main()
