#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实体类型推断模块

基于 doc/analysis/unknown_candidate_words.tsv 中的词频+类型数据，
对给定词语推断其最可能的实体类型。

用法（作为模块导入）：
    from scripts.infer_entity_type import infer, load_dict
    d = load_dict()
    print(infer('封禅', d))   # → '礼仪〈〉'
    print(infer('弃市', d))   # → '刑法【】'
    print(infer('未知词', d)) # → ''

用法（命令行）：
    python scripts/infer_entity_type.py 封禅 弃市 郡县
    python scripts/infer_entity_type.py --file /tmp/words.txt
"""

import re
import sys
from pathlib import Path

# TSV 路径（相对于项目根目录）
_TSV_PATH = Path(__file__).parent.parent / 'doc/analysis/unknown_candidate_words.tsv'

# ── 规则词表（覆盖 TSV 未收录的词，优先级高于 TSV）────────────────────────────

# 官职$ 后缀
_OFFICIAL_SUFFIXES = frozenset('侯相尉令丞卿史监都守台')
_OFFICIAL_KEYWORDS = {
    '将军','太子','太后','丞相','太尉','御史','廷尉','治粟','内史',
    '典客','宗正','少府','太仆','博士','郎中','侍中','黄门','谒者',
    '尚书','都尉','校尉','中尉','太守','县令','县长','县丞','县尉',
    '刺史','州牧','三公','九卿','百官','群臣','朝臣','列侯','彻侯',
}

# 地名= 后缀
_PLACE_SUFFIXES = frozenset('山水河海城池湖泽关塞原陵丘亭津渡岸洲岛宫殿台苑园庙堂谷野渚浦坂岭峰崖壁')

# 族群~ 后缀
_TRIBE_SUFFIXES = frozenset('族氏夷戎狄蛮羌貊越胡')

# 天文! 星宿字
_ASTRO_CHARS = frozenset('星宿辰斗牛女虚危室壁奎娄胃昴毕觜参井鬼柳张翼轸角亢氐房心尾箕')
_ASTRO_KEYWORDS = {
    '太白','岁星','荧惑','填星','辰星','北斗','南斗','彗星','流星',
    '客星','妖星','天象','天文','星象','星官','日食','月食',
}

# 生物〖+〗 后缀
_FLORA_FAUNA_SUFFIXES = frozenset('草木花树鸟鱼虫兽蛇龙鹿虎豹狼熊鹤鹰鸠鸽燕雁鸳鸯')

# 礼仪〈〉
_RITUAL_WORDS = {
    '封禅','宗庙','社稷','明堂','郊祀','祭祀','盟誓','朝聘','赐爵',
    '庙祭','宗祀','祭天','祭地','告庙','飨庙','配享','禘祭','腊祭',
    '时祭','合祭','巡狩','享祀','祈祷','祝祭','献祭','庙享','礼乐',
    '乐舞','冠礼','婚礼','丧礼','葬礼','朝会','朝见','朝拜','朝觐',
    '纳贡','进贡','朝贡','会盟','立庙','置庙','飨祀','血食','望祭',
    '五岳','五祀','太庙','山川',
}

# 刑法【】
_LEGAL_WORDS = {
    '斩首','弃市','腰斩','族诛','夷族','车裂','凌迟','磔刑','枭首',
    '坐法','当斩','当死','论死','处死','极刑','大辟','死罪','死刑',
    '诛三族','夷三族','灭族','族灭','诛族','连坐','收孥','没入',
    '髡刑','黥刑','刖刑','宫刑','劓刑','肉刑','笞刑','杖刑',
    '大赦','赦免','特赦','赦令','赦罪','免罪','赎罪','赎死','赎刑',
    '赎为','减死','贬爵','削爵','夺爵','除爵','免官','下狱',
    '论罪','坐罪','获罪','系狱','囚禁','桎梏','就戮',
}

# 思想/概念〔〕
_CONCEPT_WORDS = {
    '君子','圣人','天地','仁义','阴阳','王道','天命','天道','礼义','道德',
    '霸道','仁政','德治','礼制','法治','人道','天理','人心','民心','民意',
    '忠义','节义','大义','正义','道义','仁爱','仁德','圣德','圣王','贤王',
    '明君','暴君','昏君','仁君','五行','八卦','刚柔','动静','变化','天人',
    '圣贤','贤能','才德','德行','品德','气节','风骨','廉耻','忠孝',
    '礼乐','诗书','六艺','百家','诸子','黄老','名实','华夷','夷夏',
    '正统','法统','道统','天下','大同',
}

# 典籍《》
_BOOK_WORDS = {
    '春秋','诗经','尚书','周易','礼记','周礼','仪礼','论语','孟子',
    '老子','庄子','荀子','韩非','管子','晏子','孙子','吴子',
    '左传','国语','世本','大雅','小雅','国风','鲁颂','商颂','周颂',
    '大学','中庸','孝经','尔雅','过秦','子虚','大人','上林',
    '夏书','商书','周书','虞书',
}

# 神话〚〛
_MYTH_KEYWORDS = {
    '女娲','伏羲','神农','共工','祝融','句芒','蓐收','玄冥','后羿','夸父',
    '西王母','东王公','河伯','雨师','风伯','雷公','电母',
}

# 器物*
_ARTIFACT_KEYWORDS = {
    '宝剑','宝鼎','九鼎','玉璧','玉玺','传国','符节','旌旗','节钺',
    '黄钺','斧钺','弓弩','甲胄','战车','兵器','礼器','祭器',
    '钟鼎','玉器','铜器','铁器','钟磬',
}


def _rule_classify(word: str) -> str:
    """基于规则的分类（不查 TSV）"""
    if word in _BOOK_WORDS:       return '典籍《》'
    if word in _RITUAL_WORDS:     return '礼仪〈〉'
    if word in _LEGAL_WORDS:      return '刑法【】'
    if word in _CONCEPT_WORDS:    return '思想〔〕'
    if word in _MYTH_KEYWORDS:    return '神话〚〛'
    if word in _ASTRO_KEYWORDS:   return '天文!'
    if word in _ARTIFACT_KEYWORDS: return '器物*'
    if word in _OFFICIAL_KEYWORDS: return '官职$'

    # 后缀规则
    if len(word) >= 2:
        last = word[-1]
        if last in _FLORA_FAUNA_SUFFIXES: return '生物〖+〗'
        if last in _TRIBE_SUFFIXES:       return '族群~'
        if last in _PLACE_SUFFIXES:       return '地名='
        if last in _OFFICIAL_SUFFIXES:    return '官职$'
        # 天文：两字均为星宿字
        if len(word) == 2 and word[0] in _ASTRO_CHARS and word[1] in _ASTRO_CHARS:
            return '天文!'

    return ''


def load_dict(tsv_path: Path = None) -> dict:
    """
    加载 TSV 词典，返回 {词: 实体类型} 映射。
    只包含第三列非空的词。
    """
    path = tsv_path or _TSV_PATH
    result = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding='utf-8').splitlines():
        parts = line.split('\t')
        if len(parts) >= 3 and parts[2].strip() and parts[0] != '词':
            result[parts[0]] = parts[2].strip()
    return result


def infer(word: str, tsv_dict: dict = None) -> str:
    """
    推断词语的实体类型。
    优先使用规则，其次查 TSV 词典。
    返回实体类型字符串，无法判断时返回 ''。

    Args:
        word: 待推断的词语
        tsv_dict: 由 load_dict() 返回的字典（可选，避免重复加载）
    """
    # 1. 规则优先
    rule_result = _rule_classify(word)
    if rule_result:
        return rule_result
    # 2. TSV 词典
    if tsv_dict is None:
        tsv_dict = load_dict()
    return tsv_dict.get(word, '')


def infer_batch(words: list, tsv_dict: dict = None) -> dict:
    """批量推断，返回 {词: 类型} 字典"""
    if tsv_dict is None:
        tsv_dict = load_dict()
    return {w: infer(w, tsv_dict) for w in words}


# ── 命令行入口 ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='实体类型推断')
    parser.add_argument('words', nargs='*', help='待推断的词语')
    parser.add_argument('--file', help='从文件读取词语（每行一词）')
    args = parser.parse_args()

    d = load_dict()
    words = args.words or []
    if args.file:
        words += Path(args.file).read_text(encoding='utf-8').splitlines()
    words = [w.strip() for w in words if w.strip()]

    if not words:
        parser.print_help()
        sys.exit(0)

    for w in words:
        t = infer(w, d)
        label = t if t else '（未知）'
        print(f'{w}\t{label}')
