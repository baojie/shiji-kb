---
name: SKILL_W10y_时间线页建设
title: Wiki 内务整理 H10y：时间线页（timeline）建设规范
description: 为人物、战役、专题建设 type=timeline 页面的完整规范。样本：曹参征战时间线。
---

# SKILL W10y: 时间线页建设

> "时间线是一个人或一件事跨越时间的完整轨迹。把散落在各传、各表的事件，按时序合并到一个页面。"

---

## 一、何时建设

| 触发场景 | 说明 |
|---|---|
| 一个人物有 ≥3 个 event 页，且跨越 ≥3 年 | 建人物征战/生平时间线 |
| 一场战争有多个阶段 event 页 | 建战争时间线 |
| 用户指定某主题需要时间线 | 定向建设 |

---

## 二、Frontmatter 规范

```yaml
---
id: "主题+时间线"          # 例：曹参征战时间线
type: timeline
title: 曹参征战时间线
subject: 曹参               # 主体（人物/事件/主题名）
subject_type: person        # person / event / topic
time_range: ["前209年", "前196年"]
sources: [曹相国世家]        # 主要来源章节
description: 一句话描述时间跨度与内容
tags: [楚汉之际, 征战, 开国功臣]
quality: basic
---
```

---

## 三、段落结构（每时间段）

每段**固定顺序**，不得省略：

### 1. 节标题
```
## 一、前209年 · 初从沛公
```
格式：`## 序号、年代·阶段名`

### 2. 事件页引用
```markdown
**事件页**：[[曹参初从沛公]] [`054-001`]
```
- `[[...]]` 链接到对应 event 页
- `` [`054-001`] `` 方括号+反引号 = event ID 语法（区别于 PN）

### 3. 详细表格
```markdown
| 地点 | 行动 | 对手 | 结果 |
| --- | --- | --- | --- |
| [[胡陵]]、[[方与]] | 将击 | 秦监公军 | 大破之 |
```
- 地点列**必须**用 `[[地名]]` 链接，无论是否已建页

### 4. 路线地图
```markdown
::: route
title: 前209年征战路线
places: 胡陵 → 方与 → 薛 → 丰
:::
```
- `places` 地名必须与 wiki 页面 `label` 完全一致（用于坐标查询）
- 同一时间段可放多个 `:::route` 块（多条路线）
- 无坐标地点自动列入"坐标缺失"说明，**不报错**

### 5. 原文引用
```markdown
> 高祖为沛公而初起也，参以中涓从……（原文）
```

### 6. PN 链接
```
（054-001）
```
全角括号，由 `pn-citation` 插件自动转为可点击链接，指向原文段落。

---

## 四、末尾汇总表

```markdown
## 征战总计

| 项目 | 数量 |
| --- | --- |
| 下国 | 2 |
| 下县 | 122 |
| 得王 | 2 人 |
...
```
附原文 PN。

---

## 五、路线地图技术要点

### 坐标数据源
- 文件：`wiki/public/data/place_coords.json`
- 生成：`python3 wiki/scripts/build_place_coords.py wiki/public/pages --out wiki/public/data/place_coords.json`
- **每次新增地点坐标后必须重新运行**

### 补充缺失坐标
在地点页面 frontmatter 添加：
```yaml
coords: [116.62, 35.02]
coords_name: "胡陵（鱼台附近）"
coords_source: "历史地理推定"
```
然后重建 `place_coords.json`。

### 重复地点处理
同一地点多次经过（如去而复返）时，地图标记自动合并显示序号，如 `1,4`，不遮盖。

### 插件顺序要求
`plugins.json` 中 `route-map` 必须排在 `semantic-block` 和 `semantic-query` **之后**，否则地图不渲染。

---

## 六、创建流程

```bash
# 1. 用 add_page.py 创建页面（wiki 操作规范）
python3 wiki/scripts/butler/add_page.py 曹参征战时间线

# 2. 编辑内容（按上述格式）

# 3. 确认所有地点有坐标，无则补充后重建
python3 wiki/scripts/build_place_coords.py wiki/public/pages --out wiki/public/data/place_coords.json

# 4. 重建注册表
python3 wiki/scripts/build_registry.py wiki/public/pages
```

---

## 七、样本页面

`wiki/public/pages/曹参征战时间线.md`

包含：前209—前196年共8个时间段，每段含表格+路线地图+原文+PN，末尾附征战总计表。
