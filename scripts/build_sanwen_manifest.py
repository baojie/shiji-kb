#!/usr/bin/env python3
"""
根据 scan_sanwen_candidates.py 输出，构造精选 manifest。

输入: labs/planning/sanwen_candidates.json
输出: data/sanwen_manifest.json

规则：
- 诏令/奏疏/书信/檄文：全部采纳（scanner已做长度过滤）
- 策论：只保留 >=400 字 且 有明确 H2 标题（非"xx 传""xx 世家"通名）的
- 议论：scanner 命中的 006/048 贾生议论范围不准，剔除；改由手工补充 过秦论 三段
- 为去重，相同 (chapter_num, start_para) 以 scanner 条目为准

外加手工条目：过秦论（上/中/下）在 006，以及 048 褚先生引过秦论上
"""

from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "labs" / "planning" / "sanwen_candidates.json"
DST = ROOT / "data" / "sanwen_manifest.json"

TYPE_DESC = {
    "诏令": "帝王颁布的诏书、制诏、遗诏等",
    "奏疏": "臣下上奏皇帝的疏议、上书、上言",
    "书信": "人物之间往来的书信、国书",
    "檄文": "声讨、宣谕性质的檄文",
    "谏言": "臣下谏诤君主的政论性言辞",
    "策论": "对策、长篇建议、策士说辞",
    "议论": "长篇议论性散文（如过秦论）",
}

