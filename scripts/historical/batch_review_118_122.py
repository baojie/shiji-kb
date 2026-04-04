#!/usr/bin/env python3
"""
批量第二轮按章反思：118-122章
淮南衡山列传、循吏列传、汲郑列传、儒林列传、酷吏列传

按照SKILL_03c规则执行深度实体标注审查
"""
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 章节列表
CHAPTERS = [
    (118, '淮南衡山列传'),
    (119, '循吏列传'),
    (120, '汲郑列传'),
    (121, '儒林列传'),
    (122, '酷吏列传'),
]

# 修正规则集合（基于SKILL_03c §三）
class FixRules:
    """按章反思修正规则"""

    @staticmethod
    def fix_identity_tags(content):
        """官职→身份类型修正"""
        fixes = []
        # 天子/皇帝/太后等通称 → 身份
        identity_words = ['天子', '皇帝', '太后', '皇后', '陛下', '先帝', '先王',
                         '今王', '寡人', '人主', '单于', '诸侯', '今上']
        for word in identity_words:
            pattern = f'〖;{word}〗'
            if pattern in content:
                count = content.count(pattern)
                content = content.replace(pattern, f'〖#{word}〗')
                fixes.append(f'{pattern} → 〖#{word}〗 ({count}处)')
        return content, fixes

    @staticmethod
    def fix_penalty_tags(content):
        """制度→刑法类型修正"""
        fixes = []
        penalty_words = ['五刑', '弃市', '城旦', '坑杀', '车裂', '菹醢', '大辟',
                        '死罪', '赦免', '族诛', '诛', '伏诛', '免官', '削爵',
                        '赎死', '城旦舂']
        for word in penalty_words:
            pattern = f'〖\^{word}〗'
            if pattern in content:
                count = content.count(pattern)
                content = content.replace(pattern, f'〖[{word}〗')
                fixes.append(f'{pattern} → 〖[{word}〗 ({count}处)')
        return content, fixes

    @staticmethod
    def fix_thought_tags(content):
        """制度→思想类型修正"""
        fixes = []
        thought_words = ['仁义', '王道', '礼义', '道德', '天命', '五德', '无为',
                        '治乱', '富贵', '天道', '圣人', '阴德']
        for word in thought_words:
            pattern = f'〖\^{word}〗'
            if pattern in content:
                count = content.count(pattern)
                content = content.replace(pattern, f'〖_{word}〗')
                fixes.append(f'{pattern} → 〖_{word}〗 ({count}处)')
        return content, fixes

    @staticmethod
    def add_missing_penalties(content):
        """补充遗漏的刑法标注"""
        fixes = []
        # 刑法动词：杀/斩/诛/灭/攻/击/破/败/围等
        # 只标注明显的刑法动词，避免过度标注
        penalty_verbs = {
            '⟦◉杀⟧': '〖[⟦◉杀⟧〗',
            '⟦◉诛⟧': '〖[⟦◉诛⟧〗',
            '⟦◉族⟧': '〖[⟦◉族⟧〗',
            '⟦◉斩⟧': '〖[⟦◉斩⟧〗',
            '⟦◉刺⟧': '〖[⟦◉刺⟧〗',
            '⟦◉笞⟧': '〖[⟦◉笞⟧〗',
        }

        for verb, tagged in penalty_verbs.items():
            if verb in content and tagged not in content:
                count = content.count(verb)
                content = content.replace(verb, tagged)
                fixes.append(f'{verb} → {tagged} ({count}处)')

        return content, fixes

    @staticmethod
    def add_missing_war_actions(content):
        """补充遗漏的战争行为标注"""
        fixes = []
        war_verbs = {
            '⟦◈击⟧': '〖[⟦◈击⟧〗',
            '⟦◈攻⟧': '〖[⟦◈攻⟧〗',
            '⟦◈破⟧': '〖[⟦◈破⟧〗',
            '⟦◈败⟧': '〖[⟦◈败⟧〗',
            '⟦◈围⟧': '〖[⟦◈围⟧〗',
            '⟦◈取⟧': '〖[⟦◈取⟧〗',
        }

        for verb, tagged in war_verbs.items():
            if verb in content and tagged not in content:
                count = content.count(verb)
                content = content.replace(verb, tagged)
                fixes.append(f'{verb} → {tagged} ({count}处)')

        return content, fixes

    @staticmethod
    def fix_book_tags(content):
        """制度→典籍类型修正"""
        fixes = []
        book_words = ['诗', '书', '春秋', '麦秀']
        for word in book_words:
            pattern = f'〖\^{word}〗'
            if pattern in content:
                count = content.count(pattern)
                content = content.replace(pattern, f'〖{{{word}〗')
                fixes.append(f'{pattern} → 〖{{{word}〗 ({count}处)')
        return content, fixes

    @staticmethod
    def fix_group_identity(content):
        """补充群体称谓标注"""
        fixes = []
        # 这些词可能未标注或标注错误
        group_words = {
            '百姓': '〖#百姓〗',
            '群臣': '〖#群臣〗',
            '列侯': '〖#列侯〗',
            '宾客': '〖;宾客〗',
            '诸侯': '〖#诸侯〗',
            '士卒': '〖#士卒〗',
            '大臣': '〖#大臣〗',
        }

        for word, tagged in group_words.items():
            # 查找未标注的情况（前后无标注符号）
            pattern = f'([^〗]){word}([^〖])'
            matches = re.findall(pattern, content)
            if matches:
                # 只在明显应该标注的位置标注
                # 这里简化处理，实际应该更精细
                pass

        return content, fixes


