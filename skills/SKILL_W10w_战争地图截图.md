---
name: SKILL_W10w_战争地图截图
title: Wiki 内务整理 H24：战争事件地图截图
description: 为无地图的战争事件页面，根据战役发生的时代和地点，从谭其骧《中国历史地图集》截取对应历史地图，写入 wiki/public/images/，更新页面 frontmatter 的 image 字段。每轮处理 1 个战役。
---

# SKILL W10w: 战争事件地图截图（H24）

> "战役的地图是战争叙述的锚点。读者需要知道：这场战争发生在哪个历史格局下的什么位置。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| housekeeping 扫描发现战争事件页面缺 `image` 字段 | P2 |
| 精品页建设（W8）发现战争页无地图 | P1 |
| 用户指定某战役需要地图 | P0 |

**触发频率**：每 **19 轮**扫描一次队列（与 H7/H9 同频）。每轮只处理 **1 个战役**。

---

## 二、发现候选

```bash
python3 << 'EOF'
from pathlib import Path
import re, json

ROOT = Path(".")
PAGES = ROOT / "wiki/public/pages"
idx_path = ROOT / "corpus/谭图/place_index.json"
idx = json.loads(idx_path.read_text()) if idx_path.exists() else {"entries": []}
indexed = {e["name"]: e for e in idx["entries"]}

results = []
for f in sorted(PAGES.glob("*.md")):
    text = f.read_text()
    if "event_type: 战争" not in text:
        continue
    if "type: redirect" in text:
        continue
    if "image:" in text:
        continue
    name = f.stem

    # 提取 location
    m_loc = re.search(r'^location:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
    location = m_loc.group(1).strip() if m_loc else ""

    # 提取时间/朝代
    m_date = re.search(r'^date:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
    date_str = m_date.group(1).strip() if m_date else ""

    # 推断时代
    era = _infer_era(date_str, text)

    # 判断优先级：有谭图索引 → P1，有 location 无索引 → P2，无 location → P3
    first_loc = location.split("、")[0].split("，")[0].split(",")[0].strip()
    in_index = first_loc in indexed
    priority = "P1" if in_index else ("P2" if location else "P3")
    results.append((priority, name, first_loc, era, in_index))

def _infer_era(date_str, full_text):
    import re
    m = re.search(r'公元前(\d+)', date_str + full_text)
    if m:
        yr = int(m.group(1))
        if yr > 1046: return "商"
        if yr > 771:  return "西周"
        if yr > 475:  return "春秋"
        if yr > 221:  return "战国"
        return "秦"
    m2 = re.search(r'公元(\d+)年', date_str + full_text)
    if m2:
        yr = int(m2.group(1))
        return "西汉" if yr < 9 else "东汉"
    return "未知"

results.sort()
print(f"战争页面缺地图: {len(results)} 页（P1可直接匹配={sum(1 for r in results if r[0]=='P1')}）")
for pri, name, loc, era, in_idx in results[:20]:
    idx_mark = "✓谭图" if in_idx else "手动"
    print(f"  {pri} {name:20s} | 地点={loc or '—':10s} | 时代={era} | {idx_mark}")
EOF
```

---

## 三、执行步骤（每轮 1 个战役）

### Step 0：选取目标战役

从队列或上方扫描结果取 P1/P2 条目，读取页面：

```bash
head -30 wiki/public/pages/<战役名>.md
```

确认：
- `event_type: 战争` ✓
- `location:` 字段中的战役地点（可能有多个，取**主战场**）
- `date:` 字段中的时间（推断时代）

### Step 1：确定时代与选图

根据 `date:` 推断时代，对照下表选取谭图分区图：

| 时代 | 公元年范围 | 推荐地图（先用全图定位） |
|---|---|---|
| 夏/传说 | 前2070年以前 | `1-05_夏-全图.jpg` |
| 商 | 前1600–前1046 | `1-06_商-全图.jpg` / `1-07_商-中心区域.jpg` |
| 西周 | 前1046–前771 | `1-08_西周-全图.jpg` / `1-09_西周-中心区域.jpg` |
| 春秋 | 前770–前475 | `1-11_春秋-全图.jpg`（不确定时）→ 分区图 |
| 战国 | 前475–前221 | `1-17_战国-全图.jpg`（不确定时）→ 分区图 |
| 秦 | 前221–前206 | `2-02_秦-全图.jpg` → 分区图 |
| 楚汉/西汉 | 前206–前后 | `2-07_西汉-全图.jpg` → 分区图 |

**分区图选择**（春秋/战国时代，按主战场地区）：

| 地区 | 春秋 | 战国 |
|---|---|---|
| 关中/陕西/秦 | `1-12_春秋-晋秦.jpg` | `1-23_战国-秦蜀.jpg` |
| 山西/晋 | `1-12_春秋-晋秦.jpg` | `1-20_战国-赵中山.jpg` |
| 河南中/韩魏 | `1-13_春秋-郑宋卫.jpg` | `1-19_战国-韩魏.jpg` |
| 山东/齐鲁 | `1-14_春秋-齐鲁.jpg` | `1-21_战国-齐鲁宋.jpg` |
| 湖北/楚 | `1-16_春秋-楚吴越.jpg` | `1-24_战国-楚越.jpg` |
| 河北/赵 | — | `1-20_战国-赵中山.jpg` |

**秦/汉分区图**（按主战场郡县）：参见 `SKILL_W10v_地名地图截图.md` §二中的完整列表。

### Step 2：查谭图索引（P1 优先路径）

```python
import json
idx = json.load(open("corpus/谭图/place_index.json"))
hits = [e for e in idx["entries"] if e["name"] == "<主战场地名>"]
for h in hits:
    print(h)
```

