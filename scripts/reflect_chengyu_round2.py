#!/usr/bin/env python3
"""
成语第二轮反思：诊断脚本

1) 检查已打〘※〙的标注中，长度过短（≤3字）等明显非成语的标注
2) 检查成语词表中的条目是否出现在文本中但被实体 〖〗 标注覆盖（应改为成语标注）

只做诊断输出，不修改文件。
"""

import re
import sys
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
                if any(c in original for c in ['（', '(', '…', '...']):
                    continue
                if any(c in name for c in ['/', '/']):
                    continue
                if name.startswith(('（', '(')):
                    continue
                entries.append((current_chapter, name, original))
    return entries


def strip_all_tags(text):
    """去除所有标注符号，返回纯文本"""
    # 成语标注 〘※X〙 或 〘※X|Y〙 → X
    text = re.sub(r'〘※([^〘〙|]+)(?:\|[^〘〙]*)?〙', r'\1', text)
    # 实体标注 〖?X〗 或 〖?X|Y〗 → X (带符号)
    text = re.sub(r'〖.([^〖〗|]+)(?:\|[^〖〗]*)?〗', r'\1', text)
    # 动词标注 ⟦?X⟧ → X
    text = re.sub(r'⟦.([^⟦⟧|]+)(?:\|[^⟦⟧]*)?⟧', r'\1', text)
    return text


def find_in_chapter(chapter_path, name, original):
    """在章节中查找成语，返回诊断信息列表"""
    content = chapter_path.read_text(encoding='utf-8')
    results = []

    # 情形1：已有 〘※name〙 标注 → 跳过
    if f'〘※{name}' in content:
        return results

    # 情形2：文本中直接出现 name（未被标注）
    # 检查 name 是否在任何位置出现，无论是否在标注内
    for m in re.finditer(re.escape(name), content):
        pos = m.start()
        end = m.end()
        before = content[:pos]

        in_idiom = (before.count('〘') - before.count('〙')) > 0
        in_verb = (before.count('⟦') - before.count('⟧')) > 0
        in_entity = (before.count('〖') - before.count('〗')) > 0

        if in_idiom:
            continue

        # 取上下文
        line_no = before.count('\n') + 1
        ctx_start = max(0, pos - 15)
        ctx_end = min(len(content), end + 15)
        ctx = content[ctx_start:ctx_end].replace('\n', ' ')

        if in_entity:
            # 查找最近的 〖 和 〗
            open_pos = content.rfind('〖', 0, pos)
            close_pos = content.find('〗', end - 1)
            if open_pos >= 0 and close_pos >= 0:
                entity_inner = content[open_pos:close_pos + 1]
                results.append({
                    'type': 'in_entity',
                    'chapter': chapter_path.name,
                    'line': line_no,
                    'name': name,
                    'entity': entity_inner,
                    'ctx': ctx,
                })
        elif in_verb:
            results.append({
                'type': 'in_verb',
                'chapter': chapter_path.name,
                'line': line_no,
                'name': name,
                'ctx': ctx,
            })
        else:
            results.append({
                'type': 'untagged',
                'chapter': chapter_path.name,
                'line': line_no,
                'name': name,
                'ctx': ctx,
            })

    return results


def main():
    entries = parse_chengyu_md(CHENGYU_MD)
    print(f"# 成语词表：{len(entries)} 条\n")

    # 按章节分组
    by_chapter = {}
    for chap, name, original in entries:
        by_chapter.setdefault(chap, []).append((name, original))

    all_in_entity = []
    all_in_verb = []
    all_untagged = []

    for chap_num, chap_entries in sorted(by_chapter.items()):
        if chap_num == '130':
            continue
        files = list(CHAPTER_DIR.glob(f"{chap_num}_*.tagged.md"))
        if not files:
            continue
        chapter_file = files[0]

        for name, original in chap_entries:
            results = find_in_chapter(chapter_file, name, original)
            for r in results:
                if r['type'] == 'in_entity':
                    all_in_entity.append(r)
                elif r['type'] == 'in_verb':
                    all_in_verb.append(r)
                else:
                    all_untagged.append(r)

    print(f"## 成语被实体标注覆盖: {len(all_in_entity)} 处\n")
    for r in all_in_entity:
        print(f"  [{r['chapter']}:{r['line']}] '{r['name']}' in {r['entity']}")
        print(f"    ctx: ...{r['ctx']}...")

    print(f"\n## 成语被动词标注覆盖: {len(all_in_verb)} 处\n")
    for r in all_in_verb:
        print(f"  [{r['chapter']}:{r['line']}] '{r['name']}'")
        print(f"    ctx: ...{r['ctx']}...")

    print(f"\n## 成语未标注（普通文本中）: {len(all_untagged)} 处\n")
    for r in all_untagged[:30]:
        print(f"  [{r['chapter']}:{r['line']}] '{r['name']}'")
        print(f"    ctx: ...{r['ctx']}...")
    if len(all_untagged) > 30:
        print(f"  ... 共 {len(all_untagged)} 处，仅显示前 30")


if __name__ == '__main__':
    main()
