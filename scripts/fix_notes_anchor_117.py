#!/usr/bin/env python3
"""
fix_notes_anchor_117.py — 为 117_司马相如列传 三家注修复 anchor 匹配，填充 sentence_id。

策略（优先级从高到低）：
  1. 精确匹配 anchor_text 在 plain text 中
  2. 于/於 归一化后匹配
  3. before_context 末段（≥8字）作为锚点匹配
  4. anchor_text 的最长连续子串（≥6字）匹配

匹配后写入：
  sentence_id: 段落编号（如 "2.1"、"12"）
  section:     所在节标题（如 "子虚赋"、"上林赋"）

更新文件：
  docs/notes_cache/117-notes.json
  data/notes/117-notes.json（anchor 仍是繁体，sentence_id/section 通用）
"""

import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAGGED  = ROOT / 'chapter_md' / '117_司马相如列传.tagged.md'
CACHE   = ROOT / 'docs' / 'notes_cache' / '117-notes.json'
DATA    = ROOT / 'data' / 'notes' / '117-notes.json'


# ---------- 标注剥离 ----------

def strip_annotations(text: str) -> str:
    text = re.sub(r'〖[^一-鿿〗]{1,3}([^|〗]+)(?:\|[^〗]*)?\s*〗', r'\1', text)
    text = re.sub(r'〖[^〗]*〗', '', text)
    text = re.sub(r'〘[^一-鿿〙]{1,3}([^〙]+)〙', r'\1', text)
    text = re.sub(r'⟦[^一-鿿⟧]{1,3}([^⟧]+)⟧', r'\1', text)
    text = re.sub(r'^\[[0-9.]+\]\s*', '', text, flags=re.MULTILINE)
    # 剩余标记块（::: xxx）不影响正文
    return text


def norm_yu(text: str) -> str:
    """于↔於 归一化（anchor 用简体"于"，tagged 可能用"於"）"""
    return text.replace('于', '於')


def is_basic_cjk(c: str) -> bool:
    return 0x4E00 <= ord(c) <= 0x9FFF


def common_segments(text: str, min_len: int = 4) -> list[str]:
    """提取文本中连续基本CJK字符（U+4E00-U+9FFF）段，长度≥min_len。"""
    segs, cur = [], []
    for c in text:
        if is_basic_cjk(c) or c in '，。；：！？、""''《》〔〕':
            cur.append(c)
        else:
            if len(cur) >= min_len:
                segs.append(''.join(cur))
            cur = []
    if len(cur) >= min_len:
        segs.append(''.join(cur))
    return segs


# ---------- 解析 tagged 文件，建立 para_id → (section, plain_text) 映射 ----------

def parse_tagged(path: Path):
    """
    返回:
      sections: list of (section_name, start_line, end_line)
      paras:    list of (para_id, section_name, raw_lines)
      plain:    全文 plain text（供全局搜索）
      para_plain: { para_id: plain_text }
    """
    raw = path.read_text(encoding='utf-8')
    lines = raw.split('\n')

    sections = []           # (name, line_start)
    paras = []              # (para_id, section, [lines])
    current_sec = '章首'
    current_para = None
    current_lines = []

    PARA_RE = re.compile(r'^\[([0-9]+(?:\.[0-9]+)?)\]\s*(.*)')

    def flush_para():
        if current_para is not None:
            paras.append((current_para, current_sec, list(current_lines)))

    for line in lines:
        # 节标题
        if line.startswith('## '):
            flush_para()
            current_para = None
            current_lines = []
            current_sec = line[3:].strip()
            sections.append(current_sec)
            continue

        # 段落起始
        m = PARA_RE.match(line)
        if m:
            flush_para()
            current_para = m.group(1)
            current_lines = [line]
            current_sec_for_para = current_sec
        else:
            if current_para is not None:
                current_lines.append(line)

    flush_para()

    # 建立 para_id → (section, plain)
    para_plain = {}
    para_section = {}
    for pid, sec, plines in paras:
        plain = strip_annotations('\n'.join(plines))
        para_plain[pid] = plain
        para_section[pid] = sec

    full_plain = strip_annotations(raw)

    # 计算每个段落在 full_plain 中的字符偏移
    para_offsets = {}  # para_id → (start, end)
    for pid, plain in para_plain.items():
        pos = full_plain.find(plain[:min(len(plain), 20)])
        if pos >= 0:
            para_offsets[pid] = (pos, pos + len(plain))

    return para_plain, para_section, full_plain, paras, para_offsets


# ---------- 匹配策略 ----------

