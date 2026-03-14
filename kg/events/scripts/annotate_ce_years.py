#!/usr/bin/env python3
"""
annotate_ce_years.py - 为史记事件索引标注公元纪年

从事件索引文件中解析中国纪年时间字段，映射到公元纪年，
在 **时间** 行后追加公元年标注。

用法:
    python3 scripts/annotate_ce_years.py --dry-run          # 预览，不写文件
    python3 scripts/annotate_ce_years.py                     # 处理所有事件文件
    python3 scripts/annotate_ce_years.py --file 005          # 只处理指定章节
    python3 scripts/annotate_ce_years.py --verbose           # 显示每个事件的解析细节
"""

import os
import re
import json
import sys
from pathlib import Path
from collections import defaultdict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVENTS_DIR = _PROJECT_ROOT / "kg" / "events" / "data"
REIGN_FILE = _PROJECT_ROOT / "kg" / "chronology" / "data" / "reign_periods.json"
YEAR_CE_MAP_FILE = _PROJECT_ROOT / "kg" / "chronology" / "data" / "year_ce_map.json"

# ─── 中文数字工具 ───

CN_DIGITS = {
    '零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
}

def cn_to_int(s):
    """中文数字转整数。元->1, 十三->13, 二十->20, 四十八->48"""
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
    result += current
    return result if result > 0 else None


# ─── 章节默认 ruler（本纪/世家类，章节以某位君主为主体）───

CHAPTER_DEFAULT_RULER = {
    "001": None,       # 五帝本纪，多位帝王，无法默认
    "002": None,       # 夏本纪
    "003": None,       # 殷本纪
    "004": None,       # 周本纪
    "005": None,       # 秦本纪，多位秦公
    "006": "秦始皇",   # 秦始皇本纪
    "007": None,       # 项羽本纪
    "008": "高皇帝",   # 高祖本纪
    "009": "高后",     # 吕太后本纪
    "010": "孝文",     # 孝文本纪
    "011": "孝景",     # 孝景本纪
    "012": "孝武",     # 孝武本纪
}

# ─── 章节->国号映射 ───

CHAPTER_STATE = {
    # 本纪
    "001": "帝", "002": "夏", "003": "殷", "004": "周",
    "005": "秦", "006": "秦", "007": "秦", "008": "汉",
    "009": "汉", "010": "汉", "011": "汉", "012": "汉",
    # 表
    "013": "", "014": "", "015": "", "016": "",
    "017": "汉", "018": "汉", "019": "汉", "020": "汉",
    "021": "汉", "022": "汉",
    # 书
    "023": "", "024": "", "025": "", "026": "",
    "027": "", "028": "", "029": "", "030": "汉",
    # 世家
    "031": "吴", "032": "齐", "033": "鲁", "034": "燕",
    "035": "管蔡", "036": "陈", "037": "卫", "038": "宋",
    "039": "晋", "040": "楚", "041": "越", "042": "郑",
    "043": "赵", "044": "魏", "045": "韩", "046": "齐",
    "047": "鲁",   # 孔子世家（鲁国纪年）
    "048": "秦",   # 陈涉世家
    "049": "汉",   # 外戚世家
    "050": "楚",   # 楚元王世家
    "051": "汉",   # 荆燕世家
    "052": "汉",   # 齐悼惠王世家
    "053": "汉",   # 萧相国世家
    "054": "汉",   # 曹相国世家
    "055": "汉",   # 留侯世家
    "056": "汉",   # 陈丞相世家
    "057": "汉",   # 绛侯周勃世家
    "058": "汉",   # 梁孝王世家
    "059": "汉",   # 五宗世家
    "060": "汉",   # 三王世家
    # 列传
    "061": "汉", "062": "汉", "063": "汉", "064": "汉",
    "065": "汉", "066": "汉", "067": "汉", "068": "汉",
    "069": "", "070": "", "071": "秦", "072": "",
    "073": "秦", "074": "", "075": "", "076": "",
    "077": "", "078": "", "079": "", "080": "",
    "081": "赵", "082": "", "083": "赵", "084": "",
    "085": "秦", "086": "", "087": "秦", "088": "",
    "089": "汉", "090": "汉", "091": "汉", "092": "汉",
    "093": "汉", "094": "汉", "095": "汉", "096": "汉",
    "097": "汉", "098": "汉", "099": "汉", "100": "汉",
    "101": "汉", "102": "汉", "103": "汉", "104": "汉",
    "105": "汉", "106": "汉", "107": "汉", "108": "汉",
    "109": "汉", "110": "", "111": "汉", "112": "汉",
    "113": "汉", "114": "汉", "115": "汉", "116": "汉",
    "117": "汉", "118": "汉", "119": "汉", "120": "汉",
    "121": "汉", "122": "汉", "123": "汉", "124": "汉",
    "125": "汉", "126": "汉", "127": "汉", "128": "汉",
    "129": "汉", "130": "汉",
}

