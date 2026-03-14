#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint_text_integrity.py — 标注文本完整性检查

去除所有语义标注符号后，与 docs/original_text/ 中的原文比对，
逐一列出不一致，并保存到 logs/lint_text_integrity.txt。

用法:
    python scripts/lint_text_integrity.py              # 检查全部130章
    python scripts/lint_text_integrity.py 033 034      # 检查指定章节
    python scripts/lint_text_integrity.py --all-punct  # 也列出标点差异

差异分类:
    【实质差异】汉字字符被增加/删除/替换（需要修复）
    【标点差异】全角标点→半角标点的系统性转换（通常为标注规范，可忽略）
"""

import re
import sys
import difflib
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────
# 全角↔半角等价标点对（视为"标点差异"，不作为实质错误）
# ──────────────────────────────────────────────
_PAIRS = [
    ('，', ','), ('。', '.'), ('；', ';'), ('：', ':'),
    ('！', '!'), ('？', '?'), ('（', '('), ('）', ')'),
    ('"', '"'), ('"', '"'), (''', "'"), (''', "'"),
    ('「', '"'), ('」', '"'), ('『', '"'), ('』', '"'),
    ('——', '--'), ('…', '...'), ('·', '·'),
    # 同形异码变体
    ('巿', '市'),   # U+5DFF vs U+5E02（市字不同字形）
]
PUNCT_TRIVIAL: set[tuple[str, str]] = set()
for a, b in _PAIRS:
    PUNCT_TRIVIAL.add((a, b))
    PUNCT_TRIVIAL.add((b, a))
    PUNCT_TRIVIAL.add((a, a))
    PUNCT_TRIVIAL.add((b, b))

# 实体标注类型字符前缀
ENTITY_PREFIXES = r'[#@=;$%&^\~*!\'+]'


def strip_markup(text: str) -> str:
    """去除全部语义标注符号，保留实体内容本身。"""

    # 1. Markdown 标题行（不在原文中）：# / ## / ###
    text = re.sub(r'^#{1,6}.*$', '', text, flags=re.MULTILINE)

    # 2. ::: 围栏块标记行
    text = re.sub(r'^:::.*$', '', text, flags=re.MULTILINE)

    # 3. 行首引用符 "> "
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)

    # 4. 行首列表符 "- "（仅行首单横杠+空格）
    text = re.sub(r'^-\s', '', text, flags=re.MULTILINE)

    # 5. 段落编号 "[1]" "[1.1]" 等（行首）
    text = re.sub(r'^\[\d+(?:\.\d+)*\]\s*', '', text, flags=re.MULTILINE)

    # 6. 实体标注括号，保留内容：〖TYPE content〗 → content
    text = re.sub(rf'〖{ENTITY_PREFIXES}([^〖〗]*)〗', r'\1', text)
    # 剩余未识别 〖...〗
    text = re.sub(r'〖[^〗]*〗', '', text)

    # 7. 六类对称括号，保留内容
    text = re.sub(r'〘([^〘〙]*)〙', r'\1', text)
    text = re.sub(r'〚([^〚〛]*)〛', r'\1', text)
    text = re.sub(r'《([^《》]*)》', r'\1', text)
    text = re.sub(r'〈([^〈〉]*)〉', r'\1', text)
    text = re.sub(r'【([^【】]*)】', r'\1', text)
    text = re.sub(r'〔([^〔〕]*)〕', r'\1', text)

    # 8. 粗体 **content** → content
    text = re.sub(r'\*\*([^*]*)\*\*', r'\1', text)

    return text


def to_flat(text: str) -> str:
    """压平为无空白字符序列（用于逐字比对）。"""
    return re.sub(r'\s+', '', text)


def context(flat: str, pos: int, half: int = 20) -> str:
    lo = max(0, pos - half)
    hi = min(len(flat), pos + half)
    pre = '…' if lo > 0 else ''
    suf = '…' if hi < len(flat) else ''
    return f'{pre}{flat[lo:hi]}{suf}'


def is_punct_diff(orig: str, tagged: str) -> bool:
    """判断差异是否属于纯标点规范化（可忽略）。"""
    return (orig, tagged) in PUNCT_TRIVIAL


def compare_texts(orig_flat: str, tagged_flat: str) -> tuple[list, list]:
    """
    比对两段平铺文本，返回 (实质差异列表, 标点差异列表)。
    """
    sm = difflib.SequenceMatcher(None, orig_flat, tagged_flat, autojunk=False)
    real, punct = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        d = {
            'tag':        tag,
            'orig':       orig_flat[i1:i2],
            'tagged':     tagged_flat[j1:j2],
            'orig_ctx':   context(orig_flat, i1),
            'tagged_ctx': context(tagged_flat, j1),
        }
        if is_punct_diff(d['orig'], d['tagged']):
            punct.append(d)
        else:
            real.append(d)
    return real, punct


TAG_ZH = {'replace': '替换', 'insert': '插入（标注多字）', 'delete': '删除（标注少字）'}


def fmt_diff(d: dict, idx: int) -> str:
    label = TAG_ZH.get(d['tag'], d['tag'])
    orig_s   = repr(d['orig'])   if d['orig']   else '（无）'
    tagged_s = repr(d['tagged']) if d['tagged'] else '（无）'
    return (
        f"  [{idx}] {label}\n"
        f"      原文  : {orig_s}\n"
        f"      标注  : {tagged_s}\n"
        f"      原文上下文: {d['orig_ctx']}\n"
        f"      标注上下文: {d['tagged_ctx']}"
    )


def check_chapter(cid: str, orig_dir: Path, tagged_dir: Path):
    orig_files   = sorted(orig_dir.glob(f'{cid}_*.txt'))
    tagged_files = sorted(tagged_dir.glob(f'{cid}_*.tagged.md'))
    if not orig_files:
        return cid, [], [], '找不到原文文件'
    if not tagged_files:
        return cid, [], [], '找不到标注文件'

    name = orig_files[0].stem
    orig_flat   = to_flat(orig_files[0].read_text('utf-8'))
    tagged_flat = to_flat(strip_markup(tagged_files[0].read_text('utf-8')))
    real, punct = compare_texts(orig_flat, tagged_flat)
    return name, real, punct, None


def main():
    root       = Path('.')
    orig_dir   = root / 'docs' / 'original_text'
    tagged_dir = root / 'chapter_md'
    log_dir    = root / 'logs'
    log_dir.mkdir(exist_ok=True)

    args = sys.argv[1:]
    show_punct = '--all-punct' in args
    args = [a for a in args if not a.startswith('--')]

    if args:
        chapter_ids = [a.zfill(3) for a in args]
    else:
        chapter_ids = [f.stem[:3] for f in sorted(orig_dir.glob('*.txt'))]

    results = []
    for cid in chapter_ids:
        name, real, punct, err = check_chapter(cid, orig_dir, tagged_dir)
        results.append((name, real, punct, err))
        if err:
            print(f'  {name}: ⚠ {err}')
        elif real:
            print(f'  {name}: {len(real)}处实质差异  {len(punct)}处标点规范化')
        else:
            print(f'  {name}: ✓  {len(punct)}处标点规范化')

    # ── 生成报告 ──
    ts    = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        '# 标注文本完整性检查报告',
        f'# 生成时间: {ts}',
        f'# 检查章节数: {len(results)}',
        '',
        '说明：',
        '  【实质差异】= 汉字字符被增加/删除/替换，需要修复',
        '  【标点差异】= 全角↔半角等价转换（，→, 等），通常为标注规范，可忽略',
        '',
    ]

    total_real = total_punct = prob = 0

    for name, real, punct, err in results:
        if err:
            lines.append(f'=== {name} ===  ⚠ {err}')
            continue
        if not real and not show_punct:
            continue   # 仅标点差异时跳过（除非 --all-punct）

        prob += 1 if real else 0
        total_real  += len(real)
        total_punct += len(punct)

        lines.append('')
        lines.append(f'=== {name} ===')
        if real:
            lines.append(f'  ■ 实质差异 {len(real)} 处：')
            for i, d in enumerate(real, 1):
                lines.append(fmt_diff(d, i))
        if show_punct and punct:
            lines.append(f'  □ 标点差异 {len(punct)} 处（仅列前20）：')
            for i, d in enumerate(punct[:20], 1):
                lines.append(fmt_diff(d, i))
        lines.append('')

    lines += [
        '────────────────────────────────────────',
        f'汇总：',
        f'  检查章节: {len(results)} 章',
        f'  有实质差异: {prob} 章，共 {total_real} 处',
        f'  标点规范化: {total_punct} 处（全角↔半角，通常可忽略）',
        '',
        '差异类型：',
        '  插入（标注多字）— 标注时擅自加字，需删除',
        '  删除（标注少字）— 标注时丢字，需补回',
        '  替换           — 原文字符被改写，需核对',
    ]

    out = log_dir / 'lint_text_integrity.txt'
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(f'\n报告已保存：{out}')
    print(f'汇总：{prob}/{len(results)} 章有实质差异，共 {total_real} 处；标点规范化 {total_punct} 处')


if __name__ == '__main__':
    main()
