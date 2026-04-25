#!/usr/bin/env python3
"""
谭其骧《中国历史地图集》地名索引解析脚本

索引格式（来自第47页说明）：
  每条索引：地名（时期）图幅页码 ⑤②
    - 时期：(夏)/(商)/(西周)/(春秋)/(战国) 或 (秦)/(西汉)/(东汉)
    - 图幅页码：如 22-23 或 35（与目录对应的 atlas 页码范围）
    - ⑤ = 纵向坐标（行，圆圈数字 ①-⑩）
    - ② = 横向坐标（列，普通数字 1-10）

坐标系统（每张地图独立）：
  - 纵轴（行）：从上到下，①②③④⑤⑥...
  - 横轴（列）：从左到右，1 2 3 4 5 6 7 8 9 10

索引按汉字笔画排序，分部：
  丨部（一画）、一部（一画）、丿部、乙部 ... 等

用法：
  python parse_index.py              # 渲染所有索引页为 PNG（300 DPI）
  python parse_index.py --ocr        # 尝试 OCR（需要 tesseract + chi_sim）
  python parse_index.py --from-text  # 从已有 txt 文件解析（手工修正后用）
"""

import os
import re
import json
import argparse
from pathlib import Path
import fitz  # PyMuPDF

_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
BOOK_DIR      = os.path.join(_SCRIPT_DIR, "book")    # symlink
OUT_DIR       = os.path.join(_SCRIPT_DIR, "output")  # symlink
INDEX_IMG_DIR = os.path.join(OUT_DIR, "index_images")
INDEX_TXT_DIR = os.path.join(OUT_DIR, "index_texts")
INDEX_JSON    = os.path.join(OUT_DIR, "place_index.json")

# 圆圈数字 Unicode → 整数
CIRCLED_DIGITS = {
    "①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5,
    "⑥": 6, "⑦": 7, "⑧": 8, "⑨": 9, "⑩": 10,
    # 括号数字（备用）
    "⑪": 11, "⑫": 12,
}

# 时期关键字（括号内）
PERIOD_KEYWORDS = {
    # 第一册（先秦）
    "夏": "Xia", "商": "Shang", "西周": "W_Zhou", "周": "W_Zhou",
    "春秋": "Spring_Autumn", "战国": "Warring_States",
    "先秦": "pre_Qin",
    # 第二册（秦汉）
    "秦": "Qin", "西汉": "W_Han", "汉": "W_Han", "东汉": "E_Han",
}

# 索引页范围
INDEX_RANGES = {
    "vol1": {"file": "中国历史地图集++（精装本）1++第一册（先秦）.pdf",
             "pages": list(range(76, 93))},   # PDF 76-92
    "vol2": {"file": "中国历史地图集++（精装本）2++第二册（秦汉）.pdf",
             "pages": list(range(81, 102))},  # PDF 81-101
}


# ─────────────────────────────────────────────────────────────────────────────
# 步骤1：渲染索引页为高分辨率 PNG
# ─────────────────────────────────────────────────────────────────────────────

def render_index_pages(dpi: int = 300) -> None:
    """渲染两册所有索引页为 PNG，保存到 output/index_images/"""
    os.makedirs(INDEX_IMG_DIR, exist_ok=True)
    print(f"渲染索引页（{dpi} DPI）→ {INDEX_IMG_DIR}")

    for vol_name, cfg in INDEX_RANGES.items():
        pdf_path = os.path.join(BOOK_DIR, cfg["file"])
        doc = fitz.open(pdf_path)
        mat = fitz.Matrix(dpi / 72, dpi / 72)

        for pdf_pno in cfg["pages"]:
            page = doc[pdf_pno - 1]
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
            out_path = os.path.join(INDEX_IMG_DIR, f"{vol_name}_p{pdf_pno:03d}.png")
            pix.save(out_path)
            print(f"  {out_path} ({pix.width}×{pix.height})")

        doc.close()

    print(f"✓ 渲染完成，共 {sum(len(v['pages']) for v in INDEX_RANGES.values())} 页")


