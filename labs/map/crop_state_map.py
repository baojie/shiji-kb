#!/usr/bin/env python3
"""
crop_state_map.py

从谭图地图中裁出指定邦国/地点在特定朝代的区域，
生成适合 wiki 页面展示的小图。

用法:
  python labs/map/crop_state_map.py 齐国 战国
  python labs/map/crop_state_map.py --list         # 列出所有已定义的裁切
  python labs/map/crop_state_map.py --all          # 批量生成所有

输出: wiki/public/images/{period}-{state}.jpg
"""

import argparse
import sys
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).parent.parent.parent
ATLAS_DIR = REPO_ROOT / "corpus" / "谭图"
OUT_DIR   = REPO_ROOT / "wiki" / "public" / "images"

# ── 裁切定义表 ────────────────────────────────────────────────────────────────
# key: (state, period)
# atlas_file: corpus/谭图/ 下的文件名
# crop: [left, top, right, bottom] 归一化坐标（0.0–1.0）
# 坐标系：(0,0) = 图片左上角，(1,1) = 图片右下角
CROP_DEFS: dict[tuple[str, str], dict] = {

    # ── 战国七雄 ───────────────────────────────────────────────────────────────
    ("齐国", "战国"): {
        "atlas_file": "1-21_战国-齐鲁宋.jpg",
        "crop": [0.16, 0.05, 0.99, 0.57],
        "desc": "战国时期齐国（含山东半岛）",
    },
    ("临淄", "战国"): {
        "atlas_file": "1-21_战国-齐鲁宋.jpg",
        "crop": [0.33, 0.28, 0.60, 0.58],
        "desc": "战国时期临淄（齐国都城）及周边",
    },
    ("鲁国", "战国"): {
        "atlas_file": "1-21_战国-齐鲁宋.jpg",
        "crop": [0.16, 0.35, 0.75, 0.82],
        "desc": "战国时期鲁国",
    },
    ("宋国", "战国"): {
        "atlas_file": "1-21_战国-齐鲁宋.jpg",
        "crop": [0.05, 0.55, 0.65, 0.98],
        "desc": "战国时期宋国",
    },
    ("韩国", "战国"): {
        "atlas_file": "1-19_战国-韩魏.jpg",
        "crop": [0.05, 0.40, 0.60, 0.92],
        "desc": "战国时期韩国",
    },
    ("魏国", "战国"): {
        "atlas_file": "1-19_战国-韩魏.jpg",
        "crop": [0.20, 0.05, 0.85, 0.65],
        "desc": "战国时期魏国",
    },
    ("赵国", "战国"): {
        "atlas_file": "1-20_战国-赵中山.jpg",
        "crop": [0.05, 0.05, 0.85, 0.80],
        "desc": "战国时期赵国",
    },
    ("燕国", "战国"): {
        "atlas_file": "1-22_战国-燕.jpg",
        "crop": [0.05, 0.05, 0.95, 0.85],
        "desc": "战国时期燕国",
    },
    ("秦国", "战国"): {
        "atlas_file": "1-23_战国-秦蜀.jpg",
        "crop": [0.05, 0.05, 0.75, 0.70],
        "desc": "战国时期秦国",
    },
    ("楚国", "战国"): {
        "atlas_file": "1-24_战国-楚越.jpg",
        "crop": [0.05, 0.05, 0.90, 0.75],
        "desc": "战国时期楚国",
    },

    # ── 春秋诸侯 ───────────────────────────────────────────────────────────────
    ("齐国", "春秋"): {
        "atlas_file": "1-14_春秋-齐鲁.jpg",
        "crop": [0.15, 0.05, 0.98, 0.55],
        "desc": "春秋时期齐国",
    },
    ("鲁国", "春秋"): {
        "atlas_file": "1-14_春秋-齐鲁.jpg",
        "crop": [0.15, 0.38, 0.70, 0.85],
        "desc": "春秋时期鲁国",
    },

    # ── 全图（用于邦国主页） ────────────────────────────────────────────────────
    ("战国全图", "战国"): {
        "atlas_file": "1-17_战国-全图.jpg",
        "crop": [0.03, 0.05, 0.97, 0.92],
        "desc": "战国时期全图",
    },
    ("春秋全图", "春秋"): {
        "atlas_file": "1-11_春秋-全图.jpg",
        "crop": [0.03, 0.05, 0.97, 0.92],
        "desc": "春秋时期全图",
    },
}


def list_defs():
    """列出所有已定义的裁切。"""
    print(f"已定义 {len(CROP_DEFS)} 个裁切：")
    for (state, period), cfg in sorted(CROP_DEFS.items()):
        out_name = f"{period}-{state}.jpg"
        print(f"  {period}·{state:<10s}  {cfg['atlas_file']:<30s}  → {out_name}")


def crop_one(state: str, period: str, overwrite: bool = True) -> Path:
    """
    裁切单个邦国/地点地图。
    返回输出文件路径。
    """
    key = (state, period)
    if key not in CROP_DEFS:
        raise ValueError(f"未找到裁切定义: {period}·{state}\n"
                         f"已定义: {[f'{p}·{s}' for s, p in CROP_DEFS]}")

    cfg = CROP_DEFS[key]
    atlas_path = ATLAS_DIR / cfg["atlas_file"]
    if not atlas_path.exists():
        raise FileNotFoundError(f"地图文件不存在: {atlas_path}")

    out_name = f"{period}-{state}.jpg"
    out_path = OUT_DIR / out_name
    if out_path.exists() and not overwrite:
        print(f"  跳过（已存在）: {out_path}")
        return out_path

    img = Image.open(atlas_path)
    w, h = img.size
    l_n, t_n, r_n, b_n = cfg["crop"]
    box = (int(l_n * w), int(t_n * h), int(r_n * w), int(b_n * h))
    cropped = img.crop(box)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cropped.save(out_path, "JPEG", quality=90, subsampling=0)
    cw, ch = cropped.size
    print(f"  ✓ {out_name}  {cw}×{ch}  ({cfg['desc']})")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="从谭图裁出邦国地图小图")
    parser.add_argument("state",  nargs="?", help="邦国名称，如 齐国")
    parser.add_argument("period", nargs="?", help="朝代，如 战国")
    parser.add_argument("--list", action="store_true", help="列出所有定义")
    parser.add_argument("--all",  action="store_true", help="批量生成全部")
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args()

    if args.list:
        list_defs()
        return

    overwrite = not args.no_overwrite

    if args.all:
        ok, fail = 0, 0
        for (state, period) in CROP_DEFS:
            try:
                crop_one(state, period, overwrite=overwrite)
                ok += 1
            except Exception as e:
                print(f"  ✗ {period}·{state}: {e}")
                fail += 1
        print(f"\n完成：{ok} 成功，{fail} 失败")
        return

    if not args.state or not args.period:
        parser.print_help()
        sys.exit(1)

    out = crop_one(args.state, args.period, overwrite=overwrite)
    print(f"输出: {out}")


if __name__ == "__main__":
    main()
