#!/usr/bin/env python3
"""
语义消歧脚本：分析歧义短名，生成 disambiguation_map.json 元数据

不修改原始 tagged.md 文件。而是输出章节级消歧映射表，
供 render_shiji_html.py 在生成HTML时使用（显示原文，链接指向消歧后的实体）。

Heuristics used (in priority order):
1. Preceding state prefix: &秦&@昭王@ -> 秦昭王
2. Nearby state mention: Look at &state& and @StateX@ tags within +/-80 chars.
3. Chapter primary state: Use the chapter's known primary state/subject.
4. Co-occurrence: If full forms of a short name co-occur in the chapter.

输出格式（disambiguation_map.json）：
{
  "004": {"武王": "周武王", "成王": "周成王", ...},
  "005": {"昭王": "秦昭王", "惠王": "秦惠王", ...},
  ...
}
"""
import os
import re
import json
import sys
from collections import defaultdict, Counter

CHAPTER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chapter_md')
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'disambiguation_map.json')

# Maximum length for a "full name" - anything longer is likely a regex false positive
MAX_FULLNAME_LEN = 8

# Characters that should NOT appear in a valid person name
INVALID_NAME_CHARS = set('$?^*!~=&%#><[](){}|/\\')

# --- Chapter -> primary state mapping ---
CHAPTER_STATE = {
    '001': None, '002': '夏', '003': '殷', '004': '周',
    '005': '秦', '006': '秦', '007': '楚', '008': '汉',
    '009': '汉', '010': '汉', '011': '汉', '012': '汉',
    '013': None, '014': None, '015': None, '016': None,
    '017': '汉', '018': '汉', '019': '汉', '020': '汉',
    '021': '汉', '022': '汉',
    '023': None, '024': None, '025': None, '026': None,
    '027': None, '028': None, '029': None, '030': None,
    '031': '吴', '032': '齐', '033': '鲁', '034': '燕',
    '035': None, '036': '陈', '037': '卫', '038': '宋',
    '039': '晋', '040': '楚', '041': '越', '042': '郑',
    '043': '赵', '044': '魏', '045': '韩', '046': '齐',
    '047': '鲁', '048': None, '049': '汉', '050': '楚',
    '051': None, '052': '齐', '053': '汉', '054': '汉',
    '055': '汉', '056': '汉', '057': '汉', '058': '汉',
    '059': '汉', '060': '汉',
    '061': None, '062': '齐', '063': None, '064': '齐',
    '065': None, '066': '吴', '067': '鲁', '068': '秦',
    '069': None, '070': '秦', '071': '秦', '072': '秦',
    '073': '秦', '074': None, '075': '齐', '076': '赵',
    '077': '魏', '078': '楚', '079': '秦', '080': '燕',
    '081': '赵', '082': '齐', '083': '齐', '084': '楚',
    '085': '秦', '086': None, '087': '秦', '088': '秦',
    '089': None, '090': None, '091': '汉', '092': '汉',
    '093': '汉', '094': '齐', '095': '汉', '096': '汉',
    '097': '汉', '098': '汉', '099': '汉', '100': '汉',
    '101': '汉', '102': '汉', '103': '汉', '104': '汉',
    '105': None, '106': '汉', '107': '汉', '108': '汉',
    '109': '汉', '110': None, '111': '汉', '112': '汉',
    '113': None, '114': None, '115': None, '116': None,
    '117': '汉', '118': '汉', '119': None, '120': '汉',
    '121': '汉', '122': '汉', '123': '汉', '124': '汉',
    '125': '汉', '126': None, '127': None, '128': None,
    '129': None, '130': None,
}

# --- All known states ---
ALL_STATES_SET = set([
    '秦', '齐', '楚', '赵', '魏', '韩', '燕', '晋', '鲁', '郑',
    '卫', '宋', '陈', '蔡', '吴', '越', '周', '曹', '杞', '许',
    '邾', '滕', '薛', '莒', '夏', '殷', '商', '汉',
])

