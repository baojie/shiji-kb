# 史记专项索引

本目录包含史记的专项内容索引，提取并整理特定类型的文献内容。

## 已完成专项

### 1. 太史公曰

- **描述**：太史公司马迁在各篇章末的评论文字
- **数量**：125篇（96.2%覆盖率，130章中5章无此内容）
- **文件**：
  - [taishigongyue.json](taishigongyue.json) - 结构化数据（65KB）
  - [taishigongyue.md](taishigongyue.md) - Markdown格式（58KB）
  - [taishigongyue.html](taishigongyue.html) - HTML渲染页面（165KB）
  - [taishigongyue.pdf](taishigongyue.pdf) - PDF打印版（2.2MB）
- **访问**：[在线查看](taishigongyue.html) | [下载PDF](taishigongyue.pdf)

## 规划中的专项

### 2. 赞

司马迁以诗歌形式对历史人物和事件的歌颂与评价。

### 3. 书信

史记中收录的历史书信文献。

### 4. 其他

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
