#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《史记》多音字统计分析脚本

功能：
1. 统计指定多音字在《史记》中的出现次数
2. 提取上下文进行分类分析
3. 生成标准化的分析文档（Markdown格式）
"""

import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

# 多音字定义（从报告中提取的高频和中频多音字）
POLYPHONE_CHARS = {
    # 高频（>1000次）
    '王': ['wáng', 'wàng'],
    '将': ['jiāng', 'jiàng'],
    '相': ['xiāng', 'xiàng'],
    '行': ['xíng', 'háng'],
    '数': ['shù', 'shǔ', 'shuò'],
    '长': ['cháng', 'zhǎng'],

    # 中高频（500-1000次）
    '与': ['yǔ', 'yù', 'yú'],
    '为': ['wéi', 'wèi'],
    '使': ['shǐ', 'shì'],
    '少': ['shǎo', 'shào'],

    # 中频（100-500次）
    '骑': ['qí', 'jì'],
    '朝': ['zhāo', 'cháo'],
    '会': ['huì', 'kuài'],
    '乘': ['chéng', 'shèng'],
    '好': ['hǎo', 'hào'],
    '说': ['shuō', 'shuì', 'yuè'],
    '乐': ['lè', 'yuè', 'yào'],
    '间': ['jiān', 'jiàn'],
    '召': ['zhào', 'shào'],
    '降': ['jiàng', 'xiáng'],
    '更': ['gēng', 'gèng'],
    '传': ['chuán', 'zhuàn'],
    '率': ['shuài', 'lǜ'],
    '过': ['guò', 'guō'],
    '还': ['hái', 'huán'],
    '重': ['zhòng', 'chóng'],
    '应': ['yīng', 'yìng'],
    '便': ['biàn', 'pián'],
    '宿': ['sù', 'xiǔ', 'xiù'],
    '处': ['chù', 'chǔ'],
    '差': ['chà', 'chāi', 'cī', 'chài'],
    '殷': ['yīn', 'yān'],
    '系': ['xì', 'jì'],
    '解': ['jiě', 'jiè', 'xiè'],
    '种': ['zhǒng', 'zhòng'],
    '称': ['chēng', 'chèn', 'chèng'],
    '从': ['cóng', 'zòng'],
    '冠': ['guān', 'guàn'],
    '当': ['dāng', 'dàng'],
    '度': ['dù', 'duó'],
    '分': ['fēn', 'fèn'],
    '复': ['fù', 'fú'],
    '供': ['gōng', 'gòng'],
    '假': ['jiǎ', 'jià'],
    '禁': ['jīn', 'jìn'],
    '觉': ['jué', 'jiào'],
    '落': ['luò', 'là', 'lào'],
    '没': ['méi', 'mò'],
    '蒙': ['méng', 'mēng', 'měng'],
    '难': ['nán', 'nàn'],
    '宁': ['níng', 'nìng', 'zhù'],
    '强': ['qiáng', 'qiǎng', 'jiàng'],
    '塞': ['sāi', 'sè', 'sài'],
    '舍': ['shě', 'shè'],
    '胜': ['shèng', 'shēng'],
    '识': ['shí', 'zhì'],
    '恶': ['è', 'wù', 'ě'],
    '要': ['yāo', 'yào'],
    '曾': ['céng', 'zēng'],
    '正': ['zhèng', 'zhēng'],
    '只': ['zhī', 'zhǐ'],
    '属': ['shǔ', 'zhǔ'],

    # 古汉语特有
    '校': ['xiào', 'jiào'],
    '句': ['jù', 'gōu'],
    '隗': ['wěi', 'kuí'],
    '仇': ['chóu', 'qiú'],
    '区': ['qū', 'ōu'],
    '华': ['huá', 'huà', 'huā'],
    '单': ['dān', 'shàn', 'chán'],
    '柏': ['bǎi', 'bó', 'bò'],
    '卜': ['bǔ', 'bo'],
    '泊': ['bó', 'pō'],

    # 已完成分析
    '燕': ['yān', 'yàn'],
    '夫': ['fū', 'fú'],
    '和': ['hé', 'hè', 'huó', 'huò'],
    '且': ['qiě', 'jū'],
    '遗': ['yí', 'wèi'],
    '中': ['zhōng', 'zhòng'],
}

class PolyphoneAnalyzer:
    def __init__(self, text_file):
        """初始化分析器"""
        self.text_file = Path(text_file)
        with open(self.text_file, 'r', encoding='utf-8') as f:
            self.text = f.read()

    def count_char(self, char):
        """统计某个字符的出现次数"""
        return self.text.count(char)

    def extract_contexts(self, char, context_length=10):
        """提取某个字符的上下文"""
        contexts = []
        for match in re.finditer(re.escape(char), self.text):
            start = max(0, match.start() - context_length)
            end = min(len(self.text), match.end() + context_length)
            context = self.text[start:end]
            contexts.append({
                'before': self.text[start:match.start()],
                'char': char,
                'after': self.text[match.end():end],
                'full': context,
                'position': match.start()
            })
        return contexts

    def is_chinese_char(self, char):
        """判断是否为汉字"""
        return '\u4e00' <= char <= '\u9fff'

    def find_common_patterns(self, char, min_count=1):
        """查找包含该字符的常见词组模式（排除标点符号）"""
        patterns = defaultdict(int)

        # 2字词组（字在前，后一个字必须是汉字）
        for match in re.finditer(f'{re.escape(char)}([\u4e00-\u9fff])', self.text):
            pattern = match.group()
            patterns[pattern] += 1

        # 2字词组（字在后，前一个字必须是汉字）
        for match in re.finditer(f'([\u4e00-\u9fff]){re.escape(char)}', self.text):
            pattern = match.group()
            patterns[pattern] += 1

        # 3字词组（字在中间）
        for match in re.finditer(f'([\u4e00-\u9fff]){re.escape(char)}([\u4e00-\u9fff])', self.text):
            pattern = match.group()
            patterns[pattern] += 1

        # 3字词组（字在开头）
        for match in re.finditer(f'{re.escape(char)}([\u4e00-\u9fff]){{2}}', self.text):
            pattern = match.group()
            patterns[pattern] += 1

        # 3字词组（字在结尾）
        for match in re.finditer(f'([\u4e00-\u9fff]){{2}}{re.escape(char)}', self.text):
            pattern = match.group()
            patterns[pattern] += 1

        # 4字词组（字在开头）
        for match in re.finditer(f'{re.escape(char)}([\u4e00-\u9fff]){{3}}', self.text):
            pattern = match.group()
            patterns[pattern] += 1

        # 4字词组（字在第二位）
        for match in re.finditer(f'([\u4e00-\u9fff]){re.escape(char)}([\u4e00-\u9fff]){{2}}', self.text):
            pattern = match.group()
            patterns[pattern] += 1

        # 过滤低频词组
        return {k: v for k, v in sorted(patterns.items(), key=lambda x: x[1], reverse=True) if v >= min_count}

    def analyze_char(self, char):
        """分析单个多音字"""
        total_count = self.count_char(char)
        contexts = self.extract_contexts(char, context_length=5)
        patterns = self.find_common_patterns(char, min_count=1)  # 统计所有词组，不设最小频率

        return {
            'char': char,
            'total_count': total_count,
            'pinyin_variants': POLYPHONE_CHARS.get(char, []),
            'contexts': contexts[:100],  # 最多返回100个上下文
            'common_patterns': patterns
        }

    def generate_report(self, char, output_file=None):
        """生成分析报告"""
        result = self.analyze_char(char)

        # 生成Markdown报告
        report = self._format_report(result)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"报告已保存到: {output_file}")

        return report

    def _format_report(self, result):
        """格式化报告为Markdown"""
        char = result['char']
        pinyin_variants = result['pinyin_variants']
        total_count = result['total_count']
        patterns = result['common_patterns']

        report = f"""# 多音字分析：{char}

