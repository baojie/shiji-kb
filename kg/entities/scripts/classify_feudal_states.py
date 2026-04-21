#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为邦国实体（feudal-state 类型，标注符 〖◆X〗）生成分类标签（国类）。

完全对照 classify_officials.py 的工作流，按 L1-L5 打分：
  L1   显式白名单（上古方国/朝代/周代诸侯/秦末列国/汉诸侯王国/外邦/合称/泛称/
                  部族误标/地名误标/待拆分）
  L2   章节上下文（本纪时代判定/017 诸侯王年表 → 汉王国/018-021 侯者年表 → 地名误标/
                  110 匈奴传 → 部族误标/113-116/123 外邦传 → 外邦）
  L2.5 rulers.json + feudal_state_wordlist.json 批量归类
  L3   共现动词/上下文（chapter_md 扫描）+ 三家注
  L4   后缀启发式（默认兜底）
  L5   并列邦国传播

输出: kg/entities/data/feudal_state_categories.json
结构: { canonical_name: [cat, cat, ...] }  # 多标签
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
OUT_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'feudal_state_categories.json'
OUT_CONF_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'feudal_state_confidence.json'
WORDLIST_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'feudal_state_wordlist.json'
RULERS_JSON = _ROOT / 'kg' / 'relations' / 'rulers.json'
HANSHU_DILI = _ROOT / 'kg' / 'entities' / 'data' / 'hanshu_dili.json'
SANJIA_FILE = _ROOT / 'corpus' / 'shiji' / '史记集解三家注索隐正义.txt'
CHAPTER_DIR = _ROOT / 'chapter_md'


# ─── 类别常量 ───
CAT_ANCIENT     = '上古方国'
CAT_DYNASTY     = '朝代'
CAT_ZHOU_VASSAL = '周代诸侯'
CAT_QIN_END     = '秦末列国'
CAT_HAN_VASSAL  = '汉诸侯王国'
CAT_HAN_MARQUIS = '汉侯国'
CAT_FOREIGN     = '外邦'
CAT_COLLECTIVE  = '合称'
CAT_GENERIC     = '泛称'
CAT_TRIBE_MIS   = '部族误标'
CAT_PLACE_MIS   = '地名误标'
CAT_NEED_SPLIT  = '待拆分'


# ─── 显式白名单 ───

EXPLICIT_ANCIENT_STATE = {
    '有虞', '陶唐', '豕韦', '昆吾', '涂山',
    '有扈', '有莘',  # 有莘氏（禹妻家）
    '斟寻', '斟戈',
    '唐',            # 尧之封地（与朝代"唐"不同 — 由章节消歧）
    '夏后',          # 夏朝前名（复用朝代名，按章节消歧）
    '夏室',
    '周室',          # 周王室（上古义）
}

EXPLICIT_DYNASTY = {
    '夏', '商', '殷', '周', '汉',
    '西周', '东周', '二周',
    '炎汉', '汉家', '汉国',
    '蜀汉', '北魏',
    '成周',
    '周子南君',      # 周王室后裔封号（朝代残遗）
}

# 周代诸侯：包含原"战国七雄"七单字国（秦/楚/齐/燕/赵/魏/韩）
EXPLICIT_ZHOU_VASSAL = {
    # 战国七雄
    '秦', '楚', '齐', '燕', '赵', '魏', '韩',
    # 周代大国
    '晋', '吴', '越',
    # 姬姓诸国
    '鲁', '卫', '郑', '曹', '许', '虞', '虢',
    '邢', '霍', '耿', '芮', '管', '邓', '蔡', '陈',
    # 子男小国
    '宋', '杞', '莒', '邾', '滕', '薛', '息',
    '邹', '驺', '缯', '徐', '江', '黄', '蓼', '六',
    '英', '庸', '巴', '费', '舒', '顿', '随', '申', '邳',
    '郐', '沈', '缪',
    # 中山（战国）
    '中山', '夔',
    # 荆（楚的别称）
    '荆', '荆国',
    # 其他有名小国
    '孤竹', '义渠', '仇犹',
    '东周',  # 战国小国"东周君"（不同于朝代东周）
    # 晋卿分立之前的三晋故国
    '三梁',
    # 越之支
    '路',
    # 春秋时代他族/小国
    '范', '中行',  # 晋六卿氏族（作邦国/封地出现）
    # 战国末小国
    '成', '厓',
    # 补充：首轮未分类但属于此类
    '吕',      # 姜姓吕国（伯夷之后）
    '纪',      # 春秋纪国（齐所灭）
    '舒蓼',    # 春秋舒、蓼 两小国合称（亦可归合称）
    '璿',      # 古小国（见 rulers/古国）
}

