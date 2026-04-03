#!/usr/bin/env python3
"""
验证timeline.html中的PN引用是否指向正确的内容
通过对比旧版本和新版本中PN对应的段落内容来判断
"""

import re
import subprocess
import sys
import json
from pathlib import Path
from collections import defaultdict
from html.parser import HTMLParser


class TimelinePNExtractor(HTMLParser):
    """从timeline.html中提取所有PN引用"""
    def __init__(self):
        super().__init__()
        self.pn_refs = []  # [(chapter_file, pn, year_context)]
        self.current_year = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # 提取年份信息
        if tag == 'span' and attrs_dict.get('class') == 'canonical-name time':
            self.in_year = True

        # 提取PN引用链接
        if tag == 'a' and 'href' in attrs_dict:
            href = attrs_dict['href']
            # 匹配 ../chapters/XXX.html#pn-YYY
            match = re.match(r'\.\.\/chapters\/([^\/]+)\.html#pn-([\d.]+)', href)
            if match:
                chapter_file = match.group(1)
                pn = match.group(2)
                self.pn_refs.append((chapter_file, pn, self.current_year))

    def handle_data(self, data):
        if hasattr(self, 'in_year') and self.in_year:
            self.current_year = data.strip()
            self.in_year = False


def extract_pn_refs_from_timeline(timeline_file: str) -> list:
    """从timeline.html中提取所有PN引用"""
    with open(timeline_file, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = TimelinePNExtractor()
    parser.feed(content)
    return parser.pn_refs


def get_chapter_number_from_filename(filename: str) -> str:
    """从文件名中提取章节编号，如 001_五帝本纪 -> 001"""
    match = re.match(r'(\d+)_', filename)
    return match.group(1) if match else None


def get_pn_content_from_chapter(commit: str, chapter_file: str, pn: str) -> str:
    """
    从指定commit的章节文件中提取PN对应的段落内容（前50个字）
    chapter_file格式：001_五帝本纪
    """
    chapter_num = get_chapter_number_from_filename(chapter_file)
    if not chapter_num:
        return None

    # 查找对应的tagged.md文件
    result = subprocess.run(
        ['git', 'ls-tree', '-r', '--name-only', '-z', commit],
        capture_output=True,
        text=True
    )

    tagged_files = [f for f in result.stdout.split('\0')
                    if f.endswith('.tagged.md') and chapter_num in f]

    # 找到匹配的章节文件（优先查找chapter_md/，fallback到backups/）
    target_file = None
    for f in tagged_files:
        if f'/{chapter_num}_' in f or f.startswith(f'{chapter_num}_'):
            if 'chapter_md/' in f:
                target_file = f
                break
            elif not target_file:  # fallback
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

    # 查找PN对应的段落
    # 格式：[1.2] 段落内容...
    pattern = rf'^\[{re.escape(pn)}\]\s*(.+?)(?=^\[[\d.]+\]|^##|^---|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if match:
        paragraph = match.group(1).strip()
        # 去除标注符号
        clean_text = re.sub(r'[〖⟦][^〗⟧]*[〗⟧]', '', paragraph)
        # 去除换行和多余空格
        clean_text = re.sub(r'\s+', '', clean_text)
        # 统一引号和标点（去除所有标点符号，避免标点变化导致不匹配）
        clean_text = re.sub(r'[""\'\'：。，、；！？]', '', clean_text)
        return clean_text[:100]  # 取前100字

    return None


def verify_timeline_pn_refs(timeline_file: str, old_commit: str, new_commit: str):
    """验证timeline中的PN引用"""
    print(f"从 {timeline_file} 提取PN引用...")
    pn_refs = extract_pn_refs_from_timeline(timeline_file)
    print(f"找到 {len(pn_refs)} 个PN引用\n")

    # 去重
    unique_refs = {}
    for chapter_file, pn, year in pn_refs:
        key = (chapter_file, pn)
        if key not in unique_refs:
            unique_refs[key] = year

    print(f"去重后有 {len(unique_refs)} 个唯一的PN引用\n")
    print("=" * 80)

    mismatches = []
    verified = 0
    old_missing = 0
    new_missing = 0

    for (chapter_file, pn), year in sorted(unique_refs.items()):
        old_content = get_pn_content_from_chapter(old_commit, chapter_file, pn)
        new_content = get_pn_content_from_chapter(new_commit, chapter_file, pn)

        if old_content is None:
            old_missing += 1
            print(f"⚠ {chapter_file} pn-{pn}: 旧版本中不存在")
            continue

        if new_content is None:
            new_missing += 1
            print(f"⚠ {chapter_file} pn-{pn}: 新版本中不存在")
            continue

        if old_content == new_content:
            verified += 1
        else:
            mismatches.append({
                'chapter': chapter_file,
                'pn': pn,
                'year': year,
                'old_content': old_content,
                'new_content': new_content
            })
            print(f"\n❌ 内容不匹配: {chapter_file} pn-{pn}")
            print(f"   年份上下文: {year}")
            print(f"   旧版本({old_commit}): {old_content}")
            print(f"   新版本({new_commit}): {new_content}")

    print("\n" + "=" * 80)
    print(f"\n验证结果汇总:")
    print(f"  ✓ 内容匹配: {verified} 个")
    print(f"  ✗ 内容不匹配: {len(mismatches)} 个")
    print(f"  ⚠ 旧版本缺失: {old_missing} 个")
    print(f"  ⚠ 新版本缺失: {new_missing} 个")

    if mismatches:
        # 保存不匹配的PN列表
        output_file = '/tmp/timeline_pn_mismatches.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mismatches, f, ensure_ascii=False, indent=2)
        print(f"\n不匹配的PN详情已保存到: {output_file}")

    return mismatches


def main():
    if len(sys.argv) < 4:
        print("用法: python verify_timeline_pn_content.py <timeline_file> <old_commit> <new_commit>")
        print("示例: python verify_timeline_pn_content.py docs/entities/timeline.html 6b20e096 74032d6")
        sys.exit(1)

    timeline_file = sys.argv[1]
    old_commit = sys.argv[2]
    new_commit = sys.argv[3]

    if not Path(timeline_file).exists():
        print(f"错误: 文件不存在: {timeline_file}")
        sys.exit(1)

    mismatches = verify_timeline_pn_refs(timeline_file, old_commit, new_commit)

    if mismatches:
        print(f"\n⚠️  发现 {len(mismatches)} 个PN引用需要更新！")
        sys.exit(1)
    else:
        print("\n✓ 所有PN引用都正确！")
        sys.exit(0)


if __name__ == '__main__':
    main()
