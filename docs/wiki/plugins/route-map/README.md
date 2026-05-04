# route-map 插件

将 `:::route` 块渲染为带编号标记和方向箭头的 Leaflet 路线地图，用于可视化历史征战路线、迁徙路径等。

---

## 语法

**内联属性写法**：
```markdown
::: route title=前209年征战路线
胡陵 → 方与 → 薛
:::
```

**YAML 写法**：
```markdown
::: route
title: 前209年征战路线
places: 胡陵 → 方与 → 薛
:::
```

地点名以 `→`、`,` 或换行分隔均可。

---

## 坐标解析

地点坐标从 `data/place_coords.json` 加载，结构：
```json
{ "胡陵": [116.8, 35.2], "方与": [116.6, 35.0], ... }
```

无坐标的地点仍出现在地图下方的「未定位地点」图例中，但不绘制路线点。

---

## 渲染效果

- 编号圆形标记（①②③…）标注各地点
- 折线连接相邻地点，折线上显示方向箭头
- 地图自动适配所有已定位点的范围
- 点击标记弹出地点名 popup

---

## Hook 使用

| Hook | 作用 |
|---|---|
| `onAfterRender` | 替换 `:::route` 的占位符为地图容器 `div`，异步初始化 Leaflet 地图 |

`:::route` 块由 `semantic-block` 插件在 `onBeforeRender` 阶段统一提取为占位符，本插件在 `onAfterRender` 阶段拦截并渲染。

---

## 依赖

| 资源 | 来源 |
|---|---|
| Leaflet CSS/JS | CDN（`unpkg.com/leaflet@1.9.4`），需联网 |
| `data/place_coords.json` | 本地构建产物，由 `scripts/butler/build_place_coords.py` 生成 |

---

## 注意

- 依赖 `semantic-block` 插件先于本插件注册（`plugins.json` 中顺序靠前）
- 多个 `:::route` 块在同一页面时各自独立渲染，互不干扰
