#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 person_categories.json 中已分类但不在 person.ttl 的人物插入 TTL。

新增 concept 节点：
  per:地方官       → subClassOf per:臣
  per:平民刑徒     → subClassOf per:社会人物
  per:家臣门客     → subClassOf per:社会人物
  per:先秦宗室     → subClassOf per:宗室

用法：
  python kg/taxonomy/scripts/insert_missing_persons.py [--dry-run]
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
PERSON_TTL  = ROOT / 'kg' / 'taxonomy' / 'person.ttl'
CATS_JSON   = ROOT / 'kg' / 'entities' / 'data' / 'person_categories.json'
INDEX_JSON  = ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'

DRY_RUN = '--dry-run' in sys.argv

# ─── 章节 → 时代 映射 ──────────────────────────────────────────

CHAPTER_ERA = {
    # 本纪
    '001_五帝本纪':    '五帝',
    '002_夏本纪':      '夏代',
    '003_殷本纪':      '商代',
    '004_周本纪':      '西周',
    '005_秦本纪':      '春秋',   # 秦国作为诸侯
    '006_秦始皇本纪':  '秦朝',
    '007_项羽本纪':    '楚汉',
    '008_高祖本纪':    '楚汉',
    '009_吕太后本纪':  '汉初',
    '010_孝文本纪':    '汉中后',
    '011_孝景本纪':    '汉中后',
    '012_孝武本纪':    '汉中后',
    # 表
    '013_三代世表':              '三代',
    '014_十二诸侯年表':          '春秋',
    '015_六国年表':              '战国',
    '016_秦楚之际月表':          '楚汉',
    '017_汉兴以来诸侯王年表':    '汉初',
    '018_高祖功臣侯者年表':      '汉初',
    '019_惠景间侯者年表':        '汉初',
    '020_建元以来侯者年表':      '汉中后',
    '021_建元已来王子侯者年表':  '汉中后',
    '022_汉兴以来将相名臣年表':  '汉中后',
    # 书 (023-030) → 汉中后
    **{f'{n:03d}_': '汉中后' for n in range(23, 31)},
    # 世家 (031-060)
    '031_吴太伯世家':   '先秦',
    '032_齐太公世家':   '先秦',
    '033_鲁周公世家':   '先秦',
    '034_燕召公世家':   '先秦',
    '035_管蔡世家':     '先秦',
    '036_陈杞世家':     '春秋',
    '037_卫康叔世家':   '春秋',
    '038_宋微子世家':   '春秋',
    '039_晋世家':       '春秋',
    '040_楚世家':       '春秋',
    '041_越王句践世家': '春秋',
    '042_郑世家':       '春秋',
    '043_赵世家':       '战国',
    '044_魏世家':       '战国',
    '045_韩世家':       '战国',
    '046_田敬仲完世家': '战国',
    '047_孔子世家':     '春秋',
    '048_陈涉世家':     '楚汉',
    '049_外戚世家':     '汉中后',
    '050_楚元王世家':   '汉初',
    '051_荆燕世家':     '汉初',
    '052_齐悼惠王世家': '汉初',
    '053_萧相国世家':   '汉初',
    '054_曹相国世家':   '汉初',
    '055_留侯世家':     '汉初',
    '056_陈丞相世家':   '汉初',
    '057_绛侯周勃世家': '汉初',
    '058_梁孝王世家':   '汉中后',
    '059_五宗世家':     '汉中后',
    '060_三王世家':     '汉中后',
    # 列传 (061-130)
    '061_伯夷列传':         '先秦',
    '062_管晏列传':         '春秋',
    '063_老子韩非列传':     '战国',
    '064_司马穰苴列传':     '春秋',
    '065_孙子吴起列传':     '战国',
    '066_伍子胥列传':       '春秋',
    '067_仲尼弟子列传':     '春秋',
    '068_商君列传':         '战国',
    '069_苏秦列传':         '战国',
    '070_张仪列传':         '战国',
    '071_樗里子甘茂列传':   '战国',
    '072_穰侯列传':         '战国',
    '073_白起王翦列传':     '战国',
    '074_孟子荀卿列传':     '战国',
    '075_孟尝君列传':       '战国',
    '076_平原君虞卿列传':   '战国',
    '077_魏公子列传':       '战国',
    '078_春申君列传':       '战国',
    '079_范雎蔡泽列传':     '战国',
    '080_乐毅列传':         '战国',
    '081_廉颇蔺相如列传':   '战国',
    '082_田单列传':         '战国',
    '083_鲁仲连邹阳列传':   '战国',
    '084_屈原贾生列传':     '战国',
    '085_吕不韦列传':       '战国',
    '086_刺客列传':         '战国',
    '087_李斯列传':         '秦朝',
    '088_蒙恬列传':         '秦朝',
    '089_张耳陈馀列传':     '楚汉',
    '090_魏豹彭越列传':     '楚汉',
    '091_黥布列传':         '楚汉',
    '092_淮阴侯列传':       '楚汉',
    '093_韩信卢绾列传':     '楚汉',
    '094_田儋列传':         '楚汉',
    '095_樊郦滕灌列传':     '楚汉',
    '096_张丞相列传':       '汉初',
    '097_郦生陆贾列传':     '汉初',
    '098_傅靳蒯成列传':     '汉初',
    '099_刘敬叔孙通列传':   '汉初',
    '100_季布栾布列传':     '汉初',
    '101_袁盎晁错列传':     '汉中后',
    '102_张释之冯唐列传':   '汉中后',
    '103_万石张叔列传':     '汉中后',
    '104_田叔列传':         '汉中后',
    '105_扁鹊仓公列传':     '汉中后',
    '106_吴王濞列传':       '汉中后',
    '107_魏其武安侯列传':   '汉中后',
    '108_韩长孺列传':       '汉中后',
    '109_李将军列传':       '汉中后',
    '110_匈奴列传':         '外邦',
    '111_卫将军骠骑列传':   '汉中后',
    '112_平津侯主父列传':   '汉中后',
    '113_南越列传':         '外邦',
    '114_东越列传':         '外邦',
    '115_朝鲜列传':         '外邦',
    '116_西南夷列传':       '外邦',
    '117_司马相如列传':     '汉中后',
    '118_淮南衡山列传':     '汉中后',
    '119_循吏列传':         '汉中后',
    '120_汲郑列传':         '汉中后',
    '121_儒林列传':         '汉中后',
    '122_酷吏列传':         '汉中后',
    '123_大宛列传':         '外邦',
    '124_游侠列传':         '汉中后',
    '125_佞幸列传':         '汉中后',
    '126_滑稽列传':         '汉中后',
    '127_日者列传':         '汉中后',
    '128_龟策列传':         '汉中后',
    '129_货殖列传':         '汉中后',
    '130_太史公自序':       '汉中后',
}