EXPLICIT_QIN_END = {
    '张楚',          # 陈胜
    '西楚',          # 项羽
    # 项羽十八诸侯分封（部分）
    '雍', '塞', '翟', '西魏', '河南',
    '常山', '九江', '衡山', '临江', '辽东',
    # 三秦
    '饥国', '三飐',  # 秦末所见异名小国
    # 时代过渡 — 汉初七国之前
}

EXPLICIT_HAN_VASSAL = {
    # 汉初同姓/异姓王国
    '梁', '淮南', '淮阳',
    '胶东', '胶西', '济北', '济南',
    '江都', '长沙', '城阳', '菑川', '河间',
    '广川', '清河', '泗水', '真定', '广陵',
    '六安', '中山国',
    # 注：X国 与单字邦国同名冗余的（齐国/秦国/楚国/燕国/魏国/赵国/宋国/菑川国）
    # 不在此白名单，改由 EXPLICIT_NEED_SPLIT 识别
    # 汉王号（X王 格式）
    '临江王', '江都王', '胶西王', '胶东王',
    '梁怀王', '宋元王', '淮南王',
    '雍王', '塞王', '翟王', '西楚霸王', '缪西王',
    '代王',
}

EXPLICIT_FOREIGN = {
    # 岭南/东南
    '南越', '东越', '闽越', '两越', '百越', '瓯骆',
    # 东北 / 西南夷
    '朝鲜', '夜郎', '滇', '滇国', '滇越', '滇僰', '滇蜀',
    # 西域
    '大宛', '大夏', '大月氏', '小月氏', '月氏',
    '康居', '乌孙', '奄蔡', '条枝', '黎轩',
    '楼兰', '姑师', '于窴', '窴',
    '身毒', '身毒国',
    '仑头', '宛',   # 宛 = 大宛简称
    '苏薤', '驩潜', '扜鰛', '扞鰛',
    # 异族/附属小国
    '大益',          # 西域大益国
    '临屯',          # 朝鲜四郡之前
    '北夷',          # 北方夷
    # 东楚/南楚（秦末越/楚地分区）—— 归合称更合适，暂留外邦候选
    # 徙 = 西南夷一小国
    '徙',
}

EXPLICIT_COLLECTIVE = {
    # 数字集体
    '三代', '三晋', '三秦', '三王',
    '七国', '六国', '五国',
    '二周',          # 西周君+东周君合称（作为"二周"出现）
    # 两国/多国并称
    '吴楚', '吴楚七国', '晋楚', '齐秦',
    '齐秦楚赵',
    # 东西合称
    '两越',
    # 时代名
    '战国', '春秋',
    # 夏商/虞夏
    '唐虞', '虞夏', '夏商',
    # 五帝
    '五帝',
    # 三河（关中+河东+河内 合称）— 但也可能指地理，置于合称候选
    '三河',
    # 南楚/东楚（《货殖列传》按风俗分楚地为三）
    '东楚', '南楚',
    # 巴蜀（巴+蜀 合称）
    '巴蜀',
}

# 部族误标：应标 tribe 〖&X〗 而非 feudal-state 〖◆X〗
EXPLICIT_TRIBE_MIS = {
    # 匈奴及北族
    '匈奴',
    # 四方夷狄通称
    '戎', '狄', '胡',
    '北狄', '西戎', '东夷', '南蛮',
    '荆蛮',
    '犬戎', '山戎', '骊戎',
    '戎狄',
    # 古部族
    '三苗', '有苗',
}

# 汉侯国（列侯食邑封国 — 属邦国）
EXPLICIT_HAN_MARQUIS = {
    '赤泉',          # 赤泉侯（杨喜）
    '硃虚',          # 朱虚侯（刘章）
    '东牟',          # 东牟侯（刘兴居）
    # 原归 HAN_VASSAL 但实际是列侯封国（非王国）
    '中水', '杜衍', '吴防', '涅阳', '射阳',
    # 注：史记本书高频侯国名（酂/留/平阳/舞阳/绛 等）通常以 `〖=X〗` 标注而不进 feudal-state，
    # 此白名单仅收"当前已被标 ◆ 的侯国条目"
}

