#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为官职实体生成分类标签（职类）。

完全对照 classify_places.py 的工作流，按 L1-L5 打分：
  L1   显式白名单（三公/九卿/军职/爵位/宫廷/文学/师傅/外邦/上古/泛称）
  L2   章节上下文（侯者年表 → 爵位；匈奴传 → 外邦职）
  L2.5 《汉书·百官公卿表》白名单
  L3   共现动词/上下文（chapter_md 扫描）+ 三家注
  L4   后缀启发式（默认兜底）
  L5   并列官职传播

输出: kg/entities/data/official_categories.json
结构: { canonical_name: [cat, cat, ...] }  # 多标签
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
OUT_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'official_categories.json'
OUT_CONF_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'official_confidence.json'
HANSHU_BAIGUAN = _ROOT / 'kg' / 'entities' / 'data' / 'hanshu_baiguan.json'
SANJIA_FILE = _ROOT / 'corpus' / 'shiji' / '史记集解三家注索隐正义.txt'
CHAPTER_DIR = _ROOT / 'chapter_md'


# ─── 类别常量 ───
CAT_SANGONG  = '三公'
CAT_JIUQING  = '九卿'
CAT_LIQING   = '列卿'
CAT_JUNLI    = '郡国长吏'
CAT_XIANLI   = '县乡吏'
CAT_MILITARY = '军职'
CAT_JUE      = '爵位'
CAT_WANG     = '王号'
CAT_GUJU     = '古爵'
CAT_PALACE   = '宫廷近侍'
CAT_WENXUE   = '文学顾问'
CAT_SHIFU    = '宗师宾傅'
CAT_FOREIGN  = '外邦职'
CAT_ANCIENT  = '上古官'
CAT_GENERIC  = '泛称'
CAT_JIACHEN  = '家臣'
CAT_MIS      = '误标'
CAT_PERSON_MIS = '人名误标'
CAT_IDENTITY_MIS = '身份误标'
CAT_SHIHAO_MIS = '谥号误标'
CAT_NEED_SPLIT = '待拆分'


# ─── 显式白名单 ───

EXPLICIT_SANGONG = {
    '丞相', '相国', '左丞相', '右丞相', '太尉', '御史大夫',
    '司徒', '司马', '司空',
    '大司徒', '大司马', '大司空',
    # 楚官等同宰相
    '令尹', '右尹',  # 楚国宰相级
    '左尹',           # 楚官（副尹）
    # 春秋战国副相
    '上相', '左相', '右相', '中丞相', '左右相', '左右丞相',
}

EXPLICIT_JIUQING = {
    # 简称（史记行文常见）
    '大农',           # 大司农/大农令 简称
    '光禄',           # 光禄勋 简称
    '大鸿',           # 大鸿胪 简称
    '大司寇',         # 古/周官 — 掌刑辟，九卿级
    '羲和',           # 王莽改大司农为羲和（也是上古历官）
    # 奉常/太常
    '奉常', '太常',
    # 郎中令/光禄勋
    '郎中令', '光禄勋',
    # 卫尉
    '卫尉', '长乐卫尉', '长信卫尉',
    # 太仆
    '太仆',
    # 廷尉
    '廷尉', '大理',
    # 典客/大行令/大鸿胪
    '典客', '大行令', '大行', '大鸿胪',
    # 宗正
    '宗正',
    # 治粟内史/大农令/大司农
    '治粟内史', '大农令', '大司农',
    # 少府
    '少府',
}

EXPLICIT_LIQING = {
    '中尉', '执金吾',
    '将作少府', '将作大匠',
    '主爵中尉', '主爵都尉',
    '詹事',
    '内史', '左内史', '右内史',
    '京兆尹', '左冯翊', '右扶风', '右辅',
    '水衡都尉', '水衡',               # 简称
    '中书令', '尚书令',
    '大内',                           # 大内史 简称
    '属国',                           # 典属国 简称
    '大行礼官',                       # 典客/大行令 属官
    '大宫',                           # 内廷宫宰
    '丞相司直', '丞相府',             # 三公属官
    '相府',                           # 相府（丞相/国相官署）
    '锺官',                           # 水衡都尉属 (铸钱)
    '北军钱官',                       # 少府/水衡 属
    '北宫司空命妇',                   # 汉代宫省官
    '上林中都官',                     # 上林苑中都官
    '主铁官', '主计',                 # 少府/大农 属
    '协律', '协声律',                 # 乐府属官
    '左右都司空',                     # 廷尉/少府属
    '诸侯相国',                       # 诸侯王国相（二千石，郡级）— 归列卿级
    # 少府属
    '公车', '公车令',                 # 公车司马令
    '祠祝官',                         # 祭祀官
    # 丞相府属（三公属官）
    '丞相长史', '丞相史', '丞史',
    '中丞',                           # 御史中丞
    # 上林/长安 三辅都尉
    '京辅都尉',                       # 汉三辅都尉
    '协律都尉',                       # 乐府属
    '上林令',                         # 少府/水衡属
    # 卫尉类（列卿级）
    '东西宫卫尉',                     # 长乐/未央宫卫尉
}

EXPLICIT_MILITARY = {
    # 大将/上将
    '大将军', '大将', '上将', '上将军',
    # 柱国（楚官职，春秋战国起）
    '上柱国', '柱国',
    # 司马（军职，春秋各国）
    '左司马', '右司马', '骑司马', '中军司马', '鹰击司马',
    '军司马', '左右司马', '中司马', '车司马',
    # 骑 / 车骑 / 参乘
    '车骑', '参乘', '郎中骑', '常侍骑郎', '骑将', '骑郎',
    '骑', '骠骑', '常侍骑',
    # 偏师 / 次将
    '中军', '上军', '下军', '北军', '南军', '左军', '右军', '前军', '后军',
    '监军', '督将', '中郎', '中军将', '小将',
    # 楼船/贰师/游击 将军简称
    '楼船', '贰师', '游击',
    # 校官
    '大校', '左校', '左右校',
    # 轻车 武骑
    '武骑常侍', '轻车武射',
    # 将率 / 宿卫 / 率 / 队率
    '将率', '宿卫', '率', '队率',
    # 车骑/骠骑
    '车骑将军', '骠骑将军',
    # 前后左右
    '前将军', '后将军', '左将军', '右将军',
    # 将军 / 将
    '将军', '裨将军', '偏将军', '副将军',
    '将', '裨将', '偏将', '副将', '亚将', '次将', '末将',
    # 中郎将 / 校尉
    '中郎将', '左中郎将', '右中郎将', '五官中郎将',
    '校尉', '都尉', '骑都尉', '奉车都尉', '驸马都尉',
    '轻车将军', '材官将军', '楼船将军', '伏波将军',
    '度辽将军', '贰师将军', '嫖姚校尉',
    # 胡汉交战期常见
    '拔胡将军', '破虏将军', '彊弩将军', '强弩将军',
    # 护军/都护/军候/军司马
    '护军', '都护', '军候', '军司马',
    # 长平侯 类（此处不归军职，归爵位）
}

