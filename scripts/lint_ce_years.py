#!/usr/bin/env python3
"""
公元纪年标注质检脚本

检查规则:
1. 时序倒退：同一章节内，后序事件的公元年不应早于前序事件
2. 重大偏差：与已知历史年份差距过大的标注
3. 连续跳跃：相邻事件年份差距异常大（>100年）

输出修复建议。

使用:
    python3 scripts/lint_ce_years.py              # 检查所有
    python3 scripts/lint_ce_years.py 047           # 检查指定章节
    python3 scripts/lint_ce_years.py --fix         # 自动修复
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVENTS_DIR = _PROJECT_ROOT / "kg" / "events"
REIGN_FILE = _PROJECT_ROOT / "kg" / "reign_periods.json"

# 已知关键事件年份（用于校验）
KNOWN_DATES = {
    "孔子出生": -551,
    "孔子卒": -479,
    "秦始皇统一": -221,
    "陈胜起义": -209,
    "项羽自刎": -202,
    "高祖驾崩": -195,
    "长平之战": -260,
    "商鞅变法": -356,
    "三家分晋": -403,
    "牧野之战": -1046,
    "白起赐死": -257,
    "焚书坑儒": -213,
    "鸿门宴": -206,
    "垓下之战": -202,
    "武王伐纣": -1046,
}


def parse_events_from_file(filepath):
    """从事件索引文件中提取带公元年的事件"""
    text = filepath.read_text(encoding="utf-8")
    chapter_id = filepath.stem.split("_")[0]
    chapter_name = filepath.stem.replace("_事件索引", "")

    events = []
    table_pat = re.compile(
        r"\|\s*([\d-]+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|"
    )

    for m in table_pat.finditer(text):
        eid = m.group(1).strip()
        if not re.match(r"\d{3}-\d{3}", eid):
            continue

        name = m.group(2).strip()
        time_field = m.group(4).strip()

        ce_year = None
        ce_match = re.search(r"公元前(\d+)年", time_field)
        if ce_match:
            ce_year = -int(ce_match.group(1))
        else:
            ce_match = re.search(r"公元(\d+)年", time_field)
            if ce_match:
                ce_year = int(ce_match.group(1))

        events.append({
            "id": eid,
            "name": name,
            "time_raw": time_field,
            "ce_year": ce_year,
            "chapter_id": chapter_id,
        })

    return chapter_id, chapter_name, events


def check_temporal_order(events):
    """检查时序是否递增（公元年应递增，即越来越大/越来越接近0）"""
    issues = []
    dated = [(i, e) for i, e in enumerate(events) if e["ce_year"] is not None]

    for idx in range(1, len(dated)):
        prev_i, prev_e = dated[idx - 1]
        curr_i, curr_e = dated[idx]

        # 后面的事件年份应 >= 前面（更晚 = 数值更大）
        if curr_e["ce_year"] < prev_e["ce_year"]:
            diff = prev_e["ce_year"] - curr_e["ce_year"]
            if diff > 3:  # 允许3年误差（同年不同事件顺序可能略有出入）
                issues.append({
                    "type": "temporal_reversal",
                    "severity": "error" if diff > 20 else "warning",
                    "event": curr_e,
                    "prev_event": prev_e,
                    "diff": diff,
                    "message": f"时序倒退 {diff}年: {prev_e['id']} {prev_e['name']}({prev_e['ce_year']}) → {curr_e['id']} {curr_e['name']}({curr_e['ce_year']})"
                })

    return issues


def check_large_gaps(events):
    """检查相邻事件之间的异常大跳跃"""
    issues = []
    dated = [(i, e) for i, e in enumerate(events) if e["ce_year"] is not None]

    for idx in range(1, len(dated)):
        prev_i, prev_e = dated[idx - 1]
        curr_i, curr_e = dated[idx]

        gap = curr_e["ce_year"] - prev_e["ce_year"]
        if gap > 150:
            issues.append({
                "type": "large_gap",
                "severity": "warning",
                "event": curr_e,
                "prev_event": prev_e,
                "gap": gap,
                "message": f"跳跃 {gap}年: {prev_e['id']}({prev_e['ce_year']}) → {curr_e['id']}({curr_e['ce_year']})"
            })

    return issues


def check_known_dates(events):
    """与已知历史年份对比"""
    issues = []
    for e in events:
        if e["ce_year"] is None:
            continue
        for keyword, known_year in KNOWN_DATES.items():
            if keyword in e["name"]:
                diff = abs(e["ce_year"] - known_year)
                if diff > 5:
                    issues.append({
                        "type": "known_date_mismatch",
                        "severity": "error",
                        "event": e,
                        "expected": known_year,
                        "actual": e["ce_year"],
                        "diff": diff,
                        "message": f"已知年份不匹配: {e['id']} {e['name']} 标注={e['ce_year']}, 应为={known_year}, 差{diff}年"
                    })
    return issues


def suggest_fix(issue, reign_periods):
    """尝试给出修复建议"""
    event = issue["event"]
    time_raw = event["time_raw"]

    # 提取纪年信息
    ruler_match = re.search(r"\$([^$]+)\$", time_raw)
    year_match = re.search(r"%([^%]+)%", time_raw)

    if ruler_match and year_match:
        ruler_name = ruler_match.group(1)
        year_text = year_match.group(1)

        # 尝试从 year_text 中提取年数
        num_match = re.search(r"(\d+|[一二三四五六七八九十百]+)年", year_text)
        if num_match:
            num_str = num_match.group(1)
            try:
                num = int(num_str)
            except ValueError:
                num = chinese_to_int(num_str)

            # 在reign_periods中查找
            if ruler_name in reign_periods.get("rulers", {}):
                ruler = reign_periods["rulers"][ruler_name]
                suggested = ruler["start_bce"] - (num - 1)
                return f"建议: {ruler_name}第{num}年 = 前{suggested}年 (start_bce={ruler['start_bce']})"

            # 查aliases
            for alias, canonical in reign_periods.get("aliases", {}).items():
                if alias == ruler_name:
                    if canonical in reign_periods.get("rulers", {}):
                        ruler = reign_periods["rulers"][canonical]
                        suggested = ruler["start_bce"] - (num - 1)
                        return f"建议: {ruler_name}→{canonical}第{num}年 = 前{suggested}年"

    return None


def chinese_to_int(s):
    """简单的中文数字转换"""
    digits = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    if s in digits:
        return digits[s]
    if s.startswith('十'):
        if len(s) == 1:
            return 10
        return 10 + digits.get(s[1], 0)
    if s.endswith('十'):
        return digits.get(s[0], 0) * 10
    if '十' in s:
        parts = s.split('十')
        return digits.get(parts[0], 0) * 10 + digits.get(parts[1], 0)
    return 0


def main():
    args = sys.argv[1:]
    do_fix = "--fix" in args
    target_chapters = [a for a in args if a.isdigit()]

    # Load reign periods for fix suggestions
    reign_periods = {}
    if REIGN_FILE.exists():
        with open(REIGN_FILE, encoding="utf-8") as f:
            reign_periods = json.load(f)

    all_issues = []
    total_events = 0
    total_dated = 0

    for fp in sorted(EVENTS_DIR.glob("*_事件索引.md")):
        ch_id, ch_name, events = parse_events_from_file(fp)

        if target_chapters and ch_id not in target_chapters:
            continue

        total_events += len(events)
        total_dated += sum(1 for e in events if e["ce_year"] is not None)

        issues = []
        issues.extend(check_temporal_order(events))
        issues.extend(check_large_gaps(events))
        issues.extend(check_known_dates(events))

        if issues:
            all_issues.extend(issues)
            print(f"\n{'='*60}")
            print(f"  {ch_name}")
            print(f"{'='*60}")
            for issue in issues:
                icon = "!!" if issue["severity"] == "error" else "??"
                print(f"  [{icon}] {issue['message']}")
                fix = suggest_fix(issue, reign_periods)
                if fix:
                    print(f"       {fix}")

    # Summary
    errors = sum(1 for i in all_issues if i["severity"] == "error")
    warnings = sum(1 for i in all_issues if i["severity"] == "warning")

    print(f"\n{'='*60}")
    print(f"  总结")
    print(f"{'='*60}")
    print(f"  总事件: {total_events}")
    print(f"  有年份: {total_dated}")
    print(f"  问题数: {len(all_issues)} (错误: {errors}, 警告: {warnings})")

    if do_fix and errors > 0:
        print("\n  自动修复功能待实现...")


if __name__ == "__main__":
    main()
