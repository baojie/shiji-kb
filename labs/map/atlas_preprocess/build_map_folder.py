#!/usr/bin/env python3
"""
build_map_folder.py

1. 从 output/jpg/ 中读取地图 JPG（已旋转），自动检测地图内容边界后裁剪，
   只保留地图主体（去除页眉/页脚/白边），输出到 map/ 目录。

2. 读取 output/place_index_corrected.json，生成地名→图上像素坐标的映射表
   map/place_coords.json：
     { "name": [ { "vol", "atlas", "map_name", "period", "row", "col",
                   "grid_rows", "grid_cols",
                   "px", "py",       ← 裁剪图上的像素坐标（中心点）
                   "px_norm", "py_norm"  ← 归一化坐标 [0,1]
                   "image_file" } ] }

输出目录：labs/atlas_preprocess/map/
  - {vol}-{atlas}_{map_name}.jpg   裁剪后的地图图片
  - place_coords.json              地名坐标映射
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

import numpy as np
from PIL import Image

# ── 路径配置 ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
OUT_DIR    = SCRIPT_DIR / "output"        # symlink → 版权数据目录
JPG_DIR    = OUT_DIR / "jpg"
MAP_DIR    = SCRIPT_DIR / "map"
INDEX_JSON = OUT_DIR / "place_index_corrected.json"

VOL_DIRS = {
    "vol1": JPG_DIR / "vol1_先秦_maps",
    "vol2": JPG_DIR / "vol2_秦汉_maps",
}

MAP_DIR.mkdir(exist_ok=True)


# ── 倾斜角度检测 ────────────────────────────────────────────────────────────
def detect_skew_angle(img: Image.Image) -> float:
    """
    用地图边框线检测倾斜角度（度）。
    策略：在图像顶部20%和底部20%各采样80列，找最暗像素位置，
    线性拟合得到斜率，再换算为角度。
    顶底两条边框角度若吻合（差值<0.4°）则取均值，否则取顶边。
    超过1.5°视为检测失败返回0.0。
    """
    arr = np.array(img.convert("L"))
    h, w = arr.shape
    n_cols = 80
    cols = np.linspace(int(w * 0.05), int(w * 0.95), n_cols, dtype=int)

    def find_border_pts(search_slice):
        pts = []
        for col in cols:
            strip = arr[search_slice, max(0, col - 3):min(w, col + 4)].mean(axis=1)
            y_local = int(np.argmin(strip))
            if float(strip[y_local]) < 160:
                pts.append((col, search_slice.start + y_local))
        return pts

    def angle_from_pts(pts):
        if len(pts) < 20:
            return None
        xs = np.array([p[0] for p in pts], float)
        ys = np.array([p[1] for p in pts], float)
        # 用众数附近±8px过滤：去掉书页边缘/装订暗影造成的离群点
        y_median = float(np.median(ys))
        mode_mask = np.abs(ys - y_median) < 8
        if mode_mask.sum() < 10:
            # 如果±8px太严，退回到2σ过滤
            mode_mask = np.abs(ys - y_median) < 2 * np.std(ys)
        xs, ys = xs[mode_mask], ys[mode_mask]
        if len(xs) < 10:
            return None
        slope = float(np.polyfit(xs, ys, 1)[0])
        a = float(np.degrees(np.arctan(slope)))
        return -a if abs(a) <= 2.0 else None

    top_pts = find_border_pts(slice(0, h // 5))
    bot_pts = find_border_pts(slice(4 * h // 5, h))
    top_angle = angle_from_pts(top_pts)
    bot_angle = angle_from_pts(bot_pts)

    if top_angle is None and bot_angle is None:
        return 0.0
    if top_angle is None:
        angle = bot_angle
    elif bot_angle is None:
        angle = top_angle
    elif abs(top_angle - bot_angle) < 0.4:
        angle = (top_angle + bot_angle) / 2
    else:
        angle = top_angle  # 顶边通常更可靠

    # 超过1.5°可能是误检（地图内容干扰），保守起见跳过
    if abs(angle) > 1.5:
        return 0.0
    return round(angle, 3)


# ── 自动检测地图内容边界 ─────────────────────────────────────────────────────
def detect_map_bbox(arr: np.ndarray) -> tuple[int, int, int, int]:
    """
    在灰度图像中找地图边框线（最外层的连续暗线），返回 (left, top, right, bottom)。
    这些边界是地图框架外缘，裁剪时取框架内侧（+3px padding）。
    """
    h, w = arr.shape
    row_mean = arr.mean(axis=1)
    col_mean = arr.mean(axis=0)

    # 从顶部向下找第一条暗行（mean < 195），跳过最顶的1-5行（页面装订黑线）
    top = 0
    for i in range(4, h // 2):
        if row_mean[i] < 195:
            top = i
            break

    # 从底部向上找最后一条暗行（mean < 180）
    bot = h - 1
    for i in range(h - 2, h // 2, -1):
        if row_mean[i] < 180:
            bot = i
            break

    # 从左向右找第一条暗列（mean < 210）
    left = 0
    for i in range(w // 10):
        if col_mean[i] < 210:
            left = i
            break

    # 从右向左
    right = w - 1
    for i in range(w - 1, w * 9 // 10, -1):
        if col_mean[i] < 210:
            right = i
            break

    # 若检测失败则用保守固定值
    if top > h // 3:
        top = 85
    if bot < h * 2 // 3:
        bot = h - 3
    if left > w // 6:
        left = 95
    if right < w * 5 // 6:
        right = w - 95

    # 内缩 3px（去掉边框线本身）
    return left + 3, top + 3, right - 3, bot - 3


def crop_map(img_path: Path) -> tuple[Image.Image, int, int, int, int, float]:
    """返回 (裁剪图, left, top, right, bottom, skew_angle)。先纠偏再裁剪。"""
    img = Image.open(img_path)

    # 纠偏：检测倾斜角并旋转（跳过极小角度避免不必要的重采样）
    angle = detect_skew_angle(img)
    if abs(angle) >= 0.05:
        img = img.rotate(-angle, resample=Image.BICUBIC, expand=False,
                         fillcolor=(255, 255, 255))

    arr = np.array(img.convert("L"))
    left, top, right, bot = detect_map_bbox(arr)
    cropped = img.crop((left, top, right + 1, bot + 1))
    return cropped, left, top, right, bot, angle


# ── 从 manifest 建立 atlas→地图名称 映射 ──────────────────────────────────────
def load_manifest_map() -> dict:
    result = {}
    for vol, fname in [("vol1", "vol1_先秦_manifest.json"), ("vol2", "vol2_秦汉_manifest.json")]:
        mf = json.loads((OUT_DIR / fname).read_text(encoding="utf-8"))
        for m in mf:
            result[(vol, m["atlas"])] = {
                "name":    m["name"],
                "is_crop": m.get("crop_top_half", False),
            }
    return result


# ── JPG 文件名 → atlas 编号 ────────────────────────────────────────────────
def filename_to_atlas(fn: str) -> str:
    """从文件名 '22-23_晋_秦.jpg' 提取 atlas='22-23'。"""
    m = re.match(r"^(\d+(?:-\d+)?)_", fn)
    return m.group(1) if m else ""


# ── 估算网格尺寸 ─────────────────────────────────────────────────────────────
def estimate_grid(entries_for_atlas: list) -> tuple[int, int]:
    """
    从该 atlas 的索引条目估算网格行列数。
    用最大观测值 + 1（保留边缘余量）。
    """
    if not entries_for_atlas:
        return 8, 10
    max_row = max(e["row"] for e in entries_for_atlas)
    max_col = max(e["col"] for e in entries_for_atlas)
    # 至少保留 1 格余量
    return max(max_row + 1, 4), max(max_col + 1, 5)


# ── 主流程 ──────────────────────────────────────────────────────────────────
def run():
    manifest = load_manifest_map()

    # 读索引
    index_data = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    entries    = index_data["entries"]

    # 按 (vol, atlas) 分组
    atlas_entries = defaultdict(list)
    for e in entries:
        atlas_entries[(e["vol"], e["atlas"])].append(e)

    # 处理每张地图
    crop_info: dict = {}   # (vol, atlas) → { left, top, right, bot, grid_rows, grid_cols, image_file }
    processed = 0
    skipped   = 0

    for vol, vol_dir in VOL_DIRS.items():
        for fn in sorted(os.listdir(vol_dir)):
            if not fn.endswith(".jpg"):
                continue
            atlas = filename_to_atlas(fn)
            if not atlas:
                continue

            key = (vol, atlas)
            meta = manifest.get(key, {})
            map_name = meta.get("name", atlas)

            # 输出文件名
            safe_name = (
                map_name.replace(" ", "_").replace("/", "／")
                        .replace("（", "(").replace("）", ")")
                        .replace("、", "_")
            )
            out_fn   = f"{vol}-{atlas}_{safe_name}.jpg"
            out_path = MAP_DIR / out_fn

            src_path = vol_dir / fn
            try:
                cropped, left, top, right, bot, skew = crop_map(src_path)
                cropped.save(out_path, "JPEG", quality=95, subsampling=0)
                cw, ch = cropped.size

                atlas_ents = atlas_entries[key]
                grid_rows, grid_cols = estimate_grid(atlas_ents)

                crop_info[key] = {
                    "image_file": out_fn,
                    "map_name":   map_name,
                    "vol":        vol,
                    "atlas":      atlas,
                    "crop_box":   [left, top, right, bot],
                    "map_width":  cw,
                    "map_height": ch,
                    "grid_rows":  grid_rows,
                    "grid_cols":  grid_cols,
                }
                skew_str = f"  skew={skew:+.3f}°" if abs(skew) >= 0.05 else ""
                print(f"  ✓ {out_fn:55s} {cw}×{ch}  grid={grid_rows}×{grid_cols}{skew_str}")
                processed += 1
            except Exception as ex:
                print(f"  ✗ {fn}: {ex}")
                skipped += 1

    print(f"\n裁剪完成：{processed} 张，跳过 {skipped} 张")

    # ── 生成地名坐标映射 ──────────────────────────────────────────────────────
    place_coords: dict = {}

    for e in entries:
        key = (e["vol"], e["atlas"])
        ci  = crop_info.get(key)
        if ci is None:
            continue

        gr = ci["grid_rows"]
        gc = ci["grid_cols"]
        mw = ci["map_width"]
        mh = ci["map_height"]
        row, col = e["row"], e["col"]

        # 中心像素坐标（在裁剪图内）
        px_norm = (col - 0.5) / gc
        py_norm = (row - 0.5) / gr
        px = round(px_norm * mw)
        py = round(py_norm * mh)

        loc = {
            "vol":        e["vol"],
            "atlas":      e["atlas"],
            "map_name":   ci["map_name"],
            "period":     e["period"],
            "row":        row,
            "col":        col,
            "grid_rows":  gr,
            "grid_cols":  gc,
            "px":         px,
            "py":         py,
            "px_norm":    round(px_norm, 4),
            "py_norm":    round(py_norm, 4),
            "image_file": ci["image_file"],
        }

        name = e["name"]
        if name not in place_coords:
            place_coords[name] = []
        place_coords[name].append(loc)

    out_json = MAP_DIR / "place_coords.json"
    out_json.write_text(
        json.dumps({
            "total_places": len(place_coords),
            "total_locs":   sum(len(v) for v in place_coords.values()),
            "places":       place_coords,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n地名坐标：{len(place_coords)} 个地名，"
          f"{sum(len(v) for v in place_coords.values())} 条位置记录")
    print(f"✓ 输出 → {out_json}")


if __name__ == "__main__":
    print("构建 map/ 文件夹...")
    run()