# 汉诸侯王国的官员（郡国长吏级别 — 非中央三公九卿列卿）
# 汉初诸侯国设相/太傅/内史/中尉/郎中令等 mimicking 中央，
# 但自景帝削藩后皆由汉廷任命，级别等同郡官。
# 规则：X + 官 where X 是汉诸侯国名 → 强制归 郡国长吏
HAN_VASSAL_STATES = {
    '齐', '楚', '代', '燕', '赵', '梁', '吴',
    '长沙', '淮南', '淮阳', '常山', '河间', '中山',
    '鲁', '清河', '胶东', '胶西', '济南', '济北',
    '城阳', '广陵', '江都', '衡山', '六安', '临江',
}

EXPLICIT_JUNLI_VASSAL = {
    # 诸侯国 丞相/相（景帝后统称"相"，二千石，等同郡太守）
    '赵相', '齐相', '楚相', '代相', '燕相', '梁相', '吴相',
    '鲁相', '齐丞相', '常山丞相', '齐右丞相', '代丞相',
    '淮南相', '淮南王相', '济北相', '江都相', '城阳相', '济南相',
    '守相',                        # 代理相（诸侯国）
    '阳虚侯相',                    # 列侯国相（也属郡国长吏）
    # 诸侯国 太傅（王国高级辅官，等同郡级）
    '齐王太傅', '长沙王太傅', '梁怀王太傅',
    '河间王太傅', '清河王太傅', '常山王太傅',
    # 诸侯国 内史（王国民政长官）
    '齐内史', '梁内史', '衡山内史', '胶西内史',
    '城阳内史', '长沙内史', '胶东内史', '广陵内史',
    # 诸侯国 中尉（王国武职）
    '楚中尉', '城阳中尉', '淮南中尉',
    '鲁中尉', '胶西中尉',
    # 春秋战国"地名+大夫" = 该地邑宰（如齐威王朝阿大夫/即墨大夫故事）
    '阿大夫',           # 齐阿城大夫
    '即墨大夫',         # 齐即墨大夫
    '邯郸大夫',         # 赵邯郸大夫
    '原大夫',           # 晋原邑大夫
    '西垂大夫',         # 秦先祖所任（秦受封之始）
}


EXPLICIT_XIANLI = {
    # 汉代郡县属吏
    '功曹',             # 郡/县功曹
    '田部吏',           # 县吏
    '督道仓吏',         # 郡/县仓吏
    '里监门', '里监门吏',
    '司职吏',
    # 官署属吏
    '奏谳掾', '主吏掾',
    # 单字通称（县乡级）
    '守',                # 郡/县守通称
}


# 郡国长吏（新增：汉郡守/郡都尉 + X郡守 + X郡都尉）
EXPLICIT_JUNLI_EXTRA = {
    # X守（郡守简称）
    '三川之守', '三川守', '上党守', '东海守', '云中守',
    '会稽守', '南阳守', '兵守', '假守',
    '上党郡守', '上党郡中令',
    # 诸侯国郡级 尉（南海尉=赵佗任）
    '南海尉',
    # 郡都尉（非中央都尉）
    '东海都尉', '代郡都尉', '北地都尉', '关内都尉',
    # 古官中的"尹" (春秋"尹"多为郡长级)
    '卜尹',              # 楚官
}


EXPLICIT_JUE = {
    # 汉 20 等爵（注：'大夫' 移至 EXPLICIT_IDENTITY_MIS 身份通称；
    #            '列侯' 移至 EXPLICIT_IDENTITY_MIS always_identity）
    '公士', '上造', '簪袅', '不更', '官大夫', '公大夫',
    '公乘', '五大夫', '左庶长', '右庶长', '左更', '中更', '右更',
    '少上造', '大上造', '大良造', '驷车庶长', '大庶长', '关内侯',
    '彻侯', '通侯',      # 列侯 移至身份误标（identity_wordlist always_identity）
    # 其他 X大夫 爵位 / 爵第七级别称
    '七大夫',           # 公大夫的别称（第七级）
    # 春秋爵级"上大夫/下大夫/列大夫"
    '上大夫', '下大夫', '列大夫',
    # 其他
    '上卿', '亚卿', '下卿', '客卿', '正卿',
    # 侯号（2 字地名 + 侯 多为具体封号，也可视作爵位指称）
    '浞野',             # 浞野侯
}

EXPLICIT_PALACE = {
    '郎', '郎中', '侍郎', '中郎', '议郎', '骑郎', '户郎',
    '侍中', '常侍', '中常侍', '给事中',
    '谒者', '仆射', '谒者仆射',
    '中书', '尚书', '尚书郎',
    '黄门', '中黄门', '小黄门',
    '舍人', '太子舍人', '王舍人',
    '家令', '太子家令',
    '太子率更', '太子詹事', '太子门大夫',
    '宦者令', '中车府令',
    # 内廷近侍 + 中官
    '中候', '中宦者', '中涓', '中庶子',
    '执戟', '仆御', '司御', '待诏', '祭酒', '掌故',
    '太常掌故',
    # 虎贲（武士近侍）
    '虎贲',
    # 少府属尚X (尚方/尚席)
    '尚方', '尚席',
    # 侍医
    '侍医',
    # 涓人/厨人（古宫廷小吏）
    '涓人', '厨人',
    # 嫔御（妃嫔官号）
    '娙娥', '婕妤', '容华',
    # 左右内官
    '左右内官',
    # 门下 / 门大夫
    '门下',
}

EXPLICIT_WENXUE = {
    '博士', '议郎', '谏议大夫', '谏大夫',
    '光禄大夫', '太中大夫', '中大夫', '中大夫令',
    '大中大夫',                    # 汉官（谏官类）
    '礼官大夫',                    # 汉官（礼乐类）
    '命大夫',                      # 周/春秋官
    '三闾大夫',                    # 楚官（屈原任）— 掌宗室
    '文学掾', '文学',
    '太子太傅', '太子少傅', '太子舍人', '太子洗马',
}

EXPLICIT_SHIFU = {
    '太傅', '太师', '太保',
    '少傅', '少师', '少保',
    '师', '傅', '师傅', '保傅', '阿保',
    '太子太傅', '太子少傅',
}

EXPLICIT_FOREIGN = {
    # 归义（汉封匈奴/西羌降者）
    '归义',
    # 大鸿胪属（外邦接待官）
    '主客',
    # 西南夷/西域王号
    '且兰君',             # 西南夷 且兰国君
    '乌孙王',             # 西域乌孙王
    '休屠王',             # 匈奴休屠王
    # 匈奴官号
    '右方王将',           # 匈奴官
    # 匈奴
    '单于', '大单于',
    '左贤王', '右贤王', '贤王', '左右贤王',
    '左谷蠡王', '右谷蠡王', '左右谷蠡王',
    '屠耆', '左屠耆王', '右屠耆王',
    '当户', '大当户', '左右大当户',
    '且渠', '左且渠', '右且渠',
    '骨都侯', '左右骨都侯',
    '左大将', '右大将', '左大都尉', '右大都尉',
    # 东胡
    '东胡王', '东胡卢王', '卢胡王',
}
# 注：南越/朝鲜/西南夷的"相/将军/内史/中尉" 与中央官重名，
# 通过 L2 章节加权处理（FOREIGN_CHAPTERS 里出现才算外邦）

