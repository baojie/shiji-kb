#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史记知识库 Markdown 文件 Lint 检查工具

检查项目：
1. 实体标注语法正确性
2. 段落编号连续性和格式
3. 标题层级结构
4. 引用标记格式
5. 特殊字符和编码问题
"""

import re
import sys
from pathlib import Path
from collections import defaultdict


class MarkdownLinter:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.content = self.file_path.read_text(encoding='utf-8')
        self.lines = self.content.split('\n')
        self.errors = []
        self.warnings = []
        self.info = []

    def check_entity_tags(self):
        """检查实体标注的正确性"""
        # 定义实体标注模式
        entity_patterns = {
            '人名': r'@([^@]+)@',
            '地名': r'=([^=]+)=',
            '官职': r'#([^#]+)#',
            '时间': r'%([^%]+)%',
            '朝代': r'&([^&]+)&',
            '制度': r'\^([^^]+)\^',
            '族群': r'~([^~]+)~',
            '器物': r'\*([^*]+)\*',
            '天文': r'!([^!]+)!',
            '神话': r'〚([^〚〛]+)〛',
            '动植物': r'〘([^〘〙]+)〙',
            '标题/职位': r'\$([^$]+)\$'
        }

        # 检查是否有任何实体标注
        total_entity_count = 0
        for pattern in entity_patterns.values():
            total_entity_count += len(re.findall(pattern, self.content))
        if total_entity_count == 0:
            self.errors.append("文档中没有任何实体标注（@人名@、=地名= 等），请检查是否遗漏标注")

        for entity_type, pattern in entity_patterns.items():
            # 检查未闭合的标注
            if entity_type == '人名':
                # 检查单个@符号（应该成对出现）
                single_at = re.findall(r'(?<![^@])@(?![^@])', self.content)
                if single_at:
                    self.errors.append(f"发现未闭合的人名标注 '@'")

            # 检查嵌套标注和空标注
            matches = list(re.finditer(pattern, self.content))
            for match in matches:
                content = match.group(1)

                # 检查空标注
                if not content.strip():
                    self.warnings.append(
                        f"第{self._get_line_num(match.start())}行: 空{entity_type}标注"
                    )

                # 检查是否包含其他标注符号
                if any(char in content for char in '@=#%&^~*!?🌿〘〙$'):
                    self.warnings.append(
                        f"第{self._get_line_num(match.start())}行: "
                        f"{entity_type}标注可能嵌套了其他标注: {match.group(0)[:30]}..."
                    )

    def check_paragraph_numbers(self):
        """检查段落编号的连续性和格式"""
        para_pattern = r'^\[(\d+(?:\.\d+)*)\]'
        paragraphs = []

        for i, line in enumerate(self.lines, 1):
            match = re.match(para_pattern, line.strip())
            if match:
                para_num = match.group(1)
                paragraphs.append({
                    'num': para_num,
                    'line': i,
                    'parts': para_num.split('.')
                })

        # 检查编号格式
        for para in paragraphs:
            # 检查是否有非数字部分
            for part in para['parts']:
                if not part.isdigit():
                    self.errors.append(
                        f"第{para['line']}行: 段落编号格式错误: [{para['num']}]"
                    )

        # 检查连续性（一级编号应该连续）
        top_level_nums = [int(p['parts'][0]) for p in paragraphs if len(p['parts']) == 1]
        if top_level_nums:
            expected = list(range(top_level_nums[0], top_level_nums[-1] + 1))
            missing = set(expected) - set(top_level_nums)
            if missing:
                self.warnings.append(
                    f"一级段落编号不连续，缺失: {sorted(missing)}"
                )

    def check_heading_structure(self):
        """检查标题层级结构"""
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        headings = []

        for i, line in enumerate(self.lines, 1):
            match = re.match(heading_pattern, line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2)
                headings.append({
                    'level': level,
                    'title': title,
                    'line': i
                })

        # 检查一级标题数量（应该只有一个）
        h1_count = sum(1 for h in headings if h['level'] == 1)
        if h1_count == 0:
            self.errors.append("缺少一级标题（# 标题）")
        elif h1_count > 1:
            self.warnings.append(f"有多个一级标题（{h1_count}个），建议只保留一个")

        # 检查标题层级跳跃（如从# 直接到 ###）
        for i in range(1, len(headings)):
            prev_level = headings[i-1]['level']
            curr_level = headings[i]['level']
            if curr_level > prev_level + 1:
                self.warnings.append(
                    f"第{headings[i]['line']}行: 标题层级跳跃 "
                    f"(从 {'#'*prev_level} 到 {'#'*curr_level})"
                )

        # 检查标题内容
        for h in headings:
            # 检查是否包含段落编号
            if re.match(r'\[\d+(?:\.\d+)*\]', h['title']):
                self.warnings.append(
                    f"第{h['line']}行: 标题中包含段落编号: {h['title'][:30]}..."
                )

    def check_quote_marks(self):
        """检查引用标记格式"""
        # 检查对话引用 > 开头的行
        quote_pattern = r'^>\s*(.+)$'
        quotes = []

        for i, line in enumerate(self.lines, 1):
            match = re.match(quote_pattern, line.strip())
            if match:
                quotes.append({
                    'content': match.group(1),
                    'line': i
                })

        # 检查是否有未标记的"曰"（可能是对话）
        yue_pattern = r'[曰云谓言][:：]?\s*[「『""]'
        for i, line in enumerate(self.lines, 1):
            if re.search(yue_pattern, line) and not line.strip().startswith('>'):
                # 只是提示，不一定是错误
                self.info.append(
                    f"第{i}行: 可能是未标记的对话（包含'曰'等引语动词）"
                )

    def check_special_chars(self):
        """检查特殊字符和编码问题"""
        # 检查全角数字（应该用半角）
        fullwidth_digits = re.findall(r'[０-９]', self.content)
        if fullwidth_digits:
            self.warnings.append(
                f"发现全角数字: {set(fullwidth_digits)}，建议改为半角"
            )

        # 检查全角标点（段落编号中不应该出现）
        para_lines = [line for line in self.lines if re.match(r'^\[', line.strip())]
        for i, line in enumerate(para_lines):
            if re.search(r'[，。！？；：、]', line.split(']')[0] if ']' in line else ''):
                self.warnings.append(
                    f"段落编号中包含全角标点: {line[:30]}..."
                )

        # 检查零宽字符
        zero_width_chars = ['\u200b', '\u200c', '\u200d', '\ufeff']
        for char in zero_width_chars:
            if char in self.content:
                count = self.content.count(char)
                self.warnings.append(
                    f"发现零宽字符 (U+{ord(char):04X})，数量: {count}"
                )

    def check_line_length(self):
        """检查行长度（建议）"""
        max_length = 200
        long_lines = []

        for i, line in enumerate(self.lines, 1):
            if len(line) > max_length:
                # 排除纯标注的长行
                if not re.match(r'^\[', line.strip()):
                    long_lines.append((i, len(line)))

        if long_lines:
            self.info.append(
                f"有{len(long_lines)}行超过{max_length}字符（建议分段）"
            )

    def _get_line_num(self, char_pos):
        """根据字符位置获取行号"""
        text_before = self.content[:char_pos]
        return text_before.count('\n') + 1

    def lint(self):
        """执行所有检查"""
        print(f"正在检查: {self.file_path.name}")
        print("=" * 70)

        self.check_entity_tags()
        self.check_paragraph_numbers()
        self.check_heading_structure()
        self.check_quote_marks()
        self.check_special_chars()
        self.check_line_length()

        return self._generate_report()

    def _generate_report(self):
        """生成检查报告"""
        has_issues = bool(self.errors or self.warnings)

        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if self.info:
            print(f"\nℹ️  提示 ({len(self.info)}):")
            for info_msg in self.info[:5]:  # 只显示前5条
                print(f"  • {info_msg}")
            if len(self.info) > 5:
                print(f"  ... 还有 {len(self.info) - 5} 条提示")

        if not has_issues:
            print("\n✅ 没有发现错误或警告")

        print("=" * 70)
        print(f"总计: {len(self.errors)} 错误, {len(self.warnings)} 警告, {len(self.info)} 提示\n")

        return len(self.errors) == 0


def main():
    if len(sys.argv) < 2:
        print("用法: python lint_markdown.py <文件或目录>")
        print("示例:")
        print("  python lint_markdown.py chapter_md/001_五帝本纪.tagged.md")
        print("  python lint_markdown.py chapter_md/  # 检查整个目录")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob('*.tagged.md'))
    else:
        print(f"错误: 路径不存在: {path}")
        sys.exit(1)

    print(f"\n开始检查 {len(files)} 个文件...\n")

    total_errors = 0
    total_warnings = 0
    failed_files = []

    for md_file in files:
        linter = MarkdownLinter(md_file)
        success = linter.lint()

        total_errors += len(linter.errors)
        total_warnings += len(linter.warnings)

        if not success:
            failed_files.append(md_file.name)

    # 总结
    print("\n" + "=" * 70)
    print("检查完成")
    print("=" * 70)
    print(f"检查文件数: {len(files)}")
    print(f"总错误数: {total_errors}")
    print(f"总警告数: {total_warnings}")

    if failed_files:
        print(f"\n有错误的文件 ({len(failed_files)}):")
        for fname in failed_files[:10]:
            print(f"  • {fname}")
        if len(failed_files) > 10:
            print(f"  ... 还有 {len(failed_files) - 10} 个文件")

    sys.exit(0 if total_errors == 0 else 1)


if __name__ == '__main__':
    main()