# 地名误标：应标 place 〖=X〗 而非 feudal-state（仅纯地理大区/郡名；侯国不在此列）
EXPLICIT_PLACE_MIS = {
    # 地理大区
    '关中', '山东', '北地',
    '河东',
    # 郡名
    '上郡', '上谷', '雁门',
    '南郡', '豫章', '益州', '牂柯', '越巂',
    '酒泉', '酒泉郡', '汶山郡', '沈黎', '代郡',
    '临菑',          # 齐都/郡治 — 城邑非邦国
}

# 泛称：作为"国"的通名
EXPLICIT_GENERIC = {
    '国', '大国', '大吴',
    '天下', '中国',
    '北国', '西国', '东国', '南国',
    '附庸',
}

# 待拆分：源头标注冗余（X国 与 X 单字同名）或与 官职/人名 混合
EXPLICIT_NEED_SPLIT = {
    # X国 与单字邦国同名冗余
    '秦国', '齐国', '楚国', '燕国', '魏国',
    '赵国', '宋国', '晋国', '菑川国',
    # 郢 = 楚都（城邑，非邦国）— 若被标 〖◆郢〗 应拆为 place
    '郢',
}


# ─── 章节上下文规则 ───

# 汉诸侯王年表 → 汉诸侯王国
HAN_VASSAL_CHAPTERS = {
    '017_汉兴以来诸侯王年表',
}
# 侯者年表 → 地名误标（汉列侯国=县级）
HOUZHE_CHAPTERS = {
    '018_高祖功臣侯者年表',
    '019_惠景间侯者年表',
    '020_建元以来侯者年表',
    '021_建元已来王子侯者年表',
}
# 匈奴 → 部族误标（若 name 在 EXPLICIT_TRIBE_MIS 内）
XIONGNU_CHAPTERS = {
    '110_匈奴列传',
    '111_卫将军骠骑列传',
}
# 外邦列传 → 外邦
FOREIGN_CHAPTERS = {
    '113_南越列传', '114_东越列传',
    '115_朝鲜列传', '116_西南夷列传',
    '123_大宛列传',
}
# 朝代本纪
DYNASTY_CHAPTERS = {
    '002_夏本纪':    '夏',
    '003_殷本纪':    '殷',
    '004_周本纪':    '周',
    '006_秦始皇本纪': '秦',
    '008_高祖本纪':  '汉',
    '009_吕太后本纪':'汉',
    '010_孝文本纪':  '汉',
    '011_孝景本纪':  '汉',
    '012_孝武本纪':  '汉',
    '028_封禅书':    '汉',  # 封禅多言汉武
}
# 世家章节 → 周代诸侯（本国传）
SHIJIA_CHAPTER_TO_STATE = {
    '031_吴太伯世家':  '吴',
    '032_齐太公世家':  '齐',
    '033_鲁周公世家':  '鲁',
    '034_燕召公世家':  '燕',
    '035_管蔡世家':    '蔡',
    '036_陈杞世家':    '陈',
    '037_卫康叔世家':  '卫',
    '038_宋微子世家':  '宋',
    '039_晋世家':      '晋',
    '040_楚世家':      '楚',
    '041_越王勾践世家':'越',
    '042_郑世家':      '郑',
    '043_赵世家':      '赵',
    '044_魏世家':      '魏',
    '045_韩世家':      '韩',
    '046_田敬仲完世家':'齐',
}
# 汉诸侯王世家/列传 → 汉诸侯王国
HAN_VASSAL_CHAPTER_TO_STATE = {
    '050_楚元王世家':    '楚',
    '051_荆燕世家':      '燕',
    '052_齐悼惠王世家':  '齐',
    '054_曹相国世家':    '齐',  # 曹参相齐
    '057_绛侯周勃世家':  '梁',  # 周亚夫封条，征七国
    '058_梁孝王世家':    '梁',
    '059_五宗世家':      None,  # 武帝五母五宗
    '060_三王世家':      None,
    '106_吴王濞列传':    '吴',
    '118_淮南衡山列传':  '淮南',
}


