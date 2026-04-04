#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取多音字上下文分析器

功能：
1. 提取每个多音字前后各2个汉字的上下文
2. 遇到标点符号则停止延展
3. 保存所有多音字的上下文信息供后续分析

用法：
    python extract_polyphone_contexts.py <多音字> [输出文件]
    python extract_polyphone_contexts.py --all  # 批量处理所有多音字
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import argparse

class PolyphoneContextExtractor:
    """多音字上下文提取器"""

    def __init__(self, text_file: str = "archive/史记.简体.txt"):
        """初始化"""
        self.text_file = Path(text_file)
        if not self.text_file.exists():
            raise FileNotFoundError(f"文本文件不存在: {text_file}")

        with open(self.text_file, 'r', encoding='utf-8') as f:
            self.text = f.read()

        # 定义标点符号集合（中文和英文标点）
        self.punctuations = set('，。！？；：""''（）《》【】、·…—～,.!?;:"\'-()[]<>{}')

    def extract_context(self, char: str, max_left: int = 2, max_right: int = 2) -> List[Dict]:
        """
        提取指定字符的所有上下文

        Args:
            char: 要分析的多音字
            max_left: 左侧最多延展汉字数（遇标点停止）
            max_right: 右侧最多延展汉字数（遇标点停止）

        Returns:
            包含所有出现位置和上下文的列表
        """
        contexts = []

        # 找到所有出现位置
        for match in re.finditer(re.escape(char), self.text):
            pos = match.start()

            # 提取左侧上下文（向左延展，遇标点或开头停止）
            left_context = ""
            left_pos = pos - 1
            left_count = 0

            while left_pos >= 0 and left_count < max_left:
                c = self.text[left_pos]

                # 遇到标点符号则停止
                if c in self.punctuations:
                    break

                # 只收集汉字
                if '\u4e00' <= c <= '\u9fff':
                    left_context = c + left_context
                    left_count += 1

                left_pos -= 1

            # 提取右侧上下文（向右延展，遇标点或结尾停止）
            right_context = ""
            right_pos = pos + 1
            right_count = 0

            while right_pos < len(self.text) and right_count < max_right:
                c = self.text[right_pos]

                # 遇到标点符号则停止
                if c in self.punctuations:
                    break

                # 只收集汉字
                if '\u4e00' <= c <= '\u9fff':
                    right_context += c
                    right_count += 1

                right_pos += 1

            # 记录上下文信息
            context_info = {
                'position': pos,
                'left': left_context,
                'char': char,
                'right': right_context,
                'full': left_context + char + right_context,
                'left_count': left_count,
                'right_count': right_count
            }

            contexts.append(context_info)

        return contexts

    def analyze_contexts(self, contexts: List[Dict]) -> Dict:
        """
        分析上下文，统计词组模式

        Args:
            contexts: 上下文列表

        Returns:
            分析结果字典
        """
        # 统计不同长度的上下文模式
        full_patterns = defaultdict(int)
        left_patterns = defaultdict(int)
        right_patterns = defaultdict(int)

        for ctx in contexts:
            full = ctx['full']
            left = ctx['left']
            right = ctx['right']
            char = ctx['char']

            # 统计完整上下文
            if full:
                full_patterns[full] += 1

            # 统计左侧模式
            if left:
                left_patterns[left + char] += 1

            # 统计右侧模式
            if right:
                right_patterns[char + right] += 1

        return {
            'total_count': len(contexts),
            'full_patterns': dict(sorted(full_patterns.items(), key=lambda x: x[1], reverse=True)),
            'left_patterns': dict(sorted(left_patterns.items(), key=lambda x: x[1], reverse=True)),
            'right_patterns': dict(sorted(right_patterns.items(), key=lambda x: x[1], reverse=True))
        }

    def save_contexts(self, char: str, contexts: List[Dict], output_file: Path):
        """
        保存上下文数据到JSON文件

        Args:
            char: 多音字
            contexts: 上下文列表
            output_file: 输出文件路径
        """
        analysis = self.analyze_contexts(contexts)

        output_data = {
            'char': char,
            'total_count': len(contexts),
            'analysis': analysis,
            'contexts': contexts[:100]  # 只保存前100个示例，避免文件过大
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已保存 {char} 的上下文数据到: {output_file}")
        print(f"  总计出现: {len(contexts)} 次")
        print(f"  完整模式数: {len(analysis['full_patterns'])} 种")

    def save_contexts_txt(self, char: str, contexts: List[Dict], output_file: Path):
        """
        保存上下文数据到文本文件（便于人工审核）

        Args:
            char: 多音字
            contexts: 上下文列表
            output_file: 输出文件路径
        """
        analysis = self.analyze_contexts(contexts)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {char} - 上下文分析\n\n")
            f.write(f"**总计出现次数**: {len(contexts)}\n")
            f.write(f"**完整上下文模式数**: {len(analysis['full_patterns'])}\n\n")

            f.write("---\n\n")
            f.write("## 完整上下文模式（按频率排序）\n\n")
            f.write("| 上下文 | 出现次数 | 说明 |\n")
            f.write("|--------|---------|------|\n")

            for pattern, count in list(analysis['full_patterns'].items())[:50]:
                f.write(f"| {pattern} | {count} | |\n")

            f.write("\n---\n\n")
            f.write("## 左侧模式（前缀+字）\n\n")
            f.write("| 模式 | 出现次数 |\n")
            f.write("|------|----------|\n")

            for pattern, count in list(analysis['left_patterns'].items())[:30]:
                f.write(f"| {pattern} | {count} |\n")

            f.write("\n---\n\n")
            f.write("## 右侧模式（字+后缀）\n\n")
            f.write("| 模式 | 出现次数 |\n")
            f.write("|------|----------|\n")

            for pattern, count in list(analysis['right_patterns'].items())[:30]:
                f.write(f"| {pattern} | {count} |\n")

            f.write("\n---\n\n")
            f.write("## 示例上下文（前50个）\n\n")
            f.write("| # | 左侧 | 字 | 右侧 | 完整上下文 |\n")
            f.write("|---|------|-----|------|------------|\n")

            for i, ctx in enumerate(contexts[:50], 1):
                left = ctx['left'] or '-'
                right = ctx['right'] or '-'
                full = ctx['full']
                f.write(f"| {i} | {left} | {char} | {right} | {full} |\n")

        print(f"✓ 已保存 {char} 的文本分析到: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='提取多音字上下文')
    parser.add_argument('char', nargs='?', help='要分析的多音字')
    parser.add_argument('output', nargs='?', help='输出文件路径')
    parser.add_argument('--all', action='store_true', help='批量处理所有多音字')
    parser.add_argument('--batch', help='批量处理指定多音字列表（逗号分隔）')
    parser.add_argument('--left', type=int, default=2, help='左侧延展汉字数（默认2）')
    parser.add_argument('--right', type=int, default=2, help='右侧延展汉字数（默认2）')

    args = parser.parse_args()

    extractor = PolyphoneContextExtractor()

    # 批量处理模式
    if args.all or args.batch:
        # 从polyphone_list.py导入多音字列表
        import sys
        sys.path.append(str(Path(__file__).parent))
        from polyphone_list import HIGH_FREQUENCY, MEDIUM_FREQUENCY, ANALYZED

        # 确定要处理的字符列表
        if args.all:
            chars_to_process = HIGH_FREQUENCY + MEDIUM_FREQUENCY
        else:
            chars_to_process = args.batch.split(',')

        # 创建输出目录
        output_dir = Path('data/polyphone_contexts')
        output_dir.mkdir(exist_ok=True)

        print(f"开始批量处理 {len(chars_to_process)} 个多音字...")

        for char in chars_to_process:
            char = char.strip()
            try:
                contexts = extractor.extract_context(char, args.left, args.right)

                # 保存JSON格式
                json_file = output_dir / f"{char}_contexts.json"
                extractor.save_contexts(char, contexts, json_file)

                # 保存文本格式
                txt_file = output_dir / f"{char}_contexts.txt"
                extractor.save_contexts_txt(char, contexts, txt_file)

            except Exception as e:
                print(f"✗ 处理 {char} 时出错: {e}")

        print(f"\n✓ 批量处理完成！输出目录: {output_dir}")
        return

    # 单字符处理模式
    if not args.char:
        parser.print_help()
        return

    char = args.char
    contexts = extractor.extract_context(char, args.left, args.right)

    if not contexts:
        print(f"未找到字符 '{char}' 的出现记录")
        return

    # 确定输出文件路径
    if args.output:
        json_file = Path(args.output)
        txt_file = json_file.with_suffix('.txt')
    else:
        output_dir = Path('data/polyphone_contexts')
        output_dir.mkdir(exist_ok=True)
        json_file = output_dir / f"{char}_contexts.json"
        txt_file = output_dir / f"{char}_contexts.txt"

    # 保存结果
    extractor.save_contexts(char, contexts, json_file)
    extractor.save_contexts_txt(char, contexts, txt_file)

    print(f"\n示例上下文（前10个）：")
    for i, ctx in enumerate(contexts[:10], 1):
        print(f"{i}. {ctx['full']}")

if __name__ == '__main__':
    main()
