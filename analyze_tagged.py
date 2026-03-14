#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze tagged markdown files in shiji-kb/chapter_md/
Counts annotated vs unannotated Chinese characters and finds potential new entity types.
"""

import os
import re
import glob
from collections import Counter, defaultdict

# ─── configuration ────────────────────────────────────────────────────────────
TAGGED_DIR = "/home/baojie/work/shiji-kb/chapter_md"
PATTERN = os.path.join(TAGGED_DIR, "*.tagged.md")

# annotation markers  (regex_pattern, label)
# v2.1 format: 〖X content〗 for symmetric types, special brackets for asymmetric
ANNOTATION_TYPES = [
    (r'〖@([^〖〗\n]+)〗', 'Person 人名'),
    (r'〖=([^〖〗\n]+)〗', 'Place 地名'),
    (r'〖;([^〖〗\n]+)〗', 'Official Title 官职'),
    (r'〖%([^〖〗\n]+)〗', 'Time 时间'),
    (r'〖&([^〖〗\n]+)〗', 'Dynasty 朝代'),
    (r'〖\^([^〖〗\n]+)〗', 'Institution 制度'),
    (r'〖~([^〖〗\n]+)〗', 'Ethnic Group 族群'),
    (r'〖\*([^〖〗\n]+)〗', 'Artifact 器物'),
    (r'〖!([^〖〗\n]+)〗', 'Astronomy 天文'),
    (r'〖#([^〖〗\n]+)〗', 'Identity 身份'),
    (r'〖\+([^〖〗\n]+)〗', 'Flora/Fauna 生物'),
    (r"〖'([^〖〗\n]+)〗", 'Feudal State 邦国'),
    (r'〚([^〚〛\n]+)〛', 'Mythology 神话'),
    (r'《([^《》\n]+)》', 'Classical Text 典籍'),
    (r'〈([^〈〉\n]+)〉', 'Ritual 礼仪'),
    (r'【([^【】\n]+)】', 'Law 刑法'),
    (r'〔([^〔〕\n]+)〕', 'Philosophy 思想'),
]

# ─── helpers ──────────────────────────────────────────────────────────────────
def is_chinese_char(ch):
    """Return True for CJK unified ideograph code points."""
    cp = ord(ch)
    return (
        0x4E00 <= cp <= 0x9FFF or   # CJK Unified Ideographs
        0x3400 <= cp <= 0x4DBF or   # CJK Extension A
        0x20000 <= cp <= 0x2A6DF or # CJK Extension B
        0x2A700 <= cp <= 0x2CEAF or # CJK Extension C-F
        0xF900 <= cp <= 0xFAFF      # CJK Compatibility Ideographs
    )

def count_chinese(text):
    return sum(1 for ch in text if is_chinese_char(ch))

def strip_markdown_structure(text):
    """Remove markdown headers, section markers, paragraph numbers like [1.1], etc."""
    # Remove paragraph numbers like [1], [1.1], [0], etc.
    text = re.sub(r'\[\d+(?:\.\d+)*\]', '', text)
    # Remove markdown headers (#, ##, etc.)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    # Remove bullet list markers
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    return text

def extract_annotated_spans(text):
    """
    Extract the contents (inner text) of all annotation spans.
    Returns (list_of_spans_with_type, total_annotated_char_count).
    Each span: (type_label, inner_text)
    """
    spans = []

    for pattern, label in ANNOTATION_TYPES:
        for m in re.finditer(pattern, text):
            inner = m.group(1)
            spans.append((label, inner))

    return spans


# Regex to match ALL v2.1 annotation types (for stripping/masking)
ALL_ANNOT_RE = re.compile(
    r'〖[@=;%&\'^~\*!#\+][^〖〗\n]+?〗'
    r'|〚[^〛\n]+?〛'
    r'|《[^》\n]+?》'
    r'|〈[^〉\n]+?〉'
    r'|【[^】\n]+?】'
    r'|〔[^〕\n]+?〕'
)


def remove_all_annotations(text):
    """
    Remove annotation markers AND their contents from the text.
    Returns the stripped text.
    """
    return ALL_ANNOT_RE.sub('', text)

# ─── candidate entity detection in unannotated text ──────────────────────────

# Classical book/text titles (典籍/书名) – fixed list of known patterns
CLASSICAL_BOOKS_PATTERN = re.compile(
    r'[《〈][^》〉]{1,20}[》〉]'
)

# Numbers + measure words (数量词)
# Classical number chars + measure word chars
NUM_CHARS = '一二三四五六七八九十百千万亿兩'
MEASURE_WORDS = '年月日岁里步尺寸丈仞亩顷斛石升斗钱两匹车乘骑人口户族代世'
NUM_MEASURE_PATTERN = re.compile(
    r'[' + NUM_CHARS + r']{1,4}[' + MEASURE_WORDS + r']'
)

# Direction / cosmological terms
DIRECTION_TERMS = re.compile(r'[东西南北中上下左右前后内外四方八方]方|[东西南北]极|天[下地]|四[海方荒极]')

# Color terms
COLOR_TERMS = re.compile(r'[青赤黄白黑绿紫朱玄丹苍][色衣旗帜车马]?')

# Ritual / ceremony terms (礼仪)
RITUAL_TERMS = re.compile(
    r'(?:封禅|祭祀|宗庙|社稷|郊祀|禘祭|尝祭|享祀|礼乐|冠礼|婚礼|丧礼|祭礼|大礼|典礼|礼制|朝会|朝觐|宾礼|军礼|吉礼|凶礼|嘉礼|宾射|大射|乡射|飨礼|赐爵|策命|册命|告庙|告祭|祷祠|禬祠|郊庙|明堂|辟雍|泮宫|太学)'
)

# Music / sound terms
MUSIC_TERMS = re.compile(
    r'(?:宫商角徵羽|五音|六律|八音|钟磬|鼓瑟|琴瑟|笙竽|[大小]鼓|乐舞|雅乐|颂乐|燕乐|鼓吹|歌舞)'
)

# Law / punishment terms (刑法)
LAW_TERMS = re.compile(
    r'(?:墨劓刖宫大辟|五刑|笞杖徒流死|族诛|夷三族|夷九族|腰斩|车裂|磔|枭首|弃市|斩首|诛夷|连坐|[坐]法|论死|论罪|赦免|大赦|特赦|流放|贬谪|削爵|免官|夺爵|诛戮|诛杀|伏诛|伏法|坐罪|坐诛|坐死|论斩|诛族|夷族)'
)

# Philosophical / virtue concepts
PHIL_TERMS = re.compile(
    r'(?:仁义礼智信|仁政|王道|霸道|德政|德化|德教|天道|天命|人道|道德|礼义|廉耻|忠信|忠孝|孝悌|孝道|孝义|孝弟|名分|正名|大义|大道|圣德|圣王|圣人|贤人|贤德|贤良|明君|明主|暴君|暴政|暴虐)'
)

# Measurement / weight units (度量衡)
MEASUREMENT_UNITS = re.compile(
    r'(?:[一二三四五六七八九十百千万][里步尺寸丈仞亩顷斛石升斗钱两匹车乘骑]|里程|里地|亩地)'
)

# 2–4 char Chinese sequences not caught by annotations
# We'll extract all 2–4 char Chinese n-grams from unannotated text for frequency
NGRAM_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]+')


def get_ngrams(text, n):
    """Get all n-grams from contiguous Chinese character runs."""
    grams = []
    for m in NGRAM_RE.finditer(text):
        run = m.group()
        for i in range(len(run) - n + 1):
            grams.append(run[i:i+n])
    return grams


# ─── main analysis ────────────────────────────────────────────────────────────
def main():
    files = sorted(glob.glob(PATTERN))
    print(f"Found {len(files)} tagged files.\n")

    # Per-annotation-type counters
    annotation_char_counts = defaultdict(int)
    annotation_token_counts = defaultdict(int)

    total_raw_chinese = 0        # Chinese chars in raw text (after md stripping)
    total_annotated_chinese = 0  # Chinese chars inside annotation markers
    total_unannotated_chinese = 0

    # Accumulate unannotated text for n-gram / pattern analysis
    all_unannotated_text = []

    per_file_stats = []

    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, encoding='utf-8') as f:
            raw = f.read()

        # Strip markdown structure markers (headers, bullets, paragraph nums)
        cleaned = strip_markdown_structure(raw)

        # Count raw Chinese chars (before annotation removal)
        raw_cn = count_chinese(cleaned)
        total_raw_chinese += raw_cn

        # Extract annotation contents
        spans = extract_annotated_spans(cleaned)
        file_annotated_cn = 0
        for label, inner in spans:
            cn = count_chinese(inner)
            file_annotated_cn += cn
            annotation_char_counts[label] += cn
            annotation_token_counts[label] += 1

        total_annotated_chinese += file_annotated_cn

        # Remove annotations → unannotated text
        unann = remove_all_annotations(cleaned)
        unann = strip_markdown_structure(unann)  # strip again after removal
        file_unann_cn = count_chinese(unann)
        total_unannotated_chinese += file_unann_cn

        all_unannotated_text.append(unann)

        per_file_stats.append((fname, raw_cn, file_annotated_cn, file_unann_cn))

    unannotated_corpus = '\n'.join(all_unannotated_text)

    # ─── print main stats ────────────────────────────────────────────────────
    print("=" * 70)
    print("OVERALL CHARACTER STATISTICS")
    print("=" * 70)
    print(f"  Total Chinese chars (raw, excl. punctuation/spaces/para-nums): {total_raw_chinese:>10,}")
    print(f"  Chars inside annotation markers (annotated entities):           {total_annotated_chinese:>10,}")
    print(f"  Unannotated Chinese chars:                                       {total_unannotated_chinese:>10,}")
    pct_ann = total_annotated_chinese / total_raw_chinese * 100 if total_raw_chinese else 0
    pct_unann = total_unannotated_chinese / total_raw_chinese * 100 if total_raw_chinese else 0
    print(f"  Annotated   %:  {pct_ann:.2f}%")
    print(f"  Unannotated %:  {pct_unann:.2f}%")
    print()

    print("=" * 70)
    print("ANNOTATION TYPE BREAKDOWN")
    print("=" * 70)
    header = f"  {'Type':<30} {'Tokens':>8} {'CJK Chars':>10} {'% of Ann':>9}"
    print(header)
    print("  " + "-" * 62)
    sorted_types = sorted(annotation_char_counts.items(), key=lambda x: -x[1])
    for label, chars in sorted_types:
        tokens = annotation_token_counts[label]
        pct = chars / total_annotated_chinese * 100 if total_annotated_chinese else 0
        print(f"  {label:<30} {tokens:>8,} {chars:>10,} {pct:>8.2f}%")
    print()

    print("=" * 70)
    print("TOP 30 FILES BY TOTAL CHINESE CHARS")
    print("=" * 70)
    per_file_stats.sort(key=lambda x: -x[1])
    print(f"  {'File':<45} {'Raw':>7} {'Ann':>7} {'Unann':>7} {'Ann%':>6}")
    print("  " + "-" * 76)
    for fname, raw_cn, ann_cn, unann_cn in per_file_stats[:30]:
        pct = ann_cn / raw_cn * 100 if raw_cn else 0
        print(f"  {fname:<45} {raw_cn:>7,} {ann_cn:>7,} {unann_cn:>7,} {pct:>5.1f}%")
    print()

    # ─── unannotated text pattern analysis ───────────────────────────────────
    print("=" * 70)
    print("POTENTIAL NEW ENTITY TYPES – PATTERN ANALYSIS")
    print("=" * 70)

    def find_pattern_freqs(pattern, corpus, label, top_n=30):
        matches = pattern.findall(corpus)
        counter = Counter(matches)
        print(f"\n  [{label}]  total matches: {len(matches)},  unique: {len(counter)}")
        print(f"  {'Rank':<5} {'Term':<20} {'Count':>7}")
        print("  " + "-" * 36)
        for rank, (term, cnt) in enumerate(counter.most_common(top_n), 1):
            print(f"  {rank:<5} {term:<20} {cnt:>7,}")

    find_pattern_freqs(CLASSICAL_BOOKS_PATTERN, unannotated_corpus,
                       "CLASSICAL BOOKS/TEXTS 典籍书名", top_n=40)
    find_pattern_freqs(NUM_MEASURE_PATTERN, unannotated_corpus,
                       "NUMBERS + MEASURE WORDS 数量词", top_n=40)
    find_pattern_freqs(DIRECTION_TERMS, unannotated_corpus,
                       "DIRECTION/COSMOLOGICAL 方位天文", top_n=20)
    find_pattern_freqs(COLOR_TERMS, unannotated_corpus,
                       "COLOR TERMS 颜色", top_n=20)
    find_pattern_freqs(RITUAL_TERMS, unannotated_corpus,
                       "RITUAL/CEREMONY TERMS 礼仪", top_n=30)
    find_pattern_freqs(MUSIC_TERMS, unannotated_corpus,
                       "MUSIC/SOUND TERMS 音乐", top_n=20)
    find_pattern_freqs(LAW_TERMS, unannotated_corpus,
                       "LAW/PUNISHMENT TERMS 刑法", top_n=30)
    find_pattern_freqs(PHIL_TERMS, unannotated_corpus,
                       "PHILOSOPHICAL CONCEPTS 思想", top_n=30)

    # ─── high-frequency 2-gram and 3-gram analysis ───────────────────────────
    print("\n" + "=" * 70)
    print("HIGH-FREQUENCY N-GRAMS IN UNANNOTATED TEXT")
    print("=" * 70)

    bigrams = Counter(get_ngrams(unannotated_corpus, 2))
    trigrams = Counter(get_ngrams(unannotated_corpus, 3))
    fourgrams = Counter(get_ngrams(unannotated_corpus, 4))

    # Filter out trivial/stop-word bigrams
    # Very common classical stop chars
    STOP_CHARS = set('之乎者也而以为其於所者不与及则於於从如若此彼何曰於')

    def is_content_ngram(gram):
        # Skip if ALL chars are stop chars
        return not all(ch in STOP_CHARS for ch in gram)

    print(f"\n  [BIGRAMS 二字词]  top 60")
    print(f"  {'Rank':<5} {'Term':<12} {'Count':>7}   {'Rank':<5} {'Term':<12} {'Count':>7}")
    print("  " + "-" * 52)
    content_bigrams = [(g, c) for g, c in bigrams.most_common(300) if is_content_ngram(g)][:60]
    # print two columns
    for i in range(0, len(content_bigrams), 2):
        left = content_bigrams[i]
        right = content_bigrams[i+1] if i+1 < len(content_bigrams) else ('', 0)
        print(f"  {i+1:<5} {left[0]:<12} {left[1]:>7,}   {i+2:<5} {right[0]:<12} {right[1]:>7,}")

    print(f"\n  [TRIGRAMS 三字词]  top 50")
    print(f"  {'Rank':<5} {'Term':<16} {'Count':>7}")
    print("  " + "-" * 32)
    content_trigrams = [(g, c) for g, c in trigrams.most_common(200) if is_content_ngram(g)][:50]
    for rank, (gram, cnt) in enumerate(content_trigrams, 1):
        print(f"  {rank:<5} {gram:<16} {cnt:>7,}")

    print(f"\n  [4-GRAMS 四字词]  top 40")
    print(f"  {'Rank':<5} {'Term':<20} {'Count':>7}")
    print("  " + "-" * 36)
    content_4grams = [(g, c) for g, c in fourgrams.most_common(200) if is_content_ngram(g)][:40]
    for rank, (gram, cnt) in enumerate(content_4grams, 1):
        print(f"  {rank:<5} {gram:<20} {cnt:>7,}")

    # ─── summary recommendations ─────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("RECOMMENDED NEW ENTITY TYPES TO ANNOTATE")
    print("=" * 70)
    recs = [
        ("典籍/书名 Classical Texts",
         "High-frequency book titles in 《》brackets (《诗》《书》《春秋》《易》etc.)"),
        ("数量词 Quantity+Measure Phrases",
         "Number + measure word patterns (三年、百里、千人 etc.)"),
        ("礼仪 Ritual/Ceremony Terms",
         f"Found {len(RITUAL_TERMS.findall(unannotated_corpus))} instances: 封禅、祭祀、社稷、宗庙、郊祀 etc."),
        ("刑法 Law/Punishment Terms",
         f"Found {len(LAW_TERMS.findall(unannotated_corpus))} instances: 五刑、族诛、大辟、腰斩、弃市 etc."),
        ("思想 Philosophical Concepts",
         f"Found {len(PHIL_TERMS.findall(unannotated_corpus))} instances: 仁义、王道、天命、德政 etc."),
        ("音乐 Music Terms",
         f"Found {len(MUSIC_TERMS.findall(unannotated_corpus))} instances: 五音、六律、钟磬、琴瑟 etc."),
        ("颜色 Color Terms",
         f"Found {len(COLOR_TERMS.findall(unannotated_corpus))} instances: 青赤黄白黑 etc."),
    ]
    for i, (cat, desc) in enumerate(recs, 1):
        print(f"\n  {i}. {cat}")
        print(f"     {desc}")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == '__main__':
    main()
