#!/usr/bin/env python3
"""
build_coverage_map.py — W13 覆盖映射构建脚本

读取 sentence_index/XXX.jsonl，对每个句子判断覆盖类型，
输出到 coverage_map/XXX.jsonl

覆盖类型（优先级从高到低）：
  quote   - wiki 页面正文含 ≥10 字原文子串
  para    - wiki 页面 pn 字段引用了该句段落
  entity  - 句中含实体名，且该实体页链接到本章
  gap     - 以上全无

用法：
  python3 wiki/scripts/butler/build_coverage_map.py           # 全量
  python3 wiki/scripts/butler/build_coverage_map.py 001       # 单章
  python3 wiki/scripts/butler/build_coverage_map.py --report  # 输出汇总统计
"""

import re
import sys
import json
import glob
from pathlib import Path
from datetime import date
from collections import defaultdict

SENTENCE_DIR = Path("wiki/logs/butler/sentence_index")
OUT_DIR = Path("wiki/logs/butler/coverage_map")
HISTORY_DIR = Path("wiki/public/history")
PAGES_JSON = Path("wiki/pages.json")
SUMMARY_FILE = Path("wiki/logs/butler/coverage_summary.json")

TODAY = date.today().isoformat()
QUOTE_MIN_LEN = 10   # 引文匹配最少字数


# ─── 索引构建 ──────────────────────────────────────────────────────────────

def strip_md(text: str) -> str:
    """粗略去除 Markdown 格式，保留汉字和标点。"""
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'\[\[([^\]|]+)\|?[^\]]*\]\]', r'\1', text)  # [[链接|文字]] → 文字
    text = re.sub(r'\*+([^*]+)\*+', r'\1', text)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    return text


def load_pages() -> dict:
    """从 pages.json 加载页面元数据（id, type, aliases）。"""
    data = json.loads(PAGES_JSON.read_text(encoding="utf-8"))
    return data.get("pages", {})


def build_indices(pages_meta: dict) -> tuple[dict, dict, dict, dict]:
    """
    扫描所有 wiki/public/history/*.json，构建四个索引：

    pn_index:     {(chapter_num_str, para_id) → [page_id, ...]}
    entity_index: {entity_name → [page_id, ...]}  （id + aliases，≥2字）
    chapter_pages:{chapter_num_str → [page_id, ...]}  (页面出现在哪些章节)
    page_texts:   {page_id → stripped_text}  (用于 quote 匹配)
    """
    pn_re = re.compile(r'pn:\s*\((\d{3})-([^\)]+)\)', re.MULTILINE)
    wikilink_re = re.compile(r'\[\[(\d{3})_[^\]|]+')

    pn_index: dict[tuple, list] = defaultdict(list)
    entity_index: dict[str, list] = defaultdict(list)
    chapter_pages: dict[str, list] = defaultdict(list)
    page_texts: dict[str, str] = {}

    # 先从 pages_meta 建 entity_index（id + aliases）
    for pid, info in pages_meta.items():
        if len(pid) >= 2:
            entity_index[pid].append(pid)
        for alias in info.get("aliases", []):
            if isinstance(alias, str) and len(alias) >= 2:
                entity_index[alias].append(pid)

    print("  扫描 wiki 页面...", end="", flush=True)
    json_files = glob.glob(str(HISTORY_DIR / "*.json"))
    for i, fpath in enumerate(json_files):
        if i % 1000 == 0:
            print(f"\r  扫描 wiki 页面... {i}/{len(json_files)}", end="", flush=True)
        try:
            d = json.loads(Path(fpath).read_text(encoding="utf-8"))
        except Exception:
            continue
        page_id = d.get("page", "")
        revs = d.get("revisions", [])
        if not revs:
            continue
        content = revs[-1].get("content", "")

        # pn 索引
        for m in pn_re.finditer(content):
            chap = m.group(1)   # "062"
            para = m.group(2)   # "1" 或 "1.1" 或 "r5"
            pn_index[(chap, para)].append(page_id)

        # 章节出现索引（从 wikilink）
        for m in wikilink_re.finditer(content):
            chap = m.group(1)
            chapter_pages[chap].append(page_id)

        # 去重
        chapter_pages[chap] = list(dict.fromkeys(chapter_pages[chap]))

        # 页面文本（strip后用于quote匹配）
        stripped = strip_md(content)
        if stripped:
            page_texts[page_id] = stripped

    print(f"\r  扫描完成：{len(json_files)} 个页面                    ")
    print(f"  pn_index: {len(pn_index)} 条段落引用")
    print(f"  entity_index: {len(entity_index)} 个实体名")
    print(f"  chapter_pages: {len(chapter_pages)} 个章节有引用")
    return pn_index, entity_index, chapter_pages, page_texts


