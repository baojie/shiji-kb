#!/usr/bin/env python3
"""
找出tagged.md和原始txt之间的具体差异
"""

import re
import sys
from pathlib import Path
from validate_tagging import (
    remove_all_tags,
    normalize_text,
    get_paragraphs_from_md,
    extract_paragraph_number,
    get_root_number
)


def find_diff_position(str1, str2):
    """找到两个字符串第一个不同的位置"""
    for i, (c1, c2) in enumerate(zip(str1, str2)):
        if c1 != c2:
            return i
    return min(len(str1), len(str2))


def show_context(text, pos, context_len=50):
    """显示指定位置附近的文本"""
    start = max(0, pos - context_len)
    end = min(len(text), pos + context_len)
    before = text[start:pos]
    at = text[pos:pos+1] if pos < len(text) else '<END>'
    after = text[pos+1:end]
    return f"...{before}[{repr(at)}]{after}..."


if __name__ == '__main__':
    base_dir = Path('/home/baojie/work/shiji-kb')
    md_file = base_dir / 'chapter_md' / '005_秦本纪.tagged.md'
    txt_file = base_dir / 'chapter_numbered' / '005_秦本纪.txt'

    # 读取原始文本
    with open(txt_file, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # 清理原始文本
    clean_original = remove_all_tags(original_text)
    normalized_original = normalize_text(clean_original)

    # 获取md中的段落并分组
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

    # 检查每组段落
    print("=" * 80)
    print("文本差异详细分析")
    print("=" * 80)

    mismatch_count = 0
    for root_num in sorted(grouped_paragraphs.keys(), key=lambda x: int(x)):
        group = grouped_paragraphs[root_num]

        # 合并同一组的所有段落
        combined_text = ''
        for _, _, para in group:
            clean_para = remove_all_tags(para)
            if clean_para:
                combined_text += clean_para

        if not combined_text:
            continue

        # 标准化合并后的文本
        normalized_combined = normalize_text(combined_text)

        # 检查是否在原始文本中
        if normalized_combined not in normalized_original:
            mismatch_count += 1
            print(f"\n段落组 [{root_num}]")
            print(f"包含子段落: {[pn for _, pn, _ in group]}")

            # 找到最接近的匹配位置
            # 尝试找到第一个不匹配的字符
            # 在原始文本中查找前100个字符
            search_prefix = normalized_combined[:100]
            pos = normalized_original.find(search_prefix)

            if pos >= 0:
                # 找到了前缀，说明后面有差异
                orig_segment = normalized_original[pos:pos+len(normalized_combined)+100]
                diff_pos = find_diff_position(normalized_combined, orig_segment)
                print(f"\n前{len(search_prefix)}字符匹配，差异从位置 {diff_pos} 开始")
                print(f"MD版本: {show_context(normalized_combined, diff_pos)}")
                print(f"原始版本: {show_context(orig_segment, diff_pos)}")
            else:
                # 完全找不到，显示开头
                print(f"\n完全不匹配!")
                print(f"MD开头: {normalized_combined[:200]}")
                print(f"原始中是否包含: NO")

                # 尝试查找去标准化前的文本
                print(f"\n去标准化前的MD文本开头: {combined_text[:200]}")

    print(f"\n" + "=" * 80)
    print(f"总共发现 {mismatch_count} 个不匹配的段落组")
    print("=" * 80)
