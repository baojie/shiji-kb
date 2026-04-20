#!/usr/bin/env python3
"""
从 chapter_md/*.tagged.md 中直接提取 〘※〙 成语标注，生成 data/chengyu.json

优先级：
1. 从标注文件直接读取（准确）
2. 补充 kg/vocabularies/data/史记成语典故.md 中未被标注但有释义的条目（供参考，标记 annotated=False）

输出字段（与 extract_chengyu.py 兼容）：
  chapter_num, chapter_title, chengyu, shiji_form, original, meaning, context, paragraph, annotated
"""

import re
import json
from pathlib import Path


CHENGYU_PATTERN = re.compile(r'〘※([^〘〙|]+)(?:\|([^〘〙]+))?〙')
PARA_NUM_PATTERN = re.compile(r'^\[(\d+(?:\.\d+)?)\]')


def get_chapter_title(chapter_num: str) -> str:
    chapter_dir = Path(__file__).parent.parent / 'chapter_md'
    files = list(chapter_dir.glob(f'{chapter_num}_*.tagged.md'))
    if files:
        stem = files[0].stem.replace('.tagged', '')
        return stem[4:]  # strip "NNN_"
    return ''


def extract_context(content: str, pos: int, context_chars: int = 300) -> tuple[str, str]:
    """Return (paragraph_num, context_text) around pos."""
    # Find paragraph number by scanning backward
    para_num = ''
    line_start = content.rfind('\n', 0, pos)
    search_back = max(0, pos - 2000)
    chunk = content[search_back:pos]
    for line in reversed(chunk.split('\n')):
        m = PARA_NUM_PATTERN.match(line.strip())
        if m:
            para_num = m.group(1)
            break

    # Extract context: find the section around pos
    start = max(0, pos - context_chars)
    end = min(len(content), pos + context_chars)
    # Extend to line boundaries
    start = content.rfind('\n', 0, start)
    start = 0 if start < 0 else start + 1
    end_nl = content.find('\n', end)
    end = end_nl if end_nl >= 0 else end

    # Get 3-5 lines for context
    lines = content[start:end].split('\n')
    # Keep lines near pos
    context = '\n'.join(lines[:8])
    return para_num, context


def parse_chengyu_md(md_file: Path) -> dict:
    """Parse 史记成语典故.md → {(chapter_num, chengyu_name): (original, meaning)}"""
    content = md_file.read_text(encoding='utf-8')
    result = {}
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
                original = parts[1] if len(parts) > 1 else ''
                meaning = parts[2] if len(parts) > 2 else ''
                if any(c in name for c in ['/', '/']):
                    continue
                if name.startswith(('（', '(')):
                    continue
                result[(current_chapter, name)] = (original, meaning)

    return result


def extract_from_tagged_files(chapter_dir: Path, vocab_lookup: dict) -> list[dict]:
    """Extract all 〘※〙 annotations from tagged chapter files."""
    results = []
    seen = set()  # (chapter_num, shiji_form) to avoid duplicates

    chapter_files = sorted(chapter_dir.glob('*.tagged.md'))
    for chapter_file in chapter_files:
        stem = chapter_file.stem.replace('.tagged', '')
        m = re.match(r'^(\d{3})_(.+)$', stem)
        if not m:
            continue
        chapter_num = m.group(1)
        chapter_title = m.group(2)

        content = chapter_file.read_text(encoding='utf-8')

        for match in CHENGYU_PATTERN.finditer(content):
            shiji_form = match.group(1).strip()
            modern_form = match.group(2).strip() if match.group(2) else None
            chengyu_name = modern_form if modern_form else shiji_form

            key = (chapter_num, shiji_form)
            if key in seen:
                continue
            seen.add(key)

            pos = match.start()
            para_num, context = extract_context(content, pos)

            # Look up original text and meaning from vocabulary
            original = ''
            meaning = ''
            for lookup_key in [(chapter_num, chengyu_name), (chapter_num, shiji_form)]:
                if lookup_key in vocab_lookup:
                    original, meaning = vocab_lookup[lookup_key]
                    break

            results.append({
                'chapter_num': chapter_num,
                'chapter_title': chapter_title,
                'chengyu': chengyu_name,
                'shiji_form': shiji_form if shiji_form != chengyu_name else '',
                'original': original,
                'meaning': meaning,
                'context': context,
                'paragraph': para_num,
                'annotated': True,
            })

    return results


def main():
    project_root = Path(__file__).parent.parent
    chapter_dir = project_root / 'chapter_md'
    chengyu_md = project_root / 'kg/vocabularies/data/史记成语典故.md'
    output_json = project_root / 'data/chengyu.json'

    print('解析成语典故词表...')
    vocab_lookup = parse_chengyu_md(chengyu_md)
    print(f'词表条目: {len(vocab_lookup)}')

    print('从标注文件提取成语...')
    results = extract_from_tagged_files(chapter_dir, vocab_lookup)
    print(f'提取到 {len(results)} 条成语标注')

    # Sort by chapter_num then chengyu
    results.sort(key=lambda x: (x['chapter_num'], x['chengyu']))

    output_json.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f'已写入 {output_json}')

    # Generate Markdown
    output_md = project_root / 'data/chengyu.md'
    from collections import Counter
    by_chap = Counter(r['chapter_num'] for r in results)

    with open(output_md, 'w', encoding='utf-8') as f:
        f.write('# 史记成语典故\n\n')
        f.write(f'史记中共有 {len(results)} 条成语典故（已标注）\n\n')
        f.write(f'涵盖章节: {len(by_chap)}/130\n\n---\n\n')
        current_chapter = None
        for item in results:
            chapter_key = f"{item['chapter_num']} {item['chapter_title']}"
            if chapter_key != current_chapter:
                current_chapter = chapter_key
                f.write(f"## {chapter_key}\n\n")
            name = item['chengyu']
            if item.get('shiji_form'):
                name = f"{item['shiji_form']} → {item['chengyu']}"
            f.write(f"### {name}\n\n")
            if item['meaning']:
                f.write(f"**释义**: {item['meaning']}\n\n")
            if item['original']:
                f.write(f"**原文**: {item['original']}\n\n")
            if item['paragraph']:
                f.write(f"**位置**: 第 {item['paragraph']} 段\n\n")
            if item['context']:
                f.write(f"**上下文**:\n\n{item['context']}\n\n")
            f.write('---\n\n')
    print(f'已写入 {output_md}')

    print(f'\n涉及章节: {len(by_chap)} 章')
    print(f'最多成语章节: {by_chap.most_common(5)}')


if __name__ == '__main__':
    main()
