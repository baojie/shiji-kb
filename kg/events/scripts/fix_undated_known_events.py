#!/usr/bin/env python3
"""
fix_undated_known_events.py - 修正缺少年代标注但有明确历史定年的事件

从用户指出的错误中总结的推理规则：
1. 事件描述或原文中包含明确的时间线索（如"汉元年"、"陈胜起"等）
2. 同一事件在其他章节已有精确纪年
3. 事件属于已知历史事件，有公认定年

策略：
A. 关键词匹配：根据事件名/描述中的关键词推断年份
B. 跨章节同事件比对：同一事件在不同章节的纪年
C. 历史事件对照表：秦末汉初重大事件的公认年份
"""

import re
import json
from pathlib import Path
from collections import defaultdict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVENTS_DIR = _PROJECT_ROOT / "kg" / "events" / "data"

# ═══ 历史事件公认年份对照表 ═══
# 基于用户反馈和历史文献

KNOWN_EVENTS = {
    # ── 秦末起义（前209年）──
    "陈胜起义": -209,
    "陈胜吴广起义": -209,
    "陈涉起义": -209,
    "陈涉起兵": -209,
    "陈涉起": -209,
    "大泽乡起义": -209,
    "起兵反秦": -209,
    "从陈胜": -209,

    # ── 项梁起兵（前209~前208年）──
    "项梁渡淮": -209,
    "投奔项梁": -208,
    "归属项梁": -208,
    "从项梁": -208,

    # ── 巨鹿之战（前207年）──
    "巨鹿之战": -207,
    "破釜沉舟": -207,
    "章邯降": -207,
    "新安坑杀": -207,

    # ── 鸿门宴/入关（前206年）──
    "鸿门宴": -206,
    "鸿门之会": -206,
    "约法三章": -206,
    "入函谷关": -206,
    "秦王子婴降": -206,
    "子婴降": -206,

    # ── 楚汉分封（前206年）──
    "项羽分封": -206,
    "还定三秦": -206,
    "入汉中": -206,
    "烧绝栈道": -206,

    # ── 楚汉战争（前205~前202年）──
    "彭城大败": -205,
    "彭城之战": -205,
    "荥阳之战": -204,
    "背水一战": -204,
    "韩信破赵": -204,
    "垓下之战": -202,
    "霸王别姬": -202,
    "乌江自刎": -202,

    # ── 汉初（前202~前195年）──
    "封为淮南王": -202,
    "封为楚王": -201,
    "封为韩王": -201,
    "白登之围": -200,
    "平城之围": -200,
    "韩信被擒": -201,
    "擒韩信": -201,
    "诛吕": -180,
}

# ── 事件描述中的时间线索关键词 ──
# 仅限描述以这些词开头或事件本身就是关于此事件的
# chapter_range 限制应用范围（避免后世引用误匹配）
CONTEXT_CLUES = [
    # (描述关键词pattern, 年份, 适用章节范围)
    (r'^陈胜.*起|^陈涉.*起|起兵反秦', -209, None),
    (r'^项梁.*渡淮|从项梁', -208, ("007", "092")),
    (r'^鸿门|至鸿门', -206, None),
    (r'^还定三秦|从还定三秦|还定三秦', -206, ("008", "051", "054", "057", "095", "098")),
    (r'入汉中.*还定|从入汉中', -206, ("054", "057", "098")),
    (r'会垓下|垓下.*破|至垓下', -202, None),
    (r'^白登', -200, None),
    (r'^四皓', -196, None),
]


def scan_and_fix():
    """扫描所有事件文件，找出可修正的事件"""
    fixes = []  # (fpath, event_id, event_name, inferred_year, reason)

    for fpath in sorted(EVENTS_DIR.glob('*_事件索引.md')):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')

        # 解析详细事件
        current_id = None
        current_name = None
        current_time = None
        current_desc = None

        for line in lines:
            m = re.match(r'^### (\d{3}-\d{3})\s+(.+)', line)
            if m:
                current_id = m.group(1)
                current_name = m.group(2).strip()
                current_time = None
                current_desc = None
                continue

            if current_id:
                tm = re.match(r'^- \*\*时间\*\*: (.+)', line)
                if tm:
                    current_time = tm.group(1).strip()

                dm = re.match(r'^- \*\*事件描述\*\*: (.+)', line)
                if dm:
                    current_desc = dm.group(1).strip()

                # 当收集到描述后检查
                if current_desc and current_time:
                    # 跳过已有公元标注的
                    if '公元' in current_time:
                        current_id = None
                        continue

                    # 检查事件名是否匹配已知事件
                    # v2.1格式：〖TYPE content〗
                    clean_name = re.sub(r'[〖〗@=;%&\'^~\*!#\+〚〛《》〈〉【】〔〕]', '', current_name)
                    matched_year = None
                    matched_reason = None

                    for keyword, year in KNOWN_EVENTS.items():
                        if keyword in clean_name:
                            matched_year = year
                            matched_reason = f"事件名匹配已知事件「{keyword}」"
                            break

                    # 检查描述中的线索
                    ch_num = current_id[:3]
                    if matched_year is None and current_desc:
                        for clue in CONTEXT_CLUES:
                            pattern, year, ch_range = clue
                            # 限制章节范围
                            if ch_range and ch_num not in ch_range:
                                continue
                            if re.search(pattern, current_desc):
                                matched_year = year
                                matched_reason = f"事件描述匹配线索/{pattern}/"
                                break

                    if matched_year is not None:
                        fixes.append((fpath, current_id, clean_name, matched_year, matched_reason))

                    current_id = None

    return fixes