# 手工补充：确切段落范围
MANUAL_ENTRIES = [
    {
        "chapter_num": "006",
        "chapter_title": "秦始皇本纪",
        "type": "议论",
        "title": "贾谊过秦论上",
        "start_para": "117",
        "end_para": "124.2",
        "intro": "太史公曰：善哉乎贾生推言之也！曰——",
    },
    {
        "chapter_num": "006",
        "chapter_title": "秦始皇本纪",
        "type": "议论",
        "title": "贾谊过秦论中",
        "start_para": "125",
        "end_para": "134.3",
    },
    {
        "chapter_num": "006",
        "chapter_title": "秦始皇本纪",
        "type": "议论",
        "title": "贾谊过秦论下",
        "start_para": "135",
        "end_para": "139.4",
    },
    {
        "chapter_num": "048",
        "chapter_title": "陈涉世家",
        "type": "议论",
        "title": "贾谊过秦论上（褚先生引）",
        "start_para": "17",
        "end_para": "17.99",  # 覆盖所有 [17.x]
        "intro": "褚先生曰：……吾闻贾生之称曰——",
    },
    {
        "chapter_num": "040",
        "chapter_title": "楚世家",
        "type": "书信",
        "title": "秦昭王遗楚怀王书",
        "start_para": "86",
        "end_para": "86",
    },
    {
        "chapter_num": "040",
        "chapter_title": "楚世家",
        "type": "书信",
        "title": "秦昭王遗楚顷襄王书",
        "start_para": "89",
        "end_para": "89",
    },
    {
        "chapter_num": "075",
        "chapter_title": "孟尝君列传",
        "type": "书信",
        "title": "孟尝君遗穰侯书",
        "start_para": "12",
        "end_para": "12",
    },
    {
        "chapter_num": "080",
        "chapter_title": "乐毅列传",
        "type": "书信",
        "title": "乐毅报燕惠王书（附燕惠王让乐毅书）",
        "start_para": "6",
        "end_para": "13",
    },
    {
        "chapter_num": "080",
        "chapter_title": "乐毅列传",
        "type": "书信",
        "title": "燕王遗乐间书",
        "start_para": "16",
        "end_para": "16",
    },
    {
        "chapter_num": "083",
        "chapter_title": "鲁仲连邹阳列传",
        "type": "书信",
        "title": "鲁仲连遗燕将书（射聊城）",
        "start_para": "10.4",
        "end_para": "13",
    },
    {
        "chapter_num": "083",
        "chapter_title": "鲁仲连邹阳列传",
        "type": "奏疏",
        "title": "邹阳狱中上梁王书",
        "start_para": "15",
        "end_para": "25",
    },
    {
        "chapter_num": "117",
        "chapter_title": "司马相如列传",
        "type": "书信",
        "title": "司马相如遗札论封禅",
        "start_para": "14",
        "end_para": "14",
    },
    {
        "chapter_num": "002",
        "chapter_title": "夏本纪",
        "type": "谏言",
        "title": "皋陶谟",
        "start_para": "17",
        "end_para": "17.13",
    },
    {
        "chapter_num": "004",
        "chapter_title": "周本纪",
        "type": "谏言",
        "title": "祭公谋父谏穆王征犬戎",
        "start_para": "25",
        "end_para": "25",
    },
    {
        "chapter_num": "004",
        "chapter_title": "周本纪",
        "type": "诏令",
        "title": "穆王甫刑",
        "start_para": "26",
        "end_para": "26",
    },
    {
        "chapter_num": "004",
        "chapter_title": "周本纪",
        "type": "谏言",
        "title": "芮良夫谏厉王",
        "start_para": "29",
        "end_para": "29",
    },
    {
        "chapter_num": "004",
        "chapter_title": "周本纪",
        "type": "谏言",
        "title": "召公谏厉王止谤",
        "start_para": "30",
        "end_para": "30",
    },
    {
        "chapter_num": "004",
        "chapter_title": "周本纪",
        "type": "议论",
        "title": "伯阳甫论三川地震",
        "start_para": "35",
        "end_para": "35",
    },
    {
        "chapter_num": "043",
        "chapter_title": "赵世家",
        "type": "策论",
        "title": "赵武灵王胡服骑射论",
        "start_para": "67",
        "end_para": "67",
    },
    {
        "chapter_num": "076",
        "chapter_title": "平原君虞卿列传",
        "type": "策论",
        "title": "虞卿赂齐制秦策",
        "start_para": "15",
        "end_para": "16",
    },
    {
        "chapter_num": "078",
        "chapter_title": "春申君列传",
        "type": "策论",
        "title": "春申君说秦昭王",
        "start_para": "1",
        "end_para": "9",
    },
    {
        "chapter_num": "079",
        "chapter_title": "范睢蔡泽列传",
        "type": "奏疏",
        "title": "范睢上秦昭王书",
        "start_para": "7",
        "end_para": "13",
    },
    {
        "chapter_num": "079",
        "chapter_title": "范睢蔡泽列传",
        "type": "策论",
        "title": "范睢说秦昭王三事（远交近攻·收韩·逐四贵）",
        "start_para": "15",
        "end_para": "17",
    },
    {
        "chapter_num": "079",
        "chapter_title": "范睢蔡泽列传",
        "type": "策论",
        "title": "蔡泽说范睢功成身退",
        "start_para": "32",
        "end_para": "32",
    },
    {
        "chapter_num": "083",
        "chapter_title": "鲁仲连邹阳列传",
        "type": "策论",
        "title": "鲁仲连论帝秦之害",
        "start_para": "7.6",
        "end_para": "7.6",
    },
    {
        "chapter_num": "043",
        "chapter_title": "赵世家",
        "type": "谏言",
        "title": "触龙说赵太后",
        "start_para": "95",
        "end_para": "95",
    },
    {
        "chapter_num": "044",
        "chapter_title": "魏世家",
        "type": "谏言",
        "title": "李克论相",
        "start_para": "18",
        "end_para": "18",
    },
    {
        "chapter_num": "046",
        "chapter_title": "田敬仲完世家",
        "type": "谏言",
        "title": "邹忌以琴喻治国",
        "start_para": "14.1",
        "end_para": "14.1",
    },
    {
        "chapter_num": "046",
        "chapter_title": "田敬仲完世家",
        "type": "策论",
        "title": "苏代谓田轸论齐楚救赵",
        "start_para": "21.1",
        "end_para": "21.1",
    },
    {
        "chapter_num": "046",
        "chapter_title": "田敬仲完世家",
        "type": "谏言",
        "title": "苏代谏齐王释帝号",
        "start_para": "22.1",
        "end_para": "22.1",
    },
    {
        "chapter_num": "054",
        "chapter_title": "曹相国世家",
        "type": "谏言",
        "title": "曹参论守法无为",
        "start_para": "15",
        "end_para": "15",
    },
    {
        "chapter_num": "069",
        "chapter_title": "苏秦列传",
        "type": "策论",
        "title": "苏秦说赵王合从",
        "start_para": "8",
        "end_para": "16",
    },
    {
        "chapter_num": "069",
        "chapter_title": "苏秦列传",
        "type": "策论",
        "title": "苏秦说韩王合从",
        "start_para": "19",
        "end_para": "21",
    },
    {
        "chapter_num": "069",
        "chapter_title": "苏秦列传",
        "type": "策论",
        "title": "苏秦说魏王合从",
        "start_para": "22",
        "end_para": "25",
    },
    {
        "chapter_num": "069",
        "chapter_title": "苏秦列传",
        "type": "策论",
        "title": "苏秦说齐王合从",
        "start_para": "26",
        "end_para": "29",
    },
    {
        "chapter_num": "069",
        "chapter_title": "苏秦列传",
        "type": "策论",
        "title": "苏秦说楚王合从",
        "start_para": "30",
        "end_para": "34",
    },
    {
        "chapter_num": "072",
        "chapter_title": "穰侯列传",
        "type": "策论",
        "title": "须贾说穰侯罢梁围",
        "start_para": "6",
        "end_para": "6",
    },
    {
        "chapter_num": "070",
        "chapter_title": "张仪列传",
        "type": "策论",
        "title": "张仪说楚王连横",
        "start_para": "24",
        "end_para": "32",
    },
    {
        "chapter_num": "070",
        "chapter_title": "张仪列传",
        "type": "策论",
        "title": "张仪说韩王连横",
        "start_para": "34",
        "end_para": "37",
    },
    {
        "chapter_num": "070",
        "chapter_title": "张仪列传",
        "type": "策论",
        "title": "张仪说齐王连横",
        "start_para": "39",
        "end_para": "40",
    },
    {
        "chapter_num": "070",
        "chapter_title": "张仪列传",
        "type": "策论",
        "title": "张仪说赵王连横",
        "start_para": "41",
        "end_para": "45",
    },
    {
        "chapter_num": "070",
        "chapter_title": "张仪列传",
        "type": "策论",
        "title": "张仪说燕王连横",
        "start_para": "46",
        "end_para": "49",
    },
    {
        "chapter_num": "063",
        "chapter_title": "老子韩非列传",
        "type": "议论",
        "title": "韩非子说难",
        "start_para": "16",
        "end_para": "24",
    },
    {
        "chapter_num": "068",
        "chapter_title": "商君列传",
        "type": "策论",
        "title": "商鞅变法三辩",
        "start_para": "3",
        "end_para": "3",
    },
    {
        "chapter_num": "091",
        "chapter_title": "黥布列传",
        "type": "策论",
        "title": "随何说黥布叛楚归汉",
        "start_para": "7",
        "end_para": "7",
    },
    {
        "chapter_num": "092",
        "chapter_title": "淮阴侯列传",
        "type": "策论",
        "title": "韩信论项羽汉王优劣",
        "start_para": "6",
        "end_para": "6",
    },
    {
        "chapter_num": "099",
        "chapter_title": "刘敬叔孙通列传",
        "type": "谏言",
        "title": "娄敬谏都关中",
        "start_para": "2",
        "end_para": "2",
    },
    {
        "chapter_num": "102",
        "chapter_title": "张释之冯唐列传",
        "type": "谏言",
        "title": "冯唐论将",
        "start_para": "13",
        "end_para": "13",
    },
    {
        "chapter_num": "108",
        "chapter_title": "韩长孺列传",
        "type": "谏言",
        "title": "韩安国谏梁王",
        "start_para": "5",
        "end_para": "5",
    },
    {
        "chapter_num": "118",
        "chapter_title": "淮南衡山列传",
        "type": "谏言",
        "title": "伍被谏淮南王不可反",
        "start_para": "18.1",
        "end_para": "18.1",
    },
    {
        "chapter_num": "126",
        "chapter_title": "滑稽列传",
        "type": "谏言",
        "title": "淳于髡讽谏齐威王",
        "start_para": "5",
        "end_para": "5",
    },
    {
        "chapter_num": "130",
        "chapter_title": "太史公自序",
        "type": "议论",
        "title": "司马谈论六家要旨",
        "start_para": "7",
        "end_para": "17",
    },
    {
        "chapter_num": "130",
        "chapter_title": "太史公自序",
        "type": "议论",
        "title": "司马迁论春秋与六经",
        "start_para": "27",
        "end_para": "35",
    },
    {
        "chapter_num": "092",
        "chapter_title": "淮阴侯列传",
        "type": "策论",
        "title": "武涉说齐王韩信连楚",
        "start_para": "18",
        "end_para": "18",
    },
    {
        "chapter_num": "092",
        "chapter_title": "淮阴侯列传",
        "type": "策论",
        "title": "蒯通三说韩信三分天下",
        "start_para": "19",
        "end_para": "21",
    },
]

