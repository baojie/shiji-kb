#!/usr/bin/env python3
"""
build_year_map.py - 年份消歧与公元纪年映射

Phase 1: 从年表章节（014/015/022）解析君主在位年 → reign_periods.json
Phase 2: 扫描正文tagged.md，消歧年份实体 → year_ce_map.json

用法:
    python build_year_map.py                   # 完整流程
    python build_year_map.py --extract-reigns  # 仅提取reign_periods.json
"""
import os
import re
import json
import sys
import glob
from collections import defaultdict, OrderedDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTER_DIR = os.path.join(BASE_DIR, 'chapter_md')
REIGN_FILE = os.path.join(BASE_DIR, 'reign_periods.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'year_ce_map.json')
DISAMBIG_FILE = os.path.join(BASE_DIR, 'disambiguation_map.json')

# ============================================================
# Chinese numeral utilities
# ============================================================

CN_DIGITS = {
    '零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
}

def cn_to_int(s):
    """Convert Chinese numeral string to integer.
    元→1, 三→3, 十→10, 十三→13, 二十→20, 二十三→23, 四十八→48
    """
    if not s:
        return None
    s = s.strip()
    if s == '元':
        return 1

    result = 0
    current = 0

    for c in s:
        if c in CN_DIGITS:
            current = CN_DIGITS[c]
        elif c == '十':
            if current == 0:
                current = 1
            result += current * 10
            current = 0
        elif c == '百':
            if current == 0:
                current = 1
            result += current * 100
            current = 0
        elif c in ('有', '又'):
            # 十有三 = 13
            pass
        else:
            return None

    result += current
    return result if result > 0 else None


CN_DIGIT_STRS = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九']

def int_to_cn(n):
    """Convert integer to Chinese numeral string.
    1→'元', 2→'二', 10→'十', 13→'十三', 20→'二十', 23→'二十三'
    """
    if n == 1:
        return '元'
    if n <= 0 or n > 99:
        return str(n)
    if n < 10:
        return CN_DIGIT_STRS[n]
    tens = n // 10
    ones = n % 10
    result = ''
    if tens > 1:
        result += CN_DIGIT_STRS[tens]
    result += '十'
    if ones > 0:
        result += CN_DIGIT_STRS[ones]
    return result


# Chinese numeral pattern (matches 元 or 1-99 in Chinese)
CN_NUM_PAT = r'(?:元|[二三四五六七八九]十[一二三四五六七八九]?|十[一二三四五六七八九]?|[一二三四五六七八九])'

# ============================================================
# Table parsing utilities
# ============================================================

def parse_table_row(line):
    """Parse a markdown table row into cells."""
    if '|' not in line:
        return None
    parts = line.strip().split('|')
    # Remove first/last empty from split
    cells = [p.strip() for p in parts[1:-1]]
    return cells


def extract_bce_year(cell_text):
    """Extract BCE year number from the first column."""
    text = cell_text.strip().replace('公元前', '')
    try:
        return int(text)
    except ValueError:
        return None


def strip_entity_tags(text):
    """Remove entity tags like @name@, &state&, $title$ from text."""
    text = re.sub(r'[@&$^~!?]', '', text)
    text = text.replace('🌿', '')
    return text


# ============================================================
# Table 014: 十二诸侯年表 (841-478 BCE)
# ============================================================

TABLE_014_STATES = ['周', '鲁', '齐', '晋', '秦', '楚', '宋', '卫', '陈', '蔡', '曹', '郑', '燕', '吴']
TABLE_014_STATE_START_COL = 2  # columns: 公元前, 年, 周, 鲁, ...

# Title suffixes for ruler name normalization
TITLE_SUFFIXES = set('王公侯伯子帝后')

def normalize_ruler_name(raw_name, state):
    """Normalize a ruler name extracted from table cells.
    - Strip personal name (chars after the last title suffix)
    - Prepend state if not present
    """
    name = strip_entity_tags(raw_name).strip()
    if not name:
        return None

    # Remove trailing punctuation
    name = name.rstrip('。，、；：')

    # Strip personal name: find last title suffix, keep up to it
    last_title_idx = -1
    for i, c in enumerate(name):
        if c in TITLE_SUFFIXES:
            last_title_idx = i

    if last_title_idx >= 0 and last_title_idx < len(name) - 1:
        # There are characters after the last title suffix - strip them
        name = name[:last_title_idx + 1]

    # Special cases: Chu rulers use 熊X format (no title suffix)
    # Keep as-is if starts with state name
    ALL_STATES = {'周', '鲁', '齐', '晋', '秦', '楚', '宋', '卫', '陈',
                  '蔡', '曹', '郑', '燕', '吴', '魏', '韩', '赵', '汉'}

    if not any(name.startswith(s) for s in ALL_STATES):
        name = state + name

    return name


def parse_cell_ruler_year(cell_text):
    """Extract (ruler_name_raw, year_num) from a table cell.
    Returns (None, year_num) for continuation cells (just a number).
    Returns (None, None) for empty/unparseable cells.
    """
    cell = strip_entity_tags(cell_text).strip()
    if not cell:
        return None, None

    # Characters that should NOT appear in a valid ruler name
    INVALID_NAME_CHARS = set('。，；：、「」（）')
    MAX_NAME_LEN = 10  # Ruler names are at most ~8 chars

    def is_valid_ruler_name(name):
        """Check if extracted text looks like a ruler name."""
        name = name.strip()
        if not name:
            return False
        if len(name) > MAX_NAME_LEN:
            return False
        if any(c in INVALID_NAME_CHARS for c in name):
            return False
        return True

    # Check for "元年" entry: text + 元年 + optional annotation
    m = re.search(r'^(.+?)元年', cell)
    if m and is_valid_ruler_name(m.group(1)):
        return m.group(1), 1

    # Check for "RulerNameX年" (non-元年, like "真公濞十五年")
    m = re.match(rf'^(.+?)({CN_NUM_PAT})年', cell)
    if m:
        ruler_raw = m.group(1)
        year_num = cn_to_int(m.group(2))
        if ruler_raw and year_num and is_valid_ruler_name(ruler_raw):
            return ruler_raw, year_num

    # Continuation: just a number, possibly with annotation
    m = re.match(rf'^({CN_NUM_PAT})(?:[^年]|$)', cell)
    if m:
        year_num = cn_to_int(m.group(1))
        return None, year_num

    return None, None


def parse_table_014():
    """Parse 十二诸侯年表 to extract reign periods."""
    filepath = None
    for f in glob.glob(os.path.join(CHAPTER_DIR, '014_*.tagged.md')):
        filepath = f
        break
    if not filepath:
        print("Warning: 014_十二诸侯年表 not found")
        return {}

    rulers = {}  # {normalized_name: {state, start_bce, end_bce}}
    current_ruler = {}  # {state: normalized_name}

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_table = False
    for line in lines:
        if line.strip().startswith('| 公元前'):
            in_table = True
            continue
        if line.strip().startswith('| ---'):
            continue
        if not in_table or not line.strip().startswith('|'):
            if in_table and not line.strip().startswith('|'):
                in_table = False
            continue

        cells = parse_table_row(line)
        if not cells or len(cells) < TABLE_014_STATE_START_COL + len(TABLE_014_STATES):
            continue

        bce = extract_bce_year(cells[0])
        if bce is None:
            continue

        for i, state in enumerate(TABLE_014_STATES):
            col_idx = TABLE_014_STATE_START_COL + i
            if col_idx >= len(cells):
                break

            cell = cells[col_idx]
            ruler_raw, year_num = parse_cell_ruler_year(cell)

            if ruler_raw is not None and year_num is not None:
                # New ruler entry or first-row entry
                name = normalize_ruler_name(ruler_raw, state)
                if name:
                    start_bce = bce + year_num - 1

                    # End previous ruler for this state
                    if state in current_ruler:
                        prev_name = current_ruler[state]
                        if prev_name in rulers:
                            rulers[prev_name]['end_bce'] = bce + year_num - 1  # last year was previous year

                    rulers[name] = {'state': state, 'start_bce': start_bce}
                    current_ruler[state] = name

    # Set end years for last rulers (end of table = ~478 BCE)
    for state, name in current_ruler.items():
        if name in rulers and 'end_bce' not in rulers[name]:
            rulers[name]['end_bce'] = 478  # approximate

    return rulers


# ============================================================
# Table 015: 六国年表 (476-207 BCE)
# ============================================================

TABLE_015_STATES = ['周', '秦', '魏', '韩', '赵', '楚', '燕', '齐']
TABLE_015_STATE_START_COL = 1  # columns: 公元前, 周, 秦, ...

def parse_table_015():
    """Parse 六国年表 to extract reign periods."""
    filepath = None
    for f in glob.glob(os.path.join(CHAPTER_DIR, '015_*.tagged.md')):
        filepath = f
        break
    if not filepath:
        print("Warning: 015_六国年表 not found")
        return {}

    rulers = {}
    current_ruler = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_table = False
    for line in lines:
        if line.strip().startswith('| 公元前'):
            in_table = True
            continue
        if line.strip().startswith('| ---'):
            continue
        if not in_table or not line.strip().startswith('|'):
            if in_table and not line.strip().startswith('|'):
                in_table = False
            continue

        cells = parse_table_row(line)
        if not cells or len(cells) < TABLE_015_STATE_START_COL + 1:
            continue

        bce = extract_bce_year(cells[0])
        if bce is None:
            continue

        for i, state in enumerate(TABLE_015_STATES):
            col_idx = TABLE_015_STATE_START_COL + i
            if col_idx >= len(cells):
                break

            cell = cells[col_idx]
            ruler_raw, year_num = parse_cell_ruler_year(cell)

            if ruler_raw is not None and year_num is not None:
                name = normalize_ruler_name(ruler_raw, state)
                if name:
                    start_bce = bce + year_num - 1

                    if state in current_ruler:
                        prev_name = current_ruler[state]
                        if prev_name in rulers:
                            rulers[prev_name]['end_bce'] = start_bce

                    rulers[name] = {'state': state, 'start_bce': start_bce}
                    current_ruler[state] = name

    for state, name in current_ruler.items():
        if name in rulers and 'end_bce' not in rulers[name]:
            rulers[name]['end_bce'] = 207

    return rulers


# ============================================================
# Table 022: 汉兴以来将相名臣年表 (206-20 BCE)
# ============================================================

def parse_table_022():
    """Parse 将相年表 to extract Han dynasty reign periods and era names."""
    filepath = None
    for f in glob.glob(os.path.join(CHAPTER_DIR, '022_*.tagged.md')):
        filepath = f
        break
    if not filepath:
        print("Warning: 022_汉兴以来将相名臣年表 not found")
        return {}, {}

    rulers = {}  # {name: {state, start_bce, end_bce}}
    eras = {}    # {era_name: {ruler, start_bce, end_bce}}

    current_ruler = None  # current emperor name
    current_era = None    # current era name (年号)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_table = False
    for line in lines:
        if line.strip().startswith('| 公元前'):
            in_table = True
            continue
        if line.strip().startswith('| ---'):
            continue
        if not in_table or not line.strip().startswith('|'):
            if in_table and not line.strip().startswith('|'):
                in_table = False
            continue

        cells = parse_table_row(line)
        if not cells or len(cells) < 2:
            continue

        bce = extract_bce_year(cells[0])
        if bce is None:
            continue

        jinian = strip_entity_tags(cells[1]).strip()

        # Detect 元年 entries in 纪年 column
        if '元年' in jinian:
            # Patterns (in order of specificity):
            # 1. "孝武建元元年" → ruler=孝武, era=建元
            # 2. "孝景元年" → ruler=孝景, no era
            # 3. "元光元年" → era=元光 (same ruler)
            # 4. "后元年" or "后元元年" or "中元年" → secondary era

            if jinian in ('后元年', '中元年', '后元元年'):
                # Secondary era within current ruler's reign
                era_prefix = jinian.replace('元年', '').replace('元', '')
                era_name = (current_ruler or '') + era_prefix
                if current_era and current_era in eras:
                    eras[current_era]['end_bce'] = bce + 1
                current_era = era_name
                eras[era_name] = {'ruler': current_ruler, 'state': '汉', 'start_bce': bce}
            else:
                # Check for Emperor+Era pattern: "孝武建元元年", "孝昭始元元年"
                # Or Emperor-only: "高皇帝元年", "孝惠元年", "孝文元年"
                # Or Era-only: "元光元年", "太初元年"
                text_before = jinian.replace('元年', '').rstrip('。')

                # Known emperor prefixes
                emperor_prefixes = ['高皇帝', '孝惠', '高后', '孝文', '孝景',
                                    '孝武', '孝昭', '孝宣', '孝元', '孝成']

                found_emperor = None
                found_era = None

                for ep in emperor_prefixes:
                    if text_before.startswith(ep):
                        found_emperor = ep
                        remainder = text_before[len(ep):]
                        if remainder:
                            found_era = remainder
                        break

                if found_emperor is None and text_before:
                    # Pure era name (元光, 太初, etc.)
                    found_era = text_before

                if found_emperor:
                    # End previous ruler
                    if current_ruler and current_ruler in rulers:
                        rulers[current_ruler]['end_bce'] = bce + 1
                    if current_era and current_era in eras:
                        eras[current_era]['end_bce'] = bce + 1

                    current_ruler = found_emperor
                    rulers[found_emperor] = {'state': '汉', 'start_bce': bce}

                    if found_era:
                        current_era = found_era
                        eras[found_era] = {'ruler': found_emperor, 'state': '汉', 'start_bce': bce}
                    else:
                        current_era = None
                elif found_era:
                    # New era, same ruler
                    if current_era and current_era in eras:
                        eras[current_era]['end_bce'] = bce + 1
                    current_era = found_era
                    eras[found_era] = {'ruler': current_ruler, 'state': '汉', 'start_bce': bce}

    # Set end years for last entries
    if current_ruler and current_ruler in rulers and 'end_bce' not in rulers[current_ruler]:
        rulers[current_ruler]['end_bce'] = 20
    if current_era and current_era in eras and 'end_bce' not in eras[current_era]:
        eras[current_era]['end_bce'] = 20

    return rulers, eras


# ============================================================
# Combine and save reign_periods.json
# ============================================================

# Manual additions/corrections for rulers not well-captured by table parsing
MANUAL_RULERS = {
    # 秦统一后 (not in 015 which ends with 秦 as a state)
    '秦始皇': {'state': '秦', 'start_bce': 246, 'end_bce': 210},
    '秦二世': {'state': '秦', 'start_bce': 209, 'end_bce': 207},
    # 共和 regency
    '共和': {'state': '周', 'start_bce': 841, 'end_bce': 828},

    # ── 夏商周断代工程：西周王室（pre-841 BCE） ──
    '周文王': {'state': '周', 'start_bce': 1099, 'end_bce': 1050},  # 即位约50年，断代工程推算
    '周武王': {'state': '周', 'start_bce': 1049, 'end_bce': 1043},  # 克商1046年
    '周成王': {'state': '周', 'start_bce': 1042, 'end_bce': 1021},
    '周康王': {'state': '周', 'start_bce': 1020, 'end_bce': 996},
    '周昭王': {'state': '周', 'start_bce': 995, 'end_bce': 977},
    '周穆王': {'state': '周', 'start_bce': 976, 'end_bce': 922},
    '周共王': {'state': '周', 'start_bce': 922, 'end_bce': 900},
    '周懿王': {'state': '周', 'start_bce': 899, 'end_bce': 892},
    '周孝王': {'state': '周', 'start_bce': 892, 'end_bce': 886},
    '周夷王': {'state': '周', 'start_bce': 885, 'end_bce': 878},
    '周厉王': {'state': '周', 'start_bce': 877, 'end_bce': 841},
    # 周公摄政（成王年幼期间）
    '周公': {'state': '周', 'start_bce': 1042, 'end_bce': 1036},

    # ── 夏商周断代工程：商后期 ──
    '帝武丁': {'state': '商', 'start_bce': 1250, 'end_bce': 1192},
    '武乙': {'state': '商', 'start_bce': 1147, 'end_bce': 1113},
    '文丁': {'state': '商', 'start_bce': 1112, 'end_bce': 1102},
    '帝乙': {'state': '商', 'start_bce': 1101, 'end_bce': 1076},
    '帝辛': {'state': '商', 'start_bce': 1075, 'end_bce': 1046},

    # ── 鲁国早期（由鲁真公855BCE向前推算，据史记记载年数） ──
    '鲁公伯禽': {'state': '鲁', 'start_bce': 1040, 'end_bce': 997},  # 46年（一说53年）
    '鲁考公': {'state': '鲁', 'start_bce': 996, 'end_bce': 993},     # 4年
    '鲁炀公': {'state': '鲁', 'start_bce': 992, 'end_bce': 987},     # 6年
    '鲁幽公': {'state': '鲁', 'start_bce': 986, 'end_bce': 973},     # 14年
    '鲁魏公': {'state': '鲁', 'start_bce': 972, 'end_bce': 923},     # 50年
    '鲁厉公': {'state': '鲁', 'start_bce': 922, 'end_bce': 886},     # 37年
    '鲁献公': {'state': '鲁', 'start_bce': 885, 'end_bce': 855},     # 32年（一说50年）

    # ── 齐国早期（由齐武公850BCE向前推算） ──
    '齐献公': {'state': '齐', 'start_bce': 859, 'end_bce': 851},     # 9年

    # ── 宋国早期 ──
    '宋微子': {'state': '宋', 'start_bce': 1040, 'end_bce': 996},    # 微子启，约44年

    # ── 其他重要诸侯/人物 ──
    '越王勾践': {'state': '越', 'start_bce': 496, 'end_bce': 465},   # 句践
    '赵襄子': {'state': '赵', 'start_bce': 475, 'end_bce': 425},     # 无恤，赵氏执政
    '赵幽缪王': {'state': '赵', 'start_bce': 236, 'end_bce': 228},   # 赵迁

    # ── 汉代（CE纪年，用负数表示公元后） ──
    '孝明皇帝': {'state': '汉', 'start_bce': -57, 'end_bce': -75},   # 汉明帝 (57-75 CE)
}

# Alias mapping: primary_name → [aliases that appear in text]
RULER_ALIASES = {
    '高皇帝': ['高祖', '高帝', '刘邦', '汉王'],
    '孝惠': ['孝惠帝', '惠帝', '孝惠皇帝'],
    '高后': ['吕后', '吕太后', '高太后'],
    '孝文': ['孝文帝', '文帝', '孝文皇帝'],
    '孝景': ['孝景帝', '景帝', '孝景皇帝'],
    '孝武': ['孝武帝', '武帝', '孝武皇帝'],
    '孝昭': ['孝昭帝', '昭帝'],
    '孝宣': ['孝宣帝', '宣帝', '孝宣皇帝'],
    '孝元': ['孝元帝', '元帝'],
    '孝成': ['孝成帝', '成帝'],
    # Table names that differ from common text names
    '秦惠文王': ['秦惠王'],
    '秦昭襄王': ['秦昭王'],
    '秦始皇帝': ['秦始皇', '始皇'],
    '秦始皇': ['秦王政'],
    '秦二世': ['二世'],
    # Pre-841 BCE aliases (unambiguous in 史记 context)
    '周文王': ['西伯'],           # 西伯昌 = 周文王
    '帝武丁': ['高宗'],           # 商高宗 = 武丁
    '帝辛': ['纣', '纣王', '帝纣'],  # 商纣王
    '鲁公伯禽': ['伯禽'],         # 鲁国始封君
    '鲁湣公': ['鲁闵公'],         # 闵/湣 通假
    '宋微子': ['微子'],           # 宋国始封君
    '越王勾践': ['句践', '勾践'],  # 越王
    '赵幽缪王': ['幽缪王'],       # 赵末代王
    '孝明皇帝': ['孝明', '明帝', '汉孝明皇帝'],  # 汉明帝
}


def extract_reign_periods():
    """Extract reign periods from all tables and combine."""
    print("=== Phase 1: Extracting reign periods ===")

    # Parse tables
    rulers_014 = parse_table_014()
    print(f"  Table 014: {len(rulers_014)} rulers extracted")

    rulers_015 = parse_table_015()
    print(f"  Table 015: {len(rulers_015)} rulers extracted")

    rulers_022, eras_022 = parse_table_022()
    print(f"  Table 022: {len(rulers_022)} rulers, {len(eras_022)} eras extracted")

    # Combine rulers (015 overrides 014 for overlapping entries,
    # since 015 covers later period with better names)
    all_rulers = {}
    all_rulers.update(rulers_014)
    all_rulers.update(rulers_015)  # Later table takes precedence
    all_rulers.update(rulers_022)
    all_rulers.update(MANUAL_RULERS)

    # Fix rulers whose end_bce is wrong due to table boundaries or parsing issues.
    # In BCE numbering, LOWER values = LATER dates (207 is later than 256).
    # Two cases:
    #   - end_bce too late (too low): table default 478/207 for rulers who died earlier
    #   - end_bce too early (too high): table boundary cut off rulers who reigned longer
    END_BCE_CORRECTIONS = {
        '鲁哀公': 468,     # 实际在位到约468 BCE（史记：27年），表默认478过早
        '晋定公': 475,     # 实际在位到约475 BCE
        '郑声公': 463,     # 实际在位到约463 BCE
        '周赧王': 256,     # 周灭于256 BCE，表默认207过晚
    }
    for name, corrected_end in END_BCE_CORRECTIONS.items():
        if name in all_rulers:
            all_rulers[name]['end_bce'] = corrected_end

    # Add aliases
    aliases = {}
    for primary, alias_list in RULER_ALIASES.items():
        if primary in all_rulers:
            for alias in alias_list:
                aliases[alias] = primary

    result = {
        'rulers': all_rulers,
        'eras': eras_022,
        'aliases': aliases,
    }

    print(f"  Total: {len(all_rulers)} rulers, {len(eras_022)} eras")
    return result


def save_reign_periods(data):
    """Save reign periods to JSON file."""
    # Sort rulers by start_bce (descending = earliest first)
    sorted_rulers = OrderedDict(
        sorted(data['rulers'].items(),
               key=lambda x: x[1].get('start_bce', 0),
               reverse=True)
    )
    data['rulers'] = sorted_rulers

    with open(REIGN_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {REIGN_FILE}")


# ============================================================
# Phase 2: Year entity scanning and disambiguation
# ============================================================

# Pattern to match year entities in tagged.md: %X年%
# X = Chinese numeral (元, 二, 三, ..., 四十八, etc.)
# Exclude: durations (%十馀年%), ages (%十岁%), months (%五月%), seasons (%春%)
YEAR_ENTITY_RE = re.compile(rf'%({CN_NUM_PAT}年)%')

# Patterns that are NOT calendar years (durations, ages, etc.)
NOT_CALENDAR_YEAR_PATS = [
    re.compile(r'馀年'),    # X馀年 = more than X years (duration)
    re.compile(r'岁'),      # X岁 = X years old (age)
    re.compile(r'有馀'),    # X有馀年
]

# Era names from table 022 that appear in text as %建元六年% etc.
# (populated from reign_periods.json)

# Paragraph number pattern
PARA_NUM_RE = re.compile(r'^\[([0-9]+(?:\.[0-9]+)*)\]')

# Person entity pattern (for finding nearby ruler mentions)
# Also match $title$ since many rulers are tagged as titles (e.g., $武公$, $庄公$)
PERSON_RE = re.compile(r'@([^@\n]+)@')
TITLE_RE = re.compile(r'\$([^$\n]+)\$')

# Section header with ruler name
SECTION_HEADER_RE = re.compile(r'^##+ (.+)')

# Chapter → primary state mapping (same logic as disambiguate_names.py)
CHAPTER_STATE = {
    '001': '', '002': '', '003': '',  # 五帝/夏/殷 - no fixed state
    '004': '周', '005': '秦', '006': '秦',
    '007': '楚',  # 项羽本纪 - special
    '008': '汉', '009': '汉', '010': '汉', '011': '汉', '012': '汉',
    '031': '吴', '032': '齐', '033': '鲁', '034': '燕', '035': '管',
    '036': '陈', '037': '卫', '038': '宋', '039': '晋', '040': '楚',
    '041': '越', '042': '郑', '043': '赵', '044': '魏', '045': '韩',
    '046': '齐',  # 田敬仲完世家 (田齐=齐)
    '047': '孔', '048': '陈', '049': '楚',
}

# State aliases: some chapters use a different state name than reign_periods
# e.g., 田 → 齐 (田齐 in table 015 is listed under 齐)
STATE_ALIASES = {'田': '齐'}


def build_ruler_lookup(reign_data):
    """Build lookup structures for year disambiguation.

    Returns:
        name_to_start: {ruler_name: start_bce} (direct lookup)
        state_rulers: {state: [(ruler_name, start_bce, end_bce), ...]} sorted by time
        era_to_start: {era_name: start_bce}
        alias_to_primary: {alias: primary_name}
    """
    name_to_start = {}
    state_rulers = defaultdict(list)
    era_to_start = {}
    alias_to_primary = {}

    for name, info in reign_data.get('rulers', {}).items():
        start = info.get('start_bce', 0)
        end = info.get('end_bce', 0)
        state = info.get('state', '')
        name_to_start[name] = start
        state_rulers[state].append((name, start, end))

    # Sort by start_bce descending (earliest first)
    for state in state_rulers:
        state_rulers[state].sort(key=lambda x: x[1], reverse=True)

    for era_name, info in reign_data.get('eras', {}).items():
        era_to_start[era_name] = info.get('start_bce', 0)

    for alias, primary in reign_data.get('aliases', {}).items():
        alias_to_primary[alias] = primary

    return name_to_start, dict(state_rulers), era_to_start, alias_to_primary


def load_person_disambig():
    """Load person disambiguation map for resolving short ruler names."""
    if not os.path.exists(DISAMBIG_FILE):
        return {}
    with open(DISAMBIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_nearby_rulers(text, year_pos, max_dist=60):
    """Find all person/title entities before the year position (within max_dist).
    Searches both @person@ and $title$ patterns since rulers may be tagged as either.
    Returns list of (name, tag_type) tuples, ordered nearest-first.
    """
    search_start = max(0, year_pos - max_dist)
    before_text = text[search_start:year_pos]

    # Find all person entities AND title entities in the before text
    # Combine and sort by position
    found = []
    for m in PERSON_RE.finditer(before_text):
        found.append((m.start(), m.group(1), 'person'))
    for m in TITLE_RE.finditer(before_text):
        found.append((m.start(), m.group(1), 'title'))

    # Sort by position descending (nearest first)
    found.sort(key=lambda x: x[0], reverse=True)
    return [name for _, name, _ in found]


def resolve_ruler_name(raw_name, chapter_id, name_to_start, alias_to_primary, person_disambig,
                        chapter_state=''):
    """Resolve a ruler name to its canonical form in reign_periods.

    Tries (in order):
    1. Direct match in name_to_start
    2. Chapter-state-prefixed name (e.g., 宣公 → 秦宣公 in 秦本纪)
    3. Via ruler aliases
    4. Via person disambiguation map (short name → full name)
    5. Via aliases after disambiguation
    """
    # Direct match
    if raw_name in name_to_start:
        return raw_name

    # Try chapter-state-prefixed name (高priority for 本纪/世家 chapters)
    if chapter_state:
        prefixed = chapter_state + raw_name
        if prefixed in name_to_start:
            return prefixed
        if prefixed in alias_to_primary:
            primary = alias_to_primary[prefixed]
            if primary in name_to_start:
                return primary

    # Via aliases
    if raw_name in alias_to_primary:
        primary = alias_to_primary[raw_name]
        if primary in name_to_start:
            return primary

    # Via person disambiguation map
    chapter_disambig = person_disambig.get(chapter_id, {})
    full_name = chapter_disambig.get(raw_name, raw_name)
    if full_name in name_to_start:
        return full_name

    # Via aliases after disambiguation
    if full_name in alias_to_primary:
        primary = alias_to_primary[full_name]
        if primary in name_to_start:
            return primary

    return None


def is_calendar_year(surface_text, context_before):
    """Check if a year mention is a calendar year (not a duration/age).

    Heuristic: if the text before the year contains patterns like
    "立", "居", "在位", etc., it might be a duration.
    """
    # Check for duration/age patterns in the surface text itself
    for pat in NOT_CALENDAR_YEAR_PATS:
        if pat.search(surface_text):
            return False

    # Check context: "立X年" or "在位X年" etc. are durations
    if context_before:
        last_chars = context_before[-3:]
        if any(c in last_chars for c in ['立', '居', '历', '凡', '共', '在', '生', '国']):
            # Likely a duration: "立十二年卒" = "ruled for 12 years, died"
            return False

    return True


def calc_ce_year(start_bce, year_num):
    """Calculate CE year from ruler's start_bce and reign year number.
    Returns negative value for BCE.
    """
    bce = start_bce - year_num + 1
    return -bce


def disambiguate_years(reign_data):
    """Scan all tagged.md files and disambiguate year entities."""
    print("\n=== Phase 2: Year disambiguation ===")

    name_to_start, state_rulers, era_to_start, alias_to_primary = build_ruler_lookup(reign_data)
    person_disambig = load_person_disambig()

    year_map = {}  # {chapter_id: {para_id: {surface: {ce_year, ruler, method}}}}
    stats = defaultdict(int)

    md_files = sorted(glob.glob(os.path.join(CHAPTER_DIR, '*.tagged.md')))
    print(f"  Scanning {len(md_files)} files...")

    for filepath in md_files:
        filename = os.path.basename(filepath)
        chapter_id = filename[:3]

        # Skip table chapters (they already have BCE years)
        if chapter_id in ('013', '014', '015', '016', '017', '018', '019', '020', '021', '022'):
            continue

        chapter_state = CHAPTER_STATE.get(chapter_id, '')
        # Resolve state aliases (e.g., 田→齐)
        lookup_state = STATE_ALIASES.get(chapter_state, chapter_state) if chapter_state else ''

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        current_ruler = None
        current_section_ruler = None
        current_para = '0'

        for line in lines:
            # Track paragraph numbers
            m = PARA_NUM_RE.match(line)
            if m:
                current_para = m.group(1)

            # Track section headers for ruler context
            m = SECTION_HEADER_RE.match(line)
            if m:
                header_text = strip_entity_tags(m.group(1)).strip()
                # Check if header contains a ruler name
                # Headers like "## 文公、宁公" or "## 秦王政时期"
                # Strip common suffixes before matching
                header_cleaned = re.sub(
                    r'(?:时期|早期|晚期|征伐|之乱|世系表|大事记|东巡|暴政|称王|继位|称霸|末年|灭国|让国|出使|篡位|诏|诏书)$',
                    '', header_text)
                for part in re.split(r'[、，]', header_cleaned):
                    part = part.strip()
                    if not part:
                        continue
                    resolved = resolve_ruler_name(
                        part, chapter_id, name_to_start,
                        alias_to_primary, person_disambig, lookup_state)
                    if resolved:
                        # Only use as section ruler if matches chapter state
                        ruler_state = reign_data['rulers'].get(resolved, {}).get('state', '')
                        if not lookup_state or ruler_state == lookup_state:
                            current_section_ruler = resolved
                            current_ruler = resolved
                        break
                continue

            # Find all year entity occurrences in this line
            for match in YEAR_ENTITY_RE.finditer(line):
                surface = match.group(1)  # e.g., "三年", "元年"
                match_start = match.start()

                # Parse year number
                year_str = surface.replace('年', '')
                year_num = cn_to_int(year_str)
                if year_num is None:
                    continue

                # Check if this is a calendar year (not duration/age)
                context_before = line[max(0, match_start - 5):match_start]
                if not is_calendar_year(surface, context_before):
                    stats['skipped_duration'] += 1
                    continue

                # Check if this contains an era name: %建元六年%, %太初元年%
                era_match = None
                for era_name, era_start in era_to_start.items():
                    if surface.startswith(era_name):
                        era_year_str = surface[len(era_name):].replace('年', '')
                        if era_year_str:
                            era_year_num = cn_to_int(era_year_str)
                        else:
                            era_year_num = None
                        if era_year_num:
                            era_match = (era_name, era_start, era_year_num)
                            break

                if era_match:
                    era_name, era_start, era_year_num = era_match
                    ce_year = calc_ce_year(era_start, era_year_num)
                    if chapter_id not in year_map:
                        year_map[chapter_id] = {}
                    if current_para not in year_map[chapter_id]:
                        year_map[chapter_id][current_para] = {}
                    year_map[chapter_id][current_para][surface] = {
                        'ce_year': ce_year,
                        'ruler': era_name,
                        'method': 'era_name'
                    }
                    stats['era_name'] += 1
                    continue

                # Try to find the ruler for this year
                ruler = None
                raw_ruler = None  # unresolved nearby person name
                method = None
                best_foreign = None
                best_raw = None

                # Strategy 1: Nearby explicit ruler/title mention
                # Prefer rulers from the chapter's primary state;
                # track closest foreign ruler for fallback
                nearby_persons = find_nearby_rulers(line, match_start)
                first_resolved_foreign = None  # closest resolved foreign ruler
                if nearby_persons:
                    # Remember nearest clean name for fallback
                    for p in nearby_persons:
                        pc = p.strip()
                        if (pc and len(pc) <= 8
                                and not any(c in pc for c in '。，；：,.%@$&=*!?~')
                                and re.search(r'[\u4e00-\u9fff]', pc)):
                            best_raw = pc
                            break
                    for person in nearby_persons:
                        resolved = resolve_ruler_name(
                            person, chapter_id, name_to_start,
                            alias_to_primary, person_disambig, lookup_state)
                        if resolved:
                            ruler_state = reign_data['rulers'].get(resolved, {}).get('state', '')
                            if ruler_state == lookup_state and lookup_state:
                                ruler = resolved
                                method = 'nearby_ruler'
                                break
                            elif best_foreign is None:
                                best_foreign = resolved
                                if first_resolved_foreign is None:
                                    first_resolved_foreign = resolved
                    # Use foreign ruler if chapter has no primary state
                    if ruler is None and best_foreign and not lookup_state:
                        ruler = best_foreign
                        method = 'nearby_ruler'
                    # Remember raw name for pre-table-era fallback
                    if ruler is None and best_raw:
                        raw_ruler = best_raw

                # Strategy 1b: If the closest resolved entity is a foreign ruler
                # and it's the FIRST person found (immediately preceding the year),
                # it takes priority over sequential — explicit mention outranks inheritance
                if ruler is None and first_resolved_foreign and nearby_persons:
                    first_person = nearby_persons[0]
                    first_resolved = resolve_ruler_name(
                        first_person, chapter_id, name_to_start,
                        alias_to_primary, person_disambig, lookup_state)
                    if first_resolved == first_resolved_foreign:
                        ruler = first_resolved_foreign
                        method = 'nearby_ruler'

                # Strategy 2: Same ruler as previous year in this section
                if ruler is None and current_ruler:
                    # If this is 元年, it might be a new ruler
                    if year_num == 1 and nearby_persons:
                        pass  # already handled above
                    else:
                        ruler = current_ruler
                        method = 'sequential'

                # Strategy 3: Section header ruler
                if ruler is None and current_section_ruler:
                    ruler = current_section_ruler
                    method = 'section_ruler'

                # Strategy 4: Foreign ruler fallback (e.g., 周武王 in 鲁世家 narrative)
                if ruler is None and best_foreign:
                    ruler = best_foreign
                    method = 'nearby_ruler'

                # Compute CE year if ruler is in reign_periods
                ce_year = None
                if ruler and ruler in name_to_start:
                    start_bce = name_to_start[ruler]
                    ce_year = calc_ce_year(start_bce, year_num)

                    # Sanity check: year should be within ruler's reign
                    ruler_info = reign_data['rulers'].get(ruler, {})
                    ruler_end = ruler_info.get('end_bce', 0)
                    result_bce = start_bce - year_num + 1
                    if ruler_end > 0 and result_bce < ruler_end - 5:
                        # Out of range — try recovery: find correct same-state ruler
                        # whose reign actually contains year_num
                        ce_year = None
                        ruler_state = ruler_info.get('state', '')
                        recovered = False
                        if ruler_state and year_num <= 60:
                            matched_start = name_to_start[ruler]
                            # Look for later rulers of same state (lower start_bce)
                            candidates = [(n, s, e) for n, s, e in
                                          state_rulers.get(ruler_state, [])
                                          if s < matched_start]
                            for r_name, r_start, r_end in candidates:
                                new_bce = r_start - year_num + 1
                                if r_end - 5 <= new_bce <= r_start:
                                    ce_year = -new_bce
                                    ruler = r_name
                                    method = (method or 'sequential') + '_corrected'
                                    recovered = True
                                    stats['out_of_range_recovered'] += 1
                                    break
                        if not recovered:
                            stats['skipped_out_of_range'] += 1

                # Determine ruler_key for indexing (used when ce_year is None)
                display_ruler = ruler or raw_ruler or ''
                ruler_key = f'{display_ruler}{surface}' if display_ruler else None

                # Record the mapping
                if ruler or raw_ruler:
                    if chapter_id not in year_map:
                        year_map[chapter_id] = {}
                    if current_para not in year_map[chapter_id]:
                        year_map[chapter_id][current_para] = {}
                    entry = {
                        'ruler': display_ruler,
                        'method': method or 'raw_nearby'
                    }
                    if ce_year is not None:
                        entry['ce_year'] = ce_year
                    if ruler_key and ce_year is None:
                        entry['ruler_key'] = ruler_key
                    year_map[chapter_id][current_para][surface] = entry
                    stats[method or 'raw_nearby'] += 1

                    # Update current ruler tracking
                    if ruler and ruler in name_to_start:
                        ruler_state = reign_data['rulers'].get(ruler, {}).get('state', '')
                        if not lookup_state or ruler_state == lookup_state:
                            if year_num == 1 and method == 'nearby_ruler':
                                current_ruler = ruler
                            elif method in ('nearby_ruler', 'sequential'):
                                current_ruler = ruler
                else:
                    stats['unresolved'] += 1

    # Print stats
    total_mapped = sum(v for k, v in stats.items()
                       if k not in ('unresolved', 'skipped_duration', 'skipped_out_of_range',
                                    'out_of_range_recovered'))
    print(f"\n  SUMMARY:")
    print(f"    Mapped: {total_mapped}")
    for method in ['era_name', 'nearby_ruler', 'sequential', 'section_ruler', 'raw_nearby']:
        if stats[method]:
            print(f"      {method}: {stats[method]}")
    if stats['out_of_range_recovered']:
        print(f"    Recovered (out-of-range → correct ruler): {stats['out_of_range_recovered']}")
    print(f"    Skipped (duration/age): {stats['skipped_duration']}")
    print(f"    Skipped (out of range): {stats['skipped_out_of_range']}")
    print(f"    Unresolved: {stats['unresolved']}")

    return year_map


def save_year_map(year_map):
    """Save year_ce_map.json."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(year_map, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {OUTPUT_FILE}")

    # Count total mappings
    total = sum(
        len(paras)
        for chapter in year_map.values()
        for paras in chapter.values()
    )
    print(f"  Total mappings: {total} across {len(year_map)} chapters")


# ============================================================
# Phase 3: Generate timeline.html
# ============================================================

TIMELINE_FILE = os.path.join(BASE_DIR, 'docs', 'entities', 'timeline.html')


def get_chapter_name_map():
    """Build chapter_id → (title, full_filename_stem) map from filenames.
    E.g., '005' → ('秦本纪', '005_秦本纪')
    """
    name_map = {}
    for f in glob.glob(os.path.join(CHAPTER_DIR, '*.tagged.md')):
        fname = os.path.basename(f).replace('.tagged.md', '')
        chapter_id = fname[:3]
        parts = fname.split('_', 1)
        title = parts[1] if len(parts) > 1 else fname
        name_map[chapter_id] = (title, fname)
    return name_map


def extract_paragraph_text(chapter_id, para_id, max_len=80):
    """Extract the text of a paragraph from a chapter's tagged.md file.
    Returns a clean text snippet (entity tags stripped).
    """
    pattern = os.path.join(CHAPTER_DIR, f'{chapter_id}_*.tagged.md')
    files = glob.glob(pattern)
    if not files:
        return ''

    with open(files[0], 'r', encoding='utf-8') as f:
        for line in f:
            m = PARA_NUM_RE.match(line)
            if m and m.group(1) == para_id:
                text = strip_entity_tags(line)
                text = re.sub(r'^\[\d+(?:\.\d+)*\]\s*', '', text).strip()
                if len(text) > max_len:
                    text = text[:max_len] + '…'
                return text
    return ''


def format_bce_year(ce_year):
    """Format a CE year value to display string.
    ce_year < 0 → '公元前X年', ce_year > 0 → '公元X年'
    """
    if ce_year < 0:
        return f'公元前{-ce_year}年'
    elif ce_year == 0:
        return '公元前1年'  # No year 0
    else:
        return f'公元{ce_year}年'


def get_century_label(ce_year):
    """Get century group label for a CE year.
    -850 → '前9世纪', -350 → '前4世纪', 50 → '1世纪'
    """
    if ce_year <= 0:
        century = (-ce_year) // 100 + 1
        return f'前{century}世纪'
    else:
        century = (ce_year - 1) // 100 + 1
        return f'{century}世纪'


def compute_reign_aliases(reign_data, ce_year):
    """Compute all concurrent reign-year aliases for a given CE year.
    Returns list of strings like '秦孝公元年', '周显王八年'.
    """
    aliases = []
    bce = -ce_year if ce_year <= 0 else 0
    for ruler_name, info in reign_data.get('rulers', {}).items():
        start = info.get('start_bce', 0)
        end = info.get('end_bce', 0)
        if start >= bce >= end:
            year_num = start - bce + 1
            cn_year = int_to_cn(year_num)
            aliases.append((start, f'{ruler_name}{cn_year}年'))
    # Sort by start_bce descending (earliest-established states first)
    aliases.sort(key=lambda x: x[0], reverse=True)
    return [a[1] for a in aliases]


def generate_timeline(year_map, reign_data=None):
    """Generate timeline.html — CE-year indexed page.
    Handles both CE-year entries and ruler_key entries (pre-841 BCE).
    """
    print("\n=== Phase 3: Generating timeline.html ===")

    chapter_names = get_chapter_name_map()

    # Aggregate references:
    # CE-year entries → by_year {ce_year: [...]}
    # ruler_key entries → by_ruler_key {ruler_key: [...]}
    by_year = defaultdict(list)
    by_ruler_key = defaultdict(list)

    for chapter_id, paras in year_map.items():
        for para_id, entries in paras.items():
            for surface, info in entries.items():
                ruler = info.get('ruler', '')
                if 'ce_year' in info:
                    ce_year = info['ce_year']
                    by_year[ce_year].append((chapter_id, para_id, surface, ruler))
                elif 'ruler_key' in info:
                    rk = info['ruler_key']
                    by_ruler_key[rk].append((chapter_id, para_id, surface, ruler))

    # Sort by CE year (ascending = earliest BCE first)
    sorted_years = sorted(by_year.keys())

    total_years = len(sorted_years)
    total_refs = sum(len(refs) for refs in by_year.values())
    total_ruler_keys = len(by_ruler_key)
    total_ruler_refs = sum(len(refs) for refs in by_ruler_key.values())
    print(f"  {total_years} distinct CE years, {total_refs} references")
    if total_ruler_keys:
        print(f"  {total_ruler_keys} ruler+year entries (pre-table era), {total_ruler_refs} references")

    # Group by century
    centuries = OrderedDict()
    for ce_year in sorted_years:
        label = get_century_label(ce_year)
        if label not in centuries:
            centuries[label] = []
        centuries[label].append(ce_year)

    # Build HTML
    import html as html_mod

    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html lang="zh-CN">')
    lines.append('<head>')
    lines.append('    <meta charset="UTF-8">')
    lines.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append('    <title>编年索引 - 史记知识库</title>')
    lines.append('    <link rel="stylesheet" href="../css/shiji-styles.css">')
    lines.append('    <link rel="stylesheet" href="../css/entity-index.css">')
    lines.append('    <link rel="stylesheet" href="../css/timeline.css">')
    lines.append('</head>')
    lines.append('<body>')

    # Navigation
    lines.append('<nav class="chapter-nav">')
    lines.append('    <a href="../index.html" class="nav-home">回到主页</a>')
    lines.append('    <a href="index.html" class="nav-next">实体索引</a>')
    lines.append('</nav>')

    lines.append('<h1>编年索引</h1>')
    lines.append(f'<p class="index-stats">共 <strong>{total_years}</strong> 个年份，'
                 f'<strong>{total_refs}</strong> 次引用</p>')

    # Search filter
    lines.append('<div class="entity-filter">')
    lines.append('    <input type="text" id="filter-input" placeholder="搜索年份或人名...">')
    lines.append('</div>')

    # Century navigation bar
    lines.append('<div class="pinyin-nav">')
    for label, years in centuries.items():
        count = len(years)
        safe_id = label.replace('前', 'pre')
        lines.append(f'  <a href="#century-{safe_id}" class="pinyin-letter">'
                     f'{label}<span class="letter-count">{count}</span></a>')
    if by_ruler_key:
        lines.append(f'  <a href="#century-pretable" class="pinyin-letter">'
                     f'先秦早期<span class="letter-count">{total_ruler_keys}</span></a>')
    lines.append('</div>')

    # Year entries grouped by century
    lines.append('<div class="entity-index timeline-index">')

    for century_label, years_in_century in centuries.items():
        safe_id = century_label.replace('前', 'pre')
        lines.append(f'<div class="letter-section" id="century-{safe_id}">')
        lines.append(f'  <h2 class="letter-heading">{century_label}</h2>')

        for ce_year in years_in_century:
            refs = by_year[ce_year]
            year_display = format_bce_year(ce_year)
            year_anchor = f'year-{ce_year}'

            # Compute reign year aliases from all concurrent rulers
            if reign_data:
                alias_list = compute_reign_aliases(reign_data, ce_year)
            else:
                alias_list = []
            # Fallback: use rulers from references if no reign_data
            if not alias_list:
                rulers_at_year = set(r for _, _, _, r in refs)
                alias_list = sorted(rulers_at_year)
            ruler_str = '、'.join(alias_list)

            lines.append(f'  <div class="entity-entry timeline-entry" id="{year_anchor}">')

            # Left: year + ruler
            lines.append('    <div class="entry-left">')
            lines.append(f'      <span class="canonical-name time">{html_mod.escape(year_display)}</span>')
            if ruler_str:
                lines.append(f'      <span class="alias-list">{html_mod.escape(ruler_str)}</span>')
            lines.append(f'      <span class="entry-count">({len(refs)})</span>')
            lines.append('    </div>')

            # Right: chapter references with paragraph excerpts
            lines.append('    <div class="entry-right">')

            # Group refs by chapter
            refs_by_chapter = defaultdict(list)
            for ch_id, para_id, surface, ruler in refs:
                refs_by_chapter[ch_id].append((para_id, surface, ruler))

            ref_parts = []
            for ch_id in sorted(refs_by_chapter.keys()):
                ch_title, ch_stem = chapter_names.get(ch_id, (ch_id, ch_id))
                ch_name = html_mod.escape(ch_title)
                ch_refs = refs_by_chapter[ch_id]

                ch_link = f'<a href="../chapters/{ch_stem}.html" class="chapter-ref-name">{ch_name}</a>'
                para_links = []
                for para_id, surface, ruler in ch_refs:
                    para_links.append(
                        f'<a href="../chapters/{ch_stem}.html#pn-{para_id}" class="para-ref">{para_id}</a>'
                    )
                ref_parts.append(f'{ch_link} {", ".join(para_links)}')

            lines.append('      ' + ' <span class="ref-sep">|</span> '.join(ref_parts))
            lines.append('    </div>')

            lines.append('  </div>')

        lines.append('</div>')

    # Pre-table-era section (ruler+year indexed, no CE year)
    if by_ruler_key:
        lines.append('<div class="letter-section" id="century-pretable">')
        lines.append('  <h2 class="letter-heading">先秦早期（年代不详）</h2>')
        # Sort by ruler_key alphabetically
        for rk in sorted(by_ruler_key.keys()):
            refs = by_ruler_key[rk]
            anchor = f'ruler-{rk}'
            ruler_display = refs[0][3] if refs else ''  # ruler from first ref
            surface_display = refs[0][2] if refs else ''  # surface from first ref

            lines.append(f'  <div class="entity-entry timeline-entry" id="{html_mod.escape(anchor)}">')
            lines.append('    <div class="entry-left">')
            lines.append(f'      <span class="canonical-name time">{html_mod.escape(rk)}</span>')
            lines.append(f'      <span class="entry-count">({len(refs)})</span>')
            lines.append('    </div>')
            lines.append('    <div class="entry-right">')

            refs_by_chapter = defaultdict(list)
            for ch_id, para_id, surface, ruler in refs:
                refs_by_chapter[ch_id].append((para_id, surface, ruler))

            ref_parts = []
            for ch_id in sorted(refs_by_chapter.keys()):
                ch_title, ch_stem = chapter_names.get(ch_id, (ch_id, ch_id))
                ch_name = html_mod.escape(ch_title)
                ch_refs = refs_by_chapter[ch_id]
                ch_link = f'<a href="../chapters/{ch_stem}.html" class="chapter-ref-name">{ch_name}</a>'
                para_links = []
                for para_id, surface, ruler in ch_refs:
                    para_links.append(
                        f'<a href="../chapters/{ch_stem}.html#pn-{para_id}" class="para-ref">{para_id}</a>'
                    )
                ref_parts.append(f'{ch_link} {", ".join(para_links)}')

            lines.append('      ' + ' <span class="ref-sep">|</span> '.join(ref_parts))
            lines.append('    </div>')
            lines.append('  </div>')
        lines.append('</div>')

    lines.append('</div>')

    # Filter script
    lines.append('''<script>
document.addEventListener('DOMContentLoaded', function() {
    var input = document.getElementById('filter-input');
    var entries = document.querySelectorAll('.timeline-entry');
    var sections = document.querySelectorAll('.letter-section');
    var pinyinNav = document.querySelector('.pinyin-nav');

    input.addEventListener('input', function() {
        var query = this.value.trim().toLowerCase();

        if (!query) {
            for (var i = 0; i < entries.length; i++) entries[i].style.display = '';
            for (var i = 0; i < sections.length; i++) sections[i].style.display = '';
            if (pinyinNav) pinyinNav.style.display = '';
            return;
        }

        if (pinyinNav) pinyinNav.style.display = 'none';

        for (var i = 0; i < entries.length; i++) {
            var text = entries[i].textContent.toLowerCase();
            entries[i].style.display = text.indexOf(query) !== -1 ? '' : 'none';
        }

        for (var i = 0; i < sections.length; i++) {
            var visible = sections[i].querySelectorAll('.timeline-entry:not([style*="display: none"])');
            sections[i].style.display = visible.length > 0 ? '' : 'none';
        }
    });
});
</script>''')

    # Bottom navigation
    lines.append('<nav class="chapter-nav">')
    lines.append('    <a href="../index.html" class="nav-home">回到主页</a>')
    lines.append('    <a href="index.html" class="nav-next">实体索引</a>')
    lines.append('</nav>')

    lines.append('</body>')
    lines.append('</html>')

    # Write output
    os.makedirs(os.path.dirname(TIMELINE_FILE), exist_ok=True)
    with open(TIMELINE_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  Saved to {TIMELINE_FILE}")


# ============================================================
# Main
# ============================================================

def main():
    if '--extract-reigns' in sys.argv:
        # Phase 1 only
        reign_data = extract_reign_periods()
        save_reign_periods(reign_data)
        return

    # Full pipeline
    # Phase 1: Extract reign periods
    reign_data = extract_reign_periods()
    save_reign_periods(reign_data)

    # Phase 2: Disambiguate years
    year_map = disambiguate_years(reign_data)
    save_year_map(year_map)

    # Phase 3: Generate timeline.html
    generate_timeline(year_map, reign_data)


if __name__ == '__main__':
    main()
