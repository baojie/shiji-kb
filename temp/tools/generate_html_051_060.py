#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成世家051-060章节的HTML文件
"""

import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from render_shiji_html import markdown_to_html

CHAPTER_MD_DIR = "/home/baojie/work/shiji-kb/chapter_md"

# 需要处理的章节列表
CHAPTERS = [
    "051_荆燕世家",
    "052_齐悼惠王世家",
    "053_萧相国世家",
    "054_曹相国世家",
    "055_留侯世家",
    "056_陈丞相世家",
    "057_绛侯周勃世家",
    "058_梁孝王世家",
    "059_五宗世家",
    "060_三王世家"
]

def main():
    """主函数"""
    print("\n" + "="*60)
    print("批量生成世家051-060章节HTML文件")
    print("="*60)

    success_count = 0
    fail_count = 0

    for chapter in CHAPTERS:
        md_file = Path(CHAPTER_MD_DIR) / f"{chapter}.tagged.md"

        if not md_file.exists():
            print(f"✗ 文件不存在: {md_file}")
            fail_count += 1
            continue

        try:
            print(f"\n处理: {chapter}")
            output_file = md_file.with_suffix('.html')
            markdown_to_html(str(md_file), str(output_file))
            print(f"✓ 已生成: {output_file}")
            success_count += 1
        except Exception as e:
            print(f"✗ 生成失败: {chapter}")
            print(f"  错误: {e}")
            fail_count += 1

    print("\n" + "="*60)
    print(f"生成完成统计:")
    print(f"  成功: {success_count} 个章节")
    print(f"  失败: {fail_count} 个章节")
    print("="*60)

if __name__ == "__main__":
    main()
