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
ENTITY_ALIASES = BASE_DIR / 'kg' / 'entities' / 'data' / 'entity_aliases.json'
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


def build_alias_map(reign_aliases: dict, v1_persons: dict, rulers: dict,
                    entity_aliases: dict,
                    extra_names: set[str] | None = None) -> dict:
    """构建 任意名字 → 规范名 映射（union-find 聚类）。

    规则：
    1. reign_aliases 的 surface→canonical 全部建边（高祖~高皇帝）
    2. entity_aliases 单一 canonical 的 surface→canonical 建边（刘邦~汉高祖）
    3. 多 canonical 的 surface：只有当所有 canonical 已同簇时才建边（高祖~{刘邦,汉高祖}
       已通过 2 同簇 → OK；刘武~{梁孝王,城阳惠王} 不同簇 → 拒绝合并）
    4. 同簇中选主名：优先 rulers 键 > 较长名 > 字典序
    """
    parent: dict[str, str] = {}

    def add(n: str) -> None:
        parent.setdefault(n, n)

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # 先把所有候选名字注册进去
    candidates = set(v1_persons.keys()) | set(reign_aliases.keys()) | set(entity_aliases.keys()) | set(rulers.keys())
    if extra_names:
        candidates |= extra_names
    for n in candidates:
        add(n)

    # 边 1: reign_aliases
    for s, c in reign_aliases.items():
        add(s); add(c)
        union(s, c)

    # 边 2: entity_aliases 单 canonical
    # 1 字 surface 只有在它本身不是别人的 canonical 时才建边（否则如"子→孔子"会把
    # 许多无关名字因"子"这个单字传染到一起）
    # 若 surface 本身就是 rulers 里的独立条目（如"齐王"），视为独立身份，不合并
    # 到 entity_aliases 里它被标记的 canonical（如"齐王→韩信" 属 entity_aliases 误用）
    ea_canonicals_all: set[str] = set()
    for cans in entity_aliases.values():
        ea_canonicals_all.update(cans)
    for s, cans in entity_aliases.items():
        if len(cans) != 1:
            continue
        if len(s) < 2 and s in ea_canonicals_all:
            continue
        if s in rulers:
            continue  # surface 已在十表里有独立身份，不走 aliases 的合并
        c = cans[0]
        add(s); add(c)
        union(s, c)

    # 边 2.5: v1 note 为短别名指向（如 缪公 note="秦穆公"、梁孝王 note="刘武"）
    # 仅当 note 看起来像人名（≤5 字，非描述句）时建边
    for name, v in v1_persons.items():
        note = (v.get('note') or '').strip()
        if not note or len(note) > 5:
            continue
        # 排除明显的非指向注（如"约"、"传说"、"约，周初人"）
        if note in ('约', '传说') or note.startswith('约，'):
            continue
        add(name); add(note)
        union(name, note)

    # 边 2.6: 国名前缀补全（缪公 → 秦穆公 等）
    # 跳过 1 字名字（子/万 等过于歧义，不要自动前缀）
    for n in list(parent.keys()):
        if n in rulers or len(n) < 2:
            continue
        for sp in STATE_PREFIXES:
            cand = sp + n
            if cand in rulers:
                add(cand)
                union(n, cand)
                break
        if '缪' in n:
            alt = n.replace('缪', '穆')
            if alt in rulers:
                add(alt); union(n, alt)

    # 边 3: 多 canonical — 仅当所有 canonical 已同簇才合并（跳过 1 字 surface）
    for s, cans in entity_aliases.items():
        if len(s) < 2 or len(cans) < 2:
            continue
        for c in cans:
            add(c)
        roots = {find(c) for c in cans}
        if len(roots) == 1:
            add(s)
            union(s, cans[0])

    # 聚类并选主名
    clusters: dict[str, list[str]] = defaultdict(list)
    for n in parent:
        clusters[find(n)].append(n)

    # entity_aliases 里的 canonical 集合（做为主名偏好）
    ea_canonicals: set[str] = set()
    for cans in entity_aliases.values():
        ea_canonicals.update(cans)

    def pick_canonical(members: list[str]) -> str:
        def score(n: str) -> tuple:
            in_rulers = 1 if n in rulers else 0
            in_v1 = 1 if n in v1_persons else 0
            is_ea_canon = 1 if n in ea_canonicals else 0
            is_ea_surface_only = 1 if (n in entity_aliases and n not in ea_canonicals) else 0
            # 优先级：in_rulers > in_v1 > is_ea_canon > 非 surface only > 长度 > 字典序
            return (in_rulers, in_v1, is_ea_canon, -is_ea_surface_only, len(n), n)
        return max(members, key=score)

    alias_map: dict[str, str] = {}
    for members in clusters.values():
        if len(members) <= 1:
            continue
        canon = pick_canonical(members)
        for m in members:
            if m != canon:
                alias_map[m] = canon
    return alias_map