def process_chapter(chapter_num, chapter_name):
    """处理单章"""
    print(f"\n{'='*70}")
    print(f"开始处理 {chapter_num}_{chapter_name}")
    print(f"{'='*70}")

    # 读取文件
    file_path = Path(f'chapter_md/{chapter_num}_{chapter_name}.tagged.md')
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return None

    content = file_path.read_text(encoding='utf-8')
    original_content = content

    all_fixes = defaultdict(list)

    # 应用各类修正规则
    print("\n执行修正规则...")

    content, fixes = FixRules.fix_identity_tags(content)
    if fixes:
        all_fixes['类型误标-官职→身份'].extend(fixes)

    content, fixes = FixRules.fix_penalty_tags(content)
    if fixes:
        all_fixes['类型误标-制度→刑法'].extend(fixes)

    content, fixes = FixRules.fix_thought_tags(content)
    if fixes:
        all_fixes['类型误标-制度→思想'].extend(fixes)

    content, fixes = FixRules.fix_book_tags(content)
    if fixes:
        all_fixes['类型误标-制度→典籍'].extend(fixes)

    content, fixes = FixRules.add_missing_penalties(content)
    if fixes:
        all_fixes['遗漏补充-刑法动词'].extend(fixes)

    content, fixes = FixRules.add_missing_war_actions(content)
    if fixes:
        all_fixes['遗漏补充-战争行为'].extend(fixes)

    # 统计修正
    total_fixes = sum(len(fixes) for fixes in all_fixes.values())

    if total_fixes == 0:
        print("✓ 未发现需要修正的问题")
        return None

    # 保存修正后的文件
    file_path.write_text(content, encoding='utf-8')

    # 返回修正报告
    report = {
        'chapter_num': chapter_num,
        'chapter_name': chapter_name,
        'total_fixes': total_fixes,
        'fixes_by_category': dict(all_fixes),
        'content_changed': content != original_content,
    }

    print(f"\n✓ 完成修正 {total_fixes} 处")
    for category, fixes in all_fixes.items():
        print(f"  - {category}: {len(fixes)}处")

    return report


def generate_report(reports):
    """生成汇总报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    report_lines = [
        f"# 第二轮按章实体反思报告（批量118-122章）\n",
        f"生成时间：{timestamp}\n",
        f"\n## 总体统计\n",
    ]

    total_chapters = len([r for r in reports if r])
    total_fixes_count = sum(r['total_fixes'] for r in reports if r)

    report_lines.append(f"- 处理章节数：{total_chapters}\n")
    report_lines.append(f"- 修正总数：{total_fixes_count}处\n")
    report_lines.append(f"- 平均修正：{total_fixes_count/total_chapters if total_chapters else 0:.1f}处/章\n")

    report_lines.append(f"\n## 各章详情\n")

    for report in reports:
        if not report:
            continue

        report_lines.append(f"\n### {report['chapter_num']}_{report['chapter_name']}\n")
        report_lines.append(f"\n修正统计：{report['total_fixes']}处\n")

        if report['fixes_by_category']:
            report_lines.append(f"\n| 修正类别 | 数量 |\n")
            report_lines.append(f"|---------|------|\n")
            for category, fixes in report['fixes_by_category'].items():
                report_lines.append(f"| {category} | {len(fixes)}处 |\n")

            report_lines.append(f"\n详细修正列表：\n")
            for category, fixes in report['fixes_by_category'].items():
                report_lines.append(f"\n**{category}**：\n")
                for fix in fixes[:10]:  # 只显示前10条
                    report_lines.append(f"- {fix}\n")
                if len(fixes) > 10:
                    report_lines.append(f"- ...及其他{len(fixes)-10}处\n")

    report_lines.append(f"\n## 说明\n")
    report_lines.append(f"\n本报告为自动化批量处理结果，基于SKILL_03c规则进行类型误标修正和遗漏补充。\n")
    report_lines.append(f"重点处理了以下问题：\n")
    report_lines.append(f"1. 官职→身份类型修正（天子/皇帝/陛下等通称）\n")
    report_lines.append(f"2. 制度→刑法类型修正（五刑/弃市/诛/族等）\n")
    report_lines.append(f"3. 制度→思想类型修正（仁义/王道/天道等）\n")
    report_lines.append(f"4. 制度→典籍类型修正（诗/书/春秋等）\n")
    report_lines.append(f"5. 遗漏刑法动词补充（杀/诛/斩/刺等）\n")
    report_lines.append(f"6. 遗漏战争行为补充（击/攻/破/败/围等）\n")
    report_lines.append(f"\n---\n")

    return ''.join(report_lines)


def main():
    """主函数"""
    print("=" * 70)
    print("批量第二轮按章反思：118-122章")
    print("=" * 70)

    reports = []

    for chapter_num, chapter_name in CHAPTERS:
        report = process_chapter(chapter_num, chapter_name)
        reports.append(report)

    # 生成汇总报告
    print(f"\n{'='*70}")
    print("生成汇总报告...")
    print(f"{'='*70}")

    report_content = generate_report(reports)

    # 追加到总报告文件
    report_file = Path('doc/entities/第二轮按章实体反思报告.md')
    if report_file.exists():
        existing = report_file.read_text(encoding='utf-8')
        report_content = existing + "\n\n" + report_content

    report_file.write_text(report_content, encoding='utf-8')

    print(f"\n✓ 报告已追加到：{report_file}")
    print(f"\n完成！")


if __name__ == '__main__':
    main()
