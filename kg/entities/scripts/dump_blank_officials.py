#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为未分类官职提取上下文，供人工反思分类。

用法：
  python3 dump_blank_officials.py [轮次号]
  例：python3 dump_blank_officials.py 2    # 输出 doc/entities/官职反思/第二轮_上下文.md
默认（无参数）输出到 doc/entities/官职反思/待反思_上下文.md。

格式：
  ## 1. NAME (N 次出现)
  - 001_五帝本纪 pn-3: ...前18字...〖;NAME〗...后18字...

历史沉淀的反思报告见：
  doc/entities/官职反思/
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
CATS_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'official_categories.json'
CHAPTER_DIR = _ROOT / 'chapter_md'
REFLECT_DIR = _ROOT / 'doc' / 'entities' / '官职反思'

_CHINESE_NUM = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']


def _round_label(n):
    if 1 <= n <= 10:
        return _CHINESE_NUM[n]
    return str(n)


if len(sys.argv) >= 2 and sys.argv[1].isdigit():
    round_n = int(sys.argv[1])
    OUT_FILE = REFLECT_DIR / f'第{_round_label(round_n)}轮_上下文.md'
else:
    OUT_FILE = REFLECT_DIR / '待反思_上下文.md'

CONTEXT_CHARS = 18


def strip_all_tags(text):
    """去除所有实体/动词 tag 外壳，只保留表层文字。"""
    text = re.sub(r'〖[@=;%&◆\^~#•!\?\+\$\{:\[_]([^〖〗]+)〗', r'\1', text)
    text = re.sub(r'⟦[◈◉○◇]([^⟦⟧]+)⟧', r'\1', text)
    text = re.sub(r'([^\s|]+)\|[^〖〗\s]+', r'\1', text)
    return text


def extract_contexts(name, content, chapter_label):
    """在 content 中找到所有 〖;name〗 的出现点，返回上下文列表。"""
    results = []
    pat = re.compile(r'〖;(' + re.escape(name) + r')(?:\|[^〖〗]+)?〗')
    para_marks = [(m.start(), m.group(1)) for m in re.finditer(r'\[(\d+(?:\.\d+)*)\]', content)]
    for m in pat.finditer(content):
        pos = m.start()
        para_num = None
        for p_pos, p_num in para_marks:
            if p_pos > pos:
                break
            para_num = p_num
        start = max(0, pos - CONTEXT_CHARS * 2)
        end = min(len(content), m.end() + CONTEXT_CHARS * 2)
        raw = content[start:end]
        stripped = strip_all_tags(raw)
        idx = stripped.find(name)
        if idx >= 0:
            s = max(0, idx - CONTEXT_CHARS)
            e = min(len(stripped), idx + len(name) + CONTEXT_CHARS)
            snippet = (
                stripped[s:idx]
                + '【' + name + '】'
                + stripped[idx + len(name):e]
            )
        else:
            snippet = stripped
        snippet = re.sub(r'\s+', ' ', snippet).strip()
        results.append((chapter_label, para_num, snippet))
    return results


def main():
    cats = json.loads(CATS_JSON.read_text(encoding='utf-8'))
    idx = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
    officials = idx['official']

    blanks = [n for n, c in cats.items() if not c]
    print(f'未分类官职: {len(blanks)}')

    chapter_refs = defaultdict(set)
    for n in blanks:
        for ch, _ in officials[n]['refs']:
            chapter_refs[ch].add(n)

    all_contexts = defaultdict(list)
    for ch_id, names in chapter_refs.items():
        chap_file = CHAPTER_DIR / f'{ch_id}.tagged.md'
        if not chap_file.exists():
            continue
        content = chap_file.read_text(encoding='utf-8')
        for name in names:
            ctxs = extract_contexts(name, content, ch_id)
            all_contexts[name].extend(ctxs)

    sorted_names = sorted(blanks)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append(f'# 未分类官职上下文反思 ({len(sorted_names)} 条)')
    lines.append('')
    lines.append('> 自动从 `chapter_md/*.tagged.md` 提取上下文，供 SKILL_03i 人工反思分类。')
    lines.append('> 【X】= 目标官职；两侧各 18 字上下文，剥去所有 tag 标记。')
    lines.append('')
    lines.append(f'共 {len(sorted_names)} 条。每 10 条后可插入 ——反思区——，判断能否提炼规则。')
    lines.append('')

    for i, name in enumerate(sorted_names, 1):
        ctxs = all_contexts.get(name, [])
        total_refs = officials[name]['count']
        lines.append(f'## {i:03d}. `{name}` ({total_refs} 次出现)')
        if not ctxs:
            lines.append('  - (无上下文可提)')
        else:
            for ch, pn, snip in ctxs[:6]:
                pn_label = f'pn-{pn}' if pn else ''
                lines.append(f'  - {ch} {pn_label}: {snip}')
            if len(ctxs) > 6:
                lines.append(f'  - (另有 {len(ctxs)-6} 处同类)')
        lines.append('')

    OUT_FILE.write_text('\n'.join(lines), encoding='utf-8')
    print(f'写入: {OUT_FILE} ({len(lines)} 行)')


if __name__ == '__main__':
    main()
