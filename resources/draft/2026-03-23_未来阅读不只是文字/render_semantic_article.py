#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语义标注文章HTML渲染器
Semantic Annotation Article HTML Renderer

将 .tagged.md 文件转换为带有语义增强的交互式HTML
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class SemanticRenderer:
    """语义标注Markdown渲染器"""

    # 实体类型的中文标签
    TYPE_LABELS = {
        'PERSON': '人名',
        'BOOK': '书名',
        'EVENT': '事件',
        'TIME': '时间',
        'TECH': '技术',
        'CONCEPT': '概念',
        'TOOL': '工具',
        'JOB': '职业',
        'COUNTRY': '国家',
        'TITLE': '头衔',
        'VISUAL': '可视化',
        'NET': '网络',
        'TOPIC': '话题',
        'PROJECT': '项目',
        'GOD': '神话',
    }

    def __init__(self, input_file: Path):
        self.input_file = input_file
        self.entity_stats = defaultdict(int)
        self.entity_instances = defaultdict(list)

    def parse_tagged_markdown(self, content: str) -> str:
        """解析标注的Markdown内容"""
        # 解析标题
        content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        content = re.sub(r'^\*\*(.+?)\*\*$', r'<h2>\1</h2>', content, flags=re.MULTILINE)

        # 解析段落（连续的非空行）
        lines = content.split('\n')
        result = []
        paragraph = []

        for line in lines:
            line = line.strip()
            if line:
                # 如果已经是HTML标签，直接添加
                if line.startswith('<h'):
                    if paragraph:
                        result.append(self._wrap_paragraph(paragraph))
                        paragraph = []
                    result.append(line)
                else:
                    paragraph.append(line)
            else:
                if paragraph:
                    result.append(self._wrap_paragraph(paragraph))
                    paragraph = []

        if paragraph:
            result.append(self._wrap_paragraph(paragraph))

        return '\n\n'.join(result)

    def _wrap_paragraph(self, lines: List[str]) -> str:
        """包装段落"""
        content = ' '.join(lines)
        return f'<p>{content}</p>'

    def process_entities(self, content: str) -> str:
        """处理语义实体标注"""
        # 匹配 〖TYPE 显示名|规范名〗 或 〖TYPE 文本〗
        pattern = r'〖([A-Z_]+)\s+([^〗]+?)〗'

        def replace_entity(match):
            entity_type = match.group(1)
            entity_content = match.group(2)

            # 处理消歧语法 显示名|规范名
            if '|' in entity_content:
                display_name, canonical_name = entity_content.split('|', 1)
            else:
                display_name = canonical_name = entity_content

            # 统计
            self.entity_stats[entity_type] += 1
            self.entity_instances[entity_type].append({
                'display': display_name,
                'canonical': canonical_name
            })

            # 生成HTML
            type_label = self.TYPE_LABELS.get(entity_type, entity_type)
            entity_id = f"{entity_type}-{len(self.entity_instances[entity_type])}"

            return (
                f'<span class="entity entity-{entity_type}" '
                f'data-type="{type_label}" '
                f'data-entity-id="{entity_id}" '
                f'data-canonical="{canonical_name}">'
                f'{display_name}'
                f'</span>'
            )

        return re.sub(pattern, replace_entity, content)

    def generate_legend(self) -> str:
        """生成实体类型图例"""
        items = []
        for entity_type, count in sorted(self.entity_stats.items()):
            label = self.TYPE_LABELS.get(entity_type, entity_type)
            items.append(
                f'<div class="legend-item">'
                f'<div class="legend-color entity-{entity_type}"></div>'
                f'<span>{label} ({count})</span>'
                f'</div>'
            )

        return f'''
<div id="legend">
    <h3>实体类型图例</h3>
    <div class="legend-grid">
        {''.join(items)}
    </div>
</div>
'''

    def generate_statistics(self) -> str:
        """生成统计信息"""
        total = sum(self.entity_stats.values())
        unique_types = len(self.entity_stats)

        stats_items = [
            f'<div class="stat-item"><div class="stat-value">{total}</div><div class="stat-label">总标注数</div></div>',
            f'<div class="stat-item"><div class="stat-value">{unique_types}</div><div class="stat-label">实体类型</div></div>',
        ]

        # 前三名类型
        top_types = sorted(self.entity_stats.items(), key=lambda x: x[1], reverse=True)[:3]
        for entity_type, count in top_types:
            label = self.TYPE_LABELS.get(entity_type, entity_type)
            stats_items.append(
                f'<div class="stat-item">'
                f'<div class="stat-value">{count}</div>'
                f'<div class="stat-label">{label}</div>'
                f'</div>'
            )

        return f'''
<div id="statistics">
    <h3>标注统计</h3>
    <div class="stats-grid">
        {''.join(stats_items)}
    </div>
</div>
'''

    def generate_html(self, content: str, title: str = "语义标注文章") -> str:
        """生成完整的HTML文档"""
        # 处理实体标注
        content = self.process_entities(content)

        # 解析Markdown
        content = self.parse_tagged_markdown(content)

        # 生成图例和统计
        legend = self.generate_legend()
        statistics = self.generate_statistics()

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="semantic-reading.css">
</head>
<body data-annotation-mode="full">

    <!-- 控制面板 -->
    <div id="control-panel">
        <h3>阅读控制</h3>

        <div class="control-group">
            <label for="annotation-mode">标注模式</label>
            <select id="annotation-mode">
                <option value="full">完整标注</option>
                <option value="minimal">最小标注</option>
                <option value="none">无标注</option>
            </select>
        </div>

        <div class="control-group">
            <label>显示类型</label>
            <div class="checkbox-group" id="entity-filters">
                <!-- 动态生成 -->
            </div>
        </div>
    </div>

    <!-- 侧边信息面板 -->
    <div id="info-panel">
        <button class="close-btn" onclick="closeInfoPanel()">&times;</button>
        <div id="info-content">
            <p style="color: #6b7280;">点击标注的实体查看详情</p>
        </div>
    </div>

    <!-- 文章内容 -->
    <article id="main-content">
        {content}
    </article>

    <!-- 图例 -->
    {legend}

    <!-- 统计信息 -->
    {statistics}

    <script src="semantic-reading.js"></script>
</body>
</html>
'''

    def render(self, output_file: Path):
        """渲染文件"""
        print(f"读取文件: {self.input_file}")
        content = self.input_file.read_text(encoding='utf-8')

        # 提取标题
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else "语义标注文章"

        print(f"渲染HTML...")
        html = self.generate_html(content, title)

        print(f"写入文件: {output_file}")
        output_file.write_text(html, encoding='utf-8')

        print(f"\n✓ 渲染完成！")
        print(f"  - 总标注数: {sum(self.entity_stats.values())}")
        print(f"  - 实体类型: {len(self.entity_stats)}")
        print(f"  - 输出文件: {output_file}")


def main():
    """主函数"""
    script_dir = Path(__file__).parent
    input_file = script_dir / "未来阅读不只是文字.tagged.md"
    output_file = script_dir / "未来阅读不只是文字.html"

    if not input_file.exists():
        print(f"错误: 输入文件不存在: {input_file}")
        return

    renderer = SemanticRenderer(input_file)
    renderer.render(output_file)


if __name__ == "__main__":
    main()
