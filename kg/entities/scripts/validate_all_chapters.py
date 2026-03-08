#!/usr/bin/env python3
"""
验证多个章节的标注文件
"""

import sys
from pathlib import Path
from validate_tagging import validate_chapter


def validate_multiple_chapters(chapter_numbers):
    """验证多个章节"""
    base_dir = Path('/home/baojie/work/shiji-kb')

    results = []

    for num in chapter_numbers:
        # 构建文件路径
        md_file = base_dir / 'chapter_md' / f'{num:03d}_*.tagged.md'
        txt_file = base_dir / 'chapter_numbered' / f'{num:03d}_*.txt'

        # 使用glob查找文件
        md_files = list(base_dir.glob(f'chapter_md/{num:03d}_*.tagged.md'))
        txt_files = list(base_dir.glob(f'chapter_numbered/{num:03d}_*.txt'))

        if not md_files:
            print(f"\n⚠️  章节 {num:03d}: MD文件不存在")
            results.append({
                'chapter': num,
                'name': f'{num:03d}',
                'status': 'missing_md',
                'errors': 0
            })
            continue

        if not txt_files:
            print(f"\n⚠️  章节 {num:03d}: TXT文件不存在")
            results.append({
                'chapter': num,
                'name': f'{num:03d}',
                'status': 'missing_txt',
                'errors': 0
            })
            continue

        md_file = md_files[0]
        txt_file = txt_files[0]

        # 提取章节名称
        chapter_name = md_file.stem.replace('.tagged', '')

        print(f"\n{'='*80}")
        print(f"验证章节：{chapter_name}")
        print(f"{'='*80}")

        # 运行验证
        success = validate_chapter(md_file, txt_file)

        # 如果失败，统计错误数
        if not success:
            # 重新运行获取详细信息
            from validate_tagging import (
                remove_all_tags, normalize_text, get_paragraphs_from_md,
                extract_paragraph_number, get_root_number
            )

            with open(txt_file, 'r', encoding='utf-8') as f:
                original_text = f.read()
            clean_original = remove_all_tags(original_text)
            normalized_original = normalize_text(clean_original)

            paragraphs = get_paragraphs_from_md(md_file)
            grouped_paragraphs = {}
            for i, para in enumerate(paragraphs, 1):
                if para.startswith('#') or para.startswith('> [!NOTE]'):
                    continue
                para_num = extract_paragraph_number(para)
                if para_num:
                    root_num = get_root_number(para_num)
                    if root_num not in grouped_paragraphs:
                        grouped_paragraphs[root_num] = []
                    grouped_paragraphs[root_num].append((i, para_num, para))

            error_count = 0
            for root_num in sorted(grouped_paragraphs.keys(), key=lambda x: int(x)):
                group = grouped_paragraphs[root_num]
                combined_text = ''
                for _, _, para in group:
                    clean_para = remove_all_tags(para)
                    if clean_para:
                        combined_text += clean_para
                if combined_text:
                    normalized_combined = normalize_text(combined_text)
                    if normalized_combined not in normalized_original:
                        error_count += 1

            results.append({
                'chapter': num,
                'name': chapter_name,
                'status': 'failed',
                'errors': error_count
            })
        else:
            results.append({
                'chapter': num,
                'name': chapter_name,
                'status': 'passed',
                'errors': 0
            })

    return results


if __name__ == '__main__':
    # 验证章节 001-004
    chapters = [1, 2, 3, 4, 5]

    print("开始验证章节 001-005...")
    results = validate_multiple_chapters(chapters)

    # 生成汇总报告
    print(f"\n\n{'='*80}")
    print("汇总报告")
    print(f"{'='*80}\n")

    print(f"{'章节':<20} {'状态':<15} {'不匹配段落数':<15}")
    print("-" * 80)

    total_passed = 0
    total_failed = 0
    total_errors = 0

    for r in results:
        status_str = {
            'passed': '✅ 通过',
            'failed': '❌ 失败',
            'missing_md': '⚠️  缺少MD',
            'missing_txt': '⚠️  缺少TXT'
        }[r['status']]

        error_str = str(r['errors']) if r['errors'] > 0 else '-'

        print(f"{r['name']:<20} {status_str:<15} {error_str:<15}")

        if r['status'] == 'passed':
            total_passed += 1
        elif r['status'] == 'failed':
            total_failed += 1
            total_errors += r['errors']

    print("-" * 80)
    print(f"\n总计: {len(results)} 个章节")
    print(f"  ✅ 通过: {total_passed}")
    print(f"  ❌ 失败: {total_failed} (共 {total_errors} 个不匹配段落)")
    print(f"  ⚠️  其他: {len(results) - total_passed - total_failed}")

    # 返回状态码
    sys.exit(0 if total_failed == 0 else 1)
