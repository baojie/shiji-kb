#!/usr/bin/env python3
"""
分析第二轮按章实体反思报告中的错误分类统计和规律
"""

import re
import json
from collections import defaultdict, Counter
from pathlib import Path

def parse_report(file_path):
    """解析反思报告"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计方法：以章节详情部分为准（有完整报告的才算）
    # 支持多种章节标题格式：### 001_章名、## 001_章名、## 001章_章名、## 第021章
    chapter_nums_with_details = set()

    # 格式1: ### 001_章名
    pattern1 = re.findall(r'^### (\d{3})_', content, re.MULTILINE)
    chapter_nums_with_details.update(pattern1)

    # 格式2: ## 001_章名 或 ## 001章_章名
    pattern2 = re.findall(r'^## (\d{3})[章_]', content, re.MULTILINE)
    chapter_nums_with_details.update(pattern2)

    # 格式3: ## 第021章
    pattern3 = re.findall(r'^## 第?(\d{3})章', content, re.MULTILINE)
    chapter_nums_with_details.update(pattern3)

    # 从章节详情中提取修正数（按章号累加，处理多轮反思）
    chapter_corrections = defaultdict(int)

    # 分割章节（支持 ## 和 ### 两种级别）
    # 使用更通用的分割方式
    for chapter_num in chapter_nums_with_details:
        # 查找该章所有相关内容
        patterns = [
            f'^### {chapter_num}_.*?(?=^##[^#]|\\Z)',
            f'^## {chapter_num}_.*?(?=^##[^#]|\\Z)',
            f'^## {chapter_num}章_.*?(?=^##[^#]|\\Z)',
            f'^## 第{chapter_num}章.*?(?=^##[^#]|\\Z)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                section = match.group(0)
                # 提取修正数（支持多种格式）
                correction_patterns = [
                    r'\*\*合计\*\*.*?\*\*(\d+)处\*\*',
                    r'合计.*?(\d+)处',
                    r'\((\d+)处修正\)',
                    r'修正.*?(\d+)处',
                ]
                for corr_pattern in correction_patterns:
                    correction_match = re.search(corr_pattern, section)
                    if correction_match:
                        corrections = int(correction_match.group(1))
                        chapter_corrections[chapter_num] += corrections
                        break

    completed_corrections = list(chapter_corrections.values())
    total_chapters = len(chapter_nums_with_details)  # 使用有详情的章节数（去重）
    total_corrections = sum(completed_corrections)  # 所有轮次的修正总数

    # 高频问题
    high_freq_pattern = re.compile(r'(\d+)\.\s+(.*?)\((\d+)处[,，]占(\d+)%\)')
    high_freq_issues = high_freq_pattern.findall(content)

    # 新发现规律
    new_rules_section = re.search(r'\*\*新发现规律\*\*：(.*?)---', content, re.DOTALL)
    new_rules = []
    if new_rules_section:
        new_rules_text = new_rules_section.group(1)
        new_rules = re.findall(r'\d+\.\s+(.*?)(?=\n\d+\.|$)', new_rules_text, re.DOTALL)

    # 按章统计
    chapter_stats = []
    chapter_pattern = re.compile(r'###\s+(\d+)_(.*?)（第.*?轮）.*?\*\*修正统计\*\*：.*?合计.*?\*\*(\d+)处\*\*', re.DOTALL)
    chapters = chapter_pattern.finditer(content)

    # 错误类型统计
    error_types = defaultdict(int)
    error_details = defaultdict(list)

    # 章节详细信息
    chapter_sections = re.split(r'###\s+\d+_', content)[1:]  # 跳过开头

    for section in chapter_sections:
        # 提取章节编号和名称
        title_match = re.match(r'(.*?)（第.*?轮）', section)
        if not title_match:
            continue

        chapter_title = title_match.group(1).strip()

        # 提取修正数
        correction_match = re.search(r'\*\*合计\*\*.*?\*\*(\d+)处\*\*', section)
        if not correction_match:
            continue

        corrections = int(correction_match.group(1))

        # 提取修正类别 - 排除表头和无关行
        category_pattern = re.compile(r'\|\s+([^|]+?)\s+\|\s+(\d+)处')
        categories = []
        for match in category_pattern.finditer(section):
            cat_name = match.group(1).strip()
            cat_count = match.group(2)

            # 过滤掉非类别名称的行
            if cat_name in ['修正类别', '合计', '**合计**']:
                continue
            if re.match(r'^(第[一二三]轮|202\d-\d{2}-\d{2})$', cat_name):
                continue
            if re.match(r'^\d+$', cat_name):  # 纯数字
                continue

            categories.append((cat_name, cat_count))

        chapter_info = {
            'title': chapter_title,
            'corrections': corrections,
            'categories': {}
        }

        for cat_name, cat_count in categories:
            cat_name = cat_name.strip()
            cat_count = int(cat_count)
            chapter_info['categories'][cat_name] = cat_count
            error_types[cat_name] += cat_count

        # 提取章节特有发现
        findings_match = re.search(r'####\s+[A-Z]?\.\s*章节特有发现(.*?)(?=####|$)', section, re.DOTALL)
        if findings_match:
            findings_text = findings_match.group(1)
            findings = re.findall(r'\d+\.\s+\*\*(.*?)\*\*[：:]', findings_text)
            chapter_info['findings'] = findings
        else:
            chapter_info['findings'] = []

        chapter_stats.append(chapter_info)

    return {
        'total_chapters': total_chapters,
        'total_corrections': total_corrections,
        'completed_corrections': completed_corrections,
        'high_freq_issues': high_freq_issues,
        'new_rules': [r.strip() for r in new_rules],
        'error_types': dict(error_types),
        'chapter_stats': chapter_stats
    }

def categorize_errors(error_types):
    """对错误类型进行归类"""
    categories = {
        '遗漏类': [],
        '误标类': [],
        '边界/格式类': [],
        '消歧类': [],
        '其他': []
    }

    for error_type, count in error_types.items():
        if '遗漏' in error_type or '补充' in error_type:
            categories['遗漏类'].append((error_type, count))
        elif '误标' in error_type or '误' in error_type:
            categories['误标类'].append((error_type, count))
        elif '边界' in error_type or '格式' in error_type:
            categories['边界/格式类'].append((error_type, count))
        elif '消歧' in error_type:
            categories['消歧类'].append((error_type, count))
        else:
            categories['其他'].append((error_type, count))

    return categories

def extract_entity_type_stats(error_types):
    """提取实体类型统计（拆分复合类型，平均分配计数）"""
    entity_stats = defaultdict(float)

    # 实体类型关键词映射
    entity_keywords = {
        '刑法': ['刑法'],
        '军事': ['军事'],
        '人名': ['人名'],
        '地名': ['地名'],
        '官职': ['官职'],
        '身份': ['身份'],
        '器物': ['器物'],
        '礼仪': ['礼仪'],
        '氏族': ['氏族'],
        '邦国': ['邦国', '国名'],
        '时间': ['时间'],
        '数量': ['数量'],
        '典籍': ['典籍'],
        '制度': ['制度'],
        '思想': ['思想'],
        '生物': ['生物'],
        '天文': ['天文'],
        '作物': ['作物']
    }

    for error_type, count in error_types.items():
        # 找出所有匹配的实体类型
        matched_types = []
        for entity_type, keywords in entity_keywords.items():
            if any(kw in error_type for kw in keywords):
                matched_types.append(entity_type)

        # 如果匹配到多个类型（如"刑法/军事"），则平均分配计数
        if matched_types:
            count_per_type = count / len(matched_types)
            for entity_type in matched_types:
                entity_stats[entity_type] += count_per_type

    # 转换为整数（四舍五入）
    return {k: int(round(v)) for k, v in entity_stats.items()}

def generate_report(data):
    """生成统计报告"""
    report = []

    report.append("=" * 80)
    report.append("第二轮按章实体反思报告 - 错误分类统计与规律分析")
    report.append("=" * 80)
    report.append("")

    # 一、总体统计
    report.append("## 一、总体统计")
    report.append("")
    report.append(f"- 已完成章节数：{data['total_chapters']} / 130")
    report.append(f"- 总修正数：{data['total_corrections']} 处")
    if data['total_chapters'] > 0:
        report.append(f"- 平均每章修正数：{data['total_corrections'] // data['total_chapters']} 处")
    else:
        report.append(f"- 平均每章修正数：N/A（无章节数据）")
    report.append("")

    # 二、高频问题 TOP 5
    report.append("## 二、高频问题 TOP 5")
    report.append("")
    if data['high_freq_issues']:
        for rank, issue, count, pct in data['high_freq_issues']:
            report.append(f"{rank}. **{issue}** - {count}处 (占{pct}%)")
    report.append("")

    # 三、错误类型大类统计
    report.append("## 三、错误类型大类统计")
    report.append("")

    categorized = categorize_errors(data['error_types'])
    for cat_name, items in categorized.items():
        if items:
            total = sum(count for _, count in items)
            report.append(f"### {cat_name} - 共 {total} 处")
            report.append("")
            sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
            for error_type, count in sorted_items[:10]:  # 显示前10个
                report.append(f"- {error_type}: {count}处")
            report.append("")

    # 四、实体类型统计
    report.append("## 四、按实体类型统计")
    report.append("")
    report.append("> **说明**: 由于一个修正可能涉及多个实体类型（如\"刑法/军事动词遗漏\"同时涉及刑法和军事类），本表采用平均分配策略。因此各类型占比之和会超过100%，这是正常的交叉统计现象。")
    report.append("")

    entity_stats = extract_entity_type_stats(data['error_types'])
    sorted_entities = sorted(entity_stats.items(), key=lambda x: x[1], reverse=True)

    report.append("| 实体类型 | 错误数 | 占比 |")
    report.append("|---------|--------|------|")
    for entity_type, count in sorted_entities:
        pct = count * 100 / data['total_corrections']
        report.append(f"| {entity_type} | {count} | {pct:.1f}% |")
    report.append("")

    # 五、新发现规律
    report.append("## 五、新发现规律总结")
    report.append("")
    for i, rule in enumerate(data['new_rules'], 1):
        report.append(f"{i}. {rule}")
    report.append("")

    # 六、章节修正数分布
    report.append("## 六、章节修正数分布")
    report.append("")

    # 使用completed_corrections进行统计
    correction_ranges = {
        '0-10处': 0,
        '11-30处': 0,
        '31-50处': 0,
        '51-80处': 0,
        '81-100处': 0,
        '101-150处': 0,
        '151-200处': 0,
        '200+处': 0
    }

    # 从data中获取completed_corrections
    all_corrections = data.get('completed_corrections', [])
    if not all_corrections:
        # 备用：从chapter_stats获取
        all_corrections = [ch['corrections'] for ch in data['chapter_stats']]

    for corr in all_corrections:
        if corr <= 10:
            correction_ranges['0-10处'] += 1
        elif corr <= 30:
            correction_ranges['11-30处'] += 1
        elif corr <= 50:
            correction_ranges['31-50处'] += 1
        elif corr <= 80:
            correction_ranges['51-80处'] += 1
        elif corr <= 100:
            correction_ranges['81-100处'] += 1
        elif corr <= 150:
            correction_ranges['101-150处'] += 1
        elif corr <= 200:
            correction_ranges['151-200处'] += 1
        else:
            correction_ranges['200+处'] += 1

    report.append("| 修正数范围 | 章节数 |")
    report.append("|-----------|--------|")
    for range_name, count in correction_ranges.items():
        report.append(f"| {range_name} | {count} |")
    report.append("")

    # 七、典型章节案例
    report.append("## 七、典型章节案例")
    report.append("")

    # 修正数最多的章节
    top_chapters = sorted(data['chapter_stats'], key=lambda x: x['corrections'], reverse=True)[:5]
    report.append("### 修正数最多的章节 TOP 5")
    report.append("")
    for i, chapter in enumerate(top_chapters, 1):
        report.append(f"{i}. **{chapter['title']}** - {chapter['corrections']}处")
        if chapter['categories']:
            top_cats = sorted(chapter['categories'].items(), key=lambda x: x[1], reverse=True)[:3]
            report.append(f"   主要类型: {', '.join([f'{k}({v})' for k, v in top_cats])}")
        report.append("")

    # 修正数最少的章节（排除0）
    bottom_chapters = sorted([c for c in data['chapter_stats'] if c['corrections'] > 0],
                            key=lambda x: x['corrections'])[:5]
    report.append("### 修正数最少的章节 TOP 5")
    report.append("")
    for i, chapter in enumerate(bottom_chapters, 1):
        report.append(f"{i}. **{chapter['title']}** - {chapter['corrections']}处")
        report.append("")

    # 八、章节特有发现汇总
    report.append("## 八、章节特有发现汇总（高价值规律）")
    report.append("")

    all_findings = []
    for chapter in data['chapter_stats']:
        if chapter['findings']:
            for finding in chapter['findings']:
                all_findings.append((chapter['title'], finding))

    # 提取问题模式分类
    finding_patterns = Counter()
    for _, finding in all_findings:
        finding_lower = finding.lower()

        # 优先级1: 质量评估类（不算实际问题）
        if '质量' in finding or '基线' in finding or '特点' in finding or '特殊性' in finding or '对比' in finding:
            finding_patterns['质量/特征评述'] += 1
        # 优先级2: 误标类
        elif '误标' in finding or '误判' in finding or '混淆' in finding:
            finding_patterns['类型误标/混淆'] += 1
        # 优先级3: 语境判断
        elif '语境' in finding or '同形异义' in finding or 'vs' in finding:
            finding_patterns['语境判断问题'] += 1
        # 优先级4: 消歧和边界
        elif '消歧' in finding:
            finding_patterns['消歧问题'] += 1
        elif '边界' in finding:
            finding_patterns['边界问题'] += 1
        # 优先级5: 标注不一致
        elif '不一致' in finding or '一致性' in finding:
            finding_patterns['标注一致性问题'] += 1
        # 优先级6: 遗漏类（按实体类型细分）
        elif '遗漏' in finding or '高频' in finding or '密集' in finding or '补充' in finding or '标注' in finding or '称' in finding:
            if '人名' in finding or '省称' in finding or '主人公' in finding:
                finding_patterns['人名/省称遗漏'] += 1
            elif '身份' in finding or '群臣' in finding or '百姓' in finding or '诸侯' in finding or '群体' in finding or '称谓' in finding:
                finding_patterns['身份类遗漏'] += 1
            elif '器物' in finding or '车' in finding or '印' in finding or '衣' in finding or '财物' in finding or '礼器' in finding:
                finding_patterns['器物类遗漏'] += 1
            elif '刑法' in finding or '诛' in finding or '杀' in finding:
                finding_patterns['刑法词汇遗漏'] += 1
            elif '官职' in finding or '百工' in finding:
                finding_patterns['官职遗漏'] += 1
            elif '礼仪' in finding:
                finding_patterns['礼仪遗漏'] += 1
            elif '数量' in finding:
                finding_patterns['数量遗漏'] += 1
            elif '时间' in finding or '时长' in finding:
                finding_patterns['时间相关'] += 1
            else:
                finding_patterns['其他遗漏/标注'] += 1
        # 优先级7: 场景分析
        elif '场景' in finding or '战争' in finding or '主题' in finding:
            finding_patterns['场景化分析'] += 1
        else:
            finding_patterns['其他发现'] += 1

    if finding_patterns:
        report.append("### 高频问题模式分类")
        report.append("")
        for pattern, count in finding_patterns.most_common(15):
            pct = count * 100 / len(all_findings) if all_findings else 0
            report.append(f"- **{pattern}** - {count}次 ({pct:.1f}%)")
        report.append("")

    # 九、质量基线分析
    report.append("## 九、质量基线分析")
    report.append("")
    report.append("质量基线：正常章节（300-1000行）预期30-80处修正")
    report.append("")

    below_baseline = [c for c in data['chapter_stats'] if c['corrections'] < 20]
    above_baseline = [c for c in data['chapter_stats'] if c['corrections'] > 80]

    report.append(f"- 低于基线（<20处）的章节: {len(below_baseline)} 个")
    if below_baseline:
        for chapter in below_baseline[:10]:
            report.append(f"  - {chapter['title']}: {chapter['corrections']}处")
    report.append("")

    report.append(f"- 超过基线（>80处）的章节: {len(above_baseline)} 个")
    if above_baseline:
        for chapter in above_baseline:
            report.append(f"  - {chapter['title']}: {chapter['corrections']}处")
    report.append("")

    # 十、规律总结
    report.append("## 十、核心规律总结")
    report.append("")
    report.append("### 1. 遗漏类高发区")
    report.append("- **身份类**: 群臣、百姓、诸侯、士卒等群体性身份词")
    report.append("- **器物类**: 金、衣、车、剑、印等常见器物")
    report.append("- **刑法类**: 诛、杀、灭、阬、弑等刑法动词")
    report.append("- **人名省称**: 历史名人在段落中重复出现时的省称")
    report.append("")

    report.append("### 2. 误标类高发区")
    report.append("- **同形异义词**: 非子、得意、释之等可能是词组而非人名")
    report.append("- **谥号混淆**: 谥号误标为官职（XX侯）")
    report.append("- **时间/时长混淆**: X年/X岁的类型判断")
    report.append("- **礼仪/制度混淆**: 冠礼、聘享等行为vs制度")
    report.append("")

    report.append("### 3. 场景化遗漏模式")
    report.append("- **战争场景**: 器物（车、剑、弓、矢、旗、鼓）密集")
    report.append("- **政治斗争**: 刑法词汇（诛、杀、灭）集中")
    report.append("- **祭祀场景**: 礼器、礼仪词汇容易因专题盲区忽略")
    report.append("- **表格体裁**: 年表中人名、地名、谥号大量重复")
    report.append("")

    report.append("### 4. 语境判断关键点")
    report.append("- **稷**: 任命语境→官职，与人名并列→人名")
    report.append("- **族**: 动词族诛→刑法，名词宗族→氏族")
    report.append("- **王冠**: 成年加冠礼→礼仪，帽子→器物")
    report.append("- **网**: 捕猎工具→器物，抽象网络→不标注")
    report.append("")

    return "\n".join(report)

def main():
    report_file = Path('/home/baojie/work/shiji-kb/doc/entities/第二轮按章实体反思报告.md')

    print("正在解析报告...")
    data = parse_report(report_file)

    print(f"解析完成：")
    print(f"  - 章节数: {data['total_chapters']}")
    print(f"  - 修正总数: {data['total_corrections']}")
    print(f"  - 错误类型数: {len(data['error_types'])}")
    print()

    print("生成统计报告...")
    report = generate_report(data)

    # 输出报告
    output_file = Path('/home/baojie/work/shiji-kb/doc/entities/第二轮反思_错误分类统计报告.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"报告已保存至: {output_file}")
    print()

    # 保存JSON数据
    json_file = Path('/home/baojie/work/shiji-kb/doc/entities/第二轮反思_统计数据.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"数据已保存至: {json_file}")

    # 打印到屏幕
    print("\n" + "=" * 80)
    print(report)

if __name__ == '__main__':
    main()