# ============================================================
# 常识性生卒年约束（单位：岁）
# ============================================================
MAX_LIFESPAN = 85           # 先秦至汉代典型最长寿命（保守上限；张苍 100+ 为异常）
MIN_ADULT_AGE = 15          # 参与大事（征伐/从政/使节/著书）的最低年龄
MAX_RULER_ACCESSION_AGE = 70  # 君主即位年龄上限
MIN_RULER_ACCESSION_AGE = 0   # 婴幼即位下限（如汉昭帝 8 岁即位）
POST_DEATH_BUFFER = 15        # 人物最后出现 → 卒年的最大间隔


def load_person_event_timeline(entity_aliases: dict | None = None,
                                 alias_refs: dict | None = None
                                 ) -> dict[str, list[tuple[int, str, str]]]:
    """扫描所有事件索引，按人物聚合事件时间线。

    返回 {person_surface_or_canonical: [(ce_year, event_id, chapter_id), ...]}。
    只收录时间字段可解析为具体公元年的事件；approx（`[约公元前...年]`）同样保留。
    单字 surface 在提取时尝试 disambiguate_single_char 规范化。
    """
    entity_aliases = entity_aliases or {}
    alias_refs = alias_refs or {}
    pat_year = re.compile(r'[（\[](?:约)?公元前?(\d+)年')
    pat_year_ce = re.compile(r'[（\[]公元(\d+)年')
    pat_person = re.compile(r'〖[@;]([^〗|]+?)(?:\|([^〗]+))?〗')

    timeline: dict[str, list[tuple[int, str, str]]] = defaultdict(list)

    for fpath in sorted(EVENTS_DIR.glob('*_事件索引.md')):
        if fpath.name == '战争事件索引.md':
            continue
        chapter_id = fpath.name[:3]
        text = fpath.read_text(encoding='utf-8')
        for line in text.splitlines():
            if not line.startswith('|') or line.startswith('|---'):
                continue
            cols = [c.strip() for c in line.split('|')]
            if len(cols) < 7:
                continue
            event_id = cols[1]
            if not re.match(r'\d{3}-\d+', event_id):
                continue
            time_field = cols[4]
            persons_field = cols[6]
            event_name = cols[2]

            m = pat_year.search(time_field)
            if m:
                ce_year = -int(m.group(1))
            else:
                mc = pat_year_ce.search(time_field)
                if mc:
                    ce_year = int(mc.group(1))
                else:
                    continue

            seen: set[str] = set()
            for src in (persons_field, event_name):
                for pm in pat_person.finditer(src):
                    raw = (pm.group(2) or pm.group(1)).strip()
                    if not raw:
                        continue
                    if len(raw) == 1:
                        resolved = disambiguate_single_char(
                            raw, chapter_id, entity_aliases, alias_refs)
                        if resolved:
                            raw = resolved
                    if raw in seen:
                        continue
                    seen.add(raw)
                    timeline[raw].append((ce_year, event_id, chapter_id))

    return dict(timeline)


