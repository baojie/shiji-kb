#!/usr/bin/env python3
"""
成语第二轮反思：实际修复脚本

1. 去除明显非成语的短标注（2-3字）
2. 将被实体/动词标注覆盖的成语片段改为成语标注（整体替换）

安全机制：
- 仅当扩展后的区域括号平衡、且去除标注后的纯文本精确匹配成语名时才改动
- 扫描右向左，避免位置错乱
- 修复后验证文本完整性（去除所有标注后应与 raw.txt 一致）
"""

import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHENGYU_MD = ROOT / "kg/vocabularies/data/史记成语典故.md"
CHAPTER_DIR = ROOT / "chapter_md"

# 第一轮误标及词表中需排除的明显非成语短条目（≤3字，非真正成语）
INVALID_SHORT_TAGS = [
    '不食言',  # 3字，非成语
    '画一',    # 2字，非成语（「若画一」是萧规曹随的一句）
    '智囊',    # 2字，名词，非成语
    '凿空',    # 2字，名词，非成语
    '真将军',  # 3字，称赞语，非成语
    '人彘',    # 2字，特指吕后酷刑，非成语
    '反间计',  # 3字，36计名，非成语
    '批逆鳞',  # 3字，非成语
]


def parse_chengyu_md(md_file):
    content = md_file.read_text(encoding='utf-8')
    entries = []
    current_chapter = None
    for line in content.split('\n'):
        line = line.strip()
        m = re.match(r'^###\s+(\d+)\s+', line)
        if m:
            current_chapter = m.group(1).zfill(3)
            continue
        if current_chapter and line.startswith('|') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 2 and parts[0] and parts[0] != '成语':
                name = parts[0]
                original = parts[1]
                if '…' in original or '...' in original:
                    continue
                if any(c in name for c in ['/', '/']):
                    continue
                if name.startswith(('（', '(')):
                    continue
                # 跳过第一轮已识别的无效短标注
                if name in INVALID_SHORT_TAGS:
                    continue
                entries.append((current_chapter, name, original))
    return entries


def build_strip_map(content):
    """
    返回 (stripped_text, pos_map, owner_map)
    owner_map[i] = None | 'entity' | 'verb' | 'idiom'，表示 stripped_text[i] 在原文中属于哪种标注。
    """
    stripped_chars = []
    pos_map = []
    owner_map = []
    i = 0
    N = len(content)
    while i < N:
        c = content[i]
        if c == '〖':
            end = content.find('〗', i)
            if end < 0:
                i += 1
                continue
            inner = content[i+1:end]
            if inner:
                inner_body = inner[1:]
                if '|' in inner_body:
                    inner_body = inner_body.split('|')[0]
                for j, ch in enumerate(inner_body):
                    stripped_chars.append(ch)
                    pos_map.append(i + 2 + j)
                    owner_map.append('entity')
            i = end + 1
        elif c == '⟦':
            end = content.find('⟧', i)
            if end < 0:
                i += 1
                continue
            inner = content[i+1:end]
            if inner:
                inner_body = inner[1:]
                if '|' in inner_body:
                    inner_body = inner_body.split('|')[0]
                for j, ch in enumerate(inner_body):
                    stripped_chars.append(ch)
                    pos_map.append(i + 2 + j)
                    owner_map.append('verb')
            i = end + 1
        elif c == '〘':
            end = content.find('〙', i)
            if end < 0:
                i += 1
                continue
            inner = content[i+1:end]
            if inner.startswith('※'):
                inner_body = inner[1:]
                if '|' in inner_body:
                    inner_body = inner_body.split('|')[0]
                for j, ch in enumerate(inner_body):
                    stripped_chars.append(ch)
                    pos_map.append(i + 2 + j)
                    owner_map.append('idiom')
            i = end + 1
        else:
            stripped_chars.append(c)
            pos_map.append(i)
            owner_map.append(None)
            i += 1
    return ''.join(stripped_chars), pos_map, owner_map


