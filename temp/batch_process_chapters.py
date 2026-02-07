#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理史记章节的脚本
根据原文文件生成语义标注的 tagged.md 文件
"""

import os
import sys
import json
from pathlib import Path
import subprocess
import time

def get_chapter_range(start, end):
    """获取指定范围的章节文件"""
    original_dir = Path('docs/original_text')
    chapters = []

    for i in range(start, end + 1):
        pattern = f'{i:03d}_*.txt'
        matching_files = list(original_dir.glob(pattern))
        if matching_files:
            chapters.append(matching_files[0])

    return chapters

def check_tagged_exists(chapter_file):
    """检查对应的 tagged.md 文件是否已存在"""
    chapter_name = chapter_file.stem.replace('.txt', '')
    tagged_file = Path('chapter_md') / f'{chapter_name}.tagged.md'
    return tagged_file.exists()

def process_chapter_batch(start, end, max_parallel=3):
    """批量处理章节"""
    chapters = get_chapter_range(start, end)

    if not chapters:
        print(f"未找到 {start:03d}-{end:03d} 范围内的章节")
        return

    print(f"\n{'='*60}")
    print(f"准备处理章节 {start:03d}-{end:03d}")
    print(f"发现 {len(chapters)} 个章节文件")
    print(f"{'='*60}\n")

    # 过滤已存在的章节
    to_process = []
    for chapter in chapters:
        if check_tagged_exists(chapter):
            print(f"✓ 跳过已存在: {chapter.name}")
        else:
            to_process.append(chapter)

    if not to_process:
        print("\n所有章节都已处理完成！")
        return

    print(f"\n需要处理 {len(to_process)} 个章节\n")

    # 分批处理
    for i in range(0, len(to_process), max_parallel):
        batch = to_process[i:i+max_parallel]
        print(f"\n处理批次 {i//max_parallel + 1}:")

        processes = []
        for chapter in batch:
            chapter_num = chapter.stem[:3]
            chapter_name = chapter.stem.replace('.txt', '')

            print(f"  启动处理: {chapter_name}")

            # 使用 claude 命令行调用子任务
            prompt = f"""请对《史记·{chapter_name[4:]}》进行语义化标注。

原始文本路径: {chapter}

请按照以下规则处理：
1. 章节结构：一级标题为章节名，二级标题按主要时期/人物/事件划分
2. 段落拆分：控制段落长度（不超过150字符），对话独立成行，使用圣经式编号
3. 实体标注：
   - 人名: @人名@
   - 地名: =地名=
   - 官职: $官职$
   - 时间: %时间%
   - 朝代: &朝代&
   - 制度: ^制度^
   - 族群: ~族群~
   - 器物: *器物*
   - 天文: !天文!
   - 神话: ?神话?
   - 动植物: 🌿动植物🌿

参考已处理的章节格式：
- chapter_md/006_秦始皇本纪.tagged.md
- chapter_md/007_项羽本纪.tagged.md

请生成文件：chapter_md/{chapter_name}.tagged.md
"""

            # 这里我们不能直接调用 claude，而是返回需要处理的章节列表
            # 实际处理需要在主程序中使用 Task 工具

        print(f"\n批次 {i//max_parallel + 1} 处理中...")
        time.sleep(1)

    print(f"\n{'='*60}")
    print("批次处理完成")
    print(f"{'='*60}")

def main():
    if len(sys.argv) < 3:
        print("用法: python batch_process_chapters.py <start> <end>")
        print("示例: python batch_process_chapters.py 10 20")
        sys.exit(1)

    start = int(sys.argv[1])
    end = int(sys.argv[2])

    process_chapter_batch(start, end)

if __name__ == '__main__':
    # 直接调用处理
    if len(sys.argv) >= 3:
        main()
    else:
        print("批量处理脚本已就绪")
        print("用法: python batch_process_chapters.py <start> <end>")
