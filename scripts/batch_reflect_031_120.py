#!/usr/bin/env python3
"""
批量反思031-120章
按照SKILL_03c规则执行类型误标修正
"""
import re
from pathlib import Path
from collections import defaultdict

# 定义修正规则
RULES = {
    '制度→思想': {
        'pattern': r'〖\^({})〗',
        'replacement': r'〖_\1〗',
        'keywords': ['仁义', '王道', '礼义', '道德', '五德', '儒者', '墨者', '儒墨']
    },
    '制度→典籍': {
        'pattern': r'〖\^({})〗',
        'replacement': r'〖{{\1〗',
        'keywords': ['诗', '书', '礼', '乐', '易', '春秋', '甘誓', '甫刑',
                    '周南', '召南', '邶', '鄘', '卫风', '王', '郑', '齐', '豳', '秦', '魏',
                    '唐', '陈', '桧', '曹', '小雅', '大雅', '颂', '周乐']
    },
    '官职→身份': {
        'pattern': r'〖;({})〗',
        'replacement': r'〖#\1〗',
        'keywords': ['天子', '皇帝', '太后', '皇后', '诸侯', '今王', '先帝', '布衣', '匹夫',
                    '王者', '人主', '单于', '豪桀', '长者', '壮士', '丈夫', '少年', '大人',
                    '寡人', '陛下', '处士']
    },
    '制度→刑法': {
        'pattern': r'〖\^({})〗',
        'replacement': r'〖[\1〗',
        'keywords': ['五刑', '肉刑', '弃市', '城旦', '坑杀', '屠城', '菹醢', '车裂',
                    '禁锢', '画衣冠异章服', '相坐坐收', '收帑', '砲格之刑', '三族之罪']
    },
}

def apply_rules(content, chapter_num):
    """应用修正规则"""
    fixes = []

    for rule_name, rule_config in RULES.items():
        pattern_template = rule_config['pattern']
        replacement = rule_config['replacement']
        keywords = rule_config['keywords']

        # 构建正则表达式（使用|连接所有关键词）
        keywords_pattern = '|'.join(re.escape(kw) for kw in keywords)
        pattern = pattern_template.format(keywords_pattern)

        # 查找所有匹配
        matches = re.findall(pattern, content)
        if matches:
            # 去重统计
            unique_matches = set(matches)
            for match in unique_matches:
                count = content.count(pattern_template.replace('({})', match))
                fixes.append((rule_name, match, count))

            # 执行替换
            content = re.sub(pattern, replacement, content)

    return content, fixes

def process_chapters(start, end):
    """批量处理章节"""
    all_fixes = {}

    for chapter_num in range(start, end + 1):
        chapter_str = f"{chapter_num:03d}"
        files = list(Path("chapter_md").glob(f"{chapter_str}_*.tagged.md"))

        if not files:
            print(f"⚠ {chapter_str} 文件不存在")
            continue

        file_path = files[0]
        chapter_name = file_path.stem.replace('.tagged', '')

        # 读取文件
        content = file_path.read_text(encoding='utf-8')

        # 应用规则
        new_content, fixes = apply_rules(content, chapter_num)

        if fixes:
            # 保存修改
            file_path.write_text(new_content, encoding='utf-8')
            all_fixes[chapter_str] = (chapter_name, fixes)
            total = sum(f[2] for f in fixes)
            print(f"✓ {chapter_str} {chapter_name.split('_')[1]} 修正 {total} 处")
        else:
            print(f"○ {chapter_str} {chapter_name.split('_')[1]} 无需修正")

    return all_fixes

def generate_report(all_fixes, start, end):
    """生成反思报告"""
    report_lines = []

    for chapter_num in range(start, end + 1):
        chapter_str = f"{chapter_num:03d}"

        if chapter_str in all_fixes:
            chapter_name, fixes = all_fixes[chapter_str]
            name_only = chapter_name.split('_')[1]
            total = sum(f[2] for f in fixes)

            # 按类别统计
            by_category = defaultdict(list)
            for rule_name, match, count in fixes:
                by_category[rule_name].append((match, count))

            report_lines.append(f"\n## {chapter_str} {name_only}\n")
            report_lines.append(f"**反思日期**：2026-03-17")
            report_lines.append(f"**修正总数**：{total}处\n")
            report_lines.append("### 修正明细\n")
            report_lines.append("| 类别 | 数量 | 代表性内容 |")
            report_lines.append("|------|------|-----------|")

            for category, items in by_category.items():
                total_count = sum(c for _, c in items)
                content_str = '/'.join(m for m, _ in items[:10])  # 最多显示10个
                if len(items) > 10:
                    content_str += '等'
                report_lines.append(f"| {category} | {total_count} | {content_str} |")

            report_lines.append("\n### 章节特有发现\n")
            report_lines.append("无新发现。\n")
            report_lines.append("---\n")
        else:
            # 查找章节名
            files = list(Path("chapter_md").glob(f"{chapter_str}_*.tagged.md"))
            if files:
                name_only = files[0].stem.replace('.tagged', '').split('_')[1]
            else:
                name_only = "未找到"

            report_lines.append(f"\n## {chapter_str} {name_only}\n")
            report_lines.append(f"**反思日期**：2026-03-17")
            report_lines.append(f"**修正总数**：0处\n")
            report_lines.append("### 章节特有发现\n")
            report_lines.append("无新发现。\n")
            report_lines.append("---\n")

    return '\n'.join(report_lines)

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 3:
        print("用法: python batch_reflect_031_120.py <起始章> <结束章>")
        print("示例: python batch_reflect_031_120.py 36 40")
        sys.exit(1)

    start = int(sys.argv[1])
    end = int(sys.argv[2])

    print(f"\n开始批量处理 {start:03d}-{end:03d} 章...\n")

    all_fixes = process_chapters(start, end)

    print(f"\n处理完成！")
    print(f"总计修正章节: {len(all_fixes)}")
    print(f"总计修正次数: {sum(sum(f[2] for f in fixes) for _, fixes in all_fixes.values())}")

    # 生成报告
    report = generate_report(all_fixes, start, end)

    # 追加到反思报告
    with open('doc/entities/按章实体反思报告.md', 'a', encoding='utf-8') as f:
        f.write(report)

    print(f"\n报告已追加到 doc/entities/按章实体反思报告.md")
