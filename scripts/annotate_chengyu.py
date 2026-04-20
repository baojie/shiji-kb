#!/usr/bin/env python3
"""
批量为001-129章添加成语〘※〙标注
基于 kg/vocabularies/data/史记成语典故.md 中的成语列表

标注策略（保守优先）：
A. 直接搜索 chengyu_name → 〘※chengyu_name〙
B. chengyu_name 不在文本中，且 original_text 满足以下条件时尝试：
   - original_text 整体 ≤ 8 字（短固定词组，整体作为标注）
   - 或 original_text 首个逗号前的部分 ≤ 8 字且看起来是固定词组
   → 〘※shiji_form|chengyu_name〙
C. 其余：跳过

安全规则：
- 不标注 Markdown 标题行（# ## ### ...）
- 不标注已在 〘※〙 内的文本
- 不标注 ⟦⟧ 内的文本
- 被实体 〖〗 完整包裹的成语：移除实体标注，改为成语标注
"""

import re
import sys
from pathlib import Path


# 不考虑作为独立成语的"结尾虚词"（被截断候选中如果以这些结尾则认为不是完整词组）
PARTICLE_ENDINGS = set('也矣乎焉哉耳而与兮')

# 不作为成语候选的句首词（上下文词）
CONTEXT_STARTERS = set('今于是此其乃吾我予汝尔子乃且故曰')


def char_overlap(s1, s2):
    """两字符串的公共字符数"""
    return len(set(s1) & set(s2))


def parse_chengyu_md(md_file):
    """解析成语典故MD，返回 [(chapter_num, chengyu_name, original_text), ...]"""
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

                # 跳过注释项和省略号
                if any(c in original for c in ['（', '(', '…', '...']):
                    continue
                if any(c in name for c in ['/', '/']):
                    continue
                if name.startswith(('（', '(')):
                    continue

                entries.append((current_chapter, name, original))

    return entries


def is_in_heading(content, pos):
    """检查 pos 位置是否在 Markdown 标题行中"""
    line_start = content.rfind('\n', 0, pos)
    line_start = 0 if line_start < 0 else line_start + 1
    line = content[line_start:pos + 1]
    return bool(re.match(r'^#{1,4}\s', line))


def is_in_annotation(content, pos):
    """检查位置是否在现有标注内，返回标注类型或 None"""
    before = content[:pos]
    if (before.count('〘') - before.count('〙')) > 0:
        return 'idiom'
    if (before.count('⟦') - before.count('⟧')) > 0:
        return 'verb'
    if (before.count('〖') - before.count('〗')) > 0:
        return 'entity'
    return None


def strip_annotations(text):
    """移除标注符号，保留内容（用于比对）"""
    text = re.sub(r'〖[^\|〗]+\|([^\|〗]+)〗', r'\1', text)
    text = re.sub(r'〖.([^〖〗]+)〗', r'\1', text)
    text = re.sub(r'⟦[^\|⟦⟧]+\|([^\|⟦⟧]+)⟧', r'\1', text)
    text = re.sub(r'⟦.([^⟦⟧]+)⟧', r'\1', text)
    text = re.sub(r'〘※([^〘〙|]+)\|?[^〘〙]*〙', r'\1', text)
    return text


def get_search_candidates(chengyu_name, original_text):
    """
    返回搜索候选列表：[(search_text, annotation_text, disambiguation), ...]
    保守策略：只返回有把握的候选
    """
    candidates = []

    # 候选1：直接搜索 chengyu_name（最优先）
    candidates.append((chengyu_name, chengyu_name, None))

    # 如果 chengyu_name 已包含在 original_text 中，不需要其他候选
    if chengyu_name in original_text:
        return candidates

    # ── 以下：chengyu_name 不在 original_text 中（存在 Shiji 变体）──
    # 安全约束：候选短语必须与 chengyu_name 共享 ≥ 2 个汉字，排除纯上下文片段

    def is_valid_candidate(phrase):
        """判断短语是否可作为成语候选"""
        if not phrase or len(phrase) < 2:
            return False
        if phrase[-1] in PARTICLE_ENDINGS:
            return False  # 以虚词结尾
        if phrase[0] in CONTEXT_STARTERS:
            return False  # 以上下文词开头（今/吾/此等）
        if char_overlap(phrase, chengyu_name) < 3:
            return False  # 与成语名共享字数不足（≥3 才考虑）
        return True

    # 候选2：original_text 整体（若短且有效）
    if len(original_text) <= 10 and is_valid_candidate(original_text):
        candidates.append((original_text, original_text, chengyu_name))

    # 候选3：逗号分句中取 overlap 最高的那个（避免多段落重复标注）
    if '，' in original_text:
        best_clause = None
        best_ov = 2  # 要求 > 2，即至少 3 个共享字
        for clause in [c.strip() for c in original_text.split('，')]:
            if (4 <= len(clause) <= 8
                    and clause != chengyu_name
                    and clause not in [c[0] for c in candidates]):
                ov = char_overlap(clause, chengyu_name)
                if (ov > best_ov
                        and (not clause or clause[-1] not in PARTICLE_ENDINGS)
                        and (not clause or clause[0] not in CONTEXT_STARTERS)):
                    best_ov = ov
                    best_clause = clause
        if best_clause:
            candidates.append((best_clause, best_clause, chengyu_name))

    return candidates