EXPLICIT_JIACHEN = {
    # 春秋战国大夫/卿的家臣（私属官）
    '家臣', '家宰', '家相', '家丞', '家老', '室老',
    '邑宰', '冢宰',   # 冢宰也可能是上古三公，双标
    # 春秋鲁季孙氏家臣系统中出现的职衔
    '家令',           # 注：汉太子家令属宫廷近侍；春秋"家令"少见，主要是私邑
    '门大夫',         # 列侯门大夫
    # 私邑长官
    '宰',             # 单字"宰"春秋多作大夫家宰
    # 邑宰复合（地名+宰）
    '中牟宰', '中都宰', '郈宰',
    '相室',           # 大夫之家"相室" 亦属私邑管家
    # 宰人 / 宰夫
    '宰人', '宰夫',
}

EXPLICIT_ANCIENT = {
    '四岳', '岳', '十二牧', '诸牧', '牧',
    '共工', '朕虞', '虞', '秩宗', '典乐', '纳言',
    '稷', '士', '工师', '百工',
    '云师', '左右大监',
    '冢宰', '司徒',  # 上古义；后期作三公时 EXPLICIT_SANGONG 会抢先命中
    '六卿', '六事', '六官', '三公', '三公九卿',
    '四辅', '四辅臣',                 # 周四辅（前后左右）— 身份/上古官多标签，优先上古官
    '师尚父', '亚旅', '师氏', '千夫长', '百夫长', '万夫长',
    '冢君', '君长',
    # 上古农官/官师
    '农师', '尚父',
    # 乡里三老（秦汉乡官）
    '三老', '有秩',
    # 春秋晋古官（七舆大夫：晋献公增置的兵车长官）
    '七舆大夫',
    # 春秋诸国"司X" 古官
    '司城',     # 宋国六卿首
    '司命',     # 上古天神官
    '司中', '司禄', '司星', '司御', '司败', '司过',
    # 春秋楚/晋古官
    '大莫敖',   # 楚官
    '左师',     # 宋左师
    '右师', '右宰',
    '左徒',     # 楚官（屈原为左徒）
    # 上古/商代相
    '阿衡',     # 商伊尹之官
    # 上古火正/土正
    '祝融',     # 火正之官名
    '玄冥师',   # 水正
    # 乐师（古代掌乐之官）
    '乐师', '老师',
    # 古刑官
    '理',       # 大理之前身
}

EXPLICIT_GENERIC = {
    # ── 官员集合通称（非 "X身份"，这部分保留泛称）──
    '百官', '群臣', '朝臣', '侍臣',
    '王', '侯', '吏', '将', '相', '尉', '令', '史',
    '主', '主子', '上', '下', '公', '伯', '子', '男',  # 五等爵通称
    '卿', '九卿',
    '二千石', '二百石', '六百石', '千石', '百石',       # 汉代秩级通称
    '御史', '令史', '佐史', '卒史',
    '有司',
    '官', '吏',
    # 泛泛"X吏"
    '军吏', '文吏', '狱吏', '里吏', '长吏', '下吏', '薛狱吏',
    # 泛泛"X官"
    '大官', '太官', '学官', '史官', '祝官', '祠官', '从官', '郎官',
    '博士官', '大卜官', '太卜官', '稷官', '中都官',
    # 泛泛"X主"
    '人主', '盟主',
    # 泛泛"X者"
    '使者', '王者', '官者', '门者',
    # 泛泛"X卒" / "X人"
    '卫卒', '材官', '期门', '羽林',
    # 宫廷杂吏
    '小吏', '卒吏',
    # 单字通称
    '丞', '候', '掾', '御', '护', '校',
    # 复合通称
    '公卿大夫士', '公卿大臣',
    # 周召（双字合并通称，非具体人）
    '周召',
    # 亲民/执政 等泛称
    '亲民', '执政', '执法',
    # 单字通称
    '长',
    # "公子" 单独作 泛称（非具体卫公子/魏公子 等已归人名误标）
    '公子',
}

# 具体某人被误标为官职（人名误标）
# 这些词表面像职位，但指代特定个体：
#   - 具体单于名：老上单于（军臣单于之父）、兒单于（伊稚斜少子）等
#   - 国名+谥号：常见于春秋先秦（如"晋文公" 表某代晋君）— 但这些通常归 person 实体
#   - 其他"职位号 + 独有特征"指代具体某人的
# 身份误标：本应用 identity 标签（〖#〗）的词被误标为 official（〖;〗）
# 范围参考 kg/entities/data/identity_wordlist.json 的 always_identity + new_candidates
EXPLICIT_IDENTITY_MIS = {
    # ── 帝后身份 ──
    '太后', '皇后', '皇太后', '太皇太后', '王太后', '王后',
    '正后', '后',
    '太上皇',                           # 曾任天子的太父，身份
    # ── 帝王身份（泛称，非特定某帝）──
    '帝', '皇帝', '先帝', '天子', '周天子', '陛下',
    '少主', '少帝',
    '霸王', '帝王',                      # 霸王通称（项羽除外具体人名已在人名误标）
    # ── 皇族/血缘身份 ──
    '太子', '皇子', '王子', '长子',
    '后子', '中子', '庶子', '嗣子', '世子', '孺子',
    '冢子', '君子', '侯世子', '周王子',
    '公主', '长公主', '大长公主', '卫长公主',
    # ── 嫔御身份（非具体官号的嫔妃通称）──
    '妃', '夫人', '正夫人', '美人', '才人',
    '宠姬', '幸姬',
    # ── 外戚 ──
    '外戚',
    # ── 贵族/官员通称（据 identity_wordlist always_identity）──
    '诸侯', '列侯', '公侯', '侯王',
    '士大夫', '公卿', '卿士',
    '大臣', '大夫',                     # "大夫" 通称（非 五大夫/官大夫 爵）
    '先王', '卿相', '宠臣',
    '将相',
    '公卿大夫', '卿大夫',           # 通称（官员集合）
    # 春秋各国大夫（国名+大夫 = 某国大夫身份通称）
    '梁大夫', '越大夫', '陈大夫', '国大夫',
    # ── 君/臣（单字通称）──
    '君', '臣',
    # ── 平民/年龄身份 ──
    '布衣', '匹夫', '丈夫', '大丈夫',
    '妇人', '庶人',
    '大人', '家人', '国人', '野人',
    '男子', '女子', '小子',
    '少年', '童子',
    # ── 士人/游侠身份 ──
    '义士', '勇士', '壮士', '列士',
    '处士', '隐士', '术士', '骑士',
    '豪杰', '佐僚',
    '力士', '长者',
    # ── 宾客身份 ──
    '上客', '宾客', '门客', '食客',
    '游侠', '说客', '谋客',
    # ── 表演者/职业身份 ──
    '优侏儒',
    # ── 亲族称谓 ──
    '父兄', '子弟', '父老',
    # ── 其他通称 ──
    '功臣', '忠臣', '近臣', '陪臣', '名臣',
    '幸臣', '小臣', '重臣', '奸臣', '谋臣',
    '良臣', '宰臣',                    # "四辅臣"已移至 EXPLICIT_ANCIENT
    '主上',                             # 帝王通称
}


