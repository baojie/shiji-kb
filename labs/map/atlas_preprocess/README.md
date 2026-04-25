# atlas_preprocess — 《中国历史地图集》预处理

将《中国历史地图集》（精装本）第一册（先秦）和第二册（秦汉）的扫描 PDF 处理为可用的图片资源。

## 流水线

```
原书 PDF
  │
  ├─ extract_atlas.py      ── 按图幅裁切 PDF 页，输出单张地图 PDF + manifest.json
  │
  ├─ export_map_jpg.py     ── 从 PDF 提取原始 JPEG，处理旋转/裁切，输出高清 JPG
  │
  ├─ parse_index.py        ── 渲染地名索引页为 PNG，供 OCR 识别
  ├─ parse_ppx_index.py    ── 解析 OCR 输出，生成 place_index_ppx.json
  ├─ correct_index.py      ── 纠错索引数据，生成 place_index_corrected.json
  │
  ├─ fix_book_spread.py    ── 单张图：书脊形变校正（亮度场拉伸 + 折痕修复）
  ├─ batch_fix_spread.py   ── 批量：对全部 53 张双页图执行书脊校正，输出至 map_final/
  │
  └─ build_map_folder.py   ── 裁剪地图主体，生成地名→像素坐标映射 place_coords.json
```

## 快速运行

```bash
# 批量处理所有地图（书脊校正 + 重命名）→ map_final/
python batch_fix_spread.py

# 单张测试
python fix_book_spread.py <input.jpg> <output.jpg>
python fix_book_spread.py <input.jpg> <output.jpg> --vertical   # 横向书脊
```

## 目录结构

```
atlas_preprocess/
  *.py          脚本
  output/       → 版权受限数据（符号链接）
  map_final/    → resource/谭图/（符号链接）
```

所有脚本使用相对于脚本目录的路径，通过符号链接访问版权受限数据。

## 地图说明

- **先秦册**：原始社会、夏、商、西周、春秋、战国，共 22 张
- **秦汉册**：秦、西汉、东汉，共 38 张（含 8 张横向书脊竖版图）
- 单页图（无书脊，7 张）直接复制；双页图（53 张）做书脊形变校正

## 书脊校正物理模型

书页在装订处弯曲（圆柱模型），cos(φ) 同时导致横向压缩和亮度降低，两者同比，因此拉伸系数 `s(x) = I_ref / I(x)`。用 Hann 窗将校正限制在书脊中心 ±8% 宽度范围内，校正后对折痕暗线做局部比较检测并插值修复。