def try_annotate_in_content(content, search_text, annotation_text, disambiguation=None):
    """
    在 content 中查找 search_text 并标注。
    返回 (new_content, was_modified, info_str)
    """
    # 构建标注字符串
    if disambiguation and disambiguation != annotation_text:
        ann = f'〘※{annotation_text}|{disambiguation}〙'
    else:
        ann = f'〘※{annotation_text}〙'

    # 已有此成语标注则跳过
    if f'〘※{annotation_text}' in content:
        return content, False, 'already_annotated'

    # 直接字面搜索
    pos = 0
    while True:
        found = content.find(search_text, pos)
        if found < 0:
            break

        # 检查是否在标题行
        if is_in_heading(content, found):
            pos = found + 1
            continue

        ann_type = is_in_annotation(content, found)
        end = found + len(search_text)

        if ann_type is None:
            # 在干净文本中，直接替换
            new_content = content[:found] + ann + content[end:]
            return new_content, True, f'direct'

        elif ann_type == 'entity':
            # 在实体标注内：检查整个实体是否就是这个成语
            open_pos = content.rfind('〖', 0, found)
            close_pos = content.find('〗', end - 1)
            if open_pos >= 0 and close_pos >= 0:
                entity_inner = content[open_pos+2:close_pos]
                entity_text = entity_inner.split('|')[0] if '|' in entity_inner else entity_inner
                if entity_text.strip() == search_text.strip():
                    # 实体就是这个成语 → 替换实体为成语标注
                    new_content = content[:open_pos] + ann + content[close_pos+1:]
                    return new_content, True, f'replace_entity'
            pos = found + 1
            continue

        elif ann_type in ('idiom', 'verb'):
            pos = found + 1
            continue

    # 字面搜索失败：尝试在去标注的文本中搜索（处理成语被实体标注分割的情况）
    # 此时只处理简单情况：成语文本被单个实体标注完整包裹
    # 用正则查找：〖X search_text〗 或 〖X alt|search_text〗
    entity_wrap = re.search(
        r'〖.(' + re.escape(search_text) + r')(?:\|[^〗]*)?\]',
        content
    )
    # (备用方案：不做复杂的分片搜索，保守处理)

    return content, False, 'not_found'


def process_chapter(chapter_file, entries):
    """处理单个章节，返回 (new_content, stats)"""
    content = chapter_file.read_text(encoding='utf-8')
    stats = {'annotated': 0, 'skipped': 0, 'details': []}

    for chengyu_name, original_text in entries:
        candidates = get_search_candidates(chengyu_name, original_text)

        success = False
        for search_text, annotation_text, disambiguation in candidates:
            new_content, modified, info = try_annotate_in_content(
                content, search_text, annotation_text, disambiguation
            )
            if modified:
                content = new_content
                ann_str = f'〘※{annotation_text}' + (f'|{disambiguation}' if disambiguation else '') + '〙'
                stats['annotated'] += 1
                stats['details'].append(f'  ✓ {chengyu_name} → {ann_str}')
                success = True
                break

        if not success:
            stats['skipped'] += 1
            stats['details'].append(f'  - {chengyu_name}（跳过）')

    return content, stats


def main():
    project_root = Path(__file__).parent.parent
    chengyu_md = project_root / "kg/vocabularies/data/史记成语典故.md"
    chapter_dir = project_root / "chapter_md"

    if not chengyu_md.exists():
        print(f"错误：找不到 {chengyu_md}", file=sys.stderr)
        return 1

    print("解析成语列表...")
    all_entries = parse_chengyu_md(chengyu_md)
    print(f"共 {len(all_entries)} 条可处理成语")

    # 按章节分组（跳过130章）
    by_chapter = {}
    for chap, name, original in all_entries:
        if chap == '130':
            continue
        by_chapter.setdefault(chap, []).append((name, original))

    print(f"涉及章节：{len(by_chapter)} 章\n")

    total_annotated = 0
    total_skipped = 0
    modified_chapters = []

    for chap_num in sorted(by_chapter.keys()):
        entries = by_chapter[chap_num]
        files = list(chapter_dir.glob(f"{chap_num}_*.tagged.md"))
        if not files:
            print(f"⚠ 找不到：{chap_num}")
            continue

        chapter_file = files[0]
        new_content, stats = process_chapter(chapter_file, entries)

        total_annotated += stats['annotated']
        total_skipped += stats['skipped']

        print(f"{chapter_file.name}（{len(entries)} 条）")
        for d in stats['details']:
            print(d)

        if stats['annotated'] > 0:
            chapter_file.write_text(new_content, encoding='utf-8')
            modified_chapters.append(chapter_file.name)
            print(f"  → 写入（新增 {stats['annotated']} 条）\n")
        else:
            print(f"  → 未改动\n")

    print('=' * 60)
    print(f"完成！标注 {total_annotated} 条，跳过 {total_skipped} 条，修改 {len(modified_chapters)} 章")
    return 0


if __name__ == '__main__':
    sys.exit(main())
