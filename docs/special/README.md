# 史记专项索引

本目录包含史记的专项内容索引，提取并整理特定类型的文献内容。

## 已完成专项

### 1. 太史公曰

- **描述**：太史公司马迁在各篇章末的评论文字
- **数量**：125篇（96.2%覆盖率，130章中5章无此内容）
- **文件**：
  - [../../data/taishigongyue.json](../../data/taishigongyue.json) - 结构化数据（65KB）
  - [../../data/taishigongyue.md](../../data/taishigongyue.md) - Markdown格式（58KB）
  - [taishigongyue.html](taishigongyue.html) - HTML渲染页面（165KB）
  - [taishigongyue.pdf](taishigongyue.pdf) - PDF打印版（2.2MB）
- **访问**：[在线查看](taishigongyue.html) | [下载PDF](taishigongyue.pdf)

### 2. 韵文集

- **描述**：史记中的诗歌体裁作品
- **数量**：96篇（赞80篇、诗歌11篇、赋5篇），覆盖82章
- **文件**：
  - [../../data/yunwen.json](../../data/yunwen.json) - 结构化数据（67KB）
  - [../../data/yunwen.md](../../data/yunwen.md) - Markdown格式（60KB）
  - [yunwen.html](yunwen.html) - HTML渲染页面（159KB）
  - [yunwen.pdf](yunwen.pdf) - PDF打印版（1.95MB）
- **访问**：[在线查看](yunwen.html) | [下载PDF](yunwen.pdf)

### 3. 成语典故

- **描述**：从史记中提取的成语、典故及经典名句
- **数量**：351条，覆盖72章（定位原文134条，38%）
- **文件**：
  - [../../data/chengyu.json](../../data/chengyu.json) - 结构化数据（130KB）
  - [../../data/chengyu.md](../../data/chengyu.md) - Markdown格式（120KB）
  - [chengyu.html](chengyu.html) - HTML渲染页面（280KB）
  - [chengyu.pdf](chengyu.pdf) - PDF打印版（2.95MB）
- **访问**：[在线查看](chengyu.html) | [下载PDF](chengyu.pdf)

### 4. 战争事件

- **描述**：史记中记载的所有战争事件（多源融合）
- **数量**：736个战争，覆盖103章（多源战争16个）
- **时间跨度**：前2690年（阪泉之战）— 前119年（漠北之战）
- **文件**：
  - [../../data/wars.json](../../data/wars.json) - 结构化数据（专项索引格式）
  - [../../data/wars.md](../../data/wars.md) - Markdown格式
  - [../../kg/events/data/wars.json](../../kg/events/data/wars.json) - 完整数据（2.5MB，含交战双方、伤亡等）
  - [wars.html](wars.html) - HTML渲染页面
  - wars.pdf - PDF打印版（待生成）
- **访问**：[在线查看](wars.html) | 下载PDF（待生成）

## 规划中的专项

### 5. 书信

史记中收录的历史书信文献。

### 6. 其他

持续提取和整理史记中的各类专项内容。

## 提取流程

1. **提取**：运行 `scripts/extract_taishigongyue.py` 提取内容
2. **渲染**：运行 `scripts/render_taishigongyue_html.py` 生成HTML
3. **生成PDF**：运行 `scripts/generate_pdf.py` 生成PDF打印版
4. **访问**：通过主页 → 专项索引 → 太史公曰

## 数据格式

### JSON格式示例

```json
[
  {
    "chapter_num": "002",
    "chapter_title": "夏本纪",
    "content": "〖@太史公〗曰：..."
  }
]
```

## 使用说明

- 每个专项内容包含章节编号、标题和原文
- 原文保留实体标注（〖TYPE 内容〗格式）
- HTML渲染时会将实体标注转换为带样式的span标签
- 支持点击章节标题跳转到对应章节

## 更新记录

- 2026-03-18：创建专项索引系统，完成"太史公曰"提取和渲染