def cross_chapter_check(fixes):
    """跨章节验证：同名事件在不同章节是否有纪年"""
    # 收集所有已有纪年的事件名
    dated_events = {}  # event_name -> (ce_year, event_id, fpath)
    for fpath in sorted(EVENTS_DIR.glob('*_事件索引.md')):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        for m in re.finditer(r'^### (\d{3}-\d{3})\s+(.+)', content, re.MULTILINE):
            eid = m.group(1)
            name = re.sub(r'[〖〗@=;%&\'^~\*!#\+〚〛《》〈〉【】〔〕]', '', m.group(2).strip())

            # 查找该事件的时间
            pos = m.end()
            time_match = re.search(r'- \*\*时间\*\*: (.+)', content[pos:pos+500])
            if time_match:
                time_str = time_match.group(1)
                ce_match = re.search(r'公元前(\d+)年', time_str)
                if ce_match:
                    dated_events[name] = (-int(ce_match.group(1)), eid, fpath.name)

    # 检查 fixes 中的事件是否能从跨章节获得验证
    for i, (fpath, eid, name, year, reason) in enumerate(fixes):
        if name in dated_events:
            cross_year, cross_eid, cross_file = dated_events[name]
            if cross_year != year:
                print(f"  ⚠ {eid} {name}: 推断{year} vs 跨章节{cross_eid}@{cross_file}={cross_year}")
            else:
                fixes[i] = (fpath, eid, name, year, reason + f"（跨章节{cross_eid}验证）")

    return fixes


def apply_fixes(fixes, dry_run=True):
    """将修正写入文件"""
    by_file = defaultdict(list)
    for fpath, eid, name, year, reason in fixes:
        by_file[str(fpath)].append((eid, name, year, reason))

    total = 0
    for fpath_str, file_fixes in sorted(by_file.items()):
        fpath = Path(fpath_str)
        with open(fpath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        modified = False
        for eid, name, year, reason in file_fixes:
            if year <= 0:
                annotation = f"（公元前{-year}年）"
            else:
                annotation = f"（公元{year}年）"

            # 修改概览表
            for i, line in enumerate(lines):
                if re.match(rf'^\| {re.escape(eid)} \|', line):
                    if '公元' not in line:
                        cols = line.split('|')
                        if len(cols) >= 5:
                            time_col = cols[4].strip()
                            if time_col == '-':
                                cols[4] = f" {annotation} "
                            else:
                                cols[4] = f" {time_col} {annotation} "
                            lines[i] = '|'.join(cols)
                            modified = True

            # 修改详细记录
            for i, line in enumerate(lines):
                if line.startswith(f'### {eid} '):
                    # 找到时间行
                    for j in range(i+1, min(i+8, len(lines))):
                        if lines[j].startswith('- **时间**:'):
                            if '公元' not in lines[j]:
                                time_val = lines[j].replace('- **时间**: ', '').strip()
                                if time_val == '-':
                                    lines[j] = f'- **时间**: {annotation}\n'
                                else:
                                    lines[j] = f'- **时间**: {time_val} {annotation}\n'
                                modified = True
                            break

            total += 1

        if not dry_run and modified:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"  {fpath.name}: 修正 {len(file_fixes)} 个事件")
        elif dry_run and file_fixes:
            for eid, name, year, reason in file_fixes:
                print(f"  {eid} {name} → {year} ({reason})")

    return total


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print("扫描可修正事件...")
    fixes = scan_and_fix()
    print(f"  找到 {len(fixes)} 个可修正事件")

    print("\n跨章节验证...")
    fixes = cross_chapter_check(fixes)

    print(f"\n{'预览' if args.dry_run else '写入'}修正:")
    total = apply_fixes(fixes, dry_run=args.dry_run)
    print(f"\n共 {total} 个事件")


if __name__ == "__main__":
    main()