def build_quote_ngram_index(page_texts: dict, min_len: int = QUOTE_MIN_LEN) -> dict[str, list[str]]:
    """
    构建 n-gram 索引：{ngram_str → [page_id, ...]}
    用 10-char 滑动窗口，仅提取全为中文/标点的 ngram（过滤英文/数字）
    """
    print("  构建 quote n-gram 索引...", end="", flush=True)
    chinese_re = re.compile(r'^[一-鿿　-〿＀-￯，。！？；：、「」『』""''…—～]+$')
    ngram_index: dict[str, list[str]] = defaultdict(list)
    for i, (pid, text) in enumerate(page_texts.items()):
        if i % 2000 == 0:
            print(f"\r  构建 quote n-gram 索引... {i}/{len(page_texts)}", end="", flush=True)
        # 提取连续中文文本块（避免噪声）
        chinese_blocks = re.findall(r'[一-鿿，。！？；：、""''…—～]{' + str(min_len) + r',}', text)
        for block in chinese_blocks:
            for j in range(len(block) - min_len + 1):
                ng = block[j:j + min_len]
                if ng not in ngram_index or pid not in ngram_index[ng]:
                    ngram_index[ng].append(pid)
    print(f"\r  quote n-gram 索引：{len(ngram_index):,} 条                    ")
    return ngram_index


# ─── 覆盖判定 ──────────────────────────────────────────────────────────────

def check_coverage(
    unit: dict,
    pn_index: dict,
    entity_index: dict,
    chapter_pages: dict,
    ngram_index: dict,
) -> dict:
    """
    对一个句子单元执行三级覆盖判定，返回覆盖结果字典。
    """
    sid = unit["sid"]
    chapter = unit["chapter"]        # "001_五帝本纪"
    para = unit["para"]              # "1", "1.1", "r5"
    text = unit["text"]
    chap_num = chapter.split("_")[0] # "001"

    matched_pages: list[str] = []
    cover_type = "gap"

    # ── 1. quote 覆盖 ──────────────────────────────────────────────────────
    if len(text) >= QUOTE_MIN_LEN:
        for j in range(len(text) - QUOTE_MIN_LEN + 1):
            ng = text[j:j + QUOTE_MIN_LEN]
            if ng in ngram_index:
                matched_pages = ngram_index[ng][:5]  # 最多记5个
                cover_type = "quote"
                break

    # ── 2. para 覆盖（quote 优先，para 作为补充） ───────────────────────────
    if cover_type == "gap":
        key = (chap_num, para)
        if key in pn_index:
            matched_pages = pn_index[key]
            cover_type = "para"

    # ── 3. entity 覆盖 ─────────────────────────────────────────────────────
    if cover_type == "gap":
        chap_page_set = set(chapter_pages.get(chap_num, []))
        for ename, page_ids in entity_index.items():
            if len(ename) >= 2 and ename in text:
                linked = [pid for pid in page_ids if pid in chap_page_set]
                if linked:
                    matched_pages = linked[:3]
                    cover_type = "entity"
                    break

    status = "covered" if cover_type in ("quote", "para", "entity", "concept") else "gap"

    return {
        "sid": sid,
        "pages": matched_pages,
        "cover_type": cover_type,
        "status": status,
        "updated": TODAY,
    }


# ─── 单章处理 ─────────────────────────────────────────────────────────────

