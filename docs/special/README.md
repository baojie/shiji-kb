# 史记专项索引

本目录包含史记的专项内容索引，提取并整理特定类型的文献内容。完整 12 项已完成专项的目录见 [special_index.html](special_index.html)：

| 编号 | 专题 | 规模 |
|------|------|------|
| 01 | 太史公曰 | 125篇 · 96.2%覆盖 |
| 02 | 韵文集 | 96篇 · 覆盖82章 |
| 03 | 散文集（含书信·诏令·议论） | 92篇 · 覆盖40章 |
| 04 | 成语典故 | 340条 · 100%定位 |
| 05 | 战争事件 | 736场 · 覆盖103章 |
| 06 | 谥号索引 | 68种 · 470人 |
| 07 | 姓氏宗族 | 11大姓 · 2053人 |
| 08 | 十表结构化 | 10张表 · JSON数据 |
| 09 | 章节结构 | 130篇 · 完整结构 |
| 10 | 君号索引 | 85条 · 11类 · 23封地 |
| 11 | 避讳改字 | 13条规则 · 481处 · 覆盖90章 |
| 12 | 引文索引 | 199种典籍 · 引文38条 · 提及499条 · 疑似概念61条 · 泛引41条 · 覆盖84章 |
| 13 | 人物生卒年 | 512人 · 置信度分级 |
| 14 | 史记中的故事（草稿） | 130章 · 513个独立故事目录 · 已撰写9（五帝本纪完整） |

下列为其中核心专题的详细文件清单：

## 已完成专项

### 01. 太史公曰

- **描述**：太史公司马迁在各篇章末的评论文字
- **数量**：125篇（96.2%覆盖率，130章中5章无此内容）
- **文件**：
  - [../../data/taishigongyue.json](../../data/taishigongyue.json) - 结构化数据（65KB）
  - [../../data/taishigongyue.md](../../data/taishigongyue.md) - Markdown格式（58KB）
  - [taishigongyue.html](taishigongyue.html) - HTML渲染页面（165KB）
  - [taishigongyue.pdf](taishigongyue.pdf) - PDF打印版（2.2MB）
- **访问**：[在线查看](taishigongyue.html) | [下载PDF](taishigongyue.pdf)

### 02. 韵文集

- **描述**：史记中的诗歌体裁作品
- **数量**：96篇（赞80篇、诗歌11篇、赋5篇），覆盖82章
- **文件**：
  - [../../data/yunwen.json](../../data/yunwen.json) - 结构化数据（67KB）
  - [../../data/yunwen.md](../../data/yunwen.md) - Markdown格式（60KB）
  - [yunwen.html](yunwen.html) - HTML渲染页面（159KB）
  - [yunwen.pdf](yunwen.pdf) - PDF打印版（1.95MB）
- **访问**：[在线查看](yunwen.html) | [下载PDF](yunwen.pdf)

### 04. 成语典故

- **描述**：从史记中提取的成语、典故及经典名句
- **数量**：351条，覆盖72章（定位原文134条，38%）
- **文件**：
  - [../../data/chengyu.json](../../data/chengyu.json) - 结构化数据（130KB）
  - [../../data/chengyu.md](../../data/chengyu.md) - Markdown格式（120KB）
  - [chengyu.html](chengyu.html) - HTML渲染页面（280KB）
  - [chengyu.pdf](chengyu.pdf) - PDF打印版（2.95MB）
- **访问**：[在线查看](chengyu.html) | [下载PDF](chengyu.pdf)

### 05. 战争事件

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

### 11. 避讳改字（新增）

