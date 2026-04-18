#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从《汉书·百官公卿表》（卷十九上）提取官职名，生成 L2.5 白名单。

输入:  corpus/other/汉书.txt（包含 "卷十九上" 百官公卿表）
输出:  kg/entities/data/hanshu_baiguan.json

结构:
  {
    "sangong":  [...],   # 三公及其别名
    "jiuqing":  [...],   # 九卿及其别名
    "liqing":   [...],   # 列卿
    "junli":    [...],   # 郡国长吏
    "xianli":   [...],   # 县乡吏
    "military": [...],   # 军职
    "palace":   [...],   # 宫廷近侍
    "wenxue":   [...],   # 文学顾问
    "shifu":    [...],   # 宗师宾傅
  }

提取策略：
- 每段开头的"XX，秦官/汉官/古官"等 → 主官名
- 段内的 "更名 X" / "更名曰 X" / "复名 X" / "或曰 X" → 别名
- "属官有 X、Y、Z" → 附属官
- 爵 20 等列表 → 爵位
- 手工标注每段的 section（按段文本关键字）
"""

import json
import re
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HANSHU = _ROOT / 'corpus' / 'other' / '汉书.txt'
OUT = _ROOT / 'kg' / 'entities' / 'data' / 'hanshu_baiguan.json'

SEC_START = '百官公卿表第七上'
SEC_END = '卷十九下'


def load_baiguan_text():
    text = HANSHU.read_text(encoding='utf-8')
    # 避开目录：取第二次出现的 "百官公卿表第七上" 作为正文起点
    idx1 = text.find(SEC_START)
    idx2 = text.find(SEC_START, idx1 + 1) if idx1 >= 0 else -1
    start = idx2 if idx2 >= 0 else idx1
    end = text.find(SEC_END, start) if start >= 0 else -1
    if start < 0:
        raise RuntimeError(f'找不到 {SEC_START}')
    if end < 0:
        end = len(text)
    body = text[start:end]
    return body


# 段落分割：按自然段（由句末的换行分隔；百官公卿表实际以段首"X，秦官/汉官/古官"起头）
def split_paragraphs(body):
    # 先按换行切，每行多半是一段
    lines = [ln.strip() for ln in body.split('\n') if ln.strip()]
    return lines


# 段首开头模式：一个或多个官名（用 、 分隔），接 "，" 后为官制描述
# 例：  "相国、丞相，皆秦官" | "太师、太保，皆古官" | "县令、长，皆秦官" | "奉常，秦官"
HEAD_PATTERN = re.compile(
    r'^([^\s，。：；]{1,25}?)[，]'
    r'(?:皆)?(?:秦官|古官|周官|汉官|汉不常置|周末官|武帝\w{0,6}置|成帝\w{0,6}置|秦制|汉兴|汉)'
)

# 别名提取：官名改名的模式。分两类：
#   A) "更名 X" / "更名曰 X" / "更曰 X" / "复为 X" → X 即新名
#   B) "更名 X 为 Y" / "更名 X 曰 Y" → Y 是新名，X 是旧名
# 使用非贪婪匹配 + 严格字符类，避免抓住 "为/曰" 等连接词
_NAME_CHARS = r'[一-鿿]'
_NAME = _NAME_CHARS + r'{1,6}?'  # 非贪婪

# 模式 B：优先匹配（能同时抓到旧名和新名）
ALIAS_XY_PATTERNS = [
    re.compile(r'更名(' + _NAME + r')为(' + _NAME + r')(?=[，。])'),
    re.compile(r'更名(' + _NAME + r')曰(' + _NAME + r')(?=[，。])'),
    re.compile(r'改名(' + _NAME + r')为(' + _NAME + r')(?=[，。])'),
    re.compile(r'改(' + _NAME + r')为(' + _NAME + r')(?=[，。])'),
]

# 模式 A：单名（到句末或到 "为"/"曰" 等前）
ALIAS_PATTERNS = [
    re.compile(r'更名曰(' + _NAME + r')(?=[，。；])'),
    re.compile(r'更曰(' + _NAME + r')(?=[，。；])'),
    re.compile(r'复为(' + _NAME + r')(?=[，。；])'),
    re.compile(r'复名(' + _NAME + r')(?=[，。；])'),
    re.compile(r'或曰(' + _NAME + r')(?=[，。；])'),
    re.compile(r'改名(' + _NAME + r')(?=[，。；])'),
    # 更名 X (不接为/曰) → X 为新名
    re.compile(r'更名(' + _NAME + r')(?=[，。；])'),
    # 初置 X (段内首次设立的新官)
    re.compile(r'初置(' + _NAME + r')(?=[，。；])'),
    re.compile(r'[省复]置(' + _NAME + r')(?=[，。；])'),
]

# 附属官：属官有 X、Y 三令丞 / 属官有 X 丞 / 有 X、Y、Z
SUB_OFFICIALS_PAT = re.compile(r'属官有\s*([^。]+?)[。，]')


def extract_head_and_aliases(paragraph):
    """返回 (heads_list, list_of_aliases)。heads_list 是段首可能的多个官名。"""
    heads = []
    m = HEAD_PATTERN.match(paragraph)
    if m:
        # 段首可能是 "X、Y" 并列头，也可能是单头
        raw = m.group(1)
        for piece in re.split(r'[、]', raw):
            piece = piece.strip()
            if 1 <= len(piece) <= 10 and re.fullmatch(r'[一-鿿]+', piece):
                heads.append(piece)
    # 别名（跨整段搜）。先跑 XY 双名，再跑单名。
    aliases = []
    seen = set()

    def _add(a):
        a = a.strip()
        if not (1 <= len(a) <= 6):
            return
        if re.search(r'[一二三四五六七八九十百千万]', a):
            return
        if a in seen:
            return
        seen.add(a); aliases.append(a)

    # 已匹配的 (start, end) 区间，避免单名模式重复抓取
    occupied_spans = []
    for pat in ALIAS_XY_PATTERNS:
        for m2 in pat.finditer(paragraph):
            _add(m2.group(1))
            _add(m2.group(2))
            occupied_spans.append((m2.start(), m2.end()))

    def _inside(start):
        return any(s <= start < e for s, e in occupied_spans)

    for pat in ALIAS_PATTERNS:
        for m2 in pat.finditer(paragraph):
            if _inside(m2.start()):
                continue
            _add(m2.group(1))
    return heads, aliases


def extract_sub_officials(paragraph):
    """从 '属官有 A、B、C 三令丞' 提取附属官名。"""
    names = []
    seen = set()
    for m in SUB_OFFICIALS_PAT.finditer(paragraph):
        span = m.group(1)
        # 清理: 去除 "三令丞 / 两丞 / 令丞 / 皆..."
        span = re.sub(r'[一二三四五六七八九十]+[令长丞尉]', '', span)
        span = re.sub(r'令丞|长丞|丞尉|丞|尉|长|令', '', span)
        for token in re.split(r'[、，,]', span):
            token = token.strip()
            if 1 <= len(token) <= 6 and re.fullmatch(r'[一-鿿]+', token):
                # 去除 "又"、"属焉"、"皆"等干扰
                if token in ('又', '皆', '有', '又属', '属焉', '中', '外'):
                    continue
                if token not in seen:
                    seen.add(token)
                    names.append(token)
    return names


def extract_jue_20(body):
    """提取 20 等爵。"""
    jue = []
    # "爵：一级曰公士，二上造，三簪袅..."
    m = re.search(r'爵：一级曰(.+?)[。]', body)
    if not m:
        return jue
    text = m.group(1)
    # 按 "，" 拆分
    for item in text.split('，'):
        item = item.strip()
        # 去前缀 "N曰 " / "N "
        cleaned = re.sub(r'^[一二三四五六七八九十]+\s*[级]?\s*[曰]?\s*', '', item)
        cleaned = cleaned.strip()
        if 1 <= len(cleaned) <= 6 and re.fullmatch(r'[一-鿿]+', cleaned):
            jue.append(cleaned)
    # 加入 "彻侯/通侯/列侯" 等附加
    jue.extend(['彻侯', '通侯', '列侯', '关内侯'])
    return jue


# 分类识别：根据段落关键字决定所属 section
def classify_paragraph(paragraph, head):
    """给段落分配 category key。返回 str。"""
    if head in ('相国', '丞相', '太尉', '御史大夫', '大司徒', '大司马', '大司空'):
        return 'sangong'
    if head in ('太傅', '太师', '太保', '少傅', '少师', '少保'):
        return 'shifu'
    if head in ('前后左右将军',):
        return 'military'
    if head in ('奉常', '太常', '郎中令', '光禄勋', '卫尉', '太仆', '廷尉', '大理',
                '典客', '大行令', '大鸿胪', '宗正', '治粟内史', '大农令', '大司农', '少府'):
        return 'jiuqing'
    if head in ('中尉', '执金吾', '将作少府', '将作大匠', '詹事',
                '典属国', '水衡都尉', '内史', '主爵中尉', '护军都尉',
                '司隶校尉', '奉车都尉', '驸马都尉', '将行', '大长秋'):
        return 'liqing'
    if head in ('博士',):
        return 'wenxue'
    if head in ('监御史', '郡守', '太守', '郡尉', '关都尉', '部刺史', '牧'):
        return 'junli'
    if head in ('县令', '县长', '县令、长'):
        return 'xianli'
    if '校尉' in (head or '') or head in ('城门校尉', '中垒校尉', '屯骑校尉',
                                          '步兵校尉', '越骑校尉', '长水校尉',
                                          '虎贲校尉', '射声校尉', '西域都护',
                                          '戊己校尉'):
        return 'military'
    # 宫廷近侍
    if head in ('太子太傅', '太子少傅',):
        return 'shifu'
    # 兜底：根据段落关键字判断
    if paragraph.startswith('爵：'):
        return 'jue'
    if '太子门大夫' in paragraph and '太子' in (head or ''):
        return 'shifu'
    return 'other'


# 分类到细分的手工映射（针对属官）
SUBOFFICIAL_CATEGORY_OVERRIDE = {
    # 郎中令段下的官 → 宫廷近侍/文学
    '太中大夫': 'wenxue', '中大夫': 'wenxue', '谏大夫': 'wenxue',
    '光禄大夫': 'wenxue', '议郎': 'wenxue',
    '中郎': 'palace', '侍郎': 'palace', '郎中': 'palace',
    '郎': 'palace', '谒者': 'palace', '仆射': 'palace',
    '期门': 'palace', '羽林': 'palace', '虎贲郎': 'palace',
    '中郎将': 'military',
    # 奉常段下
    '太乐': 'liqing', '太祝': 'liqing', '太宰': 'liqing',
    '太史': 'liqing', '太卜': 'liqing', '太医': 'liqing',
    # 少府段下
    '尚书': 'palace', '中书': 'palace', '黄门': 'palace',
    '中黄门': 'palace', '小黄门': 'palace',
    '给事中': 'palace',
    '侍中': 'palace', '常侍': 'palace', '中常侍': 'palace',
    # 太子官
    '太子舍人': 'palace', '太子门大夫': 'palace',
    '太子庶子': 'palace', '太子先马': 'palace', '太子洗马': 'palace',
}


def main():
    body = load_baiguan_text()
    print(f'《百官公卿表》正文长度: {len(body)} 字符')

    # 全段落列表
    paragraphs = split_paragraphs(body)
    print(f'段落数: {len(paragraphs)}')

    result = defaultdict(list)
    seen = defaultdict(set)  # cat -> set of names

    def add(name, cat):
        if not name:
            return
        name = name.strip()
        if not (1 <= len(name) <= 8):
            return
        if not re.fullmatch(r'[一-鿿]+', name):
            return
        # 排除显然不是官名的词
        if name in ('不常置', '景帝', '武帝', '宣帝', '哀帝', '平帝', '成帝', '王莽',
                    '秦制', '秦官', '古官', '周官', '汉官', '二千石', '六百石',
                    '千石', '长吏', '少吏', '银印', '金印', '青绶', '紫绶', '黄绶'):
            return
        # 单字且歧义太重的（"长"/"令"/"丞" 作为官名太宽泛）
        if len(name) == 1 and name in ('长', '令', '丞', '尉', '守', '相', '史',
                                       '郎', '将', '卿', '君', '侯', '王', '公'):
            return
        if name in SUBOFFICIAL_CATEGORY_OVERRIDE:
            cat = SUBOFFICIAL_CATEGORY_OVERRIDE[name]
        if name in seen[cat]:
            return
        seen[cat].add(name)
        result[cat].append(name)

    # 遍历段落
    for para in paragraphs:
        # 跳过非官制段（序言/总论等）
        if not HEAD_PATTERN.match(para):
            continue
        heads, aliases = extract_head_and_aliases(para)
        if not heads:
            continue
        # 用第一个 head 判定段落类别（大多段首的主官就是分类依据）
        cat = classify_paragraph(para, heads[0])
        if not cat or cat == 'other':
            continue
        for h in heads:
            add(h, cat)
        for a in aliases:
            add(a, cat)
        # 属官
        sub_names = extract_sub_officials(para)
        for sn in sub_names:
            # 附属官如无 override，暂归 'other' 避免混乱
            sub_cat = SUBOFFICIAL_CATEGORY_OVERRIDE.get(sn, None)
            if sub_cat:
                add(sn, sub_cat)

    # 20 等爵
    jue_names = extract_jue_20(body)
    for j in jue_names:
        add(j, 'jue')

    # 诸侯王相关 — 多宫卫尉属九卿级（与中央卫尉同级）；多宫少府/詹事属列卿
    for name in ('长乐卫尉', '长信卫尉'):
        add(name, 'jiuqing')
    for name in ('诸侯王', '长信詹事', '长信少府', '长乐少府'):
        add(name, 'liqing')

    # 输出
    out = {k: sorted(v) for k, v in result.items()}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print()
    print('提取结果：')
    for cat, names in sorted(out.items(), key=lambda x: -len(x[1])):
        print(f'  {cat:<10} {len(names):>4} 项: {names[:8]}...' if len(names) > 8 else f'  {cat:<10} {len(names):>4} 项: {names}')
    print(f'\n写入: {OUT}')


if __name__ == '__main__':
    main()
