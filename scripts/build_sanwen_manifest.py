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
]

# 剔除：叙事性 section 或与其他类别重复（chapter + start_para 白名单式剔除）
# 判定标准：不是一篇独立的"文章"，而是传记中的叙事/对话段落
DROP = {
    ("006", "116"),   # 贾生议论范围错，已手工重写
    ("048", "16.1"),  # 同上
    ("040", "49"),    # 叔向论子比不能立（预言对话）
    # —— 叙事性质，非独立文章 ——
    ("028", "72"),    # 武帝祠太一与封禅准备（含多诏但主体是叙事）
    ("028", "87"),    # 武帝封禅泰山（叙事）
    ("043", "36"),    # 霍太山神谕（神话）
    ("047", "9.2"),   # 孔子出仕为政（叙事）
    ("056", "11"),    # 陈平数易其主（叙事）
    ("057", "15"),    # 周亚夫（叙事）
    ("058", "27"),    # 梁孝王褚先生曰（论赞性质）
    ("064", "1"),     # 司马穰苴受命将兵（叙事）
    ("065", "1"),     # 孙武练兵（叙事）
    ("065", "11"),    # 吴起论德与险（对话）
    ("066", "11"),    # 伍子胥入郢鞭尸（叙事）
    ("071", "9"),     # 甘茂息壤设盟（叙事）
    ("073", "12"),    # 王翦请田自坚（叙事）
    ("075", "13"),    # 冯驩弹铗焚券（叙事）
    ("076", "2"),     # 平原君养士（叙事）
    ("078", "19"),    # 春申君献女求嗣（叙事）
    ("079", "15"),    # 范睢离宫陈大计（对话）
    ("079", "24"),    # 逼赵追杀魏齐案（叙事含短信）
    ("080", "3"),     # 乐毅合纵伐齐（叙事）
    ("088", "8"),     # 蒙毅辩解（对话）
    ("096", "14"),    # 张苍为相（叙事）
    ("103", "11"),    # 石庆事迹（叙事，误判为诏令）
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
    ("130", "36"),    # 自序李陵之祸（叙事）
}

# 段落范围覆盖：(章, 起段) -> 新的 end_para
END_OVERRIDE: dict[tuple[str, str], str] = {
    ("060", "9"): "16",   # 含"右广陵王策"收束句
    ("110", "53"): "53",  # 只保留诏令本体，剔除后续叙事
}

# 改名表：(章, 起段) -> (新标题, 新类型?)  新类型 None 则保留原类型
RENAME: dict[tuple[str, str], tuple[str, str | None]] = {
    ("007", "47.1"): ("陈馀遗章邯书", "书信"),
    ("010", "41.2"): ("汉文帝遗诏", None),
    ("028", "46"): ("汉文帝初祠五畤诏", None),
    ("038", "9"): ("箕子陈洪范", "议论"),
    ("040", "83"): ("齐使遗楚王书", None),
    ("043", "81"): ("苏厉遗赵惠文王书", None),
    ("060", "1"): ("群臣请立皇子为王疏", "奏疏"),
    ("060", "9"): ("汉武帝立三王册书", None),  # 下方 END_OVERRIDE 将 end 扩展到 16
    ("069", "48"): ("苏代遗燕昭王书", None),
    ("072", "8"): ("须贾遗穰侯书", None),
    ("079", "7"): ("范睢上秦昭王书", None),
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
    ("117", "13"): ("司马相如遗札论封禅", None),
    ("130", "11"): ("司马谈论六家要旨·墨家", None),
    ("130", "14"): ("司马谈论六家要旨·道家", None),
    ("130", "28"): ("司马谈论六家要旨·儒家与六经", None),
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