# 待拆分：原文 `〖;X〗` 内同时含官职 + 人名，应源头拆成两个实体
# 典型：丞相何（萧何）/ 上谷太守郝贤 / 卫将军青（卫青）
# 区别于"人名误标"：这里是 复合体（官职+姓/名），修复方式是拆分；
#        人名误标是 裸称号指代具体人（老上单于/仲尼），修复是迁 identity/person
EXPLICIT_NEED_SPLIT = {
    # 官职 + 人名（1 字名）
    '丞相何',          # 萧何
    '长史安',          # 人名安
    '大夫黎鉏',
    '太宰嚭',          # 伯嚭
    '合骑侯敖',        # 人名敖
    '司马桓魋',
    '尉屠睢',
    '宜春侯伉',
    '平阳侯襄',        # 曹襄
    '樊将军哙',        # 樊哙
    '发干侯登',
    '议郎周霸',
    '卫将军青',        # 卫青
    '令尹子西',
    # 官职+人名（2 字以上）
    '上谷太守郝贤',
    '主爵赵食其',
    '从骠侯破奴',
    '剽姚校尉去病',    # 霍去病
    '北地都尉邢山',
    '右内史李沮',
    '右北平太守路博德',
    '护军都尉公孙敖',
    '昌武侯安稽',
    '轻骑校尉郭成',
    '阴安侯不疑',
    '鹰击司马破奴',
    '北军使者护军',
    # 爵位 + 人名
    '庶长疾', '庶长章', '庶长封',    # 秦庶长 + 人名
    # 人称 + 前置官 (郑子亹 = 郑国君子亹)
    # （郑子亹 保留在人名误标）
}


EXPLICIT_PERSON_MIS = {
    # 具体单于（匈奴君主个人名号）
    '老上单于',       # 冒顿之子稽粥
    '兒单于',         # 伊稚斜少子
    '老上',           # 老上单于简称
    # 太仓公 = 淳于意（扁鹊弟子之传人）
    '太仓公', '仓公',
    # 孔门师徒
    '仲尼', '伯鱼', '南宫敬叔',
    # 史官人名（史+名）
    '史墨', '史宽舒', '史敦', '史佚',
    # 春秋公子个人名
    '太叔', '太子免', '太子增', '太子安国', '太子御寇',
    '太子申', '太子蒯聩',
    '悼太子', '栗太子', '燕太子', '太上皇卫',    # '太上皇' 归身份误标
    '卫公子', '宋公子', '晋公子', '楚公子', '魏公子',
    # X相国 / X相 + 人名 (特定人)
    '萧相国', '韩相国', '代相国', '假相国',
    # "诸侯相国" 作 title 归 列卿；不在人名误标
    # 春秋晋/鲁大夫人名+子尊称
    '康子', '懿子', '甯武子', '武子', '文子', '成季',
    '桓子', '平子', '子家', '子思', '子慎', '子襄',
    '子高', '子京', '子上', '子男',
    # 春秋末战国早人名
    '公中缓', '公子政', '公子赫', '公孙', '公宰',
    '无彊',                        # 越国末代君
    '宰孔',                        # 周卿士
    '脩成子仲',                    # 人名
    '高昭子', '孟孙', '申徒',      # 春秋人名
    '师己',                        # 齐太史人名
    '黑肱',                        # 公子黑肱
    '君角', '信武', '奉春', '范睢',
    # 帝后谥号指代具体人（皇帝/太后）
    '孝元', '孝景', '孝武', '太祖', '高宗',
    '吕后', '魏其', '蒯成',
    # 具体汉代皇帝（谥号+帝/皇帝 指代特定帝）
    '文帝', '高帝', '高皇帝', '孝文皇帝', '孝惠皇帝',
    '孝景帝', '孝宣帝', '孝元帝',
    # 具体汉代太后
    '吕太后', '帝太后', '高后',
    # 汉代诸公主指代具体个人
    '平阳主', '平阳公主',
    # 侯号指代具体人
    '硃虚', '文成', '灵文', '秦缪',
    # 官职 + 具体人名（待拆分的典型个体 — 多数已移至 EXPLICIT_NEED_SPLIT）
    '韩王孙',                      # 人名（不是待拆分，是纯人名）
    # 匈奴单于别号
    '休屠',                        # 休屠王
    # 异族人名
    '罗姑比', '比车耆',
    # 其他
    '徐子', '郑子亹',              # 郑君
    '楼烦', '白羊',                # 匈奴王别号
    # 汉代将军 / 官号 代具体人
    '五利',                        # 五利将军 栾大
    '稷嗣',                        # 稷嗣君 叔孙通
    '监禄',                        # 秦监御史禄（史禄）— 具体人
    '齐相国',                      # 齐相国 多指召平/曹参时具体人
    # "X大夫" 作具体人号
    '五羖大夫',                    # 秦穆公时百里奚的号
    '上官大夫',                    # 楚怀王大臣上官靳尚
    # X君 封号代具体人
    '信平君',                      # 廉颇
    '信陵君',                      # 魏无忌
    '修成君',                      # 汉臧儿子（王太后之弟）
    '共德君',
    # X丞相 汉具体丞相
    '于丞相',                      # 于定国
    '张丞相',                      # 张苍
    '申屠丞相',                    # 申屠嘉
    '车丞相',                      # 车千秋
    '韦丞相',                      # 韦贤
    '魏丞相',                      # 魏相
    '邴丞相',                      # 邴吉
    '黄丞相',                      # 黄霸
    # 亚父 = 项羽尊范增
    '亚父',
    # 主父 = 主父偃
    '主父',
    # 楚武王长子
    '句亶王',
    # 冠军侯 (霍去病封号，常作具体指代)
    '冠军侯',
}


# 被错误标注为 official 的非官职实体（谥号/人名/语气词等）
# 谥号误标：裸谥号（不带国号/庙号）被误标为 official
# 例如：哀（某哀公简称）、庄（庄王/庄公）、宣（宣王/宣公）
# 区别于"人名误标"：这里是谥号字本身，不是某人的全名
EXPLICIT_SHIHAO_MIS = {
    # 常见春秋谥号（裸字被误标）
    '哀', '康', '庄', '戴', '孟', '幽', '厉', '宣',
    '景', '昭', '定', '灵', '隐',
    # 暴君恶谥
    '桀', '纣', '政',             # 政即秦始皇名嬴政，作谥号式字
    # 汉代皇帝谥号字
    '文', '武', '元', '成',
    # 其他
    '俀',
    # 姓氏/谥号字
    '范', '雍', '姬', '刘', '项', '季',
}


