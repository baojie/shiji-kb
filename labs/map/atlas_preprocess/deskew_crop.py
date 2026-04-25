#!/usr/bin/env python3
"""
deskew_crop.py — 倾斜纠正 + 边缘裁切

适用于书籍扫描地图的后处理：
  1. 边缘裁切：去除扫描时产生的黑色/深色边缘条（装订阴影等）
  2. 倾斜纠正：通过检测地图框线角度旋转校正扫描倾斜

用法：
  python deskew_crop.py input.jpg [output.jpg]          # 单张处理
  python deskew_crop.py --batch corpus/谭图/1-0*.jpg   # 批量原地处理
  python deskew_crop.py --crop-only input.jpg           # 仅裁切
  python deskew_crop.py --deskew-only input.jpg         # 仅纠偏
  python deskew_crop.py --dry-run --batch ...           # 仅打印检测结果
"""

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d


# ── 边缘裁切 ─────────────────────────────────────────────────────────────────

def _find_strip_width_frac(dark_fracs: np.ndarray, frac_thresh: float, max_strip: int) -> int:
    """
    用暗像素比例（< 100 的像素占该行/列总像素数）检测边缘暗条宽度。
    处理非均匀暗条（均值高但局部极暗），取前 max_strip 中最后一个超阈值位置后一位。
    """
    vals = dark_fracs[:max_strip]
    dark_positions = [i for i, v in enumerate(vals) if v >= frac_thresh]
    if not dark_positions:
        return 0
    last_dark = dark_positions[-1]
    if last_dark >= max_strip - 1:
        return max_strip
    return last_dark + 1


def _find_blank_bottom(gray: np.ndarray, min_blank: int = 50,
                        content_frac: float = 0.01) -> int:
    """
    从底部向上扫描，找内容结束位置。
    若底部连续空白行 >= min_blank，返回应裁掉的行数；否则返回 0。
    content_frac：某行暗像素占比超过此值即视为有内容（默认 0.5%）。
    """
    h, w = gray.shape
    last_content = h - 1
    for i in range(1, h):
        if (gray[h - i, :] < 180).mean() > content_frac:
            last_content = h - i
            break
    blank = h - last_content - 1
    return blank if blank >= min_blank else 0


def autocrop(arr: np.ndarray,
             dark_thresh: float = 130.0,
             dark_frac_thresh: float = 0.05,
             max_strip: int = 8,
             min_blank_bottom: int = 100) -> tuple[np.ndarray, tuple]:
    """
    检测并裁切四边的扫描暗条和底部大面积空白。

    双重检测暗条：均值法（dark_thresh）+ 暗像素比例法（dark_frac_thresh）。
    额外检测：底部连续空白 >= min_blank_bottom 行时自动裁除（半页图留白场景）。

    返回 (cropped_arr, (top, bot, left, right)) 裁切像素数。
    """
    h, w = arr.shape[:2]
    gray = arr.mean(axis=2)

    # ── 均值法（边缘暗条）
    top_means  = gray[:max_strip, :].mean(axis=1)
    bot_means  = gray[h-max_strip:, :].mean(axis=1)[::-1]
    left_means = gray[:, :max_strip].mean(axis=0)
    right_means= gray[:, w-max_strip:].mean(axis=0)[::-1]

    def _find_by_mean(means):
        vals = means[:max_strip]
        dark_pos = [i for i, v in enumerate(vals) if v <= dark_thresh]
        if not dark_pos:
            return 0
        last = dark_pos[-1]
        return max_strip if last >= max_strip - 1 else last + 1

    top_m   = _find_by_mean(top_means)
    bot_m   = _find_by_mean(bot_means)
    left_m  = _find_by_mean(left_means)
    right_m = _find_by_mean(right_means)

    # ── 暗像素比例法（< 100）
    top_fracs   = (gray[:max_strip, :] < 100).mean(axis=1)
    bot_fracs   = (gray[h-max_strip:, :] < 100).mean(axis=1)[::-1]
    left_fracs  = (gray[:, :max_strip] < 100).mean(axis=0)
    right_fracs = (gray[:, w-max_strip:] < 100).mean(axis=0)[::-1]

    top_f   = _find_strip_width_frac(top_fracs,   dark_frac_thresh, max_strip)
    bot_f   = _find_strip_width_frac(bot_fracs,   dark_frac_thresh, max_strip)
    left_f  = _find_strip_width_frac(left_fracs,  dark_frac_thresh, max_strip)
    right_f = _find_strip_width_frac(right_fracs, dark_frac_thresh, max_strip)

    top   = max(top_m,   top_f)
    bot   = max(bot_m,   bot_f)
    left  = max(left_m,  left_f)
    right = max(right_m, right_f)

    # ── 底部大面积空白（半页图留白，仅裁 >= min_blank_bottom 的连续空白）
    blank_bot = _find_blank_bottom(gray, min_blank=min_blank_bottom)
    bot = max(bot, blank_bot)

    r0 = top
    r1 = h - bot   if bot   > 0 else h
    c0 = left
    c1 = w - right if right > 0 else w

    return arr[r0:r1, c0:c1], (top, bot, left, right)


# ── 倾斜角检测（地图框线斜率法）──────────────────────────────────────────────