# ─── 共现动词/上下文模式 ───
# 对 〖◆X〗 条目做类别弱确认（无强类别提升作用，主要用于"这是邦国"的确认
# 和多邦国 peer 识别；分类权重主要来自 L1/L2/L2.5）

CONTEXT_PATTERNS = [
    # 汉代封王：封X为Y王 / 立X为Y王  → 汉王国候选
    (r'⟦○(?:封|立)⟧[^〖]{0,30}为〖;([一-鿿]{1,4}王)〗', CAT_HAN_VASSAL, 0.4),
    # 汉代徙封：徙X为Y王
    (r'⟦○徙⟧[^〖]{0,15}〖◆([一-鿿]{1,4})〗', CAT_HAN_VASSAL, 0.3),
    # 春秋动词：X公/X侯 + 邦国名（弱线索）
    # X之君 / X之民 — 弱确认
]

# 三家注模式
SANJIA_PATTERNS = [
    (re.compile(r'([一-鿿]{1,6})，国名(?:也)?'),           CAT_ZHOU_VASSAL),
    (re.compile(r'([一-鿿]{1,6})，国也'),                  CAT_ZHOU_VASSAL),
    (re.compile(r'([一-鿿]{1,6})，(?:小|古|殷|周|楚)国(?:也)?'), CAT_ZHOU_VASSAL),
    (re.compile(r'([一-鿿]{1,6})，(?:古封|封)国(?:也)?'),  CAT_ZHOU_VASSAL),
    (re.compile(r'([一-鿿]{1,6})，诸侯(?:国)?(?:也)?'),    CAT_ZHOU_VASSAL),
    (re.compile(r'([一-鿿]{1,6})，匈奴(?:国|号)'),         CAT_TRIBE_MIS),
    (re.compile(r'([一-鿿]{1,6})，(?:胡|夷狄)之?国'),      CAT_FOREIGN),
    (re.compile(r'([一-鿿]{1,6})，西域(?:国名|诸国|国)'),  CAT_FOREIGN),
]


# ─── 后缀/字形启发式 ───

SUFFIX_RULES = [
    # 合称：数字集体
    ('晋', 2, None),  # 占位（真实匹配在 _classify_suffix_collective）
]


def _is_collective_by_form(name):
    """形态识别合称：含数字前缀 / 两国名连写。"""
    if len(name) < 2:
        return False
    # 数字开头的集体词（三X/七X/六X/两X/五X）
    if name[0] in '三七六两五九十' and len(name) >= 2:
        # 但 "三河"/"三秦" 已在 EXPLICIT_COLLECTIVE；
        # "三晋"/"七国"/"六国" 也已收录。这里是未收录的兜底。
        return True
    return False


def _is_tribe_mis_by_form(name):
    """形态识别部族：X戎/X狄/X夷/X蛮 且非单邦国名。"""
    if len(name) >= 2 and name[-1] in '戎狄夷蛮胡':
        return True
    return False


def _is_split_xguo(name, state_set):
    """X国 且 X 本身是 feudal-state 白名单成员 → 待拆分候选。
    例：秦国/齐国/燕国/楚国/赵国/魏国/宋国/晋国
    """
    if len(name) >= 2 and name.endswith('国'):
        prefix = name[:-1]
        if prefix in state_set:
            return True
    return False


def _is_x_wang(name):
    """X王 形式（应归 official 王号，邦国表中出现 → 拆分）。"""
    return len(name) >= 2 and name.endswith('王')


# ─── 加载外部数据 ───

def _load_wordlist():
    """加载 feudal_state_wordlist.json 为 L2.5 数据源。"""
    if not WORDLIST_JSON.exists():
        return {}
    try:
        return json.loads(WORDLIST_JSON.read_text(encoding='utf-8'))
    except Exception:
        return {}


WORDLIST = _load_wordlist()


