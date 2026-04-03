#!/usr/bin/env python3
"""
使用PN映射表更新timeline.html中的PN引用
"""

import json
import re
from pathlib import Path


def load_mapping(mapping_file: str) -> dict:
    """加载PN映射表"""
    with open(mapping_file) as f:
        return json.load(f)


def update_timeline(timeline_file: str, mapping: dict, output_file: str = None):
    """
    更新timeline.html中的PN引用
    """
    with open(timeline_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计
    total_replacements = 0
    chapters_updated = set()

    # 遍历每个章节的映射
    for chapter, pn_map in mapping.items():
        for old_pn, new_pn in pn_map.items():
            if not new_pn:  # 跳过未找到映射的
                continue

            # 构造替换模式
            # 匹配: href="../chapters/XXX_章节名.html#pn-YYY"
            pattern = rf'(href="../chapters/{re.escape(chapter)}\.html#pn-){re.escape(old_pn)}(")'
            replacement = rf'\g<1>{new_pn}\g<2>'

            # 同时替换锚点文本
            # 匹配: <a ...>YYY</a>  （段落编号链接文本）
            pattern2 = rf'({re.escape(chapter)}\.html#pn-{re.escape(old_pn)}" class="para-ref">){re.escape(old_pn)}(<)'
            replacement2 = rf'\g<1>{new_pn}\g<2>'

            # 执行替换
            new_content, count1 = re.subn(pattern, replacement, content)
            content, count2 = re.subn(pattern2, replacement2, new_content)

            if count1 > 0 or count2 > 0:
                total_replacements += max(count1, count2)
                chapters_updated.add(chapter)
                print(f"  {chapter} pn-{old_pn} -> pn-{new_pn}: {max(count1, count2)} 处")

    # 保存
    if output_file is None:
        output_file = timeline_file

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n更新完成:")
    print(f"  更新的章节: {len(chapters_updated)} 个")
    print(f"  更新的链接: {total_replacements} 处")
    print(f"  输出文件: {output_file}")


def main():
    timeline_file = 'docs/entities/timeline.html'
    mapping_file = '/tmp/pn_mapping_for_timeline.json'

    if not Path(mapping_file).exists():
        print(f"错误: 映射文件不存在 {mapping_file}")
        print("请先运行 find_pn_by_text.py 生成映射表")
        return

    if not Path(timeline_file).exists():
        print(f"错误: timeline文件不存在 {timeline_file}")
        return

    print("加载PN映射表...")
    mapping = load_mapping(mapping_file)
    print(f"  {len(mapping)} 个章节需要更新")

    print("\n应用PN映射到timeline.html...")
    update_timeline(timeline_file, mapping)


if __name__ == '__main__':
    main()