# 秦国君主短名->全名映射（秦本纪常用短名）
RULER_ALIASES_EXTRA = {
    "文公": ["秦文公", "鲁文公", "晋文公", "郑文公", "宋文公", "卫文公"],
    "武公": ["秦武公", "鲁武公", "晋武公", "郑武公", "宋武公"],
    "宁公": ["秦宁公"],
    "德公": ["秦德公"],
    "宣公": ["秦宣公", "鲁宣公", "晋宣公"],
    "成公": ["秦成公", "鲁成公", "晋成公"],
    "缪公": ["秦穆公", "秦缪公"],
    "穆公": ["秦穆公"],
    "康公": ["秦康公"],
    "共公": ["秦共公"],
    "桓公": ["秦桓公", "齐桓公", "鲁桓公"],
    "景公": ["秦景公", "齐景公", "晋景公"],
    "哀公": ["鲁哀公", "秦哀公"],
    "惠公": ["秦惠公", "晋惠公"],
    "悼公": ["秦悼公", "晋悼公"],
    "厉共公": ["秦厉共公"],
    "躁公": ["秦躁公"],
    "怀公": ["秦怀公"],
    "灵公": ["秦灵公", "晋灵公"],
    "简公": ["秦简公", "齐简公"],
    "献公": ["秦献公", "晋献公"],
    "孝公": ["秦孝公"],
    "惠文君": ["秦惠文王"],
    "惠文王": ["秦惠文王"],
    "惠王": ["秦惠文王", "魏惠王"],
    "武王": ["秦武王", "周武王"],
    "昭襄王": ["秦昭襄王"],
    "昭王": ["秦昭襄王", "楚昭王", "周昭王"],
    "孝文王": ["秦孝文王"],
    "庄襄王": ["秦庄襄王"],
    "始皇帝": ["秦始皇"],
    "秦王政": ["秦始皇"],
    "二世": ["秦二世"],
    "二世皇帝": ["秦二世"],
    # 汉
    "高祖": ["高皇帝"],
    "高帝": ["高皇帝"],
    "汉王": ["高皇帝"],
    "孝惠帝": ["孝惠"],
    "惠帝": ["孝惠"],
    "吕后": ["高后"],
    "吕太后": ["高后"],
    "孝文帝": ["孝文"],
    "文帝": ["孝文"],
    "孝景帝": ["孝景"],
    "景帝": ["孝景"],
    "今上": ["孝武"],
    "武帝": ["孝武"],
    # 周
    "平王": ["周平王"],
    "幽王": ["周幽王"],
    "襄王": ["周襄王"],
    "赧王": ["周赧王"],
    # 晋
    "重耳": ["晋文公"],
    "晋文公": ["晋文公"],
    "晋襄公": ["晋襄公"],
    "晋悼公": ["晋悼公"],
    # 赵
    "赵武灵王": ["赵武灵王"],
    "赵惠文王": ["赵惠文王"],
    "赵孝成王": ["赵孝成王"],
    # 楚
    "楚怀王": ["楚怀王"],
    "楚顷襄王": ["楚顷襄王"],
    # 齐
    "齐威王": ["齐威王"],
    "齐宣王": ["齐宣王"],
    "齐湣王": ["齐湣王"],
    # 魏
    "魏惠王": ["魏惠王"],
    "魏安釐王": ["魏安釐王"],
    # 燕
    "燕昭王": ["燕昭王"],
}