def _load_rulers_by_state():
    """加载 rulers.json，按 所属国 × 类型 建立"邦国 → 预期类别"映射。"""
    if not RULERS_JSON.exists():
        return defaultdict(Counter)
    try:
        data = json.loads(RULERS_JSON.read_text(encoding='utf-8'))
    except Exception:
        return defaultdict(Counter)
    votes = defaultdict(Counter)
    type_to_cat = {
        '天子/皇帝': CAT_DYNASTY,
        '诸侯侯君':  CAT_ZHOU_VASSAL,
        '诸侯王':    CAT_ZHOU_VASSAL,
        '汉诸侯王':  CAT_HAN_VASSAL,
        '单于':      CAT_TRIBE_MIS,
        '晋卿大夫':  CAT_ZHOU_VASSAL,
        '齐卿大夫':  CAT_ZHOU_VASSAL,
        '先祖':      CAT_ANCIENT,
    }
    for r in data.get('rulers', []):
        state = r.get('所属国', '')
        typ = r.get('类型', '')
        if not state:
            continue
        cat = type_to_cat.get(typ)
        if not cat:
            continue
        # 归一化所属国名（"商（殷）"→"商"；"齐（田齐）"→"齐"；"河间国"→"河间"）
        base_state = re.sub(r'[（(].*?[）)]', '', state).strip()
        base_state = re.sub(r'国$', '', base_state) if base_state.endswith('国') else base_state
        votes[state][cat] += 1
        if base_state != state:
            votes[base_state][cat] += 1
    return votes


RULERS_VOTES = _load_rulers_by_state()


def _load_han_counties():
    """加载《汉书·地理志》郡县，用于辅助 place_mis 判定。"""
    if not HANSHU_DILI.exists():
        return set()
    try:
        data = json.loads(HANSHU_DILI.read_text(encoding='utf-8'))
        counties = set()
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    counties.update(v)
                elif isinstance(v, dict):
                    counties.update(v.keys())
        return counties
    except Exception:
        return set()


HAN_COUNTIES = _load_han_counties()


# ─── 分类主逻辑 ───

def classify_l1_whitelist(name):
    """L1: 显式白名单命中。返回 list[str]（可多标签）。
    误标三子类（tribe/place/split）早返回单标签。
    """
    # 误标类早返回
    if name in EXPLICIT_TRIBE_MIS:
        return [CAT_TRIBE_MIS]
    if name in EXPLICIT_PLACE_MIS:
        return [CAT_PLACE_MIS]
    if name in EXPLICIT_NEED_SPLIT:
        return [CAT_NEED_SPLIT]
    # 合法多标签累积
    cats = []
    if name in EXPLICIT_ANCIENT_STATE: cats.append(CAT_ANCIENT)
    if name in EXPLICIT_DYNASTY:       cats.append(CAT_DYNASTY)
    if name in EXPLICIT_ZHOU_VASSAL:   cats.append(CAT_ZHOU_VASSAL)
    if name in EXPLICIT_QIN_END:       cats.append(CAT_QIN_END)
    if name in EXPLICIT_HAN_VASSAL:    cats.append(CAT_HAN_VASSAL)
    if name in EXPLICIT_HAN_MARQUIS:   cats.append(CAT_HAN_MARQUIS)
    if name in EXPLICIT_FOREIGN:       cats.append(CAT_FOREIGN)
    if name in EXPLICIT_COLLECTIVE:    cats.append(CAT_COLLECTIVE)
    if name in EXPLICIT_GENERIC:       cats.append(CAT_GENERIC)
    # 去重保序
    seen = set(); uniq = []
    for c in cats:
        if c not in seen:
            seen.add(c); uniq.append(c)
    return uniq


def classify_l25_wordlist(name):
    """L2.5a: feudal_state_wordlist.json 数据源。"""
    if not WORDLIST:
        return None
    stays = WORDLIST.get('stays_dynasty', {})
    if name in stays.get('unified_dynasties', []):
        return CAT_DYNASTY
    if name in stays.get('collective_terms', []):
        return CAT_COLLECTIVE
    if name in stays.get('foreign_states', []):
        # 再细分：匈奴类归部族误标，其余归外邦
        if name in {'匈奴'}:
            return CAT_TRIBE_MIS
        return CAT_FOREIGN
    if name in stays.get('geographic_admin', []):
        return CAT_PLACE_MIS
    always = WORDLIST.get('always_feudal', [])
    if name in always:
        # always_feudal 里的都是正式邦国，但具体类别需要再派：
        # 作简单判断：汉王国特征 / 秦末 / 外邦 已在 L1 白名单覆盖。
        # 此处只作"此条目确实是邦国"的弱证据（不设类别）。
        return None
    return None


def classify_l25_rulers(name):
    """L2.5b: rulers.json 批量归类。返回 (cat, votes) 或 (None, 0)。"""
    ctr = RULERS_VOTES.get(name, Counter())
    if not ctr:
        return None, 0
    top_cat, top_votes = ctr.most_common(1)[0]
    return top_cat, top_votes