# 剔除：叙事性 section 或与其他类别重复（chapter + start_para 白名单式剔除）
# 判定标准：不是一篇独立的"文章"，而是传记中的叙事/对话段落
DROP = {
    ("006", "116"),   # 贾生议论范围错，已手工重写
    ("048", "16.1"),  # 同上
    # —— 叙事性质，非独立文章 ——
    ("028", "72"),    # 武帝祠太一与封禅准备（含多诏但主体是叙事）
    ("028", "87"),    # 武帝封禅泰山（叙事）
    ("043", "36"),    # 霍太山神谕（神话）
    ("047", "9.2"),   # 孔子出仕为政（叙事）
    ("056", "11"),    # 陈平数易其主（叙事）
    ("057", "15"),    # 周亚夫（叙事）
    ("064", "1"),     # 司马穰苴受命将兵（叙事）
    ("065", "1"),     # 孙武练兵（叙事）
    ("066", "11"),    # 伍子胥入郢鞭尸（叙事）
    ("071", "9"),     # 甘茂息壤设盟（叙事）
    ("073", "12"),    # 王翦请田自坚（叙事）
    ("075", "13"),    # 冯驩弹铗焚券（叙事）
    ("076", "2"),     # 平原君养士（叙事）
    ("078", "19"),    # 春申君献女求嗣（叙事）
    ("079", "24"),    # 逼赵追杀魏齐案（叙事含短信）
    ("080", "3"),     # 乐毅合纵伐齐（叙事）
    ("088", "8"),     # 蒙毅辩解（对话）
    ("096", "14"),    # 张苍为相（叙事）
    ("103", "11"),    # 石庆事迹（叙事，误判为诏令）
    ("107", "24"),    # 魏其灌夫之死（叙事，非独立散文）
    ("108", "12"),    # 韩安国晚年（叙事）
    ("112", "56"),    # 徐乐严安"俱上书"引入段（非文章本体）
    ("112", "102"),   # 主父偃被诛（叙事）
    ("114", "3"),     # 闽越围东瓯（叙事）
    ("118", "26"),    # 衡山王家乱（叙事）
    ("121", "6"),     # 武帝崇儒与学官制度（叙事混合）
    ("121", "14"),    # 伏生传尚书（叙事）
    ("122", "37"),    # 酷吏盗贼蜂起（叙事，非檄文）
    ("123", "24"),    # 大宛汉通西域（叙事）
    ("123", "31"),    # 贰师将军伐宛（叙事）
    ("126", "7"),     # 优孟衣冠（叙事）
    ("126", "21"),    # 东郭先生献策（叙事）
    ("128", "10"),    # 杀龟之辩（对话）
    # —— 2026-04-15 scanner 扩展后新浮现的叙事型 H2，批量剔除 ——
    ("012", "22.12"), # 泰一祠坛（封禅叙事）
    ("020", "2.3"),   # 建元以来侯者年表·表序（H2误触）
    ("074", "2"),     # 孟子荀卿列传·孟轲游说不遇（叙事）
    ("077", "6"),     # 信陵君列传·窃符救赵（叙事）
    ("081", "16.4"),  # 廉蔺列传·赵括其人（叙事）
    ("084", "15.1"), # 屈原贾生列传·贾生之死（叙事）
    ("109", "13"),    # 李广列传·生平（叙事）
    ("127", "38"),    # 日者列传·褚先生补述（叙事）
    ("128", "16"),    # 龟策列传·宋元王得龟（叙事）
    ("130", "11"),    # 六家要旨·墨家（已合并为完整一篇）
    ("130", "14"),    # 六家要旨·道家（已合并为完整一篇）
    ("130", "28"),    # 论春秋与六经：scanner [28-31] 已由 MANUAL [27-35] 覆盖
    ("044", "57"),    # 魏世家·中旗之谏（短对话，非独立文章）
    ("112", "114"),   # 由 MANUAL_ENTRIES 中 112/108 覆盖，scanner 范围错误
    ("117", "13"),    # 由 MANUAL_ENTRIES 覆盖：剔除 [13] 大人赋intro 与 [15-16] 尾部叙事
}