def process_chapter(
    jsonl_path: Path,
    pn_index: dict,
    entity_index: dict,
    chapter_pages: dict,
    ngram_index: dict,
    out_dir: Path,
) -> dict:
    """处理一章的句子索引，输出 coverage_map，返回章统计。"""
    units = [json.loads(l) for l in jsonl_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    results = []
    counts = {"total": len(units), "quote": 0, "para": 0, "entity": 0, "gap": 0, "exempt": 0}

    for u in units:
        r = check_coverage(u, pn_index, entity_index, chapter_pages, ngram_index)
        results.append(r)
        counts[r["cover_type"]] = counts.get(r["cover_type"], 0) + 1

    out_file = out_dir / jsonl_path.name
    with open(out_file, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    covered = counts["quote"] + counts["para"] + counts["entity"]
    counts["covered"] = covered
    counts["coverage_rate"] = round(covered / counts["total"] * 100, 1) if counts["total"] else 0
    return counts


# ─── 汇总报告 ─────────────────────────────────────────────────────────────

def print_report(summary: dict):
    total = summary["total"]
    covered = summary["covered"]
    rate = round(covered / total * 100, 1) if total else 0
    print(f"\n{'='*55}")
    print(f"  史记全文覆盖率报告  ({TODAY})")
    print(f"{'='*55}")
    print(f"  总句子数:   {total:>8,}")
    print(f"  已覆盖:     {covered:>8,}  ({rate}%)")
    print(f"  quote 覆盖: {summary['quote']:>8,}")
    print(f"  para 覆盖:  {summary['para']:>8,}")
    print(f"  entity 覆盖:{summary['entity']:>8,}")
    print(f"  gap (缺口): {summary['gap']:>8,}  ({round(summary['gap']/total*100,1) if total else 0}%)")
    print(f"{'='*55}\n")

    # 找覆盖率最低的5章
    chapters = summary.get("chapters", {})
    if chapters:
        ranked = sorted(chapters.items(), key=lambda x: x[1].get("coverage_rate", 0))
        print("  覆盖率最低的10章：")
        for chap, stats in ranked[:10]:
            print(f"    {chap}: {stats['coverage_rate']}%  ({stats['covered']}/{stats['total']})")


# ─── 入口 ─────────────────────────────────────────────────────────────────

def find_incremental_chapters() -> list[Path]:
    """
    通过 git 找出近期修改过的 wiki 页面，映射到涉及的章节，
    返回需要重算的 sentence_index JSONL 文件列表。
    """
    import subprocess
    # 读上次全量更新时间
    last_updated = None
    if SUMMARY_FILE.exists():
        s = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
        last_updated = s.get("updated", "")

    # git log 找自上次更新以来修改过的 history/*.json
    since = f"--since={last_updated}" if last_updated else "--since=1 day ago"
    result = subprocess.run(
        ["git", "log", since, "--name-only", "--pretty=format:", "--", "wiki/public/history/"],
        capture_output=True, text=True
    )
    changed_files = {l.strip() for l in result.stdout.splitlines() if l.strip().endswith(".json")}

    if not changed_files:
        print("  没有新修改的 wiki 页面，跳过增量更新")
        return []

    print(f"  发现 {len(changed_files)} 个近期修改的页面")

    # 从修改页面中提取章节引用
    wikilink_re = re.compile(r'\[\[(\d{3})_')
    pn_re = re.compile(r'pn:\s*\((\d{3})-')
    affected_chapters: set[str] = set()

    for fpath in changed_files:
        fp = Path(fpath)
        if not fp.exists():
            continue
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
            content = d.get("revisions", [{}])[-1].get("content", "")
            for m in wikilink_re.finditer(content):
                affected_chapters.add(m.group(1))
            for m in pn_re.finditer(content):
                affected_chapters.add(m.group(1))
        except Exception:
            pass

    if not affected_chapters:
        print("  修改页面中未找到章节引用，跳过增量更新")
        return []

    chapter_paths = []
    for chap_num in sorted(affected_chapters):
        matches = list(SENTENCE_DIR.glob(f"{chap_num}_*.jsonl"))
        chapter_paths.extend(matches)

    print(f"  涉及 {len(affected_chapters)} 个章节需重算：{sorted(affected_chapters)}")
    return sorted(set(chapter_paths))


def main():
    report_only = "--report" in sys.argv
    incremental = "--incremental" in sys.argv
    specific = next((a for a in sys.argv[1:] if not a.startswith("--")), None)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 如果只看报告，直接读 summary
    if report_only and SUMMARY_FILE.exists():
        summary = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
        print_report(summary)
        return

    # 构建索引（全量/增量都需要）
    print("构建覆盖索引...")
    pages_meta = load_pages()
    pn_index, entity_index, chapter_pages, page_texts = build_indices(pages_meta)
    ngram_index = build_quote_ngram_index(page_texts)

    # 确定章节列表
    if incremental:
        print("\n增量模式：查找近期修改的章节...")
        chapters_to_run = find_incremental_chapters()
        if not chapters_to_run:
            return
        # 读取现有 summary 作为基准
        if SUMMARY_FILE.exists():
            global_stats = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
        else:
            global_stats = {"total": 0, "covered": 0, "quote": 0, "para": 0,
                            "entity": 0, "gap": 0, "chapters": {}}
    else:
        all_chapters = sorted(SENTENCE_DIR.glob("*.jsonl"))
        if specific:
            chapters_to_run = [p for p in all_chapters if specific in p.stem]
            if not chapters_to_run:
                print(f"❌ 未找到匹配 '{specific}' 的章节")
                sys.exit(1)
        else:
            chapters_to_run = all_chapters
        global_stats = {"total": 0, "covered": 0, "quote": 0, "para": 0,
                        "entity": 0, "gap": 0, "chapters": {}}

    # 逐章处理
    mode_label = "增量" if incremental else "全量"
    print(f"\n{mode_label}处理 {len(chapters_to_run)} 章...\n")

    for ch_path in chapters_to_run:
        counts = process_chapter(ch_path, pn_index, entity_index, chapter_pages, ngram_index, OUT_DIR)
        chap_name = ch_path.stem
        print(f"  {chap_name}: {counts['coverage_rate']}%  "
              f"quote={counts['quote']} para={counts['para']} "
              f"entity={counts['entity']} gap={counts['gap']}")

        if incremental:
            # 增量：从总计中减去旧值，加上新值
            old = global_stats.get("chapters", {}).get(chap_name, {})
            for key in ("total", "covered", "quote", "para", "entity", "gap"):
                global_stats[key] = global_stats.get(key, 0) - old.get(key, 0) + counts.get(key, 0)
        else:
            for key in ("total", "covered", "quote", "para", "entity", "gap"):
                global_stats[key] = global_stats.get(key, 0) + counts.get(key, 0)

        global_stats.setdefault("chapters", {})[chap_name] = counts

    # 写汇总
    global_stats["updated"] = TODAY
    SUMMARY_FILE.write_text(json.dumps(global_stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print_report(global_stats)
    print(f"  覆盖映射已写入: {OUT_DIR}/")
    print(f"  汇总已写入:     {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