# 书类章节前缀映射
BOOK_CHAPTERS = {23, 24, 25, 26, 27, 28, 29, 30}

def get_era(refs):
    """从 refs 推断时代（按出现频次投票）"""
    counter = Counter()
    for ref in refs:
        chap = ref[0]
        # 精确匹配
        if chap in CHAPTER_ERA:
            counter[CHAPTER_ERA[chap]] += 1
            continue
        # 前缀匹配（书类章节）
        m = re.match(r'^(\d+)_', chap)
        if m:
            n = int(m.group(1))
            if n in BOOK_CHAPTERS:
                counter['汉中后'] += 1
            elif 31 <= n <= 60:
                counter['先秦'] += 1
            elif 87 <= n <= 88:
                counter['秦朝'] += 1
            elif 89 <= n <= 95:
                counter['楚汉'] += 1
            elif 96 <= n <= 100:
                counter['汉初'] += 1
            elif n >= 101:
                counter['汉中后'] += 1
    return counter.most_common(1)[0][0] if counter else None


# ─── 分类 + 时代 → TTL 类 ─────────────────────────────────────

# 用于 外邦 的章节关键词 → TTL 类
FOREIGN_CHAPTER_MAP = {
    '匈奴': 'per:匈奴',
    '南越': 'per:南越',
    '东越': 'per:东越',
    '大宛': 'per:大宛西域',
    '西域': 'per:大宛西域',
    '朝鲜': 'per:朝鲜',
    '西南夷': 'per:西南夷',
}

