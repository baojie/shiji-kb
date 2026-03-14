#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用AI NER批量提取史记章节中的生物实体
"""

import sys
from pathlib import Path

def extract_biology_from_chapter(chapter_file):
    """
    从章节文件中提取生物实体

    Args:
        chapter_file: 章节Markdown文件路径

    Returns:
        提取结果的字典
    """
    print(f"\n{'='*60}")
    print(f"分析文件: {chapter_file}")
    print(f"{'='*60}\n")

    # 这里应该调用AI模型进行NER分析
    # 由于是示例，这里只是打印提示信息
    print("请使用以下命令手动分析：")
    print(f"Task工具 - 分析 {chapter_file} 提取生物实体")
    print("\n任务描述：")
    print(f"""
请分析 {chapter_file} 文件，提取所有生物实体：

1. **动物实体**：
   - 具体动物名称（如：熊、罴、虎、马、牛、羊、龙、凤凰等）
   - 动物类别词（如：鸟兽、百兽、蟲蛾等）
   - 列出每个动物及其出现的段落编号和上下文

2. **植物实体**：
   - 具体植物名称（如：麻、菽、禾、麦、树等）
   - 植物类别词（如：百穀、草木、五穀等）
   - 列出每个植物及其出现的段落编号和上下文

3. **输出格式**：
   - 按动物、植物分类
   - 每个实体包含：名称、出现位置、上下文片段
   - 标注建议（如何用〖+〗标记）

请详细分析并给出完整清单。
    """)

def main():
    """主函数"""
    chapters = [
        'chapter_md/001_五帝本纪.tagged.md',
        'chapter_md/002_夏本纪.tagged.md',
        'chapter_md/003_殷本纪.tagged.md',
        'chapter_md/004_周本纪.tagged.md',
    ]

    print("史记生物实体提取工具")
    print("="*60)
    print("\n本工具用于批量提取史记章节中的生物实体")
    print("需要配合AI NER分析使用\n")

    for chapter in chapters:
        if Path(chapter).exists():
            extract_biology_from_chapter(chapter)
        else:
            print(f"警告: 文件不存在 - {chapter}")

    print("\n" + "="*60)
    print("提取完成！")
    print("\n建议使用Task工具逐个分析每个章节文件")
    print("然后将结果整理到以下位置：")
    print("  - kg/vocabularies/生物词典.md")
    print("  - FLORA_FAUNA_TAGGING_GUIDE.md (标注指南)")

if __name__ == '__main__':
    main()
