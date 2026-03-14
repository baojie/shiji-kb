#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单字人名省称推断脚本

逻辑：
  1. 扫描章节内已标注全名 @Name@（len ≥ 2）
  2. 取末字作省称候选（过滤高歧义字）
  3. 在未标注文字中匹配句法框架（主语位/宾语位）
  4. 输出建议标注列表到 doc/analysis/patch/NNN_省称建议.tsv

用法：
  python scripts/infer_single_char_names.py --chapter 007   # 单章
  python scripts/infer_single_char_names.py --all           # 全量130章
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

CHAPTER_DIR = Path('chapter_md')
PATCH_DIR   = Path('doc/analysis/patch')

# ── 高歧义字：不能作为省称候选的字 ─────────────────────────────────────────────
# 虚词、代词、常见动词、量词——这些字单独出现大概率不是人名省称
AMBIGUOUS_CHARS = frozenset(
    '也矣焉哉耳兮邪欤与耶乎之者所而且则虽若如苟即然顾但况抑或故'
    '以于於自从由为因及被不弗未无非莫勿毋否匪皆悉咸俱亦又既已尽'
    '都均共并遂乃便方正将当固旋继仍复再更还益愈甚尤颇稍仅止才殊极'
    '最过岂宁庶幸请敢肯诚果竟终卒此彼是斯夫兹其何安曷奚胡谁孰'
    '吾我余予汝尔子君朕寡孤卿'
    # 高频动词（单独出现大概率是动词不是人名）
    '曰云言谓告问对答命令使有无在来去入出上下行止'
    '伐攻战击败胜杀斩诛生死知见封拜立废'
    # 数词/量词
    '一二三四五六七八九十百千万亿年月日时岁里人口'
    # 官职/称谓后缀——这些字单独出现是官职/称谓，不是人名省称
    '王侯公帝后将军相令尉丞卿史监都守台臣氏'
    # 虽可作人名末字，但在省称位置极易与动词/状态义混淆
    '虏平楚越燕赵齐魏韩秦周汉'   # 国名/地名字，省称极易误判
)

# ── 句法框架：主语位（省称后接言说/行动词） ────────────────────────────────────
SUBJECT_SUFFIXES = [
    '曰', '乃', '遂', '则', '亦',  # 最常见
    '乃曰', '遂曰', '又曰', '复曰',
    '与', '率', '将', '引', '拔',
]

# ── 句法框架：宾语位（动词后接省称） ────────────────────────────────────────────
OBJECT_PREFIXES = [
    '斩', '杀', '诛', '败', '擒', '俘', '虏', '刺', '射', '逐',
    '破', '降', '执', '縳', '囚', '赦', '赏', '赐', '封',
]

# ── 标注符号模式（v2.1 格式，用于构建掩码） ────────────────────────────────────────
ALL_ANNOT_RE = re.compile(
    r'〖[@=;%&\'^~\*!#\+\$][^〖〗\n]+?〗'
    r'|〚[^〛\n]+?〛'
    r'|《[^》\n]+?》'
    r'|〈[^〉\n]+?〉'
    r'|【[^】\n]+?】'
    r'|〔[^〕\n]+?〕'
)

PLACEHOLDER = '░'  # 单字占位符（非汉字，不影响位置计算）

CHINESE_CHAR_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')


def mask_annotations(text: str) -> str:
    """将所有已标注span替换为等长占位符，保持字符位置不变。"""
    result = list(text)
    for m in ALL_ANNOT_RE.finditer(text):
        for i in range(m.start(), m.end()):
            result[i] = PLACEHOLDER
    return ''.join(result)


def extract_tagged_names(text: str) -> set:
    """提取所有 〖@Name〗 中长度 ≥ 2、且内容为纯汉字（不含标点/符号）的人名。"""
    names = set()
    for m in re.finditer(r'〖@([^〖〗\n]{2,8})〗', text):
        name = m.group(1)
        # 只保留纯汉字（不含嵌套符号，避免提取到破损标注）
        if re.fullmatch(r'[\u4e00-\u9fff\u3400-\u4dbf]+', name):
            names.add(name)
    return names