def strip_all_markup(text):
    """去除所有标注符号，返回纯文本（用于验证）"""
    t = text
    t = re.sub(r'〘※([^〘〙|]+)(?:\|[^〘〙]*)?〙', r'\1', t)
    t = re.sub(r'〖.([^〖〗|]+)(?:\|[^〖〗]*)?〗', r'\1', t)
    t = re.sub(r'⟦.([^⟦⟧|]+)(?:\|[^⟦⟧]*)?⟧', r'\1', t)
    return t


def expand_to_bracket_boundaries(content, start, end):
    """
    扩展 [start, end) 以包含任何跨越边界的括号对。
    返回 (new_start, new_end) 或 None（无法平衡）。
    """
    new_start = start
    new_end = end

    # 防止无限循环
    for _ in range(50):
        region = content[new_start:new_end]
        # 统计各种括号
        counts = {
            '〖': region.count('〖'), '〗': region.count('〗'),
            '⟦': region.count('⟦'), '⟧': region.count('⟧'),
            '〘': region.count('〘'), '〙': region.count('〙'),
        }

        open_e = counts['〖'] - counts['〗']
        open_v = counts['⟦'] - counts['⟧']
        open_i = counts['〘'] - counts['〙']

        # 如果开括号多于关括号：需要向右扩展以包含关括号
        if open_e > 0 or open_v > 0 or open_i > 0:
            # 找最近的关括号
            next_close = None
            for sym in ['〗', '⟧', '〙']:
                p = content.find(sym, new_end)
                if p >= 0 and (next_close is None or p < next_close):
                    next_close = p
            if next_close is None:
                return None
            new_end = next_close + 1
        # 如果关括号多于开括号：需要向左扩展以包含开括号
        elif open_e < 0 or open_v < 0 or open_i < 0:
            # 找最近的开括号
            before = content[:new_start]
            prev_open = None
            for sym in ['〖', '⟦', '〘']:
                p = before.rfind(sym)
                if p >= 0 and (prev_open is None or p > prev_open):
                    prev_open = p
            if prev_open is None:
                return None
            new_start = prev_open
        else:
            return (new_start, new_end)

    return None


def process_chapter(chapter_file, entries):
    """处理单个章节，返回 (new_content, changes_list)"""
    content = chapter_file.read_text(encoding='utf-8')
    changes = []

    # 先应用：去除 INVALID_SHORT_TAGS
    for bad in INVALID_SHORT_TAGS:
        pattern = f'〘※{bad}〙'
        if pattern in content:
            content = content.replace(pattern, bad)
            changes.append(f'去除无效标注: {pattern} → {bad}')

    # 为每个成语找匹配并转换
    # 为防止位置错乱，每次转换后重新构建 stripped/pos_map
    for name, original in entries:
        # 已有该成语标注则跳过
        if f'〘※{name}' in content:
            continue

        # 找到所有候选匹配位置（一次性枚举），然后从右向左尝试替换
        changed_any = True
        while changed_any:
            changed_any = False
            stripped, pos_map, owner_map = build_strip_map(content)

            # 找所有匹配
            candidates = []
            start = 0
            while True:
                idx = stripped.find(name, start)
                if idx < 0:
                    break
                # 跳过：匹配区间内已有 idiom 归属（即已被成语标注）
                owners = owner_map[idx:idx + len(name)]
                if 'idiom' in owners:
                    start = idx + 1
                    continue
                candidates.append(idx)
                start = idx + 1

            if not candidates:
                break

            # 从右向左处理
            for idx in reversed(candidates):
                orig_start = pos_map[idx]
                orig_end = pos_map[idx + len(name) - 1] + 1

                # 跳过 Markdown 标题行
                line_start = content.rfind('\n', 0, orig_start) + 1
                line_end_pos = content.find('\n', orig_end)
                if line_end_pos < 0:
                    line_end_pos = len(content)
                line = content[line_start:line_end_pos]
                if line.lstrip().startswith('#'):
                    continue

                # 扩展边界以包含跨越的括号
                result = expand_to_bracket_boundaries(content, orig_start, orig_end)
                if result is None:
                    continue
                ex_start, ex_end = result

                region = content[ex_start:ex_end]
                pure = strip_all_markup(region)
                if pure != name:
                    continue

                # 区域内不能已有 〘〙
                if '〘' in region or '〙' in region:
                    continue

                replacement = f'〘※{name}〙'
                content = content[:ex_start] + replacement + content[ex_end:]
                changes.append(f'{name}: {region} → {replacement}')
                changed_any = True
                # 处理一个就重新枚举（因位置变化）
                break

    return content, changes


