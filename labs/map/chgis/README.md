# chgis — CHGIS × 史记可视化

利用哈佛大学 CHGIS（China Historical GIS）V6 数据，绘制《史记》时代（前 221 年—前 100 年）的郡国分布图。

## 文件

| 文件 | 说明 |
|------|------|
| `shiji_chgis.py` | 主脚本，生成秦（前 221 年）与西汉初（前 195 年）对比地图 |
| `coords_cache.json` | 地名坐标缓存 |
| `shiji_chgis.png` | 输出示例图 |
| `data/` | CHGIS V6 Shapefile 数据（需手动下载） |

## 使用

**1. 下载 CHGIS 数据**

```
浏览器打开：https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/WW1PD6
→ Access Dataset → Original Format ZIP → 解压到 data/
```

**2. 运行**

```bash
python3 shiji_chgis.py
# 输出：shiji_chgis.png
```

数据缺失时脚本自动使用内嵌的秦汉郡国样本数据（约 47 条），坐标参照《中国历史地图集》。

## 数据说明

CHGIS V6 Time Series · Prefecture Points（DOI: 10.7910/DVN/WW1PD6）

关键字段：`NAME_CH`（汉字名）、`BEG_YR` / `END_YR`（存续年份，BCE 为负）、`TYPE_CH`（郡/國/府）。秦汉部分基本齐全，但整体数据集对 221 BCE–1350 CE 有空缺。

## 依赖

```
geopandas  matplotlib  shapely
```