# --- Known disambiguation rules: (short_name, state) -> full_name ---
RULER_DB = {
    # == 王 (king) titles ==
    ('武王', '周'): '周武王', ('武王', '秦'): '秦武王',
    ('武王', '楚'): '楚武王', ('武王', '赵'): '赵武灵王',
    ('文王', '周'): '周文王', ('文王', '楚'): '楚文王',
    ('文王', '赵'): '赵惠文王', ('文王', '魏'): '魏文王',
    ('昭王', '秦'): '秦昭王', ('昭王', '燕'): '燕昭王',
    ('昭王', '楚'): '楚昭王', ('昭王', '周'): '周昭王',
    ('昭王', '赵'): '赵昭王',
    ('惠王', '秦'): '秦惠王', ('惠王', '魏'): '魏惠王',
    ('惠王', '韩'): '韩惠王', ('惠王', '燕'): '燕惠王',
    ('惠王', '楚'): '楚惠王', ('惠王', '赵'): '赵惠文王',
    ('襄王', '秦'): '秦昭襄王', ('襄王', '楚'): '楚顷襄王',
    ('襄王', '周'): '周襄王', ('襄王', '赵'): '赵悼襄王',
    ('襄王', '魏'): '魏襄王', ('襄王', '韩'): '韩襄王',
    ('成王', '周'): '周成王', ('成王', '赵'): '赵成王',
    ('成王', '楚'): '楚成王',
    ('威王', '齐'): '齐威王', ('威王', '楚'): '楚威王',
    ('宣王', '齐'): '齐宣王', ('宣王', '周'): '周宣王',
    ('宣王', '韩'): '韩宣惠王',
    ('闵王', '齐'): '齐闵王', ('湣王', '齐'): '齐湣王',
    ('怀王', '楚'): '楚怀王',
    ('悼王', '楚'): '楚悼王', ('悼王', '周'): '周悼王',
    ('考王', '周'): '周考王', ('康王', '周'): '周康王',
    ('厉王', '周'): '周厉王', ('幽王', '周'): '周幽王',
    ('平王', '周'): '周平王', ('桓王', '周'): '周桓王',
    ('赧王', '周'): '周赧王', ('安王', '周'): '周安王',
    ('烈王', '周'): '周烈王', ('显王', '周'): '周显王',
    ('哀王', '齐'): '齐哀王',
    ('元王', '楚'): '楚元王', ('元王', '周'): '周元王',
    ('灵王', '周'): '周灵王', ('灵王', '楚'): '楚灵王',
    ('景王', '周'): '周景王', ('敬王', '周'): '周敬王',
    ('定王', '周'): '周定王', ('简王', '周'): '周简王',
    ('匡王', '周'): '周匡王',

    # == 公 (duke) titles ==
    ('桓公', '齐'): '齐桓公', ('桓公', '宋'): '宋桓公',
    ('桓公', '鲁'): '鲁桓公', ('桓公', '晋'): '晋桓公',
    ('桓公', '郑'): '郑桓公', ('桓公', '卫'): '卫桓公',
    ('桓公', '陈'): '陈桓公', ('桓公', '曹'): '曹桓公',
    ('桓公', '燕'): '燕桓公', ('桓公', '蔡'): '蔡桓公',

    ('文公', '晋'): '晋文公', ('文公', '秦'): '秦文公',
    ('文公', '卫'): '卫文公', ('文公', '鲁'): '鲁文公',
    ('文公', '郑'): '郑文公', ('文公', '陈'): '陈文公',
    ('文公', '宋'): '宋文公', ('文公', '曹'): '曹文公',
    ('文公', '蔡'): '蔡文公',

    ('襄公', '秦'): '秦襄公', ('襄公', '宋'): '宋襄公',
    ('襄公', '齐'): '齐襄公', ('襄公', '晋'): '晋襄公',
    ('襄公', '鲁'): '鲁襄公', ('襄公', '郑'): '郑襄公',

    ('景公', '晋'): '晋景公', ('景公', '齐'): '齐景公',
    ('景公', '宋'): '宋景公',

    ('庄公', '鲁'): '鲁庄公', ('庄公', '齐'): '齐庄公',
    ('庄公', '郑'): '郑庄公', ('庄公', '燕'): '燕庄公',
    ('庄公', '陈'): '陈庄公', ('庄公', '卫'): '卫庄公',
    ('庄公', '宋'): '宋庄公', ('庄公', '晋'): '晋庄公',
    ('庄公', '蔡'): '蔡庄公', ('庄公', '曹'): '曹庄公',

    ('灵公', '卫'): '卫灵公', ('灵公', '晋'): '晋灵公',
    ('灵公', '齐'): '齐灵公', ('灵公', '秦'): '秦灵公',
    ('灵公', '陈'): '陈灵公', ('灵公', '郑'): '郑灵公',

    ('惠公', '晋'): '晋惠公', ('惠公', '鲁'): '鲁惠公',
    ('惠公', '卫'): '卫惠公', ('惠公', '齐'): '齐惠公',
    ('惠公', '郑'): '郑惠公', ('惠公', '秦'): '秦惠公',
    ('惠公', '宋'): '宋惠公', ('惠公', '陈'): '陈惠公',

    ('献公', '晋'): '晋献公', ('献公', '秦'): '秦献公',
    ('献公', '鲁'): '鲁献公', ('献公', '卫'): '卫献公',
    ('献公', '郑'): '郑献公',

    ('哀公', '鲁'): '鲁哀公', ('哀公', '齐'): '齐哀公',
    ('哀公', '陈'): '陈哀公', ('哀公', '郑'): '郑哀公',

    ('穆公', '秦'): '秦穆公', ('穆公', '鲁'): '鲁穆公',
    ('穆公', '卫'): '卫穆公', ('穆公', '郑'): '郑穆公',
    ('穆公', '宋'): '宋穆公', ('穆公', '陈'): '陈穆公',
    ('穆公', '曹'): '曹穆公',

    ('缪公', '秦'): '秦缪公',

    ('宣公', '鲁'): '鲁宣公', ('宣公', '齐'): '齐宣公',
    ('宣公', '卫'): '卫宣公', ('宣公', '陈'): '陈宣公',

    ('成公', '晋'): '晋成公', ('成公', '鲁'): '鲁成公',
    ('成公', '卫'): '卫成公', ('成公', '宋'): '宋成公',
    ('成公', '郑'): '郑成公',

    ('定公', '鲁'): '鲁定公', ('定公', '晋'): '晋定公',
    ('定公', '齐'): '齐定公', ('定公', '宋'): '宋定公',
    ('定公', '卫'): '卫定公',

    ('昭公', '鲁'): '鲁昭公', ('昭公', '齐'): '齐昭公',
    ('昭公', '卫'): '卫昭公', ('昭公', '晋'): '晋昭公',
    ('昭公', '陈'): '陈昭公', ('昭公', '郑'): '郑昭公',
    ('昭公', '蔡'): '蔡昭公',

    ('闵公', '鲁'): '鲁闵公', ('闵公', '齐'): '齐闵公',
    ('隐公', '鲁'): '鲁隐公',
    ('僖公', '鲁'): '鲁僖公', ('僖公', '晋'): '晋僖公',

    ('孝公', '秦'): '秦孝公', ('孝公', '齐'): '齐孝公',
    ('孝公', '鲁'): '鲁孝公', ('孝公', '楚'): '楚孝公',

    ('武公', '秦'): '秦武公', ('武公', '晋'): '晋武公',
    ('武公', '卫'): '卫武公', ('武公', '郑'): '郑武公',
    ('武公', '宋'): '宋武公', ('武公', '曹'): '曹武公',

    ('简公', '齐'): '齐简公', ('简公', '郑'): '郑简公',
    ('简公', '鲁'): '鲁简公',

    ('厉公', '晋'): '晋厉公', ('厉公', '齐'): '齐厉公',
    ('厉公', '郑'): '郑厉公', ('厉公', '秦'): '秦厉公',
    ('厉公', '陈'): '陈厉公',

    ('悼公', '晋'): '晋悼公', ('悼公', '鲁'): '鲁悼公',
    ('悼公', '郑'): '郑悼公',

    ('出公', '晋'): '晋出公', ('出公', '秦'): '秦出公',
    ('平公', '晋'): '晋平公', ('平公', '宋'): '宋平公',
    ('懿公', '齐'): '齐懿公', ('懿公', '卫'): '卫懿公',
    ('釐公', '鲁'): '鲁釐公', ('釐公', '齐'): '齐釐公',
    ('釐公', '卫'): '卫釐公',
    ('顷公', '齐'): '齐顷公', ('顷公', '鲁'): '鲁顷公',
    ('共公', '宋'): '宋共公',
    ('康公', '齐'): '齐康公', ('康公', '晋'): '晋康公',
    ('康公', '秦'): '秦康公',
    ('幽公', '晋'): '晋幽公', ('幽公', '郑'): '郑幽公',
    ('怀公', '晋'): '晋怀公', ('怀公', '秦'): '秦怀公',
    ('烈公', '晋'): '晋烈公',
    ('穆侯', '晋'): '晋穆侯',

    # == 侯 (marquis) titles ==
    ('文侯', '魏'): '魏文侯', ('文侯', '韩'): '韩文侯',
    ('文侯', '晋'): '晋文侯',
    ('武侯', '魏'): '魏武侯',
    ('哀侯', '韩'): '韩哀侯', ('哀侯', '晋'): '晋哀侯',
    ('懿侯', '韩'): '韩懿侯', ('懿侯', '赵'): '赵懿侯',
    ('昭侯', '韩'): '韩昭侯', ('昭侯', '蔡'): '蔡昭侯',
    ('桓侯', '韩'): '韩桓侯', ('桓侯', '齐'): '齐桓侯',
    ('景侯', '韩'): '韩景侯',
    ('列侯', '韩'): '韩列侯',
    ('宣侯', '韩'): '韩宣侯',
    ('襄侯', '韩'): '韩襄侯',
    ('成侯', '赵'): '赵成侯', ('成侯', '韩'): '韩成侯',
    ('敬侯', '赵'): '赵敬侯',
    ('烈侯', '赵'): '赵烈侯', ('烈侯', '韩'): '韩烈侯',
    ('献侯', '赵'): '赵献侯', ('献侯', '韩'): '韩献侯',
    ('肃侯', '赵'): '赵肃侯', ('肃侯', '韩'): '韩肃侯',
    ('釐侯', '韩'): '韩釐侯', ('釐侯', '赵'): '赵釐侯',
    ('顷侯', '韩'): '韩顷侯',
    # == Additional entries ==
    ('惠王', '周'): '周惠王', ('庄王', '周'): '周庄王',
    ('共王', '周'): '周共王', ('穆王', '周'): '周穆王',
    ('懿王', '周'): '周懿王', ('哀王', '周'): '周哀王',
    ('思王', '周'): '周思王', ('釐王', '周'): '周釐王',
    ('庄公', '秦'): '秦庄公', ('景公', '秦'): '秦景公',
    ('简公', '秦'): '秦简公', ('悼公', '秦'): '秦悼公',
    ('桓公', '秦'): '秦桓公', ('共公', '秦'): '秦共公',
    ('哀公', '秦'): '秦哀公',
    ('献公', '齐'): '齐献公', ('悼公', '齐'): '齐悼公',
    ('平公', '齐'): '齐平公', ('文公', '齐'): '齐文公',
    ('昭王', '魏'): '魏昭王',
    ('灵公', '赵'): '赵灵公', ('景公', '赵'): '赵景公',
    ('襄公', '赵'): '赵襄公', ('武公', '赵'): '赵武公',
    ('成公', '赵'): '赵成公',
    ('悼公', '魏'): '魏悼公', ('哀王', '魏'): '魏哀王',
    ('文公', '燕'): '燕文公', ('惠公', '燕'): '燕惠公',
    ('献公', '燕'): '燕献公', ('简公', '燕'): '燕简公',
    ('襄公', '燕'): '燕襄公', ('平公', '燕'): '燕平公',
    ('釐侯', '燕'): '燕釐侯', ('顷侯', '燕'): '燕顷侯',
    ('平公', '鲁'): '鲁平公',
    ('懿公', '鲁'): '鲁懿公', ('幽公', '鲁'): '鲁幽公',
    ('武公', '鲁'): '鲁武公', ('厉公', '鲁'): '鲁厉公',
    ('景公', '韩'): '韩景公',
}

