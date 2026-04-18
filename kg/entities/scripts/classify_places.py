#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为地名实体生成分类标签（地段）。

采用启发式规则 + 高频显式清单，给 entity_index.json 的 place 条目打上分类。
不确定的条目留空（空字符串），以便后续人工修订。

输出: kg/entities/data/place_categories.json
结构: { canonical_name: category }
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
OUT_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'place_categories.json'
HANSHU_DILI = _ROOT / 'kg' / 'entities' / 'data' / 'hanshu_dili.json'
SANJIA_FILE = _ROOT / 'corpus' / 'shiji' / '史记集解三家注索隐正义.txt'
CHAPTER_DIR = _ROOT / 'chapter_md'


def _load_hanshu_dili():
    """加载《汉书·地理志》提取出的郡县白名单。
    返回 (jun_set, xian_set)。若文件不存在，返回 (set(), set())。"""
    if not HANSHU_DILI.exists():
        return set(), set()
    try:
        data = json.loads(HANSHU_DILI.read_text(encoding='utf-8'))
        # 剥去 "X郡"/"X国"/"X尹" 后缀后也加入 KNOWN_COMMANDERIES（史记中多不带后缀）
        jun_full = set(data.get('commanderies', []))
        jun_bare = set()
        for name in jun_full:
            for suf in ('郡', '国', '尹', '内史', '冯翊', '扶风'):
                if name.endswith(suf) and len(name) > len(suf):
                    jun_bare.add(name[:-len(suf)])
        jun_set = jun_full | jun_bare
        xian_set = set(data.get('counties', []))
        return jun_set, xian_set
    except Exception:
        return set(), set()


HANSHU_JUN, HANSHU_XIAN = _load_hanshu_dili()

# ─── 显式清单：优先命中 ───
# 区域（大片地理概念，非行政实体）
EXPLICIT_REGION = {
    # 天下/四海/诸夏
    '天下', '九州', '四海', '海内', '海外', '中国', '中原', '中土', '华夏',
    '四方', '八方', '东方', '南方', '西方', '北方', '四极', '四夷',
    # 关中/关东
    '关中', '关内', '关外', '关东', '关西',
    # 山东/山西
    '山东', '山西',
    # 河东/河西
    '河东', '河西', '河内', '河外', '河南地',
    # 江南/江东
    '江南', '江北', '江东', '江西', '江左', '江右',
    # 淮南/淮北
    '淮南', '淮北',
    # 其他
    '河南江北', '河表', '大河',
    '西域', '南越地', '北边', '塞北', '塞外',
    '中县', '中国诸侯',
    # 两邦国并称（以史记中"X之地/人/民"用法为主）
    '燕赵', '吴越', '齐鲁', '秦晋', '燕齐', '梁楚', '齐赵', '齐楚', '燕韩',
    '楚汉', '三晋', '三秦', '六国', '五国', '四国',
    # 方位+土/州/陲/垂/边：指广域地区（非行政州）
    '东土', '西土', '南土', '北土', '中土',
    '东州', '西州', '南州', '北州', '中州',
    '东陲', '西陲', '南陲', '北陲',
    '东垂', '西垂', '南垂', '北垂',
    '东边', '西边', '南边',
    '东裔', '南裔',
    # 方位+隅/陬 (角落/边陲地带)
    '东隅', '西隅', '南隅', '北隅',
    '东陬', '西陬', '南陬', '北陬',
    # 主要河流/山脉/邦国 + 方位 = 区域
    '河东', '河西', '河南', '河北', '河内', '河外', '河南江北',
    '济东', '济西', '济北', '济南',
    '汉北', '汉南', '汉东', '汉西', '汉中',
    '淮东', '淮西', '淮南', '淮北', '淮泗', '淮海',
    '江南', '江北', '江东', '江西', '江左', '江右',
    '泗东', '泗西', '泗上',
    '渭北', '渭南',
    '梁北', '梁南',
    '海东', '海西', '海内', '海外',
    '山南', '山北',
    '关中', '关内', '关外', '关东', '关西',
    '巴蜀', '三辅', '三河', '陇蜀', '蜀汉',
    # 新增泛区域
    '宗周', '大原', '外方', '内方', '吴中', '秦中', '假中', '於中',
    '河宗', '丰沛', '莒地', '梁地',
    # 特定长地名
    '江南九疑', '东阳河外', '休溷诸貉', '下东国',
    '京师', '周南', '北假', '北户',
    # 方位泛指
    '东北', '东南', '西北', '西南', '东方', '南方', '西方', '北方',
    # 组合区域
    '江汉', '河济', '河洛', '河雒', '河渭', '泾渭', '洙泗',
    '滇蜀', '西蜀', '西极', '西界', '西域', '西雍',
    '夏路', '邛僰', '邛笮',
    '巩洛',            # 巩县 + 洛阳 之间
    '南河之南',        # 黄河南岸
    '辽间',            # 辽东辽西间
    '种',              # 种代 北方地
    '石',              # 石北（赵东北）
    '许田', '毕',       # 周王畿田地
    '东原', '上地', '上原',  # 地区性地名
    '大原',            # 即太原/大原泛指
    '东周',            # 东周国地（王畿东部）
    '周',              # 周京区域
    '岐下',            # 岐山下
    '天',              # 天下（"自天下属地"）
    '苞满',            # 西南地
    '离碓',            # 水利地带
    '桑间', '濮上',     # 卫地民俗区域
}

# 水域（合并：江河湖泊 + 海洋）
# 海洋条目与河流合并成一个类别，因为海洋条目较少，单列不合算
EXPLICIT_WATER = {
    # 海洋
    '海', '东海', '南海', '北海', '勃海', '渤海', '西海', '瀚海', '四海', '江海', '淮海',
    # 知名河流（单字或无"水/河"后缀）
    '江', '河', '淮', '济', '汉', '泾', '渭', '洛', '雒', '汾', '沁', '漳', '滹', '沱',
    '泗', '沂', '汶', '淄', '潍', '濰', '湘', '沅', '澧', '资', '赣', '沱', '涔',
    '弱水', '黑水', '若水', '浙江', '乌江', '庐江', '九江',
    '沮', '漯', '伊', '瀍', '涧', '荆', '菏', '荷',
    '丹水', '丹', '巴', '蜀水',
    '沔',  # 沔水=汉水别名，襃水通沔/漕从沔入襃
    '襃', '褒',  # 襃水（可以行船漕）
    '斜',  # 斜水
    '潜',  # 潜水（梁州，浮于潜踰于沔）
    '瀁',  # 瀁水（嶓冢山所出）
    # 砥柱移动到 mountain 上面已加
    # 其他水系
    '汨', '汨罗',      # 屈原沉江处
    '洨',              # 洨水
    '潏', '潦',        # 关中八川
    '汾陉',            # 汾水陉
    '浐', '雷夏',      # 雷夏泽
    '焦穫',            # 穫泽
    '泜',              # 泜水（韩信背水阵）
    '钜定',            # 钜定泽
    '沈',              # 沈水
    '九防',            # 曲九防 = 九条堤防
    '镐',              # 镐京附近水泊
    '酆', '酆鄗', '酆镐', '丰镐',  # 丰水镐水
    '醴',              # 醴水
    # 补低置信度水名
    '滈',              # 滈水（关中八川）
    '若邪',            # 若邪溪（越地）
    '湫渊',            # 祠朝的湫渊
    '汜',              # 汜水
    '鸿沟',
    '襃斜',
    '天齐',            # 天齐渊（祠临菑）
    '河洲',            # 河上沙洲
    # 大湖/大泽（不带"泽/湖"后缀但是水体）
    '大野',  # 大野泽
}

