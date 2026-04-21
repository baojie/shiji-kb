#!/usr/bin/env python3
"""
Phase 1：对齐外部白话版本到本库 PN 粒度。

输入：
  - chapter_md/NNN_*.tagged.md           本库带标注原文
  - doc/translation/NNN_*_白话.md         本库 LLM 译文
  - corpus/shiji/段译/NNN_*_段译.txt      hunterhug 段级对照
  - corpus/shiji/白话史记.txt             整本白话（仅白话，无原文）

输出：
  - data/translation_alignment/NNN.json
    每个 PN 一条记录：
      {
        "pn": "1.1",
        "source": "...",            # 原文（去标注）
        "ours":   "...",            # 本库白话（去标注）
        "hunterhug": "...",         # 命中的 hunterhug 段白话
        "hunterhug_conf": 0.92,     # 原文匹配 ratio
        "baihua":   "...",          # 白话史记 对应区间
        "baihua_conf": "proportional"  # 标识用的何种启发式
      }
  - data/translation_alignment/STATS.md  对齐率统计

用法：
    python scripts/align_external_translations.py                # 全库
    python scripts/align_external_translations.py 002 007        # 单章
"""

import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher

CHAPTER_MD = Path('chapter_md')
WHITE_MD = Path('doc/translation')
DUANYI_DIR = Path('corpus/shiji/段译')
BAIHUA_FILE = Path('corpus/shiji/白话史记.txt')
OUTPUT_DIR = Path('data/translation_alignment')

# 本库 chapter_md 用的实体标注
TAG_RE = re.compile(r'〖[@=;%&◆^~•!?+#$:\[_\{][^〖〗]*〗|⟦[○◈◉◇][^⟦⟧]*⟧|〘※[^〘〙]*〙')


def strip_tags(text: str) -> str:
    """去除本库的实体/动词/成语标注，返回纯原文。"""
    # 对消歧 〖T X|Y〗 保留 X（显示名）
    text = re.sub(r'〖[@=;%&◆^~•!?+#$:\[_\{]\s*([^|〗]+)\|[^〗]+〗', r'\1', text)
    text = re.sub(r'⟦[○◈◉◇]([^|⟦⟧]+)\|[^⟦⟧]+⟧', r'\1', text)
    text = re.sub(r'〘※([^|〘〙]+)\|[^〘〙]+〙', r'\1', text)
    # 普通标注只去外壳
    text = re.sub(r'〖[@=;%&◆^~•!?+#$:\[_\{]\s*([^〗]*)〗', r'\1', text)
    text = re.sub(r'⟦[○◈◉◇]([^⟦⟧]*)⟧', r'\1', text)
    text = re.sub(r'〘※([^〘〙]*)〙', r'\1', text)
    return text