# --- Names that should NOT be disambiguated ---
SKIP_NAMES = {
    '孝文帝', '孝景帝', '孝武帝', '孝惠帝', '高皇帝',
    '黄帝', '炎帝', '吕后', '高后',
    '齐桓公', '齐桓侯',
    '秦昭王', '秦惠王', '秦孝公', '秦献公', '秦德公', '秦武王',
    '秦襄公', '秦庄襄王', '秦始皇帝',
    '齐威王', '齐宣王', '齐湣王', '齐闵王', '齐景公',
    '晋文公', '晋定公', '晋献公', '晋景公', '晋出公', '晋平公', '晋惠公',
    '楚怀王', '楚庄王', '楚顷襄王', '楚昭王',
    '燕昭王', '燕惠王', '魏惠王', '魏文侯', '魏安釐王',
    '赵武灵王', '赵惠文王', '周武王', '周襄王',
    '鲁隐公', '鲁桓公', '鲁庄公', '鲁湣公', '卫灵公', '韩懿侯',
    '浑邪王',
    '陈皇后', '窦皇后', '王太后', '窦太后', '薄太后', '鲁元太后',
    '梁孝王', '济北王', '济南王', '胶东王', '胶西王', '菑川王', '淮南王',
    '陶硃公', '穰侯', '申侯',
    '平津侯', '博望侯', '合骑侯', '蒯成侯', '辟阳侯', '平阳侯', '绛侯', '长平侯',
    '九侯', '义帝', '厉共公',
    '悼襄王', '惠文王', '孝文王', '庄襄王', '安釐王', '武灵王', '顷襄王',
    '太后', '太公', '周公', '吴王', '赵王', '陈王', '齐王', '魏王', '燕王',
    '韩王', '秦王', '楚王', '梁王', '鲁王', '鲁公',
    '代王', '张王', '彭王',
    '昭帝', '高皇帝', '惠后', '申后',
    '子公', '侯公', '冯公', '枞公', '泄公', '滕公', '翟公', '邓公',
    '荣公', '薛公', '胡公', '申公',
    '条侯', '翕侯', '鄂侯', '齐侯', '晋侯',
}

