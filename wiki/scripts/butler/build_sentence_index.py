#!/usr/bin/env python3
"""
build_sentence_index.py — W13 句子索引构建脚本

从 chapter_md/*.tagged.md 生成 wiki/logs/butler/sentence_index/XXX.jsonl
每行一个句子单元：
  {"sid": "...", "chapter": "...", "para": "...", "seq": N, "text": "...", "len": N}

用法：
  python3 wiki/scripts/butler/build_sentence_index.py          # 全量（130章）
  python3 wiki/scripts/butler/build_sentence_index.py 001      # 单章调试
  python3 wiki/scripts/butler/build_sentence_index.py 001_五帝本纪
"""

import re
import json
import sys
from pathlib import Path

CHAPTER_DIR = Path("chapter_md")
OUT_DIR = Path("wiki/logs/butler/sentence_index")


# ─── 去除标注符号，保留原文字符 ────────────────────────────────────────────

def strip_annotations(text: str) -> str:
    """
    去除所有 〖〗 ⟦⟧ 〘〙 标注符号，保留原文显示文本。

    格式规则：
      〖X display|canonical〗 → display
      〖X text〗              → text
      ⟦X text⟧              → text
      〘X text〙              → text
    其中 X 为单个 Unicode 字符（类型标记符）。
    """
    # 1. 消歧语法：〖X display|canonical〗 → display
    text = re.sub(r'〖[^\s〖〗]([^|〗]*)\|[^〗]*〗', r'\1', text)
    # 2. 普通实体标注：〖X text〗 → text
    text = re.sub(r'〖[^\s〖〗]([^〗]*)〗', r'\1', text)
    # 3. 动词标注：⟦X text⟧ → text
    text = re.sub(r'⟦[^\s⟦⟧]([^⟧]*)⟧', r'\1', text)
    # 4. 成语/短语标注：〘X text〙 → text
    text = re.sub(r'〘[^\s〘〙]([^〙]*)〙', r'\1', text)
    # 5. 清除残余括号（防御）
    text = re.sub(r'[〖〗⟦⟧〘〙]', '', text)
    return text.strip()


# ─── 分句 ─────────────────────────────────────────────────────────────────

def split_sentences(text: str) -> list[str]:
    """
    古文分句：以 。！？ 为主界，引号内不切，短碎片（<3字）合并到前句。
    """
    result: list[str] = []
    buf = ""
    depth = 0  # 引号嵌套深度

    for ch in text:
        buf += ch
        if ch in ('"', '「', '『', '【', '〔'):
            depth += 1
        elif ch in ('"', '」', '』', '】', '〕'):
            depth = max(0, depth - 1)
        if depth == 0 and ch in ('。', '！', '？'):
            s = buf.strip()
            if len(s) >= 3:
                result.append(s)
            buf = ""

    tail = buf.strip()
    if tail:
        if result and len(tail) < 3:
            result[-1] += tail
        elif tail:
            result.append(tail)

    return result


# ─── 解析单章 ─────────────────────────────────────────────────────────────

# 匹配段落标记 [1] [1.1] [12] [3.2] 等
PARA_RE = re.compile(r'^\[(\d+(?:\.\d+)?)\]\s*(.*)')
# 匹配表格行 [r1] [r23] 等
TABLE_ROW_RE = re.compile(r'^\[r(\d+)\]\s*(.*)')
# 匹配表头分隔行
TABLE_SEP_RE = re.compile(r'^\|?[\s\-|:]+\|')
# 匹配 markdown 标题
HEADING_RE = re.compile(r'^#{1,6}\s')


def parse_chapter(md_path: Path) -> list[dict]:
    # 去掉 .tagged 后缀，得到 "001_五帝本纪"
    chapter_id = md_path.stem.removesuffix(".tagged")
    lines = md_path.read_text(encoding="utf-8").splitlines()

    units: list[dict] = []
    current_para: str | None = None
    current_lines: list[str] = []

    def flush():
        nonlocal current_para, current_lines
        if current_para is None or not current_lines:
            current_para = None
            current_lines = []
            return
        full = " ".join(current_lines)
        raw = strip_annotations(full)
        if raw:
            for i, s in enumerate(split_sentences(raw), 1):
                units.append({
                    "sid": f"{chapter_id}.{current_para}.s{i}",
                    "chapter": chapter_id,
                    "para": current_para,
                    "seq": i,
                    "text": s,
                    "len": len(s),
                })
        current_para = None
        current_lines = []

    for line in lines:
        line = line.rstrip()

        # 表格行
        m = TABLE_ROW_RE.match(line)
        if m:
            flush()
            row_id = m.group(1)
            row_content = m.group(2)
            # 按 | 切列，跳过空列和分隔列
            cols = [c.strip() for c in row_content.split('|')]
            col_num = 0
            for col in cols:
                if not col or col == '---' or re.fullmatch(r'[\d\s\-:]*', col):
                    continue
                raw = strip_annotations(col)
                if not raw or len(raw) < 2:
                    continue
                col_num += 1
                units.append({
                    "sid": f"{chapter_id}.r{row_id}.c{col_num}",
                    "chapter": chapter_id,
                    "para": f"r{row_id}",
                    "seq": col_num,
                    "text": raw,
                    "len": len(raw),
                })
            continue

        # 表头分隔行（| --- | --- |），跳过
        if TABLE_SEP_RE.match(line):
            continue

        # 普通段落起始
        m = PARA_RE.match(line)
        if m:
            flush()
            current_para = m.group(1)
            rest = m.group(2).strip()
            current_lines = [rest] if rest else []
            continue

        # 跳过 markdown 标题、水平线、空行
        if not line or HEADING_RE.match(line) or line.startswith('---'):
            continue

        # 列表项：归入当前段落
        if current_para is not None and line.startswith('- '):
            current_lines.append(line[2:].strip())
            continue

        # Markdown 引用块（"> text"）：去掉 "> " 前缀，归入当前段落
        if current_para is not None and re.match(r'^>+\s*', line):
            current_lines.append(re.sub(r'^>+\s*', '', line).strip())
            continue

        # 普通续行
        if current_para is not None and line:
            current_lines.append(line)

    flush()
    return units


# ─── 入口 ─────────────────────────────────────────────────────────────────

def main():
    specific = sys.argv[1] if len(sys.argv) > 1 else None

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    chapters = sorted(CHAPTER_DIR.glob("*.tagged.md"))
    if specific:
        chapters = [p for p in chapters if specific in p.stem]
        if not chapters:
            print(f"❌ 未找到匹配 '{specific}' 的章节")
            sys.exit(1)

    total_units = 0
    for ch in chapters:
        units = parse_chapter(ch)
        out_file = OUT_DIR / (ch.stem.removesuffix(".tagged") + ".jsonl")
        with open(out_file, "w", encoding="utf-8") as f:
            for u in units:
                f.write(json.dumps(u, ensure_ascii=False) + "\n")
        print(f"  {ch.stem}: {len(units)} 句")
        total_units += len(units)

    print(f"\n✅ 共处理 {len(chapters)} 章，{total_units} 个句子单元")
    print(f"   输出目录: {OUT_DIR}/")


if __name__ == "__main__":
    main()