- **描述**：《史记》因秦汉帝王、司马迁父祖及后世传抄所涉讳字的改字规则与全书实例
- **数量**：13条规则，481处改字实例，覆盖90章
- **类别**：秦皇讳（2）· 汉帝讳（6）· 家讳（1）· 后讳（4：宣帝/光武/明帝/殇帝）
- **证据**：每条规则附《史记集解三家注》（裴骃/司马贞/张守节）文献引文
- **文件**：
  - [../../data/taboo_characters.rules.json](../../data/taboo_characters.rules.json) - 规则表（含三家注引证）
  - [../../data/taboo_characters.json](../../data/taboo_characters.json) - 全部实例机读结果
  - [../../data/taboo_characters.md](../../data/taboo_characters.md) - Markdown格式
  - [bihui.html](bihui.html) - HTML渲染页面（含类别筛选、原文定位）
- **脚本**：[`scripts/scan_taboo_characters.py`](../../scripts/scan_taboo_characters.py) · [`scripts/render_bihui_html.py`](../../scripts/render_bihui_html.py)
- **访问**：[在线查看](bihui.html)

### 12. 引文索引（新增）

- **描述**：《史记》对先秦典籍（诗经·尚书·易经·春秋·经传·诸子·兵家·辞赋）的引用与提及
- **数量**：199 种典籍，引文 38 条、提及 499 条、疑似概念 61 条（已折叠）、泛引（语·谚·野语·鄙语）41 条，覆盖 84 章
- **方法**：以原文中已标注的书名实体 `〖{典籍〗` 为主线，分三级：引文（有「曰/云」+引语）、提及（书名出现无引语或与其他书名合用）、疑似概念（单字礼/乐孤立出现且未与其他书名合用，多指礼仪/乐制抽象概念）
- **分类**：六经 · 诗经篇章 · 尚书篇章 · 易经篇章 · 经传 · 诸子 · 兵家 · 辞赋 · 史籍 等
- **文件**：
  - [../../data/citations.json](../../data/citations.json) - 结构化数据
  - [../../data/citations.md](../../data/citations.md) - Markdown 格式
  - [citations.html](citations.html) - HTML 渲染页面（含分类筛选、书名搜索、引文/泛引分页）
- **脚本**：[`scripts/extract_citations.py`](../../scripts/extract_citations.py) · [`scripts/render_citations_html.py`](../../scripts/render_citations_html.py)
- **访问**：[在线查看](citations.html)

> 注：旧版编号 02b 散文集、08b 君号索引、08c 避讳改字 已重新编号为 03、10、11。书信、诏书令文已并入 03 散文集，不再单列。

### 14. 史记中的故事（新增，草稿）

- **描述**：按章节拆分的《史记》独立故事索引（中等粒度，每章 3-10 个故事）
- **数量**：130 章 · 513 个故事目录；已撰写完整原文+白话文 9 个（001 五帝本纪全部完成）
- **方法**：以段落 PN 定位每个故事；原文去标注，白话文基于 `data/translation_alignment/NNN.json` 的 `ours` 字段拼接润色
- **文件**：
  - [../../data/stories/catalog.json](../../data/stories/catalog.json) - 诸章故事目录
  - [../../data/stories/NNN.json](../../data/stories/) - 每章故事内容（按需补齐）
  - [stories.html](stories.html) - HTML 渲染页面（含 TOC + 双栏原文/白话排版）
  - [data/stories/](data/stories/) - 供页面 fetch 的镜像
- **访问**：[在线查看](stories.html)

## 规划中的专项（12 起）

君主世系、家族谱系、官职体系、地名大全、邦国变迁、制度沿革、礼仪典章、刑法律令、族群民族、天文历法、器物文物、典籍文献、神话传说、思想学派、对话录 等，持续提取和整理中。

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
- 2026-04-18：新增"避讳改字"专题（13条规则 · 481处实例 · 覆盖90章），含秦皇/汉帝/家讳/后讳分类与三家注文献证据
- 2026-04-18：新增"引文索引"专题（199种典籍 · 引文38 · 提及560 · 泛引41 · 覆盖88章），以 `〖{典籍〗` 实体标签为主线，区分引文/提及/泛引