def verify_integrity(chapter_file, original_content, new_content):
    """验证去除所有标注后文本是否一致"""
    old_pure = strip_all_markup(original_content)
    new_pure = strip_all_markup(new_content)
    if old_pure != new_pure:
        # 找出第一个不一致位置
        for i, (a, b) in enumerate(zip(old_pure, new_pure)):
            if a != b:
                return False, f'位置 {i}: "{old_pure[max(0,i-10):i+10]}" vs "{new_pure[max(0,i-10):i+10]}"'
        return False, f'长度不一致: {len(old_pure)} vs {len(new_pure)}'
    return True, None


def main():
    entries = parse_chengyu_md(CHENGYU_MD)
    print(f"成语词表: {len(entries)} 条（已排除 {len(INVALID_SHORT_TAGS)} 条无效短标注）")

    by_chapter = {}
    for chap, name, original in entries:
        by_chapter.setdefault(chap, []).append((name, original))

    total_changes = 0
    total_files_modified = 0

    for chap_num in sorted(by_chapter.keys()):
        if chap_num == '130':
            continue
        chap_entries = by_chapter[chap_num]
        files = list(CHAPTER_DIR.glob(f"{chap_num}_*.tagged.md"))
        if not files:
            continue
        chapter_file = files[0]
        original_content = chapter_file.read_text(encoding='utf-8')

        new_content, changes = process_chapter(chapter_file, chap_entries)

        if not changes:
            continue

        # 完整性校验
        ok, err = verify_integrity(chapter_file, original_content, new_content)
        if not ok:
            print(f"\n✗ {chapter_file.name}: 完整性校验失败 - {err}")
            continue

        # 写入
        chapter_file.write_text(new_content, encoding='utf-8')
        total_files_modified += 1
        total_changes += len(changes)
        print(f"\n{chapter_file.name}: {len(changes)} 条变更")
        for c in changes:
            print(f"  ✓ {c}")

    # 处理只删除无效短标注的章节（不在 by_chapter 中的章节）
    all_chapters = list(CHAPTER_DIR.glob('*.tagged.md'))
    for chapter_file in all_chapters:
        chap_num = chapter_file.name[:3]
        if chap_num in by_chapter:
            continue  # 已处理
        content = chapter_file.read_text(encoding='utf-8')
        original = content
        changes = []
        for bad in INVALID_SHORT_TAGS:
            pattern = f'〘※{bad}〙'
            if pattern in content:
                content = content.replace(pattern, bad)
                changes.append(f'去除无效标注: {pattern} → {bad}')
        if changes:
            ok, err = verify_integrity(chapter_file, original, content)
            if not ok:
                print(f"\n✗ {chapter_file.name}: 完整性校验失败 - {err}")
                continue
            chapter_file.write_text(content, encoding='utf-8')
            total_files_modified += 1
            total_changes += len(changes)
            print(f"\n{chapter_file.name}: {len(changes)} 条变更")
            for c in changes:
                print(f"  ✓ {c}")

    print(f"\n{'='*60}")
    print(f"完成：修改 {total_files_modified} 章，共 {total_changes} 条变更")
    return 0


if __name__ == '__main__':
    sys.exit(main())
