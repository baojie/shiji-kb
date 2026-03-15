#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint_text_integrity.py — 标注文本完整性检查

去除全部语义标注符号后，与 docs/original_text/ 中的原文逐字比对，
列出不一致处并保存到 logs/lint_text_integrity.txt。

用法:
    python scripts/lint_text_integrity.py              # 检查全部130章
    python scripts/lint_text_integrity.py 033 034      # 检查指定章节
    python scripts/lint_text_integrity.py --all        # 包含标点/编码差异

差异分类（自动过滤）:
    【实质差异】— 汉字字符被增加/删除/改写，必须修复
    【标点规范化】— 全角↔半角标点（，→, 等），标注规范，可忽略
    【编码规范化】— PUA私用区字符→标准Unicode，可忽略
"""

import re
import sys
import difflib
from pathlib import Path
from datetime import datetime


# ── 白名单：已确认的正确校勘 ─────────────────────────────
def _load_whitelist(path: Path) -> dict[str, list[tuple[str, str]]]:
    """读取 lint_whitelist.txt，返回 {章节号: [(orig, tagged), ...]}"""
    wl: dict[str, list[tuple[str, str]]] = {}
    if not path.exists():
        return wl
    for line in path.read_text('utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        cid = parts[0].zfill(3)
        orig = parts[1]
        tagged = parts[2]
        wl.setdefault(cid, []).append((orig, tagged))
    return wl

# ── 预处理规范化映射 ──────────────────────────────────────
# 对原文和标注各自做同样的规范化，然后比较规范化结果。
# 差异 = 规范化后仍存在 → 实质差异。
# 差异 = 规范化后消失   → 标点/编码规范化，可忽略。

_NORM_TABLE = str.maketrans({
    # 各式引号 → ASCII 引号（编辑器自动替换，忽略差异）
    '\u201c': '"',   # "
    '\u201d': '"',   # "
    '\u300c': '"',   # 「
    '\u300d': '"',   # 」
    '\u300e': '"',   # 『
    '\u300f': '"',   # 』
    '\u2018': "'",   # '
    '\u2019': "'",   # '
    # 字形变体
    '\u5dff': '\u5e02',  # 巿 → 市
    # 通假/异体字对（史记文本常见）
    '\u4e8e': '\u65bc',  # 于 → 於（同一用法，异体）
    '\u4e0e': '\u8207',  # 与 → 與（繁简变体）
    '\u4e3a': '\u70ba',  # 为 → 為（繁简变体）
})

def _norm(text: str) -> str:
    """规范化字形变体，消除等价异体字差异。"""
    # 异体字映射
    text = text.translate(_NORM_TABLE)
    # 表格符号 | 是结构性添加（年表章节），不影响文本内容
    text = text.replace('|', '')
    # 行内标记 [r1] [r2] 等行标
    text = re.sub(r'\[r\d+\]', '', text)
    # PUA私用区字符：两侧都去掉，避免影响对齐
    text = re.sub(r'[\ue000-\uf8ff]', '', text)
    return text

# ── 实体标注前缀字符 ──────────────────────────────────────
_ENTITY_PFX = r'[#@=;$%&^\~*!\'+]'


# ═══════════════════════════════════════════════════════════
# 标注去除
# ═══════════════════════════════════════════════════════════

def strip_markup(text: str) -> str:
    """去除全部语义标注符号，保留实体内容本身。"""

    # 1. Markdown 标题行（不在原文中）
    text = re.sub(r'^#{1,6}.*$', '', text, flags=re.MULTILINE)

    # 2. ## 标题 区块（标注标题行 + 下方内容行，不在原文中）
    text = re.sub(r'^## 标题\n[^\n]*\n?', '', text, flags=re.MULTILINE)

    # 3. ::: 围栏块标记行（太史公曰 / 赞诗等）
    text = re.sub(r'^:::.*$', '', text, flags=re.MULTILINE)

    # 3. 行首引用符 "> "
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)

    # 4. 行首列表符 "- "（含缩进子列表 "  - "）
    text = re.sub(r'^\s*-\s', '', text, flags=re.MULTILINE)

    # 5. 段落编号 [1] [1.1] [1.1.2] 等
    text = re.sub(r'^\[\d+(?:\.\d+)*\]\s*', '', text, flags=re.MULTILINE)

    # 6. 实体标注括号 → 保留内容
    text = re.sub(rf'〖{_ENTITY_PFX}([^〖〗]*)〗', r'\1', text)
    text = re.sub(r'〖[^〗]*〗', '', text)   # 剩余残留

    # 7. 六类对称括号 → 保留内容
    text = re.sub(r'〘([^〘〙]*)〙', r'\1', text)
    text = re.sub(r'〚([^〚〛]*)〛', r'\1', text)
    text = re.sub(r'《([^《》]*)》', r'\1', text)
    text = re.sub(r'〈([^〈〉]*)〉', r'\1', text)
    text = re.sub(r'【([^【】]*)】', r'\1', text)
    text = re.sub(r'〔([^〔〕]*)〕', r'\1', text)

    # 8. 粗体 **content** → content
    text = re.sub(r'\*\*([^*]*)\*\*', r'\1', text)

    # 9. Markdown 分隔线（--- 等）
    text = re.sub(r'^-{3,}\s*$', '', text, flags=re.MULTILINE)

    return text


def to_flat(text: str) -> str:
    """去除全部空白，返回单一字符序列（用于逐字比对）。"""
    return re.sub(r'\s+', '', text)


# ═══════════════════════════════════════════════════════════
# 差异分类
# ═══════════════════════════════════════════════════════════

def _ctx(flat: str, pos: int, half: int = 22) -> str:
    lo = max(0, pos - half)
    hi = min(len(flat), pos + half)
    pre = '…' if lo > 0 else ''
    suf = '…' if hi < len(flat) else ''
    return f'{pre}{flat[lo:hi]}{suf}'


def compare_texts(orig_flat: str, tagged_flat: str) -> dict:
    """
    比对两段原始平铺文本。
    策略：对比规范化版本找出实质差异，再从原始版本取上下文。

    返回 {'real': [...], 'punct': [...], 'encoding': [...]}
    每项: {tag, orig, tagged, orig_ctx, tagged_ctx}
    """
    # 1. 用规范化版本找实质差异（已消除标点/编码变体）
    orig_norm   = _norm(orig_flat)
    tagged_norm = _norm(tagged_flat)

    # 收集规范化后仍存在的差异（实质差异）的位置映射
    # 同时用 orig_flat 做上下文
    real_diffs = []

    sm_norm = difflib.SequenceMatcher(None, orig_norm, tagged_norm, autojunk=False)
    for tag, i1, i2, j1, j2 in sm_norm.get_opcodes():
        if tag == 'equal':
            continue
        orig_s   = orig_norm[i1:i2]
        tagged_s = tagged_norm[j1:j2]
        real_diffs.append({
            'tag':        tag,
            'orig':       orig_s,
            'tagged':     tagged_s,
            'orig_ctx':   _ctx(orig_norm, i1),
            'tagged_ctx': _ctx(tagged_norm, j1),
        })

    # 2. 计算标点/编码差异总数（严格比对 - 规范化比对 = 变体差异）
    sm_raw = difflib.SequenceMatcher(None, orig_flat, tagged_flat, autojunk=False)
    raw_count = sum(1 for t, *_ in sm_raw.get_opcodes() if t != 'equal')

    # PUA差异（编码）
    encoding_count = sum(
        1 for t, i1, i2, j1, j2 in
        difflib.SequenceMatcher(None, orig_flat, tagged_flat, autojunk=False).get_opcodes()
        if t != 'equal' and any(0xE000 <= ord(c) <= 0xF8FF for c in orig_flat[i1:i2])
    )

    total_variant = raw_count - len(real_diffs) - encoding_count

    return {
        'real':          real_diffs,
        'punct_count':   max(0, total_variant),
        'encoding_count': encoding_count,
    }


# ═══════════════════════════════════════════════════════════
# 章节检查
# ═══════════════════════════════════════════════════════════

def check_chapter(cid: str, orig_dir: Path, tagged_dir: Path):
    orig_files   = sorted(orig_dir.glob(f'{cid}_*.txt'))
    tagged_files = sorted(tagged_dir.glob(f'{cid}_*.tagged.md'))
    if not orig_files:
        return cid, None, '找不到原文文件'
    if not tagged_files:
        return cid, None, '找不到标注文件'

    name        = orig_files[0].stem
    orig_text   = orig_files[0].read_text('utf-8')
    # 原文第一行是章节标题（与tagged的markdown标题对应，去除后再比对）
    orig_lines  = orig_text.splitlines(keepends=True)
    if orig_lines and not orig_lines[0].strip().startswith('\u300a'):
        # 若第一行不是书名号包裹的内容，则视为标题行，跳过
        orig_text = ''.join(orig_lines[1:]) if len(orig_lines) > 1 else ''
    orig_flat   = to_flat(orig_text)
    tagged_flat = to_flat(strip_markup(tagged_files[0].read_text('utf-8')))
    result      = compare_texts(orig_flat, tagged_flat)
    return name, result, None


# ═══════════════════════════════════════════════════════════
# 报告生成
# ═══════════════════════════════════════════════════════════

_TAG_ZH = {
    'replace': '替换',
    'insert':  '插入（标注多字）',
    'delete':  '删除（标注少字）',
}

def fmt_diff(d: dict, idx: int) -> str:
    label    = _TAG_ZH.get(d['tag'], d['tag'])
    orig_s   = repr(d['orig'])   if d['orig']   else '（空）'
    tagged_s = repr(d['tagged']) if d['tagged'] else '（空）'
    return (
        f"  [{idx}] {label}\n"
        f"      原文  : {orig_s}\n"
        f"      标注  : {tagged_s}\n"
        f"      原文上下文 : {d['orig_ctx']}\n"
        f"      标注上下文 : {d['tagged_ctx']}"
    )


def _is_whitelisted(d: dict, wl_entries: list[tuple[str, str]]) -> bool:
    """检查一个差异条目是否匹配白名单"""
    for wl_orig, wl_tagged in wl_entries:
        if d['orig'] == wl_orig and d['tagged'] == wl_tagged:
            return True
    return False


def main():
    root       = Path('.')
    orig_dir   = root / 'docs' / 'original_text'
    tagged_dir = root / 'chapter_md'
    log_dir    = root / 'logs'
    log_dir.mkdir(exist_ok=True)

    whitelist = _load_whitelist(root / 'scripts' / 'lint_whitelist.txt')

    args     = sys.argv[1:]
    show_all = '--all' in args
    args     = [a for a in args if not a.startswith('--')]

    if args:
        chapter_ids = [a.zfill(3) for a in args]
    else:
        chapter_ids = [f.stem[:3] for f in sorted(orig_dir.glob('*.txt'))]

    results = []
    for cid in chapter_ids:
        name, result, err = check_chapter(cid, orig_dir, tagged_dir)
        results.append((name, result, err))
        if err:
            print(f'  {name or cid}: ⚠ {err}')
        else:
            wl_entries = whitelist.get(cid, [])
            nr_raw = len(result['real'])
            nr = sum(1 for d in result['real'] if not _is_whitelisted(d, wl_entries))
            n_wl = nr_raw - nr
            np = result['punct_count']
            ne = result['encoding_count']
            mark = '✓' if nr == 0 else '✗'
            wl_note = f'  校勘:{n_wl}' if n_wl else ''
            print(f'  {mark} {name}: {nr}处实质差异  {np}处标点  {ne}处编码{wl_note}')

    # ── 报告 ──
    ts    = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        '# 标注文本完整性检查报告',
        f'# 生成时间: {ts}',
        f'# 检查章节: {len(results)} 章',
        '',
        '分类说明:',
        '  【实质差异】= 汉字字符增/删/改，需要人工修复',
        '  【标点规范化】= 全角↔半角等价转换（，→, 等），可忽略',
        '  【编码规范化】= 原文PUA私用字符→标准Unicode，可忽略',
        '',
        '─' * 50,
    ]

    total_real = total_punct = total_enc = prob_chapters = 0

    for name, result, err in results:
        if err:
            lines += ['', f'=== {name or "?"} ===  ⚠ {err}']
            continue

        cid = name[:3]
        wl_entries = whitelist.get(cid, [])
        real_diffs = result['real']
        if wl_entries:
            whitelisted = [d for d in real_diffs if _is_whitelisted(d, wl_entries)]
            real_diffs = [d for d in real_diffs if not _is_whitelisted(d, wl_entries)]
            n_wl = len(whitelisted)
        else:
            n_wl = 0

        nr = len(real_diffs)
        np = result['punct_count']
        ne = result['encoding_count']
        total_real  += nr
        total_punct += np
        total_enc   += ne
        if nr:
            prob_chapters += 1

        if nr == 0 and not show_all:
            continue

        wl_note = f'  校勘:{n_wl}' if n_wl else ''
        lines += ['', f'=== {name} ===  实质:{nr}  标点:{np}  编码:{ne}{wl_note}']

        if nr:
            lines.append(f'  ■ 实质差异 {nr} 处：')
            for i, d in enumerate(real_diffs, 1):
                lines.append(fmt_diff(d, i))

        lines.append('')

    lines += [
        '─' * 50,
        '汇总:',
        f'  检查章节    : {len(results)} 章',
        f'  有实质差异  : {prob_chapters} 章，共 {total_real} 处  ← 需要修复',
        f'  标点规范化  : {total_punct} 处  ← 可忽略',
        f'  编码规范化  : {total_enc} 处  ← 可忽略',
        '',
        '差异类型说明:',
        '  插入（标注多字）— 标注时擅自加字，应删除多余字符',
        '  删除（标注少字）— 标注时丢失字符，应补回',
        '  替换            — 字符被改写，需核对是字形变体还是错误',
    ]

    if args:
        suffix = '_' + '_'.join(a.zfill(3) for a in args)
    else:
        suffix = ''
    out = log_dir / f'lint_text_integrity{suffix}.txt'
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(f'\n报告已保存: {out}')
    print(f'汇总: {prob_chapters}/{len(results)} 章有实质差异，共 {total_real} 处')


if __name__ == '__main__':
    main()