# 原野（古代战场、开阔平野；不是水体）
EXPLICIT_PLAIN = {
    '阪泉之野', '涿鹿之野', '苍梧之野', '牧野', '商郊牧野', '东野', '都野',
    '商牧', '商郊',    # 商地牧野/郊外（同牧野系列）
}

# 误标：实体索引中被误标为 place 的非地名条目
# （修辞虚指、名号、制度名、人名、典故用语等，需要将来人工清理出 place 列表）
EXPLICIT_NON_PLACE = {
    # 典故/抽象概念 / 官号侯号（真不是地名）
    '乾封',   # "黄帝时封则天旱，乾封三年" —— 干燥封坛之典故
    '五帝',   # "宰我问五帝之德" —— 五帝 = 古代帝王
    '善置',   # "先围善置" —— "善（于）置"动词短语
    '水滨',   # "问之水滨"（修辞，水边泛指）
    '室',     # "故鼎反乎室"（宗庙/家室，非地名）
    '平陵侯', # 实为侯号而非地名
    '湘君',   # 湘水神，非地名
    '深泽侯', # 侯号
    '须如',   # 句末虚字？
    '贰师',   # 贰师将军 = 官号
    # 单字泛称（在 tag 里指代类名，不是某具体地点）
    '县', '城',       # "县名胜母"等抽象用法
    '川', '泽',       # "山川"/"泽"单字泛称
    '寝', '观', '阙', # 建筑类泛称
    '津',             # 津口泛称
    '党氏',           # 氏族，非地名
}


# 虚构（文学作品中的虚构地名）
# 例如司马相如《子虚赋》《上林赋》中为修辞/铺陈而造的非实指地名。
# 这些条目**仍然**是 place（作者有地理意象），但不是真实地理实体。
EXPLICIT_FICTIONAL = {
    # 司马相如《子虚赋》《上林赋》《大人赋》
    '列缺', '北纮', '轇輵', '洲淤', '盐浦',
    '石濑', '牛首', '汤谷',
    '乂鹊',                    # "过乂鹊"
    '嶻',                      # "九嵏、嶻"
    '青波', '清波',            # 修辞水名
    '孙原',                    # "梁孙原"
    '汶篁',                    # "植於汶篁"（汶水+篁竹林混成）
    '椒丘', '泱莽',            # 赋中虚构
    '露寒', '棠梨', '宜春', '宣曲', '龙台', '细柳',
                               # 上林苑中假托地名（或真或虚，赋体修饰）
    '紫渊',                    # 赋中虚构
}


# 国家（境外独立政权、外邦小国、西域诸国等）
# 注：匈奴/东胡等大族群多标注为〖◆〗邦国或〖~〗族群，这里只收录《史记》中以〖=〗出现者
EXPLICIT_NATION = {
    # 西域/中亚
    '大夏', '大宛', '康居', '月氏', '大月氏', '小月氏',
    '安息', '条支', '条枝', '身毒', '乌孙', '奄蔡', '罽宾',
    '婼羌', '于阗', '楼兰', '姑师', '车师', '龟兹', '焉耆',
    '大秦',
    # 东北
    '朝鲜', '真番', '临屯', '玄菟',
    # 南方外邦
    '南越', '闽越', '东瓯', '东越', '西瓯',
    # 西南夷
    '夜郎', '滇', '邛都', '笮都', '冉駹', '白马', '且兰',
    # 北方
    '乌桓', '鲜卑',
    # 上古小国 / 族群地
    '孤竹', '密须', '犬夷', '冀戎', '句吴',
    '林胡', '北蛮',
    '奄',              # 奄国
    '崇',              # 崇国
    '胡',              # 胡国
    '纪',              # 纪国
    '菟裘',            # 鲁邑（本鲁国）— actually 城邑 but keep here for hist
    '有山氏', '彭戏氏', '蔿氏', '廧咎如', '荡氏',   # 氏族地
    '虞', '邘', '邰',
    '蟠木',            # 东极之地（模糊）
    '析支',
    '北鄙', '北纮',     # 边裔地
    # 西南西北外族
    '沈犁', '犍为',
    '交阯',            # 交阯（汉置郡但有时作为外邦地出现）
    '欧代',            # 东胡欧代地
}

# 知名山岳
EXPLICIT_MOUNTAIN = {
    '泰山', '华山', '嵩山', '恒山', '衡山', '太华', '泰华', '岐', '岐山',
    '崆峒', '崆峒山', '首阳', '首阳山', '终南', '终南山',
    '骊山', '蓝田', '阴山', '燕山', '狼居胥山', '祁连', '祁连山',
    '蒙', '峄', '羽', '熊', '会稽',
    # 《禹贡》九山系统
    '汧', '壶口', '雷首', '王屋', '砥柱', '析城', '大岳', '太岳',
    '熊耳', '外方', '桐柏', '硃圉', '负尾', '内方', '大别',
    '西倾', '鸟鼠', '积石', '空桐', '大麓',
    # 战场/祭祀山岭
    '不周',    # 不周山（传说）
    '傅险',    # 傅说匿于傅险 = 山险
    '姑衍',    # 匈奴禅地（山）
    '九嵏',    # 司马相如赋"九嵏、嶻"—— 九嵏山
    '梅领',    # 梅岭（异写）
    '梓领',    # 梓岭
    '羊肠',    # 羊肠阪（太行山口）
    '岐下', '岐昌', '岐雍',   # 岐山周围区域
    '三危',    # 三危山
    '敷浅原',  # 《禹贡》
    '南巢',    # 山名（汤放桀之处）
    '硃方',    # 已知误判
    '芒',      # 芒砀山（芒砀二字常并用）
    '衡漳', '衡',
    '鸟鼠',
    '骀',      # 骀 = 尧舜时代山名
    '霍',      # 霍山
    '息壤',    # 神话山
    '什谷', '横谷', '颍谷',   # 山谷
    '邓林',    # 山林
    '大行',    # 太行山别名（"断大行"/"杜大行之道/阪"）
    # 低置信度条目中的山
    '仙闾',    # 仙闾山（泰山附近）
    '太室',    # 太室山 = 嵩山别名
    '敦物',    # 《禹贡》敦物山
    '鸿',      # 四大冢之一（"四大冢鸿、岐、吴、岳"）
    '岳',      # 吴岳/四大冢中"岳"
    '岐',      # 岐山（已有，但 "四大冢岐" 单字需保险）
    '吴岳', '鸿冢', '渎山', '汶山',
    '衰山', '薄山',
    '甘',      # 甘山（又"大战于甘"，夏启 vs 有扈氏战场）—— 兼城邑性质
    '九疑',    # 九疑山（舜葬地）
    '封',      # "封"可能指 封山
    '赤丽',    # 秦赵战场（可能 山地名）
    '庞',      # 庞山
    '封龙',    # 封龙山
    '太山',    # = 泰山别写
}