def classify_l4_form(name, state_set):
    """L4: 后缀/字形启发式。返回 str 或 None。"""
    # X国 且 X 是 feudal-state → split 候选
    if _is_split_xguo(name, state_set):
        return CAT_NEED_SPLIT
    # X王 → split 候选（应归 official 王号）
    if _is_x_wang(name) and name not in EXPLICIT_HAN_VASSAL:
        return CAT_NEED_SPLIT
    # X戎/X狄/X夷/X蛮 → 部族误标
    if _is_tribe_mis_by_form(name):
        return CAT_TRIBE_MIS
    # 数字集体 → 合称
    if _is_collective_by_form(name):
        return CAT_COLLECTIVE
    # X氏 → 朝代
    if name.endswith('氏') and len(name) >= 2:
        return CAT_DYNASTY
    return None


def classify_l2_chapter(name, refs):
    """L2: 章节上下文规则。
    - 017_汉兴以来诸侯王年表 → 汉诸侯王国
    - 018-021 侯者年表 → 地名误标
    - 110 匈奴传 → 部族误标（仅 name 本身可能是部族时）
    - 113-116 / 123 外邦传 → 外邦
    - 本纪章的主朝代 → 朝代
    - 世家章的主邦国 → 周代诸侯
    """
    if not refs:
        return None
    ch_counts = Counter(ch for ch, _ in refs)
    total = sum(ch_counts.values())
    if total == 0:
        return None

    # 1) 017 → 汉王国
    if ch_counts.get('017_汉兴以来诸侯王年表', 0) / total >= 0.5:
        return CAT_HAN_VASSAL
    # 2) 018-021 侯者年表 → 汉侯国（侯国也算邦国，不再视为误标）
    houzhe = sum(c for ch, c in ch_counts.items() if ch in HOUZHE_CHAPTERS)
    if houzhe / total >= 0.6 and total >= 2:
        return CAT_HAN_MARQUIS
    # 3) 外邦传
    foreign = sum(c for ch, c in ch_counts.items() if ch in FOREIGN_CHAPTERS)
    if foreign / total >= 0.5:
        return CAT_FOREIGN
    # 4) 匈奴传 + name 含外邦/部族关键字
    xiongnu = sum(c for ch, c in ch_counts.items() if ch in XIONGNU_CHAPTERS)
    if xiongnu / total >= 0.5:
        if any(kw in name for kw in ('匈奴', '胡', '戎', '狄')):
            return CAT_TRIBE_MIS
    # 5) 本纪章的主朝代
    for ch, expected in DYNASTY_CHAPTERS.items():
        if ch in ch_counts and name == expected:
            # 秦始皇本纪内的"秦" = 朝代；005 秦本纪内的"秦" = 周代诸侯
            return CAT_DYNASTY
    # 6) 世家章的主邦国
    for ch, state in SHIJIA_CHAPTER_TO_STATE.items():
        if ch_counts.get(ch, 0) / total >= 0.5 and name == state:
            return CAT_ZHOU_VASSAL
    # 7) 汉诸侯王世家/列传
    for ch, state in HAN_VASSAL_CHAPTER_TO_STATE.items():
        if state and ch_counts.get(ch, 0) / total >= 0.5 and name == state:
            return CAT_HAN_VASSAL
    return None


def _scan_context_votes(state_names):
    """L3: 扫描 chapter_md 累积共现类别票数。"""
    votes = defaultdict(Counter)
    name_set = set(state_names)
    compiled = [(re.compile(p), cat, w) for p, cat, w in CONTEXT_PATTERNS if cat is not None]
    for ch_file in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        content = ch_file.read_text(encoding='utf-8')
        for pat, cat, weight in compiled:
            for m in pat.finditer(content):
                hit = m.group(1)
                canonical = hit.split('|', 1)[-1] if '|' in hit else hit
                if canonical in name_set:
                    votes[canonical][cat] += weight
    return votes


def _load_sanjia_hints():
    """L3: 从三家注累积类别线索。"""
    if not SANJIA_FILE.exists():
        return defaultdict(Counter)
    votes = defaultdict(Counter)
    try:
        text = SANJIA_FILE.read_text(encoding='utf-8')
    except Exception:
        return votes
    for pat, cat in SANJIA_PATTERNS:
        if cat is None:
            continue
        for m in pat.finditer(text):
            name = m.group(1)
            votes[name][cat] += 1.0
    return votes


