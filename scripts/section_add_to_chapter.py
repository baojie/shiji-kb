#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为单个章节添加有意义的小节标题

使用方法：
    python add_sections_to_chapter.py chapter_md/061_伯夷列传.tagged.md
"""

import re
import sys
from pathlib import Path


def read_chapter(md_file):
    """读取章节内容"""
    return md_file.read_text(encoding='utf-8')


def clean_text(text):
    """清理实体标注符号（v2.1 格式）"""
    # 12种对称类型：〖X content〗 → content
    text = re.sub(r'〖[@=;%&\'^~•!#\+\$\?\{\:\[\_]([^〖〗\n]+?)〗', r'\1', text)
    return text


def extract_paragraphs(content):
    """提取段落及其内容"""
    lines = content.split('\n')
    paragraphs = []
    current_para = {'num': '', 'content': []}

    for line in lines:
        # 匹配段落编号
        para_match = re.match(r'\[(\d+(?:\.\d+)*)\]\s*(.+)', line)
        if para_match:
            if current_para['num']:
                paragraphs.append(current_para)
            current_para = {
                'num': para_match.group(1),
                'content': [para_match.group(2)]
            }
        elif current_para['num'] and line.strip():
            current_para['content'].append(line.strip())

    if current_para['num']:
        paragraphs.append(current_para)

    return paragraphs


def display_chapter_for_sectioning(md_file):
    """显示章节内容，供人工添加小节标题"""
    content = read_chapter(md_file)
    paragraphs = extract_paragraphs(content)

    print("=" * 80)
    print(f"章节: {md_file.stem.replace('.tagged', '')}")
    print("=" * 80)
    print(f"总段落数: {len(paragraphs)}")
    print("\n" + "=" * 80)
    print("段落预览（前30段）：")
    print("=" * 80)

    for i, para in enumerate(paragraphs[:30], 1):
        clean_content = clean_text(' '.join(para['content']))
        preview = clean_content[:80] + '...' if len(clean_content) > 80 else clean_content
        print(f"\n[{para['num']}] {preview}")

        # 每10段提示一次可能的分节点
        if i % 10 == 0:
            print("\n" + "-" * 80)
            print(f"💡 建议在此处添加小节标题（第{i}段）")
            print("-" * 80)

    if len(paragraphs) > 30:
        print(f"\n... 还有 {len(paragraphs) - 30} 段")

    print("\n" + "=" * 80)
    print("建议的小节数量:", max(2, len(paragraphs) // 10))
    print("=" * 80)


def suggest_section_positions(md_file):
    """建议小节插入位置"""
    content = read_chapter(md_file)
    paragraphs = extract_paragraphs(content)

    if len(paragraphs) < 10:
        return []

    # 每8-12段一个小节
    section_size = 10
    positions = []

    for i in range(0, len(paragraphs), section_size):
        if i > 0:  # 跳过第一段（通常是标题后）
            positions.append({
                'para_num': paragraphs[i]['num'],
                'para_index': i,
                'preview': clean_text(' '.join(paragraphs[i]['content'][:2]))[:60]
            })

    return positions


def insert_section_header(md_file, para_num, section_title, dry_run=True):
    """在指定段落前插入小节标题"""
    content = read_chapter(md_file)
    lines = content.split('\n')

    # 找到段落位置
    new_lines = []
    inserted = False

    for line in lines:
        # 检查是否是目标段落
        if re.match(rf'\[{re.escape(para_num)}\]', line):
            # 在此之前插入小节标题
            new_lines.append(f'\n## {section_title}\n')
            inserted = True
        new_lines.append(line)

    if not inserted:
        print(f"⚠️  警告: 未找到段落 [{para_num}]")
        return False

    new_content = '\n'.join(new_lines)

    if dry_run:
        print(f"✓ 预览: 将在段落 [{para_num}] 前插入:")
        print(f"  ## {section_title}")
        return True
    else:
        # 实际写入
        md_file.write_text(new_content, encoding='utf-8')
        print(f"✓ 已插入小节: {section_title} (段落 [{para_num}] 前)")
        return True


def main():
    if len(sys.argv) < 2:
        print("用法: python add_sections_to_chapter.py <章节文件>")
        print("示例: python add_sections_to_chapter.py chapter_md/061_伯夷列传.tagged.md")
        sys.exit(1)

    md_file = Path(sys.argv[1])

    if not md_file.exists():
        print(f"错误: 文件不存在: {md_file}")
        sys.exit(1)

    # 显示章节内容
    display_chapter_for_sectioning(md_file)

    # 显示建议的分节位置
    print("\n" + "=" * 80)
    print("建议的分节位置:")
    print("=" * 80)

    positions = suggest_section_positions(md_file)
    for i, pos in enumerate(positions, 1):
        print(f"\n{i}. 段落 [{pos['para_num']}] 前")
        print(f"   内容预览: {pos['preview']}...")
        print(f"   建议标题: [需要人工确定]")

    print("\n" + "=" * 80)
    print("下一步:")
    print("=" * 80)
    print("1. 阅读上述内容，理解章节结构")
    print("2. 确定每个小节的主题")
    print("3. 使用以下命令添加小节标题:")
    print(f"   python add_sections_to_chapter.py {md_file} insert <段落号> <小节标题>")
    print("\n示例:")
    print(f"   python add_sections_to_chapter.py {md_file} insert 10 早年经历")


if __name__ == '__main__':
    main()
