#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标注补丁应用工具

读取由各推断脚本生成的建议标注 TSV，将标注符号插入 .tagged.md 文件。

TSV 格式（由各脚本生成，通用字段）：
  章节    全名    省称/词    位置    句法框架类型    匹配模式    上下文

用法：
  # 单文件（dry-run，只显示不修改）
  python scripts/apply_annotation_patches.py --file doc/analysis/patch/055_留侯世家_省称建议.tsv --dry-run

  # 单文件（实际写入）
  python scripts/apply_annotation_patches.py --file doc/analysis/patch/055_留侯世家_省称建议.tsv

  # 批量应用某目录下所有 TSV
  python scripts/apply_annotation_patches.py --dir doc/analysis/patch/ --pattern 省称建议

  # 应用别名补标 TSV
  python scripts/apply_annotation_patches.py --dir doc/analysis/patch/ --pattern 别名补标

策略：
  - 使用上下文（context 字段）定位原文中的目标词，而非依赖位置数字（行号可能偏移）
  - 上下文匹配：取 context 字段的内容，在文件中定位，找到目标词后插入标注符号
  - 同一词多次出现时，全部插入标注（与现有标注惯例一致）
  - 已标注的词（已被 @@ 等包裹）不重复处理
  - 修改后自动验证标注格式（不依赖 fix_broken_tags.py，自行校验）
