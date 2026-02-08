#!/usr/bin/env python3
"""修复 sections_data.json 中仍然超过20节的章节（第二批）。"""

import json
import os

def main():
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sections_data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    new_sections = {}

    # === 006_秦始皇本纪: 22节 → 10节 ===
    new_sections["006_秦始皇本纪"] = [
        {"anchor": "1", "title": "秦王政时期"},
        {"anchor": "10.1", "title": "嫪毐之乱与逐客"},
        {"anchor": "22.1", "title": "统一天下与称帝"},
        {"anchor": "42.1", "title": "巡游封禅"},
        {"anchor": "65.1", "title": "阿房宫、坑儒与晚年"},
        {"anchor": "76.1", "title": "始皇崩与秦二世"},
        {"anchor": "96.1", "title": "陈胜起义与秦亡"},
        {"anchor": "112.1", "title": "秦王子婴"},
        {"anchor": "125.1", "title": "贾谊《过秦论》"},
        {"anchor": "140", "title": "秦世系表与诏书"},
    ]

    # === 027_天官书: 22节 → 10节 ===
    new_sections["027_天官书"] = [
        {"anchor": "1", "title": "中宫紫微垣"},
        {"anchor": "7", "title": "四宫二十八宿"},
        {"anchor": "25", "title": "五星运行规律"},
        {"anchor": "53", "title": "太白辰星占验"},
        {"anchor": "67", "title": "分野与日月食"},
        {"anchor": "86", "title": "彗孛云气占验"},
        {"anchor": "104", "title": "地象物候与候岁"},
        {"anchor": "111", "title": "太史公论天官"},
        {"anchor": "118", "title": "秦汉天变实录"},
        {"anchor": "122", "title": "观象修德之要"},
    ]

    # === 030_平准书: 49节 → 10节 ===
    new_sections["030_平准书"] = [
        {"anchor": "1", "title": "汉初经济与币制改革"},
        {"anchor": "6", "title": "武帝初年的国家富庶"},
        {"anchor": "9", "title": "对外战争与财政困难"},
        {"anchor": "16", "title": "币制改革与盐铁专卖"},
        {"anchor": "23", "title": "算缗告缗制度"},
        {"anchor": "27", "title": "均输制度与诸改革"},
        {"anchor": "37", "title": "赈济与边政"},
        {"anchor": "41", "title": "南越西羌与酎金"},
        {"anchor": "45", "title": "桑弘羊与平准制度"},
        {"anchor": "48", "title": "太史公赞"},
    ]

    # === 033_鲁周公世家: 26节 → 10节 ===
    new_sections["033_鲁周公世家"] = [
        {"anchor": "1", "title": "周公辅政"},
        {"anchor": "4", "title": "平定叛乱与还政成王"},
        {"anchor": "7", "title": "伯禽封鲁与早期世系"},
        {"anchor": "10", "title": "孝公至隐公"},
        {"anchor": "13", "title": "庄公与继嗣之争"},
        {"anchor": "16", "title": "釐公至文公"},
        {"anchor": "19", "title": "襄公至昭公"},
        {"anchor": "22", "title": "定公至哀公"},
        {"anchor": "24", "title": "悼公至鲁亡"},
        {"anchor": "25", "title": "太史公赞"},
    ]

    # === 034_燕召公世家: 24节 → 10节 ===
    new_sections["034_燕召公世家"] = [
        {"anchor": "1", "title": "召公封燕与德政"},
        {"anchor": "4", "title": "燕国早期世系"},
        {"anchor": "9", "title": "惠公至文公"},
        {"anchor": "13", "title": "文公与苏秦"},
        {"anchor": "15", "title": "燕哙与子之乱政"},
        {"anchor": "16", "title": "昭王求贤伐齐"},
        {"anchor": "19", "title": "武成王至今王"},
        {"anchor": "21", "title": "荆轲刺秦与燕亡"},
        {"anchor": "23", "title": "太史公赞"},
    ]

    # === 043_赵世家: 36节 → 12节 ===
    new_sections["043_赵世家"] = [
        {"anchor": "1", "title": "赵氏起源"},
        {"anchor": "3", "title": "赵盾与赵氏孤儿"},
        {"anchor": "6", "title": "赵简子与三家分晋"},
        {"anchor": "14", "title": "献侯至成侯"},
        {"anchor": "19", "title": "武灵王初立"},
        {"anchor": "21", "title": "胡服骑射"},
        {"anchor": "25", "title": "传位与沙丘之乱"},
        {"anchor": "28", "title": "惠文王后期"},
        {"anchor": "30", "title": "孝成王与长平之战"},
        {"anchor": "33", "title": "悼襄王至赵亡"},
        {"anchor": "35", "title": "太史公赞"},
    ]

    # === 044_魏世家: 28节 → 10节 ===
    new_sections["044_魏世家"] = [
        {"anchor": "1", "title": "魏氏起源"},
        {"anchor": "4", "title": "魏献子至文侯"},
        {"anchor": "7", "title": "李克论相与文侯晚年"},
        {"anchor": "9", "title": "魏武侯至惠王"},
        {"anchor": "11", "title": "马陵之战与徙都大梁"},
        {"anchor": "14", "title": "魏襄王至哀王"},
        {"anchor": "19", "title": "魏安釐王时期"},
        {"anchor": "23", "title": "信陵君救赵"},
        {"anchor": "26", "title": "景湣王与魏亡"},
        {"anchor": "27", "title": "太史公赞"},
    ]

    # === 045_韩世家: 21节 → 10节 ===
    new_sections["045_韩世家"] = [
        {"anchor": "1", "title": "韩氏起源"},
        {"anchor": "2", "title": "韩厥救赵孤"},
        {"anchor": "4", "title": "三家分晋"},
        {"anchor": "7", "title": "文侯至哀侯"},
        {"anchor": "10", "title": "昭侯至宣惠王"},
        {"anchor": "14", "title": "襄王至釐王"},
        {"anchor": "18", "title": "桓惠王至韩亡"},
        {"anchor": "20", "title": "太史公赞"},
    ]

    # === 046_田敬仲完世家: 28节 → 10节 ===
    new_sections["046_田敬仲完世家"] = [
        {"anchor": "1", "title": "陈完奔齐"},
        {"anchor": "5", "title": "田氏行阴德至田常专权"},
        {"anchor": "10", "title": "田和代齐"},
        {"anchor": "12", "title": "齐威王治国"},
        {"anchor": "17", "title": "桂陵之战与宣王"},
        {"anchor": "20", "title": "齐湣王时期"},
        {"anchor": "24", "title": "燕将乐毅伐齐"},
        {"anchor": "26", "title": "齐王建与齐亡"},
        {"anchor": "27", "title": "太史公赞"},
    ]

    # === 047_孔子世家: 38节 → 12节 ===
    new_sections["047_孔子世家"] = [
        {"anchor": "1", "title": "孔子出生与家世"},
        {"anchor": "3", "title": "问礼老子"},
        {"anchor": "5", "title": "齐景公问政"},
        {"anchor": "8", "title": "阳虎之乱与出仕"},
        {"anchor": "11", "title": "摄行相事"},
        {"anchor": "12", "title": "周游列国"},
        {"anchor": "23", "title": "陈蔡绝粮"},
        {"anchor": "27", "title": "归鲁晚年"},
        {"anchor": "28", "title": "删定群经与作春秋"},
        {"anchor": "33", "title": "临终与身后"},
        {"anchor": "36", "title": "后代世系"},
        {"anchor": "37", "title": "太史公赞"},
    ]

    # === 087_李斯列传: 22节 → 10节 ===
    new_sections["087_李斯列传"] = [
        {"anchor": "1", "title": "李斯早年入秦"},
        {"anchor": "4", "title": "谏逐客书"},
        {"anchor": "5", "title": "佐秦并天下"},
        {"anchor": "8", "title": "始皇崩与沙丘之谋"},
        {"anchor": "11", "title": "二世立与赵高用事"},
        {"anchor": "14", "title": "赵高谮李斯"},
        {"anchor": "17", "title": "李斯之死"},
        {"anchor": "18", "title": "赵高弑二世与秦亡"},
        {"anchor": "21", "title": "太史公赞"},
    ]

    # === 110_匈奴列传: 47节 → 12节 ===
    new_sections["110_匈奴列传"] = [
        {"anchor": "1", "title": "匈奴的起源与习俗"},
        {"anchor": "5", "title": "冒顿单于崛起"},
        {"anchor": "8", "title": "匈奴的制度"},
        {"anchor": "11", "title": "白登之围与和亲"},
        {"anchor": "14", "title": "文帝时期的冲突"},
        {"anchor": "18", "title": "中行说叛汉"},
        {"anchor": "23", "title": "武帝反击与马邑之谋"},
        {"anchor": "28", "title": "卫青霍去病征匈奴"},
        {"anchor": "34", "title": "汉匈对峙"},
        {"anchor": "39", "title": "兒单于至且鞮侯单于"},
        {"anchor": "44", "title": "李陵李广利降匈奴"},
        {"anchor": "46", "title": "太史公赞"},
    ]

    # === 111_卫将军骠骑列传: 21节 → 10节 ===
    new_sections["111_卫将军骠骑列传"] = [
        {"anchor": "1", "title": "卫青家世与崛起"},
        {"anchor": "3", "title": "初战匈奴"},
        {"anchor": "5", "title": "大破右贤王"},
        {"anchor": "7", "title": "霍去病初露锋芒"},
        {"anchor": "9", "title": "祁连山大捷与浑邪王降"},
        {"anchor": "11", "title": "漠北大战"},
        {"anchor": "14", "title": "霍去病为人与早逝"},
        {"anchor": "17", "title": "诸将战绩"},
        {"anchor": "19", "title": "卫氏兴衰"},
        {"anchor": "20", "title": "太史公赞"},
    ]

    # === 112_平津侯主父列传: 23节 → 8节 ===
    new_sections["112_平津侯主父列传"] = [
        {"anchor": "1", "title": "公孙弘早年与入仕"},
        {"anchor": "4", "title": "拜御史大夫与为相"},
        {"anchor": "7", "title": "公孙弘之死"},
        {"anchor": "9", "title": "主父偃入京上书"},
        {"anchor": "12", "title": "徐乐严安并上书"},
        {"anchor": "14", "title": "推恩令与主父偃之死"},
        {"anchor": "19", "title": "太史公赞"},
    ]

    # 应用修改
    changes = []
    for chapter, new_sects in new_sections.items():
        if chapter in data:
            old_count = len(data[chapter])
            data[chapter] = new_sects
            changes.append(f"  {chapter}: {old_count}节 → {len(new_sects)}节")
        else:
            print(f"  警告: {chapter} 不在 sections_data.json 中")

    # 写入
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"=== 第二批修改完成 ===")
    for c in changes:
        print(c)

    # 最终统计
    print(f"\n=== 最终统计 ===")
    still_large = []
    for chapter, sections in data.items():
        n = len(sections)
        if n > 20:
            still_large.append(f"  {chapter}: {n}节")
    if still_large:
        print("仍然超过20节的章节:")
        for s in still_large:
            print(s)
    else:
        print("所有章节均在20节以内 ✓")


if __name__ == '__main__':
    main()
