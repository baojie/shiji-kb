#!/usr/bin/env python3
"""
validate_event_dates.py - 用人物生卒年验证事件年代

策略：
1. 加载人物生卒年数据库
2. 对每个事件，检查其 CE 年是否在所提到人物的生存期间内
3. 报告冲突（事件年代在人物出生前或死亡后）
4. 对推断年代的事件，用人物生卒年修正

用法:
    python3 kg/entities/scripts/validate_event_dates.py          # 检查并报告
    python3 kg/entities/scripts/validate_event_dates.py --fix    # 修正推断年代
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

TOLERANCE = 20  # 允许 20 年误差（生卒年本身可能不精确）


def load_lifespans():
    """加载人物生卒年"""
    with open(LIFESPANS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['persons']


def load_reign_periods():
    """从 reign_periods 中提取额外的活跃期信息"""
    with open(REIGN_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    periods = {}
    for ruler, info in data['rulers'].items():
        periods[ruler] = {
            'birth': -(info['start_bce'] + 30),  # 估计即位前30年出生
            'death': -(info['end_bce'] - 5),      # 估计退位后5年去世
            'reign_start': -info['start_bce'],
            'reign_end': -info['end_bce'],
        }
    return periods


def parse_events():
    """解析所有事件索引文件，提取事件及其 CE 年和人物"""
    events = []

    for fpath in sorted(EVENTS_DIR.glob('*_事件索引.md')):
        chapter_id = fpath.stem.replace('_事件索引', '')
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析概览表
        lines = content.split('\n')
        in_table = False
        for line in lines:
            line = line.strip()
            if line.startswith('| 事件ID'):
                in_table = True
                continue
            if in_table and line.startswith('|---'):
                continue
            if in_table and not line.startswith('|'):
                in_table = False
                continue
            if not in_table:
                continue

            cols = [c.strip() for c in line.split('|')]
            if len(cols) < 7:
                continue

            event_id = cols[1].strip()
            event_name = cols[2].strip()
            time_str = cols[4].strip()
            people_str = cols[6].strip()

            # 提取 CE 年
            ce_year = None
            is_explicit = False
            m = re.search(r'公元前(\d+)年', time_str)
            if m:
                ce_year = -int(m.group(1))
                is_explicit = True
            else:
                m = re.search(r'公元(\d+)年', time_str)
                if m:
                    ce_year = int(m.group(1))
                    is_explicit = True

            # 提取人物（事件索引文件仍使用v1格式）
            people = re.findall(r'@([^@]+)@', people_str)
            clean_name = re.sub(r'[@=$%&^~*!?〖+〗〚〛]', '', event_name).strip()

            events.append({
                'event_id': event_id,
                'name': clean_name,
                'chapter_id': chapter_id,
                'ce_year': ce_year,
                'is_explicit': is_explicit,
                'time_str': time_str,
                'people': people,
            })

    return events


def estimate_person_active_period(person_name, lifespans, reign_periods):
    """获取人物的活跃年代范围 (earliest_year, latest_year)"""
    if person_name in lifespans:
        info = lifespans[person_name]
        return info['birth'], info['death']

    if person_name in reign_periods:
        info = reign_periods[person_name]
        return info['birth'], info['death']

    return None, None


def validate_events(events, lifespans, reign_periods):
    """验证事件年代与人物生卒年的一致性

    Returns:
        violations: list of dicts with error info
        suggestions: dict of event_id -> suggested_ce_year
    """
    violations = []
    suggestions = {}

    for ev in events:
        if ev['ce_year'] is None or not ev['people']:
            continue

        person_ranges = []
        for person in ev['people']:
            birth, death = estimate_person_active_period(
                person, lifespans, reign_periods)
            if birth is not None and death is not None:
                person_ranges.append((person, birth, death))

        if not person_ranges:
            continue

        # 检查事件年代是否在所有人物的生存期间内
        for person, birth, death in person_ranges:
            if ev['ce_year'] < birth - TOLERANCE:
                violations.append({
                    'event_id': ev['event_id'],
                    'name': ev['name'],
                    'ce_year': ev['ce_year'],
                    'is_explicit': ev['is_explicit'],
                    'person': person,
                    'person_birth': birth,
                    'person_death': death,
                    'error': 'before_birth',
                    'msg': f"事件{ev['ce_year']}在{person}出生{birth}之前",
                })
            elif ev['ce_year'] > death + TOLERANCE:
                violations.append({
                    'event_id': ev['event_id'],
                    'name': ev['name'],
                    'ce_year': ev['ce_year'],
                    'is_explicit': ev['is_explicit'],
                    'person': person,
                    'person_birth': birth,
                    'person_death': death,
                    'error': 'after_death',
                    'msg': f"事件{ev['ce_year']}在{person}死亡{death}之后",
                })

        # 对无精确纪年的事件，建议用人物生卒年的交集区间
        if not ev['is_explicit'] and person_ranges:
            # 求所有人物生存期的交集
            latest_birth = max(b for _, b, _ in person_ranges)
            earliest_death = min(d for _, _, d in person_ranges)
            if latest_birth <= earliest_death:
                midpoint = (latest_birth + earliest_death) // 2
                suggestions[ev['event_id']] = {
                    'suggested': midpoint,
                    'range': (latest_birth, earliest_death),
                    'current': ev['ce_year'],
                }

    return violations, suggestions


def main():
    fix_mode = '--fix' in sys.argv

    lifespans = load_lifespans()
    reign_periods = load_reign_periods()
    events = parse_events()

    print(f"已加载: {len(lifespans)} 个人物生卒年, "
          f"{len(reign_periods)} 个君主在位期")
    print(f"事件总数: {len(events)}")

    dated_events = [e for e in events if e['ce_year'] is not None]
    print(f"有纪年事件: {len(dated_events)}")

    violations, suggestions = validate_events(
        events, lifespans, reign_periods)

    # 按严重程度排序（距离越大越严重）
    for v in violations:
        if v['error'] == 'before_birth':
            v['gap'] = v['person_birth'] - v['ce_year']
        else:
            v['gap'] = v['ce_year'] - v['person_death']
    violations.sort(key=lambda x: -x['gap'])

    # 输出报告
    print(f"\n{'='*70}")
    print(f"年代冲突: {len(violations)} 处")
    print(f"{'='*70}")

    # 按事件分组
    by_event = defaultdict(list)
    for v in violations:
        by_event[v['event_id']].append(v)

    explicit_errors = []
    inferred_errors = []

    for eid, vlist in sorted(by_event.items()):
        is_explicit = vlist[0]['is_explicit']
        if is_explicit:
            explicit_errors.append((eid, vlist))
        else:
            inferred_errors.append((eid, vlist))

    if explicit_errors:
        print(f"\n## 精确纪年错误 ({len(explicit_errors)} 个事件)")
        print("  这些事件的 CE 年来自源文件标注，可能是原始标注错误")
        for eid, vlist in explicit_errors:
            v0 = vlist[0]
            print(f"\n  {eid} {v0['name']} (标注: 公元{v0['ce_year']}年)")
            for v in vlist:
                gap_str = f"差{v['gap']}年"
                print(f"    {v['error']}: {v['person']} "
                      f"({v['person_birth']}~{v['person_death']}) {gap_str}")
            if eid in suggestions:
                s = suggestions[eid]
                print(f"    建议: {s['suggested']} "
                      f"(范围 {s['range'][0]}~{s['range'][1]})")

    if inferred_errors:
        print(f"\n## 推断纪年错误 ({len(inferred_errors)} 个事件)")
        print("  这些事件无精确纪年，可用人物生卒年修正")
        shown = 0
        for eid, vlist in inferred_errors:
            if shown >= 100:
                print(f"  ... 还有 {len(inferred_errors) - 100} 个")
                break
            v0 = vlist[0]
            line = (f"  {eid} {v0['name']}: "
                    f"当前{v0['ce_year']} → ")
            if eid in suggestions:
                s = suggestions[eid]
                line += f"建议{s['suggested']} ({s['range'][0]}~{s['range'][1]})"
            else:
                line += f"冲突人物: {', '.join(v['person'] for v in vlist)}"
            print(line)
            shown += 1

    # 统计
    print(f"\n{'='*70}")
    print(f"总结:")
    print(f"  精确纪年错误: {len(explicit_errors)} 个事件")
    print(f"  推断纪年错误: {len(inferred_errors)} 个事件")
    print(f"  可修正建议: {len(suggestions)} 个")

    # 输出建议到文件
    if suggestions:
        out_file = _PROJECT_ROOT / "kg" / "entities" / "data" / "date_corrections.json"
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(suggestions, f, ensure_ascii=False, indent=2)
        print(f"  修正建议已保存: {out_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