# 用于 诸侯君主 的名称前缀 → 邦国 → TTL 诸侯子类
FEUDAL_STATE_KEYWORDS = {
    '齐': 'per:齐国', '鲁': 'per:鲁国', '燕': 'per:燕国',
    '赵': 'per:赵国', '魏': 'per:魏国', '韩': 'per:韩国',
    '楚': 'per:楚国', '秦': 'per:秦国', '吴': 'per:吴国',
    '越': 'per:越国', '卫': 'per:卫国', '宋': 'per:宋国',
    '郑': 'per:郑国', '陈': 'per:陈国', '蔡': 'per:蔡国',
    '晋': 'per:晋国',
}

# 已有诸侯子类（per:诸侯 下）
FEUDAL_STATE_CLASSES = {
    '卫国', '宋国', '秦国', '蔡国', '越国', '郑国', '陈国', '魏国',
}

ERA_TO_CHEN_CLASS = {
    '五帝':   'per:五帝时代',
    '夏代':   'per:夏代',
    '商代':   'per:商代',
    '西周':   'per:西周',
    '三代':   'per:三代',
    '先秦':   'per:先秦早期',   # 宽泛先秦，归入先秦早期
    '春秋':   'per:春秋',
    '战国':   'per:战国',
    '秦朝':   'per:秦',
    '楚汉':   'per:楚汉',
    '汉初':   'per:汉初',
    '汉中后': 'per:汉中后',
}

ERA_TO_EMPEROR_CLASS = {
    '五帝':   'per:上古',
    '夏代':   'per:夏',
    '商代':   'per:商',
    '西周':   'per:周',
    '三代':   'per:周',
    '先秦':   'per:上古',
    '春秋':   'per:周',
    '战国':   'per:周',
    '秦朝':   'per:秦朝',
    '楚汉':   'per:秦末',
    '汉初':   'per:汉',
    '汉中后': 'per:汉',
    '外邦':   'per:外邦',
}

ERA_TO_CONSORT_CLASS = {
    '五帝':   'per:先秦后妃',
    '夏代':   'per:先秦后妃',
    '商代':   'per:先秦后妃',
    '西周':   'per:先秦后妃',
    '三代':   'per:先秦后妃',
    '先秦':   'per:先秦后妃',
    '春秋':   'per:先秦后妃',
    '战国':   'per:先秦后妃',
    '秦朝':   'per:先秦后妃',
    '楚汉':   'per:汉后妃',
    '汉初':   'per:汉后妃',
    '汉中后': 'per:汉后妃',
}