def classify_l3_context(name, ctx_votes, sanjia_votes, threshold=0.6):
    combined = ctx_votes.get(name, Counter()) + sanjia_votes.get(name, Counter())
    if not combined:
        return None, 0.0
    total = sum(combined.values())
    if total < 1.0:
        return None, 0.0
    top_cat, top_votes = combined.most_common(1)[0]
    ratio = top_votes / total
    if ratio >= threshold:
        return top_cat, ratio
    return None, ratio


def _peer_split(state_names, name_to_cats):
    """L5: 并列邦国传播。
    〖◆A〗、〖◆B〗、〖◆C〗 序列中向未分类条目传播多数类别。"""
    name_set = set(state_names)
    pat = re.compile(r'〖◆([^〖〗|]+?)(?:\|[^〖〗]+)?〗')
    sep = re.compile(r'^[、，\s]+$')
    updates = defaultdict(Counter)
    for ch_file in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        content = ch_file.read_text(encoding='utf-8')
        matches = list(pat.finditer(content))
        if not matches:
            continue
        groups = []
        cur = [matches[0]]
        for prev, m in zip(matches, matches[1:]):
            between = content[prev.end():m.start()]
            if sep.fullmatch(between):
                cur.append(m)
            else:
                if len(cur) >= 2:
                    groups.append(cur)
                cur = [m]
        if len(cur) >= 2:
            groups.append(cur)
        for grp in groups:
            names = [g.group(1) for g in grp if g.group(1) in name_set]
            if len(names) < 2:
                continue
            tally = Counter()
            blank_members = []
            for n in names:
                cats = name_to_cats.get(n, [])
                if cats:
                    for c in cats:
                        tally[c] += 1
                else:
                    blank_members.append(n)
            if not tally or not blank_members:
                continue
            total = sum(tally.values())
            top_cat, top_votes = tally.most_common(1)[0]
            if top_votes / total >= 0.6:
                for bm in blank_members:
                    updates[bm][top_cat] += 1
    return updates


# ─── 置信度评分 ───

def score_evidence(name, final_cats, l1, l25_wl, l25_ruler, l2, l3_cat, l3_score, l4, peer_ctr):
    out = {}
    for cat in final_cats:
        score = 0.0
        if cat in l1:
            score += 0.6
        if l25_wl == cat:
            score += 0.3
        if l25_ruler == cat:
            score += 0.3
        if l2 == cat:
            score += 0.3
        if l3_cat == cat:
            score += 0.3 * l3_score
        if l4 == cat:
            score += 0.2
        if peer_ctr.get(cat, 0) > 0:
            score += 0.15
        score = min(1.0, score)
        if score == 0.0:
            score = 0.1
        out[cat] = round(score, 2)
    return out


# ─── 主流程 ───