def abbreviation_from_name(name: str) -> str | None:
    """
    从人名中提取省称候选（末字）。
    过滤条件：
    - 末字歧义高（在 AMBIGUOUS_CHARS 中）→ 返回 None
    - 名字本身含歧义字（如「言恨不用」中的「不」）→ 返回 None
    - 末字是「氏」→ 返回 None
    """
    if len(name) < 2:
        return None
    # 全名中含歧义字（中间字含虚词/动词意味着这不是正常人名）
    if any(ch in AMBIGUOUS_CHARS for ch in name):
        return None
    last = name[-1]
    if last in AMBIGUOUS_CHARS or last == '氏':
        return None
    return last


def find_abbreviation_hits(masked: str, original: str, abbrev: str,
                            context_chars: int = 10) -> list:
    """
    在掩码文本中搜索满足句法框架的省称，返回建议列表。
    每条建议：{pos, pattern, pattern_type, context}

    关键约束：
    - 主语位：省称前必须是子句边界（标点/注记符/行首），避免「岁馀乃」误判
    - 宾语位：省称后必须是子句边界或行尾，避免「降平齐」误判
    """
    hits = []

    # 子句边界字符集（省称前/后允许出现的字符）
    CLAUSE_BOUNDARY_BEFORE = set('，。！？；、「」『』【】〔〕《》〈〉↵\n ░')
    CLAUSE_BOUNDARY_AFTER  = set('，。！？；、「」『』【】〔〕《》〈〉↵\n ░')

    def before_is_boundary(pos: int) -> bool:
        """省称前一字是否为子句边界（或已掩码/行首）"""
        if pos == 0:
            return True
        prev = masked[pos - 1]
        return prev in CLAUSE_BOUNDARY_BEFORE or not CHINESE_CHAR_RE.match(prev)

    def after_is_boundary(pos: int, length: int = 1) -> bool:
        """省称后一字是否为子句边界（或已掩码/行尾）"""
        idx = pos + length
        if idx >= len(masked):
            return True
        nxt = masked[idx]
        return nxt in CLAUSE_BOUNDARY_AFTER or not CHINESE_CHAR_RE.match(nxt)

    # 主语位：{abbrev}{suffix}，且 abbrev 前是边界
    for suffix in SUBJECT_SUFFIXES:
        pat = re.compile(re.escape(abbrev) + re.escape(suffix))
        for m in pat.finditer(masked):
            pos = m.start()
            if (masked[pos] != PLACEHOLDER
                    and CHINESE_CHAR_RE.match(original[pos])
                    and before_is_boundary(pos)):
                ctx_s = max(0, pos - context_chars)
                ctx_e = min(len(original), pos + len(suffix) + context_chars)
                hits.append({
                    'pos': pos,
                    'pattern': abbrev + suffix,
                    'pattern_type': '主语位',
                    'context': original[ctx_s:ctx_e].replace('\n', '↵'),
                })

    # 宾语位：{prefix}{abbrev}，且 abbrev 后是边界
    for prefix in OBJECT_PREFIXES:
        pat = re.compile(re.escape(prefix) + re.escape(abbrev))
        for m in pat.finditer(masked):
            pos = m.start() + len(prefix)
            if (masked[pos] != PLACEHOLDER
                    and CHINESE_CHAR_RE.match(original[pos])
                    and after_is_boundary(pos)):
                ctx_s = max(0, pos - context_chars)
                ctx_e = min(len(original), pos + 1 + context_chars)
                hits.append({
                    'pos': pos,
                    'pattern': prefix + abbrev,
                    'pattern_type': '宾语位',
                    'context': original[ctx_s:ctx_e].replace('\n', '↵'),
                })

    # 去重（同一位置）
    seen_pos = set()
    unique_hits = []
    for h in hits:
        if h['pos'] not in seen_pos:
            seen_pos.add(h['pos'])
            unique_hits.append(h)

    return unique_hits