# 关隘
EXPLICIT_PASS = {
    '函谷', '函谷关', '武关', '散关', '萧关', '阳关', '峣关', '榆关', '井陉',
    '井陉口', '蒲关', '潼关', '雁门关', '句注', '句注塞', '飞狐', '飞狐口',
    '崤', '崤函', '殽', '殽塞',
    # 其他关隘
    '殽函', '殽厄',
    '寻陕',            # 陷寻陕（南越关口）
    '蜚狐',            # = 飞狐
}

# 建筑（宫殿/台阁/祠庙）
EXPLICIT_BUILDING = {
    '阿房', '阿房宫', '长乐', '长乐宫', '未央', '未央宫', '建章', '建章宫',
    '明堂', '辟雍', '灵台', '章华', '章华台', '姑苏', '姑苏台',
    '高庙', '太庙', '明光', '甘泉',
    # 市集/门阙/官署（长安/上林周边）
    '东市', '西市',
    '东朝',            # 长乐宫别称
    '东都门', '横城门', '禁门',
    '玉堂', '璧门', '虎圈', '清室', '宣室', '宣房', '宣曲',
    '太学', '文祖',    # 学宫/祖庙
    '五城十二楼',
    '明廷',           # 明廷 = 甘泉
    '元英',           # 燕宫
    '广成传',         # 客馆
    '永卷',           # 宫内室
    '唐中', '瓠口',    # 上林苑/渭水口附近建筑
    '仓府',
    # 城门（城X / X门 特定）
    '北门', '南门', '皇门', '寒门', '石门', '子驹之门',
    '东南郊', '南郊', '东郊', '北郊', '西郊',
    # 城门（更多）
    '夷门',           # 大梁东门
    '吴东门', '碣石门', '横城门', '金马门',
    '雍门', '雷门', '鹿门', '武闱',
    '安陵郭门',
    '五父之衢',       # 已在 SUFFIX 处理，但放这里更强
    # 邸/府/库/仓
    '燕邸', '鲁邸', '齐邸',
    '高府', '郎中府',
    '长乐锺室', '金隄',
    # 祭祀场/明堂
    '社圃', '祊', '脽', '魏脽后土营',
    '石闾', '尼谿田',
    '雍郊',
    # 特殊
    '杜南宜春苑',
    '桑林',            # 上林苑中的桑林
}

# 陵墓（皇陵/诸侯陵）
EXPLICIT_TOMB = {
    '霸陵', '茂陵', '阳陵', '长陵', '杜陵', '平陵',
    '骊山陵', '始皇陵',
    # 秦先王葬地 / 汉初陵墓
    '西垂', '西山',             # 秦先祖葬地
    '衙', '嶓冢', '鸿冢',
    '义里丘', '栎圉氏', '嚣圉', '弟圉', '陵圉', '宣阳聚', '雍平阳',
    '公陵', '南陵', '永陵', '寿陵',
    '郦邑',                      # 骊邑 = 秦昭王葬
    '高门',                      # 葬高门
}

# ─── 后缀规则（按优先级排序，先匹配更长后缀）───
# (suffix, category, exclusion_list)
SUFFIX_RULES = [
    # 三字及以上特殊
    ('之野',    '原野'),   # 阪泉之野 / 涿鹿之野 / 苍梧之野 = 平野/战场（非水体）
    ('之丘',    '城邑'),   # 轩辕之丘/句窦之丘 = 古邑
    ('之塞',    '关隘'),
    ('之塘',    '水域'),
    ('之墟',    '城邑'),   # 有娀之墟/少昊之墟 = 古城遗址
    ('之虚',    '城邑'),
    ('之阿',    '山脉'),   # 涿鹿之阿 = 山坳
    ('之浦',    '水域'),   # 三渚之浦 / 洲淤之浦
    ('之衢',    '道桥'),   # 五父之衢
    ('之阙',    '建筑'),
    ('之门',    '建筑'),
    # 二字后缀
    ('江水',    '水域'),
    # 一字后缀：水体
    ('水',      '水域'),
    ('河',      '水域'),
    ('江',      '水域'),
    ('川',      '水域'),
    ('渎',      '水域'),
    ('泽',      '水域'),
    ('陂',      '水域'),
    ('池',      '水域'),
    ('湖',      '水域'),
    ('渊',      '水域'),
    # 山岳
    ('山',      '山脉'),
    ('岳',      '山脉'),
    ('岭',      '山脉'),
    ('峰',      '山脉'),
    # 运河/河口（渠=人工河, 汭=河口）
    ('渠',      '水域'),
    ('汭',      '水域'),
    ('滨',      '水域'),   # 河滨/水滨
    ('源',      '水域'),   # 河源
    ('穴',      '山脉'),   # 禹穴（山洞）
    # 海洋并入水域
    ('海',      '水域'),
    # 原野（"X之野"/"X野"作为平野/战场）
    ('之野',    '原野'),
    ('野',      '原野'),
    # 土丘/遗迹 → 城邑 或 山脉
    ('虚',      '城邑'),   # 殷虚/夏虚/有山氏（X氏虚）
    ('墟',      '城邑'),
    ('阪',      '山脉'),   # 咸阳北阪/湛阪
    ('阜',      '山脉'),   # 堂阜
    ('谿',      '水域'),   # 堂谿/乾谿（gorge 常有水）
    # 关隘
    ('关',      '关隘'),
    ('塞',      '关隘'),
    # 行政
    ('郡',      '郡'),
    ('州',      '州'),
    ('县',      '县'),
    # 聚落
    ('邑',      '城邑'),
    ('城',      '城邑'),
    ('都',      '城邑'),
    # "X阳"/"X阴" 极高概率为城邑（古地名命名规律：山南水北曰阳）
    ('阳',      '城邑'),
    ('阴',      '城邑'),
    # "X丘" 上古先秦多为邑名（商丘/楚丘/陶丘/营丘/沙丘/帝丘）
    ('丘',      '城邑'),
    # "X武"/"X成"/"X安"/"X平"/"X梁" 史记中多为城邑
    ('武',      '城邑'),
    ('成',      '城邑'),
    ('安',      '城邑'),
    ('平',      '城邑'),
    ('梁',      '城邑'),
    # 建筑
    ('宫',      '建筑'),
    ('殿',      '建筑'),
    ('台',      '建筑'),
    ('榭',      '建筑'),
    ('阙',      '建筑'),
    ('观',      '建筑'),
    ('庙',      '建筑'),
    ('祠',      '建筑'),
    ('园',      '建筑'),
    ('畤',      '建筑'),    # 祭祀坛
    ('寝',      '建筑'),    # 宗庙后寝
    ('社',      '建筑'),    # 土地神坛
    # 陵墓（作为"X冢"）
    ('冢',      '陵墓'),
    # 道桥津
    ('道',      '道桥'),
    ('桥',      '道桥'),
    ('津',      '道桥'),
    ('渡',      '道桥'),
    ('邮',      '道桥'),    # 驿站（如 邛邮）
    # 乡里亭
    ('乡',      '乡里'),
    ('里',      '乡里'),
    ('亭',      '乡里'),
]

