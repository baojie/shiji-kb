#!/usr/bin/env python3
"""
生成原始txt和tagged.md之间所有文本差异的详细报告
"""

import re
import sys
import difflib
from pathlib import Path
from validate_tagging import (
    remove_all_tags,
    get_paragraphs_from_md,
    extract_paragraph_number,
    get_root_number
)


def find_char_differences(str1, str2):
    """找出两个字符串之间的字符级差异"""
    diffs = []
    matcher = difflib.SequenceMatcher(None, str1, str2)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            diffs.append({
                'type': tag,
                'orig': str1[i1:i2],
                'tagged': str2[j1:j2],
                'pos': i1,
                'context_before': str1[max(0,i1-20):i1],
                'context_after': str1[i2:min(len(str1), i2+20)]
            })
    return diffs


if __name__ == '__main__':
    base_dir = Path('/home/baojie/work/shiji-kb')
    md_file = base_dir / 'chapter_md' / '005_秦本纪.tagged.md'
    txt_file = base_dir / 'chapter_numbered' / '005_秦本纪.txt'

    # 读取原始文本并按段落分组
    with open(txt_file, 'r', encoding='utf-8') as f:
        txt_content = f.read()

    # 提取原始文件中的段落
    orig_paragraphs = {}
    for match in re.finditer(r'\[(\d+(?:\.\d+)*)\]\s*([^\[]*?)(?=\n\n|\n\[|\Z)', txt_content, re.DOTALL):
        para_num = match.group(1)
        para_text = match.group(2).strip()
        root_num = para_num.split('.')[0]
        if root_num not in orig_paragraphs:
            orig_paragraphs[root_num] = []
        orig_paragraphs[root_num].append((para_num, para_text))

    # 获取md中的段落并分组
    paragraphs = get_paragraphs_from_md(md_file)
    md_paragraphs = {}
    for i, para in enumerate(paragraphs, 1):
        if para.startswith('#') or para.startswith('> [!NOTE]'):
            continue
        para_num = extract_paragraph_number(para)
        if para_num:
            root_num = get_root_number(para_num)
            if root_num not in md_paragraphs:
                md_paragraphs[root_num] = []
            clean_para = remove_all_tags(para)
            if clean_para:
                md_paragraphs[root_num].append((para_num, clean_para))

    # 比较每组段落
    print("=" * 100)
    print("原始TXT与Tagged MD之间的文本差异报告")
    print("=" * 100)

    total_diffs = 0
    for root_num in sorted(set(orig_paragraphs.keys()) | set(md_paragraphs.keys()), key=lambda x: int(x)):
        if root_num not in orig_paragraphs:
            print(f"\n警告: 段落组 [{root_num}] 在原始文件中不存在，但在MD文件中存在")
            continue

        if root_num not in md_paragraphs:
            print(f"\n警告: 段落组 [{root_num}] 在MD文件中不存在，但在原始文件中存在")
            continue

        # 合并原始段落
        orig_combined = ''.join(text for _, text in orig_paragraphs[root_num])
        md_combined = ''.join(text for _, text in md_paragraphs[root_num])

        if orig_combined != md_combined:
            total_diffs += 1
            print(f"\n{'='*100}")
            print(f"段落组 [{root_num}] 有差异")
            print(f"{'='*100}")

            # 找出具体差异
            diffs = find_char_differences(orig_combined, md_combined)

            for i, diff in enumerate(diffs, 1):
                print(f"\n差异 #{i} (类型: {diff['type']}):")
                print(f"  位置: 字符 {diff['pos']}")
                print(f"  上下文: ...{diff['context_before']}【此处有差异】{diff['context_after']}...")
                print(f"  原始TXT: 「{diff['orig']}」")
                print(f"  Tagged MD: 「{diff['tagged']}」")

                # 显示字符的Unicode码位
                if diff['orig'] and diff['tagged']:
                    if len(diff['orig']) == 1 and len(diff['tagged']) == 1:
                        print(f"  Unicode: U+{ord(diff['orig'][0]):04X} → U+{ord(diff['tagged'][0]):04X}")

    print(f"\n{'='*100}")
    print(f"总结: 共发现 {total_diffs} 个段落组有文本差异")
    print(f"{'='*100}")

