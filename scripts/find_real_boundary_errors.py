#!/usr/bin/env python3
"""
精确查找真正的边界错误

基于语义规则判断
"""

import re
from pathlib import Path
from collections import defaultdict

chapter_dir = Path('chapter_md')

# 真正的边界错误规则
# 规则：X+标注 → 应该是 标注(X+内容)
boundary_error_rules = [
    {
        'name': '诸侯服边界错误',
        'pattern': r'诸〖\^侯服〗',
        'should_be': '〖#诸侯〗服',
        'reason': '"诸侯"是身份，"服"是动词'
    },
    {
        'name': '诸将边界可疑',
        'pattern': r'诸〖;将〗',
        'should_be': '〖#诸将〗?',
        'reason': '"诸将"（各位将领）通常是身份群体，不是官职'
    },
    {
        'name': '诸侯边界可疑',
        'pattern': r'诸〖;侯〗(?!〖)',  # 后面不跟标注
        'should_be': '〖#诸侯〗',
        'reason': '"诸侯"（各位诸侯）是身份，不是官职'
    },
    {
        'name': '诸侯王边界可疑',
        'pattern': r'诸〖;侯王〗',
        'should_be': '〖#诸侯王〗?',
        'reason': '"诸侯王"可能是身份群体'
    },
]

def find_errors():
    """查找所有边界错误"""
    all_errors = defaultdict(list)

    for file_path in sorted(chapter_dir.glob('*.tagged.md')):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        chapter_num = file_path.stem.split('_')[0]
        chapter_name = file_path.stem.split('_')[1]

        for rule in boundary_error_rules:
            pattern = rule['pattern']

            for match in re.finditer(pattern, content):
                # 获取上下文
                start = max(0, match.start() - 30)
                end = min(len(content), match.end() + 30)
                context = content[start:end]

                # 计算行号
                line_num = content[:match.start()].count('\n') + 1

                all_errors[rule['name']].append({
                    'chapter': chapter_num,
                    'chapter_name': chapter_name,
                    'line': line_num,
                    'matched': match.group(0),
                    'context': context,
                    'should_be': rule['should_be'],
                    'reason': rule['reason'],
                    'file': file_path
                })

    return all_errors

def print_report(all_errors):
    """打印报告"""
    total = sum(len(errors) for errors in all_errors.values())

    print("="*70)
    print("真正的边界错误检测报告")
    print("="*70)
    print(f"\n总计发现: {total} 处可能的边界错误\n")

    for error_type, errors in sorted(all_errors.items()):
        print(f"\n{error_type}: {len(errors)} 处")
        print("-"*70)
        print(f"应修改为: {errors[0]['should_be']}")
        print(f"理由: {errors[0]['reason']}\n")

        # 按章节统计
        by_chapter = defaultdict(int)
        for error in errors:
            by_chapter[error['chapter']] += 1

        print(f"涉及章节: {len(by_chapter)} 章")
        print(f"章节分布: {dict(sorted(by_chapter.items()))}\n")

        # 显示前5个示例
        print("示例:")
        for i, error in enumerate(errors[:5], 1):
            print(f"\n  {i}. [{error['chapter']}_{error['chapter_name']} 行{error['line']}]")
            print(f"     匹配: {error['matched']}")
            print(f"     上下文: ...{error['context']}...")

if __name__ == '__main__':
    all_errors = find_errors()
    print_report(all_errors)

    # 保存详细报告
    import json
    output_file = Path('logs/real_boundary_errors.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({k: v for k, v in all_errors.items()}, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n\n详细报告已保存: {output_file}")
