#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史记原文词频统计分析

从130篇已标注的Markdown文件中提取原文，进行词频统计
"""

import re
from pathlib import Path
from collections import Counter
import json

def extract_plain_text(tagged_md_file):
    """
    从标注的Markdown文件中提取纯文本
    去除所有标注符号：@人名@, =地名=, #官职#, %时间%, &朝代&, ^制度^, ~族群~, *器物*, !天文!, ?神话?, 🌿动植物🌿, $标题/职位$
    去除段落编号：[1.1], [2.3]等
    去除标题：#开头的行
    """
    with open(tagged_md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 移除标题行
    lines = content.split('\n')
    text_lines = [line for line in lines if not line.startswith('#')]
    text = '\n'.join(text_lines)

    # 移除段落编号 [X.Y]
    text = re.sub(r'\[\d+(?:\.\d+)?\]', '', text)

    # 移除实体标注符号
    # @人名@
    text = re.sub(r'@([^@]+)@', r'\1', text)
    # =地名=
    text = re.sub(r'=([^=]+)=', r'\1', text)
    # #官职#
    text = re.sub(r'#([^#]+)#', r'\1', text)
    # %时间%
    text = re.sub(r'%([^%]+)%', r'\1', text)
    # &朝代&
    text = re.sub(r'&([^&]+)&', r'\1', text)
    # ^制度^
    text = re.sub(r'\^([^^]+)\^', r'\1', text)
    # ~族群~
    text = re.sub(r'~([^~]+)~', r'\1', text)
    # *器物*
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # !天文!
    text = re.sub(r'!([^!]+)!', r'\1', text)
    # ?神话?
    text = re.sub(r'\?([^?]+)\?', r'\1', text)
    # 🌿动植物🌿 (emoji标注)
    text = re.sub(r'🌿([^🌿]+)🌿', r'\1', text)
    # $标题/职位$ (另一种标注)
    text = re.sub(r'\$([^$]+)\$', r'\1', text)

    # 移除引号标记 > 开头的行
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

    # 移除多余的空白
    text = re.sub(r'\s+', '', text)

    return text

def segment_chinese_text(text):
    """
    对中文文本进行简单的字频和常见词频统计
    不使用外部分词库，直接统计字符和常见双字/三字词
    """
    # 定义标点符号集合（用于过滤词组）
    punctuation = set('，。；：！？、""''《》（）【】「」『』…—·・,.;:!?\'"[](){}、\n\r\t ')
    # 添加Unicode引号字符
    unicode_quotes = {'\u2018', '\u2019', '\u201c', '\u201d'}  # ' ' " "
    digits = set('0123456789')
    # 添加英文字母（用于过滤NOTE等标记）
    letters = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    invalid_chars = punctuation | unicode_quotes | digits | letters

    # 统计单字
    char_freq = Counter(text)

    # 统计双字词（过滤包含标点、数字、字母的词）
    bigrams = [text[i:i+2] for i in range(len(text)-1)
               if not any(c in invalid_chars for c in text[i:i+2])]
    bigram_freq = Counter(bigrams)

    # 统计三字词（过滤包含标点、数字、字母的词）
    trigrams = [text[i:i+3] for i in range(len(text)-2)
                if not any(c in invalid_chars for c in text[i:i+3])]
    trigram_freq = Counter(trigrams)

    return char_freq, bigram_freq, trigram_freq

def main():
    print("开始史记原文词频统计...")

    # 查找所有已标注的Markdown文件
    chapter_md_dir = Path('chapter_md')
    tagged_files = sorted(chapter_md_dir.glob('*.tagged.md'))

    print(f"找到 {len(tagged_files)} 个已标注文件")

    if len(tagged_files) == 0:
        print("错误：未找到任何已标注的Markdown文件")
        return

    # 提取所有文本
    all_text = ""
    for tagged_file in tagged_files:
        plain_text = extract_plain_text(tagged_file)
        all_text += plain_text

    print(f"提取文本完成，总字符数：{len(all_text):,}")

    # 进行词频统计
    print("进行词频统计...")
    char_freq, bigram_freq, trigram_freq = segment_chinese_text(all_text)

    # 过滤掉标点符号、数字和空白字符
    punctuation = set('，。；：！？、""''《》（）【】「」『』…—·・,.;:!?\'"[](){}、\n\r\t ')
    digits = set('0123456789')
    char_freq = Counter({k: v for k, v in char_freq.items()
                        if k not in punctuation and k not in digits and k.strip()})

    # 准备统计结果
    results = {
        'total_chars': len(all_text),
        'unique_chars': len(char_freq),
        'top_100_chars': char_freq.most_common(100),
        'top_100_bigrams': bigram_freq.most_common(100),
        'top_100_trigrams': trigram_freq.most_common(100)
    }

    # 保存为JSON
    output_file = 'doc/词频统计结果.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON结果已保存到：{output_file}")

    # 生成Markdown格式的统计表
    md_output = generate_markdown_report(results)
    md_file = 'doc/词频统计表.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_output)
    print(f"✅ Markdown报告已保存到：{md_file}")

    # 打印摘要
    print("\n" + "="*50)
    print("词频统计摘要")
    print("="*50)
    print(f"总字符数：{results['total_chars']:,}")
    print(f"不同字符数：{results['unique_chars']:,}")
    print(f"\n高频字符 Top 20：")
    for char, freq in results['top_100_chars'][:20]:
        print(f"  {char}: {freq:,}次")
    print(f"\n高频双字词 Top 20：")
    for word, freq in results['top_100_bigrams'][:20]:
        print(f"  {word}: {freq:,}次")
    print(f"\n高频三字词 Top 20：")
    for word, freq in results['top_100_trigrams'][:20]:
        print(f"  {word}: {freq:,}次")

def generate_markdown_report(results):
    """生成Markdown格式的统计报告"""
    report = f"""# 史记原文词频统计表

