#!/usr/bin/env python3
"""
事件索引验证与统计汇总脚本

验证事件索引文件的格式，生成统计汇总。

使用方法:
    python3 scripts/validate_events.py              # 验证所有事件文件
    python3 scripts/validate_events.py --summary     # 生成汇总报告
"""

import os
import re
import json
import sys
from pathlib import Path
from collections import Counter

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVENTS_DIR = _PROJECT_ROOT / "kg" / "events" / "data"


def validate_event_file(filepath):
    """验证单个事件索引文件的格式"""
    errors = []
    warnings = []
    stats = {"events": 0, "types": Counter()}

    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    chapter_num = filepath.name.split("_")[0]

    # 检查事件ID格式和连续性
    event_ids = re.findall(r'^### (\d{3}-\d{3})\s', text, re.MULTILINE)
    stats["events"] = len(event_ids)

    if not event_ids:
        errors.append("未找到任何事件记录（### {ID} 格式）")
        return errors, warnings, stats

    # 检查ID前缀一致性
    expected_prefix = chapter_num
    for eid in event_ids:
        prefix = eid.split("-")[0]
        if prefix != expected_prefix:
            errors.append(f"事件ID前缀不一致: {eid}，期望 {expected_prefix}-xxx")

    # 检查ID序号连续性
    seq_nums = [int(eid.split("-")[1]) for eid in event_ids]
    for i in range(1, len(seq_nums)):
        if seq_nums[i] != seq_nums[i-1] + 1:
            warnings.append(f"事件序号不连续: {event_ids[i-1]} -> {event_ids[i]}")

    # 检查必须字段
    event_blocks = re.split(r'^### \d{3}-\d{3}', text, flags=re.MULTILINE)[1:]
    required_fields = ["事件类型", "主要人物", "事件描述", "原文引用", "段落位置"]

    for i, block in enumerate(event_blocks):
        eid = event_ids[i] if i < len(event_ids) else f"unknown-{i}"
        for field in required_fields:
            if f"**{field}**" not in block:
                warnings.append(f"{eid}: 缺少字段 {field}")

        # 提取事件类型统计
        type_match = re.search(r'\*\*事件类型\*\*:\s*(.+)', block)
        if type_match:
            stats["types"][type_match.group(1).strip()] += 1

    # 检查概览表格是否存在
    if "| 事件ID |" not in text and "| 事件ID|" not in text:
        warnings.append("缺少事件列表概览表格")

    # 检查统计信息
    if "统计信息" not in text and "统计" not in text:
        warnings.append("缺少统计信息部分")

    return errors, warnings, stats


def generate_summary():
    """生成全局汇总报告"""
    event_files = sorted(EVENTS_DIR.glob("*_事件索引.md"))

    if not event_files:
        print("未找到事件索引文件。")
        return

    total_events = 0
    total_types = Counter()
    chapter_stats = []

    for f in event_files:
        errors, warnings, stats = validate_event_file(f)
        chapter_name = f.stem.replace("_事件索引", "")
        chapter_num = chapter_name.split("_")[0]

        chapter_stats.append({
            "chapter": chapter_name,
            "num": chapter_num,
            "events": stats["events"],
            "types": dict(stats["types"]),
            "errors": len(errors),
            "warnings": len(warnings),
        })

        total_events += stats["events"]
        total_types += stats["types"]

    # 输出报告
    print(f"{'='*60}")
    print(f"  史记事件索引汇总报告")
    print(f"  文件数: {len(event_files)}")
    print(f"  事件总数: {total_events}")
    print(f"{'='*60}")

    print(f"\n事件类型分布:")
    for t, count in total_types.most_common():
        pct = count / total_events * 100 if total_events else 0
        print(f"  {t}: {count} ({pct:.1f}%)")

    print(f"\n各章节事件数:")
    for cs in chapter_stats:
        status = ""
        if cs["errors"]:
            status = f" [!{cs['errors']}错误]"
        elif cs["warnings"]:
            status = f" [{cs['warnings']}警告]"
        print(f"  {cs['chapter']}: {cs['events']} 事件{status}")

    # 保存JSON统计
    summary_file = EVENTS_DIR / "events_summary.json"
    summary_data = {
        "generated": __import__("datetime").datetime.now().isoformat(),
        "total_events": total_events,
        "total_files": len(event_files),
        "type_distribution": dict(total_types),
        "chapters": chapter_stats,
    }
    summary_file.write_text(json.dumps(summary_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n统计已保存: {summary_file}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="事件索引验证与统计")
    parser.add_argument("--summary", action="store_true", help="生成汇总报告")
    parser.add_argument("files", nargs="*", help="要验证的文件（不指定则验证所有）")
    args = parser.parse_args()

    if args.summary:
        generate_summary()
        return 0

    # 验证模式
    if args.files:
        event_files = [Path(f) for f in args.files]
    else:
        event_files = sorted(EVENTS_DIR.glob("*_事件索引.md"))

    if not event_files:
        print("未找到事件索引文件。")
        return 1

    total_errors = 0
    total_warnings = 0

    for f in event_files:
        errors, warnings, stats = validate_event_file(f)
        name = f.name

        if errors or warnings:
            print(f"\n{name} ({stats['events']} 事件)")
            for e in errors:
                print(f"  错误: {e}")
                total_errors += 1
            for w in warnings:
                print(f"  警告: {w}")
                total_warnings += 1
        else:
            print(f"  {name}: {stats['events']} 事件 OK")

    print(f"\n验证完成: {total_errors} 错误, {total_warnings} 警告")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
