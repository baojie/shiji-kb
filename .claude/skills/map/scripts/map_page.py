#!/usr/bin/env python3
"""
map_page.py — 从谭图为 wiki 页面裁切历史地图

用法（从仓库根运行）：
  python .claude/skills/map/scripts/map_page.py 曲沃
  python .claude/skills/map/scripts/map_page.py 曲沃 春秋
  python .claude/skills/map/scripts/map_page.py 曲沃 all
  python .claude/skills/map/scripts/map_page.py 曲沃 --crop-deg 4.0
  python .claude/skills/map/scripts/map_page.py 曲沃 --list-maps   # 显示匹配的地图
  python .claude/skills/map/scripts/map_page.py 曲沃 --write        # 自动写入页面+记录修订

输出: wiki/public/images/{period}-{page_id}.jpg
     同时打印 YAML frontmatter 片段供复制到页面
     --write 模式：自动追加 frontmatter + 调用 record_revision.py（作者=map）
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("✗ 请先安装 Pillow: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# ── 路径 ──────────────────────────────────────────────────────────────────────

# 脚本在 .claude/skills/map/scripts/map_page.py，仓库根在 4 级上
REPO_ROOT  = Path(__file__).resolve().parent.parent.parent.parent
# 安全回退：从 cwd 向上找仓库根
if not (REPO_ROOT / "wiki").is_dir():
    _cwd = Path.cwd()
    for candidate in [_cwd, _cwd.parent, _cwd.parent.parent]:
        if (candidate / "wiki").is_dir() and (candidate / "corpus").is_dir():
            REPO_ROOT = candidate
            break

ATLAS_DIR  = REPO_ROOT / "corpus" / "谭图"
PAGES_DIR  = REPO_ROOT / "wiki" / "public" / "pages"
OUT_DIR    = REPO_ROOT / "wiki" / "public" / "images"
EXTENTS    = Path(__file__).parent.parent / "references" / "map_extents.json"

# ── 默认参数 ──────────────────────────────────────────────────────────────────

DEFAULT_CROP_DEG      = 3.0   # 裁切半径（度），以地点为中心左右各 crop_deg 度
DEFAULT_QUALITY       = 88    # JPEG 质量
MAX_OUTPUT_WIDTH      = 2000  # 输出最大宽度（像素）
DEFAULT_EXCLUDE       = {"东汉"}  # 默认排除的时代（可用 --include 覆盖）

# ── Frontmatter 解析 ──────────────────────────────────────────────────────────

def read_frontmatter(page_path: Path) -> dict:
    text = page_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip().strip('"\'')
    # coords: [lon, lat]
    coords_raw = fm.get("coords", "")
    m2 = re.search(r"\[([0-9.]+),\s*([0-9.]+)\]", coords_raw)
    if m2:
        fm["_coords"] = [float(m2.group(1)), float(m2.group(2))]
    return fm


def find_page(page_id: str) -> Path | None:
    direct = PAGES_DIR / f"{page_id}.md"
    if direct.exists():
        return direct
    for p in PAGES_DIR.glob("*.md"):
        if p.stem == page_id:
            return p
    return None

# ── 地图匹配 ──────────────────────────────────────────────────────────────────

def load_extents() -> list[dict]:
    return json.loads(EXTENTS.read_text(encoding="utf-8"))["maps"]


def _centrality(lon: float, lat: float, m: dict) -> float:
    """计算坐标在地图内容区的居中程度（0=边缘, 1=完全居中）。"""
    lon_w, lon_e = m["lon_range"]
    lat_s, lat_n = m["lat_range"]
    cx = (lon - lon_w) / (lon_e - lon_w)  # 0~1
    cy = (lat - lat_s) / (lat_n - lat_s)  # 0~1
    # 距离中心的归一化距离（值越小越居中）
    dist = ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5
    return 1.0 - dist  # 越大越居中


def maps_for_period_and_coords(
    lon: float, lat: float,
    period: str | None,
    extents: list[dict],
) -> list[dict]:
    """
    返回覆盖 (lon, lat) 且符合 period 的地图列表。
    每个 (时代, priority) 组合只保留坐标最居中的那张，避免重复文件名。
    """
    candidates = []
    for m in extents:
        if period and period not in m["periods"]:
            continue
        lon_w, lon_e = m["lon_range"]
        lat_s, lat_n = m["lat_range"]
        if not (lon_w <= lon <= lon_e and lat_s <= lat <= lat_n):
            continue
        candidates.append(m)

    if not candidates:
        return []

    # 每个（首要时代 + priority）只取坐标最居中的一张
    best: dict[tuple, tuple] = {}  # (first_period, priority) -> (centrality, map)
    for m in candidates:
        key = (m["periods"][0], m["priority"])
        c = _centrality(lon, lat, m)
        if key not in best or c > best[key][0]:
            best[key] = (c, m)

    # 每个首要时代只取最低 priority 的一条
    per_period: dict[str, tuple] = {}  # first_period -> (priority, map)
    for (fp, pri), (_, m) in best.items():
        if fp not in per_period or pri < per_period[fp][0]:
            per_period[fp] = (pri, m)

    result = [m for _, m in per_period.values()]
    result.sort(key=lambda x: (x["periods"][0], x["priority"]))
    return result

# ── 裁切核心 ──────────────────────────────────────────────────────────────────

def crop_map(
    atlas_file: str,
    lon: float, lat: float,
    extent: dict,
    crop_deg: float,
    out_path: Path,
) -> tuple[bool, str]:
    """
    在 atlas_file 中以 (lon, lat) 为中心裁切 crop_deg 度半径的矩形。
    返回 (success, message)。
    """
    src = ATLAS_DIR / atlas_file
    if not src.exists():
        return False, f"源文件不存在: {src}"

    img = Image.open(src)
    W, H = img.size

    # 内容区像素范围
    cl, ct, cr, cb = extent["content"]
    cx0 = int(cl * W); cx1 = int(cr * W)
    cy0 = int(ct * H); cy1 = int(cb * H)
    cw = cx0 - cx1; ch = cy0 - cy1   # 负数，下面用绝对值

    lon_w, lon_e = extent["lon_range"]
    lat_s, lat_n = extent["lat_range"]
    lon_span = lon_e - lon_w
    lat_span = lat_n - lat_s

    # 内容区宽高（像素）
    content_px_w = cx1 - cx0
    content_px_h = cy1 - cy0

    # 地点在内容区的归一化位置
    nx = (lon - lon_w) / lon_span
    ny = (lat_n - lat) / lat_span   # 图像 y=0 在北方

    # 地点的像素坐标
    px = cx0 + nx * content_px_w
    py = cy0 + ny * content_px_h

    # 裁切半径（像素）
    px_per_deg_x = content_px_w / lon_span
    px_per_deg_y = content_px_h / lat_span
    half_x = crop_deg * px_per_deg_x
    half_y = crop_deg * px_per_deg_y

    # 裁切框（限定在内容区内）
    left   = max(cx0, int(px - half_x))
    top    = max(cy0, int(py - half_y))
    right  = min(cx1, int(px + half_x))
    bottom = min(cy1, int(py + half_y))

    if right - left < 50 or bottom - top < 50:
        return False, f"裁切区域过小 ({right-left}×{bottom-top}px)，坐标可能在地图边缘"

    cropped = img.crop((left, top, right, bottom))

    # 按最大宽度缩放
    cw2, ch2 = cropped.size
    if cw2 > MAX_OUTPUT_WIDTH:
        ratio = MAX_OUTPUT_WIDTH / cw2
        cropped = cropped.resize(
            (MAX_OUTPUT_WIDTH, int(ch2 * ratio)),
            Image.LANCZOS,
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cropped.save(out_path, "JPEG", quality=DEFAULT_QUALITY, subsampling=0)
    w2, h2 = cropped.size
    return True, f"{w2}×{h2}px"

# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="从谭图为 wiki 页面裁切历史地图"
    )
    parser.add_argument("page_id", help="页面 ID（wiki/public/pages/ 下文件名）")
    parser.add_argument(
        "period", nargs="?", default=None,
        help="时代（春秋/战国/秦/西汉/东汉 等）；'all' = 所有匹配时代；默认 = all",
    )
    parser.add_argument("--crop-deg", type=float, default=DEFAULT_CROP_DEG,
                        help=f"裁切半径度数（默认 {DEFAULT_CROP_DEG}）")
    parser.add_argument("--list-maps", action="store_true",
                        help="只列出匹配的地图，不执行裁切")
    parser.add_argument("--include", metavar="时代", action="append", default=[],
                        help="强制包含默认排除的时代（可多次指定），如 --include 东汉")
    parser.add_argument("--exclude", metavar="时代", action="append", default=[],
                        help="额外排除的时代（可多次指定），如 --exclude 夏")
    parser.add_argument("--write", action="store_true",
                        help="自动将 images frontmatter 追加写入页面并调用 record_revision.py")
    args = parser.parse_args()

    # 找页面
    page_path = find_page(args.page_id)
    if not page_path:
        print(f"✗ 未找到页面: {args.page_id}  (在 {PAGES_DIR})", file=sys.stderr)
        sys.exit(1)

    fm = read_frontmatter(page_path)
    coords = fm.get("_coords")
    if not coords:
        print(f"✗ 页面 {args.page_id} 无 coords 字段，跳过", file=sys.stderr)
        print(f"  请先在 frontmatter 中添加: coords: [lon, lat]")
        sys.exit(1)

    lon, lat = coords
    label = fm.get("label", args.page_id)
    print(f"[map] 页面: {label}  坐标: [{lon}, {lat}]")

    extents = load_extents()

    # 时代参数处理
    period = args.period
    if period and period.lower() == "all":
        period = None   # None = 全部匹配

    matching = maps_for_period_and_coords(lon, lat, period, extents)

    # 排除过滤：DEFAULT_EXCLUDE 减去 --include，加上 --exclude
    if period is None:  # 只在 all 模式下应用默认排除
        exclude_set = (DEFAULT_EXCLUDE - set(args.include)) | set(args.exclude)
        if exclude_set:
            before = len(matching)
            matching = [m for m in matching if m["periods"][0] not in exclude_set]
            skipped = before - len(matching)
            if skipped:
                print(f"  （跳过 {skipped} 张：{', '.join(sorted(exclude_set))}；用 --include 时代 可覆盖）")

    if not matching:
        print(f"✗ 未找到覆盖 [{lon}, {lat}] 的地图"
              + (f" (period={args.period})" if args.period else ""),
              file=sys.stderr)
        print("  提示：检查 map_extents.json 是否有对应时代和范围")
        sys.exit(1)

    if args.list_maps:
        print(f"\n匹配到 {len(matching)} 张地图：")
        for m in matching:
            in_range = "✓" if (
                m["lon_range"][0] <= lon <= m["lon_range"][1] and
                m["lat_range"][0] <= lat <= m["lat_range"][1]
            ) else "✗"
            print(f"  {in_range} [{m['periods']}] {m['file']}  lon{m['lon_range']} lat{m['lat_range']}")
        return

    # 执行裁切
    results = []
    print(f"\n裁切 {len(matching)} 张地图（crop_deg={args.crop_deg}）：")
    for m in matching:
        # 输出文件名：{第一个时代}-{page_id}.jpg
        out_period = m["periods"][0]
        out_name = f"{out_period}-{args.page_id}.jpg"
        out_path = OUT_DIR / out_name

        ok, msg = crop_map(m["file"], lon, lat, m, args.crop_deg, out_path)
        status = "✓" if ok else "✗"
        print(f"  {status} {out_name}  {msg}  (源: {m['file']})")
        if ok:
            results.append({
                "period": out_period,
                "file": f"images/{out_name}",
                "label": m["label"],
                "source_file": m["file"],
            })

    if not results:
        print("\n无成功裁切结果")
        sys.exit(1)

    # 打印 frontmatter 片段
    new_entries = []
    for r in results:
        caption = f"{r['period']}时期{label}及周边地区（谭其骧《中国历史地图集》{r['label']}）"
        new_entries.append({"file": r["file"], "caption": caption})

    print(f"\n─── 复制到 {page_path.name} 的 frontmatter ───")
    print("images:")
    for e in new_entries:
        print(f"  - file: {e['file']}")
        print(f"    caption: {e['caption']}")
    print('image_credit: 谭其骧《中国历史地图集》')
    print("────────────────────────────────────────────")

    print(f"\n生成 {len(results)} 张地图到 {OUT_DIR}")

    if args.write:
        _write_frontmatter_and_record(page_path, args.page_id, new_entries, results)


def _write_frontmatter_and_record(page_path: Path, page_id: str,
                                   new_entries: list[dict], results: list[dict]) -> None:
    """--write 模式：append-only 写 images frontmatter，然后调 record_revision.py。"""
    text = page_path.read_text(encoding="utf-8")
    m = re.match(r"^(---\n)(.*?)(\n---\n)(.*)", text, re.DOTALL)
    if not m:
        print("✗ --write: 找不到 frontmatter，跳过写入", file=sys.stderr)
        return

    fm_raw = m.group(2)
    body = m.group(4)

    # 解析已有 images 列表（简单提取已有 file: 条目，避免重复）
    existing_files = set(re.findall(r"^\s*-\s*file:\s*(.+)$", fm_raw, re.MULTILINE))
    to_add = [e for e in new_entries if e["file"] not in existing_files]

    if not to_add:
        print("= --write: 所有图片已存在于 frontmatter，跳过写入")
        return

    # 构造新 images 条目 YAML
    new_yaml_lines = []
    for e in to_add:
        new_yaml_lines.append(f"  - file: {e['file']}")
        new_yaml_lines.append(f"    caption: {e['caption']}")

    # append-only: 若有 images: 块则插入其中，否则追加新块
    if re.search(r"^images:", fm_raw, re.MULTILINE):
        # 在最后一个 images 列表项后插入
        insert_after = r"((?:(?:\n  - file:.*\n    caption:.*)+)(?=\n[a-z]|\Z))"
        # 更简单：直接在 fm_raw 末尾（或 image_credit 前）插入
        if "image_credit:" in fm_raw:
            fm_new = fm_raw.replace(
                "\nimage_credit:",
                "\n" + "\n".join(new_yaml_lines) + "\nimage_credit:",
                1,
            )
        else:
            # 找到 images: 块结尾，插入新条目
            lines = fm_raw.splitlines()
            out, in_images = [], False
            inserted = False
            for i, line in enumerate(lines):
                out.append(line)
                if line.startswith("images:"):
                    in_images = True
                elif in_images and not line.startswith("  "):
                    if not inserted:
                        out[-1:-1] = new_yaml_lines  # 在当前行前插入
                        inserted = True
                    in_images = False
            if not inserted:
                out.extend(new_yaml_lines)
            fm_new = "\n".join(out)
    else:
        # 追加新 images 块
        fm_new = fm_raw.rstrip()
        fm_new += "\nimages:\n" + "\n".join(new_yaml_lines)
        fm_new += "\nimage_credit: 谭其骧《中国历史地图集》"

    # 更新正文：在 ## 地理位置 节末尾追加配图说明（让 diff 有可读正文变化）
    body = _append_map_note(body, results[:len(to_add)])

    new_text = "---\n" + fm_new + "\n---\n" + body
    page_path.write_text(new_text, encoding="utf-8")
    periods = "、".join(r["period"] for r in results[:len(to_add)])
    print(f"✓ --write: 已追加 {len(to_add)} 条 images 到 {page_path.name}（{periods}）")

    # 调用 record_revision.py
    record_script = REPO_ROOT / "wiki" / "scripts" / "butler" / "record_revision.py"
    n = len(to_add)
    summary = f"map: 新增{n}张谭图截图（{periods}）"
    ret = subprocess.run(
        [sys.executable, str(record_script), page_id, "--summary", summary, "--author", "map"],
        cwd=REPO_ROOT,
    )
    if ret.returncode != 0:
        print(f"✗ record_revision.py 失败（exit {ret.returncode}）", file=sys.stderr)


def _append_map_note(body: str, results: list[dict]) -> str:
    """在正文 ## 地理位置 节末尾追加配图说明行；若节不存在则在 ## 相关章节/## 史记引文 前新建节。
    已有配图说明则跳过（幂等）。"""
    MAP_MARKER = "**配图**："
    if MAP_MARKER in body:
        return body  # 已存在，不重复追加

    # 生成配图说明行
    map_labels = "、".join(r['label'] for r in results)
    n = len(results)
    note_line = f"\n**配图**：谭其骧《中国历史地图集》{map_labels}等 {n} 幅（见右栏）。\n"

    # 尝试找 ## 地理位置 或 ## 地理位置与建置
    geo_pat = re.compile(r"(## 地理位置(?:与建置)?)(.*?)(?=\n## |\Z)", re.DOTALL)
    m = geo_pat.search(body)
    if m:
        # 在该节末尾插入（去掉末尾空行后加）
        section = m.group(0).rstrip()
        new_section = section + note_line
        return body[:m.start()] + new_section + body[m.end():]

    # 没有 地理位置 节：在 ## 相关章节 / ## 史记引文 / ## 历代 前插入新节
    insert_pat = re.compile(r"(?=\n## (?:相关章节|史记引文|历代|相关人物))")
    ins = insert_pat.search(body)
    new_section = f"\n## 地理位置\n{note_line}"
    if ins:
        return body[:ins.start()] + new_section + body[ins.start():]
    # 实在找不到就追加到末尾
    return body.rstrip() + new_section


if __name__ == "__main__":
    main()