def load_data():
    """加载 reign_periods.json 和 year_ce_map.json"""
    with open(REIGN_FILE, 'r', encoding='utf-8') as f:
        reign_data = json.load(f)
    rulers = reign_data['rulers']
    eras = reign_data.get('eras', {})
    aliases = reign_data.get('aliases', {})

    year_ce_map = {}
    if YEAR_CE_MAP_FILE.exists():
        with open(YEAR_CE_MAP_FILE, 'r', encoding='utf-8') as f:
            year_ce_map = json.load(f)

    return rulers, eras, aliases, year_ce_map


def resolve_ruler(name, chapter_id, rulers, aliases):
    """将短名解析为 reign_periods 中的 key，返回 (ruler_key, ruler_info) 或 None"""
    if not name:
        return None

    # 清理标记符号（事件索引文件仍使用v1格式）
    name = re.sub(r'[@$&%]', '', name).strip()
    if not name:
        return None

    # 1. 直接匹配
    if name in rulers:
        return (name, rulers[name])

    # 2. aliases 表
    if name in aliases:
        canonical = aliases[name]
        if canonical in rulers:
            return (canonical, rulers[canonical])

    # 3. RULER_ALIASES_EXTRA
    if name in RULER_ALIASES_EXTRA:
        candidates = RULER_ALIASES_EXTRA[name]
        # 优先选同章节国号的
        state = CHAPTER_STATE.get(chapter_id, "")
        for c in candidates:
            if c in rulers:
                if state and rulers[c].get('state', '') == state:
                    return (c, rulers[c])
        # 无国号匹配就取第一个有效的
        for c in candidates:
            if c in rulers:
                return (c, rulers[c])

    # 4. 加国号前缀
    state = CHAPTER_STATE.get(chapter_id, "")
    if state:
        prefixed = state + name
        if prefixed in rulers:
            return (prefixed, rulers[prefixed])

    # 5. 模糊：缪=穆
    alt_name = name.replace('缪', '穆')
    if alt_name != name and alt_name in rulers:
        return (alt_name, rulers[alt_name])

    return None


