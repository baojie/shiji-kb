#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_search_index.py — 为 docs/ 静态站构建客户端全文检索索引

扫描 chapter_md/*.tagged.md，去除全部语义标注符号，
按 Purple Number 段落 [N] / [N.M] 切分，输出紧凑 JSON：

    docs/data/search-index.json

索引结构:
    {
      "chapters": [{"n": 1, "f": "001_五帝本纪", "t": "五帝本纪"}, ...],
      "entries":  [{"c": 1, "p": "1",   "x": "黄帝者..."}, ...]
    }

段落 URL: chapters/{f}.html#pn-{p}
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = ROOT / 'chapter_md'
OUT_FILE = ROOT / 'docs' / 'data' / 'search-index.json'

# 与 scripts/lint_text_integrity.py 保持一致的标注前缀集
_ENTITY_PFX = r'[#@=;$%&^\~•!\'+?{:\[_◆]'

# [N] [N.M] [N.M.K]
_PN_RE = re.compile(r'^\s*\[(\d+(?:\.\d+)*)\]\s*(.*)$')


def strip_markup(text: str) -> str:
    """移除全部标注符号，仅保留实体内容本身。"""
    # Markdown 标题行
    text = re.sub(r'^#{1,6}.*$', '', text, flags=re.MULTILINE)
    # ## 标题 区块
    text = re.sub(r'^## 标题\n[^\n]*\n?', '', text, flags=re.MULTILINE)
    # ::: 围栏块标记
    text = re.sub(r'^:::.*$', '', text, flags=re.MULTILINE)
    # 行首 "> "
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
    # 行首 "- "（保留内容）
    text = re.sub(r'^\s*-\s', '', text, flags=re.MULTILINE)
    # 动词标注 ⟦◈X⟧ / ⟦◈X|Y⟧ → X
    text = re.sub(r'⟦[◈◉○◇]([^⟦⟧|]*)(?:\|[^⟦⟧]*)?⟧', r'\1', text)
    # 名词实体 〖@X〗 / 〖@X|Y〗 → X
    text = re.sub(rf'〖{_ENTITY_PFX}([^〖〗|]*)(?:\|[^〖〗]*)?〗', r'\1', text)
    text = re.sub(r'〖[^〗]*〗', '', text)
    # 旧格式残留
    text = re.sub(r'〘([^〘〙]*)〙', r'\1', text)
    # **bold**
    text = re.sub(r'\*\*([^*]*)\*\*', r'\1', text)
    # --- 分隔线
    text = re.sub(r'^-{3,}\s*$', '', text, flags=re.MULTILINE)
    # 表格分隔行
    text = re.sub(r'^\|[\s\-|]+\|?\s*$', '', text, flags=re.MULTILINE)
    return text


def split_paragraphs(body: str):
    """按 Purple Number 标记切分为 (pid, text) 列表。

    同一段内的多行（列表项等）合并为一个文本块。
    """
    blocks = []
    cur_pid = None
    cur_lines = []

    def flush():
        if cur_pid is None:
            return
        text = ' '.join(s for s in cur_lines if s.strip()).strip()
        text = re.sub(r'\s+', '', text)  # 中文文本去空格
        if text:
            blocks.append((cur_pid, text))

    for raw_line in body.split('\n'):
        line = raw_line.rstrip()
        m = _PN_RE.match(line)
        if m:
            flush()
            cur_pid = m.group(1)
            cur_lines = [m.group(2)]
        else:
            if cur_pid is not None:
                cur_lines.append(line)
    flush()
    return blocks


def parse_chapter(path: Path):
    """读取一个 tagged.md，返回 (chapter_num, filename_stem, chapter_title, blocks)"""
    stem = path.name.replace('.tagged.md', '')  # 001_五帝本纪
    m = re.match(r'^(\d+)_(.+)$', stem)
    if not m:
        return None
    chapter_num = int(m.group(1))
    chapter_title = m.group(2)

    raw = path.read_text(encoding='utf-8')
    stripped = strip_markup(raw)
    blocks = split_paragraphs(stripped)
    return chapter_num, stem, chapter_title, blocks


def main():
    if not CHAPTER_DIR.is_dir():
        print(f'错误: 目录不存在 {CHAPTER_DIR}', file=sys.stderr)
        sys.exit(1)

    files = sorted(CHAPTER_DIR.glob('*.tagged.md'))
    if not files:
        print(f'错误: 未找到 *.tagged.md 于 {CHAPTER_DIR}', file=sys.stderr)
        sys.exit(1)

    chapters = []
    entries = []

    for f in files:
        parsed = parse_chapter(f)
        if not parsed:
            print(f'跳过: {f.name}', file=sys.stderr)
            continue
        num, stem, title, blocks = parsed
        chapters.append({'n': num, 'f': stem, 't': title})
        for pid, text in blocks:
            entries.append({'c': num, 'p': pid, 'x': text})

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {'chapters': chapters, 'entries': entries}
    OUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(',', ':')),
        encoding='utf-8',
    )

    total_chars = sum(len(e['x']) for e in entries)
    size_kb = OUT_FILE.stat().st_size / 1024
    print(f'✓ 章节: {len(chapters)}')
    print(f'✓ 段落: {len(entries)}')
    print(f'✓ 正文总字数: {total_chars:,}')
    print(f'✓ 输出: {OUT_FILE} ({size_kb:.1f} KB)')


if __name__ == '__main__':
    main()