# --- Manual corrections for known heuristic errors ---
# (chapter_id, short_name) → correct full_name
# These override majority voting results where the heuristic is known to be wrong
MANUAL_CORRECTIONS = {
    ('004', '元王'): '周元王',     # nearby_state:楚 误判，周本纪中元王=周元王
    ('004', '惠王'): '周惠王',    # nearby_state:燕 误判，周本纪中惠王=周惠王
    ('044', '惠王'): '魏惠王',    # nearby_state:秦 误判，魏世家中惠王=魏惠王
    ('044', '襄王'): '魏襄王',    # nearby_state:秦 误判，魏世家中襄王=魏襄王
    ('071', '武王'): '秦武王',    # nearby_state:楚 误判，樗里子甘茂列传中=秦武王
    ('071', '昭王'): '秦昭王',    # nearby_state:楚 误判，樗里子甘茂列传中=秦昭王
    ('079', '昭王'): '秦昭王',    # nearby_state:周 误判，范睢蔡泽列传中=秦昭王
    ('087', '惠王'): '秦惠王',    # nearby_state:楚 误判，李斯列传中=秦惠王
}


def is_valid_person_name(name):
    """Check if a string looks like a valid person name."""
    if len(name) > MAX_FULLNAME_LEN or len(name) < 2:
        return False
    if any(c in INVALID_NAME_CHARS for c in name):
        return False
    return True