# 段落范围覆盖：(章, 起段) -> 新的 end_para
END_OVERRIDE: dict[tuple[str, str], str] = {
    ("060", "9"): "16",   # 含"右广陵王策"收束句
    ("110", "53"): "53",  # 只保留诏令本体，剔除后续叙事
    ("072", "8"): "8",    # 苏代书信本体，剔除 [9]+ 穰侯被免相后续叙事
    ("079", "15"): "17",  # 范睢说秦昭王：远交近攻·收韩·逐四贵三说
    ("040", "49"): "49",  # 叔向论子比不能立（仅保留[49]全篇说词）
    ("038", "9"): "19",   # 箕子陈洪范完整九畴（含三德/稽疑/庶徵/五福六极）
    ("058", "27"): "27",  # 褚先生论梁王储位与春秋大义
    ("065", "11"): "11",  # 吴起论在德不在险
    ("055", "15"): "15",  # 张良借箸止封六国（原 [15-21] 混入封赏/都关中等叙事）
    ("130", "36"): "38",  # 太史公发愤著书
    ("092", "13"): "13",  # 广武君献策本体，剔除 [14-19] 叙事及 蒯通/武涉 别篇（另立 MANUAL）
}

# 改名表：(章, 起段) -> (新标题, 新类型?)  新类型 None 则保留原类型
RENAME: dict[tuple[str, str], tuple[str, str | None]] = {
    ("007", "47.1"): ("陈馀遗章邯书", "书信"),
    ("010", "41.2"): ("汉文帝遗诏", None),
    ("028", "46"): ("汉文帝初祠五畤诏", None),
    ("038", "9"): ("箕子陈洪范", "谏言"),
    ("040", "83"): ("齐使遗楚王书", None),
    ("043", "81"): ("苏厉遗赵惠文王书", None),
    ("060", "1"): ("群臣请立皇子为王疏", "奏疏"),
    ("060", "9"): ("汉武帝立三王册书", None),  # 下方 END_OVERRIDE 将 end 扩展到 16
    ("069", "48"): ("苏代遗燕昭王书", None),
    ("072", "8"): ("苏代为齐阴遗穰侯书", None),
    ("079", "7"): ("范睢上秦昭王书", None),
    ("079", "15"): ("范睢说秦昭王三事（远交近攻·收韩·逐四贵）", None),
    ("040", "49"): ("叔向论子比不能立（五难论）", None),
    ("058", "27"): ("褚先生论梁王储位与春秋大义", "议论"),
    ("065", "11"): ("吴起论在德不在险", None),
    ("055", "15"): ("张良借箸止封六国", None),
    ("130", "36"): ("太史公发愤著书", "议论"),
    ("081", "3.2"): ("秦昭王遗赵惠文王请易璧书", None),
    ("084", "10.3"): ("贾谊改制建议", None),
    ("087", "4.1"): ("李斯谏逐客书", None),
    ("087", "6.2"): ("李斯请禁百家议", None),
    ("087", "14.3"): ("李斯上书言赵高", None),
    ("087", "16.3"): ("李斯狱中上书", None),
    ("106", "9"): ("吴王濞遗诸侯书", None),
    ("106", "16"): ("汉景帝讨吴楚诏", None),
    ("110", "39"): ("冒顿单于遗汉书", None),
    ("110", "40"): ("汉文帝遗匈奴书", None),
    ("110", "51"): ("汉文帝遗匈奴书（后二年）", None),
    ("110", "53"): ("汉文帝与匈奴和亲制诏", None),
    ("112", "28"): ("公孙弘临终上书", None),
    ("112", "40"): ("主父偃谏伐匈奴书", None),
    ("112", "70"): ("严安上书", None),
    ("117", "3"): ("司马相如谕巴蜀檄", None),
    ("117", "7"): ("司马相如谏猎疏", None),
    # 130 六家要旨：三个拆散条目已由 MANUAL_ENTRIES 合并覆盖
    # —— scanner 自动发现后的标题优化 ——
    ("010", "28.5"): ("缇萦救父上书", None),
    ("010", "43.1"): ("汉景帝追尊文帝庙乐诏", None),
    ("070", "5"): ("司马错张仪论伐蜀", "策论"),
    ("076", "11"): ("虞卿论长平勿媾割地", None),
    ("092", "13"): ("广武君献北燕东齐策", None),
}

