"""
CHGIS × 史记 Hello World
=========================
时间范围:公元前 221 年(秦统一) ~ 公元前 100 年(太初末年,司马迁撰《史记》时)

两个视图对比:
  (1) 秦 · 前 221 年(始皇二十六年,初并天下,分三十六郡)
  (2) 西汉初 · 前 195 年(高祖十二年,刘邦崩,郡国并行)

数据源:
  CHGIS V6 Time Series · Prefecture Points
  DOI: 10.7910/DVN/WW1PD6
  URL: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/WW1PD6

  重要说明:CHGIS V6 Time Series 的郡府点图层对 221 BCE–1350 CE 的覆盖
  是"有空缺"(have gaps)的,但秦汉部分基本齐全,足够《史记》使用。

下载方法:
  浏览器打开上述 URL → Access Dataset → Original Format ZIP
  或命令行:
    curl -L -J -O \
      "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/WW1PD6"
  解压到 ./data/ 下即可。脚本会自动递归查找 shp。

用法:
  python3 shiji_chgis.py
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import geopandas as gpd
from shapely.geometry import Point

# ---- 1. 中文字体 ----
for name in ["Noto Sans CJK SC", "Noto Sans CJK JP", "WenQuanYi Micro Hei"]:
    if any(name in f.name for f in fm.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [name]
        break
plt.rcParams["axes.unicode_minus"] = False

HERE = Path(__file__).parent
DATA_DIR = HERE / "data"

# ---- 2. 寻找 CHGIS Prefecture Points shapefile ----
def find_prefecture_pts():
    if not DATA_DIR.exists():
        return None
    for pattern in ["*pref_pts*.shp", "*prefecture*pts*.shp", "*pref*pts*.shp"]:
        hits = list(DATA_DIR.rglob(pattern))
        if hits:
            return hits[0]
    return None

shp = find_prefecture_pts()

# ---- 3. 载入数据 ----
# CHGIS Time Series 字段:
#   NAME_CH / NAME_FT : 中文名(可能繁体)
#   NAME_PY : 拼音
#   BEG_YR / END_YR : 存续起止年 (BCE 为负)
#   BEG_RULE / END_RULE : 起止原因(置/废/改名/并入...)
#   TYPE_CH / TYPE_PY : 类型(郡/國/府...)
#   SYS_ID : 唯一 ID

if shp:
    print(f"[真实数据] 读取 {shp}")
    gdf = gpd.read_file(shp)
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    name_col = next((c for c in ["NAME_CH", "NAME_FT", "NAME_PY"] if c in gdf.columns), gdf.columns[0])
    type_col = next((c for c in ["TYPE_CH", "TYPE_PY"] if c in gdf.columns), None)
    print(f"  记录数:{len(gdf)}  字段:{list(gdf.columns)[:10]}")
else:
    print("[样本数据] 本地没有真实 CHGIS 数据,使用内嵌的秦汉郡国样本\n")
    # 样本数据:秦 36 郡 + 西汉初若干郡国的代表性选择
    # 格式:(名称, 拼音, 经度, 纬度, 秦存在, 汉初存在, 类型)
    # 仅为演示,真实研究请下载 CHGIS。坐标为治所近似位置,参照谭其骧《中国历史地图集》。
    sample = [
        # 秦 36 郡的一部分(前 221 设,前 214 后增至 40+)
        ("內史",    "Neishi",     108.95, 34.27, True,  False, "郡"),  # 咸阳,汉改京兆
        ("漢中郡",  "Hanzhong",   107.02, 33.07, True,  True,  "郡"),
        ("巴郡",    "Ba",         106.55, 29.57, True,  True,  "郡"),
        ("蜀郡",    "Shu",        104.07, 30.67, True,  True,  "郡"),
        ("隴西郡",  "Longxi",     104.63, 35.57, True,  True,  "郡"),
        ("北地郡",  "Beidi",      106.27, 35.45, True,  True,  "郡"),
        ("上郡",    "Shang",      109.72, 36.60, True,  True,  "郡"),
        ("九原郡",  "Jiuyuan",    109.98, 40.58, True,  False, "郡"),  # 汉初弃守
        ("雲中郡",  "Yunzhong",   111.73, 40.48, True,  True,  "郡"),
        ("雁門郡",  "Yanmen",     112.72, 39.50, True,  True,  "郡"),
        ("代郡",    "Dai",        114.12, 39.83, True,  True,  "郡"),
        ("上谷郡",  "Shanggu",    115.50, 40.37, True,  True,  "郡"),
        ("漁陽郡",  "Yuyang",     117.12, 40.37, True,  True,  "郡"),
        ("右北平郡","Youbeiping", 118.68, 41.60, True,  True,  "郡"),
        ("遼西郡",  "Liaoxi",     118.92, 41.18, True,  True,  "郡"),
        ("遼東郡",  "Liaodong",   123.43, 41.80, True,  True,  "郡"),
        ("邯鄲郡",  "Handan",     114.48, 36.62, True,  False, "郡"),  # 汉为赵国
        ("鉅鹿郡",  "Julu",       115.03, 37.22, True,  True,  "郡"),
        ("太原郡",  "Taiyuan",    112.55, 37.87, True,  False, "郡"),  # 汉为韩国/代国
        ("上黨郡",  "Shangdang",  112.87, 36.12, True,  True,  "郡"),
        ("河東郡",  "Hedong",     110.82, 35.03, True,  True,  "郡"),
        ("河內郡",  "Henei",      113.62, 35.08, True,  True,  "郡"),
        ("三川郡",  "Sanchuan",   112.43, 34.62, True,  False, "郡"),  # 汉改河南郡
        ("東郡",    "Dong",       115.43, 35.75, True,  True,  "郡"),
        ("潁川郡",  "Yingchuan",  113.85, 34.02, True,  True,  "郡"),
        ("南陽郡",  "Nanyang",    112.53, 33.00, True,  True,  "郡"),
        ("南郡",    "Nan",        112.23, 30.33, True,  True,  "郡"),
        ("黔中郡",  "Qianzhong",  109.72, 28.45, True,  False, "郡"),  # 汉改武陵
        ("長沙郡",  "Changsha",   112.97, 28.20, True,  False, "郡"),  # 汉为长沙国
        ("九江郡",  "Jiujiang",   117.48, 31.87, True,  False, "郡"),  # 汉初分
        ("會稽郡",  "Kuaiji",     120.58, 30.00, True,  True,  "郡"),
        ("泗水郡",  "Sishui",     117.18, 34.27, True,  False, "郡"),  # 汉改沛郡
        ("薛郡",    "Xue",        117.00, 35.55, True,  False, "郡"),  # 汉改鲁国
        ("齊郡",    "Qi",         118.47, 36.87, True,  False, "郡"),  # 汉为齐国
        ("琅邪郡",  "Langya",     119.45, 36.13, True,  True,  "郡"),
        ("膠東郡",  "Jiaodong",   120.33, 36.70, True,  False, "郡"),  # 汉为胶东国
        ("象郡",    "Xiang",      108.30, 23.45, True,  False, "郡"),  # 汉改南海等
        ("桂林郡",  "Guilin",     110.30, 25.27, True,  False, "郡"),
        ("南海郡",  "Nanhai",     113.27, 23.13, True,  False, "郡"),  # 前 204 后南越国
        # 西汉特有(诸侯国)
        ("楚國",    "Chu",        117.18, 34.27, False, True,  "國"),
        ("齊國",    "Qi-guo",     118.47, 36.87, False, True,  "國"),
        ("趙國",    "Zhao",       114.48, 36.62, False, True,  "國"),
        ("梁國",    "Liang",      115.65, 34.43, False, True,  "國"),
        ("吳國",    "Wu",         119.30, 32.40, False, True,  "國"),  # 刘濞封于广陵
        ("淮南國",  "Huainan",    117.48, 31.87, False, True,  "國"),
        ("燕國",    "Yan",        116.40, 39.90, False, True,  "國"),
        ("長沙國",  "Changsha-g", 112.97, 28.20, False, True,  "國"),
    ]

    gdf = gpd.GeoDataFrame(
        {
            "NAME_CH": [r[0] for r in sample],
            "NAME_PY": [r[1] for r in sample],
            # 编造 BEG_YR/END_YR 以模拟真实 CHGIS 结构
            "BEG_YR":  [-221 if r[4] else -202 for r in sample],
            "END_YR":  [-207 if r[0] in ("內史","三川郡","泗水郡","薛郡","齊郡","膠東郡","象郡","桂林郡","南海郡","黔中郡","長沙郡","邯鄲郡","太原郡","九江郡","九原郡") and not r[5]
                        else -100 for r in sample],
            "TYPE_CH": [r[6] for r in sample],
        },
        geometry=[Point(r[2], r[3]) for r in sample],
        crs="EPSG:4326",
    )
    name_col = "NAME_CH"
    type_col = "TYPE_CH"

# ---- 4. 按年份筛选 ----
def active_in(year: int) -> gpd.GeoDataFrame:
    """返回 year 年存在的行政单位"""
    return gdf[(gdf["BEG_YR"] <= year) & (gdf["END_YR"] >= year)].copy()

# ---- 5. 画两个视图 ----
fig, axes = plt.subplots(1, 2, figsize=(18, 9), dpi=120)

views = [
    (-221, "秦 · 前221年\n始皇二十六年 · 初并天下", axes[0]),
    (-195, "西汉初 · 前195年\n高祖十二年 · 郡国并行",   axes[1]),
]

for year, title, ax in views:
    sub = active_in(year)

    # 浅色底
    ax.set_facecolor("#f6f3ea")
    for lon in range(90, 136, 5):
        ax.axvline(lon, color="white", lw=0.6, zorder=0)
    for lat in range(20, 46, 5):
        ax.axhline(lat, color="white", lw=0.6, zorder=0)

    # 按类型分色:郡=红,國=蓝
    if type_col and type_col in sub.columns:
        jun  = sub[sub[type_col].str.contains("郡", na=False)]
        guo  = sub[sub[type_col].str.contains("國|国", na=False)]
        other = sub[~sub.index.isin(jun.index) & ~sub.index.isin(guo.index)]
        legend_handles = []
        if len(jun):
            jun.plot(ax=ax, color="#c0392b", markersize=45, edgecolor="white",
                     linewidth=1.0, zorder=3, label=f"郡 ({len(jun)})")
            legend_handles.append("郡")
        if len(guo):
            guo.plot(ax=ax, color="#2874a6", markersize=55, edgecolor="white",
                     linewidth=1.0, marker="s", zorder=3, label=f"國 ({len(guo)})")
            legend_handles.append("國")
        if len(other):
            other.plot(ax=ax, color="#7f8c8d", markersize=35, zorder=3,
                       label=f"其他 ({len(other)})")
            legend_handles.append("其他")
        if legend_handles:
            ax.legend(loc="lower left", framealpha=0.85, fontsize=10)
    else:
        sub.plot(ax=ax, color="#c0392b", markersize=45, edgecolor="white",
                 linewidth=1.0, zorder=3)

    # 标注
    for _, row in sub.iterrows():
        x, y = row.geometry.x, row.geometry.y
        ax.annotate(row[name_col], (x, y), xytext=(5, 4),
                    textcoords="offset points", fontsize=7.5,
                    color="#2c3e50", zorder=4)

    ax.set_xlim(92, 128)
    ax.set_ylim(19, 45)
    ax.set_aspect(1.15)
    ax.set_xlabel("经度 °E")
    ax.set_ylabel("纬度 °N")
    ax.set_title(f"{title}\n({len(sub)} 个行政单位)", fontsize=12, pad=8)
    ax.grid(False)

fig.suptitle("《史记》时代的疆域:CHGIS 可视化",
             fontsize=16, fontweight="bold", y=1.00)

plt.tight_layout()
out = HERE / "shiji_chgis.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"\n地图已保存:{out}")
print(f"前 221 年:{len(active_in(-221))} 个单位")
print(f"前 195 年:{len(active_in(-195))} 个单位")