def load_event_details() -> dict[str, dict]:
    """解析各章事件索引的"详细事件记录"段，抽取每条 event 的原文引用/段落定位/事件名。

    返回 {event_id: {name, quote, paragraph, chapter_id}}。
    """
    result: dict[str, dict] = {}
    pat_header = re.compile(r'###\s+(\d{3}-\d+)\s+([^\n]+)')
    pat_quote = re.compile(r'\*\*原文引用\*\*:\s*"(.+?)"', re.DOTALL)
    pat_para = re.compile(r'\*\*段落位置\*\*:\s*\[?([^\]\n]+)\]?')
    pat_event_name = re.compile(r'\*\*事件[描述描述]*\*\*:\s*(.+?)$', re.MULTILINE)

    for fpath in sorted(EVENTS_DIR.glob('*_事件索引.md')):
        if fpath.name == '战争事件索引.md':
            continue
        chapter_id = fpath.name[:3]
        text = fpath.read_text(encoding='utf-8')
        # 按 ### event_id 分块
        blocks = re.split(r'(?=^###\s+\d{3}-\d+)', text, flags=re.MULTILINE)
        for blk in blocks:
            mh = pat_header.search(blk)
            if not mh:
                continue
            eid = mh.group(1)
            ename = mh.group(2).strip()
            mq = pat_quote.search(blk)
            mp = pat_para.search(blk)
            result[eid] = {
                'name': ename,
                'quote': mq.group(1).strip() if mq else '',
                'paragraph': mp.group(1).strip().rstrip(']') if mp else '',
                'chapter_id': chapter_id,
            }
    return result


def strip_tags_for_display(text: str) -> str:
    """把 〖TYPE X|canonical〗 的 X 显示名保留，清掉 TYPE/canonical/括号。用于证据展示。"""
    text = re.sub(r'〖[@=;#%&◆^~•!+?${:_\[]([^〗|]+)\|[^〗]*〗', r'\1', text)
    text = re.sub(r'〖[@=;#%&◆^~•!+?${:_\[]([^〗]+)〗', r'\1', text)
    return text


