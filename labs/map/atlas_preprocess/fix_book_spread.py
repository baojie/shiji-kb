#!/usr/bin/env python3
"""
fix_book_spread.py — 书籍跨页几何形变校正（基于亮度场）

物理模型：
  书页在中脊处弯曲（圆柱模型）。弯曲角 φ(x) 同时导致：
    1. 横向投影压缩：实际宽度 → 投影宽度乘以 cos(φ)
    2. 反射光减弱：亮度乘以 cos(φ)
  两者同比，因此：
    s(x) = I_ref / I(x)          拉伸系数（= 亮度修正系数）

  其中 I(x) 为第 x 列的平均亮度，I_ref 为无弯曲区域的参考亮度。

用法：
  python fix_book_spread.py <input.jpg> [output.jpg]
  python fix_book_spread.py <input.jpg> --debug
  python fix_book_spread.py <input.jpg> --s-max 1.6   # 限制最大拉伸系数
"""

import argparse
import numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import gaussian_filter1d, map_coordinates


# ── 拉伸场计算 ────────────────────────────────────────────────────────────────

def compute_stretch_field(gray: np.ndarray,
                          smooth_sigma: float = 20.0,
                          s_max: float = 2.0,
                          ref_frac: float = 0.20) -> tuple[np.ndarray, float]:
    """
    由灰度图的列均值计算每列拉伸系数 s(x) = I_ref / I(x)。

    策略：
    1. 用极大平滑（sigma=80）估算背景包络（慢变化趋势）
    2. 书脊阴影 = 包络与实测列均值之间的差（突然变暗）
    3. 只对突然变暗超过 3% 的区域施加拉伸，避免地图内容暗色被误校正

    参数：
      smooth_sigma  书脊阴影检测的平滑半径（px，默认 20）
      s_max         拉伸系数上限
      ref_frac      两端参考区域比例（用于估算全局 I_ref）

    返回 (s_field, I_ref)
    """
    h, w = gray.shape
    col_mean = gray.mean(axis=0)

    # 检测书脊中心：在图像中央50%区域找列均值最暗处
    cx0, cx1 = int(w * 0.25), int(w * 0.75)
    cx = cx0 + int(np.argmin(
        gaussian_filter1d(col_mean[cx0:cx1], sigma=20)
    ))

    # 参考亮度：书脊两侧各取 5~17% 宽度区域的中位数
    ref_half = int(w * 0.12)
    ref_margin = int(w * 0.05)
    left_ref  = col_mean[ref_margin:ref_margin + ref_half]
    right_ref = col_mean[w - ref_margin - ref_half:w - ref_margin]
    I_ref = float(np.median(np.concatenate([left_ref, right_ref])))

    # 平滑列均值（抑制逐列地图内容噪声，但保留书脊宽带阴影）
    col_smooth = gaussian_filter1d(col_mean, sigma=smooth_sigma)

    # 拉伸系数（仅基于亮度比值）
    s_raw = I_ref / np.clip(col_smooth, I_ref * 0.3, None)
    s_raw = np.clip(s_raw, 1.0, s_max)

    # 空间限制：只在书脊中心 ±win_half 范围内施加校正
    # 书脊阴影宽约 60-70px，窗口设为 ±160px（覆盖约 ±2.5 格网周期）
    win_half = int(w * 0.08)
    xs = np.arange(w)
    dist = np.abs(xs - cx)
    hann = np.where(
        dist < win_half,
        0.5 * (1 + np.cos(np.pi * dist / win_half)),
        0.0,
    )
    # 校正量 = (s_raw - 1) * hann，使得边界处校正为 0
    s = 1.0 + (s_raw - 1.0) * hann
    s = gaussian_filter1d(s, sigma=smooth_sigma * 0.5)

    return s, I_ref


# ── 坐标映射 ──────────────────────────────────────────────────────────────────

def build_coord_map(s: np.ndarray) -> tuple[np.ndarray, int]:
    """
    由拉伸场 s(x) 建立输出列 → 源列映射。

    正向累积：out(x) = ∫₀ˣ s(t) dt
    反向插值：对每个输出列 x_out 查找对应的源列 x_src
    """
    w = len(s)
    cumsum = np.concatenate([[0.0], np.cumsum(s)])  # shape (w+1,)
    W_out = int(np.ceil(cumsum[-1]))

    x_out = np.arange(W_out, dtype=float) + 0.5
    x_src = np.interp(x_out, cumsum, np.arange(w + 1, dtype=float))
    x_src = np.clip(x_src, 0, w - 1)
    return x_src, W_out


# ── 残余暗线修复（书脊折痕插值填充）────────────────────────────────────────────

