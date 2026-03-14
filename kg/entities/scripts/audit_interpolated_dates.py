#!/usr/bin/env python3
"""
audit_interpolated_dates.py - 审计所有基于插值法推断的事件年份

策略：
1. 重现 infer_undated_events 的推断逻辑，记录每个事件使用的策略
2. 对插值法（策略2）推断的事件，逐一检查：
   - 插值来源（前/后哪个事件的年份）
   - 与事件中人物生卒年的一致性
   - 与事件时间字段（年号、君主纪年）的一致性
3. 生成审计报告
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

# 从 build_entity_index.py 复制的 CHAPTER_ERA
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


def load_reign_periods():
    """加载君主在位期（用于验证纪年推断）"""
    try:
        with open(REIGN_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('rulers', {})
    except FileNotFoundError:
        return {}


def parse_all_events():
    """解析所有事件索引文件，提取完整事件信息"""
    events = []
    for fpath in sorted(EVENTS_DIR.glob('*_事件索引.md')):
        chapter_id = fpath.stem.replace('_事件索引', '')
        ch_num = chapter_id[:3]
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        # 解析概览表
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

            # 提取 CE 年
            ce_year = None
            m = re.search(r'公元前(\d+)年', time_str)
            if m:
                ce_year = -int(m.group(1))
            else:
                m = re.search(r'公元(\d+)年', time_str)
                if m:
                    ce_year = int(m.group(1))

            # 提取人物
            people = re.findall(r'@([^@]+)@', people_str)
            clean_name = re.sub(r'[@=$%&^~*!?〖+〗〚〛]', '', event_name).strip()

            events.append({
                'event_id': event_id,
                'name': clean_name,
                'chapter_id': chapter_id,
                'ch_num': ch_num,
                'ce_year': ce_year,
                'time_str': time_str,
                'people': people,
            })

    return events


def person_active_range(people_list, lifespans):
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


def simulate_inference(events, lifespans):
    """重现推断逻辑，记录每个事件使用的策略"""
    # 按章节分组
    by_chapter = defaultdict(list)
    for ev in events:
        by_chapter[ev['ch_num']].append(ev)

    results = []

    for ch_num, ch_events in sorted(by_chapter.items()):
        ch_events.sort(key=lambda x: x['event_id'])

        # 收集已知 CE 年的位置
        dated_positions = []
        for i, ev in enumerate(ch_events):
            if ev['ce_year'] is not None:
                dated_positions.append((i, ev['ce_year'], ev['event_id']))

        for i, ev in enumerate(ch_events):
            if ev['ce_year'] is not None:
                continue  # 已有精确年份，跳过

            strategy = None
            inferred = None
            source_info = None

            # 策略1: 人物生卒年交集
            if ev['people'] and lifespans:
                lb, ed, matched = person_active_range(ev['people'], lifespans)
                if lb is not None and ed is not None:
                    inferred = (lb + ed) // 2
                    strategy = 'person_lifespan'
                    source_info = {
                        'range': (lb, ed),
                        'persons': [(p, b, d) for b, d, p in matched]
                    }

            # 策略2: 章节内插值
            if inferred is None and dated_positions:
                prev_year = None
                prev_eid = None
                next_year = None
                next_eid = None
                for pos, year, eid in dated_positions:
                    if pos <= i:
                        prev_year = year
                        prev_eid = eid
                    if pos >= i and next_year is None:
                        next_year = year
                        next_eid = eid

                if prev_year is not None and next_year is not None:
                    inferred = prev_year
                    strategy = 'interpolation'
                    source_info = {
                        'prev': (prev_eid, prev_year),
                        'next': (next_eid, next_year),
                        'method': 'both_neighbors'
                    }
                elif prev_year is not None:
                    inferred = prev_year
                    strategy = 'interpolation'
                    source_info = {
                        'prev': (prev_eid, prev_year),
                        'next': None,
                        'method': 'prev_only'
                    }
                elif next_year is not None:
                    inferred = next_year
                    strategy = 'interpolation'
                    source_info = {
                        'prev': None,
                        'next': (next_eid, next_year),
                        'method': 'next_only'
                    }

            # 策略3: 章节时代兜底
            if inferred is None:
                inferred = CHAPTER_ERA.get(ch_num)
                strategy = 'chapter_era'
                source_info = {'chapter': ch_num}

            # 合理性检查
            adjusted = False
            if inferred is not None and ev['people'] and lifespans:
                lb, ed, matched = person_active_range(ev['people'], lifespans)
                if lb is not None and ed is not None:
                    original = inferred
                    if inferred < lb - 20:
                        inferred = (lb + ed) // 2
                        adjusted = True
                    elif inferred > ed + 20:
                        inferred = (lb + ed) // 2
                        adjusted = True

            if strategy == 'interpolation':
                results.append({
                    'event_id': ev['event_id'],
                    'name': ev['name'],
                    'chapter_id': ev['chapter_id'],
                    'ch_num': ch_num,
                    'time_str': ev['time_str'],
                    'people': ev['people'],
                    'inferred_year': inferred,
                    'strategy': strategy,
                    'source_info': source_info,
                    'adjusted': adjusted,
                })

    return results


def validate_interpolated(results, lifespans):
    """对插值推断的结果进行深度验证"""
    issues = []

    for r in results:
        problems = []

        # 1. 检查与人物生卒年一致性
        if r['people']:
            lb, ed, matched = person_active_range(r['people'], lifespans)
            if matched:
                for person, birth, death in [(p, b, d) for b, d, p in matched]:
                    if r['inferred_year'] < birth - 10:
                        problems.append(
                            f"在{person}出生(前{-birth}年)之前{birth - r['inferred_year']}年")
                    elif r['inferred_year'] > death + 10:
                        problems.append(
                            f"在{person}死亡(前{-death}年)之后{r['inferred_year'] - death}年")

        # 2. 检查插值来源的合理性
        si = r['source_info']
        if si.get('prev') and si.get('next'):
            prev_year = si['prev'][1]
            next_year = si['next'][1]
            # 如果前后事件年份差距很大，插值可能不准
            gap = abs(next_year - prev_year)
            if gap > 200:
                problems.append(
                    f"插值来源跨度过大: {si['prev'][0]}(前{-prev_year}年) → "
                    f"{si['next'][0]}(前{-next_year}年), 差{gap}年")

        # 3. 检查时间字段是否包含可用的纪年信息
        time_str = r['time_str']
        if time_str and time_str != '-':
            # 有时间字段但没被解析为 CE 年 → 可能有君主纪年信息
            if re.search(r'[元一二三四五六七八九十百]+年', time_str):
                problems.append(f"时间字段'{time_str}'包含纪年信息但未解析")

        if problems:
            issues.append({
                'event': r,
                'problems': problems,
            })

    return issues


def main():
    lifespans = load_lifespans()
    events = parse_all_events()

    print(f"事件总数: {len(events)}")
    dated = [e for e in events if e['ce_year'] is not None]
    undated = [e for e in events if e['ce_year'] is None]
    print(f"有精确纪年: {len(dated)}, 无精确纪年: {len(undated)}")

    # 模拟推断
    interpolated = simulate_inference(events, lifespans)
    print(f"\n基于插值法推断的事件: {len(interpolated)}")

    # 按章节统计
    by_chapter = defaultdict(list)
    for r in interpolated:
        by_chapter[r['ch_num']].append(r)

    # 验证
    issues = validate_interpolated(interpolated, lifespans)
    print(f"发现问题: {len(issues)}")

    # 输出详细报告
    print(f"\n{'='*80}")
    print("插值法推断年份审计报告")
    print(f"{'='*80}")

    # 按问题严重程度排序
    critical = []  # 与人物生卒年冲突
    warning = []   # 插值跨度大或有未解析纪年
    info = []      # 信息提示

    for issue in issues:
        has_person_conflict = any('出生' in p or '死亡' in p for p in issue['problems'])
        has_large_gap = any('跨度过大' in p for p in issue['problems'])
        has_unresolved = any('未解析' in p for p in issue['problems'])

        if has_person_conflict:
            critical.append(issue)
        elif has_large_gap:
            warning.append(issue)
        elif has_unresolved:
            info.append(issue)

    if critical:
        print(f"\n## 严重问题：年代与人物生卒年冲突 ({len(critical)})")
        print("-" * 60)
        for issue in critical:
            r = issue['event']
            year_str = f"前{-r['inferred_year']}年" if r['inferred_year'] < 0 else f"{r['inferred_year']}年"
            print(f"\n  {r['event_id']} {r['name']}")
            print(f"    推断年份: {year_str} (来源: {_format_source(r['source_info'])})")
            if r['time_str'] and r['time_str'] != '-':
                print(f"    原时间: {r['time_str']}")
            print(f"    人物: {', '.join(r['people'])}")
            for p in issue['problems']:
                print(f"    ❌ {p}")

    if warning:
        print(f"\n## 警告：插值跨度过大 ({len(warning)})")
        print("-" * 60)
        for issue in warning:
            r = issue['event']
            year_str = f"前{-r['inferred_year']}年" if r['inferred_year'] < 0 else f"{r['inferred_year']}年"
            print(f"\n  {r['event_id']} {r['name']}")
            print(f"    推断年份: {year_str}")
            if r['time_str'] and r['time_str'] != '-':
                print(f"    原时间: {r['time_str']}")
            for p in issue['problems']:
                print(f"    ⚠️  {p}")

    if info:
        print(f"\n## 提示：有纪年信息未被解析 ({len(info)})")
        print("-" * 60)
        for issue in info:
            r = issue['event']
            year_str = f"前{-r['inferred_year']}年" if r['inferred_year'] < 0 else f"{r['inferred_year']}年"
            print(f"  {r['event_id']} {r['name']} → {year_str} | 时间: {r['time_str']}")

    # 无问题的插值事件汇总
    no_issue_count = len(interpolated) - len(issues)
    print(f"\n{'='*80}")
    print(f"总结:")
    print(f"  插值推断事件: {len(interpolated)}")
    print(f"  严重问题（人物生卒年冲突）: {len(critical)}")
    print(f"  警告（跨度过大）: {len(warning)}")
    print(f"  提示（有未解析纪年）: {len(info)}")
    print(f"  无明显问题: {no_issue_count}")

    # 输出所有插值事件的明细到文件
    report_file = _PROJECT_ROOT / "kg" / "entities" / "data" / "interpolation_audit.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_interpolated': len(interpolated),
            'critical': len(critical),
            'warning': len(warning),
            'info': len(info),
            'events': [{
                'event_id': r['event_id'],
                'name': r['name'],
                'chapter': r['chapter_id'],
                'time_str': r['time_str'],
                'people': r['people'],
                'inferred_year': r['inferred_year'],
                'source': _format_source(r['source_info']),
                'adjusted': r['adjusted'],
            } for r in interpolated]
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  完整明细: {report_file}")

    return 0


def _format_source(source_info):
    parts = []
    if source_info.get('prev'):
        eid, year = source_info['prev']
        parts.append(f"前:{eid}(前{-year}年)" if year < 0 else f"前:{eid}({year}年)")
    if source_info.get('next'):
        eid, year = source_info['next']
        parts.append(f"后:{eid}(前{-year}年)" if year < 0 else f"后:{eid}({year}年)")
    return ', '.join(parts) if parts else '未知'


if __name__ == "__main__":
    sys.exit(main())
