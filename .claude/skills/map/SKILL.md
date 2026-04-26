---
name: map
description: 为 shiji-kb wiki 页面从谭其骧《中国历史地图集》自动裁切历史地图截图，并生成 frontmatter images 片段。适用于 type=place（地名）和 type=state（诸侯国/侯国/邦国）页面。当用户说 /map PAGE、/map PAGE 时间、/map PAGE all 时触发；/enrich 对 state/place 类型页面补图时也应调用。前提：页面 frontmatter 必须有 coords 字段（无 coords 则先补 coords 再调用）。
---

# /map — 谭图地图裁切

## 用法

```
/map PAGE           → 裁切该页面所有匹配时代的地图（等同 all）
/map PAGE 时间      → 只裁切指定时代（春秋/战国/秦/西汉/东汉/西周/商/夏）
/map PAGE all       → 裁切所有匹配时代
```

## 执行步骤

**第一步：确认页面有 coords**

读取 `wiki/public/pages/{PAGE}.md`，检查 frontmatter 是否含 `coords: [lon, lat]`。
- 若有 → 继续
- 若无 → 先考证坐标，再补写后继续（不要直接停止）

**坐标考证优先级**（coords 缺失时）：

| 来源 | 说明 |
|------|------|
| **史记三家注**（集解/索隐/正义） | 正义常注"在今某州某县"，是地望最直接的文献依据 |
| **汉书·地理志** | 郡县建置记录，侯国/县治今地的标准参照 |
| **谭图目视** | 在对应时代地图中找到地名标注，反推经纬度 |

考证结果写入页面 `## 地理位置`（或 `## 地理位置与建置`），注明来源：如"据《汉书·地理志》钜鹿郡"、"据《史记正义》注……"。

**第二步：运行脚本（⚠️ 必须加 `--write`）**

从仓库根执行（不要从 wiki/ 子目录执行）：

```bash
# 标准用法：裁切所有时代 + 自动写入页面 + 自动记录修订（一步到位）
python3 .claude/skills/map/scripts/map_page.py {PAGE} --write

# 先预览匹配哪些地图（不实际裁切）
python3 .claude/skills/map/scripts/map_page.py {PAGE} --list-maps

# 指定时代
python3 .claude/skills/map/scripts/map_page.py {PAGE} {时代} --write

# 调整裁切范围
python3 .claude/skills/map/scripts/map_page.py {PAGE} --crop-deg 4.0 --write
```

`--write` 效果：① 生成图片 ② append-only 写入 frontmatter ③ 自动调用 `record_revision.py --author map`

**不得省略 `--write`**。不加 `--write` 时只打印 YAML 片段，不写文件，不记修订，Special:Recent 看不到变化。

验证：脚本末尾应出现 `✓ {PAGE} rev=...`，否则写入失败。

## 常见问题

| 问题 | 处理 |
|------|------|
| "坐标在地图边缘" | 加 `--crop-deg` 缩小，或检查 coords 是否正确 |
| 某时代无匹配 | 该坐标不在该时代任何图幅范围内，正常 |
| 裁切结果偏移 | map_extents.json 的 lon/lat_range 是近似值；可在 `labs/map/crop_state_map.py` 用精确 crop box 替代 |
| 夏/商时代图太粗略 | 全图分辨率低，可改用 `--crop-deg 2.0` 放大 |

## 地理范围注册表

`~/.claude/skills/map/references/map_extents.json`

每条记录：`file`（源文件名）、`periods`（适用时代）、`lon_range`、`lat_range`（WGS84近似范围）、`content`（图像内容区归一化坐标）、`priority`（1=精细区域图，3=全国图）。

若某地点所属时代缺失，在 map_extents.json 新增对应条目即可。
