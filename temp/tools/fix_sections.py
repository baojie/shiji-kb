#!/usr/bin/env python3
"""修复 sections_data.json 中分节过多或编号诡异的章节。

对于分节过多的章节（>20节），合并为5-15个大节。
对于编号诡异的章节（如 1.1, 2.3 这样的 X.Y 格式），保留但减少数量。
"""

import json
import os

def main():
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sections_data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 统计问题章节
    print("=== 问题章节分析 ===")
    for chapter, sections in data.items():
        n = len(sections)
        has_decimal = any('.' in str(s['anchor']) for s in sections)
        if n > 20 or has_decimal:
            anchors = [s['anchor'] for s in sections]
            flag = ''
            if n > 20:
                flag += f' [过多:{n}节]'
            if has_decimal:
                flag += ' [X.Y编号]'
            print(f"  {chapter}: {n}节{flag}")
            if n <= 5:
                print(f"    anchors: {anchors}")

    # 定义新的合并分节
    new_sections = {}

    # === 005_秦本纪: 22节, 混合格式 → 保持大部分, 修复混合格式 ===
    new_sections["005_秦本纪"] = [
        {"anchor": "1", "title": "秦之先祖"},
        {"anchor": "3.1", "title": "造父与非子"},
        {"anchor": "6", "title": "秦立国：庄公、襄公"},
        {"anchor": "9", "title": "武公至德公"},
        {"anchor": "14", "title": "宣公至成公"},
        {"anchor": "17", "title": "缪公称霸"},
        {"anchor": "34", "title": "康公至景公"},
        {"anchor": "42", "title": "怀公至献公"},
        {"anchor": "48", "title": "孝公与商鞅变法"},
        {"anchor": "57", "title": "惠文君至武王"},
        {"anchor": "62", "title": "昭襄王"},
        {"anchor": "66", "title": "孝文王至秦始皇"},
    ]

    # === 007_项羽本纪: 20节, X.1格式 → 保持，简化编号 ===
    new_sections["007_项羽本纪"] = [
        {"anchor": "1.1", "title": "项羽早年"},
        {"anchor": "7.1", "title": "起兵反秦"},
        {"anchor": "24.1", "title": "项梁败亡"},
        {"anchor": "31.1", "title": "巨鹿之战"},
        {"anchor": "54.1", "title": "鸿门宴"},
        {"anchor": "88.1", "title": "项羽分封"},
        {"anchor": "104.1", "title": "楚汉相争"},
        {"anchor": "127.1", "title": "荥阳攻防"},
        {"anchor": "149.1", "title": "鸿沟议和"},
        {"anchor": "160.1", "title": "垓下之围"},
        {"anchor": "173.1", "title": "乌江自刎"},
        {"anchor": "185.1", "title": "太史公赞"},
    ]

    # === 008_高祖本纪: 26节, X.1格式 → 合并为~12节 ===
    new_sections["008_高祖本纪"] = [
        {"anchor": "1", "title": "刘邦早年"},
        {"anchor": "8.1", "title": "斩蛇起义"},
        {"anchor": "12.1", "title": "随项梁征战"},
        {"anchor": "20.1", "title": "入关灭秦"},
        {"anchor": "24.1", "title": "鸿门之会"},
        {"anchor": "26.1", "title": "封汉王入汉中"},
        {"anchor": "30.1", "title": "还定三秦"},
        {"anchor": "35.1", "title": "彭城之败与荥阳对峙"},
        {"anchor": "49.1", "title": "鸿沟和约与垓下决战"},
        {"anchor": "55.1", "title": "称帝封侯"},
        {"anchor": "65.1", "title": "平定天下"},
        {"anchor": "84.1", "title": "晚年与去世"},
    ]

    # === 009_吕太后本纪: 11节 → 保持不动（数量合理）===

    # === 010_孝文本纪: 16节 → 合并为~10节 ===
    new_sections["010_孝文本纪"] = [
        {"anchor": "1.1", "title": "文帝即位"},
        {"anchor": "5.1", "title": "初政与施德"},
        {"anchor": "9.1", "title": "除诽谤刑与减赋"},
        {"anchor": "14.1", "title": "贾谊进策"},
        {"anchor": "21.1", "title": "匈奴入侵"},
        {"anchor": "27", "title": "济北王与淮南王之乱"},
        {"anchor": "33.1", "title": "文帝中后期施政"},
        {"anchor": "41.1", "title": "遗诏与评价"},
    ]

    # === 011_孝景本纪: 9节 → 数量合理，保持 ===

    # === 012_孝武本纪: 17节 → 合并为~10节 ===
    new_sections["012_孝武本纪"] = [
        {"anchor": "1.1", "title": "武帝即位"},
        {"anchor": "5.1", "title": "求仙封禅"},
        {"anchor": "15.1", "title": "祭祀改革"},
        {"anchor": "22.1", "title": "巡行天下"},
        {"anchor": "30.1", "title": "太初改历"},
        {"anchor": "40.1", "title": "晚年诸事"},
        {"anchor": "52.1", "title": "武帝驾崩"},
    ]

    # === 035_管蔡世家: 28节 N.N格式 → 合并为~8节 ===
    new_sections["035_管蔡世家"] = [
        {"anchor": "1.1", "title": "武王封建诸弟"},
        {"anchor": "3.3", "title": "管蔡作乱与周公东征"},
        {"anchor": "5.5", "title": "蔡国世系"},
        {"anchor": "16.16", "title": "蔡国中后期"},
        {"anchor": "22.22", "title": "武王诸弟封国概况"},
        {"anchor": "24.24", "title": "曹国世系"},
        {"anchor": "38.38", "title": "曹国灭亡"},
        {"anchor": "41.41", "title": "太史公赞"},
    ]

    # === 036_陈杞世家: 18节 → 合并为~8节 ===
    new_sections["036_陈杞世家"] = [
        {"anchor": "1.1", "title": "陈胡公受封"},
        {"anchor": "5.5", "title": "陈国早中期"},
        {"anchor": "14.14", "title": "灵公与夏姬之乱"},
        {"anchor": "18.18", "title": "陈国后期"},
        {"anchor": "24.24", "title": "陈国灭亡"},
        {"anchor": "27.27", "title": "杞国世系"},
        {"anchor": "29.29", "title": "古代帝王后裔封国"},
        {"anchor": "31.31", "title": "太史公赞"},
    ]

    # === 037_卫康叔世家: 29节 → 合并为~10节 ===
    new_sections["037_卫康叔世家"] = [
        {"anchor": "1.1", "title": "康叔受封"},
        {"anchor": "5.5", "title": "卫国早期世系"},
        {"anchor": "10.10", "title": "州吁之乱与宣公"},
        {"anchor": "16.16", "title": "惠公至懿公好鹤亡国"},
        {"anchor": "20.20", "title": "文公治卫"},
        {"anchor": "23.23", "title": "穆公至献公"},
        {"anchor": "28.28", "title": "灵公与蒯聩之乱"},
        {"anchor": "38.41", "title": "卫国末期政变"},
        {"anchor": "45.49", "title": "秦灭卫"},
        {"anchor": "47.51", "title": "太史公赞"},
    ]

    # === 038_宋微子世家: 30节 → 合并为~8节 ===
    new_sections["038_宋微子世家"] = [
        {"anchor": "1.1", "title": "微子与箕子"},
        {"anchor": "6.8", "title": "箕子陈洪范"},
        {"anchor": "10.20", "title": "微子立宋与早期世系"},
        {"anchor": "16.27", "title": "宣公至殇公"},
        {"anchor": "23.34", "title": "桓公至襄公争霸"},
        {"anchor": "28.39", "title": "成公至文公"},
        {"anchor": "35.47", "title": "共公至元公"},
        {"anchor": "40.52", "title": "景公至宋国后期"},
        {"anchor": "43.55", "title": "宋王偃暴虐与灭宋"},
        {"anchor": "44.56", "title": "太史公赞"},
    ]

    # === 039_晋世家: 109节 → 合并为~15节 ===
    new_sections["039_晋世家"] = [
        {"anchor": "1.1", "title": "唐叔虞受封与早期世系"},
        {"anchor": "7.9", "title": "曲沃代晋"},
        {"anchor": "20.22", "title": "献公时期"},
        {"anchor": "26.29", "title": "骊姬之乱"},
        {"anchor": "33.38", "title": "里克迎惠公"},
        {"anchor": "37.43", "title": "晋饥秦虏惠公"},
        {"anchor": "43.50", "title": "重耳归晋"},
        {"anchor": "54.61", "title": "文公即位与吕郤之乱"},
        {"anchor": "58.65", "title": "文公称霸"},
        {"anchor": "69.78", "title": "殽之战与灵公"},
        {"anchor": "83.93", "title": "景公与邲之战"},
        {"anchor": "95.110", "title": "厉公至悼公"},
        {"anchor": "104.120", "title": "平公至顷公"},
        {"anchor": "114.130", "title": "六卿专权与三家分晋"},
        {"anchor": "130.146", "title": "太史公赞"},
    ]

    # === 040_楚世家: 87+节 → 合并为~15节 ===
    new_sections["040_楚世家"] = [
        {"anchor": "1.3", "title": "楚之先祖与建国"},
        {"anchor": "9.12", "title": "武王至文王"},
        {"anchor": "14.17", "title": "成王称霸"},
        {"anchor": "20.23", "title": "城濮之战与商臣弑父"},
        {"anchor": "25.28", "title": "庄王一鸣惊人"},
        {"anchor": "31.34", "title": "共王至灵王"},
        {"anchor": "36.39", "title": "灵王灭陈蔡与政变"},
        {"anchor": "43.47", "title": "平王施惠与费无忌"},
        {"anchor": "50.54", "title": "昭王与吴入郢"},
        {"anchor": "55.59", "title": "申包胥复国"},
        {"anchor": "60.64", "title": "惠王至悼王"},
        {"anchor": "66.70", "title": "宣王至威王"},
        {"anchor": "69.73", "title": "怀王受骗"},
        {"anchor": "84.88", "title": "顷襄王与秦拔郢"},
        {"anchor": "93.97", "title": "考烈王至秦灭楚"},
        {"anchor": "98.102", "title": "太史公赞"},
    ]

    # === 130_太史公自序: 151节 → 合并为~10节 ===
    new_sections["130_太史公自序"] = [
        {"anchor": "1", "title": "司马氏家世"},
        {"anchor": "2", "title": "司马谈论六家要指"},
        {"anchor": "9", "title": "司马迁继任太史令"},
        {"anchor": "14", "title": "论春秋与发愤著书"},
        {"anchor": "20", "title": "本纪提要"},
        {"anchor": "32", "title": "表提要"},
        {"anchor": "42", "title": "书提要"},
        {"anchor": "50", "title": "世家提要"},
        {"anchor": "80", "title": "列传提要（上）"},
        {"anchor": "115", "title": "列传提要（下）"},
        {"anchor": "150", "title": "太史公赞"},
    ]

    # === 其他有 .1 后缀的章节：数量合理的保持，只修正格式 ===
    # 这些章节节数不多，不需要合并，但也在此列出

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

    print(f"\n=== 修改完成 ===")
    for c in changes:
        print(c)

    # 最终统计
    print(f"\n=== 修改后统计 ===")
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
        print("所有章节均在20节以内")


if __name__ == '__main__':
    main()
