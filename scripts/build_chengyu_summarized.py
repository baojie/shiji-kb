#!/usr/bin/env python3
"""
从 kg/vocabularies/data/史记成语典故.md 构建"总结性成语"数据文件。

输出：
  data/chengyu_summarized.json  — JSON 结构化数据
  data/chengyu_summarized.md    — Markdown 文档视图

定义："总结性成语" = 词表中存在、但并未在章节文件中作 〘※〙 标注的条目。
这些通常是：
- 史记作不同字序/异体（如"移风易俗"tagged, but"助纣为虐"is summarized）
- 史记描述相关事件但未直接提及成语（如"赵氏孤儿"）
- 原文跨多段或字序颠倒，不适合逐字标注

此脚本仅从源 MD 派生，不触碰标注文件，且输出文件 chengyu.json / chengyu.md
由 extract_chengyu_tagged.py 独立生成（只含已标注）。二者并存，互不覆盖。
"""

import re
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHENGYU_MD = ROOT / "kg/vocabularies/data/史记成语典故.md"
CHAPTER_DIR = ROOT / "chapter_md"
OUT_JSON = ROOT / "data/chengyu_summarized.json"
OUT_MD = ROOT / "data/chengyu_summarized.md"


def parse_chengyu_md(md_file):
    content = md_file.read_text(encoding='utf-8')
    entries = []
    current_chapter = None
    current_title = ''
    for line in content.split('\n'):
        line = line.strip()
        m = re.match(r'^###\s+(\d+)\s+(.+)$', line)
        if m:
            current_chapter = m.group(1).zfill(3)
            current_title = m.group(2).strip()
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
                entries.append({
                    'chapter_num': current_chapter,
                    'chapter_title': current_title,
                    'chengyu': name,
                    'original': original,
                    'meaning': meaning,
                })
    return entries


def is_tagged_in_chapter(name, content):
    """章节中是否已有 〘※〙 标注匹配此成语名（modern 或 shiji 形式）"""
    for m in re.finditer(r'〘※([^〘〙|]+)(?:\|([^〘〙]+))?〙', content):
        shiji_form = m.group(1)
        modern = m.group(2)
        if modern == name or shiji_form == name:
            return True
    return False


def normalize(text):
    t = text
    t = re.sub(r"['\"'\"''\";;,。、；：！？\s（）()“”《》·—\-]", '', t)
    variants = {'脣': '唇', '於': '于', '甕': '瓮', '穀': '谷', '説': '说', '飜': '翻'}
    for k, v in variants.items():
        t = t.replace(k, v)
    return t


def strip_all_markup(text):
    t = text
    t = re.sub(r'〘※([^〘〙|]+)(?:\|[^〘〙]*)?〙', r'\1', t)
    t = re.sub(r'〖.([^〖〗|]+)(?:\|[^〖〗]*)?〗', r'\1', t)
    t = re.sub(r'⟦.([^⟦⟧|]+)(?:\|[^⟦⟧]*)?⟧', r'\1', t)
    return t


SENTENCE_END = set('。！？；')


def extract_sentence_from_pure(pure, pos, max_chars=200):
    """从纯文本中以 pos 为中心抽取所在一句"""
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
    return _clean_sentence(pure[start:end])


def extract_sentence_span(pure, start_pos, end_pos, max_chars=300):
    """抽取覆盖 [start_pos, end_pos] 的句段（向外扩展到句界）"""
    if start_pos < 0 or start_pos >= len(pure):
        return ''
    N = len(pure)
    start = start_pos
    while start > 0 and pure[start - 1] not in SENTENCE_END and pure[start - 1] != '\n':
        start -= 1
        if start_pos - start > max_chars:
            break
    end = end_pos
    while end < N and pure[end] not in SENTENCE_END and pure[end] != '\n':
        end += 1
        if end - end_pos > max_chars:
            break
    if end < N and pure[end] in SENTENCE_END:
        end += 1
    return _clean_sentence(pure[start:end])


def _clean_sentence(s):
    s = re.sub(r'\[\d+(?:\.\d+)*\]\s*', '', s)
    s = s.replace('>', '').strip()
    s = re.sub(r'^[\s\-:#>\*]+', '', s)
    return s.strip()


PN_PATTERN = re.compile(r'^\s*\[(\d+(?:\.\d+)*)\]')


def locate_in_pure(pure, phrase):
    """
    在纯文本 pure 中定位 phrase，返回位置（字符索引）。
    1. 整句 find
    2. 按 phrase 顺序取首个 ≥3 字连续汉字片段 find
    3. 兜底：首 3 字
    目标：返回的 idx 尽量指向 phrase 首段出现位置，以便正确提取句子上下文。
    """
    idx = pure.find(phrase)
    if idx >= 0:
        return idx

    # 顺序提取 ≥3 字的中文片段
    segments = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]{3,}', phrase)
    # 按 phrase 中出现顺序查找；若前段不在原文，则后段兜底
    for seg in segments:
        i = pure.find(seg)
        if i >= 0:
            return i

    head = phrase[:3] if len(phrase) >= 3 else phrase
    return pure.find(head)


def find_paragraph(content, pure, phrase):
    """定位 phrase 所在段落号（支持 [N]/[N.M]/[N.M.K] 多层）"""
    idx = locate_in_pure(pure, phrase)
    if idx < 0:
        return None
    chunk = pure[max(0, idx - 2000):idx]
    for line in reversed(chunk.split('\n')):
        m = PN_PATTERN.match(line.strip())
        if m:
            return m.group(1)
    return None


