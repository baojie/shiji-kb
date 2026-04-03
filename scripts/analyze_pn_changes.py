#!/usr/bin/env python3
"""
分析两个git版本之间章节文件的PN变化，生成映射表
"""

import re
import subprocess
import sys
import json
from pathlib import Path
from collections import defaultdict


def extract_pn_mapping_from_chapter(old_content: str, new_content: str) -> dict:
    """
    从章节的新旧内容中提取PN映射
    策略：基于段落文本内容匹配来建立新旧PN的对应关系
    """
    # 提取所有带PN的段落
    pn_pattern = r'\{#(pn-[\d.]+)\}\s*\n\n([^\n]+(?:\n(?!\{#pn-)[^\n]+)*)'

    old_paragraphs = {}  # {text_hash: pn}
    new_paragraphs = {}  # {text_hash: pn}

    # 提取旧版本的段落
    for match in re.finditer(pn_pattern, old_content):
        pn = match.group(1)
        text = match.group(2).strip()
        # 使用文本前100个字符作为key（去除标注符号）
        text_clean = re.sub(r'[〖⟦][^〗⟧]*[〗⟧]', '', text)
        text_key = text_clean[:100]
        old_paragraphs[text_key] = pn

    # 提取新版本的段落
    for match in re.finditer(pn_pattern, new_content):
        pn = match.group(1)
        text = match.group(2).strip()
        text_clean = re.sub(r'[〖⟦][^〗⟧]*[〗⟧]', '', text)
        text_key = text_clean[:100]
        new_paragraphs[text_key] = pn

    # 建立映射关系
    mapping = {}
    for text_key, old_pn in old_paragraphs.items():
        if text_key in new_paragraphs:
            new_pn = new_paragraphs[text_key]
            if old_pn != new_pn:
                mapping[old_pn] = new_pn

    return mapping


def get_chapter_content(commit: str, chapter_file: str) -> str:
    """从指定commit获取章节文件内容"""
    try:
        result = subprocess.run(
            ['git', 'show', f'{commit}:{chapter_file}'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def get_changed_chapters(old_commit: str, new_commit: str) -> list:
    """获取两个commit之间变化的章节文件"""
    result = subprocess.run(
        ['git', 'diff', '--name-only', '-z', old_commit, new_commit],
        capture_output=True,
        text=True,
        check=True
    )

    files = result.stdout.strip().split('\0')
    chapter_files = [f for f in files if f.startswith('chapter_md/') and f.endswith('.tagged.md')]
    return chapter_files


def main():
    if len(sys.argv) < 3:
        print("用法: python analyze_pn_changes.py <old_commit> <new_commit> [output_file]")
        print("示例: python analyze_pn_changes.py f1a627a 74032d6")
        sys.exit(1)

    old_commit = sys.argv[1]
    new_commit = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else '/tmp/pn_mapping.json'

    print(f"正在分析 {old_commit} -> {new_commit} 之间的PN变化...")

    # 获取变化的章节文件
    changed_chapters = get_changed_chapters(old_commit, new_commit)
    print(f"发现 {len(changed_chapters)} 个变化的章节文件")

    all_mappings = {}

    for chapter_file in changed_chapters:
        chapter_name = Path(chapter_file).stem
        print(f"  处理: {chapter_name}")

        old_content = get_chapter_content(old_commit, chapter_file)
        new_content = get_chapter_content(new_commit, chapter_file)

        if old_content and new_content:
            mapping = extract_pn_mapping_from_chapter(old_content, new_content)
            if mapping:
                all_mappings[chapter_name] = mapping
                print(f"    发现 {len(mapping)} 个PN变化")

    # 保存映射表
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_mappings, f, ensure_ascii=False, indent=2)

    print(f"\n映射表已保存到: {output_file}")
    print(f"共 {len(all_mappings)} 个章节有PN变化")

    # 显示统计信息
    total_changes = sum(len(m) for m in all_mappings.values())
    print(f"总共 {total_changes} 个PN发生变化")


if __name__ == '__main__':
    main()