def normalize_text(text: str) -> str:
    """规范化文本以便比较：去除空白、全半角标点、""''「」等差异。"""
    # 统一标点
    repl = {
        '「': '"', '」': '"', '『': '"', '』': '"',
        '，': ',', '。': '.', '！': '!', '？': '?',
        '；': ';', '：': ':', '、': ',',
        '（': '(', '）': ')', '〈': '<', '〉': '>',
        '"': '"', '"': '"', ''': "'", ''': "'",
        ' ': '', '\t': '', '\n': '', '\r': '',
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    # 繁简差异不处理（本库简体、段译也简体，不涉及点校本）
    return text


def load_chapter_pns(tagged_path: Path):
    """
    解析 chapter_md/NNN.tagged.md，返回 [(pn_id, source_stripped, source_raw), ...]。
    以 [PN] 标注为分段。
    """
    content = tagged_path.read_text()
    # 找到所有 [N] 或 [N.M] 或 [N.M.K] 的起始，按先后切分
    pattern = re.compile(r'\[(\d+(?:\.\d+)*)\]\s*')
    parts = pattern.split(content)
    # parts = ['pre_text', 'pn1', 'body1', 'pn2', 'body2', ...]
    results = []
    for i in range(1, len(parts), 2):
        pn = parts[i]
        if pn == '0':
            continue
        body = parts[i + 1] if i + 1 < len(parts) else ''
        # 去除到下一个 [ 或结尾
        # 去除 markdown 标题行 ## xxx
        body = re.sub(r'^#+\s+[^\n]+\n', '', body, flags=re.M)
        # 去除 ::: blocks
        body = re.sub(r':::[^\n]*\n', '', body)
        source_raw = body.strip()
        source_stripped = strip_tags(source_raw).strip()
        results.append((pn, source_stripped, source_raw))
    return results


def load_white_translation(white_path: Path):
    """解析 doc/translation/NNN_白话.md，返回 {pn: white_text_stripped}。"""
    content = white_path.read_text()
    result = {}
    pattern = re.compile(r'^##\s*\[(\d+(?:\.\d+)*)\][^\n]*\n((?:(?!^##).)*)', re.M | re.DOTALL)
    for m in pattern.finditer(content):
        pn = m.group(1)
        body = m.group(2).strip()
        result[pn] = strip_tags(body)
    return result


def load_duanyi(duanyi_path: Path):
    """
    解析 corpus/shiji/段译/NNN_段译.txt，返回 [(原文, 译文), ...]。
    每个块格式：
      【原文】
      ...
      【译文】
      ...
      ---
    """
    if not duanyi_path.exists():
        return []
    content = duanyi_path.read_text()
    pairs = []
    # Split by ---
    blocks = re.split(r'\n-{3,}\n', content)
    for blk in blocks:
        m_orig = re.search(r'【原文】\s*\n(.*?)(?=\n【译文】|\n\n|$)', blk, re.DOTALL)
        m_trans = re.search(r'【译文】\s*\n(.*?)(?=\n【|$)', blk, re.DOTALL)
        if m_orig and m_trans:
            pairs.append((m_orig.group(1).strip(), m_trans.group(1).strip()))
        elif m_orig:
            pairs.append((m_orig.group(1).strip(), ''))
    return pairs


def load_baihua_by_chapter():
    """
    解析 corpus/shiji/白话史记.txt，按章节切分。
    开头有 TOC，跳过；正文以章名（单独一行、无缩进）开始。
    返回 {chapter_name: [sentence, ...]}。
    """
    if not BAIHUA_FILE.exists():
        return {}
    lines = BAIHUA_FILE.read_text().splitlines()
    # 找第一个"五帝本纪"作为内容起点（TOC 里有缩进版本）
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip() == '五帝本纪' and not line.startswith(' '):
            content_start = i
            break
    # 收集所有章名（必须是准确章名集合）
    # 但我们不知道所有章名，先用 chapter_md 的章名集合
    known_names = set()
    for f in CHAPTER_MD.glob('*.tagged.md'):
        m = re.match(r'\d{3}_(.+)\.tagged\.md', f.name)
        if m:
            known_names.add(m.group(1))

    chapters = {}
    current = None
    buf = []
    for line in lines[content_start:]:
        stripped = line.strip()
        # 判断是否章名行：左边无缩进且内容是已知章名
        if not line.startswith(' ') and not line.startswith('　') and stripped in known_names:
            if current is not None:
                chapters[current] = [s for s in buf if s]
            current = stripped
            buf = []
        elif current:
            # 移除行首"　　"等装饰并按"。"或"。"粗切分
            s = re.sub(r'^[\s　]+', '', line).rstrip()
            if s:
                buf.append(s)
    if current is not None:
        chapters[current] = [s for s in buf if s]
    return chapters


def align_hunterhug(pns, duanyi_pairs):
    """
    把 hunterhug 的 [(原文, 译文), ...] 对齐到 PN。
    策略：对每个 PN，求其 normalize 后的 source 在某 hunterhug 原文 normalize 中的最长匹配块比例。
    返回 {pn: (best_trans, confidence)}。
    """
    result = {}
    duanyi_normed = [(normalize_text(o), t) for o, t in duanyi_pairs]
    for pn, source_stripped, _ in pns:
        src_norm = normalize_text(source_stripped)
        if not src_norm:
            result[pn] = ('', 0.0)
            continue
        best_ratio = 0.0
        best_trans = ''
        for o_norm, trans in duanyi_normed:
            if not o_norm:
                continue
            # 使用 SequenceMatcher 找 src 在 o 中的最长子串
            sm = SequenceMatcher(None, src_norm, o_norm, autojunk=False)
            match = sm.find_longest_match(0, len(src_norm), 0, len(o_norm))
            ratio = match.size / len(src_norm) if src_norm else 0.0
            if ratio > best_ratio:
                best_ratio = ratio
                best_trans = trans
        result[pn] = (best_trans, round(best_ratio, 3))
    return result


def align_baihua(pns, baihua_sentences):
    """
    按比例估算：第 i / N 个 PN 对应白话的 i/N ~ (i+1)/N 区段。
    返回 {pn: (text, 'proportional')}。
    """
    result = {}
    n = len(pns)
    total = len(baihua_sentences)
    if n == 0 or total == 0:
        for pn, _, _ in pns:
            result[pn] = ('', 'none')
        return result
    for i, (pn, _, _) in enumerate(pns):
        start = int(i * total / n)
        end = int((i + 1) * total / n)
        end = max(start + 1, end)
        text = ''.join(baihua_sentences[start:end])
        result[pn] = (text, 'proportional')
    return result


def align_chapter(chapter_num: str) -> dict:
    """对单章做三方对齐，返回记录 dict。"""
    tagged = next(CHAPTER_MD.glob(f'{chapter_num}_*.tagged.md'), None)
    if not tagged:
        return None
    chapter_name = re.match(rf'{chapter_num}_(.+)\.tagged\.md', tagged.name).group(1)
    pns = load_chapter_pns(tagged)

    # 本库白话
    white = next(WHITE_MD.glob(f'{chapter_num}_*_白话.md'), None)
    white_map = load_white_translation(white) if white else {}

    # hunterhug
    duanyi = next(DUANYI_DIR.glob(f'{chapter_num}_*_段译.txt'), None)
    duanyi_pairs = load_duanyi(duanyi) if duanyi else []
    hunterhug_map = align_hunterhug(pns, duanyi_pairs)

    # 白话史记
    baihua_chapters = load_baihua_by_chapter._cache if hasattr(load_baihua_by_chapter, '_cache') else None
    if baihua_chapters is None:
        baihua_chapters = load_baihua_by_chapter()
        load_baihua_by_chapter._cache = baihua_chapters
    baihua_sentences = baihua_chapters.get(chapter_name, [])
    baihua_map = align_baihua(pns, baihua_sentences)

    records = []
    for pn, source_stripped, _ in pns:
        hh_text, hh_conf = hunterhug_map.get(pn, ('', 0.0))
        bh_text, bh_mode = baihua_map.get(pn, ('', 'none'))
        records.append({
            'pn': pn,
            'source': source_stripped,
            'ours': white_map.get(pn, ''),
            'hunterhug': hh_text,
            'hunterhug_conf': hh_conf,
            'baihua': bh_text,
            'baihua_conf': bh_mode,
        })

    return {
        'chapter': chapter_num,
        'title': chapter_name,
        'n_pns': len(pns),
        'hunterhug_paragraphs': len(duanyi_pairs),
        'baihua_sentences': len(baihua_sentences),
        'records': records,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    if args:
        chapters = [a.zfill(3) for a in args]
    else:
        chapters = sorted({f.name[:3] for f in CHAPTER_MD.glob('*.tagged.md')})

    stats_lines = ['# 外部白话对齐统计', '',
                   '| 章节 | PN | hunterhug 段数 | hunterhug 对齐>0.5 | 白话 句数 |',
                   '|------|-----|---------------|--------------------|----------|']
    for ch in chapters:
        data = align_chapter(ch)
        if data is None:
            print(f'跳过 {ch}（无 tagged.md）')
            continue
        out = OUTPUT_DIR / f'{ch}.json'
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        high_hh = sum(1 for r in data['records'] if r['hunterhug_conf'] >= 0.5)
        stats_lines.append(f"| {ch} {data['title']} | {data['n_pns']} | {data['hunterhug_paragraphs']} | {high_hh}/{data['n_pns']} | {data['baihua_sentences']} |")
    (OUTPUT_DIR / 'STATS.md').write_text('\n'.join(stats_lines))
    print(f'完成：{len(chapters)} 章 → {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