def parse_time_field(time_str):
    """解析时间字段，返回 list of (ruler_name, year_num, era_name)
    可能返回多个结果（范围）
    """
    if not time_str or time_str.strip() == '-':
        return []

    results = []

    # 去除已有的公元标注（防止重复标注）
    time_str = re.sub(r'（公元[前]?\d+年.*?）', '', time_str).strip()

    # 事件索引文件仍使用v1格式（@人名@、%时间%、&氏族& 等）
    # 格式1: &年号&%X年%
    era_match = re.search(r'&([^&]+)&.*?%([^%]*?年[^%]*)%', time_str)
    if era_match:
        era_name = era_match.group(1)
        year_text = era_match.group(2)
        year_cn = re.search(r'([元一二三四五六七八九十百]+)年', year_text)
        if year_cn:
            year_num = cn_to_int(year_cn.group(1))
            results.append((None, year_num, era_name))
            return results

    # 格式2: 更元%X年%
    geng_match = re.search(r'更元.*?%([^%]*?年[^%]*)%', time_str)
    if geng_match:
        year_text = geng_match.group(1)
        year_cn = re.search(r'([元一二三四五六七八九十百]+)年', year_text)
        if year_cn:
            year_num = cn_to_int(year_cn.group(1))
            results.append((None, year_num, '更元'))
            return results

    # 格式3: %汉X年% 或 %二世X年%
    han_match = re.search(r'%汉([元一二三四五六七八九十百]+)年', time_str)
    if han_match:
        year_num = cn_to_int(han_match.group(1))
        results.append(('高皇帝', year_num, None))
        return results

    ershi_match = re.search(r'%二世([元一二三四五六七八九十百]+)年', time_str)
    if ershi_match:
        year_num = cn_to_int(ershi_match.group(1))
        results.append(('秦二世', year_num, None))
        return results

    # 格式4: @ruler@%X年% 或 $ruler$%X年%
    ruler_match = re.search(r'[@$]([^@$]+)[@$].*?%([^%]*?年[^%]*)%', time_str)
    if ruler_match:
        ruler_name = ruler_match.group(1)
        year_text = ruler_match.group(2)
        year_cn = re.search(r'([元一二三四五六七八九十百]+)年', year_text)
        if year_cn:
            year_num = cn_to_int(year_cn.group(1))
            results.append((ruler_name, year_num, None))

            # 检查是否有范围（至%X年%）
            range_match = re.search(r'至.*?%([^%]*?年[^%]*)%', time_str)
            if range_match:
                year_text2 = range_match.group(1)
                year_cn2 = re.search(r'([元一二三四五六七八九十百]+)年', year_text2)
                if year_cn2:
                    year_num2 = cn_to_int(year_cn2.group(1))
                    results.append((ruler_name, year_num2, None))
            return results

    # 格式5a: %prefix+X年...% （如 %高祖十一年春%、%建元六年%、%秦昭王四十八年%）
    inline_match = re.search(
        r'%([^%]*?)([^\d%@$&一二三四五六七八九十百]{2,}?)([元一二三四五六七八九十百]+)年',
        time_str
    )
    if inline_match:
        prefix = inline_match.group(2)
        year_cn = inline_match.group(3)
        year_num = cn_to_int(year_cn)
        if year_num and len(prefix) >= 2:
            results.append((prefix, year_num, prefix))
            return results

    # 格式5: 纯 %X年% （无ruler标注）
    year_matches = re.findall(r'%([^%]*?([元一二三四五六七八九十百]+)年[^%]*)%', time_str)
    if year_matches:
        # 取第一个（主年份）
        year_cn_str = year_matches[0][1]
        year_num = cn_to_int(year_cn_str)
        if year_num:
            results.append((None, year_num, None))
        # 如果有"至"连接的第二个年份
        if len(year_matches) > 1 and '至' in time_str:
            year_cn_str2 = year_matches[-1][1]
            year_num2 = cn_to_int(year_cn_str2)
            if year_num2:
                results.append((None, year_num2, None))
        return results

    # 格式6: 描述性文本中尝试提取（如"秦惠王八年"）
    desc_match = re.search(r'([^\s@$%&]+?)([元一二三四五六七八九十百]+)年', time_str)
    if desc_match:
        ruler_name = desc_match.group(1)
        year_num = cn_to_int(desc_match.group(2))
        if year_num and len(ruler_name) >= 2:
            results.append((ruler_name, year_num, None))
            return results

    # 格式7: @ruler@卒 / @ruler@死后 -> 取末年
    death_match = re.search(r'[@$]([^@$]+)[@$].*?[卒崩死]', time_str)
    if death_match:
        results.append((death_match.group(1), -1, None))  # -1 表示取末年
        return results

    return results


