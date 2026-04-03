#!/usr/bin/env python3
"""
建立完整的旧PN到新PN的映射表（覆盖所有130个章节）
通过对比6b20e096（PN规范化前）和HEAD（当前版本）
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
    text = re.sub(r'[\s"""\'\'：。，、；！？\[\]《》〈〉（）()]', '', text)
    return text


def get_chapter_file_path(commit: str, chapter_num: str) -> str:
    """获取章节文件在指定commit中的路径"""
    result = subprocess.run(
        ['git', 'ls-tree', '-r', '--name-only', '-z', commit],
        capture_output=True,
        text=True
    )

    tagged_files = [f for f in result.stdout.split('\0')
                    if f.endswith('.tagged.md') and chapter_num in f]

    # 优先选择chapter_md/目录下的文件
    for f in tagged_files:
        if f'/{chapter_num}_' in f or f.startswith(f'{chapter_num}_'):
            if 'chapter_md/' in f:
                return f

    # fallback到其他目录
    for f in tagged_files:
        if f'/{chapter_num}_' in f or f.startswith(f'{chapter_num}_'):
            return f

    return None


def extract_all_pns(commit: str, chapter_num: str) -> dict:
    """
    从章节文件中提取所有PN及其内容
    返回: {pn: cleaned_content}
    """
    file_path = get_chapter_file_path(commit, chapter_num)
    if not file_path:
        return {}

    try:
        result = subprocess.run(
            ['git', 'show', f'{commit}:{file_path}'],
            capture_output=True,
            text=True,
            check=True
        )
        content = result.stdout
    except subprocess.CalledProcessError:
        return {}

    # 提取所有段落
    pn_dict = {}
    pattern = r'^\[([\d.]+)\]\s*(.+?)(?=^\[[\d.]+\]|^##|^---|\Z)'

    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        pn = match.group(1)
        paragraph = match.group(2)
        clean_para = clean_text_for_matching(paragraph)

        # 取前150个字符（增加匹配准确度）
        pn_dict[pn] = clean_para[:150]

    return pn_dict


def find_best_match(old_content: str, new_pn_dict: dict) -> tuple:
    """
    在新版本的PN字典中查找与旧内容最匹配的PN
    返回: (new_pn, confidence_score)
    confidence_score: 匹配度分数 0-100
    """
    if not old_content:
        return None, 0

    best_pn = None
    best_score = 0

    for new_pn, new_content in new_pn_dict.items():
        # 策略1: 完全匹配
        if old_content == new_content:
            return new_pn, 100

        # 策略2: 开头匹配
        min_len = min(len(old_content), len(new_content))
        if min_len < 20:  # 内容太短，跳过
            continue

        # 计算开头相同的字符数
        match_len = 0
        for i in range(min_len):
            if old_content[i] == new_content[i]:
                match_len += 1
            else:
                break

        # 计算匹配度分数
        score = (match_len / min_len) * 100

        if score > best_score:
            best_score = score
            best_pn = new_pn

    # 只返回匹配度>=80的结果
    if best_score >= 80:
        return best_pn, best_score

    return None, best_score


def build_chapter_mapping(chapter_num: str, old_commit: str, new_commit: str) -> dict:
    """
    为单个章节建立PN映射
    返回: {old_pn: {"new_pn": ..., "confidence": ...}}
    """
    print(f"\n处理章节 {chapter_num}...")

    old_pns = extract_all_pns(old_commit, chapter_num)
    new_pns = extract_all_pns(new_commit, chapter_num)

    if not old_pns:
        print(f"  ⚠ 旧版本中没有找到章节文件")
        return {}

    if not new_pns:
        print(f"  ⚠ 新版本中没有找到章节文件")
        return {}

    print(f"  旧版本: {len(old_pns)} 个PN")
    print(f"  新版本: {len(new_pns)} 个PN")

    mapping = {}
    unchanged = 0
    changed = 0
    not_found = 0

    for old_pn, old_content in old_pns.items():
        new_pn, confidence = find_best_match(old_content, new_pns)

        if new_pn:
            if new_pn == old_pn:
                unchanged += 1
                # PN未变，不需要记录映射（或者记录为参考）
                # mapping[old_pn] = {"new_pn": new_pn, "confidence": confidence, "status": "unchanged"}
            else:
                changed += 1
                mapping[old_pn] = {"new_pn": new_pn, "confidence": confidence, "status": "changed"}
                print(f"    {old_pn} -> {new_pn} (confidence: {confidence:.1f}%)")
        else:
            not_found += 1
            mapping[old_pn] = {"new_pn": None, "confidence": 0, "status": "not_found"}
            print(f"    ⚠ {old_pn}: 未找到匹配")

    print(f"  统计: unchanged={unchanged}, changed={changed}, not_found={not_found}")

    return mapping