# ─────────────────────────────────────────────────────────────────────────────
# 步骤2：OCR（需要 tesseract + chi_sim 语言包）
# ─────────────────────────────────────────────────────────────────────────────

def ocr_index_pages() -> None:
    """OCR 所有索引图像，保存为 .txt 文件"""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        print("需要安装: pip install pytesseract pillow")
        return

    try:
        pytesseract.get_tesseract_version()
    except Exception:
        print("Tesseract 未安装，请运行：sudo apt install tesseract-ocr tesseract-ocr-chi-sim")
        return

    os.makedirs(INDEX_TXT_DIR, exist_ok=True)
    png_files = sorted(Path(INDEX_IMG_DIR).glob("*.png"))
    print(f"OCR {len(png_files)} 个图像文件...")

    for png_path in png_files:
        txt_path = Path(INDEX_TXT_DIR) / (png_path.stem + ".txt")
        if txt_path.exists():
            print(f"  跳过（已存在）: {txt_path.name}")
            continue

        img = Image.open(png_path)
        # 使用竖排中文 + 简体中文模式
        text = pytesseract.image_to_string(
            img,
            lang="chi_sim",
            config="--psm 6 --oem 1",
        )
        txt_path.write_text(text, encoding="utf-8")
        lines = text.count("\n")
        print(f"  {png_path.name} → {txt_path.name} ({lines} 行)")

    print("✓ OCR 完成")


# ─────────────────────────────────────────────────────────────────────────────
# 步骤3：解析文本，提取结构化数据
# ─────────────────────────────────────────────────────────────────────────────

# 匹配一条索引条目的正则
# 格式：地名（时期）图幅页码 ⑤②
# 例：上蔡（春秋）22-23⑦7   → name=上蔡, period=春秋, atlas=22-23, row=7, col=7
# 例：鄢陵（战国）35-36⑤4   → name=鄢陵, period=战国, atlas=35-36, row=5, col=4
# 例：三川（西汉）17-18③2   → name=三川, period=西汉, atlas=17-18, row=3, col=2

_CIRCLED_PATTERN = "[" + "".join(CIRCLED_DIGITS.keys()) + "]"
_ATLAS_PATTERN = r"(\d+(?:[—\-–]\d+)?)"     # 如 22-23 或 35
_ROW_PATTERN = f"({_CIRCLED_PATTERN})"
_COL_PATTERN = r"(\d+)"

ENTRY_RE = re.compile(
    r"([一-鿿㐀-䶿·•]+)"   # 地名（汉字 + 中点）
    r"[\s（(]+"                               # 可能有空格或括号
    r"((?:春秋|战国|西周|夏|商|周|秦|西汉|东汉|汉))"  # 时期
    r"[）)]\s*"
    r"(\d+(?:[—\-–]\d+)?)"                   # atlas 图幅页码
    r"\s*"
    + f"({_CIRCLED_PATTERN})"                # 行坐标（圆圈数字）
    + r"\s*(\d+)",                           # 列坐标
    re.UNICODE,
)


def parse_entry_line(line: str) -> list:
    """解析一行文本，返回条目列表（一行可能有多个条目）"""
    results = []
    for m in ENTRY_RE.finditer(line):
        name, period, atlas_str, row_char, col_str = m.groups()
        row = CIRCLED_DIGITS.get(row_char, 0)
        col = int(col_str)
        period_en = PERIOD_KEYWORDS.get(period, period)

        results.append({
            "name": name,
            "period": period,
            "period_en": period_en,
            "atlas": atlas_str.replace("—", "-").replace("–", "-"),
            "row": row,
            "col": col,
        })
    return results


