#!/usr/bin/env python3
"""
质控函数：验证标注后的 tagged.md 文件没有改动原始文本内容

核心逻辑：去除所有实体标记符号后，所得纯文本必须与原始 .txt 文件逐字相同。
这确保标注操作仅添加标记，不增删改任何原文字符。

支持的标记格式（v2.5，18类实体）：
  〖@ = ; # % & ' ^ ~ * ! + $〗  — 13种〖TYPE content〗格式
  〚神话〛 《典籍》 〈礼仪〉 【刑法】 〔思想〕 — 5种CJK括号格式
  〘生物〙 — 旧格式（已迁移为〖+〗，保留兼容）

用法：
  python validate_tagging.py                     # 验证005章（默认）
  python validate_tagging.py --chapter 001       # 验证指定章节
  python validate_tagging.py --all               # 批量验证全部130章
  python validate_tagging.py --all --stop-on-error  # 遇错即停
"""

import re
import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHAPTER_DIR = BASE_DIR / 'chapter_md'
ORIGINAL_DIR = BASE_DIR / 'archive' / 'chapter_numbered'


def remove_all_tags(text):
    """去除所有语义标签和编号，还原纯文本"""
    # 去除 markdown 标题行（二/三/四级标题是标注时新增的语义标题，原文无）
    text = re.sub(r'^#{2,4}\s+.*$', '', text, flags=re.MULTILINE)
    # 一级标题保留文字（对应原文的章节标题如"五帝本纪"）
    # 去掉 # 前缀，以及可能的章节编号前缀如 "# 033_" 或 "# 033 "
    text = re.sub(r'^#\s+(?:\d{3}[_ ]\s*)?', '', text, flags=re.MULTILINE)

    # 去除段落编号 [1], [1.1], [1.1.2] 等（须在标题去除之后，因 # [0] 标题 → [0] 标题）
    text = re.sub(r'^\[\d+(?:\.\d+)*\]\s*', '', text, flags=re.MULTILINE)
    # 去除列表项前缀 "- [1.1]" 或单独的 "- " 格式
    text = re.sub(r'^-\s+\[\d+(?:\.\d+)*\]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^-\s+', '', text, flags=re.MULTILINE)

    # 去除引用块标记、分割线、fenced div
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)  # 分割线（须在列表项之前）
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^:::.*$', '', text, flags=re.MULTILINE)

    # 去除动词标注符号（v3.0新增）
    # ⟦TYPE动词⟧ 格式（4种类型：◈◉○◇），支持内联消歧 ⟦TYPE动词|消歧说明⟧
    text = re.sub(r'⟦[◈◉○◇]([^⟦⟧\n|]+?)(?:\|[^⟦⟧\n]*)?⟧', r'\1', text)

    # 去除18种〖TYPE content〗格式的标记符号（保留content）
    # 类型标记字符: @ = ; # % & ' ^ ~ • ! + $ ? { : [ _
    text = re.sub(r'〖[@=;#%&\'^~•!\+\$\?\{:\[_]([^〖〗\n|]+?)(?:\|[^〖〗\n]*)?〗', r'\1', text)
    # 兜底：去除无类型前缀的〖content〗（早期不规范标注遗留，可能含逗号等）
    text = re.sub(r'〖([^〖〗\n]+)〗', r'\1', text)
    # 清理可能残留的空〖〗对和单独的〖〗字符
    text = text.replace('〖〗', '')
    text = text.replace('〖', '').replace('〗', '')
    # 清理可能残留的动词标注符号
    text = text.replace('⟦', '').replace('⟧', '')

    # 去除旧格式括号（兼容）
    text = re.sub(r'〘([^〘〙\n]+)〙', r'\1', text)   # 生物（旧格式，兼容）

    return text.strip()


def normalize_text(text):
    """标准化文本，用于比较：去除所有空白"""
    text = re.sub(r'\s+', '', text)
    return text


