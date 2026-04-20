#!/usr/bin/env python3
"""
符号冲突检测工具

检查标点符号、标注符号、Markdown符号的冲突和误用。
基于 SKILL_01g_符号集合Disjoint原则.md

检查项：
1. 禁止半角标点（应使用全角）
2. 禁止直角引号「」『』（应使用弯引号" " ' '）
3. 标点在标注内部（应在外部）
4. Markdown在标注内部（应在外部）
5. 嵌套标注（应拍平）
6. 标注跨越标点（应分开）

使用方法：
    python scripts/lint_symbol_conflicts.py chapter_md/001*.md
    python scripts/lint_symbol_conflicts.py chapter_md/*.md
    python scripts/lint_symbol_conflicts.py chapter_md/*.md --check-types halfwidth,nested
    python scripts/lint_symbol_conflicts.py chapter_md/*.md --report logs/symbol_conflicts.txt
"""

import re
import sys
from pathlib import Path
from typing import List, Dict
from collections import defaultdict


class SymbolConflictLinter:
    """符号冲突检查器"""

    def __init__(self):
        self.issues = defaultdict(list)

    def check_halfwidth_punctuation(self, text: str, line_num: int = 0) -> List[Dict]:
        """检测半角标点符号"""
        issues = []
        # 先移除所有标注符号（〖TYPE content〗、⟦TYPE content⟧、〘※成语〙）
        # 这样标注内部的类型标记符号不会被误判为半角标点
        text_without_annotations = re.sub(r'〖[#@=;$%&\'^~•!\'+?{:\[_][^〗]*〗', '', text)
        text_without_annotations = re.sub(r'⟦[◈◉○◇][^⟧]*⟧', '', text_without_annotations)
        text_without_annotations = re.sub(r'〘※[^〘〙]*〙', '', text_without_annotations)
        # 移除紫色编号（段落编号）：[N] 或 [N.N] 或 [N.N.N] 等任意层级
        # 正则说明：\[ 后跟一个数字，然后是 0 个或多个 ".数字" 的组合，最后是 \]
        text_without_annotations = re.sub(r'\[\d+(?:\.\d+)*\]', '', text_without_annotations)
        # 移除Markdown自定义块标记 :::
        text_without_annotations = re.sub(r'^:::.*$', '', text_without_annotations, flags=re.MULTILINE)

        # 半角标点（注意：不包括竖线|，因为它用于消歧语法）
        halfwidth_puncts = r'[,.:;?!"\']'
        for match in re.finditer(halfwidth_puncts, text_without_annotations):
            # 获取在原始文本中的实际位置
            # 由于移除了标注，需要在原始文本中查找
            context_start = max(0, match.start()-20)
            context_end = match.end()+20
            context = text_without_annotations[context_start:context_end]

            issues.append({
                'type': 'halfwidth_punct',
                'char': match.group(),
                'pos': match.start(),
                'line': line_num,
                'context': context,
                'severity': 'high',
                'message': f'禁止使用半角标点 {match.group()}，应使用全角'
            })
        return issues

    def check_square_quotes(self, text: str, line_num: int = 0) -> List[Dict]:
        """检测直角引号（日文用法）"""
        issues = []
        square_quotes = r'[「」『』]'
        for match in re.finditer(square_quotes, text):
            issues.append({
                'type': 'square_quote',
                'char': match.group(),
                'pos': match.start(),
                'line': line_num,
                'context': text[max(0, match.start()-20):match.end()+20],
                'severity': 'high',
                'message': f'禁止使用直角引号 {match.group()}，应使用弯引号" " \' \''
            })
        return issues

    def check_punct_in_annotation(self, text: str, line_num: int = 0) -> List[Dict]:
        """检测标注符号内部是否包含标点"""
        issues = []
        # 实体标注：〖TYPE content〗
        # 类型标记：@ = ; # % & ' ^ ~ • ! ? + { : [ _ $
        pattern = r'〖[#@=;$%&\'^~•!\'+?{:\[_]([^〗]+)〗'
        for match in re.finditer(pattern, text):
            content = match.group(1)
            # 检查content中是否有标点（除了消歧分隔符|）
            # 全角标点：。，、；：？！""''《》——……
            puncts = r'[。，、；：？！""''《》—…]'
            punct_match = re.search(puncts, content)
            if punct_match:
                issues.append({
                    'type': 'punct_in_annotation',
                    'annotation': match.group(),
                    'pos': match.start(),
                    'line': line_num,
                    'punct': punct_match.group(),
                    'context': text[max(0, match.start()-20):match.end()+20],
                    'severity': 'high',
                    'message': f'标注内部不应包含标点符号 {punct_match.group()}，标点应在标注外部'
                })
        return issues

    def check_markdown_in_annotation(self, text: str, line_num: int = 0) -> List[Dict]:
        """检测标注符号内部是否包含Markdown语法"""
        issues = []
        pattern = r'〖[#@=;$%&\'^~•!\'+?{:\[_]([^〗]+)〗'
        for match in re.finditer(pattern, text):
            content = match.group(1)
            # 检查content中是否有Markdown符号
            # 注意：# 在标注内部是类型标记，不算冲突
            # 这里主要检查 * _ ` [ ] >
            markdown_symbols = r'[\*_`>\[\]]'
            md_match = re.search(markdown_symbols, content)
            if md_match:
                issues.append({
                    'type': 'markdown_in_annotation',
                    'annotation': match.group(),
                    'pos': match.start(),
                    'line': line_num,
                    'markdown': md_match.group(),
                    'context': text[max(0, match.start()-20):match.end()+20],
                    'severity': 'medium',
                    'message': f'标注内部不应包含Markdown语法 {md_match.group()}'
                })
        return issues

    def check_nested_annotation(self, text: str, line_num: int = 0) -> List[Dict]:
        """检测嵌套标注"""
        issues = []

        # 名词实体嵌套：〖TYPE ... 〖TYPE ... 〗 ... 〗
        noun_nested = re.compile(
            r'〖[#@=;$%&\'^~•!\'+?{:\[_][^〖〗]*?〖[#@=;$%&\'^~•!\'+?{:\[_][^〖〗]*?〗[^〖〗]*?〗'
        )

        # 动词标注嵌套：⟦TYPE ... ⟦或〖 ... ⟧或〗 ... ⟧
        verb_nested = re.compile(
            r'⟦[◈◉○◇][^⟦⟧〖〗]*?[⟦〖][^⟦⟧〖〗]*?[⟧〗][^⟦⟧〖〗]*?⟧'
        )

        for match in noun_nested.finditer(text):
            issues.append({
                'type': 'nested_annotation',
                'annotation': match.group(),
                'pos': match.start(),
                'line': line_num,
                'context': text[max(0, match.start()-20):match.end()+20],
                'severity': 'high',
                'message': '检测到嵌套标注，应拍平或选择正确类型'
            })

        for match in verb_nested.finditer(text):
            issues.append({
                'type': 'nested_annotation',
                'annotation': match.group(),
                'pos': match.start(),
                'line': line_num,
                'context': text[max(0, match.start()-20):match.end()+20],
                'severity': 'high',
                'message': '检测到嵌套标注，应拍平或选择正确类型'
            })

        return issues

    def check_annotation_across_punct(self, text: str, line_num: int = 0) -> List[Dict]:
        """检测标注是否跨越标点符号（通常是错误的）"""
        issues = []
        pattern = r'〖[#@=;$%&\'^~•!\'+?{:\[_]([^〗]+)〗'
        for match in re.finditer(pattern, text):
            content = match.group(1)
            # 检查content中是否有句子边界标点（。！？）
            boundary_puncts = r'[。！？]'
            punct_match = re.search(boundary_puncts, content)
            if punct_match:
                issues.append({
                    'type': 'annotation_across_punct',
                    'annotation': match.group(),
                    'pos': match.start(),
                    'line': line_num,
                    'punct': punct_match.group(),
                    'context': text[max(0, match.start()-20):match.end()+20],
                    'severity': 'high',
                    'message': f'标注跨越句子边界标点 {punct_match.group()}，应分开标注'
                })
        return issues

    def check_file(self, file_path: Path, check_types: List[str] = None) -> Dict:
        """检查单个文件"""
        if check_types is None:
            check_types = ['halfwidth', 'square', 'punct_in', 'markdown_in', 'nested', 'across']

        self.issues.clear()

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            if 'halfwidth' in check_types:
                self.issues['halfwidth_punct'].extend(
                    self.check_halfwidth_punctuation(line, line_num)
                )

            if 'square' in check_types:
                self.issues['square_quote'].extend(
                    self.check_square_quotes(line, line_num)
                )

            if 'punct_in' in check_types:
                self.issues['punct_in_annotation'].extend(
                    self.check_punct_in_annotation(line, line_num)
                )

            if 'markdown_in' in check_types:
                self.issues['markdown_in_annotation'].extend(
                    self.check_markdown_in_annotation(line, line_num)
                )

            if 'nested' in check_types:
                self.issues['nested_annotation'].extend(
                    self.check_nested_annotation(line, line_num)
                )

            if 'across' in check_types:
                self.issues['annotation_across_punct'].extend(
                    self.check_annotation_across_punct(line, line_num)
                )

        return dict(self.issues)

    def format_report(self, file_path: Path, issues: Dict) -> str:
        """格式化报告"""
        if not any(issues.values()):
            return f"✓ {file_path.name}: 无符号冲突问题\n"

        report = [f"\n{'=' * 60}"]
        report.append(f"文件: {file_path.name}")
        report.append('=' * 60)

        # 按严重程度排序
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        all_issues = []
        for issue_type, issue_list in issues.items():
            all_issues.extend(issue_list)

        all_issues.sort(key=lambda x: (severity_order[x['severity']], x['line'], x['pos']))

        for issue in all_issues:
            severity_label = {
                'high': '[高危]',
                'medium': '[中危]',
                'low': '[低危]'
            }[issue['severity']]

            report.append(f"\n{severity_label} 行{issue['line']}: {issue['type']}")
            report.append(f"  位置: {issue['context']}")
            report.append(f"  问题: {issue['message']}")

        return '\n'.join(report)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='检查标点、标注、Markdown符号的冲突和误用',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('files', nargs='+', help='要检查的文件')
    parser.add_argument('--check-types', help='检查类型（逗号分隔）：halfwidth,square,punct_in,markdown_in,nested,across')
    parser.add_argument('--report', help='生成报告到文件')

    args = parser.parse_args()

    # 解析检查类型
    check_types = None
    if args.check_types:
        check_types = [t.strip() for t in args.check_types.split(',')]

    linter = SymbolConflictLinter()

    # 统计信息
    total_files = 0
    total_issues = defaultdict(int)
    reports = []

    # 处理文件
    from glob import glob
    file_paths = []
    for pattern in args.files:
        file_paths.extend(glob(pattern))

    for file_path_str in sorted(file_paths):
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"警告: 文件不存在 {file_path}", file=sys.stderr)
            continue

        total_files += 1
        issues = linter.check_file(file_path, check_types)

        # 统计
        for issue_type, issue_list in issues.items():
            total_issues[issue_type] += len(issue_list)

        # 生成报告
        report = linter.format_report(file_path, issues)
        reports.append(report)

        # 输出到控制台
        if any(issues.values()):
            print(report)

    # 汇总报告
    summary = ["\n" + "=" * 60]
    summary.append("汇总统计")
    summary.append("=" * 60)
    summary.append(f"检查文件: {total_files} 个")

    total_count = sum(total_issues.values())
    summary.append(f"发现问题: {total_count} 处")

    if total_issues:
        summary.append("\n问题分类:")
        issue_type_names = {
            'halfwidth_punct': '半角标点',
            'square_quote': '直角引号',
            'punct_in_annotation': '标点在标注内',
            'markdown_in_annotation': 'Markdown在标注内',
            'nested_annotation': '嵌套标注',
            'annotation_across_punct': '标注跨标点'
        }
        for issue_type, count in sorted(total_issues.items(), key=lambda x: -x[1]):
            type_name = issue_type_names.get(issue_type, issue_type)
            summary.append(f"  - {type_name}: {count} 处")

    summary_text = '\n'.join(summary)
    print(summary_text)

    # 写入报告文件
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("【符号冲突检查报告】\n")
            f.write(f"生成时间: {Path.cwd()}\n")
            f.write(f"检查文件: {total_files} 个\n\n")
            f.write('\n'.join(reports))
            f.write('\n\n')
            f.write(summary_text)

        print(f"\n报告已保存到: {report_path}")

    # 返回错误码
    return 0 if total_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
