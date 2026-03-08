#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史记096-110列传章节实体标注处理脚本
处理范围：096_张丞相列传 至 110_匈奴列传（共15个章节）
"""

import re
import os

# 章节列表（注意101已标注，跳过）
CHAPTERS = [
    "096_张丞相列传",
    "097_郦生陆贾列传",
    "098_傅靳蒯成列传",
    "099_刘敬叔孙通列传",
    "100_季布栾布列传",
    # "101_袁盎晁错列传",  # 已标注
    "102_张释之冯唐列传",
    "103_万石张叔列传",
    "104_田叔列传",
    "105_扁鹊仓公列传",
    "106_吴王濞列传",
    "107_魏其武安侯列传",
    "108_韩长孺列传",
    "109_李将军列传",
    "110_匈奴列传"
]

SOURCE_DIR = "/home/baojie/work/shiji-kb/docs/original_text"
OUTPUT_DIR = "/home/baojie/work/shiji-kb/chapter_md"

def process_chapter(chapter_name):
    """处理单个章节的实体标注"""
    source_file = f"{SOURCE_DIR}/{chapter_name}.txt"
    output_file = f"{OUTPUT_DIR}/{chapter_name}.tagged.md"

    print(f"\n正在处理: {chapter_name}")

    # 读取原文
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 这里需要实现具体的标注逻辑
    # 由于实体标注需要深度理解文本，建议手工处理
    # 本脚本主要用于框架搭建

    return content

def main():
    """主函数"""
    print("开始处理史记096-110列传章节实体标注")
    print(f"共{len(CHAPTERS)}个章节")

    for chapter in CHAPTERS:
        try:
            process_chapter(chapter)
        except Exception as e:
            print(f"处理 {chapter} 时出错: {e}")

    print("\n处理完成！")

if __name__ == "__main__":
    main()
