# place-map 插件

为地名（`type: place`）和邦国（`type: state`）页面在 sidebar 中渲染 Leaflet 地图，标注该地点的历史位置。

---

## 前置条件

页面 frontmatter 中需有 `coords` 字段（经度在前、纬度在后）：

```yaml
---
id: 咸阳
type: place
coords: [108.71, 34.33]
---
```

无 `coords` 或非 place/state 页面时，sidebar 地图区块自动隐藏。

---

## 渲染位置

注入到 sidebar 的 `#sidebar-map` 元素。地图使用 OpenStreetMap 瓦片，标记点为红色圆标，默认缩放级别 7。

---

## 实现

动态从 CDN 加载 Leaflet：

| 资源 | URL |
|---|---|
| Leaflet CSS | `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css` |
| Leaflet JS | `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js` |

切换页面时自动销毁旧地图实例，避免 Leaflet 多实例冲突。

---

## Hook 使用

| Hook | 作用 |
|---|---|
| `onInfobox` | 读取 frontmatter `coords`，初始化或销毁 sidebar 地图 |

---

## 注意

需要网络连接加载 Leaflet 和 OpenStreetMap 地图瓦片。`coords` 字段坐标系为 **WGS84**（十进制度）。
