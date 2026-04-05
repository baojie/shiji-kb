#!/usr/bin/env python3
"""
深度挖掘隐藏的韵文（赞、诗歌）

检查33篇尚未发现赞的章节，使用verse_score算法识别可能的韵文段落。
注意：诗歌不限于4字句，4-7字句都可能，连续多句相似长度即为疑似韵文。
"""

import re
import json
from pathlib import Path
from collections import defaultdict


def clean_text(text):
    """移除标注符号，获取纯文本"""
    # 移除段落编号 [N]
    text = re.sub(r'\[\d+(?:\.\d+)?\]\s*', '', text)

    # 移除实体标注 〖TYPE text〗，保留内部文本
    # 支持消歧语法 〖TYPE 显示名|规范名〗
    def replace_entity(match):
        content = match.group(1)
        # 去除TYPE标记（第一个字符）
        content = content[1:]
        # 处理消歧语法
        if '|' in content:
            # 保留显示名
            content = content.split('|')[0]
        return content

    text = re.sub(r'〖([^〗]+)〗', replace_entity, text)

    # 移除动词标注 ⟦TYPE⟧
    def replace_verb(match):
        content = match.group(1)
        # 去除TYPE标记（第一个字符）
        return content[1:]

    text = re.sub(r'⟦([^⟧]+)⟧', replace_verb, text)

    return text.strip()


def split_by_punctuation(text):
    """按标点符号拆分成句子"""
    # 中文标点：，。：；！？
    segments = re.split(r'[，。：；！？]', text)
    return [s.strip() for s in segments if s.strip()]


def verse_score(line):
    """
    计算一行文本的韵文得分（0-1）

    参数:
        line: 一行文本（可能包含标注符号）

    返回:
        float: 0-1之间的得分，>0.6表示韵文可能性高
    """
    clean = clean_text(line)
    if not clean:
        return 0.0

    # 按标点拆分成句子
    segments = split_by_punctuation(clean)
    if not segments:
        return 0.0

    # 计算每个句子的字数
    lengths = [len(s) for s in segments]
    total = len(lengths)

    # 计算各种长度的句子占比
    four_char = sum(1 for l in lengths if l == 4)
    near_four = sum(1 for l in lengths if 3 <= l <= 5)  # 3-5字
    mid_range = sum(1 for l in lengths if 4 <= l <= 7)  # 4-7字（诗歌范围）

    avg_length = sum(lengths) / total if total > 0 else 0

    # 评分规则
    # 1. 4字句占比 > 50%：强韵文（赞）
    if four_char / total > 0.5:
        return 0.95

    # 2. 3-5字句占比 > 70%：中强韵文
    if near_four / total > 0.7:
        return 0.8

    # 3. 4-7字句占比 > 70%：诗歌可能
    if mid_range / total > 0.7:
        return 0.7

    # 4. 平均句长6-8字，且方差小：五言七言诗
    if 6 <= avg_length <= 8:
        # 计算方差：句长一致性
        variance = sum((l - avg_length) ** 2 for l in lengths) / total
        if variance < 2.0:  # 方差小说明句长整齐
            return 0.75

    # 5. 平均句长 > 10字：散文可能性高
    if avg_length > 10:
        return 0.1

    # 6. 平均句长 7-9 字，中等可能
    if 7 <= avg_length <= 9:
        return 0.5

    # 默认：中低可能
    return 0.3


def analyze_block(lines):
    """
    分析一组连续行的韵文得分

    参数:
        lines: 连续的文本行列表

    返回:
        tuple: (avg_score, char_distribution)
    """
    if not lines:
        return 0.0, {}

    scores = [verse_score(line) for line in lines]
    avg_score = sum(scores) / len(scores)

    # 统计字数分布
    char_counts = defaultdict(int)
    for line in lines:
        clean = clean_text(line)
        segments = split_by_punctuation(clean)
        for seg in segments:
            char_counts[len(seg)] += 1

    return avg_score, dict(char_counts)


def extract_potential_yunwen(chapter_file):
    """
    从章节文件中提取潜在的韵文段落

    返回:
        list: [(start_line, end_line, score, text, char_dist), ...]
    """
    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按行分割
    lines = content.split('\n')

    results = []

    # 滑动窗口：寻找连续3行以上的韵文
    min_lines = 3
    max_lines = 20

    i = 0
    while i < len(lines):
        # 跳过空行、标题、区块标记
        line = lines[i].strip()
        if not line or line.startswith('#') or line.startswith(':::'):
            i += 1
            continue

        # 尝试不同窗口大小
        for window_size in range(max_lines, min_lines - 1, -1):
            if i + window_size > len(lines):
                continue

            window_lines = []
            for j in range(i, min(i + window_size, len(lines))):
                l = lines[j].strip()
                if l and not l.startswith('#') and not l.startswith(':::'):
                    window_lines.append(l)
                else:
                    break  # 遇到空行或标题，终止窗口

            if len(window_lines) >= min_lines:
                avg_score, char_dist = analyze_block(window_lines)

                # 如果得分 > 0.6，记录为疑似韵文
                if avg_score > 0.6:
                    text_preview = '\n'.join(window_lines[:5])  # 预览前5行
                    if len(window_lines) > 5:
                        text_preview += f'\n... (共{len(window_lines)}行)'

                    results.append({
                        'start_line': i + 1,
                        'num_lines': len(window_lines),
                        'score': avg_score,
                        'text': text_preview,
                        'char_dist': char_dist,
                        'full_text': '\n'.join(window_lines)
                    })

                    i += len(window_lines)
                    break
        else:
            i += 1

    return results


