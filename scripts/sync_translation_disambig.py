#!/usr/bin/env python3
"""
白话翻译消歧同步与审核脚本

目的：让 doc/translation/*_白话.md 的实体消歧保持与原始标注 chapter_md/*.tagged.md 一致。

规范（详见 SKILL_01h §消歧语法）：
- 原文标注 〖@籍|项籍〗：显示名=籍，规范名=项籍
- 白话译文应继承"规范名"（`|` 右侧），surface（`|` 左侧）可随白话改写
- 如原文未消歧，白话也不擅自添加

本脚本做两件事：
1. **审核**：扫描每章，找出译文中"规范名与原文不一致"或"原文消歧但译文未继承"的问题
2. **同步**（可选 --apply）：自动将原文的 (marker, 规范名) 对应用到译文中匹配的实体

使用：
    python scripts/sync_translation_disambig.py 002               # 审核 002
    python scripts/sync_translation_disambig.py --all             # 审核全部
    python scripts/sync_translation_disambig.py 002 --apply       # 审核并自动同步
    python scripts/sync_translation_disambig.py --all --apply

演化机制：当原文 .tagged.md 新增消歧（如 〖@籍〗 → 〖@籍|项籍〗），
运行 `--apply` 可自动把所有译文中引用了"项籍"或"籍"的同类实体补齐 `|项籍`。
"""

import sys
import re
import argparse
from pathlib import Path
from collections import defaultdict

# 实体标注的18类 marker
ENTITY_MARKERS = '@=;%&◆^~•!?+#$\\{:\\[_'
ENTITY_PATTERN = re.compile(rf'〖([{ENTITY_MARKERS}])\s*([^〖〗|]+)(?:\|([^〖〗]+))?〗')


def extract_entities(text: str):
    """
    提取文本中所有实体标注。

    返回：[(marker, surface, canonical_or_None), ...] 按出现顺序。
    """
    results = []
    for m in ENTITY_PATTERN.finditer(text):
        marker = m.group(1)
        surface = m.group(2).strip()
        canonical = m.group(3).strip() if m.group(3) else None
        results.append((marker, surface, canonical, m.start(), m.end()))
    return results


def parse_pn_segments(text: str, header_pattern: str):
    """
    将文本按 PN 标题切分。

    参数：
        text: 文本
        header_pattern: PN 标题的正则（要包含一个 (PN) 捕获组）

    返回：dict {pn: segment_text}
    """
    segments = {}
    # 找到所有标题位置
    matches = list(re.finditer(header_pattern, text, re.MULTILINE))
    for i, m in enumerate(matches):
        pn = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segments[pn] = text[start:end]
    return segments


def load_source_segments(src_path: Path):
    """解析 tagged.md：每 [PN] 之后到下个 [PN] 或末尾为一段。"""
    text = src_path.read_text()
    # 源文件格式 `[1]`、`[1.1]` 行首或行中
    return parse_pn_segments(text, r'\[(\d+(?:\.\d+)?)\]')


def load_translation_segments(tgt_path: Path):
    """解析白话译文：每 `## [PN] 标题` 之后到下个 `##` 或末尾为一段。"""
    text = tgt_path.read_text()
    return parse_pn_segments(text, r'^## \[(\d+(?:\.\d+)?)\][^\n]*$')


def build_canonical_map(src_path: Path):
    """
    从源文件构建"规范映射"：每类 marker 下，已知的 (surface, canonical) 配对。

    返回：
        { marker: { surface: canonical } }
        另返回已知规范名集合：{ marker: set(canonical) }
    """
    text = src_path.read_text()
    surface_to_canonical = defaultdict(dict)  # {marker: {surface: canonical}}
    canonicals = defaultdict(set)             # {marker: {canonical}}
    for marker, surface, canonical, _, _ in extract_entities(text):
        if canonical:
            surface_to_canonical[marker][surface] = canonical
            canonicals[marker].add(canonical)
    return surface_to_canonical, canonicals