EXPLICIT_MIS = {
    # 以下为"谥号"以外的人名/姓氏片段（谥号裸字已移至 EXPLICIT_SHIHAO_MIS）
    # 过度琐细（主管具体事务的杂役）
    '主屦', '主屦者',  # 主管鞋履
    # 方位词
    '左', '右',
    # 介词/助词误标（'后' 已在 IDENTITY_MIS，移除重复）
    '便', '客', '印',
    # 非官职词（地名/概念/动词短语误标 — 身份类已移至 EXPLICIT_IDENTITY_MIS）
    '上舍',           # 馆舍，非官
    '下其议',          # 动词短语
    '主主',            # 被误标
    '南子',            # 卫灵公夫人（人名）
    # 氏族（应是 dynasty 类，被误标为 official）
    '中行氏', '叔孙氏', '孟氏', '季氏', '智氏', '范氏',
    '戚氏', '安陵氏', '阏氏',
    # 待拆分（官名+人名）已全部移至 EXPLICIT_NEED_SPLIT
    # 季X子（鲁季孙氏历代宗主，是人名）
    '季平子', '季康子', '季桓子', '季武子', '季悼子',
    '司城贞子', '师襄子',
    # 纯人名被误标
    '宅皋狼', '薛文', '魏厓', '司马卬', '曼丘臣', '侯敞',
    '后胜', '佐弋',
    '中行',  # 晋军制"中行" + 氏族"中行氏" 混淆
    '卿子',   # 人名（卿子冠军前缀）
    # 其他被误标
    '东牟',            # 县名 被作官职（应在 place）
    '上间爵',          # 可能是"赐爵 + 地名" 碎片
    '瑕丘', '淮阴', '九江',  # 地名误标
    # 更多地名误标（国名/郡名被当官职）
    '北地', '代郡', '河南', '陇西', '雁门', '阳陵',
    '淮南', '齐悼',    # 以 国名/谥号 指代政权/具体人
    # 方位词误标
    '左右', '左方', '右方', '右贤',
    # 非官职词（非身份类）
    '先生',            # 尊称，非身份实体
    # 地名被误作官职
    '淮阳',            # 淮阳王国
    # 动词短语
    '免相',            # 动词 "免其相" 非官职
    # 单字歧义（无明确官职语义）
    '监',              # 多义：监察/太子监国
    '正',              # 多义：正官/副职
    # 动词/连词误标（'隐'已在 EXPLICIT_SHIHAO_MIS）
    '渠',              # 单字"渠"作人称代词（他）
    '直指', '直指使',  # 动词短语
    # 片段误标
    '水工',            # 人名 or 碎片
    '削厉工',          # 工匠身份
    '厓有', '厓求',    # 冉有/冉求 弟子名
    '附庸',            # 附属小国，非官职
    '正闳',            # 人名
    # X+名 带人名的待拆分（部分已移至 EXPLICIT_NEED_SPLIT）
    '校尉司马',        # 应拆分
    '轻车将车',        # 应拆为 轻车将军（可能是原文讹字）
    '良师傅',          # 人名或泛称（非具体官）
    # 祭品/概念 误标
    '太牢',            # 祭品等级
    '礼',              # 概念/动词
    # 注：'童子'/'后'/'隐'/'太上皇'/'太子御寇'/'上谷太守郝贤' 等已分别归至
    #     身份误标/谥号误标/人名误标/待拆分，不重复列入 EXPLICIT_MIS
}


# ─── 章节上下文规则 ───

# 侯者年表 → 爵位/王号
HOUZHE_CHAPTERS = {
    '017_汉兴以来诸侯王年表',  # → 王号
    '018_高祖功臣侯者年表',
    '019_惠景间侯者年表',
    '020_建元以来侯者年表',
    '021_建元已来王子侯者年表',
    '022_汉兴以来将相名臣年表',
}
HOUZHE_WANG_CHAPTER = '017_汉兴以来诸侯王年表'
HOUZHE_MAJORITY = 0.4
HOUZHE_MIN_REFS = 1

# 外邦列传 → 外邦职
FOREIGN_CHAPTERS = {
    '110_匈奴列传',
    '111_卫将军骠骑列传',  # 虽为汉将，但大量提及匈奴官号
    '113_南越列传',
    '114_东越列传',
    '115_朝鲜列传',
    '116_西南夷列传',
    '123_大宛列传',
}
FOREIGN_KEYWORDS = (
    '单于', '贤王', '谷蠡', '屠耆', '当户', '且渠', '骨都',
    '左大将', '右大将', '大都尉', '胡', '戎', '夷',
)


# ─── 共现动词/上下文模式 ───

CONTEXT_PATTERNS = [
    # 爵位：封X为〖;Y侯/君〗、赐爵〖;Y〗、立〖;Y〗为...
    (r'⟦○封⟧[^〖]{0,30}为〖;([^〖〗]+?)〗', CAT_JUE, 1.5),
    (r'封[^〖]{0,15}为〖;([^〖〗]+?侯)〗', CAT_JUE, 1.2),
    (r'赐[^〖]{0,6}爵[^〖]{0,6}〖;([^〖〗]+?)〗', CAT_JUE, 1.5),
    (r'⟦○赐⟧[^〖]{0,10}爵[^〖]{0,10}〖;([^〖〗]+?)〗', CAT_JUE, 1.5),

    # 王号：立〖@X〗为〖;YY王〗
    (r'⟦○立⟧[^〖]{0,30}为〖;([^〖〗]+?王)〗', CAT_WANG, 1.5),
    (r'立[^〖]{0,15}为〖;([^〖〗]+?王)〗', CAT_WANG, 1.2),

    # 拜/迁 → 中央官
    (r'⟦○拜⟧[^〖]{0,10}〖;([^〖〗]+?)〗', None, 0.5),  # 仅线索，类别由实体本身决定
    (r'⟦○拜⟧[^〖]{0,10}为〖;([^〖〗]+?)〗', None, 0.5),
    (r'迁〖;([^〖〗]+?)〗', None, 0.4),

    # 郡国长吏：X太守、X郡守、治〖=X〗之〖;Y〗
    (r'〖=[^〖〗]+?〗[^〖]{0,3}〖;([^〖〗]*?(?:太守|郡守|郡尉|国相))〗', CAT_JUNLI, 1.5),
    (r'〖;([^〖〗]*?(?:太守|郡守|都尉|郡尉))〗', CAT_JUNLI, 1.2),

    # 县乡吏：X令、X丞
    (r'〖;([^〖〗]*?(?:县令|县长|县丞|县尉|亭长|乡三老|啬夫|游徼))〗', CAT_XIANLI, 1.5),

    # 军职：〖;X〗将兵/将卒/领兵
    (r'〖;([^〖〗]+?)〗(?:将|领|帅|率)(?:兵|卒|军|众)', CAT_MILITARY, 1.0),
    (r'〖;([^〖〗]*?将军)〗', CAT_MILITARY, 1.2),
    (r'〖;([^〖〗]*?(?:校尉|中郎将|都尉|偏将|裨将|军候))〗', CAT_MILITARY, 1.2),

    # 外邦职
    (r'〖;([^〖〗]*?单于)〗', CAT_FOREIGN, 1.5),
    (r'〖;([^〖〗]*?(?:贤王|谷蠡王|屠耆|当户|且渠|骨都侯))〗', CAT_FOREIGN, 1.5),
]

