#!/usr/bin/env python3
"""
统计《高祖功臣侯者年表》143位功臣的封侯原因和国除原因

用法:
    python scripts/analyze_chapter_018_statistics.py
"""

import re
from collections import Counter, defaultdict
from pathlib import Path

def main():
    # 读取章节018文件
    chapter_file = Path("/home/baojie/work/knowledge/shiji-kb/chapter_md/018_高祖功臣侯者年表.tagged.md")

    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取表格部分(从"## 表"开始)
    table_match = re.search(r'## 表\n(.*)', content, re.DOTALL)
    if not table_match:
        print("未找到表格部分")
        return

    table_content = table_match.group(1)

    # 提取每一行(以 [rN] 开头)
    rows = re.findall(r'\[r(\d+)\](.*?)(?=\[r\d+\]|$)', table_content, re.DOTALL)

    print(f"=== 《高祖功臣侯者年表》统计分析 ===\n")
    print(f"总计功臣数量: {len(rows)} 人\n")

    # 初始化统计
    origin_stats = Counter()  # 起点统计
    position_stats = Counter()  # 身份统计
    merit_stats = Counter()  # 战功统计
    fate_stats = Counter()  # 结局统计

    # 详细分析前50条
    detailed_records = []

    for row_num, row_content in rows[:50]:  # 先分析前50条
        # 提取国名
        state_match = re.search(r'〖=?([\u4e00-\u9fff]+)〗?\。', row_content)
        state_name = state_match.group(1) if state_match else "未知"

        # 提取侯功(封侯原因)
        merit_match = re.search(r'\|\s+(.{20,500}?)\s+\|', row_content)
        merit_text = merit_match.group(1).strip() if merit_match else ""

        # 分析起点
        if '从起沛' in merit_text or '起沛' in merit_text:
            origin_stats['从起沛'] += 1
        elif '从起砀' in merit_text or '起砀' in merit_text:
            origin_stats['从起砀'] += 1
        elif '从起薛' in merit_text or '起薛' in merit_text:
            origin_stats['从起薛'] += 1
        elif '从起丰' in merit_text or '起丰' in merit_text:
            origin_stats['从起丰'] += 1
        elif '从起留' in merit_text or '起留' in merit_text:
            origin_stats['从起留'] += 1
        elif '从' in merit_text and '项梁' in merit_text:
            origin_stats['从项梁'] += 1
        elif '从' in merit_text and '项羽' in merit_text:
            origin_stats['从项羽'] += 1
        elif '赵将' in merit_text or '魏将' in merit_text or '齐将' in merit_text:
            origin_stats['诸侯降将'] += 1
        else:
            origin_stats['其他起点'] += 1

        # 分析身份
        if '中涓' in merit_text:
            position_stats['中涓'] += 1
        if '舍人' in merit_text:
            position_stats['舍人'] += 1
        if '郎中' in merit_text:
            position_stats['郎中'] += 1
        if '连敖' in merit_text:
            position_stats['连敖'] += 1
        if '客' in merit_text and '从' in merit_text:
            position_stats['客'] += 1
        if '将军' in merit_text:
            position_stats['将军'] += 1
        if '都尉' in merit_text:
            position_stats['都尉'] += 1

        # 分析战功
        if '击项羽' in merit_text or '击项籍' in merit_text or '攻项羽' in merit_text:
            merit_stats['击项羽'] += 1
        if '定三秦' in merit_text:
            merit_stats['定三秦'] += 1
        if '定齐' in merit_text or '击齐' in merit_text:
            merit_stats['定齐'] += 1
        if '击韩信' in merit_text or '击陈豨' in merit_text or '击黥布' in merit_text:
            merit_stats['平叛(韩信/陈豨/黥布)'] += 1
        if '守' in merit_text and ('关中' in merit_text or '蜀' in merit_text):
            merit_stats['守关中/蜀'] += 1
        if '击秦' in merit_text or '破秦' in merit_text:
            merit_stats['击秦'] += 1

        # 分析结局(从整行提取)
        if '反' in row_content and ('国除' in row_content or '诛' in row_content):
            fate_stats['谋反被诛'] += 1
        elif '坐吕氏诛' in row_content or '坐〖&吕氏〗诛' in row_content:
            fate_stats['坐吕氏诛'] += 1
        elif '酎金' in row_content:
            fate_stats['坐酎金'] += 1
        elif '有罪' in row_content and '国除' in row_content:
            fate_stats['有罪国除'] += 1
        elif '不敬' in row_content and '国除' in row_content:
            fate_stats['不敬国除'] += 1
        elif '无后' in row_content or '无後' in row_content:
            fate_stats['无后国除'] += 1
        elif '夺侯' in row_content or '绝' in row_content:
            fate_stats['夺侯/绝'] += 1

        # 记录详细信息(前20条)
        if len(detailed_records) < 20:
            detailed_records.append({
                'num': row_num,
                'state': state_name,
                'merit': merit_text[:100] + '...' if len(merit_text) > 100 else merit_text
            })

    # 输出统计结果
    print("=" * 60)
    print("一、封侯原因统计(基于前50条样本)")
    print("=" * 60)

    print("\n【1. 从军起点分类】")
    for origin, count in origin_stats.most_common():
        print(f"  {origin:12s}: {count:3d}人")

    print("\n【2. 从军身份分类】(可重复)")
    for position, count in position_stats.most_common():
        print(f"  {position:12s}: {count:3d}人")

    print("\n【3. 主要战功分类】(可重复)")
    for merit, count in merit_stats.most_common():
        print(f"  {merit:25s}: {count:3d}人")

    print("\n【4. 结局分类】(基于前50条样本)")
    for fate, count in fate_stats.most_common():
        print(f"  {fate:15s}: {count:3d}人")

    # 输出部分详细记录
    print("\n" + "=" * 60)
    print("二、前20位功臣详细封侯原因")
    print("=" * 60)
    for i, record in enumerate(detailed_records, 1):
        print(f"\n[{i:2d}] {record['state']} (r{record['num']})")
        print(f"     {record['merit']}")

    print("\n" + "=" * 60)
    print("注: 以上统计基于前50条样本,需要完整统计请读取全部143条记录")
    print("=" * 60)

if __name__ == '__main__':
    main()