def analyze_missing_chapters():
    """分析33篇缺失赞的章节"""

    missing_chapters = [
        '014', '015', '016', '017', '019', '020', '023', '024', '025',
        '033', '034', '043', '047', '074', '085', '088', '092',
        '102', '103', '104', '105', '106', '107', '108', '109',
        '112', '119', '125', '126', '127', '128', '129', '130'
    ]

    project_root = Path(__file__).parent.parent
    chapter_dir = project_root / "chapter_md"

    results = {}

    for chapter_num in missing_chapters:
        # 查找tagged.md文件
        chapter_files = list(chapter_dir.glob(f"{chapter_num}_*.tagged.md"))
        if not chapter_files:
            print(f"⚠ 章节 {chapter_num} 未找到tagged.md文件")
            continue

        chapter_file = chapter_files[0]
        # 从文件名提取章节标题
        chapter_title = chapter_file.stem.replace(f"{chapter_num}_", "").replace(".tagged", "")

        print(f"\n{'='*60}")
        print(f"分析章节 {chapter_num}: {chapter_title}")
        print(f"{'='*60}")

        potential = extract_potential_yunwen(chapter_file)

        if potential:
            print(f"✓ 发现 {len(potential)} 个疑似韵文段落：\n")

            for idx, item in enumerate(potential, 1):
                print(f"【段落 {idx}】")
                print(f"  位置: 第 {item['start_line']} 行起，共 {item['num_lines']} 行")
                print(f"  韵文得分: {item['score']:.2f}")
                print(f"  字数分布: {item['char_dist']}")
                print(f"  内容预览:")
                for line in item['text'].split('\n'):
                    print(f"    {line}")
                print()

            results[chapter_num] = {
                'title': chapter_title,
                'potential_yunwen': potential
            }
        else:
            print(f"✗ 未发现疑似韵文段落（阈值 > 0.6）")
            results[chapter_num] = {
                'title': chapter_title,
                'potential_yunwen': []
            }

    # 保存结果
    output_file = project_root / "logs/hidden_yunwen_detection.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✓ 分析完成，结果已保存到: {output_file}")
    print(f"{'='*60}")

    # 统计摘要
    total_potential = sum(len(v['potential_yunwen']) for v in results.values())
    chapters_with_potential = sum(1 for v in results.values() if v['potential_yunwen'])

    print(f"\n摘要:")
    print(f"  分析章节数: {len(missing_chapters)}")
    print(f"  发现疑似韵文的章节数: {chapters_with_potential}")
    print(f"  疑似韵文段落总数: {total_potential}")

    if chapters_with_potential > 0:
        print(f"\n建议人工检查的章节:")
        for chapter_num, data in results.items():
            if data['potential_yunwen']:
                print(f"  {chapter_num} {data['title']}: {len(data['potential_yunwen'])} 个疑似段落")


def test_verse_score():
    """测试verse_score函数"""
    print("=" * 60)
    print("verse_score 函数测试")
    print("=" * 60)

    test_cases = [
        # 典型赞（4字句为主）
        ("〖@鬻熊〗之嗣，〖◆周〗封於〖◆楚〗。僻在〖~荆蛮〗，荜路蓝缕。", "4字赞"),

        # 五言诗
        ("床前明月光，疑是地上霜。举头望明月，低头思故乡。", "五言诗"),

        # 七言诗
        ("两个黄鹂鸣翠柳，一行白鹭上青天。窗含西岭千秋雪，门泊东吴万里船。", "七言诗"),

        # 散文
        ("太史公曰：楚灵王方会诸侯於申，诸侯皆叛，不肯从。及其即位，已崩殂之後而不得其所。", "散文"),

        # 长句散文
        ("余读谍记，黄帝以来皆有年数，稽其历谱谍终始五德之传，古文咸不同，乖异。", "长句散文"),

        # 混合（散文+韵文）
        ("太史公曰：楚灵王不君。其心在高，危大遂位。韩襄遗孽，始从汉中。", "混合"),
    ]

    print()
    for text, label in test_cases:
        score = verse_score(text)
        clean = clean_text(text)
        segments = split_by_punctuation(clean)
        lengths = [len(s) for s in segments]

        print(f"【{label}】")
        print(f"  原文: {text[:40]}...")
        print(f"  句长: {lengths}")
        print(f"  得分: {score:.2f} {'[韵文]' if score > 0.6 else '[散文]'}")
        print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_verse_score()
    else:
        analyze_missing_chapters()
