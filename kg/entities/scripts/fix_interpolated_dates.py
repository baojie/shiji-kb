#!/usr/bin/env python3
"""
fix_interpolated_dates.py - 修正插值法推断的错误年份

对审计发现的问题事件，通过以下方式修正：
1. 解析事件名/人物中的君主名，匹配 reign_periods.json
2. 用 time_str 中的纪年（如 %十三年%）计算 CE 年
3. 输出修正建议，可选自动应用
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVENTS_DIR = _PROJECT_ROOT / "kg" / "events" / "data"
REIGN_FILE = _PROJECT_ROOT / "kg" / "chronology" / "data" / "reign_periods.json"

# 中文数字转阿拉伯数字
CN_NUM = {'元': 1, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
          '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
          '百': 100, '廿': 20, '卅': 30}


def cn_to_int(cn_str):
    """中文数字转整数: '三十三' → 33, '元' → 1"""
    if cn_str == '元':
        return 1
    total = 0
    current = 0
    for ch in cn_str:
        if ch in CN_NUM:
            val = CN_NUM[ch]
            if val == 10:
                if current == 0:
                    current = 1
                total += current * 10
                current = 0
            elif val == 100:
                if current == 0:
                    current = 1
                total += current * 100
                current = 0
            elif val == 20:
                total += 20
                current = 0
            elif val == 30:
                total += 30
                current = 0
            else:
                current = val
        else:
            pass
    total += current
    return total if total > 0 else None


def load_reign_periods():
    with open(REIGN_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rulers = {}
    aliases = {}
    for key, val in data['rulers'].items():
        if isinstance(val, str):
            aliases[key] = val
        else:
            rulers[key] = val

    # 解析别名
    for alias, target in aliases.items():
        if target in rulers:
            rulers[alias] = rulers[target]

    return rulers


def extract_ruler_from_event(event_name, people, chapter_id):
    """从事件名和人物列表中推断出相关的君主"""
    # 常见模式：事件名以君主名开头
    # 如 "文公东迁", "缪公用百里傒", "景公卒哀公立"
    rulers_in_name = []

    # 从事件名中提取君主名（去掉标签符号后）
    clean_name = re.sub(r'[@=$%&^~*!?〖+〗〚〛]', '', event_name)

    # 匹配 X公/X王/X侯/X帝 等模式
    m = re.findall(r'([\u4e00-\u9fff]{1,3}(?:公|王|侯|帝|后|伯))', clean_name)
    if m:
        rulers_in_name.extend(m)

    # 从人物列表中提取
    for p in people:
        clean_p = re.sub(r'[@=$%&^~*!?〖+〗〚〛]', '', p)
        if re.match(r'.+(?:公|王|侯|帝|后)$', clean_p):
            rulers_in_name.append(clean_p)

    return rulers_in_name


def extract_regnal_year(time_str):
    """从时间字段提取纪年数字"""
    # 匹配 %N年% 或 %元年%
    m = re.search(r'%([元一二三四五六七八九十百廿卅]+年)%', time_str)
    if m:
        year_cn = m.group(1).replace('年', '')
        return cn_to_int(year_cn)

    # 匹配更复杂的模式
    m = re.search(r'([元一二三四五六七八九十百廿卅]+)年', time_str)
    if m:
        year_cn = m.group(1)
        return cn_to_int(year_cn)

    return None


def match_ruler_to_reign(ruler_name, chapter_id, reign_periods):
    """将事件中的君主名匹配到 reign_periods"""
    ch_num = chapter_id[:3]

    # 根据章节确定国家
    chapter_state_map = {
        '005': '秦', '006': '秦',
        '031': '吴', '032': '齐', '033': '鲁',
        '034': '燕', '035': '管蔡', '036': '陈',
        '037': '卫', '038': '宋', '039': '晋',
        '040': '楚', '041': '越', '042': '郑',
        '043': '赵', '044': '魏', '045': '韩',
        '046': '田齐',
        '004': '周',
        '003': '商', '002': '夏',
    }
    state = chapter_state_map.get(ch_num, '')

    # 尝试精确匹配
    candidates = []
    for key, info in reign_periods.items():
        if isinstance(info, str):
            continue
        if ruler_name == key:
            candidates.append((key, info))
        elif state and state + ruler_name == key:
            candidates.append((key, info))
        elif ruler_name in key:
            if info.get('state', '') == state or not state:
                candidates.append((key, info))

    # 如果有多个候选，优先本国的
    if len(candidates) > 1 and state:
        state_matches = [(k, i) for k, i in candidates if i.get('state') == state]
        if state_matches:
            candidates = state_matches

    return candidates[0] if candidates else None


def parse_all_events():
    """解析所有事件"""
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

            ce_year = None
            m = re.search(r'公元前(\d+)年', time_str)
            if m:
                ce_year = -int(m.group(1))
            else:
                m = re.search(r'公元(\d+)年', time_str)
                if m:
                    ce_year = int(m.group(1))

            people = re.findall(r'@([^@]+)@', people_str)
            clean_name = re.sub(r'[@=$%&^~*!?〖+〗〚〛]', '', event_name).strip()

            events.append({
                'event_id': event_id,
                'name': clean_name,
                'raw_name': event_name,
                'chapter_id': chapter_id,
                'ch_num': ch_num,
                'ce_year': ce_year,
                'time_str': time_str,
                'people': people,
                'file': str(fpath),
            })

    return events


def compute_corrections(events, reign_periods):
    """计算年份修正"""
    corrections = []

    for ev in events:
        if ev['ce_year'] is not None:
            continue  # 已有精确年份

        # 提取纪年
        regnal_year = extract_regnal_year(ev['time_str'])
        if regnal_year is None:
            continue

        # 推断君主
        rulers = extract_ruler_from_event(ev['name'], ev['people'], ev['chapter_id'])
        if not rulers:
            continue

        # 尝试匹配
        for ruler_name in rulers:
            match = match_ruler_to_reign(ruler_name, ev['chapter_id'], reign_periods)
            if match:
                key, info = match
                # 计算 CE 年: start_bce - (regnal_year - 1)
                ce_year = -(info['start_bce'] - (regnal_year - 1))
                corrections.append({
                    'event_id': ev['event_id'],
                    'name': ev['name'],
                    'chapter_id': ev['chapter_id'],
                    'time_str': ev['time_str'],
                    'ruler': key,
                    'regnal_year': regnal_year,
                    'computed_ce': ce_year,
                    'file': ev['file'],
                })
                break

    return corrections


def main():
    reign_periods = load_reign_periods()
    events = parse_all_events()

    corrections = compute_corrections(events, reign_periods)

    print(f"可计算修正: {len(corrections)} 个事件")
    print()

    # 按章节分组显示
    by_chapter = defaultdict(list)
    for c in corrections:
        by_chapter[c['chapter_id']].append(c)

    for ch, corrs in sorted(by_chapter.items()):
        print(f"\n## {ch}")
        for c in corrs:
            year_str = f"前{-c['computed_ce']}年" if c['computed_ce'] < 0 else f"{c['computed_ce']}年"
            print(f"  {c['event_id']} {c['name']}")
            print(f"    时间: {c['time_str']} → {c['ruler']}{c['regnal_year']}年 = 公元{year_str}")

    # 保存修正建议
    out_file = _PROJECT_ROOT / "kg" / "entities" / "data" / "interpolation_corrections.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(corrections, f, ensure_ascii=False, indent=2)
    print(f"\n修正建议已保存: {out_file}")


if __name__ == "__main__":
    main()
