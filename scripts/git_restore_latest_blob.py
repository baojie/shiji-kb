#!/usr/bin/env python3
"""
章节级灾难恢复工具：为每章在 git 全对象库中挑选**创建时间最新**的 blob 写回。

应用场景：
  误删/误改了 chapter_md/NNN_*.tagged.md，希望从 .git 里找回最近一次合法状态。
  本脚本枚举所有 blob（pack+loose），按首行章节标题匹配到章节号，然后按
  blob 的 birth time（.git/objects/xx/xxxx... 的 stat %W）取最新者。

成功案例：
  2026-04-17 恢复 081-130 共 50 章。此策略在"最大 blob"策略（可能命中中间状态）
  失败后被验证为可靠方案。

用法：
  python scripts/git_restore_latest_blob.py
  （默认处理 081-130；如需改范围，调整 target_nums）

附加功能：
  写回时顺带做 3 种格式迁移（已废弃的 PUA 字符修复）：
    〖'X〗 → 〖◆X〗  （旧邦国标记 U+2018）
    〖：X〗 → 〖:X〗  （全角冒号 OCR 残留）
    行首 ：：： → :::  （fence 标记）
  写回前自动把当前 HEAD 版本备份到 backups/pre_latest_restore/
"""
import subprocess
import re
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CH = ROOT / "chapter_md"
PRE_BACKUP = ROOT / "backups" / "pre_latest_restore"
PRE_BACKUP.mkdir(exist_ok=True, parents=True)


def build_title_map():
    m = {}
    for f in sorted(CH.glob("???_*.tagged.md")):
        stem = f.stem.replace(".tagged", "")
        num, _, title = stem.partition("_")
        m[title] = num
    return m


def get_btime(h):
    p = ROOT / ".git/objects" / h[:2] / h[2:]
    if p.exists():
        r = subprocess.run(["stat", "-c", "%W", str(p)], capture_output=True, text=True)
        try:
            return float(r.stdout.strip())
        except ValueError:
            return 0.0
    return 0.0


def main():
    title2num = build_title_map()
    target_nums = {f"{n:03d}" for n in range(81, 131)}

    print("[i] 枚举所有 blob...")
    r = subprocess.run(
        ["git", "cat-file", "--batch-check", "--batch-all-objects", "--unordered"],
        cwd=ROOT, capture_output=True, text=True
    )
    objs = []
    for line in r.stdout.split("\n"):
        parts = line.split()
        if len(parts) >= 3 and parts[1] == "blob":
            s = int(parts[2])
            if 1000 < s < 200000:
                objs.append((parts[0], s))
    print(f"[i] 候选: {len(objs)}")

    by_num = {num: [] for num in target_nums}
    print("[i] 匹配章节首行...")
    for i, (h, s) in enumerate(objs):
        if i % 3000 == 0:
            print(f"  {i}/{len(objs)}")
        r2 = subprocess.run(["git", "cat-file", "-p", h], cwd=ROOT, capture_output=True)
        first = r2.stdout[:200].split(b"\n", 1)[0].decode("utf-8", errors="replace")
        m = re.match(r"^#\s+(?:\[\d+\]\s+)?(.+?)\s*$", first)
        if not m:
            continue
        title = m.group(1).strip()
        num = title2num.get(title)
        if num in target_nums:
            by_num[num].append((h, s))

    print()
    print(f"{'章':4} {'blob':12} {'size':>7} {'btime':>20}")
    print("-" * 52)
    picks = {}
    no_blob = []
    for num in sorted(target_nums):
        cands = by_num[num]
        with_bt = [(h, s, get_btime(h)) for h, s in cands]
        with_bt = [(h, s, bt) for h, s, bt in with_bt if bt > 0]
        if not with_bt:
            no_blob.append(num)
            print(f"  {num}  ✗ 无 loose blob")
            continue
        with_bt.sort(key=lambda x: -x[2])  # 最新在前
        best = with_bt[0]
        h, s, bt = best
        dt = datetime.fromtimestamp(bt).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {num}  {h[:10]}   {s:>7}   {dt}")
        picks[num] = (h, s, bt)

    print()
    print(f"[i] 写回工作区（含格式迁移 〖‘→〖◆, 〖：→〖:, ：：：→:::）...")
    for num, (h, s, bt) in picks.items():
        target = next(CH.glob(f"{num}_*.tagged.md"), None)
        if not target:
            continue
        shutil.copy(target, PRE_BACKUP / target.name)
        content = subprocess.run(
            ["git", "cat-file", "-p", h], cwd=ROOT, capture_output=True
        ).stdout.decode("utf-8")
        content, c1 = re.subn(r'〖\u2018', '〖\u25c6', content)
        content, c2 = re.subn(r'〖：', '〖:', content)
        content, c3 = re.subn(r'^：：：', ':::', content, flags=re.MULTILINE)
        target.write_text(content, encoding="utf-8")
        fixes = c1 + c2 + c3
        suffix = f" (迁移 {fixes})" if fixes else ""
        print(f"  ✓ {target.name}{suffix}")

    if no_blob:
        print(f"\n⚠ 无 loose blob 的章节：{no_blob}")
    print(f"\n备份在 {PRE_BACKUP}/")


if __name__ == "__main__":
    main()
