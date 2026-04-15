#!/usr/bin/env python3
"""
根据 data/sanwen_manifest.json，从 chapter_md/*.tagged.md 中按段落范围提取散文内容，
生成 data/sanwen.json 和 data/sanwen.md。
"""

from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "sanwen_manifest.json"
CHAPTER_DIR = ROOT / "chapter_md"
OUT_JSON = ROOT / "data" / "sanwen.json"
OUT_MD = ROOT / "data" / "sanwen.md"

PARA_HDR = re.compile(r"^\[(\d+(?:\.\d+)*)\]\s*", re.MULTILINE)

TYPE_DESC = {
    "诏令": "帝王颁布的诏书、制诏、遗诏",
    "奏疏": "臣下上奏皇帝的疏议、上书、上言",
    "书信": "人物之间往来的书信、国书",
    "檄文": "声讨、宣谕性质的檄文",
    "策论": "对策、长篇建议、策士说辞",
    "议论": "长篇议论性散文",
}


def para_tuple(s: str) -> tuple[int, ...]:
    return tuple(int(x) for x in s.split("."))


def in_range(pid: str, lo: tuple, hi: tuple) -> bool:
    t = para_tuple(pid)
    # tuple 比较：(17,) < (17,1) < (17,99)；(17,5) < (17,99)
    return lo <= t <= hi


def extract_range(text: str, start: str, end: str) -> str:
    """从 tagged.md 文本中提取段落 [start..end] 的所有内容（含段号、含标注）。"""
    lo = para_tuple(start)
    hi = para_tuple(end)
    matches = list(PARA_HDR.finditer(text))
    if not matches:
        return ""
    in_flag = False
    chunks: list[str] = []
    for i, m in enumerate(matches):
        pid = m.group(1)
        start_off = m.start()
        end_off = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        t = para_tuple(pid)
        if lo <= t <= hi:
            block = text[start_off:end_off]
            # 去掉块内可能的 `## XX` 标题行（会干扰渲染）
            block = re.sub(r"^#{1,6}\s+.*$", "", block, flags=re.MULTILINE)
            # 去除 ::: 区块围栏（开/合）
            block = re.sub(r"^:::.*$", "", block, flags=re.MULTILINE)
            # 去除 markdown 引用前缀 `> `（源文件用其标注对话）
            block = re.sub(r"^>\s?", "", block, flags=re.MULTILINE)
            chunks.append(block.rstrip())
    return "\n".join(chunks).strip()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    chapter_cache: dict[str, str] = {}
    out = []
    missing = 0

    for entry in manifest:
        ch = entry["chapter_num"]
        if ch not in chapter_cache:
            # 找到对应的章节文件
            files = list(CHAPTER_DIR.glob(f"{ch}_*.tagged.md"))
            if not files:
                print(f"! 缺少章节文件: {ch}")
                missing += 1
                chapter_cache[ch] = ""
                continue
            chapter_cache[ch] = files[0].read_text(encoding="utf-8")
        text = chapter_cache[ch]
        content = extract_range(text, entry["start_para"], entry["end_para"])
        if not content:
            print(f"! 空提取: {ch} [{entry['start_para']}-{entry['end_para']}] {entry.get('title')}")
            continue
        out.append({
            "chapter_num": ch,
            "chapter_title": entry["chapter_title"],
            "type": entry["type"],
            "type_desc": TYPE_DESC.get(entry["type"], ""),
            "title": entry["title"],
            "start_para": entry["start_para"],
            "end_para": entry["end_para"],
            "intro": entry.get("intro", ""),
            "content": content,
        })

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n提取 {len(out)} 篇 → {OUT_JSON}")
    if missing:
        print(f"  缺章节 {missing}")

    # Markdown
    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write(f"# 史记散文集\n\n共 {len(out)} 篇\n\n")
        by_type: dict[str, list] = {}
        for it in out:
            by_type.setdefault(it["type"], []).append(it)
        for t in ["诏令", "奏疏", "书信", "檄文", "策论", "议论"]:
            items = by_type.get(t, [])
            if not items:
                continue
            f.write(f"## {t}（{len(items)}篇）\n\n{TYPE_DESC.get(t, '')}\n\n")
            for it in items:
                f.write(f"### {it['title']}\n\n")
                f.write(f"*{it['chapter_num']} {it['chapter_title']} · "
                        f"[{it['start_para']}-{it['end_para']}]*\n\n")
                if it["intro"]:
                    f.write(f"> {it['intro']}\n\n")
                f.write(f"{it['content']}\n\n---\n\n")
    print(f"Markdown → {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
