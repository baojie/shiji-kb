#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从上下文数据中抽象发音规则

功能：
1. 读取上下文JSON文件
2. 抽象出词组和单字发音规则
3. 人工标注发音后，记录每个字在词/上下文中的发音
4. 对比pinyin-pro，只保留pinyin-pro无法正确处理的发音

用法：
    python analyze_pronunciation_rules.py <多音字>
    python analyze_pronunciation_rules.py --all  # 批量处理
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set
import argparse

class PronunciationRuleAnalyzer:
    """发音规则分析器"""

    def __init__(self, context_dir: str = "data/polyphone_contexts"):
        """初始化"""
        self.context_dir = Path(context_dir)
        if not self.context_dir.exists():
            raise FileNotFoundError(f"上下文目录不存在: {context_dir}")

    def load_context_data(self, char: str) -> Dict:
        """加载指定字符的上下文数据"""
        json_file = self.context_dir / f"{char}_contexts.json"

        if not json_file.exists():
            raise FileNotFoundError(f"上下文文件不存在: {json_file}")

        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_word_patterns(self, data: Dict, min_freq: int = 3) -> Dict[str, int]:
        """
        从上下文中提取词组模式

        规则：
        1. 优先提取高频完整上下文作为词组
        2. 单字上下文需要保留作为语境标注
        3. 按频率降序返回

        Args:
            data: 上下文数据
            min_freq: 最低频率阈值

        Returns:
            {词组: 出现次数}
        """
        char = data['char']
        analysis = data['analysis']

        # 提取词组候选
        word_candidates = {}

        # 从完整上下文模式中提取
        full_patterns = analysis.get('full_patterns', {})

        for pattern, count in full_patterns.items():
            if count < min_freq:
                continue

            # 分析模式长度和字的位置
            if len(pattern) >= 2:
                # 2字词：直接作为词组
                if len(pattern) == 2:
                    word_candidates[pattern] = count

                # 3字词：判断中心字位置
                elif len(pattern) == 3:
                    # 如果多音字在中间或边缘，都可能是词组
                    if char in pattern:
                        word_candidates[pattern] = count

                # 4字词：可能是成语或固定搭配
                elif len(pattern) == 4:
                    word_candidates[pattern] = count

                # 5字或更长：可能是短语，暂时保留高频的
                elif len(pattern) >= 5 and count >= min_freq * 2:
                    word_candidates[pattern] = count

        # 按频率排序
        return dict(sorted(word_candidates.items(), key=lambda x: x[1], reverse=True))

    def classify_patterns(self, word_patterns: Dict[str, int], char: str) -> Dict[str, List[Tuple[str, int]]]:
        """
        将词组模式分类

        分类：
        1. 固定词组（2-3字高频词）
        2. 成语短语（4字词）
        3. 上下文模式（5字及以上，或单字+上下文）

        Returns:
            {类别: [(模式, 频率), ...]}
        """
        fixed_words = []      # 固定词组
        idioms = []          # 成语短语
        context_patterns = []  # 上下文模式

        for pattern, count in word_patterns.items():
            length = len(pattern)

            if length == 2 or length == 3:
                fixed_words.append((pattern, count))
            elif length == 4:
                idioms.append((pattern, count))
            else:
                context_patterns.append((pattern, count))

        return {
            'fixed_words': fixed_words,
            'idioms': idioms,
            'context_patterns': context_patterns
        }

    def generate_pronunciation_template(self, char: str, classified: Dict) -> str:
        """
        生成发音标注模板

        输出Markdown格式，供人工标注发音
        """
        lines = [
            f"# {char} - 发音标注模板\n",
            "**说明**: 请为每个词组/上下文标注正确的发音（拼音）\n",
            "**格式**: `词组 | 拼音 | 说明`\n",
            "\n---\n",
        ]

        # 固定词组
        if classified['fixed_words']:
            lines.append("## 固定词组（2-3字）\n")
            lines.append("| 词组 | 拼音 | 频率 | 说明 |\n")
            lines.append("|------|------|------|------|\n")

            for word, count in classified['fixed_words'][:50]:
                lines.append(f"| {word} | _____ | {count} |  |\n")

            lines.append("\n")

        # 成语短语
        if classified['idioms']:
            lines.append("## 成语短语（4字）\n")
            lines.append("| 词组 | 拼音 | 频率 | 说明 |\n")
            lines.append("|------|------|------|------|\n")

            for word, count in classified['idioms'][:30]:
                lines.append(f"| {word} | _____ | {count} |  |\n")

            lines.append("\n")

        # 上下文模式
        if classified['context_patterns']:
            lines.append("## 上下文模式（需要保留上下文）\n")
            lines.append("| 上下文 | 拼音 | 频率 | 说明 |\n")
            lines.append("|--------|------|------|------|\n")

            for pattern, count in classified['context_patterns'][:30]:
                lines.append(f"| {pattern} | _____ | {count} |  |\n")

            lines.append("\n")

        lines.append("---\n\n")
        lines.append("## 标注说明\n\n")
        lines.append("1. 在「拼音」列填入该词组中多音字的正确读音（如 wáng, wàng）\n")
        lines.append("2. 如果是固定词组，标注后将加入全局拼音词表\n")
        lines.append("3. 如果是上下文相关的单字发音，将作为章节补充词表\n")
        lines.append("4. 在「说明」列可以补充词义或用法说明\n")

        return ''.join(lines)

    def save_template(self, char: str, template: str, output_file: Path):
        """保存标注模板"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(template)

        print(f"✓ 已生成 {char} 的发音标注模板: {output_file}")

    def parse_annotated_template(self, template_file: Path) -> Dict:
        """
        解析已标注的模板文件

        Returns:
            {
                'char': 字符,
                'fixed_words': {词组: 拼音},
                'idioms': {词组: 拼音},
                'context_patterns': {模式: 拼音}
            }
        """
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取字符
        char_match = re.search(r'^# (\S+) - 发音标注模板', content, re.MULTILINE)
        if not char_match:
            raise ValueError("无法从模板中提取字符")

        char = char_match.group(1)

        result = {
            'char': char,
            'fixed_words': {},
            'idioms': {},
            'context_patterns': {}
        }

        # 解析固定词组表格
        fixed_section = re.search(
            r'## 固定词组.*?\n\|.*?\n\|.*?\n((?:\|.*?\n)+)',
            content,
            re.DOTALL
        )

        if fixed_section:
            for line in fixed_section.group(1).strip().split('\n'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4 and parts[1] and parts[2] and parts[2] != '_____':
                    word = parts[1]
                    pinyin = parts[2]
                    result['fixed_words'][word] = pinyin

        # 解析成语短语表格
        idiom_section = re.search(
            r'## 成语短语.*?\n\|.*?\n\|.*?\n((?:\|.*?\n)+)',
            content,
            re.DOTALL
        )

        if idiom_section:
            for line in idiom_section.group(1).strip().split('\n'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4 and parts[1] and parts[2] and parts[2] != '_____':
                    word = parts[1]
                    pinyin = parts[2]
                    result['idioms'][word] = pinyin

        # 解析上下文模式表格
        context_section = re.search(
            r'## 上下文模式.*?\n\|.*?\n\|.*?\n((?:\|.*?\n)+)',
            content,
            re.DOTALL
        )

        if context_section:
            for line in context_section.group(1).strip().split('\n'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4 and parts[1] and parts[2] and parts[2] != '_____':
                    pattern = parts[1]
                    pinyin = parts[2]
                    result['context_patterns'][pattern] = pinyin

        return result

    def generate_pronunciation_dict(self, annotated_data: Dict) -> Dict:
        """
        从已标注数据生成发音词典

        Returns:
            {
                'global_dict': {词组: {拼音, 类型}},  # 加入全局拼音词表
                'context_dict': {模式: {拼音, 类型}}   # 作为章节补充
            }
        """
        char = annotated_data['char']

        global_dict = {}
        context_dict = {}

        # 固定词组 → 全局词表
        for word, pinyin in annotated_data.get('fixed_words', {}).items():
            global_dict[word] = {
                'pinyin': pinyin,
                'type': 'fixed_word',
                'char': char
            }

        # 成语短语 → 全局词表
        for word, pinyin in annotated_data.get('idioms', {}).items():
            global_dict[word] = {
                'pinyin': pinyin,
                'type': 'idiom',
                'char': char
            }

        # 上下文模式 → 章节补充词表
        for pattern, pinyin in annotated_data.get('context_patterns', {}).items():
            context_dict[pattern] = {
                'pinyin': pinyin,
                'type': 'context',
                'char': char
            }

        return {
            'global_dict': global_dict,
            'context_dict': context_dict
        }

def main():
    parser = argparse.ArgumentParser(description='分析多音字发音规则')
    parser.add_argument('char', nargs='?', help='要分析的多音字')
    parser.add_argument('--all', action='store_true', help='批量处理所有多音字')
    parser.add_argument('--min-freq', type=int, default=3, help='最低频率阈值（默认3）')
    parser.add_argument('--parse', help='解析已标注的模板文件')

    args = parser.parse_args()

    analyzer = PronunciationRuleAnalyzer()

    # 解析已标注模板模式
    if args.parse:
        template_file = Path(args.parse)
        annotated = analyzer.parse_annotated_template(template_file)

        print(f"✓ 解析完成: {annotated['char']}")
        print(f"  固定词组: {len(annotated['fixed_words'])} 个")
        print(f"  成语短语: {len(annotated['idioms'])} 个")
        print(f"  上下文模式: {len(annotated['context_patterns'])} 个")

        # 生成发音词典
        pron_dict = analyzer.generate_pronunciation_dict(annotated)

        # 保存结果
        output_file = template_file.with_suffix('.dict.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pron_dict, f, ensure_ascii=False, indent=2)

        print(f"✓ 已保存发音词典: {output_file}")
        return

    # 生成标注模板模式
    if not args.char and not args.all:
        parser.print_help()
        return

    chars_to_process = []

    if args.all:
        # 从上下文目录获取所有已提取的字符
        for json_file in analyzer.context_dir.glob("*_contexts.json"):
            char = json_file.stem.replace('_contexts', '')
            chars_to_process.append(char)
    else:
        chars_to_process = [args.char]

    # 创建输出目录
    output_dir = Path('data/pronunciation_templates')
    output_dir.mkdir(exist_ok=True)

    for char in chars_to_process:
        try:
            # 加载上下文数据
            data = analyzer.load_context_data(char)

            # 提取词组模式
            word_patterns = analyzer.extract_word_patterns(data, args.min_freq)

            if not word_patterns:
                print(f"⚠ {char}: 未找到足够频率的词组模式（阈值={args.min_freq}）")
                continue

            # 分类词组
            classified = analyzer.classify_patterns(word_patterns, char)

            # 生成标注模板
            template = analyzer.generate_pronunciation_template(char, classified)

            # 保存模板
            template_file = output_dir / f"{char}_pronunciation.md"
            analyzer.save_template(char, template, template_file)

            print(f"  固定词组: {len(classified['fixed_words'])} 个")
            print(f"  成语短语: {len(classified['idioms'])} 个")
            print(f"  上下文模式: {len(classified['context_patterns'])} 个")

        except Exception as e:
            print(f"✗ 处理 {char} 时出错: {e}")

    print(f"\n✓ 批量处理完成！输出目录: {output_dir}")

if __name__ == '__main__':
    main()