def compute_ce_year(parsed_list, chapter_id, para_id, rulers, eras, aliases, year_ce_map):
    """计算公元年。返回 (ce_year, ce_year_end) 或 (None, None)
    ce_year 为正数表示公元后，负数表示公元前
    """
    if not parsed_list:
        return None, None

    ce_years = []

    for ruler_name, year_num, era_name in parsed_list:
        ce = None

        # 方法1: 有明确 ruler 时，优先用 reign_periods 直接计算
        if ruler_name and year_num and year_num > 0:
            resolved = resolve_ruler(ruler_name, chapter_id, rulers, aliases)
            if resolved:
                _, info = resolved
                ce = -(info['start_bce'] - (year_num - 1))
                ce_years.append(ce)
                continue
            # ruler 末年
        if ruler_name and year_num == -1:
            resolved = resolve_ruler(ruler_name, chapter_id, rulers, aliases)
            if resolved:
                _, info = resolved
                ce = -info['end_bce']
                ce_years.append(ce)
                continue

        # 方法2: 年号（era_name 可能同时是 ruler 名或年号名）
        if era_name:
            if era_name == '更元':
                if year_num and year_num > 0:
                    ce = -(324 - (year_num - 1))
                    ce_years.append(ce)
                    continue
            elif era_name in eras:
                era_info = eras[era_name]
                if year_num and year_num > 0:
                    ce = -(era_info['start_bce'] - (year_num - 1))
                    ce_years.append(ce)
                    continue
            else:
                # era_name 可能实际上是 ruler 名（如 "高祖", "秦昭王"）
                resolved = resolve_ruler(era_name, chapter_id, rulers, aliases)
                if resolved:
                    _, info = resolved
                    if year_num and year_num > 0:
                        ce = -(info['start_bce'] - (year_num - 1))
                        ce_years.append(ce)
                        continue

        # 方法3: 查 year_ce_map（用于无 ruler 的纯年份）
        if chapter_id in year_ce_map and para_id and year_num and year_num > 0:
            para_data = year_ce_map[chapter_id].get(para_id, {})
            for yk, yv in para_data.items():
                if 'ce_year' in yv:
                    yk_cn = re.search(r'([元一二三四五六七八九十百]+)年', yk + '年')
                    if yk_cn:
                        yk_num = cn_to_int(yk_cn.group(1))
                        if yk_num == year_num:
                            ce = yv['ce_year']
                            break
                if 'ruler_key' in yv and not ce:
                    rk = yv['ruler_key']
                    rk_match = re.match(r'(.+?)([元一二三四五六七八九十百]+年)$', rk)
                    if rk_match:
                        rk_ruler = rk_match.group(1)
                        rk_year_cn = re.search(r'([元一二三四五六七八九十百]+)年', rk_match.group(2))
                        if rk_year_cn and cn_to_int(rk_year_cn.group(1)) == year_num:
                            resolved = resolve_ruler(rk_ruler, chapter_id, rulers, aliases)
                            if resolved:
                                _, info = resolved
                                ce = -(info['start_bce'] - (year_num - 1))
                                break
            if ce is not None:
                ce_years.append(ce)
                continue

        # 方法4: 无 ruler 的纯年份 -> 搜索最近段落
        if year_num and year_num > 0 and chapter_id in year_ce_map:
            # 搜索该章节所有段落，找匹配的年份
            best_para = None
            best_dist = float('inf')
            para_num = _para_to_float(para_id) if para_id else None

            for p_id, p_data in year_ce_map[chapter_id].items():
                for yk, yv in p_data.items():
                    yk_cn = re.search(r'([元一二三四五六七八九十百]+)年', yk + '年')
                    if yk_cn and cn_to_int(yk_cn.group(1)) == year_num:
                        if 'ce_year' in yv:
                            p_num = _para_to_float(p_id)
                            if para_num is not None and p_num is not None:
                                dist = abs(p_num - para_num)
                                if dist < best_dist:
                                    best_dist = dist
                                    best_para = yv['ce_year']
                            elif best_para is None:
                                best_para = yv['ce_year']
                        elif 'ruler_key' in yv:
                            rk = yv['ruler_key']
                            rk_match = re.match(r'(.+?)([元一二三四五六七八九十百]+年)$', rk)
                            if rk_match:
                                rk_ruler = rk_match.group(1)
                                resolved = resolve_ruler(rk_ruler, chapter_id, rulers, aliases)
                                if resolved:
                                    _, info = resolved
                                    candidate = -(info['start_bce'] - (year_num - 1))
                                    p_num = _para_to_float(p_id)
                                    if para_num is not None and p_num is not None:
                                        dist = abs(p_num - para_num)
                                        if dist < best_dist:
                                            best_dist = dist
                                            best_para = candidate
                                    elif best_para is None:
                                        best_para = candidate

            if best_para is not None and best_dist < 5:  # 段落距离不超过5
                ce_years.append(best_para)
                continue

    if not ce_years:
        return None, None

    if len(ce_years) == 1:
        return ce_years[0], None
    elif len(ce_years) >= 2:
        return ce_years[0], ce_years[-1]

    return None, None


def _para_to_float(para_id):
    """段落ID转浮点数，用于距离计算"""
    if not para_id:
        return None
    try:
        # "7.5" -> 7.5, "24" -> 24.0, "24.1" -> 24.1
        return float(para_id)
    except (ValueError, TypeError):
        # "47-47.1" -> 47.0
        m = re.match(r'(\d+)', str(para_id))
        if m:
            return float(m.group(1))
        return None


def format_ce_annotation(ce_year, ce_year_end=None):
    """格式化公元年标注"""
    def fmt(y):
        if y is None:
            return None
        if y <= 0:
            return f"前{-y}年"
        else:
            return f"{y}年"

    s = fmt(ce_year)
    if s is None:
        return None

    if ce_year_end is not None:
        e = fmt(ce_year_end)
        if e and e != s:
            return f"（公元{s}-{e}）"

    return f"（公元{s}）"


