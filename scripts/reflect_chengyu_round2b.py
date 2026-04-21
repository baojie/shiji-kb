#!/usr/bin/env python3
"""
成语第二轮反思 B：搜索成语在原文中的变体形式

针对每条成语，同时搜索其 chengyu_name 和 original_text 段落中可能的变体，
找出被实体 〖〗 标注覆盖的片段。
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHENGYU_MD = ROOT / "kg/vocabularies/data/史记成语典故.md"
CHAPTER_DIR = ROOT / "chapter_md"


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
                entries.append((current_chapter, name, original))
    return entries


def strip_tags_preserve_len(content):
    """把所有 〖X〗 / ⟦X⟧ / 〘※X〙 替换为空格填充，保持其他位置的偏移"""
    def pad(m):
        return ' ' * len(m.group(0))

    # 只去除标注符号本身（保留内部文字），但需要返回"干净文本"与"位置映射"
    # 简化：返回一个映射，原位置 -> 是否在标注内
    pass


def find_entities_containing(content, text):
    """
    找出所有 〖...〗 实体标注，其内部文本（展开消歧后）中包含 text 子串的实体。
    返回 [(entity_str, start, end, inner_text), ...]
    """
    results = []
    for m in re.finditer(r'〖(.)([^〖〗]+)〗', content):
        full = m.group(0)
        sym = m.group(1)
        inner = m.group(2)
        # 处理消歧：surface|canonical
        if '|' in inner:
            surface = inner.split('|')[0]
        else:
            surface = inner
        if text in surface:
            results.append({
                'entity': full,
                'start': m.start(),
                'end': m.end(),
                'surface': surface,
                'sym': sym,
            })
    return results


def main():
    entries = parse_chengyu_md(CHENGYU_MD)
    print(f"# 成语词表：{len(entries)} 条\n")

    by_chapter = {}
    for chap, name, original in entries:
        by_chapter.setdefault(chap, []).append((name, original))

    hits = []
    for chap_num, chap_entries in sorted(by_chapter.items()):
        if chap_num == '130':
            continue
        files = list(CHAPTER_DIR.glob(f"{chap_num}_*.tagged.md"))
        if not files:
            continue
        chapter_file = files[0]
        content = chapter_file.read_text(encoding='utf-8')

        for name, original in chap_entries:
            # 如果该章已有 name 的 〘※〙 标注，该成语已处理 → 跳过整个条目
            if f'〘※{name}' in content:
                continue

            # 检查 name 整体是否被某实体包裹
            for ent in find_entities_containing(content, name):
                if ent['surface'].strip() == name.strip():
                    hits.append({
                        'chapter': chapter_file.name,
                        'name': name,
                        'entity': ent['entity'],
                        'case': 'entity_equals_name',
                    })
                else:
                    # 实体内包含 name 作为子串
                    hits.append({
                        'chapter': chapter_file.name,
                        'name': name,
                        'entity': ent['entity'],
                        'case': 'entity_contains_name',
                    })

    print(f"## 命中: {len(hits)} 处\n")
    for h in hits:
        print(f"  [{h['chapter']}] {h['case']}: 成语='{h['name']}' 实体={h['entity']}")


if __name__ == '__main__':
    main()
