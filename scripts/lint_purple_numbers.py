#!/usr/bin/env python3
"""
Purple Numbers（段落编号）完整性检查工具

整合所有编号相关的检查，提供全面的编号质量报告。

检查项：
1. 编号格式检查：[N] 或 [N.N] 格式，不允许字母或中文
2. 编号连续性检查：同层级不允许跳跃（[1]→[2]→[3]，不允许[1]→[3]）
3. 父子关系检查：子编号必须有对应的父编号（有[67.1]必须有[67]）
4. 标题编号检查：二级和三级标题不应包含编号
5. 重复编号检查：同一章内不允许重复编号
6. 篇名编号检查：第一个编号必须是[0]
7. 段落编号缺失检查：前后有空行的自然段必须有PN编号（标题和bullet list后第一段除外）

使用方法：
    python scripts/lint_purple_numbers.py                    # 检查所有章节
    python scripts/lint_purple_numbers.py 001                # 检查指定章节
    python scripts/lint_purple_numbers.py --verbose          # 显示详细信息
"""

import re
import sys
from pathlib import Path
from collections import defaultdict, Counter


class PurpleNumberLinter:
    """Purple Numbers编号检查器"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.issues = defaultdict(list)

    def check_file(self, file_path):
        """检查单个文件的所有编号问题"""
        self.issues.clear()

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 提取所有编号
        paragraph_numbers = self._extract_paragraph_numbers(lines)

        # 运行所有检查
        self._check_format(lines)
        self._check_continuity(paragraph_numbers)
        self._check_parent_child(paragraph_numbers)
        self._check_heading_numbers(lines)
        self._check_duplicates(paragraph_numbers)
        self._check_title_number(lines)
        self._check_missing_pn(lines)

        return self.issues

    def _extract_paragraph_numbers(self, lines):
        """提取文件中的所有段落编号"""
        numbers = []
        pattern = r'^\[(\d+(?:\.\d+)*)\]'

        for i, line in enumerate(lines):
            match = re.match(pattern, line.strip())
            if match:
                pn = match.group(1)
                numbers.append({
                    'pn': pn,
                    'line': i + 1,
                    'content': line.strip()
                })

        return numbers

    def _check_format(self, lines):
        """检查编号格式（必须是纯数字点分格式）"""
        # 匹配段落编号，但允许非标准格式
        pattern = r'^\[([^\]]+)\]'
        valid_pattern = r'^\d+(?:\.\d+)*$'

        for i, line in enumerate(lines):
            match = re.match(pattern, line.strip())
            if match:
                pn = match.group(1)
                # 检查是否符合有效格式
                if not re.match(valid_pattern, pn):
                    self.issues['format'].append({
                        'line': i + 1,
                        'pn': pn,
                        'content': line.strip(),
                        'reason': '编号格式错误（只允许数字和点，如[1]或[1.2.3]）'
                    })

    def _check_continuity(self, paragraph_numbers):
        """检查编号连续性（同层级不允许跳跃）"""
        # 按层级分组
        levels = defaultdict(list)

        for item in paragraph_numbers:
            pn = item['pn']
            parts = pn.split('.')

            # 一级编号
            if len(parts) == 1:
                levels['1'].append(item)
            # 二级编号
            elif len(parts) == 2:
                parent = parts[0]
                levels[f'2_{parent}'].append(item)
            # 三级编号
            elif len(parts) == 3:
                parent = '.'.join(parts[:2])
                levels[f'3_{parent}'].append(item)

        # 检查每个层级的连续性
        for level_key, items in levels.items():
            numbers = []
            for item in items:
                parts = item['pn'].split('.')
                last_num = int(parts[-1])
                numbers.append((last_num, item))

            # 排序
            numbers.sort(key=lambda x: x[0])

            # 检查是否连续
            for i in range(len(numbers) - 1):
                current_num, current_item = numbers[i]
                next_num, next_item = numbers[i + 1]

                if next_num != current_num + 1:
                    self.issues['continuity'].append({
                        'line': next_item['line'],
                        'pn': next_item['pn'],
                        'expected': self._increment_pn(current_item['pn']),
                        'reason': f"编号跳跃：{current_item['pn']} → {next_item['pn']}（缺少{self._increment_pn(current_item['pn'])}）"
                    })

    def _increment_pn(self, pn):
        """计算下一个编号"""
        parts = pn.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        return '.'.join(parts)

    def _check_parent_child(self, paragraph_numbers):
        """检查父子关系（子编号必须有父编号）"""
        # 提取一级编号集合
        level1 = set()
        level2_plus = defaultdict(list)

        for item in paragraph_numbers:
            pn = item['pn']
            if '.' in pn:
                # 提取父编号：67.1 → 67，67.1.2 → 67
                parent = pn.split('.')[0]
                level2_plus[parent].append(item)
            else:
                level1.add(pn)

        # 检查缺失的父编号
        for parent, children in level2_plus.items():
            if parent not in level1:
                self.issues['parent_child'].append({
                    'parent': parent,
                    'children': [c['pn'] for c in children],
                    'first_line': children[0]['line'],
                    'reason': f"子编号[{children[0]['pn']}]缺少父编号[{parent}]"
                })

    def _check_heading_numbers(self, lines):
        """检查标题中的编号（二级和三级标题不应包含编号）"""
        for i, line in enumerate(lines):
            stripped = line.strip()

            # 跳过一级标题（# [0] 篇名是合法的）
            if stripped.startswith('# '):
                continue

            # 检查二级标题
            if stripped.startswith('## '):
                match = re.match(r'^##\s+\[(\d+(?:\.\d+)*)\]\s+(.+)$', stripped)
                if match:
                    self.issues['heading'].append({
                        'line': i + 1,
                        'pn': match.group(1),
                        'title': match.group(2),
                        'original': stripped,
                        'fixed': f'## {match.group(2)}',
                        'reason': '二级标题不应包含编号'
                    })

            # 检查三级标题
            elif stripped.startswith('### '):
                match = re.match(r'^###\s+\[(\d+(?:\.\d+)*)\]\s+(.+)$', stripped)
                if match:
                    self.issues['heading'].append({
                        'line': i + 1,
                        'pn': match.group(1),
                        'title': match.group(2),
                        'original': stripped,
                        'fixed': f'### {match.group(2)}',
                        'reason': '三级标题不应包含编号'
                    })

    def _check_duplicates(self, paragraph_numbers):
        """检查重复编号"""
        pn_counter = Counter([item['pn'] for item in paragraph_numbers])

        for pn, count in pn_counter.items():
            if count > 1:
                # 找到所有重复的行号
                lines = [item['line'] for item in paragraph_numbers if item['pn'] == pn]
                self.issues['duplicate'].append({
                    'pn': pn,
                    'count': count,
                    'lines': lines,
                    'reason': f"编号[{pn}]重复出现{count}次"
                })

    def _check_title_number(self, lines):
        """检查篇名编号（一级标题中应该有[0]）"""
        # 查找一级标题（# [0] 篇名）
        title_pattern = r'^#\s+\[(\d+(?:\.\d+)*)\]'
        has_title_zero = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('# '):
                match = re.match(title_pattern, stripped)
                if match:
                    pn = match.group(1)
                    if pn == '0':
                        has_title_zero = True
                    else:
                        self.issues['title'].append({
                            'line': i + 1,
                            'pn': pn,
                            'reason': '一级标题中的编号应该是[0]（篇名编号）'
                        })
                else:
                    # 一级标题没有编号
                    self.issues['title'].append({
                        'line': i + 1,
                        'content': stripped,
                        'reason': '一级标题缺少编号[0]'
                    })
                break  # 只检查第一个一级标题

    def _check_missing_pn(self, lines):
        """检查缺失的段落编号（前后有空行的自然段必须有PN编号）"""
        pn_pattern = r'^\[(\d+(?:\.\d+)*)\]'
        in_table = False

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 跳过空行
            if not line:
                i += 1
                continue

            # 检测表格开始和结束
            # Markdown表格行：以 | 开头或包含多个 | (至少2个)
            # 排除标注内的消歧语法 〖TYPE 显示名|规范名〗
            is_table_line = False
            if '|' in line:
                # 简单判断：如果行以 | 开头，或者包含至少2个 | 且不在标注内
                if line.startswith('|'):
                    is_table_line = True
                else:
                    # 移除标注标记后再检查 | 的数量
                    line_without_annotations = re.sub(r'〖[^〗]+〗', '', line)
                    line_without_annotations = re.sub(r'⟦[^⟧]+⟧', '', line_without_annotations)
                    if line_without_annotations.count('|') >= 2:
                        is_table_line = True

            if is_table_line:
                in_table = True
                i += 1
                continue
            elif in_table:
                # 如果前一行是表格，当前行不是表格，则表格结束
                in_table = False

            # 跳过表格内容
            if in_table:
                i += 1
                continue

            # 跳过标题行（以 # 开头）
            if line.startswith('#'):
                i += 1
                continue

            # 跳过引用块（以 > 开头）
            if line.startswith('>'):
                i += 1
                continue

            # 跳过markdown分隔线（--- 或 *** 或 ___）
            if line in ['---', '***', '___']:
                i += 1
                continue

            # 这是一个非空的内容行
            # 检查是否前面有空行（或是文件开头）
            has_prev_empty = (i == 0 or not lines[i-1].strip())

            # 检查是否后面有空行（或是文件结尾）
            has_next_empty = (i >= len(lines) - 1 or not lines[i+1].strip())

            # 如果前后都有空行，这是一个独立段落
            if has_prev_empty and has_next_empty:
                # 检查前一个非空行是否是标题或bullet list
                is_after_header_or_list = False
                j = i - 1
                while j >= 0:
                    prev_line = lines[j].strip()
                    if prev_line:
                        # 标题行
                        if prev_line.startswith('#'):
                            is_after_header_or_list = True
                        # Bullet list 项（以 - 或 * 或 + 或数字. 开头）
                        elif (prev_line.startswith('- ') or
                              prev_line.startswith('* ') or
                              prev_line.startswith('+ ') or
                              re.match(r'^\d+\.\s', prev_line)):
                            is_after_header_or_list = True
                        break
                    j -= 1

                # 标题或bullet list后的第一个段落不需要PN编号
                if is_after_header_or_list:
                    i += 1
                    continue

                # 检查是否有PN编号
                if not re.match(pn_pattern, line):
                    # 截取前50个字符作为预览
                    preview = line[:50] + ('...' if len(line) > 50 else '')
                    self.issues['missing_pn'].append({
                        'line': i + 1,
                        'content': preview,
                        'reason': '前后有空行的独立段落缺少PN编号'
                    })

            i += 1


def print_report(file_name, issues, verbose=False):
    """打印检查报告"""
    total_issues = sum(len(v) for v in issues.values())

    if total_issues == 0:
        print(f"✓ {file_name}: 编号检查通过")
        return 0

    print(f"\n{'='*80}")
    print(f"【{file_name}】发现 {total_issues} 个问题")
    print('='*80)

    # 1. 格式错误
    if issues['format']:
        print(f"\n▸ 格式错误 ({len(issues['format'])}处)")
        print('-'*80)
        for err in issues['format']:
            print(f"  行 {err['line']}: {err['content']}")
            print(f"    → {err['reason']}")
            print()

    # 2. 连续性错误
    if issues['continuity']:
        print(f"\n▸ 连续性错误 ({len(issues['continuity'])}处)")
        print('-'*80)
        for err in issues['continuity']:
            print(f"  行 {err['line']}: [{err['pn']}]")
            print(f"    → {err['reason']}")
            print(f"    → 建议修改为: [{err['expected']}]")
            print()

    # 3. 父子关系错误
    if issues['parent_child']:
        print(f"\n▸ 父子关系错误 ({len(issues['parent_child'])}处)")
        print('-'*80)
        for err in issues['parent_child']:
            print(f"  行 {err['first_line']}: 缺少父编号 [{err['parent']}]")
            print(f"    → 子编号: {', '.join(['['+c+']' for c in err['children']])}")
            print(f"    → 建议：在行{err['first_line']}之前插入 [{err['parent']}]")
            print()

    # 4. 标题编号错误
    if issues['heading']:
        print(f"\n▸ 标题编号错误 ({len(issues['heading'])}处)")
        print('-'*80)
        for err in issues['heading']:
            print(f"  行 {err['line']}: {err['original']}")
            print(f"    → 应改为: {err['fixed']}")
            print(f"    → {err['reason']}")
            print()

    # 5. 重复编号
    if issues['duplicate']:
        print(f"\n▸ 重复编号 ({len(issues['duplicate'])}处)")
        print('-'*80)
        for err in issues['duplicate']:
            print(f"  编号 [{err['pn']}] 重复 {err['count']} 次")
            print(f"    → 出现在行: {', '.join(map(str, err['lines']))}")
            print()

    # 6. 篇名编号错误
    if issues['title']:
        print(f"\n▸ 篇名编号错误")
        print('-'*80)
        for err in issues['title']:
            if 'pn' in err:
                print(f"  行 {err['line']}: [{err['pn']}]")
            else:
                print(f"  行 {err['line']}: {err.get('content', '')}")
            print(f"    → {err['reason']}")
            print()

    # 7. 缺失段落编号
    if issues['missing_pn']:
        print(f"\n▸ 缺失段落编号 ({len(issues['missing_pn'])}处)")
        print('-'*80)
        for err in issues['missing_pn']:
            print(f"  行 {err['line']}: {err['content']}")
            print(f"    → {err['reason']}")
            print()

    return total_issues


def main():
    """主函数"""
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]

    chapter_dir = Path(__file__).parent.parent / 'chapter_md'

    # 确定要检查的文件
    if args:
        # 检查指定章节
        chapter_num = args[0].zfill(3)
        tagged_files = list(chapter_dir.glob(f'{chapter_num}_*.tagged.md'))
        if not tagged_files:
            print(f"错误：未找到章节 {chapter_num}")
            return 1
    else:
        # 检查所有章节
        tagged_files = sorted(chapter_dir.glob('*.tagged.md'))

    print("=" * 80)
    print("Purple Numbers 编号检查")
    print("=" * 80)
    print(f"检查文件数: {len(tagged_files)}")
    print()

    linter = PurpleNumberLinter(verbose)
    total_issues = 0
    files_with_issues = []

    for file_path in tagged_files:
        issues = linter.check_file(file_path)
        issue_count = sum(len(v) for v in issues.values())

        if issue_count > 0:
            total_issues += issue_count
            files_with_issues.append((file_path.name, issue_count))
            print_report(file_path.name, issues, verbose)
        elif verbose:
            print(f"✓ {file_path.name}: 编号检查通过")

    # 汇总
    print("\n" + "=" * 80)
    print("汇总")
    print("=" * 80)
    print(f"检查文件数: {len(tagged_files)}")
    print(f"有问题的文件数: {len(files_with_issues)}")
    print(f"问题总数: {total_issues}")
    print()

    if files_with_issues:
        print("有问题的文件列表:")
        for filename, count in files_with_issues:
            print(f"  - {filename}: {count}个问题")
        print()

        print("修复建议:")
        print("  1. 格式错误: 手动修改为标准格式 [N] 或 [N.N]")
        print("  2. 连续性错误: 检查是否遗漏段落或编号错误")
        print("  3. 父子关系错误: python scripts/fix_missing_parent_pn.py")
        print("  4. 标题编号错误: python scripts/fix_heading_numbers.py")
        print("  5. 重复编号: 手动检查并重新编号")
        print("  6. 篇名编号错误: 手动确认第一段是否为篇名")
        print("  7. 缺失段落编号: 为前后有空行的独立段落添加PN编号")
        print()
        return 1
    else:
        print("✓ 所有文件的编号检查通过！")
        return 0


if __name__ == '__main__':
    sys.exit(main())
