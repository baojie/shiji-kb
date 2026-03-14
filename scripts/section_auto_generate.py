#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为没有明确小节的章节自动生成小节划分

策略：
1. 基于段落编号分组（每8-12个段落一组）
2. 读取每组的前几段内容
3. 使用启发式规则生成小节标题
4. 将小节标记插入Markdown文件
"""

import re
import json
from pathlib import Path


def get_chapters_without_sections():
    """获取没有小节的章节列表"""
    # 读取现有小节数据
    with open('sections_data.json', 'r', encoding='utf-8') as f:
        sections_data = json.load(f)

    # 获取所有章节
    all_chapters = sorted([f for f in Path('chapter_md').glob('*.tagged.md')])

    # 返回没有小节的章节
    chapters_without_sections = []
    for ch_file in all_chapters:
        ch_name = ch_file.stem.replace('.tagged', '')
        if ch_name not in sections_data:
            chapters_without_sections.append(ch_file)

    return chapters_without_sections


def analyze_chapter_structure(md_file):
    """分析章节结构，提取段落和内容"""
    content = md_file.read_text(encoding='utf-8')
    lines = content.split('\n')

    # 提取所有段落
    paragraphs = []
    current_para = None

    for line in lines:
        # 匹配段落编号 [数字] 或 [数字.数字]
        para_match = re.match(r'\[(\d+(?:\.\d+)*)\]\s*(.+)', line)
        if para_match:
            para_num = para_match.group(1)
            para_text = para_match.group(2)

            if current_para:
                paragraphs.append(current_para)

            current_para = {
                'num': para_num,
                'text': para_text,
                'line': line
            }
        elif current_para and line.strip():
            # 续行
            current_para['text'] += ' ' + line.strip()
            current_para['line'] += '\n' + line

    if current_para:
        paragraphs.append(current_para)

    return paragraphs, content


def clean_text(text):
    """清理文本中的标注符号"""
    # 移除所有实体标注
    text = re.sub(r'@([^@]+)@', r'\1', text)
    text = re.sub(r'=([^=]+)=', r'\1', text)
    text = re.sub(r'#([^#]+)#', r'\1', text)
    text = re.sub(r'%([^%]+)%', r'\1', text)
    text = re.sub(r'&([^&]+)&', r'\1', text)
    text = re.sub(r'\^([^^]+)\^', r'\1', text)
    text = re.sub(r'~([^~]+)~', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'!([^!]+)!', r'\1', text)
    text = re.sub(r'〚([^〚〛]+)〛', r'\1', text)
    text = re.sub(r'〖+([^〖+〗]+)〗', r'\1', text)  # 生物（新符号）
    text = re.sub(r'\$([^$]+)\$', r'\1', text)
    return text


def generate_section_title(paragraphs, chapter_name):
    """基于段落内容生成小节标题"""
    if not paragraphs:
        return "正文"

    # 获取这组段落的前3段文本
    sample_texts = []
    for para in paragraphs[:3]:
        clean = clean_text(para['text'])
        sample_texts.append(clean[:50])  # 取前50字

    combined = ''.join(sample_texts)

    # 简单的启发式规则
    if '曰' in combined or '云' in combined:
        return "评论与论述"
    elif '年' in combined or '月' in combined:
        return "编年记事"
    elif '战' in combined or '伐' in combined or '击' in combined:
        return "战争与征伐"
    elif '封' in combined or '侯' in combined or '王' in combined:
        return "封赏与爵位"
    elif '太史公' in combined:
        return "太史公评论"
    else:
        # 默认使用段落范围
        return f"第{paragraphs[0]['num']}节起"


def suggest_sections_for_chapter(md_file):
    """为章节建议小节划分"""
    paragraphs, content = analyze_chapter_structure(md_file)

    if len(paragraphs) < 10:
        # 段落太少，不需要分节
        return []

    # 每10个段落一个小节
    section_size = 10
    sections = []

    for i in range(0, len(paragraphs), section_size):
        group = paragraphs[i:i+section_size]
        title = generate_section_title(group, md_file.stem)

        sections.append({
            'insert_before_para': group[0]['num'],
            'title': title,
            'para_range': f"{group[0]['num']}-{group[-1]['num']}"
        })

    return sections


def main():
    print("=" * 70)
    print("为没有小节的章节生成自动小节建议")
    print("=" * 70)

    chapters = get_chapters_without_sections()
    print(f"\n找到 {len(chapters)} 个没有小节的章节")

    suggestions = {}

    for ch_file in chapters[:10]:  # 先处理前10个作为示例
        ch_name = ch_file.stem.replace('.tagged', '')
        print(f"\n处理: {ch_name}")

        sections = suggest_sections_for_chapter(ch_file)

        if sections:
            suggestions[ch_name] = sections
            print(f"  建议 {len(sections)} 个小节:")
            for i, sec in enumerate(sections, 1):
                print(f"    {i}. {sec['title']} (段落 {sec['para_range']})")
        else:
            print(f"  ⚠️  章节太短，不需要分节")

    # 保存建议
    output_file = 'auto_sections_suggestions.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(suggestions, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"✅ 建议已保存到: {output_file}")
    print("\n说明：")
    print("  这是自动生成的小节建议，需要人工审核和调整")
    print("  建议在编辑器中打开相应章节，根据实际内容添加合适的小节标题")


if __name__ == '__main__':
    main()