def parse_text_files() -> list:
    """解析所有 OCR 文本文件，返回结构化条目列表"""
    txt_files = sorted(Path(INDEX_TXT_DIR).glob("*.txt"))
    if not txt_files:
        print(f"没有找到文本文件，请先运行 OCR 或将文本放入 {INDEX_TXT_DIR}")
        return []

    all_entries = []
    total_lines = 0
    parsed_count = 0

    for txt_path in txt_files:
        vol = "vol1" if "vol1" in txt_path.name else "vol2"
        text = txt_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        total_lines += len(lines)

        for line in lines:
            entries = parse_entry_line(line)
            for e in entries:
                e["vol"] = vol
                e["source_file"] = txt_path.name
            all_entries.extend(entries)
            parsed_count += len(entries)

    print(f"解析 {len(txt_files)} 个文件，{total_lines} 行，提取 {parsed_count} 条地名")
    return all_entries


def save_index_json(entries: list) -> None:
    """保存结构化索引为 JSON"""
    # 按地名排序
    entries_sorted = sorted(entries, key=lambda e: e["name"])

    # 建立地名→位置映射（一个地名可能在多张图上）
    place_map = {}
    for e in entries_sorted:
        name = e["name"]
        if name not in place_map:
            place_map[name] = []
        place_map[name].append({
            "period": e["period"],
            "atlas": e["atlas"],
            "row": e["row"],
            "col": e["col"],
            "vol": e["vol"],
        })

    output = {
        "total_entries": len(entries_sorted),
        "total_places": len(place_map),
        "entries": entries_sorted,
        "place_map": place_map,
    }

    with open(INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✓ 索引 JSON → {INDEX_JSON}")
    print(f"  共 {len(entries_sorted)} 条，{len(place_map)} 个地名")


# ─────────────────────────────────────────────────────────────────────────────
# 辅助：打印坐标系说明
# ─────────────────────────────────────────────────────────────────────────────

def print_coordinate_guide():
    print("""
坐标系说明（每张地图独立）：
┌────────────────────────────────────────────┐
│        1    2    3    4    5  ← 横向（列）     │
│  ① ┤  ....  ....  ....  ....  ....           │
│  ② ┤  ....  ....  ....  ....  ....           │
│  ③ ┤  ....  ....  ....  ....  ....           │
│  ↑                                           │
│  纵向（行）                                   │
└────────────────────────────────────────────┘
查询示例：
  上蔡（春秋）22-23 ⑦ 7
  → 在图幅 22-23（晋秦图），第7行第7列

坐标来源：第47页（vol1）/第69页（vol2）"地名索引简要说明"
""")


# ─────────────────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="解析谭其骧地图集地名索引")
    parser.add_argument("--render", action="store_true", help="渲染索引页为高分辨率 PNG")
    parser.add_argument("--ocr", action="store_true", help="OCR 已渲染的图像")
    parser.add_argument("--parse", action="store_true", help="解析 OCR 文本文件")
    parser.add_argument("--all", action="store_true", help="执行全部步骤")
    parser.add_argument("--guide", action="store_true", help="打印坐标系说明")
    parser.add_argument("--dpi", type=int, default=300, help="渲染 DPI（默认300）")
    args = parser.parse_args()

    if args.guide:
        print_coordinate_guide()

    if args.render or args.all:
        render_index_pages(dpi=args.dpi)

    if args.ocr or args.all:
        ocr_index_pages()

    if args.parse or args.all:
        entries = parse_text_files()
        if entries:
            save_index_json(entries)

    if not any([args.render, args.ocr, args.parse, args.all, args.guide]):
        # 默认：只渲染
        print("渲染索引页（默认行为）...")
        render_index_pages(dpi=args.dpi)
        print("\n后续步骤：")
        print("  1. 安装 tesseract: sudo apt install tesseract-ocr tesseract-ocr-chi-sim")
        print("  2. 运行 OCR: python parse_index.py --ocr")
        print("  3. 解析结果: python parse_index.py --parse")
        print("  或一步到位: python parse_index.py --all")
