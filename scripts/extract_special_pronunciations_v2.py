#!/usr/bin/env python3
"""
从《史记集解三家注索隐正义》中提取特殊读音注释（改进版）
重点关注地名、人名、姓氏等的特殊读音
"""

import re
from collections import defaultdict
from typing import Dict, List, Tuple

# 文件路径
NOTES_FILE = 'corpus/shiji/史记集解三家注索隐正义.txt'
ORIGINAL_FILE = 'corpus/shiji/史记.简体.txt'

# 需要过滤的常见字（功能词、高频字等）
COMMON_WORDS = {
    '而', '其', '所', '者', '之', '也', '以', '于', '则', '为', '乎',
    '何', '与', '若', '且', '及', '虽', '然', '故', '此', '彼',
    '或', '非', '否', '无', '有', '是', '不', '未', '从', '焉',
    '哉', '矣', '乃', '即', '夫', '斯', '惟', '唯', '曰', '云'
}

def extract_special_pronunciations(notes_content: str, original_content: str) -> List[Dict]:
    """提取特殊读音注释"""
    results = []

    # 模式1: 明确的反切注音 - X音Y Z反
    pattern_fanqie = re.compile(r'([^，。：；！？「」『』\s]{1,3})音([^，。：；！？「」『』\s])([^，。：；！？「」『』\s])反')
    for match in pattern_fanqie.finditer(notes_content):
        char = match.group(1).strip()
        fanqie = match.group(2) + match.group(3)

        # 过滤掉常见虚词和一些明显的误匹配
        if char in COMMON_WORDS or '音义' in char or '音' in char:
            continue

        # 获取上下文
        context_start = max(0, match.start() - 100)
        context_end = min(len(notes_content), match.end() + 100)
        context = notes_content[context_start:context_end].replace('\n', ' ')

        # 统计在原文中出现次数
        count = original_content.count(char)

        # 识别类型
        item_type = identify_type(context)

        if count > 0 and len(char) <= 2:
            results.append({
                'char': char,
                'sound': fanqie,
                'sound_type': '反切',
                'type': item_type,
                'count': count,
                'context': context
            })

    # 模式2: X音Y（非反切）- 提取更精确的注音
    pattern_yin = re.compile(r'([^，。：；！？「」『』音\s]{1,3})音([^，。：；！？「」『』反\s]{1,4})[。，]')
    for match in pattern_yin.finditer(notes_content):
        char = match.group(1).strip()
        sound = match.group(2).strip()

        # 过滤
        if char in COMMON_WORDS or '音义' in char or '音' in char or len(sound) > 3:
            continue

        context_start = max(0, match.start() - 100)
        context_end = min(len(notes_content), match.end() + 100)
        context = notes_content[context_start:context_end].replace('\n', ' ')

        count = original_content.count(char)
        item_type = identify_type(context)

        if count > 0 and len(char) <= 2:
            results.append({
                'char': char,
                'sound': sound,
                'sound_type': '音注',
                'type': item_type,
                'count': count,
                'context': context
            })

    # 模式3: X读曰Y - 通假字读音
    pattern_duyue = re.compile(r'「?([^，。：；！？「」『』\s读]{1,3})」?读曰「?([^，。：；！？「」『』\s]{1,3})」?')
    for match in pattern_duyue.finditer(notes_content):
        char = match.group(1).strip()
        sound = match.group(2).strip()

        if char in COMMON_WORDS or len(char) > 2 or len(sound) > 2:
            continue

        context_start = max(0, match.start() - 100)
        context_end = min(len(notes_content), match.end() + 100)
        context = notes_content[context_start:context_end].replace('\n', ' ')

        count = original_content.count(char)
        item_type = identify_type(context)

        if count > 0:
            results.append({
                'char': char,
                'sound': sound,
                'sound_type': '读曰',
                'type': item_type,
                'count': count,
                'context': context
            })

    # 模式4: X读为Y - 通假字读音
    pattern_duwei = re.compile(r'「?([^，。：；！？「」『』\s读]{1,3})」?读为「?([^，。：；！？「」『』\s]{1,3})」?')
    for match in pattern_duwei.finditer(notes_content):
        char = match.group(1).strip()
        sound = match.group(2).strip()

        if char in COMMON_WORDS or len(char) > 2 or len(sound) > 2:
            continue

        context_start = max(0, match.start() - 100)
        context_end = min(len(notes_content), match.end() + 100)
        context = notes_content[context_start:context_end].replace('\n', ' ')

        count = original_content.count(char)
        item_type = identify_type(context)

        if count > 0:
            results.append({
                'char': char,
                'sound': sound,
                'sound_type': '读为',
                'type': item_type,
                'count': count,
                'context': context
            })

    return results