# 三家注模式
SANJIA_PATTERNS = [
    (re.compile(r'([一-鿿]{1,6})，官名(?:也)?'),      None),          # 按后缀细分
    (re.compile(r'([一-鿿]{1,6})，爵名(?:也)?'),      CAT_JUE),
    (re.compile(r'([一-鿿]{1,6})，爵也'),             CAT_JUE),
    (re.compile(r'([一-鿿]{1,6})，匈奴(?:官|王号)'),   CAT_FOREIGN),
    (re.compile(r'([一-鿿]{1,6})，胡(?:官|王)'),       CAT_FOREIGN),
    (re.compile(r'([一-鿿]{1,6})，秦官(?:也)?'),       None),
    (re.compile(r'([一-鿿]{1,6})，汉官(?:也)?'),       None),
    (re.compile(r'([一-鿿]{1,6})，周官(?:也)?'),       CAT_ANCIENT),
    (re.compile(r'([一-鿿]{1,6})，尊号(?:也)?'),       CAT_GENERIC),
]


# ─── 后缀启发式 ───

# 形如 (suffix, minlen, category)
SUFFIX_RULES = [
    # 外邦职关键词（优先匹配长词）
    ('单于', 2, CAT_FOREIGN),
    ('贤王', 2, CAT_FOREIGN),
    ('谷蠡王', 3, CAT_FOREIGN),
    ('屠耆王', 3, CAT_FOREIGN),
    ('骨都侯', 3, CAT_FOREIGN),

    # 王号：2+ 字 + 王
    ('王', 2, CAT_WANG),

    # 侯：2+ 字 + 侯 → 爵位
    ('侯', 2, CAT_JUE),

    # 军职
    ('将军', 2, CAT_MILITARY),
    ('中郎将', 3, CAT_MILITARY),
    ('校尉', 2, CAT_MILITARY),
    ('都尉', 2, CAT_MILITARY),
    ('将', 2, CAT_MILITARY),     # X将 (裨将/偏将)

    # 师傅
    ('太傅', 2, CAT_SHIFU),
    ('少傅', 2, CAT_SHIFU),
    ('太师', 2, CAT_SHIFU),
    ('少师', 2, CAT_SHIFU),
    ('太保', 2, CAT_SHIFU),

    # 宫廷近侍
    ('郎中', 2, CAT_PALACE),
    ('郎', 2, CAT_PALACE),
    ('舍人', 2, CAT_PALACE),
    ('谒者', 2, CAT_PALACE),
    ('尚书', 2, CAT_PALACE),
    ('侍中', 2, CAT_PALACE),

    # 郡国长吏
    ('太守', 2, CAT_JUNLI),
    ('郡守', 2, CAT_JUNLI),
    ('郡尉', 2, CAT_JUNLI),
    ('内史', 2, CAT_JUNLI),

    # 县乡吏
    ('县令', 2, CAT_XIANLI),
    ('县长', 2, CAT_XIANLI),
    ('县丞', 2, CAT_XIANLI),
    ('县尉', 2, CAT_XIANLI),
    ('亭长', 2, CAT_XIANLI),
    ('啬夫', 2, CAT_XIANLI),

    # 文学顾问
    ('博士', 2, CAT_WENXUE),
    ('谏大夫', 3, CAT_WENXUE),
    ('谏议大夫', 4, CAT_WENXUE),
    ('中大夫', 3, CAT_WENXUE),
    ('光禄大夫', 4, CAT_WENXUE),

    # 爵位末字（注意：X大夫 suffix 容易误伤——"地名+大夫" 是邑宰而非爵位，
    # 已在 EXPLICIT_JUNLI_VASSAL 单列若干。其他 X大夫 通称身份的已移至 EXPLICIT_IDENTITY_MIS。
    # 真正的爵位"X大夫" 需在 EXPLICIT_JUE 显式列出，不靠 suffix）
    ('庶长', 2, CAT_JUE),
    ('卿', 2, CAT_JUE),       # X卿 (上卿/亚卿)

    # 上古官
    ('岳', 2, CAT_ANCIENT),    # 四岳
    ('牧', 2, CAT_ANCIENT),    # 十二牧/诸牧

    # 单字通称
    ('公', 2, CAT_GUJU),       # X公 (鲁公/陈公)  多数是诸侯君号
    ('君', 2, CAT_GENERIC),    # X君 (武安君/广野君) — 也可能爵位，需 L3 细化
    ('卿', 2, CAT_JUE),        # X卿
    ('令', 2, CAT_XIANLI),     # X令 (郎中令/卫令/县令)
    ('尉', 2, CAT_MILITARY),   # X尉 → 多为军职
    ('守', 2, CAT_JUNLI),      # X守
    ('丞', 2, CAT_XIANLI),     # X丞
    ('长', 2, CAT_XIANLI),     # X长 (亭长/屯长)
    ('尹', 2, CAT_JUNLI),      # X尹 (京兆尹/河南尹)
    ('相', 2, CAT_SANGONG),    # X相 (丞相/国相) — 弱，需 L3 消歧

    # 史
    ('史', 2, CAT_PALACE),     # 御史/内史/长史 — 多数是近侍

    # 军 (2 字) → 军职 (上军/下军/中军/北军/右军/左军/监军)
    ('军', 2, CAT_MILITARY),

    # 掾 (汉代吏属，如 府掾 / 县掾 / 廷掾 / 市掾 / 功曹)
    ('掾', 2, CAT_XIANLI),

    # 监门 (守门小吏)
    ('监门', 2, CAT_XIANLI),

    # 祝 → 上古官 (商祝/宗祝/巫祝/泰祝)
    ('祝', 2, CAT_ANCIENT),

    # 正 → 上古官 (工正/火正/南正/北正) 或 列卿 (军正/廷尉正)
    ('正', 2, CAT_ANCIENT),

    # 监 → 列卿 (泗水监/建章监/尚食监/狗监)
    ('监', 2, CAT_LIQING),

    # 伯 → 古爵 (方伯/侯伯/西伯/郑伯)
    ('伯', 2, CAT_GUJU),

    # X氏 → 误标（多为氏族）
    # 注：交给 EXPLICIT_MIS 处理，此处不加后缀规则避免误判

    # X国 / X子 / X帝 / X后 / X主 / X人 / X官 / X吏 / X士 → 兜底归"泛称"
    # （低优先级，在具体类别之后）
    ('客', 2, CAT_GENERIC),     # X客 (上客/宾客/门客) — 多为身份
    ('父', 2, CAT_GENERIC),     # X父 (尚父/仲父) — 尊称
]


# ─── 加载外部数据 ───

