#!/usr/bin/env python3
"""
batch_fix_spread.py — 批量对所有双页跨页地图执行书脊形变校正

跳过单页地图（crop_top_half=True）：这些地图没有中脊，不需要处理。
横向中脊的竖版双页图使用 --vertical 参数。
输出文件名格式：朝代-地区.jpg

用法：
  python batch_fix_spread.py [--sharpen]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
OUT_DIR    = SCRIPT_DIR / "output"        # symlink
JPG_DIR    = OUT_DIR / "jpg"

VOL_DIRS = {
    "vol1": JPG_DIR / "vol1_先秦_maps",
    "vol2": JPG_DIR / "vol2_秦汉_maps",
}

# 横向中脊（竖版双页图）：需要 --vertical
VERTICAL_ATLASES = {
    ("vol2", "22-23"), ("vol2", "24-25"), ("vol2", "47-48"),
    ("vol2", "49-50"), ("vol2", "51-52"), ("vol2", "59-60"),
    ("vol1", "45-46"), ("vol1", "5-6"),
}

# 最终文件名（朝代-地区），不含 .jpg
FINAL_NAMES = {
    # ── vol1 先秦 ──────────────────────────────────────────────
    ("vol1", "1-2"):   "参考-全国（先秦册）",
    ("vol1", "3-4"):   "原始社会-遗址",
    ("vol1", "5-6"):   "原始社会-旧石器遗址",
    ("vol1", "7-8"):   "原始社会-新石器遗址",
    ("vol1", "9-10"):  "夏-全图",
    ("vol1", "11-12"): "商-全图",
    ("vol1", "13-14"): "商-中心区域",
    ("vol1", "15-16"): "西周-全图",
    ("vol1", "17-18"): "西周-中心区域",
    ("vol1", "19"):    "西周-宗周成周",       # 单页，直接复制
    ("vol1", "20-21"): "春秋-全图",
    ("vol1", "22-23"): "春秋-晋秦",
    ("vol1", "24-25"): "春秋-郑宋卫",
    ("vol1", "26-27"): "春秋-齐鲁",
    ("vol1", "28"):    "春秋-北燕",           # 单页，直接复制
    ("vol1", "29-30"): "春秋-楚吴越",
    ("vol1", "31-32"): "战国-全图",
    ("vol1", "33-34"): "战国-诸侯形势",
    ("vol1", "35-36"): "战国-韩魏",
    ("vol1", "37-38"): "战国-赵中山",
    ("vol1", "39-40"): "战国-齐鲁宋",
    ("vol1", "41-42"): "战国-燕",
    ("vol1", "43-44"): "战国-秦蜀",
    ("vol1", "45-46"): "战国-楚越",

    # ── vol2 秦汉 ──────────────────────────────────────────────
    ("vol2", "1-2"):   "参考-全国（秦汉册）",
    ("vol2", "3-4"):   "秦-全图",
    ("vol2", "5-6"):   "秦-关中",
    ("vol2", "7-8"):   "秦-山东南",
    ("vol2", "9-10"):  "秦-山东北",
    ("vol2", "11-12"): "秦-淮汉以南",
    ("vol2", "13-14"): "西汉-全图",
    ("vol2", "15-16"): "西汉-司隶",
    ("vol2", "17-18"): "西汉-并州朔方",
    ("vol2", "19-20"): "西汉-兖豫青徐",
    ("vol2", "21"):    "西汉-东郡北海",       # 单页，直接复制
    ("vol2", "22-23"): "西汉-荆州",
    ("vol2", "24-25"): "西汉-扬州",
    ("vol2", "26"):    "西汉-冀州",           # 单页，直接复制
    ("vol2", "27-28"): "西汉-幽州",
    ("vol2", "29-30"): "西汉-益州北",
    ("vol2", "31-32"): "西汉-益州南",
    ("vol2", "33-34"): "西汉-凉州",
    ("vol2", "35-36"): "西汉-交阯",
    ("vol2", "37-38"): "西汉-西域",
    ("vol2", "39"):    "西汉-匈奴",           # 单页，直接复制
    ("vol2", "40-41"): "东汉-全图",
    ("vol2", "42-43"): "东汉-司隶",
    ("vol2", "44-45"): "东汉-兖豫青徐",
    ("vol2", "46"):    "东汉-颖川",           # 单页，直接复制
    ("vol2", "47-48"): "东汉-冀州",
    ("vol2", "49-50"): "东汉-荆州",
    ("vol2", "51-52"): "东汉-扬州",
    ("vol2", "53-54"): "东汉-益州北",
    ("vol2", "55-56"): "东汉-益州南",
    ("vol2", "57-58"): "东汉-凉州",
    ("vol2", "59-60"): "东汉-并州",
    ("vol2", "61-62"): "东汉-幽州",
    ("vol2", "63-64"): "东汉-交阯",
    ("vol2", "65-66"): "东汉-西域",
    ("vol2", "67"):    "东汉-鲜卑",           # 单页，直接复制
}


def load_no_spine_atlases() -> set:
    """从 manifest 读取 crop_top_half=True 的单页地图（无中脊，跳过）。"""
    no_spine = set()
    for vol_short, vol_name in [("vol1", "vol1_先秦"), ("vol2", "vol2_秦汉")]:
        mf_path = OUT_DIR / f"{vol_name}_manifest.json"
        for m in json.loads(mf_path.read_text(encoding="utf-8")):
            if m.get("crop_top_half"):
                no_spine.add((vol_short, m["atlas"]))
    return no_spine


def filename_to_atlas(fn: str) -> str:
    m = re.match(r"^(\d+(?:-\d+)?)_", fn)
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=str(SCRIPT_DIR / "map_final"), help="输出目录（默认 map_final/）")
    ap.add_argument("--sharpen", action="store_true", help="启用文字线条增强（USM）")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    no_spine = load_no_spine_atlases()

    ok = skipped = fail = 0
    fix_script = SCRIPT_DIR / "fix_book_spread.py"

    for vol, vol_dir in VOL_DIRS.items():
        for fn in sorted(os.listdir(vol_dir)):
            if not fn.endswith(".jpg"):
                continue
            atlas = filename_to_atlas(fn)
            if not atlas:
                continue

            key = (vol, atlas)
            final_name = FINAL_NAMES.get(key)
            if final_name is None:
                print(f"  ⚠ 未配置命名：{vol} {atlas} {fn}，跳过")
                skipped += 1
                continue

            src = vol_dir / fn
            dst = out_dir / f"{final_name}.jpg"

            # 单页图（无中脊）：直接复制，不做书脊校正
            if key in no_spine:
                shutil.copy2(src, dst)
                print(f"[复制] {final_name}")
                ok += 1
                continue

            is_vertical = key in VERTICAL_ATLASES
            cmd = ["python", str(fix_script), str(src), str(dst)]
            if is_vertical:
                cmd.append("--vertical")
            if args.sharpen:
                cmd.append("--sharpen")

            tag = "[V]" if is_vertical else "   "
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                lines = [l for l in result.stdout.strip().splitlines()
                         if l.startswith("  折") or l.startswith("✓")]
                crease = next((l for l in lines if "折痕" in l), "无折痕")
                print(f"{tag}    {final_name:20s}  {crease}")
                ok += 1
            else:
                print(f"✗      {final_name}  ({fn})")
                print(result.stderr[-400:])
                fail += 1

    print(f"\n完成: {ok} 张输出（含 {sum(1 for k in no_spine if FINAL_NAMES.get(k)) } 张单页复制），{skipped} 张跳过，{fail} 张失败")
    print(f"输出目录: {out_dir}")


if __name__ == "__main__":
    main()