def get_state_prefix(name):
    """Extract state prefix from a full name like '秦昭王' -> '秦'."""
    if len(name) >= 2 and name[0] in ALL_STATES_SET:
        return name[0]
    return None


def find_state_tags_nearby(content, pos, window=100):
    """Find state names mentioned near a position."""
    start = max(0, pos - window)
    end = min(len(content), pos + window)
    context = content[start:end]

    found_states = []
    for m in re.finditer(r'&([^&\n]+)&', context):
        state = m.group(1)
        if state in ALL_STATES_SET:
            found_states.append(state)

    for m in re.finditer(r'@([^@\n]+)@', context):
        person = m.group(1)
        if len(person) >= 2 and is_valid_person_name(person):
            first_char = person[0]
            if first_char in ALL_STATES_SET:
                found_states.append(first_char)

    return found_states


def find_cooccurring_fullnames(content, short_name):
    """Find full names containing the short name in @tags@ in the same chapter."""
    pattern = r'@([^@\n]*' + re.escape(short_name) + r'[^@\n]*)@'
    matches = set()
    for m in re.finditer(pattern, content):
        full = m.group(1)
        if full != short_name and len(full) > len(short_name) and is_valid_person_name(full):
            matches.add(full)
    return matches


def find_preceding_state_prefix(content, pos):
    """Check for &state& immediately before @tag@."""
    pre_context = content[max(0, pos - 10):pos]
    m = re.search(r'&([^&]+)&$', pre_context)
    if m and m.group(1) in ALL_STATES_SET:
        return m.group(1)
    return None