def detect_skew_angle(arr: np.ndarray,
                      search_frac: float = 0.35,
                      min_dark_frac: float = 0.10,
                      outlier_thresh: float = 8.0) -> float:
    """
    通过检测地图上边框线的倾斜角来估算扫描偏角。

    方法：
      1. 在顶部 search_frac 区域找暗像素密集的框线带（dark_count > 10% * width）
      2. 在框线带范围内，逐列向下扫描，记录每列首个暗像素的 y 位置（框线顶边）
      3. 线性拟合去离群值，返回斜率对应角度（°）

    正角度 = 右侧偏低（框线斜率 > 0），需逆时针旋转纠正。
    返回 0.0 表示检测失败或倾斜可忽略。
    """
    gray = arr.mean(axis=2)
    h, w = gray.shape
    search_end = int(h * search_frac)
    sub = gray[:search_end, :]

    dark_count = (sub < 100).sum(axis=1)
    min_dark = int(w * min_dark_frac)
    candidates = np.where(dark_count > min_dark)[0]

    if len(candidates) == 0:
        return 0.0

    # 框线带：第一个候选行前 10 行到最后一个候选行后 10 行
    band_top    = max(0, candidates[0] - 10)
    band_bottom = min(search_end, candidates[-1] + 10)

    sample_cols = list(range(50, w - 50, 40))
    if len(sample_cols) < 10:
        return 0.0

    # 每列在框线带内找第一个暗像素（框线顶边）
    top_ys = []
    valid_cols = []
    for c in sample_cols:
        col_slice = gray[band_top:band_bottom, c]
        dark_pos = np.where(col_slice < 100)[0]
        if len(dark_pos) > 0:
            top_ys.append(band_top + dark_pos[0])
            valid_cols.append(c)

    if len(valid_cols) < 10:
        return 0.0

    xs = np.array(valid_cols, dtype=float)
    ys = np.array(top_ys, dtype=float)

    y_med = np.median(ys)
    valid = np.abs(ys - y_med) < outlier_thresh
    if valid.sum() < 5:
        return 0.0

    slope, _ = np.polyfit(xs[valid], ys[valid], 1)
    angle = float(np.degrees(np.arctan(slope)))

    if abs(angle) > 5.0:
        return 0.0

    return angle


# ── 旋转（PIL，双线性，背景填白）────────────────────────────────────────────────

def deskew(arr: np.ndarray, angle: float) -> np.ndarray:
    """
    将图像旋转 angle 度（逆时针）纠正倾斜，背景填充白色。

    angle > 0 = 右侧偏低 → 逆时针旋转（PIL rotate 正值 = 逆时针）
    angle < 0 = 右侧偏高 → 顺时针旋转
    """
    img = Image.fromarray(arr)
    rotated = img.rotate(angle, resample=Image.BILINEAR, expand=False, fillcolor=(255, 255, 255))
    return np.array(rotated)


# ── 主处理函数 ────────────────────────────────────────────────────────────────

def process(src: str, dst: str,
            do_deskew: bool = True,
            do_crop: bool = True,
            dry_run: bool = False,
            verbose: bool = True) -> dict:
    """
    对单张图像执行倾斜纠正 + 边缘裁切。
    返回包含检测结果的 dict。
    """
    arr = np.array(Image.open(src).convert("RGB"))
    h0, w0 = arr.shape[:2]
    result = {"file": src, "angle": 0.0, "crop": (0, 0, 0, 0)}

    # ── 1. 倾斜检测与纠正
    if do_deskew:
        angle = detect_skew_angle(arr)
        result["angle"] = angle
        if abs(angle) >= 0.05:
            if verbose:
                print(f"  倾斜: {angle:+.3f}°  →  旋转纠正")
            if not dry_run:
                arr = deskew(arr, angle)
        else:
            if verbose:
                print(f"  倾斜: {angle:+.3f}°  (可忽略，跳过)")

    # ── 2. 边缘裁切
    if do_crop:
        arr_cropped, (top, bot, left, right) = autocrop(arr)
        result["crop"] = (top, bot, left, right)
        h1, w1 = arr_cropped.shape[:2]
        if top + bot + left + right > 0:
            if verbose:
                print(f"  裁切: top={top} bot={bot} left={left} right={right}  {w0}×{h0} → {w1}×{h1}")
            if not dry_run:
                arr = arr_cropped
        else:
            if verbose:
                print(f"  无边缘暗条，跳过裁切")

    if not dry_run:
        Image.fromarray(arr).save(dst, "JPEG", quality=95, subsampling=0)
        if verbose:
            print(f"  ✓ → {dst}")

    return result


# ── 入口 ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("input",  nargs="?", help="输入 JPG（单张模式）")
    ap.add_argument("output", nargs="?", help="输出 JPG（默认原地覆盖）")
    ap.add_argument("--batch",       nargs="+", metavar="GLOB", help="批量处理（原地）")
    ap.add_argument("--crop-only",   action="store_true", help="仅裁切，不纠偏")
    ap.add_argument("--deskew-only", action="store_true", help="仅纠偏，不裁切")
    ap.add_argument("--dry-run",     action="store_true", help="仅检测，不写文件")
    args = ap.parse_args()

    do_deskew = not args.crop_only
    do_crop   = not args.deskew_only

    if args.batch:
        files = []
        for pat in args.batch:
            files.extend(sorted(glob.glob(pat)))
        files = sorted(set(files))
        if not files:
            print("未找到匹配文件")
            sys.exit(1)
        print(f"批量处理 {len(files)} 张图像...")
        for f in files:
            print(f"\n[{Path(f).name}]")
            process(f, f, do_deskew=do_deskew, do_crop=do_crop, dry_run=args.dry_run)

    elif args.input:
        dst = args.output or args.input
        process(args.input, dst, do_deskew=do_deskew, do_crop=do_crop, dry_run=args.dry_run)

    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