# 策论白名单：保留有明确 H2 的、>=400 字的
STRATEGY_KEEP_MIN_CHARS = 400


def main() -> int:
    cands = json.loads(SRC.read_text(encoding="utf-8"))
    out = []

    for c in cands:
        key = (c["chapter_num"], c["start_para"])
        if key in DROP:
            continue
        t = c["type"]
        if t == "策论":
            if c["char_count"] < STRATEGY_KEEP_MIN_CHARS:
                continue
            # 标题通名（含"世家/列传/本纪"）则跳过
            title = c.get("suggested_title", "")
            if any(x in title for x in ("世家", "列传", "本纪", "书")):
                # "书" 会把名为"XX书"的章节也滤掉，但这类多为泛 H2
                if not any(k in title for k in ("论", "策", "对", "谏", "书曰")):
                    continue
        end_para = END_OVERRIDE.get(key, c["end_para"])
        rn = RENAME.get(key)
        title = rn[0] if rn else c["suggested_title"]
        if rn and rn[1]:
            t = rn[1]
        out.append({
            "chapter_num": c["chapter_num"],
            "chapter_title": c["chapter_title"],
            "type": t,
            "title": title,
            "start_para": c["start_para"],
            "end_para": end_para,
            "char_count": c["char_count"],
            "section_heading": c.get("section_heading", ""),
        })

    # MANUAL_ENTRIES 覆盖同 (chapter_num, start_para) 的自动条目
    manual_keys = {(e["chapter_num"], e["start_para"]) for e in MANUAL_ENTRIES}
    out = [e for e in out if (e["chapter_num"], e["start_para"]) not in manual_keys]
    out.extend(MANUAL_ENTRIES)

    # 排序
    def sort_key(e):
        return (e["chapter_num"], _para_tuple(e["start_para"]))
    out.sort(key=sort_key)

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # 统计
    by_type: dict[str, int] = {}
    for e in out:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
    print(f"Manifest 共 {len(out)} 条 → {DST}")
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")
    return 0


def _para_tuple(s: str) -> tuple:
    try:
        return tuple(int(x) for x in s.split("."))
    except ValueError:
        return (0,)


if __name__ == "__main__":
    raise SystemExit(main())
