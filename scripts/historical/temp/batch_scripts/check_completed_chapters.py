#!/usr/bin/env python3
"""检查已完成的ontology-v2章节"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = PROJECT_ROOT / 'kg' / 'ontology' / 'ontology-v2' / 'chapters'

def check_empty_content(file_path):
    """检查文件是否包含空框架标记"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 检查空标记
            if '待根据原文补充' in content or '待补充' in content:
                return True
            # 检查空的小节标题（## 或 ### 后面只有空白或换行）
            if re.search(r'^##+ *$', content, re.MULTILINE):
                return True
            # 检查HTML注释形式的空框架 <!-- xxx -->
            if re.search(r'<!--.*?-->', content, re.DOTALL):
                return True
            # 检查空的JSON文件
            if file_path.suffix == '.json':
                content = content.strip()
                if content == '{}' or content == '':
                    return True
    except Exception:
        pass
    return False

def check_chapter(chapter_dir):
    """检查单个章节是否完成"""
    skus_dir = chapter_dir / 'skus'
    if not skus_dir.exists():
        return None

    facts_dir = skus_dir / 'facts'
    skills_dir = skus_dir / 'skills'

    fact_count = 0
    skill_count = 0
    has_empty = False

    # 统计facts
    if facts_dir.exists():
        for f in facts_dir.iterdir():
            if f.suffix in ['.md', '.json'] and not f.name.startswith('_TEMPLATE'):
                fact_count += 1
                if check_empty_content(f):
                    has_empty = True

    # 统计skills
    if skills_dir.exists():
        for f in skills_dir.iterdir():
            if f.suffix == '.md' and not f.name.startswith('_TEMPLATE'):
                skill_count += 1
                if check_empty_content(f):
                    has_empty = True

    total = fact_count + skill_count

    return {
        'chapter': chapter_dir.name,
        'facts': fact_count,
        'skills': skill_count,
        'total': total,
        'has_empty': has_empty,
        'completed': total >= 3 and not has_empty
    }

def main():
    """主函数"""
    chapters = []

    for chapter_dir in sorted(CHAPTERS_DIR.iterdir()):
        if not chapter_dir.is_dir() or not chapter_dir.name.startswith('chapter_'):
            continue

        result = check_chapter(chapter_dir)
        if result and result['total'] > 0:
            chapters.append(result)

    # 显示已完成章节
    print("✓ 已完成章节（3个以上SKU，无空框架）：")
    print("=" * 60)
    completed = [c for c in chapters if c['completed']]
    for c in completed:
        print(f"  {c['chapter']}: facts={c['facts']}, skills={c['skills']}, total={c['total']}")

    print(f"\n总计：{len(completed)} 个章节已完成")

    # 显示未完成但有内容的章节
    incomplete = [c for c in chapters if not c['completed'] and c['total'] > 0]
    if incomplete:
        print("\n⚠ 未完成章节（有内容但SKU<3或有空框架）：")
        print("=" * 60)
        for c in incomplete:
            status = "有空框架" if c['has_empty'] else f"SKU不足({c['total']})"
            print(f"  {c['chapter']}: facts={c['facts']}, skills={c['skills']} [{status}]")

    # 输出已完成章节路径列表（用于git add）
    print("\n已完成章节路径列表：")
    print("=" * 60)
    for c in completed:
        print(f"kg/ontology/ontology-v2/chapters/{c['chapter']}")

if __name__ == '__main__':
    main()
