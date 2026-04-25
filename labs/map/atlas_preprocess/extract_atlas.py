#!/usr/bin/env python3
"""
谭其骧《中国历史地图集》PDF 预处理脚本

任务1：提取地图页并正确旋转
  - 地图页在 PDF 中以竖版（portrait）存储，内容为逆时针旋转90°的横版地图
  - 提取时应用顺时针90°旋转，恢复为正确的横版显示
  - 单页小地图（宗周附近、东郡北海等）存储在"混合页"的上半部分，需裁切

任务2（另见 parse_index.py）：解析地名索引，获取地名→图幅→网格坐标映射

用法：
  python extract_atlas.py

输出目录（相对于脚本位置）：
  output/vol1_先秦_maps/   单张地图 PDF（旋转后）
  output/vol1_先秦_maps.pdf 合并地图 PDF
  output/vol1_先秦_index/  单张索引页 PDF
  output/vol1_先秦_index.pdf 合并索引 PDF
  output/vol1_先秦_manifest.json 页码映射清单
  output/vol2_秦汉_*  同上

结构说明：
  每册 atlas 页码 → PDF 页码 = atlas页码 + 偏移量
  偶数 atlas 页 = 地图页（标准规律）；奇数 atlas 页 = 标题/空白页
  单页奇数地图（如atlas19、21、39、67）触发"奇偶翻转"，其内容出现在下一偶数页的上半部分（混合页）
  单页偶数地图（如atlas28、26、46）不触发翻转，就是正常偶数地图页
"""

import fitz  # PyMuPDF
import os
import json

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BOOK_DIR    = os.path.join(_SCRIPT_DIR, "book")    # symlink
OUT_DIR     = os.path.join(_SCRIPT_DIR, "output")  # symlink

