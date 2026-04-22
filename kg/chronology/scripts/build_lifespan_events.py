#!/usr/bin/env python3
"""从 person_lifespans.json 生成可注入 timeline 的生卒年事件。

筛选规则
    - 排除 note == "传说"
    - 排除 note 单独为 "约" 或以 "约，..." 形式开头
    - 排除 note 中含 "约" 但不含明确在位/考证说明
    - 保留 note 为空、别名指向（如"商鞅"）、详细考证（含"在位"/"君主"/"即"）

去重策略
    对同一 (公元年, 生|卒) 组合：
    - 别名合并：生卒年完全相同的多个 person_key 只保留一条（优先长名/更正式名）
    - 已有事件抑制：若 kg/events/data/*_事件索引.md 同一公元年里已有包含该人物任一名称与生/卒关键词的事件，则跳过

输出
    kg/chronology/data/person_lifespan_events.json
        {
          "_doc": "...",
          "events": {
            "-551": [["LIFE-孔子-生", "孔子生", "047", false], ...],
            "-479": [["LIFE-孔子-卒", "孔子卒", "047", false]]
          },
          "persons_included": [...],
          "persons_skipped": [{"name":..., "reason":...}]
        }

使用：
    python kg/chronology/scripts/build_lifespan_events.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
LIFESPANS_FILE = BASE_DIR / 'kg' / 'entities' / 'data' / 'person_lifespans.json'
EVENTS_DIR = BASE_DIR / 'kg' / 'events' / 'data'
OUTPUT_FILE = BASE_DIR / 'kg' / 'chronology' / 'data' / 'person_lifespan_events.json'

# 判定：note 是否代表"明确纪年"
LEGEND_NOTES = {'传说'}
APPROX_PREFIX_RE = re.compile(r'^约(?:，|$)')
CERTAIN_KEYWORDS = ('在位', '君主', '即', '明确记载', '本纪', '世家', '之子', '之孙', '之弟', '皇帝', '太后')

# 同生卒年簇的主名选择：当 person_lifespans 中多条记录共享 (birth, death)，
# 显式指定以哪个名字作为事件显示主名。用于纠正默认 prefer() 的误选
# （如 刘邦 vs 高帝、项羽 vs 项王、英布 vs 黥布）。
PREFERRED_MAIN_NAME = {
    frozenset(['刘邦', '高祖', '高帝', '沛公']): '刘邦',
    frozenset(['项羽', '项王']): '项羽',
    frozenset(['英布', '黥布']): '英布',
    frozenset(['窦太后', '窦皇后']): '窦太后',
    frozenset(['秦昭王', '秦昭襄王']): '秦昭襄王',
    frozenset(['晋文公', '重耳']): '晋文公',
    frozenset(['秦穆公', '缪公']): '秦穆公',
    frozenset(['商鞅', '卫鞅']): '商鞅',
    frozenset(['范睢', '范雎']): '范雎',
    frozenset(['吴王刘濞', '刘濞']): '吴王刘濞',
    frozenset(['梁孝王', '刘武']): '梁孝王',
    frozenset(['陈胜', '吴广']): None,  # 不合并：两人，仅生卒年巧合相同
    frozenset(['伯夷', '叔齐']): None,  # 不合并：两人
}

# 人物级排除：这些 person_key 的生卒年不可信（上游数据 bug 或纯占位），不参与生成
EXCLUDE_PERSONS = {
    '蒙恬',  # 生卒年与秦始皇重合，疑为 person_lifespans 占位
}

# 人物主章（用于事件 ch_id 链接）— 只覆盖少量典型人物；其他归 000
CANONICAL_CHAPTER = {
    '孔子': '047', '刘邦': '008', '高祖': '008', '秦始皇': '006', '始皇': '006',
    '项羽': '007', '项王': '007', '汉武帝': '012', '武帝': '012',
    '汉文帝': '010', '文帝': '010', '汉景帝': '011', '景帝': '011',
    '汉惠帝': '009', '刘盈': '009', '吕后': '009',
    '齐桓公': '032', '管仲': '062',
    '晋文公': '039', '重耳': '039',
    '楚庄王': '040', '秦穆公': '005', '缪公': '005',
    '伍子胥': '066', '孙武': '065',
    '商鞅': '068', '卫鞅': '068',
    '孟尝君': '075', '平原君': '076', '信陵君': '077', '春申君': '078',
    '白起': '073', '王翦': '073', '廉颇': '081', '蔺相如': '081',
    '范睢': '079', '范雎': '079', '穰侯': '072', '魏冉': '072',
    '吴起': '065', '乐毅': '080',
    '韩信': '092', '萧何': '053', '张良': '055', '陈平': '056',
    '周勃': '057', '英布': '091', '黥布': '091', '彭越': '090',
    '陈胜': '048', '吴广': '048',
    '二世': '006', '胡亥': '006',
    '周公': '033', '太公': '032',
    '曹参': '054', '樊哙': '095', '灌婴': '095',
    '窦太后': '049', '窦皇后': '049',
    '梁孝王': '058', '刘武': '058', '吴王刘濞': '106', '刘濞': '106',
    '周亚夫': '057', '李广': '109', '卫青': '111', '霍去病': '111',
    '司马相如': '117', '董仲舒': '121',
    '秦昭王': '005', '秦昭襄王': '005', '秦武王': '005', '嬴荡': '005',
    '张仪': '070', '苏秦': '069',
    '老子': '063', '庄子': '063', '韩非': '063', '韩非子': '063',
    '屈原': '084', '贾谊': '084',
}


def is_explicit(note: str) -> tuple[bool, str]:
    """返回 (是否纳入, 原因)。"""
    note = note.strip()
    if not note:
        return True, 'empty_note'
    if note in LEGEND_NOTES:
        return False, '传说'
    if APPROX_PREFIX_RE.match(note):
        return False, '约'
    # 含"约"字但不伴随考证 → 排除（如"田文，约"/"魏冉，约"）
    if '约' in note and not any(kw in note for kw in CERTAIN_KEYWORDS):
        return False, '含约'
    return True, 'explicit'


def load_lifespans() -> dict:
    return json.loads(LIFESPANS_FILE.read_text(encoding='utf-8'))


def collect_alias_clusters(persons: dict) -> list[tuple[str, list[str]]]:
    """按 (birth, death) 聚类同生卒年的 person_key 为别名簇，并在簇内选主名。

    PREFERRED_MAIN_NAME 显式覆盖默认 prefer() 的选择：
    - 若 value 为字符串：使用该字符串作为主名
    - 若 value 为 None：拆分为多个独立人物（不合并）
    """
    clusters = defaultdict(list)
    for name, v in persons.items():
        if name in EXCLUDE_PERSONS:
            continue
        key = (v.get('birth'), v.get('death'))
        clusters[key].append(name)

    def prefer(names: list[str]) -> str:
        """默认选主名：优先带姓氏或长名，含'公'/'王'/'帝'等正式名加分。"""
        def score(n: str) -> tuple:
            formality = sum(c in n for c in '公王帝君侯后子祖皇')
            return (formality, len(n), n)
        return sorted(names, key=score, reverse=True)[0]

    result: list[tuple[str, list[str]]] = []
    for names in clusters.values():
        cluster_key = frozenset(names)
        if cluster_key in PREFERRED_MAIN_NAME:
            override = PREFERRED_MAIN_NAME[cluster_key]
            if override is None:
                # 不合并：每个名字单独成簇
                for n in names:
                    result.append((n, [n]))
                continue
            result.append((override, names))
        else:
            result.append((prefer(names), names))
    return result


def load_existing_birth_death_events() -> dict:
    """扫描 kg/events/data/*_事件索引.md，提取含生/卒/出生/薨/崩/死 且带公元年的事件，
    按 {(ce_year, action): set(name_snippets)} 索引，用于与 lifespans 去重。
    """
    pat_event_row = re.compile(r'^\|\s*(\d{3}-\d+)\s*\|\s*([^|]+?)\s*\|\s*[^|]*\|\s*([^|]+?)\s*\|', re.MULTILINE)
    pat_year = re.compile(r'[（\[](?:约)?公元前(\d+)年')
    pat_tag = re.compile(r'〖[@=;#%&◆\^~•!\+\$\?\{\:\[\_](?:[^〗|]+\|)?([^〗]+)〗')

    result = defaultdict(set)

    for fpath in sorted(EVENTS_DIR.glob('*_事件索引.md')):
        if fpath.name == '战争事件索引.md':
            continue
        text = fpath.read_text(encoding='utf-8')
        for m in pat_event_row.finditer(text):
            event_name_raw = m.group(2)
            time_field = m.group(3)
            # 清洗事件名：取标签内显示名
            event_name_clean = pat_tag.sub(r'\1', event_name_raw)

            ym = pat_year.search(time_field)
            if not ym:
                continue
            ce_year = -int(ym.group(1))

            # 判定动作类型
            if any(kw in event_name_clean for kw in ('出生', '生于', '诞生')):
                action = '生'
            elif re.search(r'(^|[^先])生$', event_name_clean):
                action = '生'
            elif any(kw in event_name_clean for kw in ('卒', '薨', '崩', '死', '殁')):
                action = '卒'
            else:
                continue

            result[(ce_year, action)].add(event_name_clean)
    return result


def event_matches_person(event_names: set[str], aliases: list[str]) -> bool:
    """若任一 alias 在任一 event_name 中出现则认为已有事件覆盖。"""
    for name in event_names:
        for alias in aliases:
            if alias and alias in name:
                return True
    return False


def build_lifespan_events() -> dict:
    data = load_lifespans()
    persons = data['persons']
    clusters = collect_alias_clusters(persons)
    existing = load_existing_birth_death_events()

    events_by_year: dict[int, list[list]] = defaultdict(list)
    included = []
    skipped = []

    for main_name, aliases in clusters:
        note = persons[main_name].get('note', '')
        ok, reason = is_explicit(note)
        if not ok:
            skipped.append({'name': main_name, 'aliases': aliases, 'reason': reason, 'note': note})
            continue

        birth = persons[main_name].get('birth')
        death = persons[main_name].get('death')
        ch_id = CANONICAL_CHAPTER.get(main_name, '000')
        for alias in aliases:
            ch_id = CANONICAL_CHAPTER.get(alias, ch_id) if ch_id == '000' else ch_id

        # 生
        if isinstance(birth, int):
            already = event_matches_person(existing.get((birth, '生'), set()), aliases)
            if not already:
                ev = [f'LIFE-{main_name}-生', f'{main_name}生', ch_id, False]
                events_by_year[birth].append(ev)

        # 卒
        if isinstance(death, int):
            already = event_matches_person(existing.get((death, '卒'), set()), aliases)
            if not already:
                ev = [f'LIFE-{main_name}-卒', f'{main_name}卒', ch_id, False]
                events_by_year[death].append(ev)

        included.append({'name': main_name, 'aliases': aliases, 'birth': birth, 'death': death})

    # 稳定排序
    events_sorted = {str(yr): sorted(evs) for yr, evs in sorted(events_by_year.items())}

    return {
        '_doc': '由 person_lifespans.json 中明确纪年的人物派生的生/卒事件，用于 timeline.html 注入',
        '_generator': 'kg/chronology/scripts/build_lifespan_events.py',
        '_filters': {
            '排除note': ['传说', '约', '约，...', '含约且无考证'],
            '别名合并': '同生卒年的 person_key 合并为一条，选长名/正式名为主',
            '去重': '与 kg/events/data/*_事件索引.md 中已有的生/卒事件按人名子串匹配去重',
        },
        'events': events_sorted,
        'persons_included': included,
        'persons_skipped': skipped,
    }


def main():
    result = build_lifespan_events()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    n_events = sum(len(v) for v in result['events'].values())
    n_years = len(result['events'])
    n_included = len(result['persons_included'])
    n_skipped = len(result['persons_skipped'])
    print(f'Wrote {OUTPUT_FILE}')
    print(f'  persons: {n_included} included / {n_skipped} skipped')
    print(f'  events:  {n_events} across {n_years} distinct CE years')


if __name__ == '__main__':
    main()
