#!/usr/bin/env python3
"""
动词标注Lint检查工具

功能：
1. 检查动词标注与实体标注嵌套问题
2. 检查动词标注格式错误
3. 检查未识别的动词类型
4. 检查消歧说明格式
5. 生成详细的质量报告

用法：
  python lint_verb_tagging.py                           # 检查所有章节
  python lint_verb_tagging.py --chapter 040             # 检查指定章节
  python lint_verb_tagging.py --fix                     # 自动修复部分问题
  python lint_verb_tagging.py --report output.md        # 生成报告
"""

import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHAPTER_DIR = BASE_DIR / 'chapter_md'

# 导入动词词表
from query_verbs_by_type import (
    MILITARY_VERBS, PENALTY_VERBS, POLITICAL_VERBS, PENALTY_NOUNS, ALL_VERBS
)


class VerbLinter:
    """动词标注Lint检查器"""

    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = Counter()

    def lint_chapter(self, chapter_file):
        """检查单个章节"""
        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        chapter_name = chapter_file.stem
        chapter_issues = {
            'nesting': [],          # 嵌套问题
            'format_error': [],     # 格式错误
            'unknown_type': [],     # 未知类型
            'invalid_disambig': [], # 无效消歧
            'empty_verb': [],       # 空动词
            'mixed_brackets': []    # 混用括号
        }

        # 1. 检查嵌套问题
        chapter_issues['nesting'].extend(self._check_nesting(content, chapter_name))

        # 2. 检查格式错误
        chapter_issues['format_error'].extend(self._check_format(content, chapter_name))

        # 3. 检查未知类型
        chapter_issues['unknown_type'].extend(self._check_unknown_types(content, chapter_name))

        # 4. 检查消歧说明
        chapter_issues['invalid_disambig'].extend(self._check_disambig(content, chapter_name))

        # 5. 检查空动词
        chapter_issues['empty_verb'].extend(self._check_empty_verb(content, chapter_name))

        # 6. 检查混用括号
        chapter_issues['mixed_brackets'].extend(self._check_mixed_brackets(content, chapter_name))

        # 统计
        for issue_type, issues in chapter_issues.items():
            self.stats[issue_type] += len(issues)
            if issues:
                self.issues[chapter_name].extend(issues)

        return chapter_issues

    def _check_nesting(self, content, chapter_name):
        """检查嵌套问题"""
        issues = []

        # 检查 ⟦...〖...⟧ (动词标注内包含实体标注)
        pattern1 = r'⟦([◈◉○◇])([^⟧]*)(〖[^〗]*〗)([^⟧]*)⟧'
        for match in re.finditer(pattern1, content):
            issues.append({
                'type': 'nesting',
                'severity': 'error',
                'message': '动词标注内嵌套了实体标注',
                'match': match.group(0),
                'position': self._get_line_number(content, match.start()),
                'suggestion': f'⟦{match.group(1)}{match.group(2)}{match.group(4)}⟧{match.group(3)}'
            })

        # 检查 〖...⟦...〗 (实体标注内包含动词标注)
        pattern2 = r'〖([^〗]*)(⟦[^⟧]*⟧)([^〗]*)〗'
        for match in re.finditer(pattern2, content):
            issues.append({
                'type': 'nesting',
                'severity': 'error',
                'message': '实体标注内嵌套了动词标注',
                'match': match.group(0),
                'position': self._get_line_number(content, match.start()),
                'suggestion': f'{match.group(2)}〖{match.group(1)}{match.group(3)}〗'
            })

        # 检查 ⟦...⟦...⟧ (动词标注内嵌套动词标注)
        pattern3 = r'⟦([◈◉○◇])([^⟧]*)(⟦[^⟧]*⟧)([^⟧]*)⟧'
        for match in re.finditer(pattern3, content):
            issues.append({
                'type': 'nesting',
                'severity': 'error',
                'message': '动词标注内嵌套了动词标注',
                'match': match.group(0),
                'position': self._get_line_number(content, match.start()),
                'suggestion': f'⟦{match.group(1)}{match.group(2)}{match.group(4)}⟧{match.group(3)}'
            })

        return issues

    def _check_format(self, content, chapter_name):
        """检查格式错误"""
        issues = []

        # 检查错误的TYPE符号
        pattern = r'⟦([^◈◉○◇⟧])'
        for match in re.finditer(pattern, content):
            issues.append({
                'type': 'format_error',
                'severity': 'error',
                'message': f'无效的TYPE符号: {match.group(1)}',
                'match': match.group(0),
                'position': self._get_line_number(content, match.start()),
                'suggestion': '应使用 ◈(军事) ◉(刑罚) ○(政治) ◇(经济)'
            })

        # 检查不配对的括号
        # 动词括号
        verb_open = content.count('⟦')
        verb_close = content.count('⟧')
        if verb_open != verb_close:
            issues.append({
                'type': 'format_error',
                'severity': 'error',
                'message': f'动词括号不配对: ⟦({verb_open}) vs ⟧({verb_close})',
                'match': None,
                'position': None,
                'suggestion': '检查所有动词标注的括号是否配对'
            })

        return issues

    def _check_unknown_types(self, content, chapter_name):
        """检查未知动词类型"""
        issues = []

        # 提取所有动词标注
        pattern = r'⟦([◈◉○◇])([^⟧|]+)(?:\|([^⟧]+))?⟧'
        for match in re.finditer(pattern, content):
            type_symbol = match.group(1)
            verb = match.group(2).strip()
            disambig = match.group(3)

            # 检查动词是否在词表中
            if type_symbol == '◈' and verb not in MILITARY_VERBS:
                issues.append({
                    'type': 'unknown_type',
                    'severity': 'warning',
                    'message': f'未知的军事动词: {verb}',
                    'match': match.group(0),
                    'position': self._get_line_number(content, match.start()),
                    'suggestion': f'请确认"{verb}"是否应该标注为军事动词'
                })

            elif type_symbol == '◉' and verb not in PENALTY_VERBS:
                issues.append({
                    'type': 'unknown_type',
                    'severity': 'warning',
                    'message': f'未知的刑罚动词: {verb}',
                    'match': match.group(0),
                    'position': self._get_line_number(content, match.start()),
                    'suggestion': f'请确认"{verb}"是否应该标注为刑罚动词'
                })

            elif type_symbol == '○' and verb not in POLITICAL_VERBS:
                issues.append({
                    'type': 'unknown_type',
                    'severity': 'warning',
                    'message': f'未知的政治动词: {verb}',
                    'match': match.group(0),
                    'position': self._get_line_number(content, match.start()),
                    'suggestion': f'请确认"{verb}"是否应该标注为政治动词'
                })

        return issues

    def _check_disambig(self, content, chapter_name):
        """检查消歧说明"""
        issues = []

        # 检查空消歧说明
        pattern = r'⟦([◈◉○◇])([^⟧|]+)\|(\s*)⟧'
        for match in re.finditer(pattern, content):
            if not match.group(3).strip():
                issues.append({
                    'type': 'invalid_disambig',
                    'severity': 'warning',
                    'message': '消歧说明为空',
                    'match': match.group(0),
                    'position': self._get_line_number(content, match.start()),
                    'suggestion': f'删除空的消歧说明: ⟦{match.group(1)}{match.group(2)}⟧'
                })

        return issues

    def _check_empty_verb(self, content, chapter_name):
        """检查空动词"""
        issues = []

        # 检查空动词 ⟦TYPE⟧
        pattern = r'⟦([◈◉○◇])\s*⟧'
        for match in re.finditer(pattern, content):
            issues.append({
                'type': 'empty_verb',
                'severity': 'error',
                'message': '动词内容为空',
                'match': match.group(0),
                'position': self._get_line_number(content, match.start()),
                'suggestion': '删除空的动词标注或补充动词内容'
            })

        return issues

    def _check_mixed_brackets(self, content, chapter_name):
        """检查混用括号 (动词用了实体括号，或实体用了动词括号)"""
        issues = []

        # 检查 〖[verb〗 格式 (应该已迁移完成，如果还有则是遗漏)
        pattern = r'〖\[([^〗]+)〗'
        for match in re.finditer(pattern, content):
            verb = match.group(1).split('|')[0].strip()
            if verb in ALL_VERBS:
                issues.append({
                    'type': 'mixed_brackets',
                    'severity': 'warning',
                    'message': f'动词"{verb}"使用了旧格式括号',
                    'match': match.group(0),
                    'position': self._get_line_number(content, match.start()),
                    'suggestion': '应使用动词标注格式 ⟦TYPE动词⟧'
                })

        return issues

    def _get_line_number(self, content, position):
        """获取位置对应的行号"""
        return content[:position].count('\n') + 1

    def generate_report(self):
        """生成检查报告"""
        report_lines = []

        report_lines.append("=" * 70)
        report_lines.append("动词标注Lint检查报告")
        report_lines.append("=" * 70)
        report_lines.append("")

        # 总体统计
        report_lines.append("## 总体统计")
        report_lines.append("")
        report_lines.append(f"检查章节数: {len(self.issues)}")
        report_lines.append(f"问题总数: {sum(self.stats.values())}")
        report_lines.append("")

        # 问题类型分布
        if self.stats:
            report_lines.append("## 问题类型分布")
            report_lines.append("")
            report_lines.append(f"{'类型':<20} {'数量':>8} {'严重程度':<10}")
            report_lines.append("-" * 45)

            type_names = {
                'nesting': '嵌套问题',
                'format_error': '格式错误',
                'unknown_type': '未知类型',
                'invalid_disambig': '无效消歧',
                'empty_verb': '空动词',
                'mixed_brackets': '混用括号'
            }

            severity_map = {
                'nesting': 'ERROR',
                'format_error': 'ERROR',
                'unknown_type': 'WARNING',
                'invalid_disambig': 'WARNING',
                'empty_verb': 'ERROR',
                'mixed_brackets': 'WARNING'
            }

            for issue_type, count in self.stats.most_common():
                type_name = type_names.get(issue_type, issue_type)
                severity = severity_map.get(issue_type, 'INFO')
                report_lines.append(f"{type_name:<20} {count:>8} {severity:<10}")

            report_lines.append("")

        # 详细问题列表
        if self.issues:
            report_lines.append("## 详细问题列表")
            report_lines.append("")

            for chapter_name, chapter_issues in sorted(self.issues.items()):
                if chapter_issues:
                    report_lines.append(f"### {chapter_name}")
                    report_lines.append("")

                    for i, issue in enumerate(chapter_issues, 1):
                        severity_icon = "🔴" if issue['severity'] == 'error' else "⚠️"
                        report_lines.append(f"{i}. {severity_icon} **{issue['type']}** - {issue['message']}")

                        if issue.get('position'):
                            report_lines.append(f"   - 位置: 第 {issue['position']} 行")

                        if issue.get('match'):
                            report_lines.append(f"   - 内容: `{issue['match']}`")

                        if issue.get('suggestion'):
                            report_lines.append(f"   - 建议: {issue['suggestion']}")

                        report_lines.append("")

        # 建议和总结
        report_lines.append("## 建议和总结")
        report_lines.append("")

        error_count = sum(self.stats[t] for t in ['nesting', 'format_error', 'empty_verb'])
        warning_count = sum(self.stats[t] for t in ['unknown_type', 'invalid_disambig', 'mixed_brackets'])

        if error_count == 0 and warning_count == 0:
            report_lines.append("✅ 所有检查通过！动词标注质量良好。")
        else:
            if error_count > 0:
                report_lines.append(f"🔴 发现 {error_count} 个严重错误，需要立即修复：")
                report_lines.append("   - 嵌套问题会导致解析错误")
                report_lines.append("   - 格式错误会导致无法识别")
                report_lines.append("   - 空动词没有实际意义")
                report_lines.append("")

            if warning_count > 0:
                report_lines.append(f"⚠️  发现 {warning_count} 个警告，建议检查：")
                report_lines.append("   - 未知类型可能是词表需要扩展")
                report_lines.append("   - 无效消歧应删除或补充")
                report_lines.append("   - 混用括号应迁移至新格式")
                report_lines.append("")

        report_lines.append("=" * 70)
        report_lines.append("检查完成")
        report_lines.append("=" * 70)

        return '\n'.join(report_lines)


