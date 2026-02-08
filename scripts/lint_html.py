#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史记知识库 HTML 文件 Lint 检查工具

检查项目：
1. HTML标签闭合和嵌套
2. 实体样式类名正确性
3. Purple Numbers段落编号完整性
4. 导航链接有效性
5. CSS/JS资源引用
6. 特殊字符转义
"""

import re
import sys
from pathlib import Path
from html.parser import HTMLParser


class HTMLStructureParser(HTMLParser):
    """HTML结构解析器，检查标签闭合"""
    def __init__(self):
        super().__init__()
        self.tag_stack = []
        self.errors = []
        self.self_closing_tags = {
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
            'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'
        }

    def handle_starttag(self, tag, attrs):
        if tag not in self.self_closing_tags:
            self.tag_stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.self_closing_tags:
            return

        if not self.tag_stack:
            self.errors.append(f"闭合标签 </{tag}> 没有对应的开始标签")
        elif self.tag_stack[-1] != tag:
            self.errors.append(
                f"标签嵌套错误: 期望 </{self.tag_stack[-1]}>, 实际 </{tag}>"
            )
        else:
            self.tag_stack.pop()

    def check_complete(self):
        if self.tag_stack:
            self.errors.append(
                f"未闭合的标签: {', '.join(f'<{tag}>' for tag in self.tag_stack)}"
            )


class HTMLLinter:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.content = self.file_path.read_text(encoding='utf-8')
        self.lines = self.content.split('\n')
        self.errors = []
        self.warnings = []
        self.info = []

    def check_html_structure(self):
        """检查HTML结构完整性"""
        parser = HTMLStructureParser()
        try:
            parser.feed(self.content)
            parser.check_complete()
            self.errors.extend(parser.errors)
        except Exception as e:
            self.errors.append(f"HTML解析错误: {str(e)}")

        # 检查基本HTML结构
        required_tags = ['html', 'head', 'body', 'title']
        for tag in required_tags:
            if f'<{tag}' not in self.content.lower():
                self.errors.append(f"缺少必需的标签: <{tag}>")

    def check_entity_styles(self):
        """检查实体标注的CSS类名"""
        # 定义标准实体类名
        valid_entity_classes = {
            'person',           # 人名
            'place',            # 地名
            'official',         # 官职
            'time',             # 时间
            'dynasty',          # 朝代/氏族
            'institution',      # 制度
            'tribe',            # 族群
            'artifact',         # 器物/书名
            'astronomy',        # 天文
            'mythical',         # 神话
            'flora-fauna'       # 动植物
        }

        # 查找所有带class的span标签
        span_pattern = r'<span\s+class="([^"]+)"'
        matches = re.finditer(span_pattern, self.content)

        for match in matches:
            classes = match.group(1).split()
            for cls in classes:
                # 检查是否是实体类名但不在标准列表中
                if cls not in valid_entity_classes and cls not in [
                    'para-num', 'original-text-link', 'nav-home',
                    'nav-prev', 'nav-next', 'toggle-arrow', 'intro-content',
                    'chapter-num', 'chapter-desc', 'more-sections',
                    'entity-tags', 'section-links'
                ]:
                    # 可能是拼写错误或未知类名
                    if any(entity in cls for entity in ['person', 'place', 'official']):
                        self.warnings.append(
                            f"可疑的CSS类名: '{cls}' (可能是拼写错误)"
                        )

    def check_purple_numbers(self):
        """检查Purple Numbers段落编号"""
        # 查找所有段落编号链接
        para_pattern = r'<a\s+href="#pn-(\d+(?:\.\d+)*)"\s+id="pn-\1"\s+class="para-num"'
        paragraphs = re.findall(para_pattern, self.content)

        if not paragraphs:
            self.warnings.append("未找到Purple Numbers段落编号")
            return

        # 检查编号连续性
        top_level = [int(p.split('.')[0]) for p in paragraphs if '.' not in p]
        if top_level:
            expected = list(range(min(top_level), max(top_level) + 1))
            missing = set(expected) - set(top_level)
            if missing:
                self.warnings.append(
                    f"段落编号不连续，缺失: {sorted(missing)}"
                )

        # 检查锚点链接格式
        bad_anchors = re.findall(
            r'<a\s+href="#pn-(\d+(?:\.\d+)*)"\s+id="pn-(\d+(?:\.\d+)*)"\s+class="para-num"',
            self.content
        )
        for href, id_val in bad_anchors:
            if href != id_val:
                self.errors.append(
                    f"段落编号不一致: href='#pn-{href}' id='pn-{id_val}'"
                )

    def check_navigation_links(self):
        """检查导航链接"""
        # 检查主页链接
        home_link_pattern = r'href="\.\./(docs/)?index\.html"'
        if not re.search(home_link_pattern, self.content):
            self.warnings.append("未找到主页链接")

        # 检查是否还有.tagged.html链接（应该已移除）
        tagged_links = re.findall(r'href="[^"]*\.tagged\.html"', self.content)
        if tagged_links:
            self.errors.append(
                f"发现{len(tagged_links)}个.tagged.html链接（应该已移除）"
            )
            for link in tagged_links[:3]:
                self.errors.append(f"  • {link}")

        # 检查章节导航链接格式
        nav_pattern = r'<a\s+href="(\d{3}_[^"]+\.html)"\s+class="nav-(prev|next)"'
        nav_links = re.findall(nav_pattern, self.content)

        for link, nav_type in nav_links:
            # 检查文件名格式
            if not re.match(r'\d{3}_[^/]+\.html$', link):
                self.warnings.append(
                    f"导航链接格式可疑: {link}"
                )

    def check_resource_links(self):
        """检查CSS/JS资源链接"""
        # 检查CSS链接
        css_pattern = r'<link\s+rel="stylesheet"\s+href="([^"]+)"'
        css_links = re.findall(css_pattern, self.content)

        expected_css = ['../css/shiji-styles.css', '../css/chapter-nav.css']
        for expected in expected_css:
            if expected not in css_links:
                self.warnings.append(f"缺少CSS文件引用: {expected}")

        # 检查错误的路径（如../docs/css/）
        bad_css_paths = re.findall(r'href="\.\./(docs/css/[^"]+)"', self.content)
        if bad_css_paths:
            self.errors.append(
                f"CSS路径错误（包含docs/）: {bad_css_paths}"
            )

        # 检查JS链接
        js_pattern = r'<script\s+src="([^"]+)"'
        js_links = re.findall(js_pattern, self.content)

        if '../js/purple-numbers.js' not in js_links:
            self.warnings.append("缺少purple-numbers.js引用")

        # 检查错误的JS路径
        bad_js_paths = re.findall(r'src="\.\./(docs/js/[^"]+)"', self.content)
        if bad_js_paths:
            self.errors.append(
                f"JS路径错误（包含docs/）: {bad_js_paths}"
            )

    def check_special_chars(self):
        """检查特殊字符转义"""
        # 检查未转义的特殊字符（在HTML标签外）
        # 注意：这个检查比较复杂，这里做简化版本

        # 检查<和>是否正确转义（排除HTML标签）
        content_no_tags = re.sub(r'<[^>]+>', '', self.content)

        unescaped_lt = re.findall(r'(?<!&lt;)<(?![\w/!])', content_no_tags)
        if unescaped_lt:
            self.warnings.append(
                f"可能有未转义的 < 字符（数量: {len(unescaped_lt)}）"
            )

    def check_title(self):
        """检查页面标题"""
        title_match = re.search(r'<title>([^<]+)</title>', self.content)

        if not title_match:
            self.errors.append("缺少<title>标签")
        else:
            title = title_match.group(1)
            # 检查是否还包含.tagged后缀
            if '.tagged' in title:
                self.warnings.append(
                    f"页面标题包含.tagged后缀: {title}"
                )

    def check_encoding(self):
        """检查字符编码声明"""
        if '<meta charset="UTF-8">' not in self.content and \
           '<meta charset="utf-8">' not in self.content.lower():
            self.errors.append("缺少UTF-8字符编码声明")

    def lint(self):
        """执行所有检查"""
        print(f"正在检查: {self.file_path.name}")
        print("=" * 70)

        self.check_html_structure()
        self.check_entity_styles()
        self.check_purple_numbers()
        self.check_navigation_links()
        self.check_resource_links()
        self.check_special_chars()
        self.check_title()
        self.check_encoding()

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
            for warning in self.warnings[:10]:  # 最多显示10条
                print(f"  • {warning}")
            if len(self.warnings) > 10:
                print(f"  ... 还有 {len(self.warnings) - 10} 条警告")

        if self.info:
            print(f"\nℹ️  提示 ({len(self.info)}):")
            for info_msg in self.info[:5]:
                print(f"  • {info_msg}")

        if not has_issues:
            print("\n✅ 没有发现错误或警告")

        print("=" * 70)
        print(f"总计: {len(self.errors)} 错误, {len(self.warnings)} 警告\n")

        return len(self.errors) == 0


def main():
    if len(sys.argv) < 2:
        print("用法: python lint_html.py <文件或目录>")
        print("示例:")
        print("  python lint_html.py docs/chapters/001_五帝本纪.html")
        print("  python lint_html.py docs/chapters/  # 检查整个目录")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob('*.html'))
    else:
        print(f"错误: 路径不存在: {path}")
        sys.exit(1)

    print(f"\n开始检查 {len(files)} 个HTML文件...\n")

    total_errors = 0
    total_warnings = 0
    failed_files = []

    for html_file in files:
        linter = HTMLLinter(html_file)
        success = linter.lint()

        total_errors += len(linter.errors)
        total_warnings += len(linter.warnings)

        if not success:
            failed_files.append(html_file.name)

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

    print("\n提示: 使用 -v 参数查看详细信息（未实现）")

    sys.exit(0 if total_errors == 0 else 1)


if __name__ == '__main__':
    main()
