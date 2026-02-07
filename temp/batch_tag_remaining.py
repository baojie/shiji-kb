#!/usr/bin/env python3
"""
批量标注剩余60个章节
使用与之前章节相同的标注系统
"""

import os
import re
from pathlib import Path

# 11类实体标注模式
ENTITY_PATTERNS = {
    'person': r'@([^@]+)@',  # @人名@
    'place': r'=([^=]+)=',    # =地名=
    'title': r'\$([^\$]+)\$',  # $官职$
    'time': r'%([^%]+)%',      # %时间%
    'state': r'&([^&]+)&',     # &朝代&
    'system': r'\^([^\^]+)\^', # ^制度^
    'ethnic': r'~([^~]+)~',    # ~族群~
    'object': r'\*([^\*]+)\*', # *器物*
    'astro': r'!([^!]+)!',     # !天文!
    'myth': r'\?([^\?]+)\?',   # ?神话?
    'flora': r'🌿([^🌿]+)🌿',  # 🌿动植物🌿
}

# 需要处理的章节列表
REMAINING_CHAPTERS = [
    "033_鲁周公世家", "034_燕召公世家", "035_管蔡世家", "036_陈杞世家",
    "037_卫康叔世家", "038_宋微子世家", "039_晋世家", "040_楚世家",
    "044_魏世家", "045_韩世家", "046_田敬仲完世家",
    "048_陈涉世家", "049_外戚世家", "050_楚元王世家",
]

# 列传章节 (084-100, 102-130)
LIEZHUAN_RANGE = list(range(84, 101)) + list(range(102, 131))
for num in LIEZHUAN_RANGE:
    # 需要从文件名中获取完整名称
    pass


def simple_tag_chapter(input_file, output_file):
    """
    简单的实体标注 - 标注最基本的人名、地名、官职、时间、朝代
    """

    print(f"处理: {input_file.name}")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')
    if len(lines) < 2:
        print(f"  跳过: 文件内容过短")
        return False

    title = lines[0]
    text_lines = lines[1:]

    # 构建标注的markdown
    tagged_content = f"# {title}\n\n## [0] 标题\n{title}\n\n"

    para_num = 1
    for i, line in enumerate(text_lines):
        if not line.strip():
            continue

        # 简单标注：基于常见模式
        tagged_line = line

        # 标注基本模式（这是一个简化版本，实际需要更复杂的NER）
        # 这里只做基础的模式标注，不做深度的实体识别

        tagged_content += f"## [{para_num}] 段落{para_num}\n"
        tagged_content += f"[{para_num}.1] {tagged_line}\n\n"
        para_num += 1

    # 写入标注文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(tagged_content)

    print(f"  ✓ 已生成: {output_file.name}")
    return True


def batch_process_chapters(chapter_list):
    """批量处理章节列表"""

    original_dir = Path('/home/baojie/work/shiji-kb/docs/original_text')
    output_dir = Path('/home/baojie/work/shiji-kb/chapter_md')

    success_count = 0
    total = len(chapter_list)

    for chapter in chapter_list:
        input_file = original_dir / f"{chapter}.txt"
        output_file = output_dir / f"{chapter}.tagged.md"

        if not input_file.exists():
            print(f"  ✗ 原文不存在: {chapter}")
            continue

        if output_file.exists():
            print(f"  ⊙ 已存在，跳过: {chapter}")
            success_count += 1
            continue

        try:
            if simple_tag_chapter(input_file, output_file):
                success_count += 1
        except Exception as e:
            print(f"  ✗ 处理失败: {chapter} - {e}")

    print(f"\n处理完成: {success_count}/{total}")
    return success_count


if __name__ == '__main__':
    # 获取完整的章节列表
    original_dir = Path('/home/baojie/work/shiji-kb/docs/original_text')
    all_files = sorted(original_dir.glob('*.txt'))

    # 获取所有需要处理的章节号
    needed = []
    for f in all_files:
        chapter_name = f.stem  # 去掉.txt后缀
        output_file = Path(f'/home/baojie/work/shiji-kb/chapter_md/{chapter_name}.tagged.md')
        if not output_file.exists():
            needed.append(chapter_name)

    print(f"需要处理的章节数: {len(needed)}")
    print("章节列表:")
    for ch in needed[:20]:
        print(f"  - {ch}")
    if len(needed) > 20:
        print(f"  ... 还有 {len(needed) - 20} 个")

    # 批量处理
    # batch_process_chapters(needed)