## 基本信息

- **字**: {char}
- **主要读音**: {' / '.join(pinyin_variants)}
- **分析日期**: 自动生成
- **分析人**: analyze_polyphone_statistics.py
- **数据来源**: `corpus/shiji/史记.简体.txt`

## 出现次数统计

- **总出现次数**: {total_count}次

## 词组统计（按出现频率排序，仅汉字）

| 词组 | 出现次数 | 说明 |
|------|---------|------|
"""

        # 添加所有词组（按频率排序）
        for pattern, count in list(patterns.items())[:200]:  # 最多显示200个
            report += f"| {pattern} | {count} | 待分类 |\n"

        report += f"""
## 待完成工作

- [ ] 人工分类各词组的读音
- [ ] 统计各读音的使用频率
- [ ] 提取典型例句
- [ ] 确定词表处理方案
- [ ] 添加历史典故和语言学注释

## 分析说明

本报告由自动脚本生成，提供基础统计数据。需要人工审核和补充：

1. **读音分类**: 根据词组含义判断读音
2. **频率统计**: 计算各读音的使用占比
3. **词表方案**: 根据SKILL_01d v3.0原则确定处理方案
4. **例句补充**: 添加有代表性的例句

## 参考命令

```bash
# 提取所有上下文（用于人工分类）
grep -o ".{{5}}{char}.{{5}}" corpus/shiji/史记.简体.txt > /tmp/{char}_contexts.txt

# 统计特定词组
grep -o "{char}X" corpus/shiji/史记.简体.txt | sort | uniq -c | sort -rn
```
"""

        return report

    def batch_analyze(self, chars, output_dir='docs/pronunciation'):
        """批量分析多个多音字"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for char in chars:
            print(f"分析 '{char}' ...")
            result = self.analyze_char(char)
            results.append(result)

            # 生成报告文件
            pinyin = POLYPHONE_CHARS.get(char, ['unknown'])[0]
            output_file = output_dir / f"{char}_{pinyin}.draft.md"
            self.generate_report(char, output_file)

        return results


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python analyze_polyphone_statistics.py <字符> [输出文件]")
        print("示例: python analyze_polyphone_statistics.py 王 docs/pronunciation/王_wang.draft.md")
        sys.exit(1)

    char = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # 分析
    analyzer = PolyphoneAnalyzer('corpus/shiji/史记.简体.txt')
    report = analyzer.generate_report(char, output_file)

    if not output_file:
        print(report)


