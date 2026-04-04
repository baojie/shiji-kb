#!/usr/bin/env python3
"""
从《史记集解三家注索隐正义》中提取特殊读音注释
并在《史记》原文中验证出现频次
"""

import re
from collections import defaultdict
from typing import Dict, List, Tuple

# 文件路径
NOTES_FILE = 'corpus/shiji/史记集解三家注索隐正义.txt'
ORIGINAL_FILE = 'corpus/shiji/史记.简体.txt'

def extract_pronunciations(content: str) -> List[Dict]:
    """提取各种读音注释"""
    results = []

    # 模式1: X音Y (反切注音)
    # 例如: "解音蟹"、"朝音招"、"单读禅"
    pattern1 = re.compile(r'([^，。：；！？」』\s]{1,3})音([^，。：；！？」』反\s]{1,3})(?:反)?[。，]')
    for match in pattern1.finditer(content):
        char = match.group(1)
        sound = match.group(2)
        # 过滤掉一些常见的误匹配
        if len(char) <= 2 and len(sound) <= 3 and '音义' not in char:
            context = content[max(0, match.start()-50):min(len(content), match.end()+50)]
            results.append({
                'char': char,
                'sound': sound,
                'type': '音注',
                'context': context.replace('\n', ' ')
            })

    # 模式2: X读曰Y
    pattern2 = re.compile(r'「?([^，。：；！？」』\s]{1,3})」?读曰「?([^，。：；！？」』\s]{1,3})」?')
    for match in pattern2.finditer(content):
        char = match.group(1)
        sound = match.group(2)
        if len(char) <= 3 and len(sound) <= 3:
            context = content[max(0, match.start()-50):min(len(content), match.end()+50)]
            results.append({
                'char': char,
                'sound': sound,
                'type': '读曰',
                'context': context.replace('\n', ' ')
            })

    # 模式3: X读为Y
    pattern3 = re.compile(r'「?([^，。：；！？」』\s]{1,3})」?读为「?([^，。：；！？」』\s]{1,3})」?')
    for match in pattern3.finditer(content):
        char = match.group(1)
        sound = match.group(2)
        if len(char) <= 3 and len(sound) <= 3:
            context = content[max(0, match.start()-50):min(len(content), match.end()+50)]
            results.append({
                'char': char,
                'sound': sound,
                'type': '读为',
                'context': context.replace('\n', ' ')
            })

    # 模式4: 反切注音 X音Y Z反
    pattern4 = re.compile(r'([^，。：；！？」』\s]{1,3})音([^，。：；！？」』\s])([^，。：；！？」』\s])反')
    for match in pattern4.finditer(content):
        char = match.group(1)
        fanqie = match.group(2) + match.group(3)
        context = content[max(0, match.start()-50):min(len(content), match.end()+50)]
        results.append({
            'char': char,
            'sound': fanqie,
            'type': '反切',
            'context': context.replace('\n', ' ')
        })

    return results

def count_in_original(char: str, original_content: str) -> int:
    """统计字符在原文中出现的次数"""
    return original_content.count(char)

def identify_type(context: str) -> str:
    """根据上下文识别是地名、人名还是其他"""
    if '地名' in context or '县' in context or '州' in context or '邑' in context:
        return '地名'
    elif '姓' in context:
        return '姓氏'
    elif '人名' in context or '名' in context:
        return '人名'
    elif '官' in context or '职' in context:
        return '官职'
    else:
        return '其他'

def main():
    # 读取文件
    print("读取文件...")
    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
        notes_content = f.read()

    with open(ORIGINAL_FILE, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # 提取读音
    print("提取读音注释...")
    pronunciations = extract_pronunciations(notes_content)
    print(f"共提取 {len(pronunciations)} 条读音注释")

    # 去重并统计
    unique_chars = {}
    for item in pronunciations:
        char = item['char']
        if char not in unique_chars:
            count = count_in_original(char, original_content)
            item_type = identify_type(item['context'])
            unique_chars[char] = {
                'char': char,
                'sound': item['sound'],
                'type': item_type,
                'note_type': item['type'],
                'count': count,
                'context': item['context']
            }

    # 按出现次数排序
    sorted_items = sorted(unique_chars.values(), key=lambda x: x['count'], reverse=True)

    # 筛选有实际意义的结果（在原文中至少出现过，且字符长度合适）
    filtered_items = [
        item for item in sorted_items
        if item['count'] > 0 and len(item['char']) <= 2
    ]

    # 输出结果
    print("\n" + "="*80)
    print("特殊读音注释列表（在《史记》原文中有出现）")
    print("="*80)

    for i, item in enumerate(filtered_items[:50], 1):  # 显示前50个
        print(f"\n{i}. 【{item['char']}】")
        print(f"   读音: {item['sound']} ({item['note_type']})")
        print(f"   类型: {item['type']}")
        print(f"   原文出现: {item['count']} 次")
        print(f"   上下文: {item['context'][:100]}...")

    # 输出统计
    print("\n" + "="*80)
    print("统计信息")
    print("="*80)
    print(f"总提取数: {len(pronunciations)}")
    print(f"去重后: {len(unique_chars)}")
    print(f"在原文中出现: {len(filtered_items)}")

    type_counts = defaultdict(int)
    for item in filtered_items:
        type_counts[item['type']] += 1

    print("\n按类型统计:")
    for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {t}: {count}")

if __name__ == '__main__':
    main()
