#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量标注史记021-040章节
"""

import re
from pathlib import Path

def tag_entities(text):
    """对文本进行实体标注"""
    # 此处为简化版本，实际标注需要更复杂的逻辑
    # 可以基于已有的标注规则来扩展

    # 官职标注（简单示例）
    offices = ['太史公', '御史', '丞相', '太尉', '将军', '大夫', '侯', '王', '帝', '皇帝']
    for office in offices:
        text = re.sub(rf'(?<!\$){office}(?!\$)', f'${office}$', text)

    # 朝代标注
    dynasties = ['汉', '秦', '周', '商', '殷', '夏', '楚', '齐', '燕', '赵', '魏', '韩', '吴', '越']
    for dynasty in dynasties:
        text = re.sub(rf'(?<!&){dynasty}(?!&)', f'&{dynasty}&', text)

    return text

def process_chapter(input_file, output_file, chapter_num, chapter_name):
    """处理单个章节"""
    print(f"处理 {chapter_num}_{chapter_name}...")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')

    # 生成标注后的文本
    tagged_lines = [f"# [0] {chapter_name}\n"]

    para_num = 1
    for line in lines[1:]:  # 跳过第一行标题
        if not line.strip():
            continue

        # 简单的段落标注
        tagged_line = f"[{para_num}] {tag_entities(line)}"
        tagged_lines.append(tagged_line + '\n')
        para_num += 1

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(tagged_lines)

    print(f"✓ 完成 {output_file}")

def main():
    """主函数"""
    original_dir = Path('/home/baojie/work/shiji-kb/docs/original_text')
    output_dir = Path('/home/baojie/work/shiji-kb/chapter_md')

    # 021-040章节列表
    chapters = [
        ('021', '建元已来王子侯者年表'),
        ('022', '汉兴以来将相名臣年表'),
        ('023', '礼书'),
        ('024', '乐书'),
        ('025', '律书'),
        ('026', '历书'),
        ('027', '天官书'),
        ('028', '封禅书'),
        ('029', '河渠书'),
        ('030', '平准书'),
        ('031', '吴太伯世家'),
        ('032', '齐太公世家'),
        ('033', '鲁周公世家'),
        ('034', '燕召公世家'),
        ('035', '管蔡世家'),
        ('036', '陈杞世家'),
        ('037', '卫康叔世家'),
        ('038', '宋微子世家'),
        ('039', '晋世家'),
        ('040', '楚世家'),
    ]

    for num, name in chapters:
        input_file = original_dir / f'{num}_{name}.txt'
        output_file = output_dir / f'{num}_{name}.tagged.md'

        if not input_file.exists():
            print(f"✗ 文件不存在: {input_file}")
            continue

        if output_file.exists():
            print(f"- 跳过已存在: {output_file.name}")
            continue

        try:
            process_chapter(input_file, output_file, num, name)
        except Exception as e:
            print(f"✗ 处理失败 {num}_{name}: {e}")

if __name__ == '__main__':
    main()
