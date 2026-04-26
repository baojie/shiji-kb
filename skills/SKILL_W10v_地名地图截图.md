---
name: SKILL_W10v_地名地图截图
title: Wiki 内务整理 H23：地名地图截图
description: 为无地图的地名/邦国页面，从谭图历史地图集中找到正确分区图，截取包含该地名的区域，写入 wiki/public/images/，更新页面 frontmatter，并将裁切坐标写回 corpus/谭图/place_index.json 积累映射。
---

# SKILL W10v: 地名地图截图（H23）

> "谭图是最权威的中国历史地理基准。每个地名页都应当锚定到具体的历史地图区域。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| housekeeping 扫描发现 place/state 页面缺 `image` 字段 | P2 |
| 精品页建设（W8）发现页面无地图 | P1 |
| 用户指定某地名需要地图 | P0 |

---

## 二、发现候选（扫描方法）

```bash
# 扫描无图的 place/state 页面，优先匹配谭图索引
python3 << 'EOF'
import json
from pathlib import Path

ROOT = Path(".")
index = json.loads((ROOT / "corpus/谭图/place_index.json").read_text())
indexed = {e["name"]: e for e in index["entries"]}
pages_dir = ROOT / "wiki/public/pages"

results = []
for f in sorted(pages_dir.glob("*.md")):
    text = f.read_text()
    if "type: place" not in text and "type: state" not in text:
        continue
    if "image:" in text:
        continue
    name = f.stem
    entry = indexed.get(name)
    priority = "P1" if entry else "P2"
    results.append((priority, name, entry))

print(f"无图地名: {len(results)} 页（P1可直接匹配={sum(1 for r in results if r[0]=='P1')}）")
for pri, name, e in results[:20]:
    if e:
        print(f"  {pri} {name:10s} → {e['corpus_file']} | {e['atlas_name']}")
    else:
        print(f"  {pri} {name:10s} → 需手动查谭图")
EOF
```

---

## 三、执行步骤

### Step 0：确认目标地名

```bash
# 检查页面现状
head -20 wiki/public/pages/<地名>.md

# 查 place_index.json 是否有记录
python3 -c "
import json
idx = json.load(open('corpus/谭图/place_index.json'))
hits = [e for e in idx['entries'] if e['name'] == '<地名>']
for h in hits: print(h)
"
```

### Step 0.5：考证坐标（地名位置不明时）

确定 `coords` 前，按以下优先级查阅文献：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | **史记三家注**（集解/索隐/正义） | 正义尤多地理注，常注"在今某州某县"；索隐补充音义和地望 |
| 2 | **汉书·地理志** | 记录西汉郡县建置，是侯国/郡县今地考证的标准依据 |
| 3 | **后汉书·郡国志** | 东汉沿革，补充汉书未载的变化 |
| 4 | **谭图地图** | 目视确认地名在地图上的位置，反推坐标 |

