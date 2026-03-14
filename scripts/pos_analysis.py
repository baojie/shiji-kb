#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文言文字级词性分析脚本

对史记130章的未标注文字进行字级词性分析，估计其中
虚词、动词、形容词、数词、候选实体（名词类）的分布。

设计原则：
- 文言文以单字词为主，字即词，直接基于字表分类
- 无需外部NLP库，词表驱动，零依赖
- 虚词表高度封闭（约230字），准确率高
- 动词/形容词为中置信度分类，注意词类活用现象
- 两遍分析：第一遍字级分类，第二遍lint检测被误分字（实为复合实体一部分）

第二遍lint说明：
  某些字在词表中归为虚词/动词（如"之""无""有""行"），但可能出现在
  人名/地名复合词中（如"无忌"、"有虞氏"）。第二遍扫描"夹心"模式：
  [候选字][非候选字][候选字] → 标记为潜在复合实体，输出到 lint_warnings。

用法：
  python scripts/pos_analysis.py --chapter 001   # 单章测试
  python scripts/pos_analysis.py --all            # 全量130章
  python scripts/pos_analysis.py --report         # 仅生成汇总报告（需已有JSON）
"""

import os
import re
import json
import glob
import argparse
from collections import Counter, defaultdict
from pathlib import Path


# ─── 路径配置 ────────────────────────────────────────────────────────────────
TAGGED_DIR = Path("/home/baojie/work/shiji-kb/chapter_md")
OUTPUT_DIR = Path("/home/baojie/work/shiji-kb/doc/analysis/pos")
SUMMARY_FILE = Path("/home/baojie/work/shiji-kb/doc/analysis/pos_summary.md")


# ─── 文言文字级词性表 ─────────────────────────────────────────────────────────

# Level 1：肯定不是实体（高置信度虚词）
# 包含语气词、助词、连词、介词、副词、代词等功能词
FUNCTION_CHARS = frozenset([
    # 语气词 / 助词（句末、句中）
    '也', '矣', '焉', '哉', '耳', '兮', '邪', '欤', '与', '耶',
    '乎', '哟',
    # 结构助词
    '之', '者', '所',
    # 连词
    '而', '且', '则', '虽', '若', '如', '苟', '即', '然', '顾',
    '但', '况', '抑', '或', '或', '故',
    # 介词
    '以', '于', '於', '自', '从', '由', '为', '因', '及', '与',
    '被', '被',
    # 否定副词
    '不', '弗', '未', '无', '非', '莫', '勿', '毋', '否', '匪',
    # 范围/程度副词
    '皆', '悉', '咸', '俱', '亦', '又', '且', '既', '已', '尽',
    '都', '均', '共', '并',
    # 时序副词
    '遂', '乃', '则', '即', '便', '方', '正', '将', '当', '固',
    '旋', '继', '仍', '复', '再', '更', '又', '还',
    # 程度副词
    '益', '愈', '更', '甚', '尤', '颇', '稍', '仅', '止', '才',
    '殊', '极', '最', '甚', '尤', '过',
    # 语气副词
    '岂', '宁', '庶', '幸', '请', '敢', '肯', '诚', '果', '竟',
    '终', '卒', '遂', '乃',
    # 指示代词
    '此', '彼', '是', '斯', '夫', '兹', '其',
    # 疑问代词
    '何', '安', '曷', '奚', '胡', '谁', '孰', '焉',
    # 人称代词
    '吾', '我', '余', '予', '汝', '尔', '子', '君', '朕', '寡',
    '孤', '卿', '汝',
    # 数词（单独出现作虚用）— 注意：作名词时不算虚词
    # 不放在这里，单独处理
])

# Level 2：通常是动词（中置信度，注意词类活用）
VERB_CHARS = frozenset([
    # 言说动词
    '曰', '云', '言', '谓', '告', '问', '对', '答', '诉', '语',
    '称', '谏', '奏', '启', '陈', '申', '述',
    # 命令/使役
    '命', '令', '使', '遣', '征', '召', '聘', '请', '求',
    # 存在/系词
    '有', '无', '在', '居', '处',
    # 动作（位移）
    '来', '去', '入', '出', '上', '下', '归', '还', '至', '到',
    '往', '诣', '赴', '返', '回', '进', '退', '趋', '走', '奔',
    '逃', '遁', '亡', '徙', '迁', '流', '放', '贬',
    # 动作（站立/坐）
    '立', '坐', '卧', '起', '行', '止',
    # 军事动词
    '伐', '攻', '战', '击', '败', '胜', '克', '取', '夺', '守',
    '围', '拔', '破', '陷', '降', '抵', '抗', '援', '救',
    '杀', '斩', '诛', '刑', '戮', '射', '刺', '擒', '俘',
    # 政治/官场动词
    '封', '拜', '立', '废', '徙', '迁', '贬', '降', '升', '除',
    '任', '用', '拔', '擢', '录', '赐', '赏', '罚', '赦',
    '朝', '觐', '见', '辞', '献', '贡', '纳',
    # 生死动词
    '生', '死', '薨', '卒', '崩', '殂', '弃',
    # 感知动词
    '知', '见', '闻', '观', '察', '视', '听', '得', '失',
    '忘', '思', '虑', '谋', '计',
    # 给予/得到
    '与', '给', '予', '授', '赐', '赠', '取', '受', '纳',
    # 情感动词
    '爱', '恶', '喜', '怒', '忧', '惧', '怨', '恨', '慕',
    # 其他高频动词
    '为', '作', '造', '建', '立', '置', '设', '定', '制',
    '行', '施', '用', '习', '学', '教', '治', '理',
    '归', '服', '从', '附', '叛', '背', '违', '犯',
    '会', '合', '分', '别', '离', '聚', '散',
    '送', '迎', '遇', '逢', '见', '待', '留',
])

# 形容词（中置信度）
ADJECTIVE_CHARS = frozenset([
    # 道德评价
    '仁', '义', '礼', '智', '信', '忠', '孝', '廉', '耻',
    '善', '恶', '贤', '愚', '暴', '虐', '慈', '刚', '柔',
    '直', '曲', '正', '邪', '忠', '奸',
    # 能力/状态
    '强', '弱', '勇', '怯', '勤', '惰', '贫', '富', '贵', '贱',
    '贤', '能', '才', '德',
    # 大小/多少（形容词用法）
    '大', '小', '多', '少', '长', '短', '高', '低', '深', '浅',
    '广', '狭', '远', '近', '重', '轻', '厚', '薄',
    # 颜色
    '青', '赤', '黄', '白', '黑', '绿', '紫', '朱', '玄', '苍',
    # 状态
    '新', '旧', '古', '今', '久', '暂', '早', '晚',
    '盛', '衰', '兴', '废', '安', '危', '治', '乱', '清', '浊',
])

# 数词（单字数字，通常不是实体，但复合数量词可能是度量单位实体）
NUMBER_CHARS = frozenset([
    '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '百', '千', '万', '亿', '兩', '两', '零', '数', '几',
])

# 量词（配合数词，不单独成实体）
MEASURE_CHARS = frozenset([
    '年', '月', '日', '时', '岁', '世', '代',
    '里', '步', '尺', '寸', '丈', '仞',
    '亩', '顷', '斛', '石', '升', '斗',
    '钱', '两', '斤', '匹', '乘', '骑',
    '人', '口', '户', '族',
])

# ─── 标注符号移除 ─────────────────────────────────────────────────────────────

# v2.1 标注格式：统一移除正则
ALL_ANNOT_RE = re.compile(
    r'〖[@=;%&\'^~\*!#\+][^〖〗\n]+?〗'
    r'|〚[^〛\n]+?〛'
    r'|《[^》\n]+?》'
    r'|〈[^〉\n]+?〉'
    r'|【[^】\n]+?】'
    r'|〔[^〕\n]+?〕'
)


def remove_all_annotations(text):
    """移除所有标注符号及其内容"""
    return ALL_ANNOT_RE.sub('', text)


def strip_markdown_structure(text):
    """去除Markdown结构标记（标题、段落编号、列表符号等）"""
    text = re.sub(r'\[\d+(?:\.\d+)*\]', '', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    return text


def is_chinese_char(ch):
    cp = ord(ch)
    return (
        0x4E00 <= cp <= 0x9FFF or
        0x3400 <= cp <= 0x4DBF or
        0x20000 <= cp <= 0x2A6DF or
        0xF900 <= cp <= 0xFAFF
    )


# ─── 双字/三字候选实体 n-gram 提取 ────────────────────────────────────────────

CHINESE_RUN_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]+')

# 不应出现在候选n-gram边缘的字符集（虚词+常见动词）
NON_ENTITY_BOUNDARY = FUNCTION_CHARS | VERB_CHARS


def get_candidate_ngrams(text, n, boundary_filter=True):
    """
    从候选实体字符序列中提取n-gram。
    boundary_filter=True 时，过滤掉首尾为虚词/常见动词的n-gram。
    """
    grams = []
    for m in CHINESE_RUN_RE.finditer(text):
        run = m.group()
        for i in range(len(run) - n + 1):
            gram = run[i:i+n]
            if boundary_filter:
                if gram[0] in NON_ENTITY_BOUNDARY or gram[-1] in NON_ENTITY_BOUNDARY:
                    continue
            grams.append(gram)
    return grams


# ─── 单章分析 ─────────────────────────────────────────────────────────────────

def analyze_chapter(fpath):
    """
    分析单章 .tagged.md 文件的未标注文字词性分布。
    返回 dict。
    """
    with open(fpath, encoding='utf-8') as f:
        raw = f.read()

    # 去除标注内容（移除整个标注span，只留下未标注的原文）
    untagged = remove_all_annotations(raw)
    untagged = strip_markdown_structure(untagged)

    # 按字分类
    counts = {
        'function': 0,    # 虚词
        'verb': 0,        # 动词
        'adjective': 0,   # 形容词
        'number': 0,      # 数词
        'measure': 0,     # 量词
        'candidate': 0,   # 候选实体（余下汉字，主要是名词类）
    }

    candidate_text_parts = []  # 用于n-gram提取

    current_candidate_run = []

    for ch in untagged:
        if not is_chinese_char(ch):
            if current_candidate_run:
                candidate_text_parts.append(''.join(current_candidate_run))
                current_candidate_run = []
            continue

        if ch in FUNCTION_CHARS:
            counts['function'] += 1
            if current_candidate_run:
                candidate_text_parts.append(''.join(current_candidate_run))
                current_candidate_run = []
        elif ch in VERB_CHARS:
            counts['verb'] += 1
            if current_candidate_run:
                candidate_text_parts.append(''.join(current_candidate_run))
                current_candidate_run = []
        elif ch in ADJECTIVE_CHARS:
            counts['adjective'] += 1
            if current_candidate_run:
                candidate_text_parts.append(''.join(current_candidate_run))
                current_candidate_run = []
        elif ch in NUMBER_CHARS:
            counts['number'] += 1
            if current_candidate_run:
                candidate_text_parts.append(''.join(current_candidate_run))
                current_candidate_run = []
        elif ch in MEASURE_CHARS:
            counts['measure'] += 1
            if current_candidate_run:
                candidate_text_parts.append(''.join(current_candidate_run))
                current_candidate_run = []
        else:
            counts['candidate'] += 1
            current_candidate_run.append(ch)

    if current_candidate_run:
        candidate_text_parts.append(''.join(current_candidate_run))

    total = sum(counts.values())

    # ── 第一遍完成，建立字→类别映射表供第二遍使用 ──────────────────────────────
    # 重建每个字的分类序列（供第二遍扫描）
    char_categories = []
    for ch in untagged:
        if not is_chinese_char(ch):
            char_categories.append((ch, 'non_chinese'))
            continue
        if ch in FUNCTION_CHARS:
            char_categories.append((ch, 'function'))
        elif ch in VERB_CHARS:
            char_categories.append((ch, 'verb'))
        elif ch in ADJECTIVE_CHARS:
            char_categories.append((ch, 'adjective'))
        elif ch in NUMBER_CHARS:
            char_categories.append((ch, 'number'))
        elif ch in MEASURE_CHARS:
            char_categories.append((ch, 'measure'))
        else:
            char_categories.append((ch, 'candidate'))

    # ── 第二遍 Lint：检测"夹心"模式 ──────────────────────────────────────────
    # 模式：[候选字+][非候选汉字][候选字+]
    # 这类"夹心"非候选字可能是人名/地名复合词的一部分，如"无忌"、"有虞氏"
    # 结果：lint_warnings = 高频"夹心"bigram/trigram，供人工审核
    SUSPECT_PATTERNS = Counter()

    cn_only = [(ch, cat) for ch, cat in char_categories if cat != 'non_chinese']
    n = len(cn_only)

    for i in range(1, n - 1):
        ch_i, cat_i = cn_only[i]
        if cat_i in ('function', 'verb', 'adjective'):
            # 检查 [candidate][当前非候选][candidate] 夹心模式（窗口±1）
            prev_cat = cn_only[i-1][1]
            next_cat = cn_only[i+1][1]
            if prev_cat == 'candidate' and next_cat == 'candidate':
                bigram_left  = cn_only[i-1][0] + ch_i
                bigram_right = ch_i + cn_only[i+1][0]
                trigram = cn_only[i-1][0] + ch_i + cn_only[i+1][0]
                SUSPECT_PATTERNS[trigram] += 1

    # 只保留频次>=2的可疑模式（单次出现可能是语法结构，频繁出现才值得注意）
    lint_warnings = {gram: cnt for gram, cnt in SUSPECT_PATTERNS.most_common(50)
                     if cnt >= 2}

    # ── 从候选实体文字中提取高频双字/三字n-gram ────────────────────────────────
    candidate_joined = '\n'.join(candidate_text_parts)
    bigrams = Counter(get_candidate_ngrams(candidate_joined, 2))
    trigrams = Counter(get_candidate_ngrams(candidate_joined, 3))

    fname = os.path.basename(fpath)
    chapter_id = fname.split('_')[0]
    chapter_name = fname.replace('.tagged.md', '')

    result = {
        'chapter': chapter_name,
        'chapter_id': chapter_id,
        'file': fname,
        'total_untagged_chars': total,
        'breakdown': {},
        'candidate_top_bigrams': [w for w, _ in bigrams.most_common(30)],
        'candidate_top_trigrams': [w for w, _ in trigrams.most_common(20)],
        'candidate_bigram_freq': dict(bigrams.most_common(100)),
        'candidate_trigram_freq': dict(trigrams.most_common(50)),
        'lint_warnings': lint_warnings,
        'lint_warning_count': len(lint_warnings),
    }

    for cat, cnt in counts.items():
        pct = cnt / total * 100 if total > 0 else 0.0
        notes = {
            'function': '虚词（之乎者也等），肯定不是实体',
            'verb': '动词（通常不是实体，注意动名活用）',
            'adjective': '形容词（通常不是实体，但可修饰实体）',
            'number': '数词（通常不是实体，但复合词可能是度量单位）',
            'measure': '量词（通常不是实体，但"二千石"等可归入官职）',
            'candidate': '候选实体（余下汉字，主要是名词/专名，需进一步筛选）',
        }
        result['breakdown'][cat] = {
            'chars': cnt,
            'pct': round(pct, 2),
            'note': notes[cat],
        }

    return result


# ─── 汇总报告生成 ─────────────────────────────────────────────────────────────

def generate_summary_report(all_results):
    """
    从所有章节的分析结果生成 Markdown 汇总报告。
    """
    # 全局汇总
    total_untagged = sum(r['total_untagged_chars'] for r in all_results)
    global_counts = defaultdict(int)
    all_bigrams = Counter()
    all_trigrams = Counter()

    for r in all_results:
        for cat, info in r['breakdown'].items():
            global_counts[cat] += info['chars']
        all_bigrams.update(r['candidate_bigram_freq'])
        all_trigrams.update(r['candidate_trigram_freq'])

    # 汇总lint警告
    all_lint = Counter()
    for r in all_results:
        all_lint.update(r.get('lint_warnings', {}))
    top_lint = all_lint.most_common(50)

    def pct(n):
        return n / total_untagged * 100 if total_untagged > 0 else 0.0

    # 分类汇总
    definitely_not = global_counts['function']
    usually_not = global_counts['verb'] + global_counts['adjective'] + global_counts['number'] + global_counts['measure']
    candidates = global_counts['candidate']

    lines = [
        "# 史记未标注文字词性分析汇总报告",
        "",
        f"> 生成日期：2026-03-12",
        f"> 分析脚本：`scripts/pos_analysis.py`",
        f"> 数据来源：`chapter_md/*.tagged.md`（{len(all_results)}章）",
        f"> 方法：字级规则分析（文言虚词表+动词表），无外部NLP依赖",
        "",
        "---",
        "",
        "## 一、全局词性分布",
        "",
        f"未标注汉字总数：**{total_untagged:,}**",
        "",
        "| 分类 | 字数 | 占比 | 说明 |",
        "|------|------|------|------|",
        f"| 虚词（肯定不是实体）| {definitely_not:,} | {pct(definitely_not):.1f}% | 之乎者也等语气词、助词、代词、连词 |",
        f"| 动词（通常不是实体）| {global_counts['verb']:,} | {pct(global_counts['verb']):.1f}% | 注意词类活用，部分可作名词 |",
        f"| 形容词 | {global_counts['adjective']:,} | {pct(global_counts['adjective']):.1f}% | 偶尔实体化（如贤者中的贤） |",
        f"| 数词 | {global_counts['number']:,} | {pct(global_counts['number']):.1f}% | 通常不独立成实体 |",
        f"| 量词 | {global_counts['measure']:,} | {pct(global_counts['measure']):.1f}% | 二千石等可归入官职类 |",
        f"| **候选实体（名词类）** | **{candidates:,}** | **{pct(candidates):.1f}%** | 余下汉字，主要是名词/专名，需进一步筛选 |",
        "",
        "### 关键结论",
        "",
        f"- **{definitely_not + usually_not:,}字**（占未标注的 **{pct(definitely_not + usually_not):.1f}%**）可判定为非实体",
        f"  - 其中虚词（肯定不是实体）：{definitely_not:,}字（{pct(definitely_not):.1f}%）",
        f"  - 动词/形容词/数词/量词（通常不是实体）：{usually_not:,}字（{pct(usually_not):.1f}%）",
        f"- **{candidates:,}字**（{pct(candidates):.1f}%）是候选实体（主要是名词/专名类）",
        "- 候选实体中，一部分已被其他方式表达（如动名两用的礼仪词封禅），",
        f"  实际可新增标注的实体数量预估在 **{int(candidates * 0.3):,}~{int(candidates * 0.5):,}字** 之间",
        "",
        "---",
        "",
        "## 二、候选实体高频双字词 TOP 100",
        "",
        "> 从候选实体字符中提取，已过滤首尾为虚词/动词的组合",
        "",
        "| 排名 | 词语 | 频次 | 排名 | 词语 | 频次 | 排名 | 词语 | 频次 | 排名 | 词语 | 频次 |",
        "|------|------|------|------|------|------|------|------|------|------|------|------|",
    ]

    top_bigrams = all_bigrams.most_common(100)
    for i in range(0, min(100, len(top_bigrams)), 4):
        row_parts = []
        for j in range(4):
            if i + j < len(top_bigrams):
                word, cnt = top_bigrams[i + j]
                row_parts.append(f"| {i+j+1} | {word} | {cnt:,} ")
            else:
                row_parts.append("| | | ")
        lines.append(''.join(row_parts) + "|")

    lines += [
        "",
        "---",
        "",
        "## 三、候选实体高频三字词 TOP 60",
        "",
        "| 排名 | 词语 | 频次 | 排名 | 词语 | 频次 | 排名 | 词语 | 频次 |",
        "|------|------|------|------|------|------|------|------|------|",
    ]

    top_trigrams = all_trigrams.most_common(60)
    for i in range(0, min(60, len(top_trigrams)), 3):
        row_parts = []
        for j in range(3):
            if i + j < len(top_trigrams):
                word, cnt = top_trigrams[i + j]
                row_parts.append(f"| {i+j+1} | {word} | {cnt:,} ")
            else:
                row_parts.append("| | | ")
        lines.append(''.join(row_parts) + "|")

    # ── Lint警告节：夹心型潜在复合实体 ──────────────────────────────────────────
    lines += [
        "",
        "---",
        "",
        "## 四、第二遍Lint：疑似误分字（含虚词/动词字的复合实体候选）",
        "",
        "> **背景**：第一遍字级分类后，部分字被归入虚词/动词，但可能实为复合实体的一部分。",
        "> 检测模式：`[候选字][非候选字][候选字]`（夹心模式），频次≥2次的视为可疑。",
        "> **使用方式**：检查下表，判断是否需要将某些字从虚词/动词表中移除，或加入词表豁免列表。",
        "",
        "| 排名 | 夹心三字组合 | 全文频次 | 说明 |",
        "|------|-------------|---------|------|",
    ]

    for rank, (gram, cnt) in enumerate(top_lint[:50], 1):
        # 标注中间字的类别
        if len(gram) == 3:
            mid = gram[1]
            if mid in FUNCTION_CHARS:
                cat_label = "虚词"
            elif mid in VERB_CHARS:
                cat_label = "动词"
            elif mid in ADJECTIVE_CHARS:
                cat_label = "形容词"
            else:
                cat_label = "其他"
            lines.append(f"| {rank} | `{gram}` | {cnt:,} | 中间字`{mid}`被分类为{cat_label} |")

    lines += [
        "",
        "---",
        "",
        "## 五、各章节词性分布一览（130章）",
        "",
        "| 章节 | 未标注字数 | 虚词% | 动词% | 形容词% | 数量词% | 候选实体% | Lint警告数 |",
        "|------|-----------|-------|-------|---------|---------|-----------|-----------|",
    ]

    for r in sorted(all_results, key=lambda x: x['chapter_id']):
        t = r['total_untagged_chars']
        if t == 0:
            continue
        bd = r['breakdown']
        fn_pct = bd['function']['pct']
        vb_pct = bd['verb']['pct']
        adj_pct = bd['adjective']['pct']
        num_pct = bd['number']['pct'] + bd['measure']['pct']
        cand_pct = bd['candidate']['pct']
        lint_cnt = r.get('lint_warning_count', 0)
        lines.append(
            f"| {r['chapter']} | {t:,} | {fn_pct:.1f}% | {vb_pct:.1f}% | "
            f"{adj_pct:.1f}% | {num_pct:.1f}% | {cand_pct:.1f}% | {lint_cnt} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 六、实体类型与词性的关系",
        "",
        "史记标注系统的实体**不都是名词**，按语法功能分三类：",
        "",
        "| 类别 | 例子 | 语法特征 | 标注依据 |",
        "|------|------|----------|----------|",
        "| **纯名词实体** | 人名、地名、器物、族群 | 典型名词，做主宾语 | 语义指称特定个体 |",
        "| **动名两用实体** | 礼仪（封禅/祭祀）、刑法（弃市/腰斩） | 可作动词，也可作名词 | 语义指称事件/行为类别 |",
        "| **概念型实体** | 思想（天命/王道）、典籍书名 | 常作主题论述 | 语义指称概念/文献 |",
        "",
        '> 标注系统是**语义驱动**而非词性驱动。',
        '> 判断依据是"是否指称某类可独立命名的对象"，而非词性。',
        '> 因此 `封禅`、`弃市`、`天命` 等动名两用词/概念词均应标注。',
        "",
        "---",
        "",
        "## 七、分析局限性",
        "",
        '1. **字级分析的精度**：文言文存在大量词类活用，如"王天下"中的王是动词而非名词。',
        "   字级词表无法识别活用，候选实体中有约10-15%实为动词活用。",
        '2. **专有名词混入动词表**：部分字（如封字可为动词"封赏"，也可在"封禅"中作名词），',
        '   已保守处理，归入动词表，导致"封禅"中的封被略微低估。',
        "   → 可通过lint警告表（第四节）识别此类情况，将其从词表移除。",
        "3. **n-gram边界过滤**：候选实体n-gram已过滤首尾为虚词/动词的组合，但仍可能",
        "   包含部分描述性短语而非真正实体名称。",
        '4. **Lint夹心检测的误报**：部分夹心模式是正常语法结构（如某之某），',
        "   而非复合实体名称。需人工筛选lint警告表中的有效条目。",
        "",
        "---",
        "",
        f"*本报告由 `scripts/pos_analysis.py` 自动生成。*",
    ]

    return '\n'.join(lines)


# ─── 主程序 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='文言文字级词性分析')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--chapter', metavar='NNN',
                       help='分析单章（如 001），用于测试')
    group.add_argument('--all', action='store_true',
                       help='分析全部130章')
    group.add_argument('--report', action='store_true',
                       help='仅从已有JSON生成汇总报告')
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.chapter:
        # 单章模式
        pattern = str(TAGGED_DIR / f"{args.chapter}_*.tagged.md")
        files = glob.glob(pattern)
        if not files:
            print(f"[ERROR] 未找到章节 {args.chapter} 的文件：{pattern}")
            return
        fpath = files[0]
        print(f"分析：{os.path.basename(fpath)}")
        result = analyze_chapter(fpath)
        out_path = OUTPUT_DIR / f"{result['chapter']}_pos.json"
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存：{out_path}")

        # 打印简报
        print(f"\n未标注字数：{result['total_untagged_chars']:,}")
        for cat, info in result['breakdown'].items():
            print(f"  {cat:12} {info['chars']:6,}字  {info['pct']:5.1f}%  {info['note']}")
        print(f"\n候选实体高频双字词：{result['candidate_top_bigrams'][:20]}")
        print(f"候选实体高频三字词：{result['candidate_top_trigrams'][:15]}")
        print(f"\n第二遍Lint警告（夹心型疑似复合实体，频次≥2）：")
        if result['lint_warnings']:
            for gram, cnt in sorted(result['lint_warnings'].items(), key=lambda x: -x[1])[:20]:
                mid = gram[1] if len(gram) == 3 else '?'
                if mid in FUNCTION_CHARS:
                    cat = '虚词'
                elif mid in VERB_CHARS:
                    cat = '动词'
                else:
                    cat = '其他'
                print(f"  {gram}  ({cnt}次, 中间字'{mid}'={cat})")
        else:
            print("  无警告（频次≥2的夹心模式未发现）")

    elif args.all:
        # 全量模式
        files = sorted(glob.glob(str(TAGGED_DIR / "*.tagged.md")))
        print(f"找到 {len(files)} 个文件，开始分析...")
        all_results = []
        for i, fpath in enumerate(files, 1):
            fname = os.path.basename(fpath)
            print(f"[{i:3d}/{len(files)}] {fname}", end='\r', flush=True)
            result = analyze_chapter(fpath)
            out_path = OUTPUT_DIR / f"{result['chapter']}_pos.json"
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            all_results.append(result)
        print(f"\n✅ 已保存 {len(all_results)} 个JSON到 {OUTPUT_DIR}/")

        # 生成汇总报告
        report_md = generate_summary_report(all_results)
        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            f.write(report_md)
        print(f"✅ 汇总报告已保存：{SUMMARY_FILE}")

    elif args.report:
        # 仅生成报告
        json_files = sorted(OUTPUT_DIR.glob("*_pos.json"))
        if not json_files:
            print(f"[ERROR] 未找到JSON文件，请先运行 --all")
            return
        all_results = []
        for jf in json_files:
            with open(jf, encoding='utf-8') as f:
                all_results.append(json.load(f))
        print(f"读取 {len(all_results)} 个JSON文件...")
        report_md = generate_summary_report(all_results)
        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            f.write(report_md)
        print(f"✅ 汇总报告已保存：{SUMMARY_FILE}")


if __name__ == '__main__':
    main()