def load_event_birth_death(entity_aliases: dict | None = None,
                            alias_refs: dict | None = None,
                            event_details: dict | None = None
                            ) -> tuple[dict[str, tuple[int, str, str]], dict[str, tuple[int, str, str]]]:
    """从 kg/events/data/*_事件索引.md 提取生卒事件。

    返回 (births, deaths)，每个 dict 格式为 {person: (ce_year, event_id, approx_marker)}。
    approx_marker 为 '约' 或 '' （精确/推算）。

    事件索引行列序：| 事件ID | 事件名称 | 事件类型 | 时间 | 地点 | 主要人物 | 朝代 |

    人名提取：
    - 从"主要人物"列解析所有 〖@〗（person）和 〖;〗（shihao/title）标签
    - 多人事件（如 011-038 梁孝王城阳共王汝南王薨）为每个标签人名各记一条
    """
    pat_year = re.compile(r'[（\[](约)?公元前(\d+)年')
    pat_person = re.compile(r'〖[@;]([^〗|]+?)(?:\|([^〗]+))?〗')
    # 死亡关键词集合（包含自然死、刑杀、战死、自尽等）
    # - 卒/薨/崩/殁：须排除作为"士兵"义的 X卒（降卒/士卒等）
    # - 斩/腰斩/诛/伏诛/弑/自杀/自刎/刎/自尽/戮/自戕/自焚
    # - 死/赐死：常见死亡委婉语，排除 死罪/死士/死守/生死/死节/死敌 等组合
    pat_death = re.compile(
        r'(?<![士降兵马骑车戍卒楚汉秦赵齐燕韩魏宋周鲁吴越陈蔡])(?:卒|薨|崩|殁|驾崩)(?!徒)'
        r'|(?:腰斩|伏诛|自刎|自杀|自尽|自戕|自焚|赐死|身死|遇害)'
        r'|(?:诛|弑|戮|刎)(?![绝诸])'
        r'|(?<![生必以求贪])死(?![罪士守节敌灰后生])'
    )
    pat_birth = re.compile(r'(?:出生|生于|诞生|而生)')
    births: dict[str, tuple[int, str, str]] = {}
    deaths: dict[str, tuple[int, str, str]] = {}

    entity_aliases = entity_aliases or {}
    alias_refs = alias_refs or {}

    for fpath in sorted(EVENTS_DIR.glob('*_事件索引.md')):
        if fpath.name == '战争事件索引.md':
            continue
        text = fpath.read_text(encoding='utf-8')
        chapter_id = fpath.name[:3]
        for line in text.splitlines():
            if not line.startswith('|') or line.startswith('|---'):
                continue
            cols = [c.strip() for c in line.split('|')]
            if len(cols) < 7:
                continue
            event_id = cols[1]
            if not re.match(r'\d{3}-\d+', event_id):
                continue
            event_name = cols[2]
            time_field = cols[4]
            persons_field = cols[6]

            has_death = bool(pat_death.search(event_name))
            has_birth = bool(pat_birth.search(event_name))
            if not (has_death or has_birth):
                continue

            ym = pat_year.search(time_field)
            if not ym:
                continue
            approx = '约' if ym.group(1) else ''
            ce_year = -int(ym.group(2))

            # 从 persons_field 抽所有 tagged 人名
            tagged: list[str] = []
            for pm in pat_person.finditer(persons_field):
                nm = (pm.group(2) or pm.group(1)).strip()
                if nm:
                    tagged.append(nm)
            # 事件名称里额外的 @ 标签（如 004-013 的 〖@发〗）
            for pm in pat_person.finditer(event_name):
                nm = (pm.group(2) or pm.group(1)).strip()
                if nm and nm not in tagged:
                    tagged.append(nm)

            def canon_name(raw: str) -> str:
                if len(raw) == 1:
                    resolved = disambiguate_single_char(
                        raw, chapter_id, entity_aliases, alias_refs)
                    if resolved:
                        return resolved
                return raw

            # 不及物死亡动词：subject 在动词前（X崩、X自刎、X腰斩）— X 是死者
            pat_death_subj_intrans = re.compile(
                r'([\u4e00-\u9fa5]+?)'
                r'(?:驾崩|腰斩|伏诛|自刎|自杀|自尽|自戕|自焚|赐死|身死|遇害'
                r'|崩|薨|殁'
                r'|卒(?!徒)'
                r'|(?<![生必以求贪])死(?![罪士守节敌灰后生]))'
                r'(?!徒)'
            )
            # 及物死亡动词：object 在动词后（X诛Y、X杀Y）— Y 是死者，不是 X
            pat_death_obj_trans = re.compile(
                r'(?:诛|弑|戮|斩|杀|刎)([\u4e00-\u9fa5]+?)(?:[，。、；：]|$)'
            )
            pat_birth_subj = re.compile(r'([\u4e00-\u9fa5]+?)(?:出生|生于|诞生|而生)')

            def match_tagged(subject: str) -> list[str]:
                """从 subject 串中挑出 persons_field 里出现的人名。"""
                return [t for t in tagged if t in subject]

            # 去掉 event_name 中的 〖...〗 标签以便字符匹配
            clean_event_name = re.sub(r'〖[^〗]+〗', lambda m: m.group(0).split('|')[0].lstrip('〖').lstrip('@=;%&^◆~•!#+?{:[_$'), event_name)
            clean_event_name = clean_event_name.replace('〗', '')

            if has_death:
                matched_deaths: list[str] = []
                # 不及物：取紧邻死亡动词前 **最近** 的一个 tagged 人名作为 victim
                # （避免"项王伐齐田荣败死"因主语头是项王就误把项王判为死者）
                intrans_verbs = re.compile(
                    r'驾崩|腰斩|伏诛|自刎|自杀|自尽|自戕|自焚|赐死|身死|遇害'
                    r'|崩|薨|殁|卒(?!徒)|(?<![生必以求贪])死(?![罪士守节敌灰后生])'
                )
                for vm in intrans_verbs.finditer(clean_event_name):
                    v_start = vm.start()
                    prefix = clean_event_name[:v_start]
                    # 在 prefix 中找 **最后出现** 的 tagged 名字
                    nearest = None
                    nearest_pos = -1
                    for t in tagged:
                        p = prefix.rfind(t)
                        if p > nearest_pos:
                            nearest = t
                            nearest_pos = p
                    if nearest and nearest not in matched_deaths:
                        matched_deaths.append(nearest)
                # 及物：动词后的最 **近** object = victim
                trans_verbs = re.compile(r'诛|弑|戮|斩|杀|刎')
                for vm in trans_verbs.finditer(clean_event_name):
                    v_end = vm.end()
                    suffix = clean_event_name[v_end:]
                    # 在 suffix 开头找 tagged 名字
                    best = None
                    best_pos = 10**9
                    for t in tagged:
                        p = suffix.find(t)
                        if p >= 0 and p < best_pos:
                            best = t
                            best_pos = p
                    if best and best not in matched_deaths:
                        matched_deaths.append(best)
                # 保守 fallback：以下两种情况可用 tagged[0] 作为死者
                # (a) persons_field 只有 1 人 + event_name 以不及物死亡动词结尾
                # (b) event_name 含"自刎/自杀/自尽/自戕/自焚/腰斩/伏诛/赐死/身死/遇害/驾崩"
                #     等强自死标记（无论 persons 几个，首位通常是主角）
                pat_ends_with_intrans_death = re.compile(
                    r'(?:驾崩|腰斩|伏诛|自刎|自杀|自尽|自戕|自焚|赐死|身死|遇害'
                    r'|崩|薨|殁|卒|(?<![生必以求贪])死)$'
                )
                strong_self_death = re.compile(
                    r'(?:自刎|自杀|自尽|自戕|自焚|腰斩|伏诛|赐死|身死|遇害|驾崩)'
                )
                if not matched_deaths:
                    if len(tagged) == 1 and pat_ends_with_intrans_death.search(clean_event_name):
                        matched_deaths = [tagged[0]]
                    elif tagged and strong_self_death.search(clean_event_name):
                        matched_deaths = [tagged[0]]
                for raw in matched_deaths:
                    deaths.setdefault(canon_name(raw), (ce_year, event_id, approx))

            if has_birth:
                matched_births: list[str] = []
                for sm in pat_birth_subj.finditer(clean_event_name):
                    subj = sm.group(1)
                    for t in match_tagged(subj):
                        if t not in matched_births:
                            matched_births.append(t)
                if not matched_births and tagged:
                    matched_births = [tagged[0]]
                for raw in matched_births:
                    births.setdefault(canon_name(raw), (ce_year, event_id, approx))
    return births, deaths


