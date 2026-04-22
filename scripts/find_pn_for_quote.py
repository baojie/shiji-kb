#!/usr/bin/env python3
"""
引文 PN 查找工具

用途：给定一段引文，在全部 130 篇 tagged.md 去标注后的纯文本中做模糊匹配，
      返回最可能的 PN（章节编号 + 段落号）。

使用方法：
    python scripts/find_pn_for_quote.py "欲以求旷日长久"
    python scripts/find_pn_for_quote.py "欲以求旷日长久" --top 10
    python scripts/find_pn_for_quote.py --rebuild    # 强制重建索引

索引缓存：data/pn_text_index.pkl（当 chapter_md 文件更新时自动重建）
"""

import re
import sys
import pickle
import argparse
from pathlib import Path
from difflib import SequenceMatcher

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from config import BASE_COPY, DATA_ROOT
from semantic_tags import strip_markup

CACHE_PATH = DATA_ROOT / 'pn_text_index.pkl'

# 段落分割 regex：匹配行首 [N]、[N.M]、[N.M.K]
_PN_SPLIT = re.compile(
    r'^\[([\d.]+)\]\s*(.*?)(?=^\[[\d.]+\]|^##|^---|\Z)',
    re.MULTILINE | re.DOTALL,
)

# 用于清洗匹配文本：去除标点和空白
# 覆盖：ASCII标点、全角标点、引号（全角/半角）、空白
_PUNCT = re.compile(
    r'[\s\t\n\r'
    r'，。、；：！？'   # ，。、；：！？ (全角)
    r'「」『』【】〔〕'   # 「」『』【】〔〕
    r'《》〈〉'   # 《》〈〉
    r'“”‘’'   # "" ''
    r'·‧…—―∼'   # ·‧…—―～
    r'　'   # 全角空格
    r',.;:!?()\[\]{}/\\\'"@#%&*+=<>|^`~-]'
)


def _clean(text: str) -> str:
    """去除标点和空白，用于纯文字匹配。"""
    return _PUNCT.sub('', text)


def _index_cache_stale(cache_path: Path, chapter_dir: Path) -> bool:
    """检查缓存是否比最新章节文件更旧。"""
    if not cache_path.exists():
        return True
    cache_mtime = cache_path.stat().st_mtime
    for f in chapter_dir.glob('*.tagged.md'):
        if f.stat().st_mtime > cache_mtime:
            return True
    return False


def build_index(chapter_dir: Path = BASE_COPY) -> list:
    """
    扫描全部 tagged.md，去除语义标注，按 PN 切段，建立索引。

    索引项结构：
        chapter_num   : str   "001"
        chapter_title : str   "五帝本纪"
        pn            : str   "4.1"
        text_raw      : str   去标注后的段落原文（含标点）
        text_clean    : str   进一步去标点空白后的文字，用于匹配
    """
    index = []
    files = sorted(chapter_dir.glob('*.tagged.md'))
    print(f'[find_pn_for_quote] 扫描 {len(files)} 个章节文件...', file=sys.stderr)

    for fpath in files:
        m = re.match(r'(\d+)_(.+)\.tagged\.md', fpath.name)
        if not m:
            continue
        chapter_num = m.group(1)
        chapter_title = m.group(2)
        content = fpath.read_text(encoding='utf-8')

        for seg in _PN_SPLIT.finditer(content):
            pn = seg.group(1)
            # 对段落文本（不含行首 PN 前缀）做去标注
            raw_para = seg.group(2).strip()
            if not raw_para:
                continue
            stripped = strip_markup(raw_para)
            # 合并多行空白
            stripped = re.sub(r'\n+', ' ', stripped).strip()
            clean = _clean(stripped)
            if len(clean) < 4:
                continue
            index.append({
                'chapter_num': chapter_num,
                'chapter_title': chapter_title,
                'pn': pn,
                'text_raw': stripped,
                'text_clean': clean,
            })

    print(f'[find_pn_for_quote] 索引完成：{len(index)} 个段落', file=sys.stderr)
    return index


def load_index(force_rebuild: bool = False) -> list:
    """从缓存加载索引，必要时自动重建。"""
    if not force_rebuild and not _index_cache_stale(CACHE_PATH, BASE_COPY):
        with open(CACHE_PATH, 'rb') as f:
            return pickle.load(f)

    idx = build_index()
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, 'wb') as f:
        pickle.dump(idx, f)
    print(f'[find_pn_for_quote] 缓存已保存到 {CACHE_PATH}', file=sys.stderr)
    return idx


def find_pn(query: str, index: list, top_n: int = 5) -> list:
    """
    在索引中查找与 query 最匹配的段落，返回 [(score, entry), ...] 降序列表。

    匹配策略（优先级递减）：
      1. 精确子串：clean_query 包含于 clean_para            → score = 1.0
      2. 反向子串：clean_para 包含于 clean_query（query更长）→ score = len(para)/len(query)
      3. SequenceMatcher 模糊比（threshold = 0.55）
    """
    query_stripped = strip_markup(query)
    query_clean = _clean(query_stripped)

    if not query_clean:
        return []

    results = []

    for entry in index:
        para_clean = entry['text_clean']

        # 策略 1：精确子串
        if query_clean in para_clean:
            results.append((1.0, entry))
            continue

        # 策略 2：反向子串（query 覆盖整段，例如查整段文字）
        if para_clean and para_clean in query_clean:
            score = len(para_clean) / len(query_clean)
            if score >= 0.4:
                results.append((score, entry))
            continue

        # 策略 3：SequenceMatcher（仅在 query 有足够长度时）
        if len(query_clean) >= 6:
            ratio = SequenceMatcher(
                None, query_clean, para_clean, autojunk=False
            ).ratio()
            if ratio >= 0.55:
                results.append((ratio, entry))

    results.sort(key=lambda x: -x[0])
    return results[:top_n]


def format_result(rank: int, score: float, entry: dict) -> str:
    preview = entry['text_raw']
    if len(preview) > 80:
        preview = preview[:80] + '…'
    return (
        f"  {rank}. [{score:.3f}] "
        f"{entry['chapter_num']}_{entry['chapter_title']} "
        f"§{entry['pn']}\n"
        f"       {preview}"
    )


def main():
    parser = argparse.ArgumentParser(description='在《史记》全文中查找引文对应的 PN')
    parser.add_argument('query', nargs='?', help='待查引文')
    parser.add_argument('--top', type=int, default=5, help='返回最多 N 个结果（默认 5）')
    parser.add_argument('--rebuild', action='store_true', help='强制重建索引缓存')
    parser.add_argument('--json', action='store_true', help='以 JSON 格式输出')
    args = parser.parse_args()

    if args.rebuild and not args.query:
        load_index(force_rebuild=True)
        return

    if not args.query:
        parser.print_help()
        sys.exit(1)

    index = load_index(force_rebuild=args.rebuild)
    results = find_pn(args.query, index, top_n=args.top)

    if args.json:
        import json as _json
        out = [
            {
                'rank': i + 1,
                'score': round(score, 4),
                'chapter_num': e['chapter_num'],
                'chapter_title': e['chapter_title'],
                'pn': e['pn'],
                'text_preview': e['text_raw'][:120],
            }
            for i, (score, e) in enumerate(results)
        ]
        print(_json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if not results:
            print(f'未找到匹配：{args.query}')
        else:
            print(f'查询：{args.query}')
            print(f'共找到 {len(results)} 个匹配：')
            for i, (score, entry) in enumerate(results):
                print(format_result(i + 1, score, entry))


if __name__ == '__main__':
    main()