# ─────────────────────────────────────────────────────────────────────────────
# 第一册（先秦）配置
# PDF 92页，偏移 = 29，地图区 PDF 30-75，索引区 PDF 76-92
#
# 奇偶翻转记录：
#   atlas 19 (ODD单页) → 触发翻转 → atlas 20 = 混合页(宗周+label20-21)，atlas 21 = 春秋全图
#   atlas 28 (EVEN单页) → 触发翻转回 → atlas 29 = 混合页(北燕+label29-30)，atlas 30 = 楚吴越
# ─────────────────────────────────────────────────────────────────────────────
VOL1 = {
    "file": "中国历史地图集++（精装本）1++第一册（先秦）.pdf",
    "name": "vol1_先秦",
    "index_section_start": 76,
    "index_section_end": 92,
    "maps": [
        # Phase 1 (even=map): atlas 2,4,...18
        {"atlas": "1-2",  "pdf": 31, "name": "中华人民共和国全图"},
        {"atlas": "3-4",  "pdf": 33, "name": "原始社会遗址图"},
        {"atlas": "5-6",  "pdf": 35, "name": "原始社会早期遗址图（旧石器时代）"},
        {"atlas": "7-8",  "pdf": 37, "name": "黄河流域原始社会晚期遗址图（新石器时代）"},
        {"atlas": "9-10", "pdf": 39, "name": "夏时期全图"},
        {"atlas": "11-12","pdf": 41, "name": "商时期全图"},
        {"atlas": "13-14","pdf": 43, "name": "商时期中心区域图"},
        {"atlas": "15-16","pdf": 45, "name": "西周时期全图"},
        {"atlas": "17-18","pdf": 47, "name": "西周时期中心区域图"},
        # atlas 19 单ODD → 翻转，内容在 atlas 20 混合页(PDF 49)上半
        {"atlas": "19",   "pdf": 49, "name": "宗周、成周附近", "crop_top_half": True},
        # Phase 2 (odd=map): atlas 21,23,25,27
        {"atlas": "20-21","pdf": 50, "name": "春秋时期全图"},
        {"atlas": "22-23","pdf": 52, "name": "晋 秦"},
        {"atlas": "24-25","pdf": 54, "name": "郑 宋 卫"},
        {"atlas": "26-27","pdf": 56, "name": "齐 鲁"},
        # atlas 28 单EVEN → 翻转回，内容在 atlas 29 混合页(PDF 58)上半
        {"atlas": "28",   "pdf": 58, "name": "北燕", "crop_top_half": True},
        # Phase 3 (even=map): atlas 30,32,...46
        {"atlas": "29-30","pdf": 59, "name": "楚 吴 越"},
        {"atlas": "31-32","pdf": 61, "name": "战国时期全图"},
        {"atlas": "33-34","pdf": 63, "name": "诸侯形势图（公元前350年）"},
        {"atlas": "35-36","pdf": 65, "name": "韩 魏"},
        {"atlas": "37-38","pdf": 67, "name": "赵 中山"},
        {"atlas": "39-40","pdf": 69, "name": "齐 鲁 宋"},
        {"atlas": "41-42","pdf": 71, "name": "燕"},
        {"atlas": "43-44","pdf": 73, "name": "秦 蜀"},
        {"atlas": "45-46","pdf": 75, "name": "楚 越"},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# 第二册（秦汉）配置
# PDF 101页，偏移 = 13，地图区 PDF 14-80，索引区 PDF 81-101
#
# 奇偶翻转记录：
#   atlas 21 (ODD单页,东郡北海) → 翻转 → atlas 22=混合页(东郡北海+label22-23), atlas 23=荆州
#   atlas 26 (EVEN单页,冀州) → 翻转回 → atlas 27=混合页(冀州+label27-28), atlas 28=幽州
#   atlas 39 (ODD单页,匈奴) → 翻转 → atlas 40=混合页(匈奴+label40-41), atlas 41=东汉全图
#   atlas 46 (EVEN单页,颖川间) → 翻转回 → atlas 47=混合页(颖川+label47-48), atlas 48=冀州
#   atlas 67 (ODD单页,鲜卑) → 翻转 → atlas 68=混合页(鲜卑+index说明), atlas 68以后=索引
# ─────────────────────────────────────────────────────────────────────────────
VOL2 = {
    "file": "中国历史地图集++（精装本）2++第二册（秦汉）.pdf",
    "name": "vol2_秦汉",
    "index_section_start": 81,  # atlas 68 → PDF 81（含鲜卑混合页）
    "index_section_end": 101,
    "maps": [
        # Phase 1 (even=map): atlas 2,4,...20
        {"atlas": "1-2",  "pdf": 15, "name": "中华人民共和国全图"},
        {"atlas": "3-4",  "pdf": 17, "name": "秦时期全图"},
        {"atlas": "5-6",  "pdf": 19, "name": "关中诸郡"},
        {"atlas": "7-8",  "pdf": 21, "name": "山东南部诸郡"},
        {"atlas": "9-10", "pdf": 23, "name": "山东北部诸郡"},
        {"atlas": "11-12","pdf": 25, "name": "淮汉以南诸郡"},
        {"atlas": "13-14","pdf": 27, "name": "西汉时期全图"},
        {"atlas": "15-16","pdf": 29, "name": "司隶部（长安附近）"},
        {"atlas": "17-18","pdf": 31, "name": "并州、朔方刺史部"},
        {"atlas": "19-20","pdf": 33, "name": "兖豫青徐刺史部"},
        # atlas 21 单ODD(东郡北海) → 翻转，内容在 atlas 22 混合页(PDF 35)上半
        {"atlas": "21",   "pdf": 35, "name": "东郡北海间诸郡", "crop_top_half": True},
        # Phase 2 (odd=map): atlas 23,25
        {"atlas": "22-23","pdf": 36, "name": "荆州刺史部"},
        {"atlas": "24-25","pdf": 38, "name": "扬州刺史部"},
        # atlas 26 单EVEN(冀州) → 翻转回，内容在 atlas 27 混合页(PDF 40)上半
        {"atlas": "26",   "pdf": 40, "name": "冀州刺史部", "crop_top_half": True},
        # Phase 3 (even=map): atlas 28,30,32,34,36,38
        {"atlas": "27-28","pdf": 41, "name": "幽州刺史部（渤海附近）"},
        {"atlas": "29-30","pdf": 43, "name": "益州刺史部北部"},
        {"atlas": "31-32","pdf": 45, "name": "益州刺史部南部 哀牢"},
        {"atlas": "33-34","pdf": 47, "name": "凉州刺史部"},
        {"atlas": "35-36","pdf": 49, "name": "交阯刺史部（日南南部）"},
        {"atlas": "37-38","pdf": 51, "name": "西域都护府"},
        # atlas 39 单ODD(匈奴) → 翻转，内容在 atlas 40 混合页(PDF 53)上半
        {"atlas": "39",   "pdf": 53, "name": "匈奴及邻族", "crop_top_half": True},
        # Phase 4 (odd=map): atlas 41,43,45
        {"atlas": "40-41","pdf": 54, "name": "东汉时期全图"},
        {"atlas": "42-43","pdf": 56, "name": "司隶刺史部（洛阳附近）"},
        {"atlas": "44-45","pdf": 58, "name": "兖豫青徐刺史部"},
        # atlas 46 单EVEN(颖川间) → 翻转回，内容在 atlas 47 混合页(PDF 60)上半
        {"atlas": "46",   "pdf": 60, "name": "颖川间诸郡", "crop_top_half": True},
        # Phase 5 (even=map): atlas 48,50,52,54,56,58,60,62,64,66
        {"atlas": "47-48","pdf": 61, "name": "冀州刺史部"},
        {"atlas": "49-50","pdf": 63, "name": "荆州刺史部（宛县附近）"},
        {"atlas": "51-52","pdf": 65, "name": "扬州刺史部"},
        {"atlas": "53-54","pdf": 67, "name": "益州刺史部北部"},
        {"atlas": "55-56","pdf": 69, "name": "益州刺史部南部"},
        {"atlas": "57-58","pdf": 71, "name": "凉州刺史部"},
        {"atlas": "59-60","pdf": 73, "name": "并州刺史部"},
        {"atlas": "61-62","pdf": 75, "name": "幽州刺史部"},
        {"atlas": "63-64","pdf": 77, "name": "交阯刺史部"},
        {"atlas": "65-66","pdf": 79, "name": "西域都护府"},
        # atlas 67 单ODD(鲜卑) → 翻转，内容在 atlas 68 混合页(PDF 81)上半
        {"atlas": "67",   "pdf": 81, "name": "鲜卑及邻族", "crop_top_half": True},
    ],
}


def extract_maps_from_vol(vol_config: dict, out_dir: str) -> list:
    """提取单册的地图页和索引页"""
    pdf_path = os.path.join(BOOK_DIR, vol_config["file"])
    doc = fitz.open(pdf_path)

    vol_name = vol_config["name"]
    maps_dir = os.path.join(out_dir, f"{vol_name}_maps")
    index_dir = os.path.join(out_dir, f"{vol_name}_index")
    os.makedirs(maps_dir, exist_ok=True)
    os.makedirs(index_dir, exist_ok=True)

    maps_config = vol_config["maps"]

    # ── 1. 验证页码映射 ─────────────────────────────────────────
    print(f"\n[{vol_name}] 验证页码映射...")
    for m in maps_config:
        pno = m["pdf"]
        page = doc[pno - 1]
        has_image = bool(page.get_images(full=True))
        status = "✓" if has_image else "⚠ 无图像！"
        crop_note = " [裁上半]" if m.get("crop_top_half") else ""
        print(f"  PDF {pno:3d} | atlas {m['atlas']:5s} | {m['name'][:22]:22s} {status}{crop_note}")

    # ── 2. 逐张提取地图 ──────────────────────────────────────────
    saved_maps = []
    manifest = []

    for m in maps_config:
        pno = m["pdf"]
        atlas_id = m["atlas"]
        map_name = m["name"]
        safe_name = (map_name
                     .replace(" ", "_")
                     .replace("/", "／")
                     .replace("（", "(")
                     .replace("）", ")")
                     .replace("、", "_"))
        out_name = f"{atlas_id}_{safe_name}.pdf"
        out_path = os.path.join(maps_dir, out_name)

        out_doc = fitz.open()
        src_page = doc[pno - 1]
        orig_rect = src_page.rect  # 原始 portrait 尺寸，如 595×842

        if m.get("crop_top_half"):
            # 混合页：小地图在上半部分（约55%高度），横版不需旋转
            # 取上55%区域，保持横版
            clip = fitz.Rect(
                orig_rect.x0,
                orig_rect.y0,
                orig_rect.x1,
                orig_rect.y0 + orig_rect.height * 0.56,
            )
            # 小地图已是横版（landscape），尺寸约 595×472
            new_page = out_doc.new_page(width=clip.width, height=clip.height)
            new_page.show_pdf_page(new_page.rect, doc, pno - 1, clip=clip)
        else:
            # 正常全页地图：portrait 存储，需旋转 90° CW → landscape
            # 旋转后尺寸：842×595（原 h×w）
            new_w, new_h = orig_rect.height, orig_rect.width
            new_page = out_doc.new_page(width=new_w, height=new_h)
            new_page.show_pdf_page(new_page.rect, doc, pno - 1, rotate=90)

        out_doc.save(out_path, garbage=4, deflate=True)
        out_doc.close()

        entry = {
            "atlas": atlas_id,
            "pdf_page": pno,
            "name": map_name,
            "file": out_name,
            "crop_top_half": m.get("crop_top_half", False),
        }
        manifest.append(entry)
        saved_maps.append(out_path)

    print(f"\n[{vol_name}] 提取地图 {len(saved_maps)} 张 → {maps_dir}")

    # ── 3. 合并为单个地图 PDF ─────────────────────────────────────
    merged_path = os.path.join(out_dir, f"{vol_name}_maps.pdf")
    merged = fitz.open()
    for src_path in saved_maps:
        src = fitz.open(src_path)
        merged.insert_pdf(src)
        src.close()
    merged.save(merged_path, garbage=4, deflate=True)
    merged.close()
    print(f"  合并地图 PDF → {merged_path}")

    # ── 4. 提取索引页 ─────────────────────────────────────────────
    idx_start = vol_config["index_section_start"]
    idx_end = vol_config["index_section_end"]

    idx_doc = fitz.open()
    for pno in range(idx_start, idx_end + 1):
        idx_doc.insert_pdf(doc, from_page=pno - 1, to_page=pno - 1)

    idx_merged = os.path.join(out_dir, f"{vol_name}_index.pdf")
    idx_doc.save(idx_merged, garbage=4, deflate=True)
    idx_doc.close()
    print(f"  提取索引 PDF ({idx_end - idx_start + 1} 页) → {idx_merged}")

    for pno in range(idx_start, idx_end + 1):
        out_name = f"index_p{pno:03d}.pdf"
        out_path = os.path.join(index_dir, out_name)
        tmp = fitz.open()
        tmp.insert_pdf(doc, from_page=pno - 1, to_page=pno - 1)
        tmp.save(out_path)
        tmp.close()
    print(f"  索引单页 → {index_dir}")

    # ── 5. 保存清单 ────────────────────────────────────────────────
    manifest_path = os.path.join(out_dir, f"{vol_name}_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  清单 → {manifest_path}")

    doc.close()
    return manifest


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    for vol in [VOL1, VOL2]:
        print("\n" + "=" * 60)
        print(f"处理 {vol['name']}")
        print("=" * 60)
        extract_maps_from_vol(vol, OUT_DIR)

    print("\n✓ 全部完成")