# 单字古邑/县（多为春秋战国古邑，秦汉后部分仍为县）
# 仅作为 '城邑' 的显式清单，不强制为县（县由 L2.5 处理）
EXPLICIT_ANCIENT_CITY = {
    # 郑/卫/陈/宋 等古邑
    '匡', '宿', '屯', '翼', '棠', '祁', '纶', '应', '张', '圉', '硃',
    '甘', '毕', '耿', '彤', '管', '条', '梅', '敖', '邽', '巢',
    '郕', '郩', '郰', '郈', '郭', '郏', '邠', '祝',
    '沈', '纪', '肸', '菑', '菟裘', '郁郅', '鄙衍', '鄜衍',
    '鄪', '酅', '郏鄏', '首垣', '首止', '须如',
    '注', '注人', '氾', '邘', '邰', '邺', '马服',
    '隆', '陵', '陉', '陉廷', '陉氏',
    '越', '胡', '种', '玄', '硰石', '骀', '霍人',
    '许田', '干隧', '干遂',
    '成周', '景亳', '宗周',    # 古都
    '番吾', '昌壮', '平与', '平氏', '庐柳',
    '豳', '负夏', '负尾', '湛阪', '山阳',
    '宁秦', '戎蛮',
    # 战场/行军地
    '嬴下', '平与', '武彊', '武林',
    '宛叶', '兹方', '圉', '刚寿',
    '五鹿', '下辩', '下黄', '上原', '上假密',
    '乐徐', '临济', '城颍', '博浪沙', '博狼沙',
    '衍氏', '盐浦', '雍林',
    '京索',
    '西丞', '西雍', '西蜀',
    '泰卷', '泰卷陶',
    # 单字地名（明显城邑）
    '卢', '芒', '皋', '蕞', '棠', '邽', '巢',
    '纪', '条', '越',
    # 汉初地名
    '燕邸', '鲁邸', '齐邸',    # 已在 building
    '金马门',                   # 已在 building
    '长乐锺室',
    '白登',            # 白登山（匈奴围处）
    '雍林',
    '犬丘', '西犬丘',
    '回中',             # 回中道（可归道桥，但这里归城邑安全）
    '成皋玉门',        # 玉门是城门
    '祋祤',
    '离碓', '灵轵',    # 水利所在地
    '金隄',
    # 残余单字/两字古邑
    '不羹', '东莒', '伊庐', '南阳杜衍', '夷维', '宛朐',
    '密', '居鄛', '斄', '朐界', '惮狐', '江乘', '砀鲁',
    '甬东', '蜀犍为', '覃怀', '达巷党', '防', '阳人',
    '颍', '颍上', '鲁甸', '鹿上', '黾', '茅', '葭萌',
    '葛孽', '籍柯', '蒲泥', '稷下', '窳浑', '符离', '高栎',
    '韩原', '石章', '石阿', '万里沙', '石纽', '沛谷',
    '垂涉', '先俞', '巠分', '欧代', '纲寿', '太湟', '针巫氏',
    # 邛邮 / 胜母 / 俞 / 葭萌 / 城南（复合）/ 旸谷 / 昧谷 — 多数算城邑
    '邛邮', '胜母', '俞', '城南', '旸谷', '昧谷',
    '三澨',                   # 三澨水（可归水域，但作为城邑地也合理；先归 city 安全）
    '霸渭',                   # 霸水+渭水之间
    '复雠',                   # 楚之粟仓并列"复雠、庞、长沙"
    # 低置信度补录的古邑
    '城皋', '蒲坂', '蒲反', '蒲惣',   # 蒲坂系列（蒲津渡之地）
    '践土',   # 春秋晋文公会盟地
    '郭狼',   # 赵地
    '鄱',     # 鄱阳县前身
    '龙兑',   # 代郡地
    '下雉', '阐',   # 史记所见邑
    '新垣', '平舒', '少曲',   # 魏赵战国地
    '汾门',   # 汾水关口
    '王垣', '首垣',
    '寿', '常', '聊', '葛', '甯', '衍', '阳晋',
    '宗胡',   # 楚地
    '有诡', '氏篸', '河雍', '橑杨',  # 战国散见邑名
    '长榆',   # 关/榆塞
    '英',     # 英氏国/英邑
    '孤',     # 孤竹之简？单作邑
    '厓',     # 厓（战国邑）
    '駹',     # 冉駹
    '僰',     # 僰道
    '长门',   # 长门宫之外也有"长门"县？实际多为宫
    # 陵系列 — 多为陵邑/封邑（非陵墓）
    '东陵', '信陵', '幽陵', '景陵', '肥陵', '薛陵', '防陵', '竟泽陵',
    # 其他
    '龙',     # 龙城/龙县
    '首',     # 首阳
    # 江乘/甬东 等
}


# 汉代诸侯王国（与郡同级的王国，规则：要么算郡，要么算国家）
# 用户约定：诸侯国不应归为县或城邑。此处默认归"郡"（与郡同级的行政区）。
HAN_VASSAL_KINGDOMS = {
    '楚国', '齐国', '赵国', '燕国', '代国', '梁国', '吴国',
    '淮南国', '淮阳国', '衡山国', '济北国', '济南国', '菑川国',
    '胶东国', '胶西国', '长沙国', '河间国', '常山国', '中山国',
    '鲁国', '广川国', '清河国', '信都国', '琅邪国', '东平国',
    '济阳国', '平原国', '城阳国', '广阳国', '汝南国', '泗水国',
    '渤海国', '沛国', '真定国', '广平国', '高密国', '陈国',
    '郑国', '晋国', '昌国', '安国', '充国',
    # 史记中出现的小国/诸侯国
    '东国', '南国', '北国', '西国', '耆国',
}


