#!/usr/bin/env python3
"""
生成增强版段落结构HTML（支持多种关系类型可视化）
"""

import json
from pathlib import Path

def generate_html(json_path, output_path):
    """生成HTML页面"""

    # 读取JSON数据
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    paragraphs = data['paragraphs']
    relations = data['relations']

    # 按section分组
    sections = {}
    for para in paragraphs:
        section = para['section']
        if section not in sections:
            sections[section] = []
        sections[section].append(para)

    # 关系类型配色
    relation_colors = {
        'temporal': '#999',        # 灰色 - 时序关系
        'causal': '#e74c3c',       # 红色 - 因果关系
        'genealogy': '#9b59b6',    # 紫色 - 世系关系
        'hierarchy': '#3498db',    # 蓝色 - 总分关系
        'parallel': '#2ecc71',     # 绿色 - 并列关系
        'contrast': '#e67e22',     # 橙色 - 对比关系
        'meta': '#95a5a6',         # 浅灰 - 元评论
        'elaboration': '#1abc9c'   # 青色 - 补充说明
    }

    # 统计各类关系数量
    relation_stats = {}
    for rel in relations:
        rel_type = rel['type']
        if rel_type not in relation_stats:
            relation_stats[rel_type] = 0
        relation_stats[rel_type] += 1

    # 生成HTML
    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>《史记》段落结构分析 - 五帝本纪（增强版）</title>
    <style>
        body {{
            font-family: "Songti SC", "SimSun", serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
            line-height: 1.8;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}

        h1 {{
            text-align: center;
            color: #8B4513;
            border-bottom: 3px double #8B4513;
            padding-bottom: 15px;
            margin-bottom: 10px;
        }}

        .subtitle {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 30px;
        }}

        .stats {{
            background: #fffaf0;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
            border-left: 5px solid #8B4513;
        }}

        .stats h3 {{
            color: #8B4513;
            margin-top: 0;
            margin-bottom: 15px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}

        .stat-item {{
            background: white;
            padding: 10px;
            border-radius: 3px;
            border-left: 3px solid #ddd;
        }}

        .legend {{
            background: #f9f9f9;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}

        .legend h4 {{
            margin-top: 0;
            color: #8B4513;
        }}

        .legend-items {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 8px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 0.9em;
        }}

        .legend-color {{
            width: 20px;
            height: 3px;
            margin-right: 8px;
        }}

        .graph {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 5px;
        }}

        .node {{
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .node-header {{
            font-size: 1.2em;
            font-weight: bold;
            color: #8B4513;
            margin-bottom: 10px;
            border-bottom: 2px solid #deb887;
            padding-bottom: 5px;
        }}

        .paragraph {{
            margin: 8px 0;
            padding: 8px;
            background: #fff;
            border-radius: 3px;
            font-size: 0.9em;
            border-left: 3px solid #deb887;
        }}

        .para-anchor {{
            color: #8B4513;
            font-weight: bold;
            margin-right: 5px;
        }}

        .para-subsection {{
            color: #666;
            font-style: italic;
            margin-right: 5px;
        }}

        .para-summary {{
            color: #555;
        }}

        .relation-viz {{
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
        }}

        .relation-group {{
            margin: 15px 0;
        }}

        .relation-type-header {{
            font-weight: bold;
            margin-bottom: 8px;
            padding: 5px 10px;
            background: #f5f5f5;
            border-radius: 3px;
        }}

        .relation-item {{
            font-size: 0.85em;
            padding: 5px 10px;
            margin: 3px 0;
            border-left: 3px solid;
            background: #fafafa;
        }}

        .notice {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            color: #856404;
        }}

        .notice strong {{
            color: #8B4513;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>《史记》章节段落语义关系分析</h1>
        <div class="subtitle">示例：001_五帝本纪（增强版 - 多维关系）</div>

        <div class="stats">
            <h3>📊 统计数据</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <strong>章节</strong>: {data['chapter']}<br>
                    <strong>总段落</strong>: {data['total_paragraphs']}个
                </div>
                <div class="stat-item">
                    <strong>大节数</strong>: {len(sections)}个<br>
                    <strong>关系数</strong>: {len(relations)}个
                </div>
                <div class="stat-item">
                    <strong>关系类型</strong>: {len(relation_stats)}种<br>
                    <strong>最多</strong>: {max(relation_stats.items(), key=lambda x: x[1])[0]} ({max(relation_stats.values())}个)
                </div>
            </div>
        </div>

        <div class="legend">
            <h4>🎨 关系类型图例</h4>
            <div class="legend-items">
'''

    # 添加图例
    relation_names = {
        'temporal': '时序关系',
        'causal': '因果关系',
        'genealogy': '世系关系',
        'hierarchy': '总分关系',
        'parallel': '并列关系',
        'contrast': '对比关系',
        'meta': '元评论',
        'elaboration': '补充说明'
    }

    for rel_type, color in relation_colors.items():
        count = relation_stats.get(rel_type, 0)
        name = relation_names.get(rel_type, rel_type)
        html += f'''
                <div class="legend-item">
                    <div class="legend-color" style="background: {color};"></div>
                    <span>{name} ({count})</span>
                </div>'''

    html += '''
            </div>
        </div>

        <div class="notice">
            <strong>⚠️ 开发中 (WIP)</strong><br>
            这是 SKILL-02d "段落语义关系建模" 的初步成果。目前已完成《五帝本纪》的多维关系分析，包含8种关系类型、101个具体关系。
            <br><br>
            <strong>已识别的关系类型</strong>：
            <ul style="margin: 5px 0;">
                <li>时序关系 (temporal): 同一叙事线的时间先后</li>
                <li>因果关系 (causal): 前因后果的逻辑联系</li>
                <li>世系关系 (genealogy): 帝王传承与禅让</li>
                <li>总分关系 (hierarchy): 总述与分述、总结</li>
                <li>并列关系 (parallel): 五帝的并列描述</li>
                <li>对比关系 (contrast): 善恶、逆境与美德的对照</li>
                <li>元评论 (meta): 太史公对全文的评论</li>
                <li>补充说明 (elaboration): 对前文的详细展开</li>
            </ul>
            后续将扩展到全部130篇章节。
        </div>

        <div class="graph">
            <h3 style="color: #8B4513; margin-top: 0;">📖 段落结构图</h3>
'''

    # 生成section节点HTML
    section_order = ['黄帝', '帝颛顼', '帝喾', '帝尧', '帝舜', '举贤任能', '五帝', '太史公']

    for section_name in section_order:
        if section_name not in sections:
            continue

        paras = sections[section_name]

        html += f'''
            <div class="node">
                <div class="node-header">【{section_name}】- {len(paras)}个段落</div>
'''

        # 显示所有段落
        for para in paras:
            subsection = para.get('subsection', '')
            subsection_html = f'<span class="para-subsection">{subsection}</span>' if subsection else ''
            html += f'''
                <div class="paragraph">
                    <span class="para-anchor">[{para['anchor']}]</span>
                    {subsection_html}
                    <span class="para-summary">{para['summary'][:60]}...</span>
                </div>'''

        html += '''
            </div>
'''

    html += '''
        </div>

        <div class="relation-viz">
            <h3 style="color: #8B4513; margin-top: 0;">🔗 关系可视化</h3>
            <p style="color: #666; font-size: 0.9em; margin-bottom: 15px;">
                显示前50个关系（按类型分组）
            </p>
'''

    # 按类型分组显示关系
    relation_by_type = {}
    for rel in relations:
        rel_type = rel['type']
        if rel_type not in relation_by_type:
            relation_by_type[rel_type] = []
        relation_by_type[rel_type].append(rel)

    for rel_type in ['genealogy', 'causal', 'parallel', 'contrast', 'hierarchy', 'meta', 'elaboration', 'temporal']:
        if rel_type not in relation_by_type:
            continue

        rels = relation_by_type[rel_type]
        color = relation_colors[rel_type]
        name = relation_names[rel_type]

        # 限制每种类型显示的数量
        display_limit = 10 if rel_type != 'temporal' else 5

        html += f'''
            <div class="relation-group">
                <div class="relation-type-header" style="border-left: 4px solid {color};">
                    {name} ({len(rels)}个)
                </div>
'''

        for rel in rels[:display_limit]:
            desc = rel.get('description', '')
            html += f'''
                <div class="relation-item" style="border-left-color: {color};">
                    [{rel['source']}] → [{rel['target']}]: {desc}
                </div>'''

        if len(rels) > display_limit:
            html += f'''
                <div style="font-size: 0.85em; color: #999; padding: 5px 10px; font-style: italic;">
                    ... 还有{len(rels) - display_limit}个{name}
                </div>'''

        html += '''
            </div>
'''

    html += '''
        </div>

        <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 0.9em;">
            <p>生成自《史记》知识库 - SKILL-02d 段落语义关系建模</p>
            <p>数据文件: kg/structure/data/paragraph_relations_001_enhanced.json</p>
        </div>
    </div>
</body>
</html>'''

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'✅ HTML已生成: {output_path}')
    print(f'   段落数: {data["total_paragraphs"]}')
    print(f'   关系数: {len(relations)}')
    print(f'   大节数: {len(sections)}')
    print(f'   关系类型: {len(relation_stats)}种')

def main():
    root = Path(__file__).resolve().parent.parent
    json_path = root / 'kg/structure/data/paragraph_relations_001_enhanced.json'
    output_path = root / 'docs/special/structure.html'

    generate_html(json_path, output_path)

if __name__ == '__main__':
    main()