def main():
    print('━' * 60)
    print('邦国分类脚本 classify_feudal_states.py')
    print('━' * 60)

    index = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
    states = index.get('feudal-state', {})
    names = list(states.keys())
    state_set = set(names)
    print(f'邦国实体总数: {len(names)}')
    print(f'rulers.json 按所属国映射条目: {len(RULERS_VOTES)}')
    print(f'feudal_state_wordlist.json 分组: {list(WORDLIST.keys()) if WORDLIST else "未加载"}')
    print(f'《汉书·地理志》郡县: {len(HAN_COUNTIES)}')
    print()

    print('L3: 扫描 chapter_md 共现模式...')
    ctx_votes = _scan_context_votes(names)
    print(f'  命中条目: {len(ctx_votes)}')
    print('L3: 扫描三家注...')
    sanjia_votes = _load_sanjia_hints()
    print(f'  命中条目: {len(sanjia_votes)}')
    print()

    name_to_cats = {}
    name_to_details = {}
    for name in names:
        refs = [tuple(r) for r in states[name].get('refs', [])]

        l1 = classify_l1_whitelist(name)
        l25_wl = classify_l25_wordlist(name)
        l25_ruler, _ = classify_l25_rulers(name)
        l2 = classify_l2_chapter(name, refs)
        l3_cat, l3_score = classify_l3_context(name, ctx_votes, sanjia_votes)
        l4 = classify_l4_form(name, state_set)

        final = []
        # 误标三子类早返回（单标签）
        if l1 and l1[0] in (CAT_TRIBE_MIS, CAT_PLACE_MIS, CAT_NEED_SPLIT):
            final = [l1[0]]
        else:
            # 合并多层。优先级 L1 > L2.5(wordlist) > L2.5(rulers) > L2 > L3 > L4
            for c in l1: final.append(c)
            if l25_wl and l25_wl not in final:
                final.append(l25_wl)
            # rulers.json 的"诸侯王"类型会把外邦/秦末列国/汉王国也映射为"周代诸侯"，
            # 故当 L1 已给出更具体类别时，不再追加 ZHOU_VASSAL
            _has_specific_period = any(c in final for c in
                (CAT_FOREIGN, CAT_QIN_END, CAT_HAN_VASSAL, CAT_ANCIENT))
            if l25_ruler and l25_ruler not in final:
                if l25_ruler == CAT_ZHOU_VASSAL and _has_specific_period:
                    pass
                else:
                    final.append(l25_ruler)
            if l2 and l2 not in final:
                # L2（地名误标/部族误标）在 L1 已有合法分类时不追加
                if l2 in (CAT_PLACE_MIS, CAT_TRIBE_MIS) and final:
                    pass
                else:
                    final.append(l2)
            if l3_cat and l3_cat not in final and not final:
                final.append(l3_cat)
            if l4 and l4 not in final:
                # L4 split/tribe-mis 只在 L1/L2/L2.5 都没给出合法类别时采用
                if l4 in (CAT_NEED_SPLIT, CAT_TRIBE_MIS) and final:
                    pass
                elif not final:
                    final.append(l4)

        name_to_cats[name] = final
        name_to_details[name] = dict(
            l1=l1, l25_wl=l25_wl, l25_ruler=l25_ruler,
            l2=l2, l3=(l3_cat, l3_score), l4=l4, peer=Counter()
        )

    print('L5: 并列邦国传播...')
    for round_i in range(3):
        peer_updates = _peer_split(names, name_to_cats)
        changed = 0
        for name, cats_ctr in peer_updates.items():
            if name_to_cats.get(name):
                continue
            if not cats_ctr:
                continue
            top_cat, top_votes = cats_ctr.most_common(1)[0]
            total = sum(cats_ctr.values())
            if top_votes / total >= 0.6 and top_votes >= 2:
                name_to_cats[name] = [top_cat]
                name_to_details[name]['peer'][top_cat] = top_votes
                changed += 1
        print(f'  第 {round_i+1} 轮传播: 新增 {changed} 条')
        if changed == 0:
            break

    # 置信度
    confidence = {}
    for name, cats in name_to_cats.items():
        if not cats:
            continue
        d = name_to_details[name]
        conf = score_evidence(
            name, cats,
            l1=d['l1'], l25_wl=d['l25_wl'], l25_ruler=d['l25_ruler'],
            l2=d['l2'], l3_cat=d['l3'][0], l3_score=d['l3'][1],
            l4=d['l4'], peer_ctr=d['peer'],
        )
        confidence[name] = conf

    OUT_JSON.write_text(
        json.dumps(name_to_cats, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    OUT_CONF_JSON.write_text(
        json.dumps(confidence, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    # 统计
    cat_counter = Counter()
    blank_names = []
    multi_label = 0
    for name, cats in name_to_cats.items():
        if not cats:
            blank_names.append(name)
        else:
            for c in cats:
                cat_counter[c] += 1
            if len(cats) > 1:
                multi_label += 1
    print()
    print('━' * 60)
    print('分类结果')
    print('━' * 60)
    total = len(name_to_cats)
    for cat, n in sorted(cat_counter.items(), key=lambda x: -x[1]):
        print(f'  {cat:<10} {n:>5}  ({n/total*100:.1f}%)')
    print(f'  {"未分类":<10} {len(blank_names):>5}  ({len(blank_names)/total*100:.1f}%)')
    print(f'  {"多标签":<10} {multi_label:>5}  ({multi_label/total*100:.1f}%)')
    print()
    print(f'未分类样本: {blank_names[:40]}')
    print()
    print(f'写入: {OUT_JSON}')
    print(f'写入: {OUT_CONF_JSON}')


if __name__ == '__main__':
    main()