def extract_para_id(lines, start_idx):
    """从事件详细记录中提取段落位置"""
    for i in range(start_idx, min(start_idx + 12, len(lines))):
        m = re.search(r'\*\*段落位置\*\*.*?\[(\d+(?:\.\d+)?)', lines[i])
        if m:
            return m.group(1)
    return None


def extract_people(lines, start_idx):
    """从事件详细记录中提取主要人物"""
    for i in range(start_idx, min(start_idx + 12, len(lines))):
        if '**主要人物**' in lines[i]:
            # 提取 @name@ 标注的人名
            names = re.findall(r'@([^@]+)@', lines[i])
            return names
    return []


def process_event_file(filepath, rulers, eras, aliases, year_ce_map,
                       dry_run=False, verbose=False):
    """处理单个事件文件，标注公元纪年

    Returns: (annotated_count, skipped_count, failed_count)
    """
    chapter_id = filepath.name.split('_')[0]

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    annotated = 0
    skipped = 0
    failed = 0
    failed_details = []

    # 收集 event_id -> ce_annotation 用于回填概览表
    event_annotations = {}

    # 上下文追踪：记住最近成功解析的 ruler，用于推断纯年份的 ruler
    last_ruler_key = None   # reign_periods 中的 key
    last_ruler_info = None  # ruler info dict

    # 初始化默认 ruler（如孝文本纪默认为孝文帝）
    default_ruler = CHAPTER_DEFAULT_RULER.get(chapter_id)
    if default_ruler:
        resolved = resolve_ruler(default_ruler, chapter_id, rulers, aliases)
        if resolved:
            last_ruler_key, last_ruler_info = resolved

    # ── 第一遍：处理详细事件记录 ──
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
        if time_match:
            time_str = time_match.group(1).strip()

            # 跳过已标注的
            if '公元' in time_str:
                existing = re.search(r'（公元[^）]+）', time_str)
                if existing and current_event_id:
                    event_annotations[current_event_id] = existing.group(0)
                skipped += 1
                i += 1
                continue

            if time_str == '-' or not time_str:
                skipped += 1
                i += 1
                continue

            # 提取段落位置
            para_id = extract_para_id(lines, i)

            # 解析时间
            parsed = parse_time_field(time_str)
            if not parsed:
                # 区分：无年份信息（月份、帝号+时）vs 真正的解析失败
                has_year_info = bool(re.search(r'[元一二三四五六七八九十百]+年', time_str))
                if has_year_info:
                    failed += 1
                    if verbose:
                        failed_details.append(f"  [解析失败] {current_event_id}: {time_str}")
                else:
                    skipped += 1  # 无年份信息，跳过
                i += 1
                continue

            # 计算公元年
            ce_year, ce_year_end = compute_ce_year(
                parsed, chapter_id, para_id,
                rulers, eras, aliases, year_ce_map
            )

            # 如果有明确的 @ruler@ 标注（非内联），更新上下文
            ruler_name = parsed[0][0] if parsed else None
            has_explicit_ruler = ruler_name and re.search(r'[@$]', time_str)
            if has_explicit_ruler and ce_year is not None:
                resolved = resolve_ruler(ruler_name, chapter_id, rulers, aliases)
                if resolved:
                    last_ruler_key, last_ruler_info = resolved

            # 如果失败且是纯年份，尝试用上下文 ruler
            if ce_year is None and parsed and not parsed[0][0] and not parsed[0][2]:
                year_num = parsed[0][1]
                if last_ruler_info and year_num and year_num > 0:
                    candidate_ce = -(last_ruler_info['start_bce'] - (year_num - 1))
                    ruler_end_ce = -last_ruler_info['end_bce']
                    if candidate_ce <= ruler_end_ce + 2:
                        ce_year = candidate_ce
                        if len(parsed) > 1 and not parsed[-1][0] and not parsed[-1][2]:
                            y2 = parsed[-1][1]
                            if y2 and y2 > 0:
                                ce_year_end = -(last_ruler_info['start_bce'] - (y2 - 1))

            # 如果仍然失败，尝试从主要人物推断 ruler
            if ce_year is None and parsed and not parsed[0][0] and not parsed[0][2]:
                year_num = parsed[0][1]
                if year_num and year_num > 0:
                    people = extract_people(lines, i)
                    for person in people:
                        resolved = resolve_ruler(person, chapter_id, rulers, aliases)
                        if resolved:
                            rk, info = resolved
                            candidate_ce = -(info['start_bce'] - (year_num - 1))
                            ruler_end_ce = -info['end_bce']
                            if candidate_ce <= ruler_end_ce + 2:
                                ce_year = candidate_ce
                                last_ruler_key, last_ruler_info = rk, info
                                if len(parsed) > 1 and not parsed[-1][0] and not parsed[-1][2]:
                                    y2 = parsed[-1][1]
                                    if y2 and y2 > 0:
                                        ce_year_end = -(info['start_bce'] - (y2 - 1))
                                break

            if ce_year is not None:
                annotation = format_ce_annotation(ce_year, ce_year_end)
                new_line = f"- **时间**: {time_str} {annotation}\n"
                lines[i] = new_line
                annotated += 1
                if current_event_id:
                    event_annotations[current_event_id] = annotation
                if verbose:
                    print(f"  [OK] {current_event_id}: {time_str} -> {annotation}")
            else:
                failed += 1
                if verbose:
                    failed_details.append(
                        f"  [映射失败] {current_event_id}: {time_str} "
                        f"(parsed={parsed}, para={para_id})"
                    )

        i += 1

    # ── 第二遍：回填概览表的时间列 ──
    if event_annotations:
        i = 0
        while i < len(lines):
            line = lines[i]
            # 匹配概览表行: | 005-001 | ... | ... | 时间 | ...
            table_match = re.match(r'^(\| \d{3}-\d{3} .*)$', line)
            if table_match:
                row = line
                # 提取 event_id
                eid_match = re.search(r'(\d{3}-\d{3})', row)
                if eid_match:
                    eid = eid_match.group(1)
                    if eid in event_annotations and '公元' not in row:
                        # 找到时间列（第4列）并追加标注
                        cols = row.split('|')
                        if len(cols) >= 5:  # |  | ID | name | type | time | ...
                            time_col = cols[4].strip()
                            if time_col != '-':
                                cols[4] = f" {time_col} {event_annotations[eid]} "
                                lines[i] = '|'.join(cols)
            i += 1

    # 写回文件
    if not dry_run and annotated > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    if verbose and failed_details:
        for d in failed_details:
            print(d)

    return annotated, skipped, failed


