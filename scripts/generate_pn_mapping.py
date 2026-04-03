#!/usr/bin/env python3
"""
为timeline.html中内容不匹配的PN生成映射表
通过在新版本中查找旧版本内容对应的PN
"""

import json
import re
import subprocess
from pathlib import Path


def get_all_pns_from_chapter(commit: str, chapter_file: str) -> dict:
    """
    从章节文件中提取所有PN及其内容
    返回: {pn: content_first_50_chars}
    """
    # 查找文件
    result = subprocess.run(
        ['git', 'ls-tree', '-r', '--name-only', '-z', commit],
        capture_output=True,
        text=True
    )

    chapter_num = re.match(r'(\d+)_', chapter_file).group(1)
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
        return {}

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
        return {}

    # 提取所有PN
    pn_dict = {}
    pattern = r'^\[([\d.]+)\]\s*(.+?)(?=^\[[\d.]+\]|^##|^---|\Z)'

    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        pn = match.group(1)
        paragraph = match.group(2).strip()
        # 去除标注符号
        clean_text = re.sub(r'[〖⟦][^〗⟧]*[〗⟧]', '', paragraph)
        # 去除换行和多余空格
        clean_text = re.sub(r'\s+', '', clean_text)
        # 统一引号和标点（去除所有标点符号，避免标点变化导致不匹配）
        clean_text = re.sub(r'[""\'\'：。，、；！？]', '', clean_text)
        pn_dict[pn] = clean_text[:100]  # 取前100字

    return pn_dict


def find_matching_pn(old_content: str, new_pn_dict: dict) -> str:
    """
    在新版本的PN字典中查找与旧内容匹配的PN
    匹配策略：
    1. 精确匹配（前50字完全相同）
    2. 包含匹配（新内容以旧内容开头）
    3. 模糊匹配（新内容包含旧内容的前30字）
    """
    # 策略1：精确匹配
    for pn, content in new_pn_dict.items():
        if content == old_content:
            return pn

    # 策略2：开头匹配（旧内容是新内容的前缀）
    for pn, content in new_pn_dict.items():
        if content.startswith(old_content[:40]):  # 至少前40字匹配
            return pn

    # 策略3：新内容以旧内容开头
    for pn, content in new_pn_dict.items():
        if old_content.startswith(content[:40]) and len(content) >= 40:
            return pn

    return None


def generate_mapping(mismatches_file: str, new_commit: str) -> dict:
    """生成PN映射表"""
    with open(mismatches_file, 'r', encoding='utf-8') as f:
        mismatches = json.load(f)

    mapping = {}  # {chapter: {old_pn: new_pn}}

    print(f"处理 {len(mismatches)} 个不匹配的PN引用...")

    for item in mismatches:
        chapter = item['chapter']
        old_pn = item['pn']
        old_content = item['old_content']

        if chapter not in mapping:
            # 获取该章节在新版本中的所有PN
            print(f"  加载章节: {chapter}")
            new_pn_dict = get_all_pns_from_chapter(new_commit, chapter)
            mapping[chapter] = {}
        else:
            new_pn_dict = {v: k for k, v in mapping[chapter].items()}
            # 需要重新加载
            if not new_pn_dict:
                new_pn_dict = get_all_pns_from_chapter(new_commit, chapter)

        # 查找匹配的PN
        new_pn = find_matching_pn(old_content, new_pn_dict)

        if new_pn:
            print(f"    {old_pn} -> {new_pn}")
            mapping[chapter][old_pn] = new_pn
        else:
            print(f"    ⚠ {old_pn}: 未找到匹配的新PN")
            mapping[chapter][old_pn] = None

    return mapping


def main():
    mismatches_file = '/tmp/timeline_pn_mismatches.json'
    if not Path(mismatches_file).exists():
        print(f"错误: 请先运行 verify_timeline_pn_content.py 生成 {mismatches_file}")
        return

    new_commit = '74032d6'  # PN规范化之后 (2026-04-02 22:33)
    mapping = generate_mapping(mismatches_file, new_commit)

    # 统计
    total = sum(len(v) for v in mapping.values())
    found = sum(1 for chapter_map in mapping.values()
                for new_pn in chapter_map.values() if new_pn)
    not_found = total - found

    print(f"\n映射生成完成:")
    print(f"  总共: {total} 个")
    print(f"  找到匹配: {found} 个")
    print(f"  未找到: {not_found} 个")

    # 保存映射表
    output_file = '/tmp/pn_mapping_for_timeline.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\n映射表已保存到: {output_file}")


if __name__ == '__main__':
    main()