def inpaint_spine_line(arr: np.ndarray, cx: int = -1,
                       axis: int = 1,
                       verbose: bool = True) -> np.ndarray:
    """
    只修复书脊物理折痕产生的极窄暗线（1~8px），不动周围已校正的区域。

    检测方法：局部比较，而非全局阈值。
      每列/行与其紧邻 ±neighbor_half 内的均值比较，
      只有比邻居暗 local_thresh 以上的才算折痕线。
      这样只找到真正的折痕，而不是整个阴影带。

    参数：
      cx    书脊中心坐标（在 axis 方向）；-1 则自动检测
      axis  1 = 竖向书脊（按列处理），0 = 横向书脊（按行处理）
    """
    arr = arr.copy()
    h, w = arr.shape[:2]

    # 将问题统一到"按列"处理：axis=0（横脊）时转置
    if axis == 0:
        arr = np.transpose(arr, (1, 0, 2))
        h, w = arr.shape[:2]
        cx_use = cx  # cx 已是转置后的列坐标

    # 列均值
    col_mean = arr.mean(axis=2).mean(axis=0).astype(float)

    # 书脊中心
    if cx < 0:
        mid0, mid1 = int(w * 0.25), int(w * 0.75)
        cx_use = mid0 + int(np.argmin(gaussian_filter1d(col_mean[mid0:mid1], sigma=5)))
    else:
        cx_use = cx

    # 搜索范围：书脊中心 ±25px
    search_half = 25
    x0 = max(1, cx_use - search_half)
    x1 = min(w - 1, cx_use + search_half)

    # 局部比较：每列与其 ±15px 邻居均值之差
    neighbor_half = 15
    local_bg = gaussian_filter1d(col_mean, sigma=neighbor_half)
    local_dark = local_bg - col_mean  # 正值 = 比邻居暗

    # 折痕线判定：局部暗度 > 12 灰度值（约 5%），且在搜索范围内
    local_thresh = 12.0
    crease_mask = np.zeros(w, bool)
    crease_mask[x0:x1] = local_dark[x0:x1] > local_thresh

    if not crease_mask.any():
        if verbose:
            print("  未检测到折痕暗线，跳过")
        if axis == 0:
            arr = np.transpose(arr, (1, 0, 2))
        return arr

    # 合并连续暗列（间距≤2）
    cols = np.where(crease_mask)[0]
    regions = []
    start = prev = cols[0]
    for c in cols[1:]:
        if c - prev <= 2:
            prev = c
        else:
            regions.append((start, prev))
            start = prev = c
    regions.append((start, prev))

    if verbose:
        tag = "行" if axis == 0 else "列"
        for a, b in regions:
            print(f"  折痕: {tag}={a}~{b} ({b-a+1}px)  局部暗度={local_dark[a:b+1].mean():.1f}")

    # 修复：左半用左邻锚，右半用右邻锚（各取紧邻 5px 均值，保持原侧内容）
    anchor_w = 5
    for x_left, x_right in regions:
        left_anchor  = arr[:, max(0, x_left - anchor_w):x_left].astype(float).mean(axis=1)
        right_anchor = arr[:, x_right + 1:min(w, x_right + 1 + anchor_w)].astype(float).mean(axis=1)

        xmid = (x_left + x_right) / 2.0
        for x in range(x_left, x_right + 1):
            t = (x - xmid) / max(1, x_right - x_left) + 0.5  # 0→1
            t = max(0.0, min(1.0, t))
            col = (1 - t) * left_anchor + t * right_anchor
            arr[:, x] = np.clip(col, 0, 255).astype(np.uint8)

    if axis == 0:
        arr = np.transpose(arr, (1, 0, 2))
    return arr


# ── 去噪 + 锐化 ──────────────────────────────────────────────────────────────

def enhance_text(arr: np.ndarray,
                 amount: float = 1.5,
                 radius: float = 1.5) -> np.ndarray:
    """
    文字线条增强（非锐化掩模，无去噪）。

    原理：USM = 原图 + amount × (原图 - 高斯模糊(原图, radius))
      radius 控制增强的"笔画宽度"：
        - 1.5px → 突出笔画主体，线条平滑
        - 0.5px → 强调像素级边缘，易放大噪点
      amount 控制增强强度（1.5 为适度）。
    """
    from scipy.ndimage import gaussian_filter
    out = arr.astype(float)
    blurred = np.empty_like(out)
    for c in range(out.shape[2]):
        blurred[:, :, c] = gaussian_filter(out[:, :, c], sigma=radius)
    out = out + amount * (out - blurred)
    return np.clip(out, 0, 255).astype(np.uint8)


# ── 重采样 + 亮度修正 ─────────────────────────────────────────────────────────

