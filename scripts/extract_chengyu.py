#!/usr/bin/env python3
"""
提取史记成语典故
从现有的成语典故MD文件转换为JSON格式，并定位原文位置
"""

import re
import json
from pathlib import Path

def parse_chengyu_md(md_file):
    """
    解析成语典故MD文件

    Returns:
        list: [{'chapter_num': '001', 'chapter_title': '五帝本纪',
                'chengyu': '生而神灵', 'original': '生而神灵，弱而能言',
                'meaning': '天赋异禀'}, ...]
    """
    content = md_file.read_text(encoding='utf-8')
    chengyu_list = []

    current_chapter_num = None
    current_chapter_title = None

    # 逐行解析
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 匹配章节标题: ### 001 五帝本纪
        chapter_match = re.match(r'^###\s+(\d+)\s+(.+)$', line)
        if chapter_match:
            current_chapter_num = chapter_match.group(1)
            current_chapter_title = chapter_match.group(2)
            i += 1
            continue

        # 匹配表格行: | 成语 | 原文 | 释义 |
        if current_chapter_num and line.startswith('|') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')[1:-1]]  # 去掉首尾空白格

            # 跳过表头
            if len(parts) == 3 and parts[0] != '成语':
                chengyu = parts[0]
                original = parts[1]
                meaning = parts[2]

                # 过滤掉注释行（括号开头）
                if not chengyu.startswith('（'):
                    chengyu_list.append({
                        'chapter_num': current_chapter_num,
                        'chapter_title': current_chapter_title,
                        'chengyu': chengyu,
                        'original': original,
                        'meaning': meaning,
                        'context': '',  # 待填充
                        'paragraph': ''  # 待填充
                    })

        i += 1

    return chengyu_list

def clean_text(text):
    """清理文本中的实体标注和特殊符号，用于匹配"""
    # 移除实体标注符号，但保留内容
    # 〖@人名〗 -> 人名
    # 包括所有可能的标记符号：@=^%•{&'~#+?;!$:[]_\
    text = re.sub(r'〖[@=^%•{&\'~#+?;!$:\[\]_\\]([^〗]+)〗', r'\1', text)
    # 移除段落编号 [N] 或 [N.M]
    text = re.sub(r'\[\d+(?:\.\d+)?\]\s*', '', text)
    # 移除引用标记 >
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    # 统一引号（中英文引号都移除）
    text = re.sub(r'["""\'\'\'`]', '', text)
    # 移除空格、换行、标点
    text = re.sub(r'[\s，。；：、？！「」『』《》（）]', '', text)
    return text