def find_para(anchor: str, before_ctx: str, para_plain: dict, full_plain: str,
              para_offsets: dict):
    """返回 (para_id, method) 或 (None, None)。

    para_offsets: { para_id: (start_pos, end_pos) } 相对于 full_plain 的字节偏移
    """
    anchor_yu = norm_yu(anchor)

    for pid, plain in para_plain.items():
        plain_yu = norm_yu(plain)
        if anchor in plain:
            return pid, 'exact'
        if anchor_yu in plain_yu:
            return pid, 'yu_norm'

    # before_context 末段精确匹配
    if before_ctx:
        bc = re.sub(r'^[.…。\s]+', '', before_ctx.strip())
        for tail_len in (20, 12, 8):
            bc_tail = norm_yu(bc[-tail_len:]) if len(bc) >= tail_len else norm_yu(bc)
            if len(bc_tail) < 6:
                continue
            for pid, plain in para_plain.items():
                if bc_tail in norm_yu(plain):
                    return pid, 'before_ctx'

    # anchor 连续基本CJK子串（≥6字）精确匹配
    for length in range(min(len(anchor), 12), 5, -1):
        for start in range(0, len(anchor) - length + 1, 2):
            substr = anchor[start:start + length]
            substr_yu = norm_yu(substr)
            for pid, plain in para_plain.items():
                if substr in plain or substr_yu in norm_yu(plain):
                    return pid, f'substr_{length}'

    # ── 近似匹配：before_context 中提取最长基本CJK段，在 full_plain 中定位 ──
    # 策略：从 before_context 提取若干连续普通汉字段（去掉罕见字），
    # 在全文 plain 中找这些段，推断出 anchor 所在段落。
    if before_ctx:
        bc_clean = re.sub(r'^[.…。\s]+', '', before_ctx.strip())
        # 同时用 anchor 的普通字段辅助
        combined = bc_clean + anchor
        segs = common_segments(combined, min_len=4)
        # 从长到短尝试
        for seg in sorted(segs, key=len, reverse=True):
            seg_yu = norm_yu(seg)
            pos = full_plain.find(seg)
            if pos < 0:
                pos = norm_yu(full_plain).find(seg_yu)
            if pos >= 0:
                # 找到该位置属于哪个段落
                for pid, (p_start, p_end) in para_offsets.items():
                    if p_start <= pos < p_end:
                        return pid, f'approx_{len(seg)}'
                # 若不在任何段落内（可能在段落间的节标题处），找最近的段落
                closest = min(para_offsets.items(),
                              key=lambda kv: min(abs(pos - kv[1][0]), abs(pos - kv[1][1])))
                return closest[0], f'approx_near_{len(seg)}'

    return None, None


# ---------- 主流程 ----------

def main():
    para_plain, para_section, full_plain, paras, para_offsets = parse_tagged(TAGGED)
    print(f'[ok] tagged 解析完：{len(para_plain)} 段，{len(set(para_section.values()))} 节')

    results = {
        'exact': 0, 'yu_norm': 0, 'before_ctx': 0,
        'substr': 0, 'approx': 0, 'approx_near': 0, 'failed': 0
    }

    def process_notes(path: Path):
        data = json.loads(path.read_text(encoding='utf-8'))
        notes = data['notes']
        changed = 0

        for n in notes:
            anchor = n.get('anchor_text', '')
            before = n.get('before_context', '') or ''

            pid, method = find_para(anchor, before, para_plain, full_plain, para_offsets)

            if pid:
                n['sentence_id'] = pid
                n['section'] = para_section.get(pid, '')
                changed += 1
                if method and method.startswith('approx_near'):
                    key = 'approx_near'
                elif method and method.startswith('approx'):
                    key = 'approx'
                else:
                    key = method if method in results else 'substr'
                results[key] += 1
            else:
                n['sentence_id'] = None
                n.pop('section', None)
                results['failed'] += 1

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f'[ok] {path.name}: 更新 {changed}/{len(notes)} 条')

    # 先处理 cache（简体）
    process_notes(CACHE)

    # 再把 sentence_id/section 同步到 data（繁体 anchor，但 id/section 通用）
    cache_data = json.loads(CACHE.read_text(encoding='utf-8'))
    cache_map = {n['id']: n for n in cache_data['notes']}
    data_obj  = json.loads(DATA.read_text(encoding='utf-8'))
    for n in data_obj['notes']:
        cn = cache_map.get(n['id'])
        if cn:
            n['sentence_id'] = cn.get('sentence_id')
            if cn.get('section'):
                n['section'] = cn['section']
            elif 'section' in n:
                del n['section']
    DATA.write_text(
        json.dumps(data_obj, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f'[ok] data/notes/117-notes.json 同步完')

    print()
    print('=== 匹配统计 ===')
    total = sum(results.values())
    for k, v in results.items():
        print(f'  {k:12s}: {v:4d} ({100*v/total:.0f}%)')


if __name__ == '__main__':
    main()
