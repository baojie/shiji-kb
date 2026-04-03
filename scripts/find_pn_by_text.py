#!/usr/bin/env python3
"""
通过文本内容查找对应的PN
策略：在chapter文件中搜索包含指定文本的段落，返回其PN
"""

import re
import subprocess
import json
from pathlib import Path


def clean_text_for_matching(text: str) -> str:
    """
    清理文本用于匹配
    去除所有标注符号、标点、空格
    """
    # 去除标注符号
    text = re.sub(r'[〖⟦][^〗⟧]*[〗⟧]', '', text)
    # 去除所有标点和空格
    text = re.sub(r'[\s"""\'\'：。，、；！？\[\]]', '', text)
    return text


def find_pn_by_content(commit: str, chapter_file: str, search_text: str) -> str:
    """
    在指定章节中查找包含search_text的段落的PN
    search_text: 已经清理过的文本（无标注、无标点）
    """
    # 查找文件
    chapter_num = re.match(r'(\d+)_', chapter_file).group(1)

    result = subprocess.run(
        ['git', 'ls-tree', '-r', '--name-only', '-z', commit],
        capture_output=True,
        text=True
    )

    tagged_files = [f for f in result.stdout.split('\0')
                    if f.endswith('.tagged.md') and chapter_num in f]

    target_file = None
    for f in tagged_files:
        if f'/{chapter_num}_' in f or f.startswith(f'{chapter_num}_'):
            if 'chapter_md/' in f:
                target_file = f
                break
            elif not target_file:
                target_file = f

    if not target_file:
        return None

    # 获取文件内容
    try:
        result = subprocess.run(
            ['git', 'show', f'{commit}:{target_file}'],
            capture_output=True,
            text=True,
            check=True
        )
        content = result.stdout
    except subprocess.CalledProcessError:
        return None

    # 提取所有段落
    pattern = r'^\[([\d.]+)\]\s*(.+?)(?=^\[[\d.]+\]|^##|^---|\Z)'

    best_match = None
    best_match_length = 0

    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        pn = match.group(1)
        paragraph = match.group(2)
        clean_para = clean_text_for_matching(paragraph)

        # 检查是否包含搜索文本（或搜索文本包含段落）
        if search_text in clean_para or clean_para in search_text:
            # 选择匹配长度最长的
            match_len = min(len(search_text), len(clean_para))
            if match_len > best_match_length:
                best_match = pn
                best_match_length = match_len

    return best_match


def main():
    mismatches_file = '/tmp/timeline_pn_mismatches.json'
    if not Path(mismatches_file).exists():
        print(f"错误: 文件不存在 {mismatches_file}")
        return

    with open(mismatches_file) as f:
        mismatches = json.load(f)

    mapping = {}
    print(f"处理 {len(mismatches)} 个不匹配的PN...")

    for item in mismatches:
        chapter = item['chapter']
        old_pn = item['pn']
        old_content = item['old_content']

        # 在新版本中查找
        new_pn = find_pn_by_content('74032d6', chapter, old_content)

        if chapter not in mapping:
            mapping[chapter] = {}

        if new_pn and new_pn != old_pn:
            print(f"  {chapter} {old_pn} -> {new_pn}")
            mapping[chapter][old_pn] = new_pn
        elif new_pn == old_pn:
            # PN编号没变，但内容有细微差异（标注修改等）
            print(f"  {chapter} {old_pn} (内容微调，PN未变)")
            # 不需要更新
        else:
            print(f"  ⚠ {chapter} {old_pn}: 未找到匹配")
            mapping[chapter][old_pn] = None

    # 移除空的章节映射
    mapping = {k: v for k, v in mapping.items() if v and any(vv for vv in v.values())}

    # 统计
    total = sum(len(v) for v in mapping.values())
    found = sum(1 for chapter_map in mapping.values()
                for new_pn in chapter_map.values() if new_pn)

    print(f"\n映射统计:")
    print(f"  需要更新的PN: {total} 个")
    print(f"  找到新PN: {found} 个")

    # 保存
    output_file = '/tmp/pn_mapping_for_timeline.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\n映射表已保存到: {output_file}")


if __name__ == '__main__':
    main()
