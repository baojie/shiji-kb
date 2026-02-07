#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取所有章节的小节标题（支持多种格式）

支持的小节格式：
1. ## [数字] 标题  （如：## [1] 历法总论）
2. ## 标题         （如：## 秦王政时期）
3. ### 标题        （作为三级小节）
"""

import re
from pathlib import Path
import json


def extract_sections_from_chapter(md_file):
    """从Markdown文件中提取小节标题"""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ⚠️  读取文件失败: {e}")
        return []

    sections = []
    lines = content.split('\n')

    section_num = 0  # 自动编号计数器

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # 跳过第一行标题（通常是 # 章节名）
        if line_num == 1 and line.startswith('# '):
            continue

        # 格式1: ## [数字] 标题
        match_numbered = re.match(r'^## \[(\d+)\] (.+)$', line)
        if match_numbered:
            num = match_numbered.group(1)
            title = match_numbered.group(2)
            # 移除实体标注符号
            title = clean_entity_tags(title)
            sections.append({
                'num': num,
                'title': title,
                'level': 2
            })
            continue

        # 格式2: ## 标题（无编号）
        match_h2 = re.match(r'^## (.+)$', line)
        if match_h2:
            title = match_h2.group(1)
            # 移除实体标注符号
            title = clean_entity_tags(title)
            # 跳过某些特殊标题
            if should_skip_title(title):
                continue
            section_num += 1
            sections.append({
                'num': str(section_num),
                'title': title,
                'level': 2
            })
            continue

        # 格式3: ### 标题（三级标题，作为子节）
        match_h3 = re.match(r'^### (.+)$', line)
        if match_h3:
            title = match_h3.group(1)
            # 移除实体标注符号
            title = clean_entity_tags(title)
            # 跳过某些特殊标题
            if should_skip_title(title):
                continue
            # 三级标题不单独编号，作为上一个二级标题的子节
            if sections:  # 确保有父节
                section_num += 0.1  # 使用小数表示子节
                sections.append({
                    'num': f"{int(section_num)}.{len([s for s in sections if s.get('level') == 3 and s['num'].startswith(f'{int(section_num)}.')])+ 1}",
                    'title': title,
                    'level': 3
                })

    return sections


def clean_entity_tags(text):
    """移除实体标注符号"""
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
    # 🌿动植物🌿
    text = re.sub(r'🌿([^🌿]+)🌿', r'\1', text)
    # $标题/职位$
    text = re.sub(r'\$([^$]+)\$', r'\1', text)

    return text.strip()


def should_skip_title(title):
    """判断是否应该跳过某些标题"""
    skip_keywords = [
        '太史公曰',
        '赞',
        '论',
        '索隐',
        '集解',
        '正义'
    ]

    # 如果标题完全匹配跳过关键词
    if title in skip_keywords:
        return True

    # 如果标题太短（可能是不完整的）
    if len(title) < 2:
        return True

    return False


def main():
    print("=" * 60)
    print("提取所有章节的小节标题")
    print("=" * 60)

    # 查找所有已标注的Markdown文件
    chapter_md_dir = Path('chapter_md')
    tagged_files = sorted(chapter_md_dir.glob('*.tagged.md'))

    print(f"\n找到 {len(tagged_files)} 个章节文件")

    sections_data = {}
    chapters_with_sections = 0
    total_sections = 0

    for tagged_file in tagged_files:
        chapter_name = tagged_file.stem.replace('.tagged', '')
        print(f"\n处理: {chapter_name}")

        sections = extract_sections_from_chapter(tagged_file)

        if sections:
            # 只保留二级标题（level=2）的小节用于导航
            nav_sections = [s for s in sections if s.get('level', 2) == 2]
            if nav_sections:
                sections_data[chapter_name] = [
                    {'num': s['num'], 'title': s['title']}
                    for s in nav_sections
                ]
                chapters_with_sections += 1
                total_sections += len(nav_sections)
                print(f"  ✓ 提取了 {len(nav_sections)} 个小节")
        else:
            print(f"  ⚠️  未找到小节")

    # 保存为JSON
    output_file = 'sections_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sections_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("提取完成！")
    print("=" * 60)
    print(f"有小节的章节数: {chapters_with_sections} / {len(tagged_files)}")
    print(f"总小节数: {total_sections}")
    print(f"平均每章小节数: {total_sections / chapters_with_sections:.1f}")
    print(f"\n✅ 小节数据已保存到: {output_file}")


if __name__ == '__main__':
    main()
