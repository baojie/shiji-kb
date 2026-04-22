#!/usr/bin/env python3
"""按 SKILL 07a 对人物生卒年做区间推断，输出 person_lifespans_v2.json。

证据来源（按优先级）
    1. 文本模式：生X岁立 / 年X岁卒 / 立X年卒（方法 2-3，SKILL 07a §三）
    2. reign_periods.json：君主在位起止年（卒年强约束；生年可按即位年 -10~-60 给宽区间）
    3. person_lifespans.json（既有 v1）：外部来源，作为参考 / 冲突检测

输出格式：SKILL 07a §2.1 的 v2 区间格式
    {
      "persons": {
        "秦缪公": {
          "birth_min": -724, "birth_max": -660,
          "death_min": -621, "death_max": -621,
          "birth_label": "[约公元前682年]",
          "death_label": "（公元前621年）",
          "confidence": "high",
          "state": "秦",
          "evidence": [
            "reign_periods: 在位 659–621 BCE",
            "v1 lifespans: 生卒 682~621 BCE（外部）"
          ]
        }
      }
    }

使用：
    python kg/entities/scripts/infer_lifespans.py
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
REIGN_FILE = BASE_DIR / 'kg' / 'chronology' / 'data' / 'reign_periods.json'
LIFESPAN_V1 = BASE_DIR / 'kg' / 'entities' / 'data' / 'person_lifespans.json'
CHAPTER_DIR = BASE_DIR / 'chapter_md'
EVENTS_DIR = BASE_DIR / 'kg' / 'events' / 'data'
OUTPUT_FILE = BASE_DIR / 'kg' / 'entities' / 'data' / 'person_lifespans_v2.json'

# ============================================================
# 中文数字转阿拉伯
# ============================================================

CN_DIGITS = {'零': 0, '〇': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
             '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '百': 100, '千': 1000}


def cn_to_int(s: str) -> int | None:
    """简单中文数字转整数，支持 "二十"、"三十五"、"百有馀岁" 等常见写法。"""
    s = s.strip()
    # 去掉量词和修饰
    for ch in ('有', '馀', '余', '岁', '载', '年'):
        s = s.replace(ch, '')
    if not s:
        return None
    # 纯阿拉伯数字
    if s.isdigit():
        return int(s)
    # 逐字解析
    total, unit, num = 0, 1, 0
    try:
        for ch in s:
            v = CN_DIGITS.get(ch)
            if v is None:
                return None
            if v >= 10:  # 十 百 千
                if num == 0:
                    num = 1
                total += num * v
                num = 0
            else:
                num = v
        total += num
        return total if total > 0 else None
    except Exception:
        return None


# ============================================================
# Pattern extraction
# ============================================================

RULER_PREFIX = r'〖[@;◆^=][^〗]+?〗'

PATTERNS = {
    'REIGN_LEN': re.compile(
        r'(?P<ruler>' + RULER_PREFIX + r')(?:[^。〗]{0,8})立〖%(?P<n>[^〗|]+?)年(?:\|时长)?〗[^。]{0,8}(?:卒|崩|薨|而卒|而崩|而薨)'
    ),
    'AGE_AT_ACC': re.compile(
        r'(?P<ruler>' + RULER_PREFIX + r')生〖%(?P<n>[^〗|]+?)岁(?:\|[^〗]*)?〗(?:而)?(?:⟦○立⟧|而立|立)'
    ),
    'AGE_AT_DEATH': re.compile(
        r'(?P<ruler>' + RULER_PREFIX + r')(?:[^。]{0,15})(?:享|享年|年|寿)〖%(?P<n>[^〗|]+?)岁?(?:\|[^〗]*)?〗(?:[^。]{0,3})(?:卒|崩|薨)'
    ),
}

RULER_NAME_RE = re.compile(r'〖[@;◆^=]([^〗|]+?)(?:\|([^〗]+))?〗')


def extract_ruler_name(tag: str) -> str:
    """从 〖@name|canonical〗 取消歧后的规范名；无消歧则取显示名。"""
    m = RULER_NAME_RE.match(tag)
    if not m:
        return tag
    display, canonical = m.group(1), m.group(2)
    return (canonical or display).strip()


def scan_patterns() -> dict[str, list[dict]]:
    """扫描所有 tagged.md，按模式名分组收集证据。"""
    found = defaultdict(list)
    for fpath in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        ch_id = fpath.name[:3]
        text = fpath.read_text(encoding='utf-8')
        for pat_name, pat in PATTERNS.items():
            for m in pat.finditer(text):
                ruler = extract_ruler_name(m.group('ruler'))
                n_str = m.group('n')
                n = cn_to_int(n_str)
                if n is None:
                    continue
                found[pat_name].append({
                    'ruler': ruler,
                    'value': n,
                    'raw': n_str,
                    'chapter': ch_id,
                    'context': text[max(0, m.start()-20):m.end()+5].replace('\n', ' '),
                })
    return found


# ============================================================
# Inference
# ============================================================

def signed_bce(bce: int) -> int:
    """Convert positive BCE → signed CE (negative)."""
    return -bce if bce > 0 else bce


def fmt_year(year_ce: int) -> str:
    return f'公元前{-year_ce}年' if year_ce < 0 else f'公元{year_ce}年'


STATE_PREFIXES = ['秦', '齐', '晋', '楚', '鲁', '宋', '卫', '陈', '蔡', '曹',
                  '郑', '燕', '吴', '魏', '韩', '赵', '周', '汉']


def resolve_to_canonical(name: str, reign_aliases: dict, v1_persons: dict, rulers: dict) -> str:
    """尝试把任意名字解析为 rulers 的规范键。找不到则返回原名。"""
    if name in rulers:
        return name
    # reign_aliases 一级跳
    if name in reign_aliases and reign_aliases[name] in rulers:
        return reign_aliases[name]
    # v1 note 指向
    v1 = v1_persons.get(name)
    if v1:
        note = (v1.get('note') or '').strip()
        if note and len(note) <= 5 and note in rulers:
            return note
    # 国名前缀
    for sp in STATE_PREFIXES:
        cand = sp + name
        if cand in rulers:
            return cand
    # 缪↔穆
    if '缪' in name:
        alt = name.replace('缪', '穆')
        if alt in rulers:
            return alt
        for sp in STATE_PREFIXES:
            cand = sp + alt
            if cand in rulers:
                return cand
    if '穆' in name:
        alt = name.replace('穆', '缪')
        if alt in rulers:
            return alt
    return name


def build_alias_map(reign_aliases: dict, v1_persons: dict, rulers: dict,
                    extra_names: set[str] | None = None) -> dict:
    """构建 任意名字 → 规范名 映射。"""
    alias_map: dict[str, str] = {}
    candidates = set(v1_persons.keys()) | set(reign_aliases.keys())
    if extra_names:
        candidates |= extra_names
    for name in candidates:
        canonical = resolve_to_canonical(name, reign_aliases, v1_persons, rulers)
        if canonical != name:
            alias_map[name] = canonical
    return alias_map


def load_event_deaths() -> dict[str, int]:
    """从 kg/events/data/*_事件索引.md 提取"X卒/薨/崩"事件的公元年，返回 {person: ce_year}。
    用于为非君主人物补充卒年锚点（如张苍）。

    事件索引行列序：| 事件ID | 事件名称 | 事件类型 | 时间 | 地点 | 主要人物 | 朝代 |
    """
    pat_year = re.compile(r'[（\[](?:约)?公元前(\d+)年')
    pat_person = re.compile(r'〖@([^〗|]+?)(?:\|([^〗]+))?〗')
    pat_death = re.compile(r'(?:卒|薨|崩)(?:$|[^徒])')
    result: dict[str, int] = {}

    for fpath in sorted(EVENTS_DIR.glob('*_事件索引.md')):
        if fpath.name == '战争事件索引.md':
            continue
        text = fpath.read_text(encoding='utf-8')
        for line in text.splitlines():
            if not line.startswith('|') or line.startswith('|---'):
                continue
            cols = [c.strip() for c in line.split('|')]
            # 期望 cols[1]=事件ID, cols[2]=事件名称, cols[4]=时间, cols[6]=主要人物
            if len(cols) < 7:
                continue
            event_id = cols[1]
            if not re.match(r'\d{3}-\d+', event_id):
                continue
            event_name = cols[2]
            time_field = cols[4]
            persons_field = cols[6]

            if not pat_death.search(event_name):
                continue
            ym = pat_year.search(time_field)
            if not ym:
                continue
            ce_year = -int(ym.group(1))

            # 先从"主要人物"列取首位 @标签 人名
            person_names: list[str] = []
            for pm in pat_person.finditer(persons_field):
                person_names.append((pm.group(2) or pm.group(1)).strip())
            # 若事件名称含 @标签 则优先
            for pm in pat_person.finditer(event_name):
                person_names.insert(0, (pm.group(2) or pm.group(1)).strip())
            # 兜底：若事件名称以"X 卒/薨/崩"开头，取首字至卒前的片段
            if not person_names:
                m = re.match(r'^([\u4e00-\u9fa5]+?)(?:免相病?|病|免相)?(?:卒|薨|崩)', event_name)
                if m:
                    person_names.append(m.group(1))

            if person_names:
                result.setdefault(person_names[0], ce_year)
    return result


def infer_all():
    reign_data = json.loads(REIGN_FILE.read_text(encoding='utf-8'))
    rulers = reign_data['rulers']
    aliases = reign_data.get('aliases', {})
    v1 = json.loads(LIFESPAN_V1.read_text(encoding='utf-8'))
    v1_persons = v1['persons']
    event_deaths = load_event_deaths()

    # 模式扫描结果（提前以收集名字）
    evidence_by_pattern = scan_patterns()
    pattern_names = {h['ruler'] for hits in evidence_by_pattern.values() for h in hits}
    extra_names = pattern_names | set(event_deaths.keys())
    alias_to_canonical = build_alias_map(aliases, v1_persons, rulers, extra_names=extra_names)

    def canon(name: str) -> str:
        return alias_to_canonical.get(name, name)

    # 按人物聚合（已规范化）
    pattern_by_person: dict[str, list[dict]] = defaultdict(list)
    for pat_name, hits in evidence_by_pattern.items():
        for h in hits:
            pattern_by_person[canon(h['ruler'])].append({**h, 'pattern': pat_name})

    # 事件死亡也规范化
    event_deaths_canon: dict[str, int] = {}
    for name, year in event_deaths.items():
        event_deaths_canon.setdefault(canon(name), year)

    # v1 人物 也合并别名（保留首个出现，其余忽略避免歧义）
    v1_canon: dict[str, dict] = {}
    for name, v in v1_persons.items():
        c = canon(name)
        if c not in v1_canon:
            v1_canon[c] = v
        # 冲突时若当前值没 note 但新值有，则替换
        elif not (v1_canon[c].get('note') or '') and (v.get('note') or ''):
            v1_canon[c] = v

    # 候选人物：reign_periods + v1（canon） + 模式 + 事件卒年
    all_persons = (set(rulers.keys()) | set(v1_canon.keys())
                   | set(pattern_by_person.keys()) | set(event_deaths_canon.keys()))

    result_persons: dict[str, dict] = {}
    for name in sorted(all_persons):
        entry = infer_one(name, rulers, v1_canon,
                          pattern_by_person.get(name, []),
                          event_deaths_canon.get(name))
        if entry is not None:
            result_persons[name] = entry

    # 统计
    conf_count = defaultdict(int)
    birth_conf_count = defaultdict(int)
    death_conf_count = defaultdict(int)
    for v in result_persons.values():
        conf_count[v['confidence']] += 1
        birth_conf_count[v.get('birth_confidence', 'n/a')] += 1
        death_conf_count[v.get('death_confidence', 'n/a')] += 1
    sources_count = defaultdict(int)
    for v in result_persons.values():
        for src in v.get('sources', []):
            sources_count[src] += 1

    return {
        '_doc': '史记人物生卒年 v2：按 SKILL 07a 区间推断，合并 reign_periods + 文本模式 + v1 lifespans',
        '_generator': 'kg/entities/scripts/infer_lifespans.py',
        '_schema_ref': 'skills/SKILL_07a_人物生卒年推断.md §2.1',
        '_stats': {
            'total_persons': len(result_persons),
            'confidence_distribution': dict(conf_count),
            'birth_confidence_distribution': dict(birth_conf_count),
            'death_confidence_distribution': dict(death_conf_count),
            'source_distribution': dict(sources_count),
            'pattern_evidence': {k: len(v) for k, v in evidence_by_pattern.items()},
        },
        'persons': result_persons,
    }


# 置信度优先级（低→高）
CONF_RANK = {'low': 0, 'external': 1, 'approximate': 1, 'medium': 2, 'legend': 2, 'high': 3, 'exact': 4}


def promote(current: str, new: str) -> str:
    """返回更高置信度。legend 不被 high/exact 覆盖（属于特殊标记）。"""
    if current == 'legend':
        return 'legend'
    return new if CONF_RANK.get(new, 0) > CONF_RANK.get(current, 0) else current


def infer_one(name: str, rulers: dict, v1_persons: dict,
              patterns: list[dict], event_death_year: int | None = None) -> dict | None:
    """对单个人物应用证据链推断生卒年区间。

    置信度分生/卒两路：
    - 十表（reign_periods）中的卒年 → death_confidence=high
    - 文本模式（立X年卒 / 生X岁立 / 享年X岁）→ 对应路 high
    - 事件索引卒年 → death_confidence=high（来自原文事件锚点）
    - v1 lifespans 外部来源 → medium（无考证）；approximate → low；传说 → legend
    - reign_periods 派生的生年（由即位年 ±10~60 岁推得）→ birth_confidence=low
    """
    evidence: list[str] = []
    sources: set[str] = set()
    state: str | None = None

    birth_min = birth_max = None
    death_min = death_max = None
    birth_conf = 'low'
    death_conf = 'low'

    # Source 1: reign_periods（十表）
    if name in rulers:
        r = rulers[name]
        state = r.get('state')
        sources.add('reign_periods')
        start = signed_bce(r['start_bce'])
        end = signed_bce(r['end_bce'])
        # 卒年 = 在位末年（来自十表明文）→ high
        death_min = death_max = end
        death_conf = promote(death_conf, 'high')
        # 生年：即位年 ±10~60 岁（推算，低置信）
        birth_min = start - 59
        birth_max = start - 9
        birth_conf = promote(birth_conf, 'low')
        evidence.append(f'十表 reign_periods: {r.get("state","?")} 在位 {r["start_bce"]}–{r["end_bce"]} BCE')

    # Source 1b: 事件索引卒年（来自原文事件锚点）
    if death_min is None and event_death_year is not None:
        sources.add('event_index')
        death_min = death_max = event_death_year
        death_conf = promote(death_conf, 'high')
        evidence.append(f'事件索引（原文）: 卒于 {fmt_year(event_death_year)}')

    # Source 2: 文本模式（方法 2/3）
    for p in patterns:
        sources.add('text_pattern')
        if p['pattern'] == 'AGE_AT_ACC' and name in rulers:
            age = p['value']
            acc = signed_bce(rulers[name]['start_bce'])
            inferred_birth = acc - (age - 1)
            birth_min = birth_max = inferred_birth
            birth_conf = promote(birth_conf, 'high')
            evidence.append(
                f'原文模式 生{p["raw"]}岁立 @{p["chapter"]}：'
                f'生年={fmt_year(inferred_birth)}（即位年 −{age-1}）'
            )
        elif p['pattern'] == 'AGE_AT_DEATH':
            age = p['value']
            if death_max is not None:
                inferred_birth = death_max - (age - 1)
                birth_min = birth_max = inferred_birth
                birth_conf = promote(birth_conf, 'high')
                evidence.append(
                    f'原文模式 享年{p["raw"]}岁 @{p["chapter"]}：'
                    f'生年={fmt_year(inferred_birth)}（卒年 −{age-1}）'
                )
            else:
                evidence.append(
                    f'原文模式 享年{p["raw"]}岁 @{p["chapter"]}（卒年未知，无法反推生年）'
                )
        elif p['pattern'] == 'REIGN_LEN':
            n = p['value']
            if name in rulers:
                actual = rulers[name]['start_bce'] - rulers[name]['end_bce'] + 1
                note = '✓一致' if actual == n else f'⚠不一致（十表为 {actual} 年）'
                evidence.append(f'原文模式 立{p["raw"]}年卒 @{p["chapter"]}：{note}')
            else:
                evidence.append(f'原文模式 立{p["raw"]}年卒 @{p["chapter"]}：在位 {n} 年')

    # Source 3: person_lifespans v1（外部）
    if name in v1_persons:
        sources.add('lifespans_v1')
        v = v1_persons[name]
        v1_note = v.get('note', '')
        v1_birth = v.get('birth')
        v1_death = v.get('death')

        if v1_note == '传说':
            legacy_conf = 'legend'
        elif v1_note.startswith('约') and not any(kw in v1_note for kw in ('在位', '君主')):
            legacy_conf = 'approximate'
        else:
            legacy_conf = 'external'

        evidence.append(
            f'v1 lifespans: {fmt_year(v1_birth)}–{fmt_year(v1_death)}'
            + (f'（{v1_note}）' if v1_note else '')
        )

        if legacy_conf == 'legend':
            if birth_min is None:
                birth_min = v1_birth - 30
                birth_max = v1_birth + 30
            if death_min is None:
                death_min = v1_death - 30
                death_max = v1_death + 30
            birth_conf = 'legend'
            death_conf = 'legend'
        elif legacy_conf == 'approximate':
            if birth_min is None:
                birth_min = v1_birth - 10
                birth_max = v1_birth + 10
                birth_conf = promote(birth_conf, 'approximate')
            if death_min is None:
                death_min = v1_death - 10
                death_max = v1_death + 10
                death_conf = promote(death_conf, 'approximate')
        else:
            if birth_min is None:
                birth_min = v1_birth - 3
                birth_max = v1_birth + 3
                birth_conf = promote(birth_conf, 'medium')
            if death_min is None:
                death_min = v1_death - 3
                death_max = v1_death + 3
                death_conf = promote(death_conf, 'medium')

    if birth_min is None and death_min is None:
        return None

    entry: dict = {
        'sources': sorted(sources),
        'birth_confidence': birth_conf,
        'death_confidence': death_conf,
        # 总体置信度 = min(生,卒)，作展示摘要；legend 保留
        'confidence': ('legend' if 'legend' in (birth_conf, death_conf)
                       else min((birth_conf, death_conf), key=lambda c: CONF_RANK.get(c, 0))),
        'evidence': evidence,
    }
    if state:
        entry['state'] = state
    if birth_min is not None:
        entry['birth_min'] = birth_min
        entry['birth_max'] = birth_max
    if death_min is not None:
        entry['death_min'] = death_min
        entry['death_max'] = death_max

    if birth_min is not None and death_min is not None:
        age_min = death_min - birth_max + 1
        age_max = death_max - birth_min + 1
        if 0 < age_min <= 120 and 0 < age_max <= 150:
            entry['age_min'] = age_min
            entry['age_max'] = age_max

    return entry


def main():
    result = infer_all()
    OUTPUT_FILE.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    stats = result['_stats']
    print(f'Wrote {OUTPUT_FILE}')
    print(f'  persons: {stats["total_persons"]}')
    print(f'  overall:    {stats["confidence_distribution"]}')
    print(f'  birth_conf: {stats["birth_confidence_distribution"]}')
    print(f'  death_conf: {stats["death_confidence_distribution"]}')
    print(f'  sources:    {stats["source_distribution"]}')
    print(f'  patterns:   {stats["pattern_evidence"]}')


if __name__ == '__main__':
    main()