# 已知汉代县名（参考《汉书·地理志》与《史记》常见县名）
# 这些地名常以"城邑"形式出现，但实际为汉代县级行政区；
# 规则：若主分类为"城邑"且在此集合中，改判为"县"。
# 注：大都会（长安、洛阳等）虽也是县，但其作为"都会城市"属性更强，仍归"城邑"。
KNOWN_HAN_XIAN = {
    # 著名都会——虽以都邑著称，但在汉代皆为县级（含汉书别名）
    '长安', '洛阳', '雒阳', '咸阳', '成都', '临淄', '临菑',
    '大梁', '浚仪', '邯郸', '蓟', '宛', '寿春', '彭城',
    '定陶', '睢阳', '番禺',
    # 单字地名（三家注明确指 X县/X邑）
    '阿',    # 齐之东阿 (徐广: "阿者，今之东阿")
    '甄',    # 齐之甄城
    '鄄',    # 卫之鄄城
    # 秦汉典型县名（补充）
    '桂林',  # 秦桂林郡下的郡名地，但实际多出现作为"郡"context，归郡更准
    '符离', '江乘', '葭萌', '窳浑', '覃怀',
    '瑕丘',
    # 沛郡一带（刘邦起家）
    '丰', '沛', '砀', '萧', '相', '栗', '留', '戚', '单父', '成武',
    # 东郡/东海/陈留等
    '外黄', '下邳', '彭城', '定陶', '睢阳', '寿春', '阳武', '新郑', '荥阳',
    '陈留', '扶沟', '浚仪', '阳夏', '苦', '柘', '铚', '陈', '蔡', '胡陵',
    # 齐鲁一带
    '曲阜', '邹', '鲁', '薛', '滕', '任', '乘氏', '瑕丘',
    '即墨', '高宛', '临朐', '博', '博阳', '黄', '腄', '芝罘',
    '莒', '胶东', '历下',
    # 三河/关中
    '阳翟', '历阳', '酂', '襄城', '共', '汲', '酸枣', '修武', '脩武',
    '温', '轵', '轵道', '黾池', '渑池', '陕', '河津', '解', '安邑',
    '舞阳', '期思', '鄂', '南阳',
    # 南方
    '江陵', '鄢', '西陵', '夷陵', '夷道',
    # 燕赵
    '蓟', '容城', '涿', '范阳', '易', '督亢',
    '巨鹿', '钜鹿', '武安', '常山', '元氏', '赵平', '中牟',
    # 晋地
    '狄道', '肤施', '壶关',
    # 其他散见侯国/县
    '高祖', '高阳', '穰', '蓝田', '朝那', '云阳', '阳周',
    '阳城', '城父', '襄陵', '濮阳', '聊城', '蕲', '谷阳',
    '夏阳', '频阳', '宜春', '中阳', '东阳', '武关', '临晋',
    '櫟阳', '栎阳', '栎', '废丘', '雍',
}


# 已知秦汉郡名（不带"郡"后缀也算郡）
KNOWN_COMMANDERIES = {
    '大宋', '方与',   # "魏之东外…大宋、方与二郡" (040_楚世家)
    # 秦 36 郡及汉代郡名（部分，逐步补充）
    '内史', '京兆', '左冯翊', '右扶风',
    '陇西', '北地', '上郡', '汉中', '蜀郡', '巴郡', '黔中', '南郡', '南阳',
    '长沙', '九江', '泗水', '薛郡', '东海', '会稽', '闽中',
    '砀郡', '颍川', '陈郡', '三川', '东郡', '上党', '邯郸', '钜鹿', '巨鹿',
    '太原', '云中', '雁门', '代郡', '九原', '上谷', '渔阳', '右北平',
    '辽西', '辽东', '河东', '河内', '河南', '东海郡',
    '齐郡', '临淄', '胶东', '胶西', '济南', '济北', '城阳', '琅邪', '琅琊',
    '弘农', '武威', '张掖', '酒泉', '敦煌',
    '珠崖', '儋耳', '交趾', '合浦',
}


# 侯者年表章节：绝大多数 place 引用为汉代侯国（= 县级行政区）
HOUZHE_CHAPTERS = {'018', '019', '020', '021'}
HOUZHE_MAJORITY = 0.5   # refs 中 ≥50% 落在侯者年表即判为县
HOUZHE_MIN_REFS = 1     # 单条 ref 命中侯者年表也算（大量冷僻侯国只在年表出现一次）


def _houzhe_ratio(refs):
    """返回 refs 中命中侯者年表章节的比例；refs 为空返回 0。
    chapter_id 形如 '018_高祖功臣侯者年表'，取前 3 位数字匹配。
    """
    if not refs:
        return 0.0
    hit = 0
    for r in refs:
        chap = r[0] if isinstance(r, (list, tuple)) else None
        if isinstance(chap, str) and chap[:3] in HOUZHE_CHAPTERS:
            hit += 1
    return hit / len(refs)


# ─── L3: 动词/共现词上下文规则 ───
#
# 扫描 chapter_md/*.tagged.md，统计每个 place 出现时的前后文模式，
# 为每个 place 累计 {category: hit_count}。
#
# 每条规则以 (正则, 类别, 最小命中数, 描述) 表示。
# 正则必须含一个捕获组（匹配地名原文，含消歧后缀如 "台|吕台"）。