def apply_correction(arr: np.ndarray,
                     x_src: np.ndarray,
                     s_field: np.ndarray) -> np.ndarray:
    """
    按 x_src 映射重采样（双三次），并对每输出列乘以 s(src_x)（亮度修正）。
    """
    h = arr.shape[0]
    W_out = len(x_src)

    y_grid = np.tile(np.arange(h, dtype=float)[:, None], (1, W_out))
    x_grid = np.tile(x_src[None, :],                      (h, 1))

    # 每输出列对应的亮度系数（由源列插值得到）
    s_out = np.interp(x_src, np.arange(len(s_field)), s_field)

    result = np.empty((h, W_out, arr.shape[2]), dtype=np.uint8)
    for c in range(arr.shape[2]):
        warped = map_coordinates(
            arr[:, :, c].astype(float),
            [y_grid.ravel(), x_grid.ravel()],
            order=3, mode='nearest', prefilter=True,
        ).reshape(h, W_out)
        brightened = warped * s_out[None, :]
        result[:, :, c] = np.clip(brightened, 0, 255).astype(np.uint8)

    return result


# ── 主流程 ────────────────────────────────────────────────────────────────────

def fix_spread(img_path: str, out_path: str,
               smooth_sigma: float = 8.0,
               s_max: float = 2.0,
               vertical: bool = False,
               sharpen: bool = False,
               sharpen_amount: float = 0.8,
               sharpen_radius: float = 1.5,
               debug: bool = False,
               verbose: bool = True) -> None:

    img = Image.open(img_path)
    arr = np.array(img)

    # 横向中脊：转置后用同一套水平校正逻辑，完成后再转置回来
    if vertical:
        arr = np.transpose(arr, (1, 0, 2))

    h, w = arr.shape[:2]
    gray = arr.mean(axis=2).astype(float)

    s_field, I_ref = compute_stretch_field(
        gray, smooth_sigma=smooth_sigma, s_max=s_max
    )

    s_peak  = float(np.max(s_field))
    cx_src  = int(np.argmax(s_field))   # 书脊在源图中的列
    W_out   = int(np.ceil(np.sum(s_field)))

    if verbose:
        print(f"参考亮度: {I_ref:.1f}")
        print(f"最大拉伸: s={s_peak:.4f}  位于 x={cx_src}")
        print(f"输出宽度: {w} → {W_out}px  (+{W_out-w}px, +{(W_out-w)/w*100:.1f}%)")

    if s_peak < 1.005:
        if verbose:
            print("拉伸量极小，跳过校正，直接复制")
        arr_out = arr
        cx_out  = cx_src
    else:
        x_src, _ = build_coord_map(s_field)
        arr_out = apply_correction(arr, x_src, s_field)
        # 书脊在输出图中的列（正向映射：累积和中 cx_src 对应的输出位置）
        cumsum = np.concatenate([[0.0], np.cumsum(s_field)])
        cx_out = int(cumsum[cx_src])

    if vertical:
        arr_out = np.transpose(arr_out, (1, 0, 2))

    # 修复校正后残余的书脊折痕暗线（仅在书脊中心附近搜索）
    spine_axis = 0 if vertical else 1
    arr_out = inpaint_spine_line(arr_out, cx=cx_out, axis=spine_axis, verbose=verbose)

    if sharpen:
        if verbose:
            print(f"文字增强: 强度={sharpen_amount}  半径={sharpen_radius}px")
        arr_out = enhance_text(arr_out,
                               amount=sharpen_amount,
                               radius=sharpen_radius)

    Image.fromarray(arr_out).save(out_path, "JPEG", quality=95, subsampling=0)

    if verbose:
        print(f"✓ 输出: {out_path}")

    if debug:
        _save_debug(gray, s_field, I_ref, cx, out_path)


def _save_debug(gray, s_field, I_ref, cx, out_path):
    """打印拉伸场统计。"""
    w = len(s_field)
    col_mean = gray.mean(axis=0)
    print("\n  列      亮度I(x)   拉伸s(x)")
    sample_xs = sorted(set(
        list(range(0, w, w // 12)) + [cx]
    ))
    for x in sample_xs:
        if x < w:
            print(f"  x={x:<5d}  {col_mean[x]:6.1f}    {s_field[x]:.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input",  help="输入JPG路径")
    ap.add_argument("output", nargs="?", help="输出JPG路径（默认覆盖输入）")
    ap.add_argument("--debug",           action="store_true")
    ap.add_argument("--smooth",          type=float, default=8.0,  help="列均值平滑σ（默认8）")
    ap.add_argument("--s-max",           type=float, default=2.0,  help="最大拉伸系数上限（默认2.0）")
    ap.add_argument("--vertical",        action="store_true",       help="横向中脊（竖版双页图）")
    ap.add_argument("--sharpen",         action="store_true",       help="启用文字线条增强（USM）")
    ap.add_argument("--sharpen-amount",  type=float, default=0.8,  help="增强强度（默认0.8）")
    ap.add_argument("--sharpen-radius",  type=float, default=1.5,  help="笔画宽度半径px（默认1.5）")
    args = ap.parse_args()

    out = args.output or args.input
    fix_spread(args.input, out,
               smooth_sigma=args.smooth, s_max=args.s_max,
               vertical=args.vertical,
               sharpen=args.sharpen,
               sharpen_amount=args.sharpen_amount,
               sharpen_radius=args.sharpen_radius,
               debug=args.debug)