def load_event_deaths() -> dict[str, int]:
    """向后兼容：仅返回 {person: ce_year} 形式的卒年字典。"""
    _, deaths = load_event_birth_death()
    return {n: v[0] for n, v in deaths.items()}


def load_entity_aliases() -> dict[str, list[str]]:
    """从 kg/entities/data/entity_aliases.json 构建 surface -> canonicals（多重 canonical）。
    返回 {surface: [canonical, ...]} — 若一个 surface 指向多个 canonical（同名不同人），
    则保留所有，调用方需自行处理歧义。
    """
    if not ENTITY_ALIASES.exists():
        return {}
    d = json.loads(ENTITY_ALIASES.read_text(encoding='utf-8'))
    persons = d.get('person', [])
    sf_map: dict[str, set] = defaultdict(set)
    for e in persons:
        sf = e.get('surface')
        can = e.get('canonical')
        if sf and can:
            sf_map[sf].add(can)
    return {sf: sorted(cans) for sf, cans in sf_map.items()}


def load_alias_refs() -> dict[tuple[str, str], set[str]]:
    """构建 (surface, canonical) -> {chapter_id...}，用于单字名的章节消歧。

    refs 格式 [[chapter_stem, paragraph], ...] — chapter_stem 如 "112_平津侯主父列传"，
    提取前 3 位作为 chapter_id。
    """
    if not ENTITY_ALIASES.exists():
        return {}
    d = json.loads(ENTITY_ALIASES.read_text(encoding='utf-8'))
    result: dict[tuple[str, str], set[str]] = defaultdict(set)
    for e in d.get('person', []):
        sf = e.get('surface')
        can = e.get('canonical')
        if not sf or not can:
            continue
        for ref in e.get('refs', []):
            if isinstance(ref, list) and len(ref) >= 1:
                stem = ref[0]
                m = re.match(r'(\d{3})', stem)
                if m:
                    result[(sf, can)].add(m.group(1))
    return dict(result)