def main():
    parser = argparse.ArgumentParser(description='动词标注Lint检查工具')
    parser.add_argument('--chapter', type=int, metavar='NNN',
                        help='检查指定章节（如 040）')
    parser.add_argument('--all', action='store_true',
                        help='检查所有章节（默认）')
    parser.add_argument('--report', metavar='FILE',
                        help='生成报告并保存到文件')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示详细信息')

    args = parser.parse_args()

    # 收集章节
    if args.chapter:
        chapter_files = list(CHAPTER_DIR.glob(f'{args.chapter:03d}_*.tagged.md'))
        if not chapter_files:
            print(f"错误: 未找到章节 {args.chapter:03d}")
            sys.exit(1)
    else:
        chapter_files = sorted(CHAPTER_DIR.glob('*.tagged.md'))

    # 执行检查
    print(f"\n正在检查 {len(chapter_files)} 个章节...")

    linter = VerbLinter()

    for i, chapter_file in enumerate(chapter_files, 1):
        if args.verbose:
            print(f"[{i}/{len(chapter_files)}] {chapter_file.stem} ...", end=' ')

        chapter_issues = linter.lint_chapter(chapter_file)
        total_issues = sum(len(issues) for issues in chapter_issues.values())

        if args.verbose:
            if total_issues == 0:
                print("✅ 通过")
            else:
                print(f"⚠️  {total_issues} 个问题")

    # 生成报告
    report = linter.generate_report()

    if args.report:
        output_path = BASE_DIR / args.report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存到: {output_path}")

    print("\n" + report)

    # 返回错误码
    error_count = sum(linter.stats[t] for t in ['nesting', 'format_error', 'empty_verb'])
    sys.exit(1 if error_count > 0 else 0)


if __name__ == '__main__':
    main()
