#!/usr/bin/env python3
"""
从 .git/lost-found/other/ 里按章节首行标题匹配，提取 chapter_md/*.tagged.md
的候选 blob，按章节归类 dump 到 backups/rescue_<date>/NNN_xxx/，并为每章
生成 _SUMMARY.txt（候选特征：大小/标注数/引号类型/与 HEAD 差异行数）。

应用场景：
  误删/误改后，从 `git fsck --lost-found` 产生的 lost-found/other/ 里拉回候选。
  输出供人工审查（或用 git_restore_latest_blob.py 按 btime 自动选最新）。

注意：
  仅扫描 lost-found 目录；若该目录为空，优先使用 git_scan_all_blobs.py
  （后者扫全库含 pack）。

只读操作，不写 chapter_md/。
"""
import subprocess
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
LOST_FOUND = ROOT / ".git" / "lost-found" / "other"
CHAPTER_DIR = ROOT / "chapter_md"
DATE = datetime.now().strftime("%Y%m%d")
OUT_DIR = ROOT / "backups" / f"rescue_{DATE}"


def git_show(blob_hash: str) -> bytes:
    r = subprocess.run(
        ["git", "cat-file", "-p", blob_hash],
        cwd=ROOT, capture_output=True
    )
    return r.stdout if r.returncode == 0 else b""


def git_head_version(path: str) -> bytes:
    r = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=ROOT, capture_output=True
    )
    return r.stdout if r.returncode == 0 else b""


def build_title_map() -> dict:
    """章节标题 -> 编号（如 '廉颇蔺相如列传' -> '081'）"""
    m = {}
    for f in sorted(CHAPTER_DIR.glob("???_*.tagged.md")):
        stem = f.stem.replace(".tagged", "")
        num, _, title = stem.partition("_")
        m[title] = num
    return m


def count_quotes(data: bytes) -> dict:
    """统计全/半角引号数"""
    text = data.decode("utf-8", errors="replace")
    return {
        "full_left": text.count("\u201c"),      # "
        "full_right": text.count("\u201d"),     # "
        "half": text.count("\u0022"),           # "
        "entity_marks": text.count("\u3016"),   # 〖
    }


def diff_linecount(a: bytes, b: bytes) -> int:
    """简单行级差异：统计不同的行数"""
    la = a.decode("utf-8", errors="replace").splitlines()
    lb = b.decode("utf-8", errors="replace").splitlines()
    import difflib
    diff = list(difflib.unified_diff(la, lb, n=0, lineterm=""))
    return sum(1 for line in diff if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))


def main():
    title2num = build_title_map()
    print(f"[i] 章节标题映射加载：{len(title2num)} 条")

    # 收集候选 blob
    print(f"[i] 扫描 {LOST_FOUND} ...")
    candidates_by_chapter = {}  # num -> [(hash, size, data)]

    for blob_file in sorted(LOST_FOUND.iterdir()):
        blob_hash = blob_file.name
        data = git_show(blob_hash)
        if not data:
            continue
        first_line = data.split(b"\n", 1)[0].decode("utf-8", errors="replace")
        # 匹配 "# [0] XXX" 格式（tagged.md 统一用 [0] 作为起始章节号）
        m = re.match(r"^# \[\d+\] (.+?)\s*$", first_line)
        if not m:
            continue
        title = m.group(1).strip()
        num = title2num.get(title)
        if not num:
            continue
        # 只处理 081-130
        try:
            if not (81 <= int(num) <= 130):
                continue
        except ValueError:
            continue
        candidates_by_chapter.setdefault(num, []).append((blob_hash, len(data), data))

    print(f"[i] 找到 {sum(len(v) for v in candidates_by_chapter.values())} 个候选 blob，"
          f"覆盖 {len(candidates_by_chapter)} 章")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[i] 输出目录：{OUT_DIR}")

    # 总索引
    global_summary_lines = ["# 081-130 救援总索引", ""]
    global_summary_lines.append("| 章 | 候选数 | HEAD大小 | 最大blob | 推荐blob | 说明 |")
    global_summary_lines.append("|---|---|---|---|---|---|")

    missing_chapters = []

    for num_int in range(81, 131):
        num = f"{num_int:03d}"
        # 找章节名
        ch_files = list(CHAPTER_DIR.glob(f"{num}_*.tagged.md"))
        if not ch_files:
            continue
        ch_name = ch_files[0].stem.replace(".tagged", "")  # e.g. 081_廉颇蔺相如列传
        rel_path = f"chapter_md/{ch_files[0].name}"
        head_data = git_head_version(rel_path)
        head_size = len(head_data)

        cands = candidates_by_chapter.get(num, [])
        if not cands:
            missing_chapters.append(num)
            global_summary_lines.append(f"| {num} | **0** | {head_size} | - | - | ❌ 无救援 blob |")
            continue

        # 输出到本章目录
        ch_dir = OUT_DIR / ch_name
        ch_dir.mkdir(parents=True, exist_ok=True)

        # HEAD 参照
        (ch_dir / "_HEAD.md").write_bytes(head_data)

        # 按大小排序（大在前）
        cands.sort(key=lambda x: -x[1])

        summary = [f"# {ch_name} 救援候选清单", ""]
        summary.append(f"- HEAD 版本大小: **{head_size}** bytes")
        summary.append(f"- 候选 blob 数: **{len(cands)}**")
        summary.append("")
        summary.append("| # | blob hash (短) | 大小 | 〖数 | 全角" + '"' + " | 半角\" | 与HEAD差异行 | 文件名 |")
        summary.append("|---|---|---|---|---|---|---|---|")

        for idx, (h, size, data) in enumerate(cands, 1):
            short = h[:10]
            # dump blob 文件
            out_name = f"cand_{idx:02d}_{short}_{size}.md"
            (ch_dir / out_name).write_bytes(data)

            q = count_quotes(data)
            diff_lines = diff_linecount(head_data, data)

            full_pair = min(q["full_left"], q["full_right"])
            quote_status_full = f"{q['full_left']}/{q['full_right']}"
            summary.append(
                f"| {idx} | `{short}` | {size} | {q['entity_marks']} | "
                f"{quote_status_full} | {q['half']} | {diff_lines} | {out_name} |"
            )

        (ch_dir / "_SUMMARY.md").write_text("\n".join(summary), encoding="utf-8")

        # 总索引行：推荐选最大且半角=0 的 blob
        recommended = None
        for h, size, data in cands:
            q = count_quotes(data)
            if q["half"] == 0 and q["full_left"] > 0:
                recommended = (h[:10], size)
                break
        if recommended is None:
            recommended = (cands[0][0][:10], cands[0][1])

        biggest = cands[0][1]
        note = "✓" if biggest > head_size else "⚠ blob 未大于 HEAD"
        global_summary_lines.append(
            f"| {num} | {len(cands)} | {head_size} | {biggest} | `{recommended[0]}`({recommended[1]}) | {note} |"
        )

    global_summary_lines.append("")
    if missing_chapters:
        global_summary_lines.append(f"## ❌ 无救援数据的章节（{len(missing_chapters)} 章）")
        global_summary_lines.append(", ".join(missing_chapters))

    (OUT_DIR / "_INDEX.md").write_text("\n".join(global_summary_lines), encoding="utf-8")
    print(f"[✓] 救援 dump 完成")
    print(f"[✓] 索引：{OUT_DIR / '_INDEX.md'}")
    print(f"[!] 无救援数据的章节：{missing_chapters}")


if __name__ == "__main__":
    main()
