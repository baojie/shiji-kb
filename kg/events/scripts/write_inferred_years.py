#!/usr/bin/env python3
"""
write_inferred_years.py - 将推断年代写入所有原始事件索引

标记规则：
  - 有明确纪年的年份：（公元前XXX年）  ← 已存在，不动
  - 推断的年份：[约公元前XXX年]         ← 方括号 + 约

在详细记录的每个事件中加入：
  - **年代推断**: 推断方法和依据

推断策略（与 build_entity_index.py 一致）：
  1. 人物生卒年交集中点
  2. 章节内最近已知纪年事件（插值）
  3. 章节时代兜底（CHAPTER_ERA）
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVENTS_DIR = _PROJECT_ROOT / "kg" / "events" / "data"
LIFESPANS_FILE = _PROJECT_ROOT / "kg" / "entities" / "data" / "person_lifespans.json"
REIGN_FILE = _PROJECT_ROOT / "kg" / "chronology" / "data" / "reign_periods.json"

# 章节时代兜底
CHAPTER_ERA = {
    "001": -2500, "002": -1900, "003": -1300, "004": -900, "005": -900,
    "006": -230, "007": -207, "008": -205, "009": -190, "010": -175,
    "011": -155, "012": -135,
    "013": -1500, "014": -800, "015": -450, "016": -250,
    "017": -200, "018": -200, "019": -200, "020": -200,
    "021": -200, "022": -200,
    "023": -300, "024": -300, "025": -300, "026": -300,
    "027": -300, "028": -300, "029": -300, "030": -150,
    "031": -800, "032": -800, "033": -800, "034": -800,
    "035": -1000, "036": -700, "037": -700, "038": -700,
    "039": -650, "040": -700, "041": -500, "042": -700,
    "043": -450, "044": -400, "045": -400, "046": -350,
    "047": -520, "048": -209, "049": -200, "050": -200,
    "051": -200, "052": -200, "053": -200, "054": -200,
    "055": -210, "056": -210, "057": -200, "058": -170,
    "059": -150, "060": -120,
    "061": -1050, "062": -200, "063": -200, "064": -200,
    "065": -500, "066": -300, "067": -200, "068": -200,
    "069": -334, "070": -330, "071": -350, "072": -300,
    "073": -280, "074": -400, "075": -300, "076": -300,
    "077": -300, "078": -300, "079": -270, "080": -284,
    "081": -300, "082": -300, "083": -300, "084": -350,
    "085": -250, "086": -250, "087": -250, "088": -250,
    "089": -210, "090": -200, "091": -200, "092": -210,
    "093": -210, "094": -200, "095": -200, "096": -200,
    "097": -200, "098": -200, "099": -200, "100": -200,
    "101": -200, "102": -180, "103": -170, "104": -170,
    "105": -160, "106": -160, "107": -160, "108": -150,
    "109": -150, "110": -200, "111": -130, "112": -130,
    "113": -130, "114": -130, "115": -130, "116": -130,
    "117": -140, "118": -140, "119": -130, "120": -130,
    "121": -150, "122": -200, "123": -150, "124": -130,
    "125": -130, "126": -130, "127": -130, "128": -130,
    "129": -500, "130": -100,
}


def load_lifespans():
    with open(LIFESPANS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['persons']


def person_active_range(people_list, lifespans):
    """计算人物生卒年交集"""
    ranges = []
    for person in people_list:
        if person in lifespans:
            info = lifespans[person]
            ranges.append((info['birth'], info['death'], person))
    if not ranges:
        return None, None, []
    latest_birth = max(b for b, d, _ in ranges)
    earliest_death = min(d for _, d, _ in ranges)
    if latest_birth <= earliest_death:
        return latest_birth, earliest_death, ranges
    return None, None, ranges


def fmt_ce(ce_year):
    """CE年 -> 显示字符串"""
    if ce_year is None:
        return "?"
    if ce_year <= 0:
        return f"前{-ce_year}年"
    return f"{ce_year}年"


def parse_all_events_from_files():
    """解析所有事件索引文件，提取概览表中的事件信息"""
    events = []
    for fpath in sorted(EVENTS_DIR.glob('*_事件索引.md')):
        chapter_id = fpath.stem.replace('_事件索引', '')
        ch_num = chapter_id[:3]
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')

        in_table = False
        for line in lines:
            line_s = line.strip()
            if line_s.startswith('| 事件ID'):
                in_table = True
                continue
            if in_table and line_s.startswith('|---'):
                continue
            if in_table and not line_s.startswith('|'):
                in_table = False
                continue
            if not in_table:
                continue

            cols = [c.strip() for c in line_s.split('|')]
            if len(cols) < 7:
                continue

            event_id = cols[1].strip()
            event_name = cols[2].strip()
            time_str = cols[4].strip()
            people_str = cols[6].strip()

            # 提取 CE 年 - 只认（公元前XXX年）为精确纪年
            ce_year = None
            has_precise = False
            m = re.search(r'（公元前(\d+)年', time_str)
            if m:
                ce_year = -int(m.group(1))
                has_precise = True
            else:
                m = re.search(r'（公元(\d+)年', time_str)
                if m:
                    ce_year = int(m.group(1))
                    has_precise = True

            # 也检查已有的 [约公元前XXX年]
            has_inferred = bool(re.search(r'\[约公元前\d+年\]', time_str))
            if has_inferred:
                m2 = re.search(r'\[约公元前(\d+)年\]', time_str)
                if m2 and ce_year is None:
                    ce_year = -int(m2.group(1))

            people = re.findall(r'@([^@]+)@', people_str)

            events.append({
                'event_id': event_id,
                'name': re.sub(r'[@=$%&^~*!?〖+〗〚〛]', '', event_name).strip(),
                'chapter_id': chapter_id,
                'ch_num': ch_num,
                'ce_year': ce_year,
                'has_precise': has_precise,
                'has_inferred': has_inferred,
                'time_str': time_str,
                'people': people,
                'fpath': str(fpath),
            })

    return events


def infer_all_events(events, lifespans):
    """对所有事件执行推断，返回 {event_id: (inferred_year, strategy, reason)}"""
    by_chapter = defaultdict(list)
    for ev in events:
        by_chapter[ev['ch_num']].append(ev)

    inferences = {}

    for ch_num, ch_events in sorted(by_chapter.items()):
        ch_events.sort(key=lambda x: x['event_id'])

        # 收集已知 CE 年的位置（只用精确纪年）
        dated_positions = []
        for i, ev in enumerate(ch_events):
            if ev['has_precise'] and ev['ce_year'] is not None:
                dated_positions.append((i, ev['ce_year'], ev['event_id']))

        for i, ev in enumerate(ch_events):
            if ev['has_precise']:
                continue  # 已有精确年份
            if ev['has_inferred']:
                continue  # 已有推断年份

            strategy = None
            inferred = None
            reason = None

            # 计算人物生卒年交集（备用）
            person_lb, person_ed, person_matched = None, None, []
            if ev['people'] and lifespans:
                person_lb, person_ed, person_matched = person_active_range(ev['people'], lifespans)

            # 策略1: 章节内插值（优先：史记按时间叙事，相邻事件年份更准）
            prev_year = None
            prev_eid = None
            next_year = None
            next_eid = None
            if dated_positions:
                for pos, year, eid in dated_positions:
                    if pos <= i:
                        prev_year = year
                        prev_eid = eid
                    if pos >= i and next_year is None:
                        next_year = year
                        next_eid = eid

                # 计算插值跨度
                gap = None
                if prev_year is not None and next_year is not None:
                    gap = abs(next_year - prev_year)

                # 只在跨度不太大时用插值（<200年）
                source_year = None
                source_eid = None
                if prev_year is not None and (gap is None or gap < 200):
                    source_year = prev_year
                    source_eid = prev_eid
                elif next_year is not None and (gap is None or gap < 200):
                    source_year = next_year
                    source_eid = next_eid

                if source_year is not None:
                    inferred = source_year
                    strategy = 'interpolation'
                    if prev_year is not None and next_year is not None:
                        reason = f"章节插值：前锚{prev_eid}({fmt_ce(prev_year)})，后锚{next_eid}({fmt_ce(next_year)})，取前锚"
                    elif prev_year is not None:
                        reason = f"章节插值：前锚{prev_eid}({fmt_ce(prev_year)})"
                    else:
                        reason = f"章节插值：后锚{next_eid}({fmt_ce(next_year)})"

            # 合理性调整：插值结果用人物生卒年修正
            if inferred is not None and strategy == 'interpolation':
                if person_lb is not None and person_ed is not None:
                    if inferred < person_lb - 20 or inferred > person_ed + 20:
                        old_inferred = inferred
                        inferred = (person_lb + person_ed) // 2
                        person_strs = [f"{p}({fmt_ce(b)}~{fmt_ce(d)})" for b, d, p in person_matched]
                        reason = (f"插值{fmt_ce(old_inferred)}与人物生卒年冲突，"
                                  f"改用人物交集中点：{', '.join(person_strs)}，"
                                  f"中点{fmt_ce(inferred)}")
                        strategy = 'person_adjusted'

            # 策略2: 人物生卒年交集中点（插值不可用或跨度太大时）
            if inferred is None and person_lb is not None and person_ed is not None:
                inferred = (person_lb + person_ed) // 2
                strategy = 'person_lifespan'
                person_strs = [f"{p}({fmt_ce(b)}~{fmt_ce(d)})" for b, d, p in person_matched]
                reason = f"人物生卒年交集中点：{', '.join(person_strs)}，交集[{fmt_ce(person_lb)}~{fmt_ce(person_ed)}]，中点{fmt_ce(inferred)}"

            # 大跨度插值作为次选（>200年但有锚点）
            if inferred is None and dated_positions:
                source_year = None
                source_eid = None
                if prev_year is not None:
                    source_year = prev_year
                    source_eid = prev_eid
                elif next_year is not None:
                    source_year = next_year
                    source_eid = next_eid
                if source_year is not None:
                    inferred = source_year
                    strategy = 'interpolation_wide'
                    reason = f"大跨度插值：锚点{source_eid}({fmt_ce(source_year)})"

            # 策略3: 章节时代兜底
            if inferred is None:
                inferred = CHAPTER_ERA.get(ch_num)
                strategy = 'chapter_era'
                reason = f"章节时代兜底：第{ch_num}章默认{fmt_ce(inferred)}"

            if inferred is not None:
                inferences[ev['event_id']] = (inferred, strategy, reason)

    return inferences


def write_inferred_to_file(fpath, inferences, dry_run=False, verbose=False):
    """将推断年代写入单个事件索引文件

    返回 (written_count, already_count)
    """
    with open(fpath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    written = 0
    already = 0
    modified = False

    # === 第一遍：处理详细事件记录 ===
    # 记录每个事件写入的标注，用于回填概览表
    event_annotations = {}  # event_id -> "[约公元前XXX年]"

    i = 0
    current_event_id = None
    while i < len(lines):
        line = lines[i]

        # 检测事件标题
        event_match = re.match(r'^### (\d{3}-\d{3})', line)
        if event_match:
            current_event_id = event_match.group(1)

        # 检测时间行
        time_match = re.match(r'^- \*\*时间\*\*: (.+)$', line)
        if time_match and current_event_id:
            time_str = time_match.group(1).strip()

            # 跳过已有精确纪年
            if '（公元' in time_str:
                already += 1
                i += 1
                continue

            # 跳过已有推断标注
            if '[约公元' in time_str:
                already += 1
                i += 1
                continue

            # 查找推断结果
            if current_event_id in inferences:
                inferred, strategy, reason = inferences[current_event_id]
                if inferred <= 0:
                    annotation = f"[约公元前{-inferred}年]"
                else:
                    annotation = f"[约公元{inferred}年]"

                # 修改时间行
                if time_str == '-':
                    new_time = f"- **时间**: {annotation}"
                else:
                    new_time = f"- **时间**: {time_str} {annotation}"
                lines[i] = new_time + '\n'

                # 查找是否已有年代推断行，找到下一个 - ** 行之前插入
                insert_idx = i + 1
                has_reason_line = False
                while insert_idx < len(lines):
                    next_line = lines[insert_idx]
                    if next_line.startswith('- **年代推断**'):
                        has_reason_line = True
                        break
                    if next_line.startswith('- **') or next_line.startswith('###') or next_line.strip() == '---':
                        break
                    insert_idx += 1

                if not has_reason_line and reason:
                    # 在事件描述之后、原文引用之前插入
                    # 找到段落位置行之后插入
                    target_idx = i + 1
                    while target_idx < len(lines):
                        if lines[target_idx].startswith('- **段落位置**'):
                            target_idx += 1  # 在段落位置之后
                            break
                        if lines[target_idx].startswith('###') or lines[target_idx].strip() == '---':
                            break
                        target_idx += 1
                    lines.insert(target_idx, f'- **年代推断**: {reason}\n')

                event_annotations[current_event_id] = annotation
                written += 1
                modified = True

                if verbose:
                    print(f"  {current_event_id}: {annotation} ({strategy})")

        i += 1

    # === 第二遍：回填概览表 ===
    if event_annotations:
        for i in range(len(lines)):
            line = lines[i]
            table_match = re.match(r'^(\| \d{3}-\d{3} .*)$', line)
            if table_match:
                eid_match = re.search(r'(\d{3}-\d{3})', line)
                if eid_match:
                    eid = eid_match.group(1)
                    if eid in event_annotations:
                        # 不重复添加
                        if '约公元' not in line and '（公元' not in line:
                            cols = line.split('|')
                            if len(cols) >= 5:
                                time_col = cols[4].strip()
                                anno = event_annotations[eid]
                                if time_col == '-':
                                    cols[4] = f" {anno} "
                                else:
                                    cols[4] = f" {time_col} {anno} "
                                lines[i] = '|'.join(cols)
                                modified = True

    if not dry_run and modified:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    return written, already


def main():
    import argparse
    parser = argparse.ArgumentParser(description="将推断年代写入事件索引")
    parser.add_argument("--dry-run", action="store_true", help="预览，不写文件")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--file", help="只处理指定章节号（如 005）")
    parser.add_argument("--stats", action="store_true", help="只显示统计")
    args = parser.parse_args()

    print("加载数据...")
    lifespans = load_lifespans()
    print(f"  人物生卒年: {len(lifespans)} 人")

    print("解析事件...")
    events = parse_all_events_from_files()
    print(f"  总事件数: {len(events)}")

    precise = sum(1 for e in events if e['has_precise'])
    inferred_existing = sum(1 for e in events if e['has_inferred'])
    no_year = sum(1 for e in events if not e['has_precise'] and not e['has_inferred'] and e['ce_year'] is None)
    print(f"  精确纪年: {precise}")
    print(f"  已有推断: {inferred_existing}")
    print(f"  无年代: {no_year}")

    print("\n推断年代...")
    inferences = infer_all_events(events, lifespans)
    print(f"  可推断: {len(inferences)} 个事件")

    # 统计推断策略
    strategy_counts = defaultdict(int)
    for eid, (year, strat, reason) in inferences.items():
        strategy_counts[strat] += 1
    for strat, cnt in sorted(strategy_counts.items()):
        print(f"    {strat}: {cnt}")

    if args.stats:
        return 0

    # 写入文件
    print(f"\n{'写入' if not args.dry_run else '预览'}...")

    if args.file:
        files = sorted(EVENTS_DIR.glob(f"{args.file}_*_事件索引.md"))
    else:
        files = sorted(EVENTS_DIR.glob("*_事件索引.md"))

    total_written = 0
    total_already = 0
    for fpath in files:
        w, a = write_inferred_to_file(
            fpath, inferences,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        if w > 0:
            status = "预览" if args.dry_run else "写入"
            print(f"  {fpath.name}: {status} {w}, 已有 {a}")
        total_written += w
        total_already += a

    print(f"\n{'='*50}")
    print(f"  写入: {total_written}")
    print(f"  已有: {total_already}")
    remaining = no_year - total_written
    print(f"  仍无年代: {remaining}")
    if args.dry_run:
        print("  (dry-run 模式，未写入文件)")
    print(f"{'='*50}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