CONTEXT_PATTERNS = [
    # 定都 → 城邑
    (r'(?:都|徙都|建都|定都|居)〖=([^〖〗\n]+)〗',    '城邑', 1, '都X/徙都X'),
    # 修筑城邑 → 城邑
    (r'(?:城|筑)〖=([^〖〗\n]+)〗',                    '城邑', 1, '城X/筑X'),
    # 渡水 → 河湖
    (r'(?:渡|济|涉|临|溯|游)〖=([^〖〗\n]+)〗',        '水域', 1, '渡/济/涉/临X'),
    # 登山 → 山脉（"上X" 歧义过大：既可登山也可溯水，故剔除）
    (r'(?:登|陟|望)〖=([^〖〗\n]+)〗',                  '山脉', 1, '登/陟/望X'),
    # 水运 → 水域（"漕/行船/浮/溯" + X 指水）
    (r'(?:漕|行船|浮|溯|泛舟|顺流|通)〖=([^〖〗\n]+)〗', '水域', 1, '漕/行船/浮/溯X'),
    # "漕从X" / "漕从…X" 多是水
    (r'漕[^。，\n]{0,10}?〖=([^〖〗\n]+)〗',             '水域', 1, '漕…X'),
    # X 通 (某水) → X 也是水
    (r'〖=([^〖〗\n]+)〗通(?:〖=[^〖〗\n]+〗|[^。，\n]{0,5}?(?:水|江|河|海))',
                                                       '水域', 1, 'X通水'),
    # 封禅 → 山脉（禅总是对山；"封X禅Y" 中 X 也是山）
    (r'禅(?:于|乎)?〖=([^〖〗\n]+)〗',                   '山脉', 1, '禅X'),
    (r'〖\^禅〗〖=([^〖〗\n]+)〗',                        '山脉', 1, '〖^禅〗X'),
    (r'登封〖=([^〖〗\n]+)〗',                           '山脉', 1, '登封X'),
    # 侯国名：〖=X〗侯/〖=X〗戴侯 等 → 县
    # 避免误匹配 "X侯国"（已属县），匹配 "X侯" 后紧接非"国"字符
    (r'〖=([^〖〗\n]+)〗(?:戴|康|懿|庄|哀|敬|文|武|孝|献|节|恭|简|共|平|穆|惠|景|成|桓|灵|元|宣|昭|襄|僖|悼|殇|幽|厉|愍|殷)?侯(?!国)',
                                                        '县',   1, 'X(谥)侯'),
    # "封为 X 侯" —— 更强的信号
    (r'封[^。，；\n]{0,20}为〖=([^〖〗\n]+)〗侯',        '县',   1, '封为X侯'),
    # 郡治 → 郡
    (r'(?:治)〖=([^〖〗\n]+)〗',                         '郡',   1, '治X (郡治)'),
    # 下葬 → 陵墓/城邑（陵墓信号较弱，作为附加线索）
    (r'葬(?:于)?〖=([^〖〗\n]+)〗',                      '陵墓', 1, '葬X/葬于X'),
    # 官职+守：X太守 → X 是郡
    (r'〖=([^〖〗\n]+)〗〖;[^〖〗]*?太守',                '郡',   1, 'X太守'),
    # "X郡" 或 "X、Y二郡" / "X、Y三郡"：X 为郡（仅捕获第一个，peer 会扩散）
    (r'〖=([^〖〗\n]+)〗郡',                              '郡',   1, 'X郡（直称）'),
    (r'〖=([^〖〗\n]+)〗(?:、〖=[^〖〗\n]+〗){1,4}\s*(?:二|三|四|五|六|七|八)郡',
                                                        '郡',   1, 'X、Y…二(三)郡'),
    # 军事攻取：攻/取/拔/降/入/袭/围/屠/破/略/徇/下 X → 城邑（弱）
    (r'(?:攻|取|拔|降|入|袭|围|屠|破|略|徇|下|克|陷|定|复|略)〖=([^〖〗\n]+)〗',
                                                        '城邑', 2, '军事攻取X'),
    # 诸侯会盟地 → 城邑
    (r'(?:会|盟|会于|会於|盟于|盟於)〖=([^〖〗\n]+)〗',   '城邑', 1, '会/盟X'),
    # 割让/献纳 → 城邑（土地）
    (r'(?:献|割|予|予以|赐|纳)〖=([^〖〗\n]+)〗',        '城邑', 1, '献/割X'),
    # 封邑 → 县（封地）
    (r'封[^。\n]{0,10}?[于於]〖=([^〖〗\n]+)〗',         '县',   1, '封…于X'),
    # 越过：逾/越 → 山脉
    (r'(?:逾|越|过|度)〖=([^〖〗\n]+)〗(?:山|岭|岳|关)?', '山脉', 2, '逾/越X'),
    # 迁徙/迁都 → 城邑
    (r'(?:迁|徙|迁於|徙於|迁于|徙于)[^。\n]{0,6}?〖=([^〖〗\n]+)〗',
                                                        '城邑', 1, '迁/徙X'),
    # 战败/战胜地 → 城邑
    (r'(?:败|战|战于|战於|战败)[^。\n]{0,8}?〖=([^〖〗\n]+)〗',
                                                        '城邑', 2, '战于X'),
    # 军驻地 → 城邑
    (r'(?:军|驻)〖=([^〖〗\n]+)〗',                      '城邑', 1, '军X'),
    # 行军目的地：至/过/经 X → 城邑（弱，需要多次命中）
    (r'(?:至|过|经|次|趋)〖=([^〖〗\n]+)〗',             '城邑', 2, '至/过X'),
    # 附加名词：X之战 → 弱（X 多为城邑/原野）
    (r'〖=([^〖〗\n]+)〗之(?:战|役)',                    '城邑', 1, 'X之战'),
    # 附加名词：X之野 → 原野（后缀规则已覆盖"X之野"一体词，但这里是"〖=X〗之野"）
    (r'〖=([^〖〗\n]+)〗之野',                           '原野', 1, 'X之野（分离）'),
    # 附加名词：X之山 → 山脉
    (r'〖=([^〖〗\n]+)〗之山',                           '山脉', 1, 'X之山'),
    # 附加名词：X之水 → 水域
    (r'〖=([^〖〗\n]+)〗之水',                           '水域', 1, 'X之水'),
    # 附加名词：X之国 → 国家
    (r'〖=([^〖〗\n]+)〗之国',                           '国家', 1, 'X之国'),
    # 附加名词：X之民/X之人 → 区域
    (r'〖=([^〖〗\n]+)〗之(?:民|人|俗)',                 '区域', 1, 'X之民/人'),
    # 附加名词：X之郊 → 城邑（X是城邑，近郊）
    (r'〖=([^〖〗\n]+)〗之郊',                           '城邑', 1, 'X之郊'),
    # X城 → 城邑（X是城名）
    (r'〖=([^〖〗\n]+)〗城(?:中|下|上)?',                '城邑', 2, 'X城'),
    # "故X" 前置：故地/故国 泛指（弱，略）
]


def _strip_disambig(raw: str) -> str:
    """消歧语法：'台|吕台' → '吕台'；无 | 时返回原样"""
    if '|' in raw:
        return raw.split('|', 1)[1].strip()
    return raw.strip()


def build_context_hints(place_names):
    """扫描所有 chapter_md，为每个 place 累积上下文类别票数。
    返回 {name: {category: hit_count}}"""
    hints = defaultdict(lambda: defaultdict(int))
    name_set = set(place_names)
    # 并列郡名：〖=X〗、〖=Y〗(…)?\s*(?:二|三|四|五|六)郡 → 列表中所有项都是郡
    MULTI_JUN_RE = re.compile(
        r'(〖=[^〖〗\n]+〗(?:、〖=[^〖〗\n]+〗){1,4})\s*(?:二|三|四|五|六|七|八)?郡'
    )
    NAME_RE = re.compile(r'〖=([^〖〗\n]+)〗')
    for chap_file in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        try:
            content = chap_file.read_text(encoding='utf-8')
        except Exception:
            continue
        # 常规模式
        for pat, cat, _min_hits, _desc in CONTEXT_PATTERNS:
            for m in re.finditer(pat, content):
                name = _strip_disambig(m.group(1))
                if name in name_set:
                    hints[name][cat] += 1
        # 特殊：并列郡名（所有列表成员都为郡，票数权重 2）
        for m in MULTI_JUN_RE.finditer(content):
            for nm in NAME_RE.findall(m.group(1)):
                name = _strip_disambig(nm)
                if name in name_set:
                    hints[name]['郡'] += 2
    return hints


# ─── L4: 三家注（集解/索隐/正义）注释线索 ───
# 扫描裴駰集解、司马贞索隐、张守节正义的注释文本，
# 匹配 "X，Y名" 格式的类型声明，作为 L3 hints 的补充票数。
# 例："涿鹿，山名" → 涿鹿 累计一票 山脉

SANJIA_PATTERNS = [
    # 先匹配两字及以上的更具体类型
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*山\s*名',     '山脉'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*湖\s*名',     '水域'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*水\s*名',     '水域'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*泽\s*名',     '水域'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*海\s*名',     '水域'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*县\s*名',     '县'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*郡\s*名',     '郡'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*乡\s*名',     '乡里'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*亭\s*名',     '乡里'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*邑\s*名',     '城邑'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*关\s*名',     '关隘'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*塞\s*名',     '关隘'),
    (r'([\u4e00-\u9fa5]{1,5})(?:者)?[，,]\s*国\s*名',     '国家'),
    # 一些强模式：X 在 Y县 → X 是 县（把 X 定位到某县）—— 略
    # "X城在Y县" 等暂不处理，因为"城"未必等同 X 类别
]


def build_sanjia_hints(place_names):
    """扫描三家注文本，抽取 "X，Y名" 模式，累积 place 类别线索。
    返回 {name: {category: hit_count}}"""
    if not SANJIA_FILE.exists():
        return {}
    try:
        text = SANJIA_FILE.read_text(encoding='utf-8')
    except Exception:
        return {}
    hints = defaultdict(lambda: defaultdict(int))
    name_set = set(place_names)
    for pat, cat in SANJIA_PATTERNS:
        for m in re.finditer(pat, text):
            name = m.group(1)
            if name in name_set:
                hints[name][cat] += 1
    return hints