def _load_hanshu_baiguan():
    if not HANSHU_BAIGUAN.exists():
        return {}
    try:
        return json.loads(HANSHU_BAIGUAN.read_text(encoding='utf-8'))
    except Exception:
        return {}


HANSHU_BG = _load_hanshu_baiguan()


def _load_feudal_states():
    """加载邦国列表（用于识别 X王 中的 X 是邦国名）。"""
    try:
        data = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
        return set(data.get('feudal-state', {}).keys())
    except Exception:
        return set()


FEUDAL_STATES = _load_feudal_states()


def _load_places():
    try:
        data = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
        return set(data.get('place', {}).keys())
    except Exception:
        return set()


PLACES = _load_places()


# ─── 分类主逻辑 ───

_VASSAL_OFFICIAL_SUFFIXES = ('丞相', '相', '内史', '中尉', '郎中令',
                             '少府', '廷尉', '太傅', '太仆', '宗正',
                             '大鸿胪')

def _is_vassal_official(name):
    """动态识别：X + 诸侯国官位 where X 是汉诸侯国名。
    返回 True 则该条目应归郡国长吏（诸侯国官）。"""
    for suffix in _VASSAL_OFFICIAL_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            prefix = name[:-len(suffix)]
            # 支持 "X王" 前缀（如 "淮南王相" / "齐王太傅"）
            if prefix.endswith('王') and len(prefix) > 1:
                prefix = prefix[:-1]
            if prefix in HAN_VASSAL_STATES:
                return True
    return False


def classify_l1_whitelist(name):
    """L1: 显式白名单命中。返回 list[str]（可多标签）。

    优先级（三类 MIS 早返回，单标签）:
      1. EXPLICIT_PERSON_MIS → 人名误标
      2. EXPLICIT_IDENTITY_MIS → 身份误标
      3. EXPLICIT_MIS → 误标
      4. EXPLICIT_JUNLI_VASSAL → 郡国长吏（诸侯国官强制归郡级，不可与三公多标签）
      5. 其他 → 多标签累积
    """
    cats = []
    if name in EXPLICIT_NEED_SPLIT:
        return [CAT_NEED_SPLIT]
    if name in EXPLICIT_PERSON_MIS:
        return [CAT_PERSON_MIS]
    if name in EXPLICIT_IDENTITY_MIS:
        return [CAT_IDENTITY_MIS]
    if name in EXPLICIT_SHIHAO_MIS:
        return [CAT_SHIHAO_MIS]
    if name in EXPLICIT_MIS:
        return [CAT_MIS]
    if name in EXPLICIT_JUNLI_VASSAL:
        return [CAT_JUNLI]
    # 动态匹配：X + 诸侯国官 where X 是汉诸侯国名
    if _is_vassal_official(name):
        return [CAT_JUNLI]
    if name in EXPLICIT_SANGONG:   cats.append(CAT_SANGONG)
    if name in EXPLICIT_JIUQING:   cats.append(CAT_JIUQING)
    if name in EXPLICIT_LIQING:    cats.append(CAT_LIQING)
    if name in EXPLICIT_MILITARY:  cats.append(CAT_MILITARY)
    if name in EXPLICIT_XIANLI:    cats.append(CAT_XIANLI)
    if name in EXPLICIT_JUNLI_EXTRA: cats.append(CAT_JUNLI)
    if name in EXPLICIT_JUE:       cats.append(CAT_JUE)
    if name in EXPLICIT_PALACE:    cats.append(CAT_PALACE)
    if name in EXPLICIT_WENXUE:    cats.append(CAT_WENXUE)
    if name in EXPLICIT_SHIFU:     cats.append(CAT_SHIFU)
    if name in EXPLICIT_ANCIENT:   cats.append(CAT_ANCIENT)
    if name in EXPLICIT_JIACHEN:   cats.append(CAT_JIACHEN)
    if name in EXPLICIT_FOREIGN:   cats.append(CAT_FOREIGN)
    if name in EXPLICIT_GENERIC:   cats.append(CAT_GENERIC)

    # X王 特判：若 X 在邦国或地名集合 → 王号
    if len(name) >= 2 and name.endswith('王') and name not in EXPLICIT_ANCIENT:
        prefix = name[:-1]
        if prefix in FEUDAL_STATES or prefix in PLACES:
            cats.append(CAT_WANG)

    # 去重保序
    seen = set(); uniq = []
    for c in cats:
        if c not in seen:
            seen.add(c); uniq.append(c)
    return uniq


def classify_l4_suffix(name):
    """L4: 末字后缀启发式。返回 str 或 None。"""
    if name in EXPLICIT_MIS:
        return None
    for suffix, minlen, cat in SUFFIX_RULES:
        if len(name) >= minlen and name.endswith(suffix):
            return cat
    return None


def classify_l25_hanshu(name):
    """L2.5: 《汉书·百官公卿表》白名单。返回 str 或 None。"""
    for cat_key, names_list in HANSHU_BG.items():
        if name in names_list:
            # cat_key 是 'sangong'/'jiuqing'/... 映射成中文
            return {
                'sangong': CAT_SANGONG,
                'jiuqing': CAT_JIUQING,
                'liqing':  CAT_LIQING,
                'junli':   CAT_JUNLI,
                'xianli':  CAT_XIANLI,
                'military':CAT_MILITARY,
                'palace':  CAT_PALACE,
                'wenxue':  CAT_WENXUE,
                'shifu':   CAT_SHIFU,
            }.get(cat_key)
    return None


def classify_l2_chapter_context(name, refs):
    """L2: 章节上下文规则。
    - 如 refs 中 >= 40% 来自侯者年表 → 爵位
    - 如 >= 40% 来自匈奴等外邦传 且 name 含外邦关键字 → 外邦职
    - 如 refs 在 017 诸侯王年表 且以"王"结尾 → 王号
    """
    if not refs:
        return None

    ch_counts = Counter(ch for ch, _ in refs)
    total = sum(ch_counts.values())
    houzhe = sum(c for ch, c in ch_counts.items() if ch in HOUZHE_CHAPTERS)
    foreign = sum(c for ch, c in ch_counts.items() if ch in FOREIGN_CHAPTERS)

    # 王号优先
    if ch_counts.get(HOUZHE_WANG_CHAPTER, 0) >= 1 and name.endswith('王') and len(name) >= 2:
        return CAT_WANG
    if houzhe / total >= HOUZHE_MAJORITY and houzhe >= HOUZHE_MIN_REFS:
        return CAT_JUE
    if foreign / total >= HOUZHE_MAJORITY:
        for kw in FOREIGN_KEYWORDS:
            if kw in name:
                return CAT_FOREIGN
    return None


def _scan_context_votes(officials_names):
    """L3: 扫描 chapter_md，对每个 official 累积类别票数。
    返回 { name: Counter({cat: votes}) }"""
    votes = defaultdict(Counter)
    name_set = set(officials_names)
    # 编译所有 context 模式
    compiled = [(re.compile(p), cat, w) for p, cat, w in CONTEXT_PATTERNS if cat is not None]

    for ch_file in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        content = ch_file.read_text(encoding='utf-8')
        for pat, cat, weight in compiled:
            for m in pat.finditer(content):
                hit = m.group(1)
                # 显示名中可能带 "|规范名"，先分离
                canonical = hit.split('|', 1)[-1] if '|' in hit else hit
                if canonical in name_set:
                    votes[canonical][cat] += weight
    return votes