def main():
    all_entries = parse_chengyu_md(CHENGYU_MD)

    summarized = []
    chapter_cache = {}
    chapter_pure = {}

    for ent in all_entries:
        chap = ent['chapter_num']
        if chap not in chapter_cache:
            files = list(CHAPTER_DIR.glob(f"{chap}_*.tagged.md"))
            if not files:
                chapter_cache[chap] = ''
                chapter_pure[chap] = ''
            else:
                content = files[0].read_text(encoding='utf-8')
                chapter_cache[chap] = content
                chapter_pure[chap] = strip_all_markup(content)

        content = chapter_cache[chap]
        pure = chapter_pure[chap]
        name = ent['chengyu']

        # 跳过已标注的条目
        if is_tagged_in_chapter(name, content):
            continue

        # 验证：原文是否在 pure 中出现（忽略括号）
        original = ent['original']
        is_paren = original.startswith('（') or original.startswith('(')

        if is_paren:
            # 括号叙述性概括：无法验证原文，但保留
            anchor = None
            verified = 'narrative'
        else:
            # 清理原文
            cleaned = re.sub(r'（[^）]*）', '', original).strip()
            cleaned = cleaned.strip("'\"'\"")
            # 省略号分段
            if '…' in cleaned or '...' in cleaned:
                parts = re.split(r'…+|\.{3,}', cleaned)
                parts = [p.strip().strip("'\"'\"") for p in parts if len(p.strip()) >= 3]
                matched = [p for p in parts if normalize(p) in normalize(pure)]
                if matched:
                    anchor = matched[0]
                    verified = 'partial'
                else:
                    anchor = None
                    verified = 'unverified'
            elif normalize(cleaned) in normalize(pure):
                anchor = cleaned
                verified = 'verbatim'
            else:
                # 按分句检查
                clauses = re.split(r'[，、；;。]', cleaned)
                clauses = [c.strip() for c in clauses if len(c.strip()) >= 3]
                matched = [c for c in clauses if normalize(c) in normalize(pure)]
                if matched:
                    anchor = matched[0]
                    verified = 'partial'
                else:
                    anchor = None
                    verified = 'unverified'

        paragraph = find_paragraph(content, pure, anchor) if anchor else None

        # 抽取所在句子（clean text）；若 anchor 跨多句，则覆盖首末两段
        sentence = ''
        if anchor:
            segments = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]{3,}', anchor)
            first_idx = locate_in_pure(pure, anchor)
            if first_idx < 0 and segments:
                first_idx = pure.find(segments[0])
            # 找末段位置
            last_idx = -1
            if len(segments) >= 2:
                for seg in reversed(segments):
                    i = pure.find(seg, max(0, first_idx))
                    if i >= 0:
                        last_idx = i + len(seg) - 1
                        break
            if first_idx >= 0 and first_idx < len(pure):
                if last_idx > first_idx and last_idx - first_idx < 200:
                    sentence = extract_sentence_span(pure, first_idx, last_idx)
                else:
                    sentence = extract_sentence_from_pure(pure, first_idx)

        summarized.append({
            'chapter_num': chap,
            'chapter_title': ent['chapter_title'],
            'chengyu': name,
            'original': original,
            'meaning': ent['meaning'],
            'verified': verified,
            'anchor': anchor,
            'paragraph': paragraph,
            'context': sentence,
        })

    # 按章节排序
    summarized.sort(key=lambda x: (x['chapter_num'], x['chengyu']))

    # 写 JSON
    doc = {
        '_description': '史记成语典故中"总结性"条目：未在章节以〘※〙直接标注，但与原文相关。由 build_chengyu_summarized.py 从 kg/vocabularies/data/史记成语典故.md 派生。',
        '_note': '修改源头请编辑 kg/vocabularies/data/史记成语典故.md 后重新运行脚本。请勿手编此文件。',
        '_total': len(summarized),
        'entries': summarized,
    }
    OUT_JSON.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f'已写入 {OUT_JSON}（{len(summarized)} 条）')

    # 写 Markdown
    from collections import Counter
    by_chap = Counter(e['chapter_num'] for e in summarized)
    by_verified = Counter(e['verified'] for e in summarized)

    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('# 史记总结性成语典故\n\n')
        f.write('> 本文件由 `scripts/build_chengyu_summarized.py` 从 '
                '`kg/vocabularies/data/史记成语典故.md` 派生。\n'
                '> 收录**未在章节作 〘※〙 标注**的成语条目（原文字序异体、跨段概括、'
                '或叙事性总结）。\n'
                '> 已作 〘※〙 标注的成语见 `data/chengyu.md`。\n\n')
        f.write(f'- 总条目：{len(summarized)}\n')
        f.write(f'- 涉及章节：{len(by_chap)}\n')
        f.write('- 验证状态分布：\n')
        for k, v in by_verified.items():
            f.write(f'  - {k}: {v}\n')
        f.write('\n---\n\n')

        current_chap = None
        for e in summarized:
            ck = f"{e['chapter_num']} {e['chapter_title']}"
            if ck != current_chap:
                f.write(f"## {ck}\n\n")
                current_chap = ck
            f.write(f"### {e['chengyu']}\n\n")
            f.write(f"- **释义**: {e['meaning']}\n")
            f.write(f"- **原文**: {e['original']}\n")
            if e['paragraph']:
                f.write(f"- **位置**: 第 {e['paragraph']} 段\n")
            if e['anchor']:
                f.write(f"- **锚句**: {e['anchor']}\n")
            f.write(f"- **验证**: {e['verified']}\n\n")

    print(f'已写入 {OUT_MD}')
    print(f'涉及章节: {len(by_chap)}')
    print(f'验证分布: {dict(by_verified)}')


if __name__ == '__main__':
    main()
