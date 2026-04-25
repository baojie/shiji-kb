#!/usr/bin/env python3
"""
从 PDF 中直接提取地图页的原始 JPEG，旋转后输出最高分辨率 JPG。

策略：
  - 全页地图：提取嵌入 JPEG → jpegtran 无损旋转 90°CW → 输出 landscape JPG
  - 小地图（crop_top_half）：用 Pillow 裁取上半部分后保存（保留原始质量）

输出：output/jpg/vol1_先秦_maps/*.jpg
         output/jpg/vol2_秦汉_maps/*.jpg
"""

import os, sys, subprocess, tempfile, json
from pathlib import Path
import fitz
from PIL import Image
import io

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BOOK_DIR    = os.path.join(_SCRIPT_DIR, "book")    # symlink
OUT_DIR     = os.path.join(_SCRIPT_DIR, "output")  # symlink
JPG_DIR     = os.path.join(OUT_DIR, "jpg")
JPG_QUALITY = 95          # Pillow 保存质量（仅裁切小图用到）
CROP_RATIO  = 0.56        # 混合页：取上 56% 高度

# 以竖版直接存入 PDF 的地图（无需旋转）
# 格式: (vol_short, atlas)
# 判断依据：PDF 原始图像中标题/图例/比例尺文字横向可读 → 竖版直存
# 相对地，横版旋转存储的地图（vol2-26 等）标题文字在 PDF 竖版中呈旋转状态
PORTRAIT_MAPS = {
    ("vol1", "5-6"),   # 原始社会早期遗址图（旧石器时代）：全页竖版
    ("vol1", "19"),    # 宗周、成周附近：半页竖版
    ("vol1", "28"),    # 北燕：半页竖版
    ("vol2", "21"),    # 东郡北海间诸郡：半页竖版
    ("vol2", "39"),    # 匈奴及邻族：半页竖版
    ("vol2", "46"),    # 颖川间诸郡：半页竖版（名为"东郡齐国间诸郡"）
    ("vol2", "67"),    # 鲜卑及邻族：半页竖版
    ("vol2", "22-23"), # 荆州刺史部（西汉）：全页竖版
    ("vol2", "24-25"), # 扬州刺史部（西汉）：全页竖版
    ("vol2", "47-48"), # 冀州刺史部（东汉）：全页竖版
    ("vol2", "49-50"), # 荆州刺史部（东汉）：全页竖版
    ("vol2", "51-52"), # 扬州刺史部（东汉）：全页竖版
    ("vol2", "59-60"), # 并州刺史部：全页竖版
    ("vol1", "45-46"), # 楚 越：全页竖版
}

# ── 读取两册地图清单 ────────────────────────────────────────────────────────

def load_manifests():
    manifests = {}
    for vol in ["vol1_先秦", "vol2_秦汉"]:
        mf_path = os.path.join(OUT_DIR, f"{vol}_manifest.json")
        with open(mf_path, encoding="utf-8") as f:
            manifests[vol] = json.load(f)
    return manifests

# ── 从 PDF 页面提取原始 JPEG 字节 ─────────────────────────────────────────

def extract_jpeg_bytes(doc: fitz.Document, pdf_page_1based: int) -> bytes:
    """提取页面上第一张嵌入图像的原始 JPEG 字节。"""
    page = doc[pdf_page_1based - 1]
    imgs = page.get_images(full=True)
    if not imgs:
        raise ValueError(f"页面 {pdf_page_1based} 无嵌入图像")
    xref = imgs[0][0]
    img_info = doc.extract_image(xref)
    if img_info["ext"] != "jpeg":
        # 非 JPEG（理论上不存在，但作为保底）
        pix = fitz.Pixmap(doc, xref)
        return bytes(pix.tobytes("jpeg", jpg_quality=JPG_QUALITY))
    return img_info["image"]

# ── 无损旋转（jpegtran）────────────────────────────────────────────────────