**统计时间**：2026-02-08
**数据来源**：130篇已标注章节（去除标注符号后的纯文本）

---

## 总体统计

- **总字符数**：{results['total_chars']:,}
- **不同字符数**：{results['unique_chars']:,}

---

## 高频字符 Top 100

| 排名 | 字符 | 出现次数 | 排名 | 字符 | 出现次数 | 排名 | 字符 | 出现次数 | 排名 | 字符 | 出现次数 |
|------|------|----------|------|------|----------|------|------|----------|------|------|----------|
"""

    # 每行4个字符，共25行
    top_chars = results['top_100_chars']
    for i in range(0, 100, 4):
        row = ""
        for j in range(4):
            if i + j < len(top_chars):
                rank = i + j + 1
                char, freq = top_chars[i + j]
                row += f"| {rank} | {char} | {freq:,} "
            else:
                row += "| | | "
        row += "|\n"
        report += row

    report += f"""
---

## 高频双字词 Top 100

| 排名 | 词语 | 出现次数 | 排名 | 词语 | 出现次数 | 排名 | 词语 | 出现次数 | 排名 | 词语 | 出现次数 |
|------|------|----------|------|------|----------|------|------|----------|------|------|----------|
"""

    top_bigrams = results['top_100_bigrams']
    for i in range(0, 100, 4):
        row = ""
        for j in range(4):
            if i + j < len(top_bigrams):
                rank = i + j + 1
                word, freq = top_bigrams[i + j]
                row += f"| {rank} | {word} | {freq:,} "
            else:
                row += "| | | "
        row += "|\n"
        report += row

    report += f"""
---

## 高频三字词 Top 100

| 排名 | 词语 | 出现次数 | 排名 | 词语 | 出现次数 | 排名 | 词语 | 出现次数 | 排名 | 词语 | 出现次数 |
|------|------|----------|------|------|----------|------|------|----------|------|------|----------|
"""

    top_trigrams = results['top_100_trigrams']
    for i in range(0, 100, 4):
        row = ""
        for j in range(4):
            if i + j < len(top_trigrams):
                rank = i + j + 1
                word, freq = top_trigrams[i + j]
                row += f"| {rank} | {word} | {freq:,} "
            else:
                row += "| | | "
        row += "|\n"
        report += row

    report += """
---

## 说明

- **总字符数**：去除标注符号、段落编号、标题后的纯文本字符总数
- **字符统计**：包含所有汉字，已过滤标点符号
- **双字词**：相邻两个字符组成的词
- **三字词**：相邻三个字符组成的词

**注意**：本统计未使用专业分词工具，双字词和三字词为简单的字符组合统计，可能包含非词汇的字符组合。
"""

    return report

if __name__ == '__main__':
    main()