def identify_type(context: str) -> str:
    """根据上下文识别是地名、人名还是其他"""
    # 按优先级判断
    if any(kw in context for kw in ['县', '州', '郡', '国', '城', '山', '水', '河', '地名', '在', '今', '括地志']):
        return '地名'
    elif any(kw in context for kw in ['姓', '氏']):
        return '姓氏'
    elif any(kw in context for kw in ['名', '字', '号', '人']):
        return '人名'
    elif any(kw in context for kw in ['官', '职', '位']):
        return '官职'
    elif any(kw in context for kw in ['乐', '礼', '书', '诗', '易']):
        return '典籍/礼乐'
    else:
        return '其他'

def deduplicate_and_merge(results: List[Dict]) -> Dict[str, Dict]:
    """去重并合并同一字的不同读音"""
    char_dict = {}

    for item in results:
        char = item['char']

        if char not in char_dict:
            char_dict[char] = {
                'char': char,
                'sounds': [],
                'types': set(),
                'count': item['count'],
                'contexts': []
            }

        # 添加读音信息
        sound_info = f"{item['sound']}({item['sound_type']})"
        if sound_info not in char_dict[char]['sounds']:
            char_dict[char]['sounds'].append(sound_info)

        # 添加类型
        char_dict[char]['types'].add(item['type'])

        # 添加上下文（限制数量）
        if len(char_dict[char]['contexts']) < 2:
            char_dict[char]['contexts'].append(item['context'])

    return char_dict

def main():
    # 读取文件
    print("读取文件...")
    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
        notes_content = f.read()

    with open(ORIGINAL_FILE, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # 提取读音
    print("提取特殊读音注释...")
    pronunciations = extract_special_pronunciations(notes_content, original_content)
    print(f"共提取 {len(pronunciations)} 条读音注释")

    # 去重并合并
    unique_chars = deduplicate_and_merge(pronunciations)
    print(f"去重后 {len(unique_chars)} 个不同字符")

    # 按出现次数排序
    sorted_items = sorted(unique_chars.values(), key=lambda x: x['count'], reverse=True)

    # 分类统计
    type_groups = defaultdict(list)
    for item in sorted_items:
        # 获取主要类型（取第一个）
        main_type = list(item['types'])[0] if item['types'] else '其他'
        type_groups[main_type].append(item)

    # 输出结果
    print("\n" + "="*100)
    print("《史记》特殊读音注释提取结果")
    print("="*100)

    # 按类型输出
    for type_name in ['地名', '姓氏', '人名', '官职', '典籍/礼乐', '其他']:
        if type_name not in type_groups:
            continue

        items = type_groups[type_name]
        print(f"\n{'='*100}")
        print(f"【{type_name}】 共 {len(items)} 个")
        print("="*100)

        for i, item in enumerate(items[:20], 1):  # 每类显示前20个
            types_str = '/'.join(item['types'])
            sounds_str = '、'.join(item['sounds'])

            print(f"\n{i}. 【{item['char']}】")
            print(f"   读音: {sounds_str}")
            print(f"   类型: {types_str}")
            print(f"   原文出现: {item['count']} 次")
            if item['contexts']:
                print(f"   上下文: {item['contexts'][0][:120]}...")

    # 输出总体统计
    print("\n" + "="*100)
    print("统计信息")
    print("="*100)
    for type_name, items in sorted(type_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{type_name}: {len(items)} 个")

if __name__ == '__main__':
    main()