def analyze_chapter(fpath: Path) -> list:
    """
    分析单章，返回省称建议列表。
    每条：{chapter, full_name, abbrev, pos, pattern, pattern_type, context}
    """
    text = fpath.read_text(encoding='utf-8')
    masked = mask_annotations(text)

    tagged_names = extract_tagged_names(text)
    if not tagged_names:
        return []

    chapter = fpath.name.replace('.tagged.md', '')

    # 按省称聚合全名（多个全名可能有相同省称）
    abbrev_to_names: dict[str, list] = defaultdict(list)
    for name in tagged_names:
        abbrev = abbreviation_from_name(name)
        if abbrev:
            abbrev_to_names[abbrev].append(name)

    suggestions = []
    for abbrev, full_names in abbrev_to_names.items():
        hits = find_abbreviation_hits(masked, text, abbrev)
        for h in hits:
            suggestions.append({
                'chapter': chapter,
                'full_name': '|'.join(sorted(set(full_names))),
                'abbrev': abbrev,
                'pos': h['pos'],
                'pattern': h['pattern'],
                'pattern_type': h['pattern_type'],
                'context': h['context'],
            })

    # 按位置排序
    suggestions.sort(key=lambda x: x['pos'])
    return suggestions


def run_chapter(chapter_id: str):
    """单章模式。"""
    pattern = str(CHAPTER_DIR / f'{chapter_id}_*.tagged.md')
    import glob
    files = glob.glob(pattern)
    if not files:
        print(f'[ERROR] 未找到章节 {chapter_id}')
        return

    fpath = Path(files[0])
    print(f'分析：{fpath.name}')
    suggestions = analyze_chapter(fpath)

    if not suggestions:
        print('  无省称建议。')
        return

    print(f'  发现 {len(suggestions)} 条省称建议：')
    for s in suggestions[:30]:
        print(f'  [{s["pattern_type"]}] @{s["full_name"]}@ → 省称 @{s["abbrev"]}@'
              f'  pattern={s["pattern"]}  ctx=「{s["context"]}」')

    # 保存到 patch 目录
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    chapter = fpath.name.replace('.tagged.md', '')
    out = PATCH_DIR / f'{chapter}_省称建议.tsv'
    _write_tsv(out, suggestions)
    print(f'  已保存：{out}')


def run_all():
    """全量130章模式。"""
    files = sorted(CHAPTER_DIR.glob('*.tagged.md'))
    print(f'共 {len(files)} 章，开始分析...')
    PATCH_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    for i, fpath in enumerate(files, 1):
        suggestions = analyze_chapter(fpath)
        if suggestions:
            chapter = fpath.name.replace('.tagged.md', '')
            out = PATCH_DIR / f'{chapter}_省称建议.tsv'
            _write_tsv(out, suggestions)
            total += len(suggestions)
            print(f'  [{i:3d}] {fpath.name[:30]:30s}  {len(suggestions):3d} 条建议', flush=True)

    print(f'\n✅ 共 {total} 条省称建议，已保存到 {PATCH_DIR}/')


def _write_tsv(out: Path, suggestions: list):
    """写入建议 TSV 文件。"""
    with open(out, 'w', encoding='utf-8') as f:
        f.write('章节\t全名\t省称\t位置\t句法框架类型\t匹配模式\t上下文\n')
        for s in suggestions:
            f.write(f'{s["chapter"]}\t{s["full_name"]}\t{s["abbrev"]}\t'
                    f'{s["pos"]}\t{s["pattern_type"]}\t{s["pattern"]}\t{s["context"]}\n')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='单字人名省称推断')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--chapter', metavar='NNN', help='单章测试（如 007）')
    group.add_argument('--all', action='store_true', help='全量130章')
    args = parser.parse_args()

    if args.chapter:
        run_chapter(args.chapter)
    else:
        run_all()


if __name__ == '__main__':
    main()