# ─── L5: 并列地名传播 ───
# 规则：在正文中相邻并列出现的地名（〖=X〗、〖=Y〗、〖=Z〗...）通常属于同一类别，
# 例如"攻〖=铚〗、〖=酂〗、〖=苦〗、〖=柘〗"—— 都是被攻取的县。
# 从已分类的"邻居"向未分类项传播。

PEER_TAG_RE = re.compile(r'〖=([^〖〗\n]+)〗')
# peer 分隔符：仅使用顿号 "、"（古文列举号）。
#   逗号 "，" 通常表示更长的停顿/子句边界，跨逗号的并列不可靠，排除之。
#   "与/及/和/或" 作为弱连接，也排除。
PEER_SEP_RE = re.compile(r'\s*、\s*')


def build_peer_groups(name_set):
    """扫描 chapter_md，提取相邻并列的 place 列表（长度≥2）。
    判断"并列"：两个相邻 〖=X〗 tag 之间只有"、"或"，"（可含空白）即视为同列。
    返回 [[name, ...], ...]。"""
    groups = []
    for chap_file in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        try:
            content = chap_file.read_text(encoding='utf-8')
        except Exception:
            continue
        matches = list(PEER_TAG_RE.finditer(content))
        if len(matches) < 2:
            continue
        i = 0
        while i < len(matches):
            run = [_strip_disambig(matches[i].group(1))]
            j = i
            while j + 1 < len(matches):
                between = content[matches[j].end():matches[j+1].start()]
                if PEER_SEP_RE.fullmatch(between):
                    run.append(_strip_disambig(matches[j+1].group(1)))
                    j += 1
                else:
                    break
            if len(run) >= 2:
                valid = [nm for nm in run if nm in name_set]
                if len(valid) >= 2:
                    groups.append(valid)
            i = j + 1
    return groups


def propagate_peer_categories(result, groups, max_rounds=3, majority=0.6):
    """根据同列地名传播类别。仅填充当前为空字符串的条目。
    返回本次总更新数。"""
    peer_map = defaultdict(set)
    for g in groups:
        for n in g:
            peer_map[n].update(g)

    total_updates = 0
    for _ in range(max_rounds):
        updated = 0
        for name, peers in peer_map.items():
            if result.get(name):
                continue  # 已分类，尊重先前结果
            counter = Counter()
            for p in peers:
                if p == name:
                    continue
                pc = result.get(p)
                if pc:
                    counter[pc] += 1
            if not counter:
                continue
            best_cat, best_n = counter.most_common(1)[0]
            if best_n / sum(counter.values()) >= majority:
                result[name] = best_cat
                updated += 1
        total_updates += updated
        if updated == 0:
            break
    return total_updates


def infer_from_hints(hints_for_name, primary):
    """根据上下文投票推断类别。primary 为空或'城邑'时才考虑覆盖。
    返回 (推断类别, 命中数) 或 (None, 0)。"""
    if not hints_for_name:
        return None, 0
    # 排除与 primary 相同的类别（无需更新）
    items = [(c, n) for c, n in hints_for_name.items() if c]
    if not items:
        return None, 0
    items.sort(key=lambda x: -x[1])
    best_cat, best_n = items[0]
    total = sum(n for _, n in items)
    # 要求主导类别票数占比 >= 60%
    if best_n / total < 0.6:
        return None, 0
    # 首选类别与主分类相同 → 无需推断
    if best_cat == primary:
        return None, 0
    return best_cat, best_n


def classify(name: str, refs=None, hints=None) -> str:
    """对单个地名分类。refs: entity_index 中的 [[chapter_id, para], ...]"""
    # L1: 显式清单
    # 顺序策略：
    #   - 误标最先（不再继续处理）
    #   - 区域/水域/原野/山脉/关隘/建筑/陵墓 等自然/功能类优先
    #   - 行政类（郡/县）先于"国家"（用户约定：若可归郡或国家，优先郡）
    if name in EXPLICIT_NON_PLACE:
        return '误标'
    if name in EXPLICIT_FICTIONAL:
        return '虚构'
    if name in EXPLICIT_REGION:
        return '区域'
    if name in EXPLICIT_WATER:
        return '水域'
    if name in EXPLICIT_PLAIN:
        return '原野'
    if name in EXPLICIT_MOUNTAIN:
        return '山脉'
    if name in EXPLICIT_PASS:
        return '关隘'
    if name in EXPLICIT_BUILDING:
        return '建筑'
    if name in EXPLICIT_TOMB:
        return '陵墓'
    # 郡优先于国家（用户约定）
    if name in KNOWN_COMMANDERIES or name in HANSHU_JUN:
        return '郡'
    if name in HAN_VASSAL_KINGDOMS:
        return '郡'
    # 国家置于郡之后
    if name in EXPLICIT_NATION:
        return '国家'
    # 单字古邑：置于后，让 L2/L2.5 的县规则优先（不少已成汉县）
    if name in EXPLICIT_ANCIENT_CITY:
        return '城邑'

    # L4: 后缀启发式（先跑一遍，拿到初步类别）
    primary = ''
    if name.endswith('陵') and len(name) >= 2:
        primary = '城邑'
    else:
        for suf, cat in SUFFIX_RULES:
            if name.endswith(suf) and len(name) > len(suf):
                primary = cat
                break
            if name == suf and cat:
                primary = cat
                break

    # L2: 章节上下文（侯者年表）
    # 条件：refs 以侯者年表为主，且初步类别为空/城邑（弱类别），改判为县
    if refs and len(refs) >= HOUZHE_MIN_REFS:
        if _houzhe_ratio(refs) >= HOUZHE_MAJORITY:
            if primary in ('', '城邑'):
                return '县'

    # L2.5: 汉代县名白名单
    # 已知为汉代县的名字（KNOWN_HAN_XIAN 为手工精选 + HANSHU_XIAN 为地理志自动提取），
    # 若主分类为空或城邑，升级为县
    if primary in ('', '城邑') and (name in KNOWN_HAN_XIAN or name in HANSHU_XIAN):
        return '县'

    # L3: 动词/共现上下文（弱于 L2，强于"空"）
    # 仅在 primary 为空或"城邑"时考虑覆盖
    if hints is not None and primary in ('', '城邑'):
        name_hints = hints.get(name, {})
        inferred, _hits = infer_from_hints(name_hints, primary)
        if inferred:
            # 保护逻辑：不让 L3 推翻强类别（后缀规则已给出明确的非 primary 弱类别）
            # primary 为空时直接采用；primary 为城邑时，只接受 河湖/山脉/关隘/建筑/陵墓/郡/县 这类更具体的类别
            if primary == '':
                return inferred
            SPECIFIC_OVERRIDE = {'水域', '山脉', '关隘', '建筑', '陵墓', '郡', '县', '国家', '州', '区域'}
            if inferred in SPECIFIC_OVERRIDE:
                return inferred

    return primary


# ─── 可拆分复合地名检测 ───
# 如"新丰鸿门" = 新丰 + 鸿门（两个独立地名连写）。
# 若一个 place 名可以切分为 ≥2 个已知 place 名的连接，标记为"待拆分"
# 并把各子串的类别作为该复合地名的类别来源。