def audit_chapter(chapter_num: str, apply: bool = False):
    """
    审核单章译文消歧一致性。

    返回：{
        'issues': [(pn, message), ...],
        'fixed': int,     # 如果 apply=True，实际修正了多少处
    }
    """
    src_path = next(Path('chapter_md').glob(f'{chapter_num}_*.tagged.md'), None)
    tgt_path = next(Path('doc/translation').glob(f'{chapter_num}_*_白话.md'), None)
    if not src_path or not tgt_path:
        return {'issues': [(None, f'缺失文件: src={src_path} tgt={tgt_path}')], 'fixed': 0}

    surface_to_canonical, canonicals = build_canonical_map(src_path)
    src_segs = load_source_segments(src_path)
    tgt_segs = load_translation_segments(tgt_path)

    issues = []
    fixed = 0
    new_content = tgt_path.read_text()

    for pn, tgt_seg in tgt_segs.items():
        tgt_entities = extract_entities(tgt_seg)
        for marker, surface, canonical, _, _ in tgt_entities:
            # Case A: 译文已消歧 〖T surface|canonical〗
            if canonical:
                # 规范名若未出现在源文件规范池中 → 警告
                if canonical not in canonicals.get(marker, set()):
                    issues.append((pn, f'未知规范名: 〖{marker}{surface}|{canonical}〗（marker {marker} 在源中无此规范名）'))
            # Case B: 译文未消歧 〖T surface〗
            else:
                # 如果 surface 是一个已知 surface 映射，自动补齐 canonical
                known = surface_to_canonical.get(marker, {}).get(surface)
                if known and known != surface:
                    issues.append((pn, f'建议消歧: 〖{marker}{surface}〗 → 〖{marker}{surface}|{known}〗'))
                    if apply:
                        # 仅替换 *当前 PN 段* 中的第一个匹配，避免误替
                        old = f'〖{marker}{surface}〗'
                        new = f'〖{marker}{surface}|{known}〗'
                        # 全文替换（因为标注应前后一致）
                        count = new_content.count(old)
                        if count > 0:
                            new_content = new_content.replace(old, new)
                            fixed += count

    if apply and fixed > 0:
        tgt_path.write_text(new_content)

    return {'issues': issues, 'fixed': fixed, 'src': src_path.name, 'tgt': tgt_path.name}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('chapters', nargs='*', help='章节号（如 002），或 --all')
    ap.add_argument('--all', action='store_true', help='处理所有章节')
    ap.add_argument('--apply', action='store_true', help='实际写入修正（默认只审核）')
    ap.add_argument('--quiet', action='store_true', help='只打印有问题的章节')
    args = ap.parse_args()

    if args.all:
        chapters = sorted({f.name[:3] for f in Path('doc/translation').glob('*_白话.md')})
    else:
        chapters = [c.zfill(3) for c in args.chapters]

    if not chapters:
        ap.print_help()
        sys.exit(1)

    total_issues = 0
    total_fixed = 0
    for ch in chapters:
        r = audit_chapter(ch, apply=args.apply)
        n = len(r['issues'])
        total_issues += n
        total_fixed += r.get('fixed', 0)
        if args.quiet and n == 0:
            continue
        print(f'=== 第 {ch} 章 ===')
        if n == 0:
            print('  ✓ 一致')
        else:
            for pn, msg in r['issues'][:30]:
                print(f'  [{pn or "-"}] {msg}')
            if n > 30:
                print(f'  ... 另有 {n - 30} 条')
        if args.apply and r.get('fixed'):
            print(f'  → 自动修正 {r["fixed"]} 处')

    print(f'\n汇总：{len(chapters)} 章，总问题 {total_issues} 条，{"修正 " + str(total_fixed) + " 处" if args.apply else "未写入（加 --apply 执行修正）"}')


if __name__ == '__main__':
    main()