- **有索引 → 直接用 `corpus_file` 和已有 `crop` 坐标**（若 crop 已存在可直接复用）
- **无索引 → 进入 Step 2B**

### Step 3：读图定位

```python
from PIL import Image
img = Image.open("corpus/谭图/<corpus_file>")
w, h = img.size
# 先看中间区域
check = img.crop((0, int(h*0.2), int(w*0.6), int(h*0.7)))
check.save("/tmp/war_map_check.jpg", quality=95)
```

用 Read 工具查看 `/tmp/war_map_check.jpg`，在图中找到主战场地名的汉字标注，估算归一化坐标 `(x/w, y/h)`。

### Step 4：裁切并保存

```python
from PIL import Image

corpus_file = "<corpus_file>"
war_name    = "<战役名>"
era         = "<时代>"   # 如"战国"、"春秋"

img = Image.open(f"corpus/谭图/{corpus_file}")
w, h = img.size

# 以主战场为中心，周围留 ~0.15 边距，展示地理语境
crop_norm = [left_n, top_n, right_n, bottom_n]  # 手动填写
box = (int(crop_norm[0]*w), int(crop_norm[1]*h),
       int(crop_norm[2]*w), int(crop_norm[3]*h))
cropped = img.crop(box).convert("RGB")

OUT_NAME = f"{war_name}-{era}.jpg"
OUT_PATH = f"wiki/public/images/{OUT_NAME}"
cropped.save(OUT_PATH, "JPEG", quality=92, subsampling=0)
print(f"✓ {OUT_PATH} ({cropped.size[0]}×{cropped.size[1]})")
```

**裁切原则**：
- 主战场地名居中（不贴边）
- 保留周边邦国/郡县标注，体现战略格局
- 宽度 500–900px，比例约 3:2 或 4:3
- 避免裁入左侧图例列（≈前 0.10）

### Step 5：写回谭图索引

```python
import json
from pathlib import Path

idx_path = Path("corpus/谭图/place_index.json")
idx = json.loads(idx_path.read_text())

# 若主战场已在索引中，补充 crop/image_file
for entry in idx["entries"]:
    if entry["name"] == "<主战场地名>" and entry.get("corpus_file") == corpus_file:
        entry["crop"] = crop_norm
        entry["image_file"] = OUT_NAME
        break
else:
    idx["entries"].append({
        "name": "<主战场地名>",
        "period": era,
        "vol": "vol1",
        "corpus_file": corpus_file,
        "atlas_name": "<谭图地图名>",
        "crop": crop_norm,
        "image_file": OUT_NAME,
        "source": "war-map"
    })
    idx["total_entries"] = len(idx["entries"])

idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2))
print(f"✓ place_index.json 更新：{idx['total_entries']} 条")
```

### Step 6：更新战役页面 frontmatter

读取页面原内容，在 frontmatter 末尾（`---` 之前）**追加**三行：

```yaml
image: images/<战役名>-<时代>.jpg
image_caption: "<谭图地图名>（谭其骧《中国历史地图集》）：<主战场地名>一带"
image_credit: "谭其骧《中国历史地图集》，<时代>·<谭图地图名>"
```

```python
import re, sys
from pathlib import Path

page = Path(f"wiki/public/pages/<战役名>.md")
content = page.read_text("utf-8")

# 在第二个 --- 之前插入三行
fm_end = content.find("\n---\n", 3)
if fm_end == -1:
    print("ERROR: no frontmatter end")
    sys.exit(1)

image_lines = (
    f'\nimage: images/{OUT_NAME}'
    f'\nimage_caption: "{atlas_name}（谭其骧《中国历史地图集》）：{loc_name}一带"'
    f'\nimage_credit: "谭其骧《中国历史地图集》，{era}·{atlas_name}"'
)
new_content = content[:fm_end] + image_lines + content[fm_end:]

# 写入（通过 edit_page.py）
tmp = Path("/tmp/<战役名>_updated.md")
tmp.write_text(new_content, "utf-8")
```

```bash
python3 wiki/scripts/butler/edit_page.py "<战役名>" /tmp/<战役名>_updated.md \
  --summary "H24: 战争地图截图 (<谭图地图名>，<时代>)" --author "butler"
```

---

## 四、成功标准

- [ ] `wiki/public/images/<战役名>-<时代>.jpg` 已存在，图中能看到主战场地名
- [ ] `corpus/谭图/place_index.json` 已写入 crop 坐标（积累供后续复用）
- [ ] wiki 页面 frontmatter 含 `image`、`image_caption`、`image_credit` 三字段
- [ ] 页面写入使用 `edit_page.py`（不直接编辑 .md）

---

## 五、队列条目格式

在 `wiki/logs/butler/housekeeping_queue.md` 中：

```markdown
- [ ] **H24** | [[战役名]] | 缺战争地图，时代=<时代>，地点=<主战场>，谭图→<corpus_file>
  来源: H24 扫描 <日期>
- [ ] **H24-manual** | [[战役名]] | 缺战争地图，地点不明，需手动确认时代/地区
  来源: H24 扫描 <日期>
```

---

## 六、注意事项

- 战役可能涉及多个地点（如"鄢、郢"），截图以**主战场**（决战发生地）为中心
- 时代不明时用 `war_id` 前缀（如 `WAR-005-` = 秦本纪 → 战国/秦时代）推断
- 跨时代战役（如楚汉之争）用**战役发生年份最接近**的那张谭图
- 每 5 个战役完成后，将 `place_index.json` 连同页面一起 commit
- `crop` 坐标一旦写入索引，同地点其他战役可复用，无需重新目视
