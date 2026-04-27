#!/usr/bin/env python3
"""
check_scale.py — Butler 规模健康检查
每次反思时调用，输出当前指标并标注是否越过警戒线/临界线。

退出码：
  0 = 全部正常（绿色）
  1 = 有指标越过警戒线 🟡（提示关注）
  2 = 有指标越过临界线 🔴（触发架构提案）
"""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent  # shiji-kb/

PAGES_JSON    = ROOT / "wiki/public/pages.json"
PAGES_DIR     = ROOT / "wiki/public/pages"
HISTORY_DIR   = ROOT / "wiki/public/history"
RECENT_JSONL  = ROOT / "wiki/public/recent.jsonl"
ACTIONS_JSONL = ROOT / "wiki/logs/butler/actions.jsonl"
SNOOZE_JSON   = ROOT / "wiki/logs/butler/arch_snooze.json"

# 默认阈值（可被 snooze 文件临时调高）
THRESHOLDS = {
    "pages_json_kb":    {"warn": 500,  "crit": 1024},
    "total_pages":      {"warn": 800,  "crit": 1500},
    "person_pages":     {"warn": 600,  "crit": 1000},
    "history_files":    {"warn": 1000, "crit": 2000},
    "total_revisions":  {"warn": 2000, "crit": 5000},
    "avg_action_s":     {"warn": 30,   "crit": 90},
}


def load_snooze():
    """读取用户暂缓的阈值覆盖（每个指标可临时调高 20%）。"""
    if SNOOZE_JSON.exists():
        with open(SNOOZE_JSON) as f:
            return json.load(f)
    return {}


def apply_snooze(thresholds, snooze):
    result = {k: dict(v) for k, v in thresholds.items()}
    for key, data in snooze.items():
        if key in result and "expires" in data:
            if time.time() < data["expires"]:
                result[key]["warn"] = int(result[key]["warn"] * 1.2)
                result[key]["crit"] = int(result[key]["crit"] * 1.2)
    return result


def count_person_pages(pages_json_path):
    try:
        with open(pages_json_path) as f:
            data = json.load(f)
        return sum(1 for v in data.get("pages", {}).values() if v.get("type") == "person")
    except Exception:
        return -1


def avg_recent_action_duration(actions_path, n=20):
    """从 actions.jsonl 最近 n 条提取 duration_s 的均值。"""
    if not actions_path.exists():
        return -1
    lines = []
    try:
        with open(actions_path) as f:
            lines = f.readlines()
    except Exception:
        return -1
    durations = []
    for line in reversed(lines):
        try:
            rec = json.loads(line)
            if "duration_s" in rec:
                durations.append(float(rec["duration_s"]))
            if len(durations) >= n:
                break
        except Exception:
            continue
    return round(sum(durations) / len(durations), 1) if durations else -1


def check_total_revisions(recent_path):
    try:
        lines = Path(recent_path).read_text(encoding='utf-8').splitlines()
        return sum(1 for l in lines if l.strip())
    except Exception:
        return -1


def main():
    snooze = load_snooze()
    thresholds = apply_snooze(THRESHOLDS, snooze)

    metrics = {}

    # 1. pages.json 大小（KB）
    if PAGES_JSON.exists():
        metrics["pages_json_kb"] = round(PAGES_JSON.stat().st_size / 1024, 1)
    else:
        metrics["pages_json_kb"] = -1

    # 2. 总页面数
    metrics["total_pages"] = len(list(PAGES_DIR.glob("*.md"))) if PAGES_DIR.exists() else -1

    # 3. person 页数量
    metrics["person_pages"] = count_person_pages(PAGES_JSON) if PAGES_JSON.exists() else -1

    # 4. history/ 文件数
    metrics["history_files"] = len(list(HISTORY_DIR.glob("*.json"))) if HISTORY_DIR.exists() else -1

    # 5. 总修订数
    metrics["total_revisions"] = check_total_revisions(RECENT_JSONL)

    # 6. 平均 action 耗时
    metrics["avg_action_s"] = avg_recent_action_duration(ACTIONS_JSONL)

    # 评估
    worst = 0  # 0=ok, 1=warn, 2=crit
    lines = []
    labels = {
        "pages_json_kb":   "pages.json 大小 (KB)",
        "total_pages":     "wiki 总页面数",
        "person_pages":    "person 页数量",
        "history_files":   "history/ 文件数",
        "total_revisions": "总修订数",
        "avg_action_s":    "平均 action 耗时 (s)",
    }
    for key, val in metrics.items():
        t = thresholds[key]
        label = labels[key]
        if val < 0:
            status = "⚪ N/A"
        elif val >= t["crit"]:
            status = "🔴 临界"
            worst = max(worst, 2)
        elif val >= t["warn"]:
            status = "🟡 警戒"
            worst = max(worst, 1)
        else:
            status = "🟢 正常"
        lines.append(f"  {status}  {label}: {val}  (警戒≥{t['warn']} 临界≥{t['crit']})")

    print("=== Butler 规模健康检查 ===")
    for l in lines:
        print(l)
    print()

    if worst == 2:
        print("⛔ 有指标越过临界线 → 本次反思须输出 arch_YYYY-MM-DD.md 架构提案，等待用户批准。")
    elif worst == 1:
        print("⚠️  有指标越过警戒线 → 在反思报告中注明，规划应对方案，尚不需要架构提案。")
    else:
        print("✅ 所有指标正常，无需架构干预。")

    return worst


if __name__ == "__main__":
    sys.exit(main())