def batch_analyze_all():
    """批量分析所有待分析的多音字"""
    # 已完成分析的字
    analyzed = {'燕', '夫', '和', '且', '遗', '中'}

    # 待分析的高频字（>100次）
    high_priority = {
        '王', '将', '相', '行', '数', '长',  # >1000次
        '与', '为', '使', '少',              # 500-1000次
        '骑', '朝', '会', '乘', '好', '说', '乐', '间', '召'  # 100-500次
    }

    # 排除已完成的
    pending = high_priority - analyzed

    # 批量分析
    analyzer = PolyphoneAnalyzer('corpus/shiji/史记.简体.txt')
    results = analyzer.batch_analyze(list(pending))

    print(f"\n批量分析完成！共分析 {len(results)} 个多音字。")
    print("生成的草稿文件位于: docs/pronunciation/")
    print("\n待分析的多音字:")
    for char in sorted(pending):
        count = analyzer.count_char(char)
        print(f"  {char}: {count}次")


def batch_analyze_medium():
    """批量分析中低频多音字（50-1000次）"""
    # 已分析过的（包括草稿）
    already_done = {
        '燕', '夫', '和', '且', '遗', '中',  # 已完成
        '王', '将', '相', '行', '数', '长', '与', '为', '使', '少',  # 已有草稿
        '骑', '朝', '会', '乘', '好', '说', '乐', '间', '召'
    }

    # 中低频多音字
    medium_freq = {
        '过', '还', '重', '应', '便', '宿', '处', '差', '殷', '系',
        '解', '种', '称', '从', '冠', '当', '度', '分', '复', '供',
        '假', '禁', '觉', '落', '没', '蒙', '难', '宁', '强', '塞',
        '舍', '胜', '识', '恶', '要', '曾', '正', '只', '属', '累',
        '更', '传', '率', '降', '校', '句', '隗', '仇', '区', '华',
        '单', '柏', '卜', '泊', '见', '得', '几'
    }

    # 排除已分析的
    pending = medium_freq - already_done

    # 批量分析
    analyzer = PolyphoneAnalyzer('corpus/shiji/史记.简体.txt')

    # 先统计出现次数，过滤掉出现次数<50的
    char_counts = {}
    for char in pending:
        count = analyzer.count_char(char)
        if count >= 50:
            char_counts[char] = count

    # 按出现次数排序
    sorted_chars = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)

    print(f"\n找到 {len(sorted_chars)} 个中低频多音字（≥50次）：")
    for char, count in sorted_chars:
        print(f"  {char}: {count}次")

    # 批量生成草稿
    chars_to_analyze = [char for char, _ in sorted_chars]
    results = analyzer.batch_analyze(chars_to_analyze)

    print(f"\n批量分析完成！共分析 {len(results)} 个多音字。")
    print("生成的草稿文件位于: docs/pronunciation/")

    return sorted_chars


def batch_analyze_low():
    """批量分析低频多音字（所有剩余的多音字，不设最低频率）"""
    # 导入低频多音字列表
    from polyphone_list import LOW_FREQUENCY

    # 已分析过的所有字（包括草稿）
    already_analyzed_files = set()
    import os
    for filename in os.listdir('docs/pronunciation'):
        if filename.endswith('.draft.md') or (filename.endswith('.md') and '_' in filename):
            char = filename.split('_')[0]
            already_analyzed_files.add(char)

    # 从低频列表中提取字符
    low_freq_chars = {char for char, _ in LOW_FREQUENCY}

    # 排除已分析的
    pending = low_freq_chars - already_analyzed_files

    # 批量分析
    analyzer = PolyphoneAnalyzer('corpus/shiji/史记.简体.txt')

    # 统计所有字符的出现次数
    char_counts = {}
    for char in pending:
        count = analyzer.count_char(char)
        if count > 0:  # 只要出现过就统计
            char_counts[char] = count

    # 按出现次数排序
    sorted_chars = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)

    print(f"\n找到 {len(sorted_chars)} 个低频多音字（>0次）：")
    for char, count in sorted_chars[:20]:  # 显示前20个
        print(f"  {char}: {count}次")
    if len(sorted_chars) > 20:
        print(f"  ... 还有 {len(sorted_chars) - 20} 个")

    # 批量生成草稿
    chars_to_analyze = [char for char, _ in sorted_chars]
    results = analyzer.batch_analyze(chars_to_analyze)

    print(f"\n批量分析完成！共分析 {len(results)} 个多音字。")
    print("生成的草稿文件位于: docs/pronunciation/")

    return sorted_chars


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--batch':
            batch_analyze_all()
        elif sys.argv[1] == '--medium':
            batch_analyze_medium()
        elif sys.argv[1] == '--low':
            batch_analyze_low()
        else:
            main()
    else:
        main()