def decide_ttl_class(name, cats, refs, persons_data):
    """给定人物名、分类列表、refs，返回最佳 TTL 类 URI。"""
    primary = cats[0] if cats else '未知'
    era = get_era(refs)
    chapter_names = [r[0] for r in refs]

    # ── 直接映射 ──
    if primary == '误标' or primary == '待拆分':
        return 'per:疑似误标'
    if primary == '虚构寓言':
        return 'per:虚构人物'
    if primary == '货殖':
        return 'per:商贾'
    if primary == '谋臣策士':
        return 'per:策士'

    # ── 上古神话 ──
    if primary == '上古神话':
        return 'per:五帝时代'

    # ── 刺客游侠 ──
    if primary == '刺客游侠':
        if any('游侠' in c for c in chapter_names):
            return 'per:游侠'
        return 'per:刺客'

    # ── 近臣奇人 ──
    if primary == '近臣奇人':
        if any('滑稽' in c for c in chapter_names):
            return 'per:滑稽'
        return 'per:佞幸'

    # ── 地方官 ──
    if primary == '地方官':
        return 'per:地方官'

    # ── 平民刑徒 ──
    if primary == '平民刑徒':
        return 'per:平民刑徒'

    # ── 家臣门客 ──
    if primary == '家臣门客':
        return 'per:家臣门客'

    # ── 学者文士 ──
    if primary == '学者文士':
        # 尝试根据章节推断
        if any('仲尼弟子' in c or '孔门' in c for c in chapter_names):
            return 'per:孔门弟子'
        if any('儒林' in c for c in chapter_names):
            return 'per:汉儒'
        if any('老子韩非' in c or '商君' in c for c in chapter_names):
            return 'per:法家'
        if any('孙子吴起' in c for c in chapter_names):
            return 'per:兵家'
        if any('日者' in c for c in chapter_names):
            return 'per:日者龟策'
        if any('扁鹊仓公' in c for c in chapter_names):
            return 'per:医者'
        # 根据时代兜底
        if era in ('汉初', '汉中后'):
            return 'per:汉儒'
        if era in ('春秋',):
            return 'per:孔门弟子'
        return 'per:思想家'

    # ── 外邦 ──
    if primary == '外邦':
        for keyword, cls in FOREIGN_CHAPTER_MAP.items():
            if any(keyword in c for c in chapter_names):
                return cls
        # 时代/外邦兜底
        if era == '外邦':
            # 看章节号确定
            for c in chapter_names:
                m = re.match(r'^(\d+)', c)
                if m:
                    n = int(m.group(1))
                    if n == 110: return 'per:匈奴'
                    if n == 113: return 'per:南越'
                    if n == 114: return 'per:东越'
                    if n == 115: return 'per:朝鲜'
                    if n == 116: return 'per:西南夷'
                    if n == 123: return 'per:大宛西域'
        return 'per:外邦'

    # ── 后妃 ──
    if primary == '后妃':
        if era in ERA_TO_CONSORT_CLASS:
            return ERA_TO_CONSORT_CLASS[era]
        return 'per:先秦后妃'

    # ── 帝王 ──
    if primary == '帝王':
        # 特殊：有些名字以"帝"开头可判断是殷商/夏
        if name.startswith('帝') and era in ('商代',):
            return 'per:商'
        if name.startswith('帝') and era in ('夏代',):
            return 'per:夏'
        if era in ERA_TO_EMPEROR_CLASS:
            return ERA_TO_EMPEROR_CLASS[era]
        return 'per:上古'

    # ── 诸侯君主 ──
    if primary == '诸侯君主':
        # 优先看章节：世家对应的邦国
        for c in chapter_names:
            for keyword, state_cls in FEUDAL_STATE_KEYWORDS.items():
                if keyword in c:
                    # 章节名中有邦国 → 归入该邦国下的诸侯子类
                    state = state_cls.replace('per:', '')
                    if state in FEUDAL_STATE_CLASSES:
                        return state_cls
                    # 否则归入 per:诸侯
                    return 'per:诸侯'
        # 名字中有帝字 → 归为帝王
        if name.startswith('帝'):
            if era in ERA_TO_EMPEROR_CLASS:
                return ERA_TO_EMPEROR_CLASS[era]
            return 'per:上古'
        # 时代
        if era in ('五帝', '夏代', '商代', '西周', '三代'):
            # 是古代天子，归帝王
            return ERA_TO_EMPEROR_CLASS.get(era, 'per:上古')
        return 'per:诸侯'

    # ── 宗室 ──
    if primary == '宗室':
        if any('吴楚' in c or '七国' in c or '吴王濞' in c for c in chapter_names):
            return 'per:吴楚七国'
        if any('淮南' in c or '衡山' in c for c in chapter_names):
            return 'per:淮南衡山'
        if era in ('汉初', '汉中后', '楚汉'):
            return 'per:宗室'
        # 先秦宗室 → 新概念
        return 'per:先秦宗室'

    # ── 将相（最大类，用时代映射） ──
    if primary == '将相':
        if era in ERA_TO_CHEN_CLASS:
            return ERA_TO_CHEN_CLASS[era]
        return 'per:臣'

    # 未知兜底
    return 'per:疑似误标'


# ─── 新增概念节点 ─────────────────────────────────────────────

NEW_CONCEPTS = """
# -- 新增概念（第四轮补全） --

per:地方官 a owl:Class ; rdfs:subClassOf per:臣 ; rdfs:label "地方官"@zh .
per:平民刑徒 a owl:Class ; rdfs:subClassOf per:社会人物 ; rdfs:label "平民刑徒"@zh .
per:家臣门客 a owl:Class ; rdfs:subClassOf per:社会人物 ; rdfs:label "家臣门客"@zh .
per:先秦宗室 a owl:Class ; rdfs:subClassOf per:宗室 ; rdfs:label "先秦宗室"@zh .
"""