def disambiguate_single_char(surface: str, chapter_id: str,
                               entity_aliases: dict, alias_refs: dict) -> str | None:
    """对单字 surface 在指定章节里选一个 canonical（若有唯一章节命中则返回，否则 None）。"""
    cans = entity_aliases.get(surface, [])
    if not cans:
        return None
    if len(cans) == 1:
        return cans[0]
    # 多 canonical：看哪个 canonical 的 refs 包含 chapter_id
    hits = [c for c in cans if chapter_id in alias_refs.get((surface, c), set())]
    if len(hits) == 1:
        return hits[0]
    return None  # 0 或 >1 → 无法确定


def infer_all():
    reign_data = json.loads(REIGN_FILE.read_text(encoding='utf-8'))
    rulers = reign_data['rulers']
    aliases = reign_data.get('aliases', {})
    v1 = json.loads(LIFESPAN_V1.read_text(encoding='utf-8'))
    v1_persons = v1['persons']
    entity_aliases = load_entity_aliases()
    alias_refs = load_alias_refs()
    event_details = load_event_details()
    event_births, event_deaths_full = load_event_birth_death(entity_aliases, alias_refs)
    event_deaths = {n: v[0] for n, v in event_deaths_full.items()}
    event_timeline = load_person_event_timeline(entity_aliases, alias_refs)

    # 模式扫描结果（提前以收集名字）
    evidence_by_pattern = scan_patterns()
    pattern_names = {h['ruler'] for hits in evidence_by_pattern.values() for h in hits}
    extra_names = pattern_names | set(event_deaths.keys()) | set(event_births.keys())
    alias_to_canonical = build_alias_map(aliases, v1_persons, rulers, entity_aliases,
                                          extra_names=extra_names)

    def canon(name: str) -> str:
        return alias_to_canonical.get(name, name)

    # 按人物聚合（已规范化）
    pattern_by_person: dict[str, list[dict]] = defaultdict(list)
    for pat_name, hits in evidence_by_pattern.items():
        for h in hits:
            pattern_by_person[canon(h['ruler'])].append({**h, 'pattern': pat_name})

    # 事件死亡/出生也规范化
    event_deaths_canon: dict[str, tuple[int, str, str]] = {}
    for name, tup in event_deaths_full.items():
        event_deaths_canon.setdefault(canon(name), tup)
    event_births_canon: dict[str, tuple[int, str, str]] = {}
    for name, tup in event_births.items():
        event_births_canon.setdefault(canon(name), tup)

    # 时间线规范化（所有事件按 canonical 聚合）
    timeline_canon: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for name, evs in event_timeline.items():
        c = canon(name)
        timeline_canon[c].extend(evs)

    # v1 人物 也合并别名（保留首个出现，其余忽略避免歧义）
    v1_canon: dict[str, dict] = {}
    for name, v in v1_persons.items():
        c = canon(name)
        if c not in v1_canon:
            v1_canon[c] = v
        # 冲突时若当前值没 note 但新值有，则替换
        elif not (v1_canon[c].get('note') or '') and (v.get('note') or ''):
            v1_canon[c] = v

    # 候选人物：reign_periods + v1（canon） + 模式 + 事件卒/生年 + 时间线
    all_persons = (set(rulers.keys()) | set(v1_canon.keys())
                   | set(pattern_by_person.keys())
                   | set(event_deaths_canon.keys()) | set(event_births_canon.keys())
                   | set(timeline_canon.keys()))

    result_persons: dict[str, dict] = {}
    for name in sorted(all_persons):
        entry = infer_one(name, rulers, v1_canon,
                          pattern_by_person.get(name, []),
                          event_deaths_canon.get(name),
                          event_births_canon.get(name),
                          timeline_canon.get(name),
                          event_details)
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
              patterns: list[dict],
              event_death: tuple[int, str, str] | None = None,
              event_birth: tuple[int, str, str] | None = None,
              timeline: list[tuple[int, str, str]] | None = None,
              event_details: dict | None = None) -> dict | None:
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
    accession_year = None
    if name in rulers:
        r = rulers[name]
        state = r.get('state')
        sources.add('reign_periods')
        start = signed_bce(r['start_bce'])
        end = signed_bce(r['end_bce'])
        accession_year = start
        # 卒年 = 在位末年（来自十表明文）→ high
        death_min = death_max = end
        death_conf = promote(death_conf, 'high')
        evidence.append(f'十表 reign_periods: {r.get("state","?")} 在位 {r["start_bce"]}–{r["end_bce"]} BCE')

    # Source 1b: 事件索引卒年（来自原文事件锚点）
    if event_death is not None:
        ed_year, ed_id, ed_approx = event_death
        sources.add('event_index')
        if death_min is None:
            death_min = death_max = ed_year
        if ed_approx == '约':
            if death_conf in ('low',):
                death_conf = promote(death_conf, 'approximate')
        else:
            death_conf = promote(death_conf, 'high')
        approx_prefix = '约 ' if ed_approx else ''
        detail = (event_details or {}).get(ed_id, {})
        ename = detail.get('name', '')
        quote = detail.get('quote', '')
        para = detail.get('paragraph', '')
        ch_id = detail.get('chapter_id', ed_id[:3])
        parts = [f'事件索引 {ed_id}（{ename}）: {approx_prefix}卒于 {fmt_year(ed_year)}']
        if para:
            parts.append(f'[{ch_id}:{para}]')
        evidence.append(' '.join(parts))
        if quote:
            display = strip_tags_for_display(quote)
            evidence.append(f'  · 原文："{display}"')

    # Source 1c: 事件索引生年
    if event_birth is not None:
        eb_year, eb_id, eb_approx = event_birth
        sources.add('event_index')
        birth_min = birth_max = eb_year
        if eb_approx == '约':
            birth_conf = promote(birth_conf, 'approximate')
        else:
            birth_conf = promote(birth_conf, 'high')
        approx_prefix = '约 ' if eb_approx else ''
        detail = (event_details or {}).get(eb_id, {})
        ename = detail.get('name', '')
        quote = detail.get('quote', '')
        para = detail.get('paragraph', '')
        ch_id = detail.get('chapter_id', eb_id[:3])
        parts = [f'事件索引 {eb_id}（{ename}）: {approx_prefix}生于 {fmt_year(eb_year)}']
        if para:
            parts.append(f'[{ch_id}:{para}]')
        evidence.append(' '.join(parts))
        if quote:
            display = strip_tags_for_display(quote)
            evidence.append(f'  · 原文："{display}"')

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

    # Source 4: 事件时间线 + 常识约束（只在生年仍无点值时应用）
    has_direct_birth = (birth_min is not None and birth_min == birth_max and birth_conf == 'high')
    has_direct_death = (death_min is not None and death_min == death_max and death_conf == 'high')
    timeline_years = sorted({y for y, _, _ in (timeline or [])})
    if timeline_years:
        first_yr = timeline_years[0]
        last_yr = timeline_years[-1]
        evidence.append(
            f'事件时间线: 共 {len(timeline_years)} 年跨度'
            f'（{fmt_year(first_yr)} → {fmt_year(last_yr)}）'
        )
        sources.add('event_timeline')

        # 约束组：(lower, upper, label)
        birth_constraints = []
        death_constraints = []

        # 约束 A：首次出现 → 生年 ≤ first_yr（必须已出生）
        # 君主另有即位约束（通常更紧）；非君主加 MIN_ADULT_AGE 启发（首次出现多半成年）
        if accession_year is not None:
            birth_constraints.append((None, first_yr,
                                       f'首次出现 {fmt_year(first_yr)}（已出生）'))
        else:
            birth_constraints.append((None, first_yr - MIN_ADULT_AGE,
                                       f'首次出现 {fmt_year(first_yr)} 时 ≥{MIN_ADULT_AGE} 岁（非君主默认）'))

        # 约束 B：最后出现时仍在世 ≤ MAX_LIFESPAN 岁 → 生年 ≥ last_yr - MAX_LIFESPAN
        birth_constraints.append((last_yr - MAX_LIFESPAN, None,
                                   f'最后出现 {fmt_year(last_yr)} 时 ≤{MAX_LIFESPAN} 岁'))
        # 约束 C：卒年 ≥ last_yr（最后出现时仍在世）
        death_constraints.append((last_yr, None,
                                   f'最后出现于 {fmt_year(last_yr)}'))
        # 约束 D：卒年 ≤ last_yr + POST_DEATH_BUFFER（罕有身后仍被纪录事件）
        death_constraints.append((None, last_yr + POST_DEATH_BUFFER,
                                   f'最后出现后 ≤{POST_DEATH_BUFFER} 年内卒'))

        # 即位年约束（若为君主）— 即位时年龄 0–70 岁（涵盖幼主）
        if accession_year is not None:
            birth_constraints.append((
                accession_year - MAX_RULER_ACCESSION_AGE,
                accession_year - MIN_RULER_ACCESSION_AGE,
                f'即位 {fmt_year(accession_year)} 时年龄 '
                f'{MIN_RULER_ACCESSION_AGE}–{MAX_RULER_ACCESSION_AGE} 岁'
            ))

        # 仅当无直接点值时，用约束更新区间（取交集）
        if not has_direct_birth:
            lo_candidates = [c[0] for c in birth_constraints if c[0] is not None]
            hi_candidates = [c[1] for c in birth_constraints if c[1] is not None]
            new_lo = max(lo_candidates) if lo_candidates else None
            new_hi = min(hi_candidates) if hi_candidates else None
            if new_lo is not None and new_hi is not None and new_lo <= new_hi:
                # 与现有区间取交（若已有）
                if birth_min is not None and birth_max is not None:
                    new_lo = max(new_lo, birth_min)
                    new_hi = min(new_hi, birth_max)
                    if new_lo > new_hi:
                        new_lo, new_hi = birth_min, birth_max  # 冲突时保留原
                birth_min = new_lo
                birth_max = new_hi
                # 区间越窄置信度越高；点值 → medium，≤5 年 → medium，其他 → low
                width = new_hi - new_lo
                if width == 0:
                    birth_conf = promote(birth_conf, 'medium')
                elif width <= 5:
                    birth_conf = promote(birth_conf, 'medium')
                else:
                    birth_conf = promote(birth_conf, 'low')
                for lo, hi, label in birth_constraints:
                    evidence.append(f'  · 约束: {label}')

        if not has_direct_death:
            lo_candidates = [c[0] for c in death_constraints if c[0] is not None]
            hi_candidates = [c[1] for c in death_constraints if c[1] is not None]
            new_lo = max(lo_candidates) if lo_candidates else None
            new_hi = min(hi_candidates) if hi_candidates else None
            if new_lo is not None and new_hi is not None and new_lo <= new_hi:
                if death_min is not None and death_max is not None:
                    new_lo = max(new_lo, death_min)
                    new_hi = min(new_hi, death_max)
                    if new_lo > new_hi:
                        new_lo, new_hi = death_min, death_max
                death_min = new_lo
                death_max = new_hi
                width = new_hi - new_lo
                if width <= 5:
                    death_conf = promote(death_conf, 'medium')
                else:
                    death_conf = promote(death_conf, 'low')

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
