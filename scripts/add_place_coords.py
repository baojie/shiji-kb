"""
add_place_coords.py
===================
为 wiki/public/pages/ 下的所有地名/邦国页面添加地理坐标。

数据来源（按优先级）:
  1. 本地 CHGIS V6 shapefile（labs/map/data/）—— 有则用，快且无网络依赖
  2. TGAZ 在线 API（chgis.hudci.org）—— 本地无数据时自动回落

坐标写入页面 frontmatter:
  coords: [lon, lat]          # GeoJSON 标准：经度在前
  coords_name: "邯郸郡"       # CHGIS 中匹配到的名称
  coords_source: "CHGIS hvd_xxxxx"

用法:
  python3 scripts/add_place_coords.py            # 处理所有无坐标的地名页
  python3 scripts/add_place_coords.py --dry-run  # 只打印，不写文件
  python3 scripts/add_place_coords.py --page 长安 # 只处理单个地名
  python3 scripts/add_place_coords.py --force     # 覆盖已有 coords
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

# ── 路径配置 ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
PAGES_DIR  = ROOT / "wiki/public/pages"
CACHE_FILE = ROOT / "labs/map/coords_cache.json"
CHGIS_DATA = ROOT / "labs/map/data"

TGAZ_BASE  = "https://chgis.hudci.org/tgaz/placename"

# 史记主体时代（秦汉）：按标签推断搜索年份
ERA_YEARS = {
    "夏朝": -1800, "商朝": -1200, "商": -1200,
    "西周": -900,  "周朝": -700,  "春秋": -600,
    "战国": -300,  "秦国": -260,  "秦末": -207,
    "楚汉": -203,  "西汉": -180,  "汉朝": -150,
    "汉武帝": -110,"匈奴": -150,  "南越": -130,
}
DEFAULT_YEAR_TRIES = [-200, -221, -150, -100, -300, -400, 0]

# ── 辅助函数 ──────────────────────────────────────────────────────────────

def load_cache() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def guess_year(tags: list[str]) -> int:
    """根据 tags 推断最合适的搜索年份。"""
    for tag in tags:
        for key, yr in ERA_YEARS.items():
            if key in tag:
                return yr
    return -200  # 默认秦汉交替期


def query_tgaz(name: str, year: int) -> list[dict]:
    """调用 TGAZ API，返回 placenames 列表。"""
    try:
        r = requests.get(
            TGAZ_BASE,
            params={"fmt": "json", "n": name, "yr": str(year)},
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("placenames", [])
    except Exception as e:
        print(f"  [API 错误] {name} yr={year}: {e}", file=sys.stderr)
        return []


def parse_xy(xy_str: str) -> list[float] | None:
    """'108.93719, 34.31799' → [108.93719, 34.31799]"""
    try:
        lon, lat = (float(x.strip()) for x in xy_str.split(","))
        if lon == 0.0 and lat == 0.0:
            return None
        return [round(lon, 5), round(lat, 5)]
    except Exception:
        return None


def best_match(results: list[dict], name: str) -> dict | None:
    """
    从 TGAZ 结果中选最佳匹配：
      - 过滤无效坐标（0,0）
      - 优先选 name 前缀匹配的结果
      - 优先选史记时代（-600 ~ 100）内的记录
    """
    if not results:
        return None

    valid = []
    for p in results:
        xy = parse_xy(p.get("xy coordinates", ""))
        if xy:
            p["_xy"] = xy
            valid.append(p)
    if not valid:
        return None

    def score(p):
        n = p.get("name", "")
        # 名称前缀匹配加分
        name_score = 2 if n.startswith(name) else (1 if name in n else 0)
        # 史记时代内加分
        yr_str = p.get("years", "")
        time_score = 0
        m = re.match(r"(-?\d+)\s*~\s*(-?\d+)", yr_str)
        if m:
            beg, end = int(m.group(1)), int(m.group(2))
            if beg <= 0 <= end or (-600 <= beg <= 200):
                time_score = 1
        return (name_score, time_score)

    return max(valid, key=score)


# ── 本地 CHGIS 数据库（启动时加载） ──────────────────────────────────────

_CHGIS_RECORDS: list[dict] | None = None  # 延迟加载


def _load_chgis_local() -> list[dict]:
    """读取本地 CHGIS DBF，返回所有记录（字典列表）。"""
    global _CHGIS_RECORDS
    if _CHGIS_RECORDS is not None:
        return _CHGIS_RECORDS

    dbf_files = list(CHGIS_DATA.rglob("*.dbf"))
    if not dbf_files:
        _CHGIS_RECORDS = []
        return _CHGIS_RECORDS

    try:
        from dbfread import DBF
    except ImportError:
        print("提示: 安装 dbfread 可使用本地 CHGIS（pip install dbfread）", file=sys.stderr)
        _CHGIS_RECORDS = []
        return _CHGIS_RECORDS

    records = []
    for dbf_path in dbf_files:
        try:
            for r in DBF(str(dbf_path), encoding="utf-8"):
                if r.get("X_COOR") and r.get("Y_COOR"):
                    records.append(dict(r))
        except Exception as e:
            print(f"  [DBF 读取错误] {dbf_path}: {e}", file=sys.stderr)

    _CHGIS_RECORDS = records
    print(f"[本地 CHGIS] 已加载 {len(records)} 条记录（{len(dbf_files)} 个 DBF）")
    return _CHGIS_RECORDS


def try_chgis_local(name: str, year: int):
    """
    从本地 CHGIS DBF 查找坐标。
    返回 (coords, matched_name, sys_id) 或 None。
    """
    records = _load_chgis_local()
    if not records:
        return None

    def name_match(r):
        for field in ("NAME_CH", "NAME_FT"):
            v = r.get(field, "") or ""
            if v.startswith(name):
                return v
        return None

    def year_overlap(r, yr):
        beg = r.get("BEG_YR", -9999)
        end = r.get("END_YR",  9999)
        try:
            return int(beg) <= yr <= int(end)
        except (TypeError, ValueError):
            return False

    # 第一轮：名称前缀 + 年份范围匹配
    candidates = []
    for r in records:
        nm = name_match(r)
        if nm:
            candidates.append((r, nm))

    if not candidates:
        return None

    # 在年份范围内优先
    year_ok = [(r, nm) for r, nm in candidates if year_overlap(r, year)]
    best_list = year_ok if year_ok else candidates

    # 精确名称优先（长度更短 = 更基础的地名单元）
    best_list.sort(key=lambda x: (len(x[1]) - len(name), abs(x[0].get("BEG_YR", 0) or 0)))
    r, nm = best_list[0]

    try:
        lon = round(float(r["X_COOR"]), 5)
        lat = round(float(r["Y_COOR"]), 5)
    except (TypeError, ValueError):
        return None
    if lon == 0.0 and lat == 0.0:
        return None

    return ([lon, lat], nm, str(r.get("SYS_ID", "")))


# ── 核心：查询单个地名 ────────────────────────────────────────────────────

def lookup_place(name: str, tags: list[str], cache: dict) -> dict | None:
    """
    查询地名坐标，返回 {"coords":[], "name":str, "sys_id":str} 或 None。
    优先用缓存，然后本地 CHGIS，最后 TGAZ API。
    """
    if name in cache:
        return cache[name]  # None 也缓存（表示查不到）

    # 1. 尝试本地 CHGIS
    year = guess_year(tags)
    local = try_chgis_local(name, year)
    if local:
        result = {"coords": local[0], "name": local[1], "sys_id": local[2], "source": "CHGIS-local"}
        cache[name] = result
        return result

    # 2. 尝试 TGAZ API（多个年份）
    years_to_try = [year] + [y for y in DEFAULT_YEAR_TRIES if y != year]
    for yr in years_to_try:
        results = query_tgaz(name, yr)
        match = best_match(results, name)
        if match:
            coords = match["_xy"]
            result = {
                "coords": coords,
                "name": match.get("name", name),
                "sys_id": match.get("sys_id", ""),
                "source": "CHGIS-tgaz",
            }
            cache[name] = result
            return result
        time.sleep(0.4)

    cache[name] = None  # 查不到，缓存避免重试
    return None


# ── frontmatter 读写 ──────────────────────────────────────────────────────

def read_frontmatter(content: str) -> tuple[str, str, str]:
    """返回 (before_fm, fm_content, after_fm)"""
    parts = content.split("---", 2)
    if len(parts) < 3 or parts[0].strip():
        return content, "", ""
    return parts[0], parts[1], parts[2]


def get_fm_field(fm: str, key: str) -> str | None:
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else None


def get_fm_tags(fm: str) -> list[str]:
    m = re.search(r"^tags:\s*\[(.+)\]", fm, re.MULTILINE)
    if m:
        return [t.strip().strip('"\'') for t in m.group(1).split(",")]
    return []


def write_coords(path: Path, result: dict, dry_run: bool) -> bool:
    """将 coords 写入 frontmatter。返回是否有变更。"""
    content = path.read_text(encoding="utf-8")
    _, fm, rest = read_frontmatter(content)
    if not fm:
        return False

    lon, lat = result["coords"]
    matched = result["name"]
    sys_id  = result["sys_id"]
    src_tag = f"CHGIS {sys_id}".strip()

    new_fields = (
        f'\ncoords: [{lon}, {lat}]'
        f'\ncoords_name: "{matched}"'
        f'\ncoords_source: "{src_tag}"'
    )
    new_fm = fm.rstrip() + new_fields + "\n"
    new_content = f"---{new_fm}---{rest}"

    if dry_run:
        return True
    path.write_text(new_content, encoding="utf-8")
    return True


# ── 主程序 ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="为 wiki 地名页添加 CHGIS 坐标")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    ap.add_argument("--force",   action="store_true", help="覆盖已有 coords")
    ap.add_argument("--page",    metavar="NAME", help="只处理指定地名")
    ap.add_argument("--limit",   type=int, default=0, help="最多处理 N 个（0=全部）")
    args = ap.parse_args()

    cache = load_cache()
    pages = sorted(PAGES_DIR.glob("*.md"))

    # 筛选地名/邦国页面
    targets = []
    for p in pages:
        content = p.read_text(encoding="utf-8")
        _, fm, _ = read_frontmatter(content)
        if not fm:
            continue
        ptype = get_fm_field(fm, "type")
        if ptype not in ("place", "state"):
            continue
        if not args.force and "coords:" in fm:
            continue
        pid = get_fm_field(fm, "id") or p.stem
        if args.page and pid != args.page:
            continue
        targets.append((p, pid, get_fm_tags(fm)))

    total = len(targets)
    if args.limit:
        targets = targets[: args.limit]
    print(f"待处理: {len(targets)} / {total} 个地名页面")

    added = skipped = errors = 0

    for i, (path, name, tags) in enumerate(targets, 1):
        result = lookup_place(name, tags, cache)
        if result:
            ok = write_coords(path, result, args.dry_run)
            if ok:
                added += 1
                flag = "[DRY]" if args.dry_run else "✓"
                print(f"  {flag} {name} → {result['coords']}  ({result['name']})")
            else:
                skipped += 1
        else:
            errors += 1
            print(f"  ✗ {name} — 未找到坐标")

        # 每 20 个保存一次缓存
        if i % 20 == 0:
            save_cache(cache)
            print(f"  [进度 {i}/{len(targets)}，缓存已保存]")

    save_cache(cache)
    print(f"\n完成: 添加 {added}，跳过 {skipped}，未找到 {errors}")


if __name__ == "__main__":
    main()