def _load_sanjia_hints():
    """L3: 从三家注中累积类别线索。"""
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
    """L3: 共现上下文 + 三家注。返回 (str, score) 或 (None, 0)。
    score = 主导类别票数 / 总票数。"""
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


def _peer_split(content, officials_names, name_to_cats):
    """L5: 并列官职传播。
    在 `〖;A〗、〖;B〗、〖;C〗` 这类序列中向未分类条目传播多数类别。"""
    name_set = set(officials_names)
    # 匹配 〖;...〗 或 〖;X|Y〗，捕获规范名
    pat = re.compile(r'〖;([^〖〗|]+?)(?:\|[^〖〗]+)?〗')
    # 仅顿号分隔（与地名并列规则一致）
    sep = re.compile(r'^[、，\s]+$')

    updates = defaultdict(Counter)

    for ch_file in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        content = ch_file.read_text(encoding='utf-8')
        # 查找所有 official 匹配位置
        matches = list(pat.finditer(content))
        if not matches:
            continue
        # 按相邻位置聚合成 peer 组
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
            # 统计已分类成员的类别多数
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

def score_evidence(name, final_cats, l1, l4, l25, l2, l3_cat, l3_score, peer_ctr):
    """为每个 (name, cat) 组合打分 0-1。

    证据层级（与地名置信度设计一致）：
    - L1 白名单命中（人工维护）                    +0.6
    - L2.5 《汉书·百官公卿表》命中                 +0.3
    - L2 章节上下文命中                            +0.3
    - L3 上下文/三家注且比例 >= 0.6                +0.3 * ratio
    - L4 后缀命中                                  +0.2
    - L5 peer 传播（peer_ctr 有此 cat）            +0.15
    - 与其他层级一致加分；冲突减分
    """
    out = {}
    for cat in final_cats:
        score = 0.0
        if cat in l1:
            score += 0.6
        if l25 == cat:
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
        # 没有任何证据的默认兜底 0.1
        if score == 0.0:
            score = 0.1
        out[cat] = round(score, 2)
    return out


# ─── 主流程 ───

def main():
    print('━' * 60)
    print('官职分类脚本 classify_officials.py')
    print('━' * 60)

    index = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
    officials = index.get('official', {})
    names = list(officials.keys())
    print(f'官职实体总数: {len(names)}')
    print(f'邦国（用于 X王 判定）: {len(FEUDAL_STATES)}')
    print(f'地名（用于 X王 判定）: {len(PLACES)}')
    print(f'《汉书·百官公卿表》类别: {list(HANSHU_BG.keys()) if HANSHU_BG else "未生成 (先跑 extract_hanshu_baiguan.py)"}')
    print()

    # ── L3: 一次性扫描 chapter_md ──
    print('L3: 扫描 chapter_md 收集共现动词/上下文票数...')
    ctx_votes = _scan_context_votes(names)
    print(f'  命中条目: {len(ctx_votes)}')

    print('L3: 扫描三家注...')
    sanjia_votes = _load_sanjia_hints()
    print(f'  命中条目: {len(sanjia_votes)}')
    print()

    # ── 按条目分类 ──
    name_to_cats = {}
    name_to_details = {}
    for name in names:
        refs = [tuple(r) for r in officials[name].get('refs', [])]

        l1 = classify_l1_whitelist(name)
        l2 = classify_l2_chapter_context(name, refs)
        l25 = classify_l25_hanshu(name)
        l3_cat, l3_score = classify_l3_context(name, ctx_votes, sanjia_votes)
        l4 = classify_l4_suffix(name)

        final = []
        # 误标类（五子类）是早返回单标签，L2/L3/L4/L5 都不再叠加
        if l1 and l1[0] in (CAT_MIS, CAT_PERSON_MIS, CAT_IDENTITY_MIS,
                            CAT_SHIHAO_MIS, CAT_NEED_SPLIT):
            final = [l1[0]]
        elif l1 == [CAT_JUNLI] and name in EXPLICIT_JUNLI_VASSAL:
            # 诸侯国官也单标签（不叠加三公/列卿）
            final = [CAT_JUNLI]
        else:
            # 合并多层来源。优先级: L1 > L2.5 > L3 > L4 > L2
            # L2（侯者年表→爵位/诸侯王年表→王号）只做兜底，
            # 避免把 县乡吏/军职/文学顾问/家臣 等具体官误叠为爵位
            #   典型错例: "园厩啬夫" 在 020 侯者年表出现但本质是县乡吏
            #           "复土将军" 在 020 出现但本质是军职
            for c in l1: final.append(c)
            if l25 and l25 not in final: final.append(l25)
            # L3 context 只在 L1/L2.5 未给出具体类别时生效
            # 避免 "丞相将兵"→军职 等上下文噪音覆盖 三公 等明确分类
            _has_specific = final and not (set(final) <= {CAT_GENERIC})
            if l3_cat and l3_cat not in final and not _has_specific:
                final.append(l3_cat)
            if l4 and l4 not in final:
                # L4 只在 L1/L2.5/L3 都没给出时才采纳
                if not final:
                    final.append(l4)
            # L2 最后兜底：仅当 final 为空时才应用
            # （原"只有泛称时亦叠加"会让 子/男/卿 泛称条目误加爵位）
            if l2 and l2 not in final and not final:
                final.append(l2)

        name_to_cats[name] = final
        name_to_details[name] = dict(
            l1=l1, l2=l2, l25=l25, l3=(l3_cat, l3_score), l4=l4, peer=Counter()
        )

    # ── L5: peer 传播 ──
    print('L5: 并列官职传播...')
    for round_i in range(3):
        peer_updates = _peer_split('', names, name_to_cats)
        changed = 0
        for name, cats_ctr in peer_updates.items():
            if name_to_cats.get(name):
                continue  # 已分类不改写
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

    # ── 置信度计算 ──
    confidence = {}
    for name, cats in name_to_cats.items():
        if not cats:
            continue
        d = name_to_details[name]
        conf = score_evidence(
            name, cats,
            l1=d['l1'], l4=d['l4'], l25=d['l25'],
            l2=d['l2'], l3_cat=d['l3'][0], l3_score=d['l3'][1],
            peer_ctr=d['peer'],
        )
        confidence[name] = conf

    # ── 写出 ──
    OUT_JSON.write_text(
        json.dumps(name_to_cats, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    OUT_CONF_JSON.write_text(
        json.dumps(confidence, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    # ── 统计 ──
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
    print(f'未分类样本 (前 30): {blank_names[:30]}')
    print()
    print(f'写入: {OUT_JSON}')
    print(f'写入: {OUT_CONF_JSON}')


if __name__ == '__main__':
    main()
