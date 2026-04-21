#!/usr/bin/env python3
"""
将 find_new_chengyu_from_dict.py 产出的候选列表合并到源词表。

策略：
- 对每条候选，在对应章节干净文本中搜索位置
- 取所在句子作为"原文"栏（去标注、去 PN，首句完整）
- 释义留空（人工填）
- 按章节插入到源 MD 对应 section；若 section 不存在则新建
- 跳过已存在的条目（以成语名为键）

输出文件不覆盖源 MD；产生新建议版本 kg/vocabularies/data/史记成语典故.new.md
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SOURCE_MD = ROOT / 'kg/vocabularies/data/史记成语典故.md'
CHAPTER_DIR = ROOT / 'chapter_md'
DICT_NAMES = ROOT / 'private/book/chengyu_dict_names.txt'
OUT_MD = ROOT / 'kg/vocabularies/data/史记成语典故.new.md'

PN_PATTERN = re.compile(r'^\s*\[(\d+(?:\.\d+)*)\]')
SENTENCE_END = set('。！？；')


def strip_all_markup(text):
    t = text
    t = re.sub(r'〘※([^〘〙|]+)(?:\|[^〘〙]*)?〙', r'\1', t)
    t = re.sub(r'〖.([^〖〗|]+)(?:\|[^〖〗]*)?〗', r'\1', t)
    t = re.sub(r'⟦.([^⟦⟧|]+)(?:\|[^⟦⟧]*)?⟧', r'\1', t)
    return t


def clean_sentence(s):
    s = re.sub(r'\[\d+(?:\.\d+)*\]\s*', '', s)
    s = s.replace('>', '').strip()
    s = re.sub(r'^[\s\-:#>\*]+', '', s)
    # 去除首尾引号/对话标记
    s = s.strip('“”"\'‘’ ')
    s = re.sub(r'^[^\u4e00-\u9fff]*', '', s)  # 去掉开头非汉字（包括引号、冒号、空格）
    # 如果文本以逗号或顿号结尾（不完整句），剥除尾部逗号
    s = s.rstrip('，、；, ')
    # 如果文本超过 60 字，截到首个 。！？ 处
    if len(s) > 60:
        for i, c in enumerate(s):
            if c in '。！？' and i >= 6:
                s = s[:i + 1]
                break
    return s.strip()


def extract_sentence(pure, pos, max_chars=200):
    if pos < 0 or pos >= len(pure):
        return ''
    N = len(pure)
    start = pos
    while start > 0 and pure[start - 1] not in SENTENCE_END and pure[start - 1] != '\n':
        start -= 1
        if pos - start > max_chars:
            break
    end = pos
    while end < N and pure[end] not in SENTENCE_END and pure[end] != '\n':
        end += 1
        if end - pos > max_chars:
            break
    if end < N and pure[end] in SENTENCE_END:
        end += 1
    return clean_sentence(pure[start:end])


def parse_existing():
    """返回 {(chap_num, chengyu_name)}, {chap_num: 章节标题}"""
    existing = set()
    chap_titles = {}
    current_chap = None
    for line in SOURCE_MD.read_text(encoding='utf-8').split('\n'):
        line = line.rstrip('\n')
        m = re.match(r'^###\s+(\d+)\s+(.+)$', line.strip())
        if m:
            current_chap = m.group(1).zfill(3)
            chap_titles[current_chap] = m.group(2).strip()
            continue
        if current_chap and line.startswith('|') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 2 and parts[0] and parts[0] != '成语':
                existing.add((current_chap, parts[0]))
    return existing, chap_titles


def find_new_candidates(dict_names, existing):
    """返回 [(chap, name, original_sentence)]，按 chap+name 排序"""
    # 建已知 name 集（不分章节，避免跨章节重复）
    existing_names = {name for _, name in existing}

    # 加载每章干净文本
    chapters = {}
    for f in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        stem = f.stem.replace('.tagged', '')
        m = re.match(r'(\d{3})_(.+)', stem)
        if not m:
            continue
        chapters[m.group(1)] = {'title': m.group(2), 'pure': strip_all_markup(f.read_text(encoding='utf-8'))}

    results = []
    for name in dict_names:
        if name in existing_names:
            continue
        if len(name) < 4:
            continue
        # 找首个命中的章节
        for num, c in chapters.items():
            idx = c['pure'].find(name)
            if idx >= 0:
                sentence = extract_sentence(c['pure'], idx)
                results.append((num, c['title'], name, sentence))
                break
    results.sort()
    return results


def main():
    existing, chap_titles = parse_existing()
    dict_names = [n.strip() for n in DICT_NAMES.read_text().split('\n') if n.strip()]
    candidates = find_new_candidates(dict_names, existing)
    print(f'新候选: {len(candidates)}')

    # 按章节分组
    by_chap = {}
    for num, title, name, sentence in candidates:
        by_chap.setdefault(num, {'title': title, 'entries': []})['entries'].append((name, sentence))

    # 读取源 MD 并插入
    lines = SOURCE_MD.read_text(encoding='utf-8').split('\n')
    # 找每个 ### NNN 行的位置
    chap_line_idx = {}
    for i, line in enumerate(lines):
        m = re.match(r'^###\s+(\d+)\s+', line.strip())
        if m:
            chap_line_idx[m.group(1).zfill(3)] = i

    # 对每个候选章节找表格末尾，插入新行
    # 倒序处理避免索引错乱
    inserts = []  # (chap, line_idx_to_insert_after, [new_lines])
    for num in sorted(by_chap.keys()):
        group = by_chap[num]
        new_rows = [f"| {name} | {sentence[:100]} |  |" for name, sentence in group['entries']]
        if num in chap_line_idx:
            # 找该章表格结尾：从章节行往下找，遇到下一个 ### 或文件末尾
            start = chap_line_idx[num]
            end = start + 1
            while end < len(lines) and not re.match(r'^###\s', lines[end].strip()):
                end += 1
            # 表格末尾（可能跟空行）
            insert_pos = end
            # 回退到最后一个 | 行
            while insert_pos > start and not lines[insert_pos - 1].strip().startswith('|'):
                insert_pos -= 1
            inserts.append((insert_pos, new_rows))
        else:
            # 章节不存在，在末尾追加
            inserts.append((len(lines), [
                '',
                f'### {num} {group["title"]}',
                '',
                '| 成语 | 原文 | 释义 |',
                '|------|------|------|',
            ] + new_rows))

    # 倒序插入
    inserts.sort(key=lambda x: -x[0])
    for pos, new_lines in inserts:
        lines[pos:pos] = new_lines

    OUT_MD.write_text('\n'.join(lines), encoding='utf-8')
    print(f'写入 {OUT_MD}')
    print(f'新增章节: {sum(1 for num in by_chap if num not in chap_line_idx)}')
    print(f'涉及章节: {len(by_chap)}')
    print(f'新增条目: {sum(len(g["entries"]) for g in by_chap.values())}')


if __name__ == '__main__':
    main()