def validate_chapter(md_path, txt_path, verbose=False):
    """验证章节标注的正确性：去标记后与原文逐字比对"""
    with open(txt_path, 'r', encoding='utf-8') as f:
        original_text = f.read()

    with open(md_path, 'r', encoding='utf-8') as f:
        tagged_text = f.read()

    # 去除标记，还原纯文本
    stripped = remove_all_tags(tagged_text)
    clean_original = remove_all_tags(original_text)

    # 标准化后比较
    norm_stripped = normalize_text(stripped)
    norm_original = normalize_text(clean_original)

    if norm_stripped == norm_original:
        if verbose:
            print(f"  ✅ {md_path.name}")
        return True, []

    # 找出差异位置
    errors = []
    min_len = min(len(norm_stripped), len(norm_original))

    diff_positions = []
    for i in range(min_len):
        if norm_stripped[i] != norm_original[i]:
            diff_positions.append(i)
            if len(diff_positions) >= 10:
                break

    if len(norm_stripped) != len(norm_original):
        errors.append(f"长度不同: 标注去标记后={len(norm_stripped)}, 原文={len(norm_original)} (差{len(norm_stripped)-len(norm_original)}字)")

    for pos in diff_positions[:5]:
        ctx_start = max(0, pos - 10)
        ctx_end = min(min_len, pos + 10)
        errors.append(
            f"位置{pos}: 标注='{norm_stripped[ctx_start:ctx_end]}' "
            f"原文='{norm_original[ctx_start:ctx_end]}'"
        )

    if verbose:
        print(f"  ❌ {md_path.name}: {len(errors)} 处差异")
        for err in errors:
            print(f"     {err}")

    return False, errors


def find_chapter_pair(chapter_num):
    """查找章节的 tagged.md 和原文 .txt 文件对"""
    md_files = list(CHAPTER_DIR.glob(f'{chapter_num:03d}_*.tagged.md'))
    txt_files = list(ORIGINAL_DIR.glob(f'{chapter_num:03d}_*.txt'))

    if not md_files:
        return None, None, f"未找到 tagged.md: {chapter_num:03d}"
    if not txt_files:
        return None, None, f"未找到原文 txt: {chapter_num:03d}"

    return md_files[0], txt_files[0], None


def main():
    parser = argparse.ArgumentParser(description='验证标注文件未改动原文')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--chapter', type=int, metavar='NNN',
                       help='验证指定章节（如 001）')
    group.add_argument('--all', action='store_true',
                       help='批量验证全部章节')
    parser.add_argument('--stop-on-error', action='store_true',
                        help='遇到第一个错误即停止')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='显示详细信息')

    args = parser.parse_args()

    if args.all:
        # 批量验证全部章节
        passed = 0
        failed = 0
        skipped = 0

        for chapter_num in range(1, 131):
            md_path, txt_path, err = find_chapter_pair(chapter_num)
            if err:
                skipped += 1
                if args.verbose:
                    print(f"  ⏭ {chapter_num:03d}: {err}")
                continue

            ok, errors = validate_chapter(md_path, txt_path, verbose=args.verbose)
            if ok:
                passed += 1
            else:
                failed += 1
                if not args.verbose:
                    print(f"  ❌ {md_path.name}: {errors[0] if errors else '未知差异'}")
                if args.stop_on_error:
                    print(f"\n停止：已验证 {passed + failed} 章，{failed} 章有差异")
                    sys.exit(1)

        print(f"\n验证完成: {passed} 通过, {failed} 失败, {skipped} 跳过")
        sys.exit(1 if failed > 0 else 0)

    else:
        # 单章验证
        chapter_num = args.chapter or 5
        md_path, txt_path, err = find_chapter_pair(chapter_num)
        if err:
            print(f"错误: {err}")
            sys.exit(1)

        ok, errors = validate_chapter(md_path, txt_path, verbose=True)
        if ok:
            print(f"\n✅ 验证成功：标注未改动原文")
        else:
            print(f"\n❌ 验证失败：存在 {len(errors)} 处差异")
            for e in errors:
                print(f"  {e}")

        sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