def split_into_known_places(name, known_set):
    """贪心+最长匹配把 name 切分为 ≥2 个已知 place。
    成功返回 [part1, part2, ...]；失败返回 None。
    约束：
      - 每个子串必须 ≥ 2 字（避免"函谷关"被拆为"函谷+关"这种1字尾缀误判）
      - 子串不能等于 name 本身
    """
    if len(name) < 4:
        return None
    parts = []
    i = 0
    while i < len(name):
        found = False
        for j in range(len(name), i + 1, -1):  # j > i+1，保证子串 ≥ 2 字
            sub = name[i:j]
            if sub == name:
                continue
            if sub in known_set:
                parts.append(sub)
                i = j
                found = True
                break
        if not found:
            return None
    if len(parts) >= 2:
        return parts
    return None


# ─── 多标签支持 ───
# 一个地名可能在不同篇章/上下文中指代不同实体（典型：单字"阿"在不同章节
# 既指齐之东阿，也指阿房宫；单字"河"主要是黄河但也可能指其他河流）。
# 本函数在 primary 之外，收集其它"次要但可靠"的分类线索，产出一个类别列表。
def collect_all_categories(name, primary, refs, hints, split_inherit=None):
    """返回 (primary, [secondary, ...]) 的所有类别列表；primary 首位。
    去重、保序。secondary 要求证据足够强：
      - 出现在其它 EXPLICIT_* 白名单中（即显式判过至少两种类别）
      - 或 hints 中某非 primary 类别累计票数 ≥ 2
    """
    cats = []
    if primary:
        cats.append(primary)

    # 1) 多 EXPLICIT 命中（同一 name 出现在多个白名单）
    explicit_matches = []
    if name in EXPLICIT_REGION: explicit_matches.append('区域')
    if name in EXPLICIT_WATER:  explicit_matches.append('水域')
    if name in EXPLICIT_PLAIN:  explicit_matches.append('原野')
    if name in EXPLICIT_MOUNTAIN: explicit_matches.append('山脉')
    if name in EXPLICIT_PASS:   explicit_matches.append('关隘')
    if name in EXPLICIT_BUILDING: explicit_matches.append('建筑')
    if name in EXPLICIT_TOMB:   explicit_matches.append('陵墓')
    if name in EXPLICIT_NATION: explicit_matches.append('国家')
    if name in KNOWN_COMMANDERIES or name in HANSHU_JUN: explicit_matches.append('郡')
    if name in HAN_VASSAL_KINGDOMS: explicit_matches.append('郡')
    if name in KNOWN_HAN_XIAN or name in HANSHU_XIAN: explicit_matches.append('县')
    for c in explicit_matches:
        if c not in cats:
            cats.append(c)

    # 2) hints 中支持 ≥ 2 的其它类别（排除已在 cats 中的）
    if hints is not None:
        name_hints = hints.get(name, {})
        for cat, n in name_hints.items():
            if cat and n >= 2 and cat not in cats:
                cats.append(cat)

    # 3) 可拆分复合地名：继承子串的类别 + "待拆分"标记
    if split_inherit:
        for c in split_inherit:
            if c and c not in cats:
                cats.append(c)
        if '待拆分' not in cats:
            cats.append('待拆分')

    return cats


def main():
    with open(INDEX_JSON, encoding='utf-8') as f:
        data = json.load(f)
    places = data.get('place', {})

    # 先做一次基础分类（L1+L2+L4），找出需要 L3 增强的候选（blank/城邑）
    print('扫描 chapter_md 构建上下文线索...')
    hints = build_context_hints(places.keys())
    hit_total = sum(sum(c.values()) for c in hints.values())
    print(f'  上下文命中 {hit_total} 次，覆盖 {len(hints)} 个 place')

    # 叠加三家注注释线索
    print('扫描三家注注释...')
    sanjia_hints = build_sanjia_hints(places.keys())
    sj_total = sum(sum(c.values()) for c in sanjia_hints.values())
    print(f'  三家注命中 {sj_total} 次，覆盖 {len(sanjia_hints)} 个 place')
    # 合并：同名同类别票数相加
    for name, cats in sanjia_hints.items():
        for cat, n in cats.items():
            hints[name][cat] += n

    # 先生成每个 place 的 primary 分类
    primary_result = {}
    l3_upgrades = 0
    for name, info in places.items():
        refs = info.get('refs') if isinstance(info, dict) else None
        base = classify(name, refs, hints=None)
        final = classify(name, refs, hints=hints)
        if final != base:
            l3_upgrades += 1
        primary_result[name] = final
    print(f'  L3 上下文升级: {l3_upgrades} 个 place')

    # L5: 并列地名传播（仍然在 primary 层进行）
    print('提取并列地名序列并传播类别...')
    peer_groups = build_peer_groups(places.keys())
    print(f'  共发现 {len(peer_groups)} 组并列序列')
    l5_upgrades = propagate_peer_categories(primary_result, peer_groups)
    print(f'  L5 并列传播升级: {l5_upgrades} 个 place')

    # 多标签扩展：为每个 place 收集全部类别（primary 在首位）
    print('扩展多标签（单名多类的条目）...')
    all_names_set = set(places.keys())
    result = {}
    multi_tag_count = 0
    split_count = 0
    for name, info in places.items():
        refs = info.get('refs') if isinstance(info, dict) else None
        primary = primary_result.get(name, '')
        # 可拆分复合地名：继承子串类别 + "待拆分"
        split_parts = split_into_known_places(name, all_names_set)
        split_inherit_cats = []
        if split_parts:
            for p in split_parts:
                sub_cats = result.get(p) or []
                if not sub_cats:
                    # 子串可能还未进 result，回退到 primary_result
                    pc = primary_result.get(p, '')
                    if pc:
                        sub_cats = [pc]
                for c in sub_cats:
                    if c and c != '待拆分' and c not in split_inherit_cats:
                        split_inherit_cats.append(c)
            split_count += 1
        cats = collect_all_categories(name, primary, refs, hints,
                                       split_inherit=split_inherit_cats)
        result[name] = cats
        if len(cats) >= 2:
            multi_tag_count += 1
    print(f'  多标签条目: {multi_tag_count}')
    print(f'  可拆分复合地名（待拆分）: {split_count}')

    # 统计（仅用 primary 计数，用于保持与以前一致的可读性）
    stats = {}
    for v in primary_result.values():
        stats[v] = stats.get(v, 0) + 1

    # 排序：按 primary + 拼音
    result_sorted = dict(sorted(
        result.items(),
        key=lambda kv: ((kv[1][0] if kv[1] else 'zzz'), kv[0])
    ))
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(result_sorted, f, ensure_ascii=False, indent=2)
    total = sum(stats.values())
    uncat = stats.get('', 0)
    print(f'Total places: {total}')
    print(f'Uncategorized (blank): {uncat} ({uncat*100/total:.1f}%)')
    print('Primary category distribution:')
    for cat, n in sorted(stats.items(), key=lambda x: -x[1]):
        label = cat if cat else '(空)'
        print(f'  {label}: {n}')
    print(f'\nWritten: {OUT_JSON}')


if __name__ == '__main__':
    main()