def disambiguate():
    """Main disambiguation function - generates disambiguation_map.json."""
    # Identify ambiguous short names directly from RULER_DB
    # No dependency on entity_index.json
    ambiguous_names = set()
    for (short_name, state) in RULER_DB:
        if short_name not in SKIP_NAMES:
            ambiguous_names.add(short_name)

    print("=== Name Disambiguation (metadata mode) ===")
    print(f"Ambiguous names to process: {len(ambiguous_names)}")
    print(f"Names: {sorted(ambiguous_names)}")
    print()

    # Collect per-occurrence results (do NOT modify files)
    # all_results[chapter_id][short_name] = [(full_name, method), ...]
    all_results = defaultdict(lambda: defaultdict(list))
    total_resolved = 0
    total_uncertain = 0
    replacements_log = []
    uncertain_log = []

    chapter_files = sorted([f for f in os.listdir(CHAPTER_DIR) if f.endswith('.tagged.md')])
    print(f"Analyzing {len(chapter_files)} chapter files...")
    print()

    for fname in chapter_files:
        chapter_id = fname[:3]
        primary_state = CHAPTER_STATE.get(chapter_id, None)
        fpath = os.path.join(CHAPTER_DIR, fname)

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pre-compute co-occurring full names
        cooccur_cache = {}
        for short_name in ambiguous_names:
            if '@' + short_name + '@' in content:
                cooccur_cache[short_name] = find_cooccurring_fullnames(content, short_name)

        chapter_resolved = 0

        for short_name in ambiguous_names:
            tag_str = '@' + short_name + '@'
            if tag_str not in content:
                continue

            tag_pattern = '@' + re.escape(short_name) + '@'

            for m in re.finditer(tag_pattern, content):
                pos = m.start()
                resolved = None
                method = None

                # -- Heuristic 1: Preceding state prefix --
                preceding_state = find_preceding_state_prefix(content, pos)
                if preceding_state:
                    key = (short_name, preceding_state)
                    if key in RULER_DB:
                        resolved = RULER_DB[key]
                        method = f'preceding_state:{preceding_state}'

                # -- Heuristic 2: Nearby state mentions --
                if not resolved:
                    nearby_states = find_state_tags_nearby(content, pos, window=80)
                    for state in nearby_states:
                        key = (short_name, state)
                        if key in RULER_DB:
                            resolved = RULER_DB[key]
                            method = f'nearby_state:{state}'
                            break

                # -- Heuristic 3: Chapter's primary state --
                if not resolved and primary_state:
                    key = (short_name, primary_state)
                    if key in RULER_DB:
                        resolved = RULER_DB[key]
                        method = f'chapter_state:{primary_state}'

                # -- Heuristic 4: Co-occurrence as fallback --
                if not resolved and short_name in cooccur_cache:
                    full_names = cooccur_cache[short_name]
                    if len(full_names) == 1:
                        candidate = list(full_names)[0]
                        candidate_state = get_state_prefix(candidate)
                        if candidate_state:
                            broad_nearby = find_state_tags_nearby(content, pos, window=200)
                            if candidate_state in broad_nearby or not primary_state:
                                resolved = candidate
                                method = 'cooccur_unique'
                        else:
                            resolved = candidate
                            method = 'cooccur_unique'
                    elif len(full_names) > 1:
                        nearby = find_state_tags_nearby(content, pos, window=120)
                        for st in nearby:
                            candidates = [fn for fn in full_names if fn.startswith(st)]
                            if len(candidates) == 1:
                                resolved = candidates[0]
                                method = f'cooccur+nearby:{st}'
                                break

                # Record result
                if resolved and resolved != short_name:
                    all_results[chapter_id][short_name].append((resolved, method))
                    total_resolved += 1
                    title = fname[4:-10]
                    replacements_log.append(
                        f'{chapter_id} {title:20s}  @{short_name}@ -> @{resolved}@  [{method}]'
                    )
                    chapter_resolved += 1
                else:
                    start_ctx = max(0, pos - 30)
                    end_ctx = min(len(content), pos + 50)
                    ctx = content[start_ctx:end_ctx].replace('\n', ' ').strip()
                    uncertain_log.append((short_name, ctx, chapter_id))
                    total_uncertain += 1

        if chapter_resolved:
            print(f'  {fname[:40]:42s}  {chapter_resolved} disambiguations')

    # --- Build chapter-level map with majority voting ---
    print()
    print("Building chapter-level disambiguation map...")
    chapter_map = {}
    conflicts = []

    for chapter_id in sorted(all_results):
        chapter_map[chapter_id] = {}
        for short_name, results in all_results[chapter_id].items():
            name_counts = Counter(r[0] for r in results)
            top_name, top_count = name_counts.most_common(1)[0]
            total = sum(name_counts.values())

            if len(name_counts) == 1:
                # Unanimous
                chapter_map[chapter_id][short_name] = top_name
            elif top_count * 3 >= total * 2:
                # Clear majority (>= 2/3)
                chapter_map[chapter_id][short_name] = top_name
                conflicts.append(
                    f'  {chapter_id}: {short_name} → {top_name} '
                    f'(majority {top_count}/{total}, others: {dict(name_counts)})'
                )
            else:
                # Split - don't disambiguate
                conflicts.append(
                    f'  {chapter_id}: {short_name} SKIPPED '
                    f'(split: {dict(name_counts)})'
                )

    # Apply manual corrections
    corrections_applied = 0
    for (chapter_id, short_name), correct_name in MANUAL_CORRECTIONS.items():
        old = chapter_map.get(chapter_id, {}).get(short_name)
        if old != correct_name:
            chapter_map.setdefault(chapter_id, {})[short_name] = correct_name
            corrections_applied += 1
            print(f'  Manual correction: {chapter_id} {short_name}: {old} → {correct_name}')

    # Count total mappings
    total_mappings = sum(len(v) for v in chapter_map.values())

    # --- Output JSON ---
    output = {}
    for chapter_id in sorted(chapter_map):
        if chapter_map[chapter_id]:
            output[chapter_id] = dict(sorted(chapter_map[chapter_id].items()))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # --- Summary ---
    print()
    print('=' * 60)
    print('SUMMARY')
    print('=' * 60)
    print(f"Per-occurrence disambiguations: {total_resolved}")
    print(f"Uncertain (skipped): {total_uncertain}")
    print(f"Chapter-level mappings: {total_mappings}")
    print(f"Chapters with mappings: {len(output)}")
    print(f"Manual corrections applied: {corrections_applied}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    if conflicts:
        print(f"Conflicts ({len(conflicts)}):")
        for c in conflicts:
            print(c)
        print()

    # Top changes
    change_counts = Counter()
    for log_line in replacements_log:
        m = re.search(r'@(\S+)@ -> @(\S+)@', log_line)
        if m:
            change_counts[f'@{m.group(1)}@ -> @{m.group(2)}@'] += 1

    print("Top disambiguation patterns:")
    print('-' * 50)
    for change, count in change_counts.most_common(30):
        print(f'  {count:4d}x  {change}')

    # Method stats
    method_counts = Counter()
    for log_line in replacements_log:
        m = re.search(r'\[(.+)\]', log_line)
        if m:
            method_name = m.group(1).split(':')[0]
            method_counts[method_name] += 1

    print()
    print("Methods used:")
    print('-' * 50)
    for method, count in method_counts.most_common():
        print(f'  {count:4d}x  {method}')

    if uncertain_log:
        print()
        print(f"Uncertain names (not disambiguated): {len(uncertain_log)}")
        uncertain_names = Counter(item[0] for item in uncertain_log)
        for name, count in uncertain_names.most_common(20):
            print(f'  {count:4d}x  @{name}@')

    return output


if __name__ == '__main__':
    disambiguation_map = disambiguate()