"""

import re
import sys
from pathlib import Path

CHAPTER_DIR = Path('chapter_md')
PATCH_DIR   = Path('doc/analysis/patch')

# 实体类型 → 标注符号映射（v2.1 格式）
TYPE_TO_SYMBOL = {
    '人名':  ('〖@', '〗'),
    '地名':  ('〖=', '〗'),
    '官职':  ('〖;', '〗'),
    '时间':  ('〖%', '〗'),
    '朝代':  ('〖&', '〗'),
    '制度':  ('〖^', '〗'),
    '族群':  ('〖~', '〗'),
    '器物':  ('〖*', '〗'),
    '天文':  ('〖!', '〗'),
    '身份':  ('〖#', '〗'),
    '生物':  ('〖+', '〗'),
    '数量':  ('〖$', '〗'),
    '邦国':  ("〖'", '〗'),
    '神话':  ('〚', '〛'),
    '典籍':  ('《', '》'),
    '礼仪':  ('〈', '〉'),
    '刑法':  ('【', '】'),
    '思想':  ('〔', '〕'),
}

# 省称建议 TSV 中，实体类型固定为人名
ABBREV_TSV_ENTITY_TYPE = '人名'

# 已有标注的检测正则（v2.1 格式，覆盖全部17种类型）
ALL_ANNOT_RE = re.compile(
    r'〖[@=;%&\'^~\*!#\+\$][^〖〗\n]+?〗'
    r'|〚[^〛\n]+?〛'
    r'|《[^》\n]+?》'
    r'|〈[^〉\n]+?〉'
    r'|【[^】\n]+?】'
    r'|〔[^〕\n]+?〕'
)


def load_tsv(tsv_path: Path) -> list[dict]:
    """加载建议 TSV，返回 patch 列表。"""
    patches = []
    lines = tsv_path.read_text(encoding='utf-8').splitlines()
    if not lines:
        return patches
    header = lines[0].split('\t')
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) < 7:
            continue
        # 通用字段：章节 全名 省称/词 位置 框架类型 匹配模式 上下文
        patches.append({
            'chapter': parts[0],
            'full_name': parts[1],
            'word': parts[2],       # 省称 或 别名词
            'pos': int(parts[3]) if parts[3].isdigit() else 0,
            'frame_type': parts[4],
            'pattern': parts[5],
            'context': parts[6].replace('↵', '\n') if len(parts) > 6 else '',
            'entity_type': parts[7] if len(parts) > 7 else ABBREV_TSV_ENTITY_TYPE,
        })
    return patches


def is_already_tagged(text: str, start: int, word: str) -> bool:
    """检查 text[start:start+len(word)] 是否已被任意标注符号包裹。"""
    for m in ALL_ANNOT_RE.finditer(text):
        if m.start() <= start < m.end():
            return True
    return False


def apply_patch_to_text(text: str, word: str, entity_type: str,
                         context_hint: str = '', dry_run: bool = False) -> tuple[str, int]:
    """
    在 text 中找到所有未标注的 word，插入标注符号。
    优先使用 context_hint 定位，然后全文替换。
    返回 (new_text, count)。
    """
    open_sym, close_sym = TYPE_TO_SYMBOL.get(entity_type, ('@', '@'))
    tagged_word = open_sym + word + close_sym

    count = 0
    result = list(text)
    offsets = 0  # 已插入字符导致的位置偏移

    # 构建"已标注位置"集合，避免重复标注
    tagged_ranges = set()
    for m in ALL_ANNOT_RE.finditer(text):
        for i in range(m.start(), m.end()):
            tagged_ranges.add(i)

    # 查找所有未标注的 word 出现位置
    search_start = 0
    positions = []
    while True:
        idx = text.find(word, search_start)
        if idx == -1:
            break
        # 确认这些位置不在已标注区域内
        if not any(i in tagged_ranges for i in range(idx, idx + len(word))):
            positions.append(idx)
        search_start = idx + 1

    if not positions:
        return text, 0

    # 如果有上下文提示，优先找最接近 context_hint 的位置
    if context_hint and len(positions) > 1:
        # 在文本中找 context_hint 出现的位置，取最近的 word 位置
        ctx_clean = re.sub(r'[░\n\r]', '', context_hint)[:20]
        ctx_pos = text.find(ctx_clean)
        if ctx_pos >= 0:
            positions.sort(key=lambda p: abs(p - ctx_pos))

    if dry_run:
        for p in positions:
            ctx_s = max(0, p - 8)
            ctx_e = min(len(text), p + len(word) + 8)
            ctx = text[ctx_s:ctx_e].replace('\n', '↵')
            print(f'    [DRY-RUN] 将在位置 {p} 插入 {tagged_word}  ctx=「{ctx}」')
        return text, len(positions)

    # 从后往前替换，避免位置偏移问题
    positions_rev = sorted(positions, reverse=True)
    text_list = list(text)
    for p in positions_rev:
        text_list[p:p + len(word)] = list(open_sym + word + close_sym)
        count += 1

    return ''.join(text_list), count


def apply_tsv_to_chapter(tsv_path: Path, dry_run: bool = False) -> dict:
    """
    将一个 TSV 文件中的所有建议应用到对应的 .tagged.md 文件。
    返回统计信息。
    """
    patches = load_tsv(tsv_path)
    if not patches:
        return {'tsv': tsv_path.name, 'patches': 0, 'applied': 0}

    # 按章节分组
    by_chapter: dict[str, list] = {}
    for p in patches:
        chapter = p['chapter']
        by_chapter.setdefault(chapter, []).append(p)

    total_applied = 0
    for chapter, chapter_patches in by_chapter.items():
        fpath = CHAPTER_DIR / f'{chapter}.tagged.md'
        if not fpath.exists():
            print(f'  [WARN] 章节文件不存在：{fpath}')
            continue

        text = fpath.read_text(encoding='utf-8')
        original_text = text
        chapter_count = 0

        # 按词分组，避免同一词多次处理
        words_seen = set()
        for patch in chapter_patches:
            word = patch['word']
            entity_type = patch.get('entity_type', ABBREV_TSV_ENTITY_TYPE)
            context_hint = patch.get('context', '')

            if word in words_seen:
                continue
            words_seen.add(word)

            new_text, cnt = apply_patch_to_text(
                text, word, entity_type, context_hint, dry_run=dry_run
            )
            if cnt > 0:
                text = new_text
                chapter_count += cnt
                if not dry_run:
                    print(f'    ✓ {chapter}: @{word}@ 插入 {cnt} 处')

        if not dry_run and text != original_text:
            fpath.write_text(text, encoding='utf-8')
            total_applied += chapter_count

    return {'tsv': tsv_path.name, 'patches': len(patches), 'applied': total_applied}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='标注补丁应用工具')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', help='应用单个 TSV 文件')
    group.add_argument('--dir', help='批量应用目录下的 TSV 文件')
    parser.add_argument('--pattern', default='',
                        help='与 --dir 配合，只处理文件名含此字符串的 TSV')
    parser.add_argument('--dry-run', action='store_true',
                        help='只显示将要做的修改，不实际写入')
    args = parser.parse_args()

    if args.dry_run:
        print('[DRY-RUN 模式，不写入任何文件]')

    if args.file:
        tsv_path = Path(args.file)
        if not tsv_path.exists():
            print(f'[ERROR] 文件不存在：{tsv_path}')
            sys.exit(1)
        result = apply_tsv_to_chapter(tsv_path, dry_run=args.dry_run)
        print(f'\n{result["tsv"]}: {result["patches"]} 条建议, 实际插入 {result["applied"]} 处')

    elif args.dir:
        patch_dir = Path(args.dir)
        tsv_files = sorted(patch_dir.glob('*.tsv'))
        if args.pattern:
            tsv_files = [f for f in tsv_files if args.pattern in f.name]
        if not tsv_files:
            print(f'[WARN] 未找到匹配的 TSV 文件')
            sys.exit(0)

        print(f'找到 {len(tsv_files)} 个 TSV 文件...')
        total = 0
        for tsv in tsv_files:
            result = apply_tsv_to_chapter(tsv, dry_run=args.dry_run)
            if result['applied'] > 0 or args.dry_run:
                print(f'  {result["tsv"]}: 插入 {result["applied"]} 处')
            total += result['applied']
        print(f'\n✅ 合计插入 {total} 处标注')


if __name__ == '__main__':
    main()