def main():
    import argparse
    parser = argparse.ArgumentParser(description="为事件索引标注公元纪年")
    parser.add_argument("--dry-run", action="store_true", help="预览，不写文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细解析信息")
    parser.add_argument("--file", help="只处理指定章节号（如 005）")
    parser.add_argument("--show-failures", action="store_true", help="只显示映射失败的事件")
    args = parser.parse_args()

    rulers, eras, aliases, year_ce_map = load_data()
    print(f"已加载: {len(rulers)} 个君主, {len(eras)} 个年号, "
          f"{len(year_ce_map)} 章年份映射")

    # 收集事件文件
    if args.file:
        files = sorted(EVENTS_DIR.glob(f"{args.file}_*_事件索引.md"))
    else:
        files = sorted(EVENTS_DIR.glob("*_事件索引.md"))

    if not files:
        print("未找到事件文件")
        return 1

    total_annotated = 0
    total_skipped = 0
    total_failed = 0

    for f in files:
        a, s, fail = process_event_file(
            f, rulers, eras, aliases, year_ce_map,
            dry_run=args.dry_run,
            verbose=args.verbose or args.show_failures
        )
        if a > 0 or fail > 0:
            status = "预览" if args.dry_run else "已标注"
            print(f"  {f.name}: {status} {a}, 跳过 {s}, 失败 {fail}")
        total_annotated += a
        total_skipped += s
        total_failed += fail

    print(f"\n{'='*50}")
    print(f"  总计: {len(files)} 个文件")
    print(f"  标注: {total_annotated}")
    print(f"  跳过: {total_skipped} (无时间/已标注)")
    print(f"  失败: {total_failed} (无法映射)")
    pct = total_annotated / (total_annotated + total_failed) * 100 if (total_annotated + total_failed) > 0 else 0
    print(f"  成功率: {pct:.1f}%")
    if args.dry_run:
        print(f"  (dry-run 模式，未写入文件)")
    print(f"{'='*50}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
