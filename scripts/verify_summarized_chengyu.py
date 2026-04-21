#!/usr/bin/env python3
"""
验证"总结性成语"的原文是否在史记对应章节中出现。

分类：
- tagged: 章节中已有 〘※〙 标注（无需总结，已直接从原文提取）
- verbatim: 原文字串在章节干净文本中直接出现
- partial: 原文包含省略号，主要片段在章节中出现
- paren: 原文是括号内的叙述性概括（需人工审核相关性）
- unverified: 原文在章节中完全找不到 → 疑似无关

输出:
  logs/chengyu_verification.txt  — 详细报告
  data/chengyu_summarized.json   — 通过验证的总结性成语清单
"""

import re
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHENGYU_MD = ROOT / "kg/vocabularies/data/史记成语典故.md"
CHAPTER_DIR = ROOT / "chapter_md"
LOG = ROOT / "logs/chengyu_verification.txt"
OUT_JSON = ROOT / "data/chengyu_summarized.json"
OUT_MD = ROOT / "data/chengyu_summarized.md"


def parse_chengyu_md(md_file):
    content = md_file.read_text(encoding='utf-8')
    entries = []
    current_chapter = None
    for line in content.split('\n'):
        line = line.strip()
        m = re.match(r'^###\s+(\d+)\s+(.+)$', line)
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
                entries.append((current_chapter, name, original, meaning))
    return entries


def strip_all_markup(text):
    t = text
    t = re.sub(r'〘※([^〘〙|]+)(?:\|[^〘〙]*)?〙', r'\1', t)
    t = re.sub(r'〖.([^〖〗|]+)(?:\|[^〖〗]*)?〗', r'\1', t)
    t = re.sub(r'⟦.([^⟦⟧|]+)(?:\|[^⟦⟧]*)?⟧', r'\1', t)
    return t


def get_chapter_title(chap_num):
    files = list(CHAPTER_DIR.glob(f'{chap_num}_*.tagged.md'))
    if files:
        stem = files[0].stem.replace('.tagged', '')
        return stem[4:]
    return ''


def is_tagged_in_chapter(chap_num, name, content):
    """检查成语是否已被 〘※〙 标注（匹配 modern 或 shiji_form）"""
    for m in re.finditer(r'〘※([^〘〙|]+)(?:\|([^〘〙]+))?〙', content):
        shiji_form = m.group(1)
        modern = m.group(2)
        if modern == name or shiji_form == name:
            return True
    return False


def extract_quotable(original_text):
    """
    从 original_text 中提取可查询的子串列表。
    处理：
    - 省略号 … 或 ... 分隔的多段
    - 括号内注释忽略
    - 单引号/特殊标点保持
    """
    # 移除括号注释
    cleaned = re.sub(r'（[^）]*）', '', original_text)
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)
    # 按 … 或 ... 分割
    parts = re.split(r'…+|\.{3,}', cleaned)
    # 去除引号
    parts = [p.strip().strip("'\"'\"") for p in parts]
    parts = [p for p in parts if len(p) >= 3]  # 至少3字才查询
    return parts


def normalize(text):
    """规范化标点与异体字以利匹配"""
    t = text
    # 去所有常见标点/空白/引号（对比仅保留汉字+少量分隔）
    t = re.sub(r"['\"'\"''\";;,。、；：！？\s（）()“”《》·—\-]", '', t)
    # 异体字归并（史记用 脣/於/无/谿 等）
    variants = {
        '脣': '唇',
        '於': '于',
        '甕': '瓮',
        '壅': '雍',
        '穀': '谷',
        '飜': '翻',
        '説': '说',
    }
    for k, v in variants.items():
        t = t.replace(k, v)
    return t


def verify_entry(chap_num, name, original, meaning, content, pure):
    """
    验证单条目，返回 (status, detail)
    status: 'tagged' | 'verbatim' | 'partial' | 'paren' | 'unverified'
    """
    if is_tagged_in_chapter(chap_num, name, content):
        return 'tagged', {'note': '已打〘※〙标注'}

    # 是否整段在括号里？
    if original.startswith('（') or original.startswith('('):
        return 'paren', {'note': '原文为括号内叙述性概括', 'original': original}

    pure_norm = normalize(pure)

    # 有省略号？
    if '…' in original or '...' in original:
        parts = extract_quotable(original)
        matched = []
        for p in parts:
            if normalize(p) in pure_norm:
                matched.append(p)
        if matched:
            return 'partial', {'matched_parts': matched, 'original': original}
        else:
            return 'unverified', {'original': original, 'parts_checked': parts}

    # 规范化后原文是否在干净文本中？
    orig_norm = normalize(original)
    if orig_norm and orig_norm in pure_norm:
        return 'verbatim', {'original': original}

    # 主要片段匹配（按逗号/分号/句号分句）
    clauses = re.split(r'[，、；;。]', original)
    clauses = [c.strip() for c in clauses if len(c.strip()) >= 3]
    matched_clauses = [c for c in clauses if normalize(c) in pure_norm]
    if matched_clauses:
        return 'partial', {'matched_parts': matched_clauses, 'original': original}

    return 'unverified', {'original': original}


def main():
    entries = parse_chengyu_md(CHENGYU_MD)

    # 缓存章节内容
    chapter_cache = {}
    chapter_pure_cache = {}

    by_status = {
        'tagged': [],
        'verbatim': [],
        'partial': [],
        'paren': [],
        'unverified': [],
    }

    for chap_num, name, original, meaning in entries:
        if chap_num not in chapter_cache:
            files = list(CHAPTER_DIR.glob(f'{chap_num}_*.tagged.md'))
            if not files:
                chapter_cache[chap_num] = ''
                chapter_pure_cache[chap_num] = ''
            else:
                content = files[0].read_text(encoding='utf-8')
                chapter_cache[chap_num] = content
                chapter_pure_cache[chap_num] = strip_all_markup(content)

        content = chapter_cache[chap_num]
        pure = chapter_pure_cache[chap_num]

        status, detail = verify_entry(chap_num, name, original, meaning, content, pure)
        by_status[status].append({
            'chapter_num': chap_num,
            'chapter_title': get_chapter_title(chap_num),
            'chengyu': name,
            'original': original,
            'meaning': meaning,
            'status': status,
            'detail': detail,
        })

    # 打印汇总
    log_lines = []
    log_lines.append(f"总条目: {len(entries)}")
    for k, v in by_status.items():
        log_lines.append(f"  {k}: {len(v)}")

    for cat in ['unverified', 'paren', 'partial', 'verbatim', 'tagged']:
        log_lines.append(f"\n{'='*60}")
        log_lines.append(f"=== {cat.upper()} ({len(by_status[cat])} 条) ===")
        log_lines.append(f"{'='*60}")
        for item in by_status[cat]:
            log_lines.append(f"[{item['chapter_num']}] {item['chengyu']}")
            log_lines.append(f"    原文: {item['original']}")
            log_lines.append(f"    释义: {item['meaning']}")
            if 'matched_parts' in item.get('detail', {}):
                log_lines.append(f"    匹配片段: {item['detail']['matched_parts']}")
            if item.get('detail', {}).get('note'):
                log_lines.append(f"    备注: {item['detail']['note']}")
            log_lines.append('')

    LOG.write_text('\n'.join(log_lines), encoding='utf-8')
    print('\n'.join(log_lines[:10]))
    print(f'\n完整报告: {LOG}')


if __name__ == '__main__':
    main()
