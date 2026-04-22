#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为身份实体（identity 类型，标注符 〖;X〗）生成分类标签（身份类）。

对照 classify_officials.py 的简化版工作流，按 L1-L3 打分：
  L1   显式白名单（14 大类 + 人名误标）
  L2   后缀/关键字启发式（臣/士/王/子/人/民/者 等）
  L3   兜底：归入"泛称其它"

输出:
  kg/entities/data/identity_categories.json  { name: [cat, cat, ...] }
  kg/entities/data/identity_confidence.json  { name: {cat: score, ...} }

与 classify_officials.py 保持语义一致：
  - 多标签（如"士大夫"可同时属 士人儒生 + 臣属）
  - 人名误标用于后续迁移 identity → person
"""

import json
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
OUT_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'identity_categories.json'
OUT_CONF_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'identity_confidence.json'


# ─── 类别常量 ───
CAT_RULER    = '君主'           # 天子/王/帝/陛下/朕/寡人/主上
CAT_ROYAL    = '宗室皇族'       # 太子/太后/皇子/公主/王子/宗室
CAT_CONSORT  = '后妃侍妾'       # 夫人/美人/妃/乳母/婢妾
CAT_NOBLE    = '爵衔通称'       # 诸侯/列侯/封君/侯/伯/公
CAT_MINISTER = '臣属泛称'       # 臣/大臣/忠臣/功臣/谗臣
CAT_GENTRY   = '士人儒生'       # 士/大夫/儒/先生/学者/处士
CAT_MILITARY = '军旅兵员'       # 将军/士卒/骑士/武士/死士
CAT_GUEST    = '宾客门徒'       # 宾客/食客/舍人/门人/辩士/说客
CAT_COMMONER = '百姓庶民'       # 民/百姓/庶人/黔首/黎民
CAT_KIN      = '血缘亲属'       # 父/母/兄弟/妻子/嫡子/庶子
CAT_MERCHANT = '工商贫富'       # 商贾/富人/贫民/豪俊
CAT_OUTCAST  = '罪囚奴役'       # 盗/贼/囚/奴婢/罪人/徒
CAT_FOREIGN  = '外邦异族'       # 单于/阏氏/右贤王/浑邪王
CAT_GENERIC  = '泛称其它'       # 人/众/主/天下/王室
CAT_PERSON_MIS = '人名误标'     # 具体人名被误标为身份


# ─── L1: 显式白名单 ───

EXPLICIT_RULER = {
    # 通称
    '天子', '皇帝', '帝', '王', '君', '公', '伯', '辟', '主', '上',
    '今上', '今王', '今天子', '先王', '先帝', '先君', '先祖', '祖',
    '太上', '太上皇', '太祖', '天王', '主上', '人主', '人君', '主君',
    '主父', '大王', '寡人', '陛下', '朕', '孤', '后',
    # 修饰 + 王/帝/君
    '帝王', '霸王', '霸者', '王者', '圣王', '圣君', '圣主', '圣',
    '明王', '明君', '明主', '贤王', '贤君', '贤主', '世主',
    '盟主', '二伯', '二君', '三王', '五帝', '三代', '夏后', '群后',
    '少主', '少帝', '幼主', '储君', '君主',
    # 外号（指某代天子）
    '周天子', '栗太子',  # 栗太子也会被单独处理为误标
    # 朝代＋王
    '殷王', '周王', '秦王', '韩王', '代王', '赵王', '楚王', '齐王',
    '鲁王', '燕王', '广陵王', '昌邑王', '成王', '晋君', '燕君',
    '周王子', '群公',
    # 史家赞语
    '迹',  # "迹"指帝王事功/轨迹，按君主通称
}

EXPLICIT_ROYAL = {
    '太子', '皇太子', '皇太后', '太皇太后', '太后', '皇后', '王后',
    '正后', '皇子', '王子', '王孙', '公子', '群公子', '诸公子',
    '公主', '长公主', '大长公主', '卫长公主',
    '宗室', '宗亲', '宗戚', '宗族', '宗人', '王室', '同姓', '异姓',
    '七国', '世子', '侯世子', '嗣子', '嫡子', '適子', '適孙', '適长孙',
    '元孙', '曾孙', '婴兒主', '太傅',
    '帝太戊', '帝武丁', '帝太后',
}

EXPLICIT_CONSORT = {
    '夫人', '正夫人', '美人', '贵人', '才人', '妃', '姬', '宠姬',
    '幸姬', '妾', '婢妾', '仆妾', '老妾', '官婢', '奴婢', '乳母',
    '王太后',
}

EXPLICIT_NOBLE = {
    '诸侯', '列侯', '诸侯王', '封君', '君侯', '君', '侯', '侯伯',
    '侯王', '王侯', '公侯', '王公', '留侯', '子侯', '伦侯',
    '番君', '郑君', '君母', '辟', '大官',  # '辟'/'大官' 重复归属
}

EXPLICIT_MINISTER = {
    # 通称
    '臣', '群臣', '众臣', '大臣', '人臣', '小臣', '重臣', '老臣',
    '近臣', '幸臣', '宠臣', '佞臣', '孤臣', '社稷臣', '陪臣',
    '故人', '故旧', '宰臣', '武臣', '有司', '百官', '百僚',
    '百吏', '吏', '吏卒', '军吏', '将吏', '诸吏', '豪吏', '文吏',
    '贼吏', '官吏卒', '佐僚', '臣子', '臣妾', '六卿', '县官',
    # 赞贬
    '忠臣', '贤臣', '良臣', '名臣', '谋臣', '贵臣', '贞臣',
    '奸臣', '乱臣', '贼臣', '邪臣', '谗臣', '谗嬖臣',
    # 功臣 / 元老
    '功臣', '大功臣', '诸大臣', '公卿大臣', '公卿大夫',
    # 君臣关系
    '君臣', '将相', '卿相', '诸将相', '三公',
}

EXPLICIT_GENTRY = {
    # 士的各种修饰
    '士', '士大夫', '大夫', '卿', '卿大夫', '卿士', '公卿',
    '士人', '士民', '下士', '中士', '多士', '处士', '志士',
    '壮士', '烈士', '义士', '勇士', '谋士', '策士', '辩士',
    '隐士', '岩穴之士', '岩穴隐者', '清士', '素士', '名士',
    '列士', '锐士', '教士', '死士', '游说之士', '忠言之士',
    '谏说之士', '青云之士', '青云',
    # 特定地方大夫
    '梁大夫', '陈大夫', '越大夫', '国大夫', '群大夫', '贤大夫',
    # 先生 / 夫子 / 师
    '先生', '夫子', '大师', '贤师', '诸老先生', '荐绅先生',
    '缙绅', '三老五更', '族长', '卜人', '长老',
    # 儒 / 学者
    '儒', '儒者', '儒生', '诸儒', '群儒', '学者', '宿学',
    '大贤人', '贤', '贤者', '贤士', '七十子', '门人', '门弟子',
    '弟子', '诸生', '门客', '三良', '至人', '真人', '德人',
    '竖儒',
    # 智仁圣义
    '圣人', '贤人', '仁人', '仁者', '知者', '智者', '君子',
    '君子长', '善人', '义人', '诗人', '拘士', '贤母',
    '贤圣', '孝子',
    # 方术
    '方士', '术士', '巫', '巫祝', '畴人', '众医',
    # 其他
    '丈夫', '丈人', '大人', '俊桀', '俊雄', '豪杰', '豪桀',
    '豪俊', '豪', '豪举', '狗盗者', '誉者', '毁者', '议者',
    '谋者', '游士', '侠者', '游侠', '游说者', '说客',
}

EXPLICIT_MILITARY = {
    '将', '将军', '大将', '诸将', '宿将', '枭将', '将帅', '将率',
    '将种', '武士', '甲士', '骑士', '力士', '士卒', '卒', '兵',
    '厮养卒', '走卒', '锐士', '勇士', '死士', '教士', '轻锐',
    '军', '军吏', '诸军', '众', '楚众', '群虏', '散兵', '冠军',
    '丁壮', '万夫', '侍御', '御',
}

EXPLICIT_GUEST = {
    '宾客', '宾主', '诸客', '客', '上客', '食客', '门客',
    '门人', '门弟子',
    '弟子', '从者', '从人', '从官', '舍人', '家属', '家臣', '徒',
    '徒属', '徒役', '侍者', '侍御', '仆', '优侏儒', '倡', '讴者',
    '厨人', '抱关者', '监者', '守者', '守囚者', '屠者', '卖浆者',
    '主屦者', '主屦', '坐者', '逆旅', '庸保', '庸', '厮徒',
    '厮役', '博徒', '党', '使者', '使', '主人',
    # 宫廷近侍
    '宦者', '宦人', '中贵人', '左右', '足下', '外戚',
    '贵戚',
}

EXPLICIT_COMMONER = {
    '民', '百姓', '庶民', '庶', '庶人', '庶孽', '黔首', '万民',
    '兆民', '黎民', '黎人', '黎庶', '黎甿', '众民', '众庶', '人民',
    '人众', '群众', '元元', '国人', '下民', '邑人', '闾巷之人',
    '鄙人', '鄙细人', '细人', '小民', '民人', '齐民', '畯民',
    '野人', '布衣', '匹夫', '好事者', '巿人', '萌隶', '庶孙',
    '天下', '人', '众', '中人', '妇', '妇人', '妇女', '女子',
    '男女', '夫', '童子', '僮子', '狡童', '狡僮', '孺子',
    '中男', '少年', '长者', '老父', '老妇', '老人', '老', '老长',
    '后人', '後人',
    # 无嗣弱势
    '寡妇', '鳏寡', '老弱', '常人', '庸人', '小人', '愚者',
    '妄人', '竖', '竖子', '小子',
}

EXPLICIT_KIN = {
    # 直系
    '父', '母', '子', '女', '兄', '弟', '姊', '妹', '嫂', '叔',
    '伯', '舅', '婿', '赘婿', '妻', '妾', '夫', '妇', '祖', '孙',
    # 组合
    '父母', '父子', '父兄', '父老', '兄弟', '夫妇', '夫子',
    '妻子', '妻妾', '母子', '父母妻子', '子女', '子弟', '子孙',
    '男女', '昆弟', '群弟', '少弟', '小弟', '小弱弟', '大叔',
    '太叔', '女弟', '族子', '族长', '亲', '亲戚', '宗人', '宗戚',
    '宗族', '苗裔', '后子', '遗腹子', '他子', '二子', '少子',
    '长子', '长男', '中子', '诸子', '诸子孙', '诸子弟', '群公子',
    # 尊卑
    '世子', '嫡子', '庶子', '嗣子', '適子', '適孙', '適长孙',
    '质子', '元孙', '曾孙', '外孙', '女孙', '庶孙', '姑姊',
    '家属', '祖宗', '先人', '先祖',
    # 仇/友/邻
    '仇', '知友乡党', '诸公',
    '母弟', '父母', '寡', '姬', '从妹',
}

EXPLICIT_MERCHANT = {
    '商', '贾', '贾人', '商者', '商贾', '贩卖贾人', '富人', '富豪',
    '贫', '贫人', '贫者', '贫民', '贫穷', '财者', '饥民',
    '豪', '豪杰', '豪桀', '豪俊', '豪举', '豪吏', '俊桀',
    '俊雄', '夸者', '水工', '削厉工',
}

EXPLICIT_OUTCAST = {
    '盗', '贼', '奸人', '盗贼', '群盗', '寇', '贪夫', '罪人',
    '囚', '刑人', '胥靡', '徒', '徒役', '亡命', '亡人', '逋亡',
    '逋亡人', '奴', '奴婢', '嬖人', '不臣者', '不肖者', '弃',
    '不肖', '妒妻', '狗盗者',
}

EXPLICIT_FOREIGN = {
    '单于', '阏氏', '右贤王', '左贤王', '左右贤王', '大当户',
    '大且渠', '右王', '左王', '戎王', '繇王', '浑邪', '浑邪王',
    '日逐王', '因淳王', '楼剸王', '符离王', '西于王', '若苴王',
    '车师王', '休屠王', '归义', '小国', '彊国', '群神', '司命',
}

EXPLICIT_GENERIC = {
    '众人', '三代', '群神',  # 纯泛称
}

# 人名误标：具体可考证的人名被误标为 identity
EXPLICIT_PERSON_MIS = {
    '刘邦',       # 汉高祖（本人）
    '栗太子',     # 景帝废太子刘荣
    '帝太戊',     # 商王太戊
    '帝武丁',     # 商王武丁
    '郑君',       # 项伯父（具体人物）— 亦可归爵衔，视上下文
    '番君',       # 吴芮（具体人物）
    '留侯',       # 张良封号
    '浑邪',       # 匈奴浑邪王（具体人物）
    '大鸿',       # 大鸿胪的简称，应是 official
    '毋',         # 单字"毋"不成身份，多为人名或动词误标
    '善',         # 单字"善"为概念/赞语，非身份
}


# 汇总白名单
WHITELIST = [
    (CAT_RULER, EXPLICIT_RULER),
    (CAT_ROYAL, EXPLICIT_ROYAL),
    (CAT_CONSORT, EXPLICIT_CONSORT),
    (CAT_NOBLE, EXPLICIT_NOBLE),
    (CAT_MINISTER, EXPLICIT_MINISTER),
    (CAT_GENTRY, EXPLICIT_GENTRY),
    (CAT_MILITARY, EXPLICIT_MILITARY),
    (CAT_GUEST, EXPLICIT_GUEST),
    (CAT_COMMONER, EXPLICIT_COMMONER),
    (CAT_KIN, EXPLICIT_KIN),
    (CAT_MERCHANT, EXPLICIT_MERCHANT),
    (CAT_OUTCAST, EXPLICIT_OUTCAST),
    (CAT_FOREIGN, EXPLICIT_FOREIGN),
    (CAT_GENERIC, EXPLICIT_GENERIC),
]


def classify_l1_whitelist(name: str) -> list:
    """L1: 显式白名单（多标签）"""
    # 人名误标单标签、早返回
    if name in EXPLICIT_PERSON_MIS:
        return [CAT_PERSON_MIS]

    cats = []
    for cat, whitelist in WHITELIST:
        if name in whitelist:
            cats.append(cat)
    return cats


# ─── L2: 后缀/关键字启发式 ───

def _already_in_any(name, *whitelists) -> bool:
    for wl in whitelists:
        if name in wl:
            return True
    return False


def classify_l2_suffix(name: str) -> list:
    """L2: 根据字符/后缀推断类别（多标签）

    重要：若名字已在"主类白名单"（君主/宗室/后妃/爵衔/外邦/人名误标）中，
    则跳过泛后缀（人/子/民/者），避免"天子→血缘""夫人→庶民"等错配。
    """
    cats = []
    has_primary = _already_in_any(
        name,
        EXPLICIT_RULER, EXPLICIT_ROYAL, EXPLICIT_CONSORT,
        EXPLICIT_NOBLE, EXPLICIT_FOREIGN, EXPLICIT_PERSON_MIS,
    )

    # 强后缀（不受 primary 屏蔽）
    if name.endswith('臣') and name not in EXPLICIT_MINISTER:
        cats.append(CAT_MINISTER)
    if name.endswith('士') and name not in EXPLICIT_GENTRY:
        cats.append(CAT_GENTRY)
    if name.endswith('将') and name not in EXPLICIT_MILITARY and len(name) <= 4:
        cats.append(CAT_MILITARY)
    if name.endswith('卒') and name not in EXPLICIT_MILITARY:
        cats.append(CAT_MILITARY)
    if name.endswith('兵') and name not in EXPLICIT_MILITARY:
        cats.append(CAT_MILITARY)
    if name.endswith('王') and len(name) >= 2 and name not in EXPLICIT_FOREIGN \
            and name not in EXPLICIT_RULER:
        if any(name.startswith(p) for p in ('单于', '右', '左', '休', '浑', '车')):
            cats.append(CAT_FOREIGN)
        else:
            cats.append(CAT_RULER)
    if name.endswith('君') and len(name) >= 2 and name not in EXPLICIT_NOBLE \
            and name not in EXPLICIT_RULER:
        cats.append(CAT_RULER)
    if name.endswith('侯') and len(name) >= 2 and name not in EXPLICIT_NOBLE:
        cats.append(CAT_NOBLE)
    if name.endswith('儒') or (name.endswith('生') and len(name) <= 3):
        if name not in EXPLICIT_GENTRY:
            cats.append(CAT_GENTRY)
    if name.endswith('吏') and name not in EXPLICIT_MINISTER:
        cats.append(CAT_MINISTER)
    if name.endswith('客') and name not in EXPLICIT_GUEST:
        cats.append(CAT_GUEST)
    if (name.endswith('妻') or name.endswith('妾') or name.endswith('妃')) \
            and not _already_in_any(name, EXPLICIT_KIN, EXPLICIT_CONSORT):
        cats.append(CAT_CONSORT)
    if (name.endswith('公主') or name.endswith('太子') or name.endswith('太后')
            or name.endswith('皇后') or name.endswith('皇帝')) \
            and name not in EXPLICIT_ROYAL:
        cats.append(CAT_ROYAL)

    # 弱后缀（primary 白名单已命中则跳过，避免过度标注）
    if not has_primary:
        if name.endswith('子') and name not in EXPLICIT_KIN and len(name) <= 3:
            cats.append(CAT_KIN)
        if name.endswith('孙') and len(name) <= 3 and name not in EXPLICIT_KIN:
            cats.append(CAT_KIN)
        if name.endswith('民') and name not in EXPLICIT_COMMONER:
            cats.append(CAT_COMMONER)
        if name.endswith('人') and not _already_in_any(
                name, EXPLICIT_COMMONER, EXPLICIT_GUEST, EXPLICIT_GENTRY):
            cats.append(CAT_COMMONER)
        if name.endswith('者') and not _already_in_any(
                name, EXPLICIT_GENTRY, EXPLICIT_GUEST, EXPLICIT_COMMONER):
            cats.append(CAT_GENTRY)
        if (name.endswith('母') or name.endswith('父') or name.endswith('兄')
                or name.endswith('弟')) and name not in EXPLICIT_KIN:
            cats.append(CAT_KIN)

    seen = set()
    out = []
    for c in cats:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


# ─── 置信度评分 ───

def score_evidence(final_cats, l1, l2) -> dict:
    """为每个 (name, cat) 组合打分 0-1。"""
    out = {}
    for cat in final_cats:
        score = 0.0
        if cat in l1:
            score += 0.6
        if cat in l2:
            score += 0.3
        # 没有任何证据的默认兜底 0.1
        if score == 0.0:
            score = 0.1
        out[cat] = round(min(1.0, score), 2)
    return out


# ─── 主流程 ───

def main():
    print('━' * 60)
    print('身份分类脚本 classify_identities.py')
    print('━' * 60)

    index = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
    identities = index.get('identity', {})
    names = list(identities.keys())
    print(f'身份实体总数: {len(names)}')
    print()

    # ── 按条目分类 ──
    name_to_cats = {}
    name_to_details = {}
    for name in names:
        l1 = classify_l1_whitelist(name)
        l2 = classify_l2_suffix(name)

        final = []
        if l1 == [CAT_PERSON_MIS]:
            final = [CAT_PERSON_MIS]
        else:
            for c in l1:
                if c not in final:
                    final.append(c)
            for c in l2:
                if c not in final:
                    final.append(c)
            # 兜底
            if not final:
                final = [CAT_GENERIC]

        name_to_cats[name] = final
        name_to_details[name] = dict(l1=l1, l2=l2)

    # ── 置信度 ──
    confidence = {}
    for name, cats in name_to_cats.items():
        if not cats:
            continue
        d = name_to_details[name]
        confidence[name] = score_evidence(cats, l1=d['l1'], l2=d['l2'])

    # ── 写出 ──
    OUT_JSON.write_text(
        json.dumps(name_to_cats, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    OUT_CONF_JSON.write_text(
        json.dumps(confidence, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    # ── 统计 ──
    cat_counter = Counter()
    multi_label = 0
    only_generic = []
    for name, cats in name_to_cats.items():
        for c in cats:
            cat_counter[c] += 1
        if len(cats) > 1:
            multi_label += 1
        if cats == [CAT_GENERIC]:
            only_generic.append(name)

    print('━' * 60)
    print('分类结果')
    print('━' * 60)
    total = len(name_to_cats)
    for cat, n in sorted(cat_counter.items(), key=lambda x: -x[1]):
        print(f'  {cat:<10} {n:>5}  ({n / total * 100:.1f}%)')
    print(f'  {"多标签":<10} {multi_label:>5}  ({multi_label / total * 100:.1f}%)')
    print()
    print(f'仅泛称（需人工审查，前 40）: {only_generic[:40]}')
    print()
    print(f'写入: {OUT_JSON}')
    print(f'写入: {OUT_CONF_JSON}')


if __name__ == '__main__':
    main()