# ─── 主函数 ──────────────────────────────────────────────────

def ttl_name(name):
    """将人名转为合法 TTL URI 片段（per:XXX）"""
    # 替换空格、特殊字符
    safe = re.sub(r'[\s\(\)\[\]<>"\']', '_', name)
    return safe


def main():
    # 1. 加载现有 TTL 实例
    ttl_text = PERSON_TTL.read_text(encoding='utf-8')
    existing = set(re.findall(r'^per:(.+?) a per:', ttl_text, re.MULTILINE))
    print(f'现有 TTL 实例: {len(existing)}')

    # 2. 加载分类数据
    with open(CATS_JSON, encoding='utf-8') as f:
        cats = json.load(f)
    print(f'person_categories 总计: {len(cats)}')

    # 3. 加载 entity_index（获取 count 和 refs）
    with open(INDEX_JSON, encoding='utf-8') as f:
        ei = json.load(f)
    persons_data = ei.get('person', {})
    print(f'entity_index persons: {len(persons_data)}')

    # 4. 找到缺失人物
    missing = {k: v for k, v in cats.items() if k not in existing}
    print(f'缺失人物（需插入）: {len(missing)}')

    # 5. 为每个人分配 TTL 类，统计结果
    assignments = {}     # name → ttl_class
    new_concepts_needed = set()

    for name, cat_list in missing.items():
        p = persons_data.get(name, {})
        refs = p.get('refs', [])
        count = p.get('count', 0)
        ttl_cls = decide_ttl_class(name, cat_list, refs, persons_data)
        assignments[name] = (ttl_cls, count, cat_list)

        if ttl_cls in ('per:地方官', 'per:平民刑徒', 'per:家臣门客', 'per:先秦宗室'):
            new_concepts_needed.add(ttl_cls)

    # 6. 统计
    cls_counter = Counter(v[0] for v in assignments.values())
    print('\n分配统计（TTL 类）:')
    for cls, cnt in sorted(cls_counter.items(), key=lambda x: -x[1]):
        print(f'  {cls}: {cnt}')

    print(f'\n需要新增概念节点: {new_concepts_needed}')

    if DRY_RUN:
        print('\n[DRY RUN] 不写入文件。')
        return

    # 7. 按 TTL 类分组生成 Turtle 文本
    by_class = {}
    for name, (ttl_cls, count, cat_list) in sorted(assignments.items()):
        by_class.setdefault(ttl_cls, []).append((name, count))

    # 8. 构造插入文本
    lines = ['\n# ── 第四轮自动插入（共 %d 人）──' % len(missing)]

    # 添加新概念
    if new_concepts_needed:
        lines.append(NEW_CONCEPTS)

    for cls in sorted(by_class.keys()):
        persons_in_cls = sorted(by_class[cls], key=lambda x: -x[1])
        class_label = cls.replace('per:', '')
        lines.append(f'\n# {class_label} ({len(persons_in_cls)})')
        for name, count in persons_in_cls:
            safe = ttl_name(name)
            lines.append(f'per:{safe} a {cls} ; rdfs:label "{name}"@zh ; :count {count} .')

    new_text = '\n'.join(lines)

    # 9. 更新文件头部的人数注释
    current_total = len(existing) + len(missing)
    new_header = re.sub(
        r'# 史记人物本体 — \d+人',
        f'# 史记人物本体 — {current_total}人',
        ttl_text
    )

    # 10. 追加到文件末尾
    final_text = new_header.rstrip() + '\n' + new_text + '\n'
    PERSON_TTL.write_text(final_text, encoding='utf-8')
    print(f'\n✓ 已写入 person.ttl，新增 {len(missing)} 人，总计 {current_total} 人')

    # 11. 打印问题案例（class=per:疑似误标 但原始类别不是误标）
    suspect = [(n, v[2]) for n, v in assignments.items()
               if v[0] == 'per:疑似误标' and v[2] and v[2][0] not in ('误标', '待拆分')]
    if suspect:
        print(f'\n⚠ 非误标但归入疑似误标 ({len(suspect)} 人):')
        for n, c in suspect[:10]:
            print(f'  {n}: {c}')


if __name__ == '__main__':
    main()
