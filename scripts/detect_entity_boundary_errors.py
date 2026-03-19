#!/usr/bin/env python3
"""
实体边界错误检测脚本

检测类型：
1. 标注吞噬前后文字：如"诸〖#侯服〗秦" → 应为"诸侯服秦"
2. 标注边界切分错误：如"〖@秦〗〖;王〗" → 应为"〖@秦王〗"
3. 标注内部包含不应包含的词：如"〖@李斯为相〗" → 应为"〖@李斯〗为相"
4. 标注边界缺失部分：如"〖@刘〗邦" → 应为"〖@刘邦〗"
"""

import re
from pathlib import Path
from collections import defaultdict
import json

# 目录
CHAPTER_DIR = Path('chapter_md')

# 常见边界错误模式
BOUNDARY_PATTERNS = [
    {
        'name': '身份词吞噬前文',
        'pattern': r'([一二三四五六七八九十百千万众诸群])(〖[_#;][^〗]+〗)',
        'desc': '数量词/范围词被标注吞噬',
        'example': '诸〖#侯〗 → 诸侯（不应标注）'
    },
    {
        'name': '动词被标注吞噬',
        'pattern': r'(〖[@\'&=][^〗]+)(为|曰|立|封|使|令|谓|称)([^〗]*)〗',
        'desc': '实体标注内包含动词',
        'example': '〖@李斯为相〗 → 〖@李斯〗为相'
    },
    {
        'name': '官职与人名分裂',
        'pattern': r'〖[@][^〗]+〗〖[;][^〗]+〗',
        'desc': '人名+官职分裂为两个标注',
        'example': '〖@秦〗〖;王〗 → 〖@秦王〗'
    },
    {
        'name': '姓氏与名字分裂',
        'pattern': r'〖[@]([^〗]{1,2})〗([^〖]{1,2})(?=[，。」\n])',
        'desc': '姓氏被标注，名字在外',
        'example': '〖@刘〗邦 → 〖@刘邦〗'
    },
    {
        'name': '地名吞噬后缀',
        'pattern': r'〖[=][^〗]+(之|者|人|氏)〗',
        'desc': '地名标注包含结构助词',
        'example': '〖=秦之〗 → 〖=秦〗之'
    },
    {
        'name': '实体内嵌套其他标注',
        'pattern': r'〖([^〗]+)〖([^〗]+)〗([^〗]+)〗',
        'desc': '标注内部嵌套另一标注',
        'example': '〖@李〖_斯〗相〗 → 格式错误'
    },
    {
        'name': '连续身份标注',
        'pattern': r'〖[_#]([^〗]+)〗〖[_#]([^〗]+)〗',
        'desc': '连续身份标注可能需要合并',
        'example': '〖_弟〗〖_子〗 → 〖_弟子〗'
    },
    {
        'name': '数量词被其他实体吞噬',
        'pattern': r'〖[^$][^〗]*(一|二|三|四|五|六|七|八|九|十|百|千|万|数)[^〗]*〗',
        'desc': '非数量实体标注内包含数量词',
        'example': '〖@三公〗 → 可能应为〖_三公〗（身份）'
    },
]

# 特殊词汇白名单（这些词内部包含数字但不是边界错误）
WHITELIST = {
    '三公', '九卿', '五帝', '三王', '四夷', '五刑', '九州',
    '六国', '七国', '八百', '三晋', '五霸', '十二诸侯',
    '天子', '诸侯', '百姓', '万民', '千里', '百里'
}

def check_boundary_errors(content, file_name):
    """检查单个文件的边界错误"""
    errors = []

    for pattern_info in BOUNDARY_PATTERNS:
        pattern = pattern_info['pattern']
        matches = re.finditer(pattern, content)

        for match in matches:
            matched_text = match.group(0)

            # 白名单过滤
            if any(word in matched_text for word in WHITELIST):
                continue

            # 获取上下文
            start = max(0, match.start() - 20)
            end = min(len(content), match.end() + 20)
            context = content[start:end]

            # 计算行号
            line_num = content[:match.start()].count('\n') + 1

            errors.append({
                'file': file_name,
                'line': line_num,
                'type': pattern_info['name'],
                'matched': matched_text,
                'context': context,
                'desc': pattern_info['desc'],
                'position': match.start()
            })

    return errors

def analyze_all_chapters():
    """分析所有章节"""
    all_errors = defaultdict(list)
    chapter_stats = {}

    tagged_files = sorted(CHAPTER_DIR.glob('*.tagged.md'))

    print(f"开始检查 {len(tagged_files)} 个章节的边界错误...\n")

    for file_path in tagged_files:
        chapter_num = file_path.stem.split('_')[0]

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        errors = check_boundary_errors(content, file_path.name)

        if errors:
            all_errors[chapter_num] = errors
            chapter_stats[chapter_num] = len(errors)
            print(f"✓ {chapter_num} - 发现 {len(errors)} 处疑似边界错误")

    return all_errors, chapter_stats

def generate_report(all_errors, chapter_stats):
    """生成报告"""
    total_errors = sum(chapter_stats.values())

    print(f"\n{'='*60}")
    print(f"实体边界错误检测报告")
    print(f"{'='*60}\n")

    print(f"总计: {total_errors} 处疑似边界错误")
    print(f"涉及章节: {len(chapter_stats)} 章\n")

    # 按错误类型统计
    type_stats = defaultdict(int)
    for errors in all_errors.values():
        for error in errors:
            type_stats[error['type']] += 1

    print("按错误类型统计:")
    for error_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {error_type}: {count} 处")

    print(f"\n{'='*60}\n")

    # 详细错误列表（前50个示例）
    print("详细错误示例（前50个）:\n")

    all_errors_flat = []
    for chapter, errors in sorted(all_errors.items()):
        all_errors_flat.extend(errors)

    for i, error in enumerate(all_errors_flat[:50], 1):
        print(f"{i}. [{error['file']}:{error['line']}] {error['type']}")
        print(f"   匹配: {error['matched']}")
        print(f"   上下文: ...{error['context']}...")
        print(f"   说明: {error['desc']}\n")

    # 保存详细报告
    report_file = Path('logs/entity_boundary_errors_report.json')
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_errors': total_errors,
                'affected_chapters': len(chapter_stats),
                'type_stats': dict(type_stats),
                'chapter_stats': chapter_stats
            },
            'errors': {k: v for k, v in all_errors.items()}
        }, f, ensure_ascii=False, indent=2)

    print(f"完整报告已保存: {report_file}")

    # 生成TSV格式供人工审查
    tsv_file = Path('logs/entity_boundary_errors_review.tsv')
    with open(tsv_file, 'w', encoding='utf-8') as f:
        f.write("章节\t行号\t错误类型\t匹配文本\t上下文\t是否修复\t修复建议\n")
        for error in all_errors_flat:
            f.write(f"{error['file']}\t{error['line']}\t{error['type']}\t"
                   f"{error['matched']}\t{error['context']}\t\t\n")

    print(f"人工审查表已生成: {tsv_file}")

def main():
    """主函数"""
    all_errors, chapter_stats = analyze_all_chapters()
    generate_report(all_errors, chapter_stats)

if __name__ == '__main__':
    main()