def main():
    old_commit = '6b20e096'  # PN规范化之前 (2026-04-02 02:27)
    new_commit = '74032d6'   # PN规范化之后 (2026-04-02 22:33)

    print(f"建立完整的PN映射表")
    print(f"  旧版本: {old_commit}")
    print(f"  新版本: {new_commit}")
    print("=" * 80)

    # 获取所有章节编号（001-130）
    all_chapters = [f"{i:03d}" for i in range(1, 131)]

    complete_mapping = {}

    for chapter_num in all_chapters:
        chapter_mapping = build_chapter_mapping(chapter_num, old_commit, new_commit)

        if chapter_mapping:
            # 只保存有变化的映射
            changed_mapping = {k: v for k, v in chapter_mapping.items()
                             if v.get("status") == "changed"}
            if changed_mapping:
                complete_mapping[chapter_num] = changed_mapping

    # 保存完整映射表（带元数据）
    output_file = 'data/pn_mapping_complete.json'
    Path('data').mkdir(exist_ok=True)

    # 添加元数据
    complete_data = {
        "_meta": {
            "description": "史记章节Purple Numbers (PN)映射表 - 完整版",
            "old_version": {
                "commit": old_commit,
                "date": "2026-04-02 02:27:56 +0800",
                "description": "PN规范化之前"
            },
            "new_version": {
                "commit": new_commit,
                "date": "2026-04-02 22:33:53 +0800",
                "description": "PN规范化之后"
            },
            "generated_at": "2026-04-02 23:41:00 +0800",
            "total_chapters": len(complete_mapping),
            "total_mappings": sum(len(v) for v in complete_mapping.values())
        },
        "mappings": complete_mapping
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_data, f, ensure_ascii=False, indent=2)

    # 生成统计报告
    total_chapters = len(complete_mapping)
    total_mappings = sum(len(v) for v in complete_mapping.values())
    high_confidence = sum(1 for chapter in complete_mapping.values()
                         for pn_map in chapter.values()
                         if pn_map.get('confidence', 0) >= 95)
    medium_confidence = sum(1 for chapter in complete_mapping.values()
                           for pn_map in chapter.values()
                           if 80 <= pn_map.get('confidence', 0) < 95)
    not_found = sum(1 for chapter in complete_mapping.values()
                   for pn_map in chapter.values()
                   if pn_map.get('new_pn') is None)

    print("\n" + "=" * 80)
    print("完整映射表统计:")
    print(f"  有变化的章节: {total_chapters} 个")
    print(f"  总映射数: {total_mappings} 个")
    print(f"  高置信度 (>=95%): {high_confidence} 个")
    print(f"  中置信度 (80-95%): {medium_confidence} 个")
    print(f"  未找到匹配: {not_found} 个")
    print(f"\n映射表已保存到: {output_file}")

    # 同时生成一个简化版本
    simple_mapping = {}
    for chapter_num, pn_maps in complete_mapping.items():
        simple_mapping[chapter_num] = {
            old_pn: data['new_pn']
            for old_pn, data in pn_maps.items()
            if data['new_pn'] is not None
        }

    simple_data = {
        "_meta": {
            "description": "史记章节Purple Numbers (PN)映射表 - 简化版",
            "old_version": {
                "commit": old_commit,
                "date": "2026-04-02 02:27:56 +0800",
                "description": "PN规范化之前"
            },
            "new_version": {
                "commit": new_commit,
                "date": "2026-04-02 22:33:53 +0800",
                "description": "PN规范化之后"
            },
            "generated_at": "2026-04-02 23:41:00 +0800",
            "total_chapters": len(simple_mapping),
            "total_mappings": sum(len(v) for v in simple_mapping.values()),
            "note": "此版本只包含PN映射，不包含置信度信息。如需详细信息请使用pn_mapping_complete.json"
        },
        "mappings": simple_mapping
    }

    simple_output = 'data/pn_mapping_simple.json'
    with open(simple_output, 'w', encoding='utf-8') as f:
        json.dump(simple_data, f, ensure_ascii=False, indent=2)

    print(f"简化版映射表已保存到: {simple_output}")


if __name__ == '__main__':
    main()