def levenshtein_distance(s1, s2):
    """计算两个字符串的编辑距离（Levenshtein距离）"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # 插入、删除、替换的代价
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def fuzzy_find(pattern, text, threshold=0.3):
    """
    在文本中模糊查找pattern

    返回: (best_match_pos, best_match_text, similarity)
    similarity = 1 - (distance / pattern_length)
    """
    pattern_len = len(pattern)
    if pattern_len == 0:
        return -1, "", 0.0

    best_pos = -1
    best_match = ""
    best_similarity = 0.0

    # 滑动窗口，窗口大小为 pattern_len ± 30%
    min_window = int(pattern_len * 0.7)
    max_window = int(pattern_len * 1.3)

    for window_size in range(min_window, max_window + 1):
        for i in range(len(text) - window_size + 1):
            substring = text[i:i + window_size]
            distance = levenshtein_distance(pattern, substring)
            similarity = 1 - (distance / max(len(pattern), len(substring)))

            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_pos = i
                best_match = substring

    return best_pos, best_match, best_similarity

def extract_key_phrase(text):
    """从原文中提取关键短语（用于匹配）"""
    # 清理文本
    clean = clean_text(text)

    # 提取关键短语的多种策略：
    # 1. 去掉开头的人名（1-3字）+ 连接词
    # 2. 取中间部分避开人名主语

    patterns = [
        # 去掉"XX乃/於是/而..."
        r'^.{1,3}[乃於是而則故](.+)$',
        # 去掉"XX，YY，ZZ" 取后半部分
        r'^.{2,10}?([^，。]{6,})$',
        # 保持原样
        r'^(.+)$',
    ]

    for pattern in patterns:
        m = re.match(pattern, clean)
        if m and m.group(1):
            result = m.group(1)
            # 如果结果足够长（至少4字），返回
            if len(result) >= 4:
                return result

    return clean

def locate_chengyu_in_chapter(chengyu_item, chapter_file):
    """
    在章节文件中定位成语的原文位置，提取完整上下文

    Returns:
        dict: 更新后的chengyu_item，包含context和paragraph
    """
    if not chapter_file.exists():
        return chengyu_item

    content = chapter_file.read_text(encoding='utf-8')
    original_text = chengyu_item['original']

    # 跳过括号注释的成语（如"据XX概括"）
    if '（' in original_text or '(' in original_text:
        return chengyu_item

    # 处理省略号：拆分成多个片段，匹配第一个片段
    if '…' in original_text or '...' in original_text:
        fragments = re.split(r'[…\.]{1,}', original_text)
        fragments = [f.strip() for f in fragments if f.strip()]
        if fragments:
            original_text = fragments[0]

    # 清理原文，用于匹配
    clean_original = clean_text(original_text)

    # 如果原文太短（少于3字），跳过
    if len(clean_original) < 3:
        return chengyu_item

    # 提取关键短语
    key_phrase = extract_key_phrase(original_text)

    # 策略1：精确匹配原文
    match_pos = -1
    if original_text in content:
        match_pos = content.index(original_text)

    # 策略2：清理后匹配
    if match_pos < 0:
        clean_content = clean_text(content)

        # 尝试匹配完整清理文本
        if clean_original in clean_content:
            clean_pos = clean_content.index(clean_original)
        # 尝试匹配关键短语
        elif key_phrase in clean_content and len(key_phrase) >= 4:
            clean_pos = clean_content.index(key_phrase)
        # 尝试部分匹配（前N字）
        else:
            clean_pos = -1
            match_len = len(clean_original)
            for test_len in range(match_len, max(3, match_len - 5), -1):
                test_pattern = clean_original[:test_len]
                if test_pattern in clean_content:
                    clean_pos = clean_content.index(test_pattern)
                    break

        if clean_pos >= 0:
            # 映射回原始位置
            char_count = 0
            for i, char in enumerate(content):
                # 只计算实际文字字符（排除所有标注符号和标点）
                if not (char in '〖〗 \t\n' or char in '@=^%•{&\'~#+?;!$:[]_\\' or char in '，。；：、？！「」『』《》（）"\''):
                    if char_count == clean_pos:
                        match_pos = i
                        break
                    char_count += 1

    # 策略3：模糊匹配（用于精确匹配失败的情况）
    if match_pos < 0 and len(clean_original) >= 4:
        clean_content = clean_text(content)

        # 使用关键短语进行模糊匹配
        search_pattern = key_phrase if len(key_phrase) >= 4 else clean_original

        # 短成语（4-5字）使用更高的相似度阈值
        threshold = 0.8 if len(search_pattern) <= 5 else 0.7
        fuzzy_pos, fuzzy_match, similarity = fuzzy_find(search_pattern, clean_content, threshold=threshold)

        if fuzzy_pos >= 0:
            # 映射回原始位置
            char_count = 0
            for i, char in enumerate(content):
                # 只计算实际文字字符（排除所有标注符号和标点）
                if not (char in '〖〗 \t\n' or char in '@=^%•{&\'~#+?;!$:[]_\\' or char in '，。；：、？！「」『』《》（）"\''):
                    if char_count == fuzzy_pos:
                        match_pos = i
                        break
                    char_count += 1

    if match_pos >= 0:
        # 找到匹配位置，提取上下文（前后各150字）
        start = max(0, match_pos - 150)
        end = min(len(content), match_pos + len(original_text) + 150)
        context = content[start:end]

        # 提取所在段落（通过段落编号）
        # 向前搜索最近的段落编号 [N] 或 [N.M]
        before_text = content[:match_pos]
        para_match = None
        for m in re.finditer(r'\[(\d+(?:\.\d+)?)\]', before_text):
            para_match = m

        paragraph_num = para_match.group(1) if para_match else ''

        chengyu_item['context'] = context.strip()
        chengyu_item['paragraph'] = paragraph_num

    return chengyu_item

def main():
    project_root = Path(__file__).parent.parent

    # 输入文件
    input_md = project_root / "kg/vocabularies/data/史记成语典故.md"

    # 输出目录和文件（保存在根目录的data/下）
    output_dir = project_root / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_json = output_dir / "chengyu.json"
    output_md = output_dir / "chengyu.md"

    chapter_dir = project_root / "chapter_md"

    print("解析成语典故MD文件...")
    chengyu_list = parse_chengyu_md(input_md)
    print(f"共提取 {len(chengyu_list)} 条成语")

    # 按章节统计
    chapter_counts = {}
    for item in chengyu_list:
        key = f"{item['chapter_num']} {item['chapter_title']}"
        chapter_counts[key] = chapter_counts.get(key, 0) + 1

    print(f"\n涵盖章节: {len(chapter_counts)} 章")

    # 定位成语在章节文件中的位置
    print("\n定位成语原文位置...")
    located_count = 0
    for i, item in enumerate(chengyu_list):
        chapter_num = item['chapter_num']
        chapter_title = item['chapter_title']

        # 查找章节文件
        chapter_file = chapter_dir / f"{chapter_num}_{chapter_title}.tagged.md"

        chengyu_list[i] = locate_chengyu_in_chapter(item, chapter_file)

        if chengyu_list[i]['context']:
            located_count += 1

        if (i + 1) % 50 == 0:
            print(f"  已处理 {i + 1}/{len(chengyu_list)} 条...")

    print(f"✓ 成功定位 {located_count}/{len(chengyu_list)} 条成语的原文位置")

    # 保存JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(chengyu_list, f, ensure_ascii=False, indent=2)
    print(f"\n✓ JSON 已保存: {output_json}")

    # 生成 Markdown
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write("# 史记成语典故\n\n")
        f.write(f"史记中共有 {len(chengyu_list)} 条成语典故\n\n")
        f.write(f"涵盖章节: {len(chapter_counts)}/130\n\n")

        f.write("---\n\n")

        # 按章节分组
        current_chapter = None
        for item in chengyu_list:
            chapter_key = f"{item['chapter_num']} {item['chapter_title']}"

            if chapter_key != current_chapter:
                current_chapter = chapter_key
                f.write(f"## {chapter_key}\n\n")

            f.write(f"### {item['chengyu']}\n\n")
            f.write(f"**释义**: {item['meaning']}\n\n")
            f.write(f"**原文**: {item['original']}\n\n")

            if item['paragraph']:
                f.write(f"**位置**: 第 {item['paragraph']} 段\n\n")

            if item['context']:
                f.write(f"**上下文**:\n\n{item['context']}\n\n")

            f.write("---\n\n")

    print(f"✓ Markdown 已保存: {output_md}")

    # 统计信息
    print(f"\n统计信息：")
    print(f"  成语总数: {len(chengyu_list)}")
    print(f"  涵盖章节: {len(chapter_counts)}/130")
    print(f"  定位成功: {located_count}/{len(chengyu_list)} ({located_count*100//len(chengyu_list)}%)")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