**三家注检索方式**：在 `chapter_md/*.tagged.md` 已有注文标注；或直接查 [ctext.org 史记正义/集解/索隐](https://ctext.org/shiji/zhs)。

**汉书地理志检索**：[ctext.org 汉书·地理志](https://ctext.org/han-shu/di-li-zhi-shang/zhs)，搜索地名所属郡，对照今地。

**注意**：以考证结果写入页面 `## 地理位置` 散文，并注明来源（如"据《汉书·地理志》钜鹿郡"、"据《史记正义》注……"）。

### Step 1：查找正确的谭图分区图

**情况A：地名在 place_index.json 中**

直接取 `corpus_file` 字段，即对应的谭图文件名（如 `1-20_战国-赵中山.jpg`）。

**情况B：地名不在索引中**

按地名所属时代和地区从下表选取分区图。不确定时先用全图目视定位，再切换分区图。

#### 第一册·先秦（vol1）

| 文件名 | 谭图地图名 | 覆盖地区/时期 |
|---|---|---|
| `1-01_参考-全国（先秦册）.jpg` | 中华人民共和国全图 | 参考底图，含现代地名 |
| `1-02_原始社会-遗址.jpg` | 原始社会遗址图 | 旧石器~新石器遗址 |
| `1-03_原始社会-旧石器遗址.jpg` | 原始社会早期遗址图 | 旧石器时代 |
| `1-04_原始社会-新石器遗址.jpg` | 黄河流域原始社会晚期遗址图 | 新石器时代 |
| `1-05_夏-全图.jpg` | 夏时期全图 | **夏**·全域 ⚠️ 注意：此图显示西北方向（银川/兰州/西安一带），**不包含中原（开封/郑州）地区**，中原地名请勿选此图 |
| `1-06_商-全图.jpg` | 商时期全图 | **商**·全域 |
| `1-07_商-中心区域.jpg` | 商时期中心区域图 | **商**·中原核心区 |
| `1-08_西周-全图.jpg` | 西周时期全图 | **西周**·全域 |
| `1-09_西周-中心区域.jpg` | 西周时期中心区域图 | **西周**·关中/中原核心 |
| `1-10_西周-宗周成周.jpg` | 宗周、成周附近 | **西周**·镐京/洛邑周边（半页） |
| `1-11_春秋-全图.jpg` | 春秋时期全图 | **春秋**·全域概览 |
| `1-12_春秋-晋秦.jpg` | 晋 秦 | **春秋**·晋（山西/河北）、秦（陕西/甘肃） |
| `1-13_春秋-郑宋卫.jpg` | 郑 宋 卫 | **春秋**·郑（河南中）、宋（豫东）、卫（豫北/冀南） |
| `1-14_春秋-齐鲁.jpg` | 齐 鲁 | **春秋**·齐鲁（山东） |
| `1-15_春秋-北燕.jpg` | 北燕 | **春秋**·燕（河北北/辽西，半页） |
| `1-16_春秋-楚吴越.jpg` | 楚 吴 越 | **春秋**·楚（湖北/皖赣）、吴越（苏浙） |
| `1-17_战国-全图.jpg` | 战国时期全图 | **战国**·全域概览（不确定时优先用此） |
| `1-18_战国-诸侯形势.jpg` | 诸侯形势图（前350年） | **战国中期**·七雄形势 |
| `1-19_战国-韩魏.jpg` | 韩 魏 | **战国**·韩（豫西/晋南）、魏（豫中/晋/冀南）、上党 |
| `1-20_战国-赵中山.jpg` | 赵 中山 | **战国**·赵（晋北/冀西）、中山（冀中） |
| `1-21_战国-齐鲁宋.jpg` | 齐 鲁 宋 | **战国**·齐（山东）、鲁、宋（豫东/苏北） |
| `1-22_战国-燕.jpg` | 燕 | **战国**·燕（河北北/辽宁） |
| `1-23_战国-秦蜀.jpg` | 秦 蜀 | **战国**·秦（陕西/甘肃）、蜀（四川） |
| `1-24_战国-楚越.jpg` | 楚 越 | **战国**·楚（湖北/湖南/皖赣）、越（浙闽） |

#### 第二册·秦汉（vol2）

| 文件名 | 谭图地图名 | 覆盖地区/时期 |
|---|---|---|
| `2-01_参考-全国（秦汉册）.jpg` | 中华人民共和国全图 | 参考底图，含现代地名 |
| `2-02_秦-全图.jpg` | 秦时期全图 | **秦**·全域概览 |
| `2-03_秦-关中.jpg` | 关中诸郡 | **秦**·关中（陕西渭河流域）、巴蜀 |
| `2-04_秦-山东南.jpg` | 山东南部诸郡 | **秦**·豫/皖/苏/浙/闽/赣诸郡 |
| `2-05_秦-山东北.jpg` | 山东北部诸郡 | **秦**·山东半岛/冀/晋/辽诸郡 |
| `2-06_秦-淮汉以南.jpg` | 淮汉以南诸郡 | **秦**·淮河/汉水以南（楚地/岭南） |
| `2-07_西汉-全图.jpg` | 西汉时期全图 | **西汉**·全域概览（不确定时优先用此） |
| `2-08_西汉-司隶.jpg` | 司隶部（长安附近） | **西汉**·关中/三辅、河东、弘农（豫西） |
| `2-09_西汉-并州朔方.jpg` | 并州、朔方刺史部 | **西汉**·并州（山西/内蒙南）、朔方（河套） |
| `2-10_西汉-兖豫青徐.jpg` | 兖豫青徐刺史部 | **西汉**·兖（鲁西/豫东）、豫（河南）、青（山东）、徐（苏皖北） |
| `2-11_西汉-东郡北海.jpg` | 东郡北海间诸郡 | **西汉**·东郡/北海（鲁西北/冀东，半页） |
| `2-12_西汉-荆州.jpg` | 荆州刺史部 | **西汉**·荆州（湖北/湖南） |
| `2-13_西汉-扬州.jpg` | 扬州刺史部 | **西汉**·扬州（皖/苏/浙/赣） |
| `2-14_西汉-冀州.jpg` | 冀州刺史部 | **西汉**·冀州（河北/晋东），含井陉、常山 |
| `2-15_西汉-幽州.jpg` | 幽州刺史部（渤海附近） | **西汉**·幽州（冀北/辽宁） |
| `2-16_西汉-益州北.jpg` | 益州刺史部北部 | **西汉**·益州北部（四川盆地/汉中） |
| `2-17_西汉-益州南.jpg` | 益州刺史部南部 哀牢 | **西汉**·益州南部（云贵）、哀牢（滇西） |
| `2-18_西汉-凉州.jpg` | 凉州刺史部 | **西汉**·凉州（甘肃/宁夏/青海东） |
| `2-19_西汉-交阯.jpg` | 交阯刺史部（日南南部） | **西汉**·交阯（越南北/两广） |
| `2-20_西汉-西域.jpg` | 西域都护府 | **西汉**·西域（新疆/中亚） |
| `2-21_西汉-匈奴.jpg` | 匈奴及邻族 | **西汉**·匈奴（蒙古高原，半页） |
| `2-22_东汉-全图.jpg` | 东汉时期全图 | **东汉**·全域概览 |
| `2-23_东汉-司隶.jpg` | 司隶刺史部（洛阳附近） | **东汉**·司隶（洛阳/三河/弘农） |
| `2-24_东汉-兖豫青徐.jpg` | 兖豫青徐刺史部 | **东汉**·兖/豫/青/徐 |
| `2-25_东汉-颖川.jpg` | 颖川间诸郡 | **东汉**·颖川/汝南（豫中南，半页） |
| `2-26_东汉-冀州.jpg` | 冀州刺史部 | **东汉**·冀州（河北） |
| `2-27_东汉-荆州.jpg` | 荆州刺史部（宛县附近） | **东汉**·荆州（湖北/湖南/豫南） |
| `2-28_东汉-扬州.jpg` | 扬州刺史部 | **东汉**·扬州（皖/苏/浙/赣） |
| `2-29_东汉-益州北.jpg` | 益州刺史部北部 | **东汉**·益州北（四川/汉中） |
| `2-30_东汉-益州南.jpg` | 益州刺史部南部 | **东汉**·益州南（云贵） |
| `2-31_东汉-凉州.jpg` | 凉州刺史部 | **东汉**·凉州（甘肃/宁夏） |
| `2-32_东汉-并州.jpg` | 并州刺史部 | **东汉**·并州（山西/内蒙南） |
| `2-33_东汉-幽州.jpg` | 幽州刺史部 | **东汉**·幽州（冀北/辽宁） |
| `2-34_东汉-交阯.jpg` | 交阯刺史部 | **东汉**·交阯（越南北/两广） |
| `2-35_东汉-西域.jpg` | 西域都护府 | **东汉**·西域（新疆/中亚） |
| `2-36_东汉-鲜卑.jpg` | 鲜卑及邻族 | **东汉**·鲜卑（蒙古/东北，半页） |

**选图原则**：
- **夏全图（1-05）禁止用于中原地名**：夏·全图实际显示西北区域（银川/兰州/西安），中原（开封/郑州/洛阳附近）地名截夏朝图时直接跳过
- 同一地点跨越多时期时，优先选**地名所在史记叙事的朝代**对应地图
- 《史记》涉及地名多为先秦~西汉，东汉地图仅在《汉书》互证或地名延续时参考
- 半页地图（`crop_top_half: true`）覆盖范围较小，不确定时先用相邻全页图确认位置

### Step 2：读图确认地名位置

```python
from PIL import Image
img = Image.open("corpus/谭图/<corpus_file>")
w, h = img.size
print(f"{w}×{h}")

# 先裁出中间区域目视检查
crop = img.crop((0, int(h*0.2), int(w*0.6), int(h*0.7)))
crop.save("/tmp/check.jpg", quality=95)
```

用 Read 工具查看 `/tmp/check.jpg`，在图中找到目标地名标注，目视估算其在**全图**中的归一化坐标 `(x/w, y/h)`。

### Step 3：确定裁切框

以目标地名为中心，裁取能展示地理语境的区域：

```python
# 归一化坐标 [left, top, right, bottom]，0.0~1.0
# 地名居中，周围留约 0.15~0.20 的边距（以展示相邻地名为地理语境）
crop_norm = [left_n, top_n, right_n, bottom_n]

# 转换为像素并裁切
box = (int(left_n*w), int(top_n*h), int(right_n*w), int(bottom_n*h))
cropped = img.crop(box)
```

**裁切原则**：
- 目标地名应出现在图中偏中心位置（不要贴边）
- 保留能说明地理意义的周边地名（郡治、邻国、山川）
- 避免裁入图例列（通常在图的最左侧 ≈ 0.10 范围内）
- 输出尺寸建议 500~900px 宽，比例约 3:2 或 4:3

### Step 4：保存图片

```python
OUT_NAME = "<地名>-<朝代>.jpg"   # 如 "元氏-战国.jpg"
OUT_PATH = f"wiki/public/images/{OUT_NAME}"

cropped = cropped.convert("RGB")
cropped.save(OUT_PATH, "JPEG", quality=92, subsampling=0)
print(f"✓ {OUT_PATH} ({cropped.size[0]}×{cropped.size[1]})")
```

### Step 5：将裁切坐标写回 place_index.json

```python
import json
from pathlib import Path

idx_path = Path("corpus/谭图/place_index.json")
idx = json.loads(idx_path.read_text())

for entry in idx["entries"]:
    if entry["name"] == "<地名>" and entry.get("corpus_file") == "<corpus_file>":
        entry["crop"] = crop_norm          # [left, top, right, bottom]
        entry["image_file"] = OUT_NAME     # wiki/public/images/ 下的文件名
        break
else:
    # 地名不在索引中，追加新条目
    idx["entries"].append({
        "name": "<地名>",
        "period": "<朝代>",
        "vol": "vol1",  # 或 vol2
        "atlas": "<atlas编号>",
        "corpus_file": "<corpus_file>",
        "atlas_name": "<谭图地图名>",
        "crop": crop_norm,
        "image_file": OUT_NAME,
        "source": "manual"
    })
    idx["total_entries"] = len(idx["entries"])

idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2))
print(f"✓ place_index.json 更新，条目 {idx['total_entries']} 条")
```

### Step 6：更新 wiki 页面 frontmatter

```bash
# 准备更新后的页面内容（保持原内容，只在 frontmatter 末尾加字段）
python3 wiki/scripts/butler/edit_page.py <地名> /tmp/<地名>_updated.md \
  --summary "H23: 添加谭图地图截图（<谭图地图名>）" --author "butler"
```

新增的 frontmatter 字段：
```yaml
image: images/<地名>-<朝代>.jpg
image_caption: "<谭图地图名>（谭其骧《中国历史地图集》），<地名>位于<地理描述>"
image_credit: "谭其骧《中国历史地图集》<第N册>，<朝代>·<谭图地图名>（页<atlas编号>）"
```

---

## 四、成功标准

- [ ] 图片已保存到 `wiki/public/images/<地名>-<朝代>.jpg`
- [ ] 图中能清晰看到目标地名的汉字标注
- [ ] `corpus/谭图/place_index.json` 已写入 `crop` 和 `image_file` 字段
- [ ] wiki 页面 frontmatter 已更新 `image`、`image_caption`、`image_credit`
- [ ] 使用 `edit_page.py` 完成页面写入（不直接编辑 .md 文件）

---

## 五、工具与脚本

| 工具/文件 | 用途 |
|---|---|
| `corpus/谭图/place_index.json` | 地名→谭图分区图映射表（含已裁切坐标） |
| `corpus/谭图/*.jpg` | 谭图原图（24+36 张） |
| `labs/map/crop_state_map.py` | 已有裁切定义的批量工具（邦国级） |
| `wiki/scripts/butler/edit_page.py` | 写入 wiki 页面（必须用此脚本，禁止直接编辑） |
| `PIL.Image` | 裁切和格式转换 |

---

## 六、队列条目格式

在 `wiki/logs/butler/housekeeping_queue.md` 中的格式：

```markdown
- [ ] **H23** | [[地名]] | 缺地图，谭图索引→ corpus_file=<文件名> 朝代=<朝代>
  来源: H23 扫描 <日期>
```

无谭图记录的地名：
```markdown
- [ ] **H23-manual** | [[地名]] | 缺地图，需手动查谭图分区图（tags: <朝代/地区>）
  来源: H23 扫描 <日期>
```

---

## 七、注意事项

- 单个原子操作只处理 **1 个地名**，完成后进入下一轮
- 每 5 个地名完成后将 `place_index.json` 连同页面一起 commit
- `place_index.json` 的 `crop` 坐标一旦写入，后续同一地名可直接复用，无需重新目视确认
- 谭图每张地图上已印有地名汉字，确认方法：在图中找到汉字标注即可，无需与外部数据库对照