def rotate90ccw_lossless(jpeg_bytes: bytes) -> bytes:
    """用 jpegtran 对 JPEG 执行无损逆时针 90° 旋转（= jpegtran -rotate 270）。
    地图在 PDF 中以竖版存储，需逆时针旋转 90° 后北方朝上、东方朝右。
    """
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_in:
        tmp_in.write(jpeg_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path + "_rot.jpg"
    try:
        subprocess.run(
            ["jpegtran", "-rotate", "270", "-trim", "-outfile", tmp_out_path, tmp_in_path],
            check=True, capture_output=True,
        )
        with open(tmp_out_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.unlink(tmp_out_path)

# ── 裁切上半并保存（Pillow）───────────────────────────────────────────────

def crop_top_and_save(jpeg_bytes: bytes, out_path: str) -> tuple:
    """横版旋转存储的半页图：先90°CCW旋转还原横版，再裁左56%宽度。返回(w,h)。
    适用于 vol2-26 等少数横版旋转存储的半页图。"""
    img = Image.open(io.BytesIO(jpeg_bytes))
    img = img.rotate(90, expand=True)
    w, h = img.size
    crop_w = int(w * CROP_RATIO)
    cropped = img.crop((0, 0, crop_w, h))
    cropped.save(out_path, "JPEG", quality=JPG_QUALITY, subsampling=0)
    return crop_w, h

def crop_top_portrait_save(jpeg_bytes: bytes, out_path: str) -> tuple:
    """竖版直存的半页图：直接裁取上56%高度，无需旋转。返回(w,h)。
    适用于 vol1-19/28, vol2-21/39/46/67 等竖版存储的半页图。"""
    img = Image.open(io.BytesIO(jpeg_bytes))
    w, h = img.size
    crop_h = int(h * CROP_RATIO)
    cropped = img.crop((0, 0, w, crop_h))
    cropped.save(out_path, "JPEG", quality=JPG_QUALITY, subsampling=0)
    return w, crop_h

# ── 主流程 ──────────────────────────────────────────────────────────────────

def export_vol(vol_name: str, maps: list):
    # 确定对应的 PDF 文件
    if "vol1" in vol_name:
        pdf_file = "中国历史地图集++（精装本）1++第一册（先秦）.pdf"
    else:
        pdf_file = "中国历史地图集++（精装本）2++第二册（秦汉）.pdf"

    pdf_path = os.path.join(BOOK_DIR, pdf_file)
    doc = fitz.open(pdf_path)

    jpg_vol_dir = os.path.join(JPG_DIR, f"{vol_name}_maps")
    os.makedirs(jpg_vol_dir, exist_ok=True)

    print(f"\n[{vol_name}] → {jpg_vol_dir}")

    for m in maps:
        atlas_id  = m["atlas"]
        map_name  = m["name"]
        pno       = m["pdf_page"]
        is_crop   = m.get("crop_top_half", False)

        safe_name = (map_name
                     .replace(" ", "_").replace("/", "／")
                     .replace("（", "(").replace("）", ")")
                     .replace("、", "_"))
        out_name = f"{atlas_id}_{safe_name}.jpg"
        out_path = os.path.join(jpg_vol_dir, out_name)

        jpeg_bytes = extract_jpeg_bytes(doc, pno)

        vol_short = "vol1" if "vol1" in vol_name else "vol2"
        is_portrait = (vol_short, atlas_id) in PORTRAIT_MAPS

        if is_portrait and is_crop:
            # 竖版直存半页图：直接裁取上56%高度
            w, h = crop_top_portrait_save(jpeg_bytes, out_path)
            size_kb = os.path.getsize(out_path) // 1024
            print(f"  {out_name:50s} {w}×{h}px  {size_kb}KB  [竖版裁上半]")
        elif is_portrait:
            # 竖版直存全页图：无旋转，直接输出原始 JPEG
            with open(out_path, "wb") as f:
                f.write(jpeg_bytes)
            img = Image.open(out_path)
            w, h = img.size
            img.close()
            size_kb = len(jpeg_bytes) // 1024
            print(f"  {out_name:50s} {w}×{h}px  {size_kb}KB  [竖版直存]")
        elif is_crop:
            w, h = crop_top_and_save(jpeg_bytes, out_path)
            size_kb = os.path.getsize(out_path) // 1024
            print(f"  {out_name:50s} {w}×{h}px  {size_kb}KB  [裁上半]")
        else:
            rotated = rotate90ccw_lossless(jpeg_bytes)
            with open(out_path, "wb") as f:
                f.write(rotated)
            # 读取旋转后尺寸
            img = Image.open(out_path)
            w, h = img.size
            img.close()
            size_kb = len(rotated) // 1024
            print(f"  {out_name:50s} {w}×{h}px  {size_kb}KB")

    doc.close()
    count = len(maps)
    total_kb = sum(os.path.getsize(p) for p in Path(jpg_vol_dir).glob("*.jpg")) // 1024
    print(f"  ✓ {count} 张，合计 {total_kb//1024} MB")


if __name__ == "__main__":
    os.makedirs(JPG_DIR, exist_ok=True)
    manifests = load_manifests()

    for vol_name, maps in manifests.items():
        export_vol(vol_name, maps)

    print("\n✓ 全部完成")
    print(f"输出目录: {JPG_DIR}")
