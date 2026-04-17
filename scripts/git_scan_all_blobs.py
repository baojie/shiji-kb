#!/usr/bin/env python3
"""
枚举 git 全对象库（pack + loose）里所有 blob，按章节首行标题匹配到
chapter_md/NNN_*.tagged.md 的候选。比 git_lost_found_extract.py 更全面
（覆盖所有 pack 打包对象）。

应用场景：
  lost-found 不够用时的最全扫描。典型管道：
    git_scan_all_blobs.py         # 列出所有候选（快速过滤 size 区间）
    git_restore_latest_blob.py    # 择 btime 最新者自动回写

默认章节范围按注释内 target 调整；本脚本保留 2026-04 恢复时的 121-125/129
范围作为示例，实际使用时请按需修改。
"""
import subprocess
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CH = ROOT / "chapter_md"


def build_title_map():
    m = {}
    for f in sorted(CH.glob("???_*.tagged.md")):
        stem = f.stem.replace(".tagged", "")
        num, _, title = stem.partition("_")
        m[title] = num
    return m


def main():
    title2num = build_title_map()
    target_nums = {"121", "122", "123", "124", "125", "129"}

    print("[i] 枚举所有 blob（含 pack）...")
    # 只要 blob，用 --batch-check + filter
    r = subprocess.run(
        ["git", "cat-file", "--batch-check", "--batch-all-objects", "--unordered"],
        cwd=ROOT, capture_output=True, text=True
    )
    all_objs = []
    for line in r.stdout.split("\n"):
        parts = line.split()
        if len(parts) >= 3 and parts[1] == "blob":
            all_objs.append((parts[0], int(parts[2])))
    print(f"[i] 共 {len(all_objs)} 个 blob")

    # 过滤：内容大小在 1KB~100KB 之间（章节标注文件范围）
    candidates = [(h, s) for h, s in all_objs if 1000 < s < 100000]
    print(f"[i] 尺寸合理的 blob: {len(candidates)}")

    # 批量读取首行
    print("[i] 读首行匹配目标章节...")
    by_chapter = {num: [] for num in target_nums}
    batch_input = "\n".join(h for h, _ in candidates).encode()
    r = subprocess.Popen(
        ["git", "cat-file", "--batch=%(objectname)%x00%(objectsize)"],
        cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )
    # 简化：对每个 blob 单独 git cat-file -p 的第一行
    # 但这很慢。改用一种更快方法：只处理尺寸范围匹配章节大小的
    for h, s in candidates:
        r2 = subprocess.run(
            ["git", "cat-file", "-p", h],
            cwd=ROOT, capture_output=True
        )
        first_line = r2.stdout[:200].split(b"\n", 1)[0].decode("utf-8", errors="replace")
        m = re.match(r"^# \[\d+\] (.+?)\s*$", first_line)
        if not m:
            continue
        title = m.group(1).strip()
        num = title2num.get(title)
        if num in target_nums:
            by_chapter[num].append((h, s))

    # 对每章找 btime
    anchor = datetime(2026, 4, 17, 3, 21, 20).timestamp()

    def get_btime_for_hash(h):
        p = ROOT / ".git" / "objects" / h[:2] / h[2:]
        if p.exists():
            r = subprocess.run(["stat", "-c", "%W", str(p)], capture_output=True, text=True)
            try:
                return float(r.stdout.strip())
            except ValueError:
                return 0.0
        # pack 里的没法拿精确时间
        return 0.0

    for num in sorted(target_nums):
        ch_files = list(CH.glob(f"{num}_*.tagged.md"))
        ch_name = ch_files[0].stem.replace(".tagged", "") if ch_files else num
        head_size = 0
        if ch_files:
            r3 = subprocess.run(
                ["git", "show", f"HEAD:chapter_md/{ch_files[0].name}"],
                cwd=ROOT, capture_output=True
            )
            head_size = len(r3.stdout) if r3.returncode == 0 else 0

        cands = by_chapter[num]
        print(f"\n=== {num} {ch_name} (HEAD={head_size}) ===")
        if not cands:
            print("  ❌ 无任何候选")
            continue
        # 过滤：只要 > HEAD 的（可能是第四轮增量版）
        bigger = [(h, s, get_btime_for_hash(h)) for h, s in cands if s > head_size]
        same_or_smaller = [(h, s, get_btime_for_hash(h)) for h, s in cands if s <= head_size]
        if bigger:
            print(f"  大于 HEAD 的 {len(bigger)} 个 blob:")
            bigger.sort(key=lambda x: -x[2])
            for h, s, bt in bigger[:10]:
                dt = datetime.fromtimestamp(bt).strftime("%Y-%m-%d %H:%M") if bt > 0 else "pack(无btime)"
                delta = abs(bt - anchor) / 3600 if bt > 0 else 9999
                mark = "★" if 0 < delta < 5 else ""
                print(f"    {h[:10]}  size={s}  btime={dt}  Δ={delta:.1f}h {mark}")
        if same_or_smaller:
            print(f"  ≤ HEAD 的 {len(same_or_smaller)} 个 blob（一般不需要）")


if __name__ == "__main__":
    main()
