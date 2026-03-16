#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新4类实体标注脚本

对史记130章未标注文字中，扫描并建议标注：
  典籍〖{〗  礼仪〖:〗  刑法〖[〗  思想〖_〗

逻辑：
  1. 加载各类实体词表（来自 infer_entity_type.py）
  2. 对每章，在未标注文字中搜索词表词（按字数降序贪心匹配）
  3. 输出建议标注 TSV 到 doc/analysis/patch/NNN_新实体.tsv

字段（TSV）：
  章节    正名    词    位置    框架类型    匹配模式    上下文    实体类型

用法：
  python scripts/tag_new_entity_types.py --chapter 001
  python scripts/tag_new_entity_types.py --all
  python scripts/tag_new_entity_types.py --all --types 典籍 礼仪 刑法 思想
  python scripts/tag_new_entity_types.py --all --min-freq 2
"""

import re
import argparse
import glob
from pathlib import Path
from collections import defaultdict

CHAPTER_DIR = Path('chapter_md')
PATCH_DIR   = Path('doc/analysis/patch')

# ── 4类新实体词表 ──────────────────────────────────────────────────────────────

BOOK_WORDS = {
    '春秋', '诗经', '尚书', '周易', '礼记', '周礼', '仪礼', '论语', '孟子',
    '老子', '庄子', '荀子', '韩非', '管子', '晏子', '孙子', '吴子',
    '左传', '国语', '世本', '大雅', '小雅', '国风', '鲁颂', '商颂', '周颂',
    '大学', '中庸', '孝经', '尔雅', '过秦', '子虚', '大人', '上林',
    '夏书', '商书', '周书', '虞书', '太誓', '牧誓', '金縢', '大诰',
    # 楚辞类
    '离骚', '九歌', '九章', '天问',
    # 诸子/史书补充
    '吕览', '战国策', '国策', '鬼谷子',
    '新书', '春秋繁露', '淮南',   # 贾谊/董仲舒/刘安
    # 韩非子篇目（其他章节可能出现）
    '说难', '孤愤', '兵法',
    # 注：诗/书/易/礼/乐 单字太歧义（同时是普通名词），不列入
}

RITUAL_WORDS = {
    '封禅', '宗庙', '社稷', '明堂', '郊祀', '祭祀', '盟誓', '朝聘', '赐爵',
    '庙祭', '宗祀', '祭天', '祭地', '告庙', '飨庙', '配享', '禘祭', '腊祭',
    '时祭', '合祭', '巡狩', '享祀', '祈祷', '祝祭', '献祭', '庙享', '礼乐',
    '乐舞', '冠礼', '婚礼', '丧礼', '葬礼', '朝会', '朝见', '朝拜', '朝觐',
    '纳贡', '进贡', '朝贡', '会盟', '立庙', '置庙', '飨祀', '血食', '望祭',
    '五岳', '五祀', '太庙', '禅让', '郊天', '郊祭', '郊庙', '庙号',
    '谥号', '庙讳', '宗祧', '昭穆', '虞祭', '练祭', '祔祭', '大祥', '小祥',
    '饮至', '告成', '飨食', '赐食', '朝食', '朝礼',
}

LEGAL_WORDS = {
    '斩首', '弃市', '腰斩', '族诛', '夷族', '车裂', '凌迟', '磔刑', '枭首',
    '坐法', '当斩', '当死', '论死', '处死', '极刑', '大辟', '死罪', '死刑',
    '诛三族', '夷三族', '灭族', '族灭', '诛族', '连坐', '收孥', '没入',
    '髡刑', '黥刑', '刖刑', '宫刑', '劓刑', '肉刑', '笞刑', '杖刑',
    '大赦', '赦免', '特赦', '赦令', '赦罪', '免罪', '赎罪', '赎死', '赎刑',
    '赎为', '减死', '贬爵', '削爵', '夺爵', '除爵', '免官', '下狱',
    '论罪', '坐罪', '获罪', '系狱', '囚禁', '桎梏', '就戮', '伏诛',
    '具五刑', '论腰斩', '行军法', '夷三族', '诛灭', '枭示',
}

CONCEPT_WORDS = {
    '君子', '圣人', '天地', '仁义', '阴阳', '王道', '天命', '天道', '礼义', '道德',
    '霸道', '仁政', '德治', '礼制', '法治', '人道', '天理', '人心', '民心', '民意',
    '忠义', '节义', '大义', '正义', '道义', '仁爱', '仁德', '圣德', '圣王', '贤王',
    '明君', '暴君', '昏君', '仁君', '五行', '八卦', '刚柔', '动静', '变化', '天人',
    '圣贤', '贤能', '才德', '德行', '品德', '气节', '风骨', '廉耻', '忠孝',
    '礼乐', '诗书', '六艺', '百家', '诸子', '黄老', '名实', '华夷', '夷夏',
    '正统', '法统', '道统', '天下', '大同', '治乱', '兴衰', '王霸',
    '无为', '清静', '自然', '道家', '儒家', '法家', '墨家', '纵横',
    '富贵', '贫贱', '祸福', '吉凶', '是非', '善恶', '邪正',
    # 儒家伦理体系补充
    '礼义廉耻', '仁义礼智信', '三纲', '五常',
    # 政治哲学补充
    '大一统', '天人合一', '德政', '义利',
}

# 类型名 → 词表 + 符号
TYPE_CONF = {
    '典籍': {'words': BOOK_WORDS,    'open': '〖{', 'close': '〗'},
    '礼仪': {'words': RITUAL_WORDS,  'open': '〖:', 'close': '〗'},
    '刑法': {'words': LEGAL_WORDS,   'open': '〖[', 'close': '〗'},
    '思想': {'words': CONCEPT_WORDS, 'open': '〖_', 'close': '〗'},
}

# ── 已有标注的检测正则（含新4类）──────────────────────────────────────────────
ALL_ANNOT_RE = re.compile(
    r'〖[@=;%&\'^~•!#\+\$\?\{\:\[\_][^〖〗\n]+?〗'
)

PLACEHOLDER = '░'


def mask_annotations(text: str) -> str:
    result = list(text)
    for m in ALL_ANNOT_RE.finditer(text):
        for i in range(m.start(), m.end()):
            result[i] = PLACEHOLDER
    return ''.join(result)


def build_word_map(types_filter: list = None) -> dict:
    """
    返回 {词: (词, 实体类型)} 映射（去重，按类型优先级：刑法>礼仪>典籍>思想）。
    """
    priority = ['刑法', '礼仪', '典籍', '思想']
    word_map = {}
    for cat in priority:
        if types_filter and cat not in types_filter:
            continue
        conf = TYPE_CONF[cat]
        for word in conf['words']:
            word = word.strip()
            if not word:
                continue
            if word not in word_map:
                word_map[word] = (word, cat)
    return word_map


def scan_chapter(fpath: Path, word_map: dict, min_freq: int = 1) -> list:
    """
    扫描单章，返回建议列表。
    每条：{chapter, canonical, word, pos, context, entity_type}
    """
    text = fpath.read_text(encoding='utf-8')
    masked = mask_annotations(text)

    chapter = fpath.name.replace('.tagged.md', '')

    candidates = defaultdict(list)  # {(word, canonical, cat): [occ, ...]}

    # 按词长降序排列
    sorted_words = sorted(word_map.keys(), key=len, reverse=True)

    covered = set()

    for word in sorted_words:
        canonical, cat = word_map[word]
        search_start = 0
        while True:
            idx = masked.find(word, search_start)
            if idx == -1:
                break
            search_start = idx + 1

            positions = set(range(idx, idx + len(word)))
            if positions & covered:
                continue
            if any(masked[i] == PLACEHOLDER for i in positions):
                continue

            ctx_s = max(0, idx - 10)
            ctx_e = min(len(text), idx + len(word) + 10)
            context = text[ctx_s:ctx_e].replace('\n', '↵')

            key = (word, canonical, cat)
            candidates[key].append({'pos': idx, 'context': context})
            covered.update(positions)

    suggestions = []
    for (word, canonical, cat), occurrences in candidates.items():
        if len(occurrences) < min_freq:
            continue
        for occ in occurrences:
            suggestions.append({
                'chapter': chapter,
                'canonical': canonical,
                'word': word,
                'pos': occ['pos'],
                'frame_type': '词表匹配',
                'pattern': word,
                'context': occ['context'],
                'entity_type': cat,
            })

    suggestions.sort(key=lambda x: x['pos'])
    return suggestions


def write_tsv(out: Path, suggestions: list):
    with open(out, 'w', encoding='utf-8') as f:
        f.write('章节\t正名\t词\t位置\t框架类型\t匹配模式\t上下文\t实体类型\n')
        for s in suggestions:
            f.write(f'{s["chapter"]}\t{s["canonical"]}\t{s["word"]}\t'
                    f'{s["pos"]}\t{s["frame_type"]}\t{s["pattern"]}\t'
                    f'{s["context"]}\t{s["entity_type"]}\n')


def run_chapter(chapter_id: str, word_map: dict, min_freq: int):
    pattern = str(CHAPTER_DIR / f'{chapter_id}_*.tagged.md')
    files = glob.glob(pattern)
    if not files:
        print(f'[ERROR] 未找到章节 {chapter_id}')
        return

    fpath = Path(files[0])
    print(f'扫描：{fpath.name}')
    suggestions = scan_chapter(fpath, word_map, min_freq)

    if not suggestions:
        print('  无建议。')
        return

    print(f'  发现 {len(suggestions)} 条建议（词种数：'
          f'{len(set(s["word"] for s in suggestions))}）：')

    by_word = defaultdict(list)
    for s in suggestions:
        by_word[s['word']].append(s)
    for word, items in sorted(by_word.items(), key=lambda x: -len(x[1]))[:20]:
        cat = items[0]['entity_type']
        print(f'  {cat}  {word}  {len(items)}处  示例：「{items[0]["context"]}」')

    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    chapter = fpath.name.replace('.tagged.md', '')
    out = PATCH_DIR / f'{chapter}_新实体.tsv'
    write_tsv(out, suggestions)
    print(f'  已保存：{out}')


def run_all(word_map: dict, min_freq: int):
    files = sorted(CHAPTER_DIR.glob('*.tagged.md'))
    print(f'共 {len(files)} 章，开始扫描...')
    PATCH_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    for i, fpath in enumerate(files, 1):
        suggestions = scan_chapter(fpath, word_map, min_freq)
        if suggestions:
            chapter = fpath.name.replace('.tagged.md', '')
            out = PATCH_DIR / f'{chapter}_新实体.tsv'
            write_tsv(out, suggestions)
            total += len(suggestions)
            print(f'  [{i:3d}] {fpath.name[:35]:35s}  {len(suggestions):4d} 条', flush=True)

    print(f'\n✅ 合计 {total} 条新实体建议，已保存到 {PATCH_DIR}/')


def main():
    parser = argparse.ArgumentParser(description='新4类实体标注（典籍/礼仪/刑法/思想）')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--chapter', metavar='NNN')
    group.add_argument('--all', action='store_true')
    parser.add_argument('--types', nargs='+',
                        choices=list(TYPE_CONF.keys()),
                        help='只扫描指定类型（默认全部）')
    parser.add_argument('--min-freq', type=int, default=1,
                        help='章节内最少出现次数（默认1）')
    args = parser.parse_args()

    word_map = build_word_map(args.types)
    print(f'词表加载完毕：{len(word_map)} 词'
          f'（类型：{args.types or list(TYPE_CONF.keys())}）')

    if args.chapter:
        run_chapter(args.chapter, word_map, args.min_freq)
    else:
        run_all(word_map, args.min_freq)


if __name__ == '__main__':
    main()
