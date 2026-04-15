---
name: skill-02b2
description: 散文集（诏令、奏疏、书信、檄文、策论、议论）的识别规则、触发短语、段落边界判定与 manifest 维护方法。与韵文集（SKILL_02b1）平行。
---

# SKILL 02b2: 散文识别规则 — 长篇非叙事散文的抽取与整理

> 覆盖：诏令、奏疏/上书、书信、檄文、策论、议论。
> 数据产物：`data/sanwen_manifest.json`（人工精选清单）→ `data/sanwen.json` → `docs/special/sanwen.html`。

---

## 一、类型定义

| 类型 | 典型示例 | 关键触发短语 |
|------|----------|--------------|
| **诏令** | 文帝遗诏（010）、武帝封禅诏（028）、景帝制诏将军（106） | "诏曰"、"制诏御史"、"手诏曰"、"制曰" |
| **奏疏** | 李斯谏逐客书（087，功能上为上书）、主父偃上书（112）、徐乐严安上书（112） | "上书曰"、"乃上疏曰"、"奏曰"、"上言曰" |
| **书信** | 冒顿与文帝国书（110）、吴王濞遗诸侯书（106）、乐毅报燕王书（080） | "遗X书曰"、"报X书"、"与X书" |
| **檄文** | 司马相如谕巴蜀檄（117）、酷吏檄告（122） | "移檄"、"为檄告"、"谕X曰" |
| **策论** | 广武君献策（092）、张良八难（055）、孙武练兵对（065） | "对曰"+长引文、"献策曰" |
| **议论** | 贾谊过秦论上/中/下（006）、褚先生引过秦论（048）、贾生改制建议（084） | 作者名+"曰"+长论述；或独立段落 |

### 与其他索引的边界

- **论赞（太史公曰）** → 已由 `SKILL_02b1` 韵文集处理；散文集**不重复收录**
- **赋/诗歌/韵文赞** → 韵文集专属
- **短对话 / 说辞** → 阈值 `MIN_CHARS=120`（纯文本去标注后字数），低于不收
- **议论 vs 策论**：策论是臣对君的建议；议论是作者脱离情节的思辨（如过秦论）

---

## 二、工作流（三步）

```
chapter_md/*.tagged.md
    ↓ scripts/scan_sanwen_candidates.py
labs/planning/sanwen_candidates.{json,tsv,md}   ← 人工审阅
    ↓ scripts/build_sanwen_manifest.py（+ 手工补充）
data/sanwen_manifest.json
    ↓ scripts/extract_sanwen.py
data/sanwen.json + data/sanwen.md
    ↓ scripts/render_sanwen_html.py
docs/special/sanwen.{html,pdf,json,md}
```

### 2.1 扫描（自动）

`scan_sanwen_candidates.py`：
- 两条路径：**触发短语**（如"乃上书曰"）+ **H2 标题**（如 `## 谏逐客书`）
- 跳过 `::: 太史公曰` 等 fenced block 内的匹配
- 长度阈值 `MIN_CHARS=120`，去重策略：重叠区间只保留第一个
- 输出 TSV 供表格工具审阅

### 2.2 策划 manifest（半自动）

`build_sanwen_manifest.py`：
- 自动采纳：诏令、奏疏、书信、檄文（质量稳定）
- 过滤规则：策论只保留 `>=400 字` 且 H2 标题非通名
- `MANUAL_ENTRIES` 手工补充扫描器遗漏或切分不准的名篇（如过秦论三部）
- `DROP` 白名单剔除误判

**过秦论特别说明**：位于 fenced `:::太史公曰` 块后接多个 `## 贾谊过秦论X` 小节，跨 23 个段落（[117]-[139.4]）。扫描器难以自动识别整体边界，必须手工写入 manifest。褚先生在 048 章的引用版本独立成条。

### 2.3 抽取（自动）

`extract_sanwen.py`：
- 按 `chapter_num + start_para..end_para` 段落区间抽取
- 支持子段号（如 `17.99` 作为"覆盖所有 [17.x]"的上界）
- 段号比较：`"17" < "17.1" < "17.99"`，使用 tuple 顺序

---

## 三、段落边界规则

### 3.1 起点

- 优先用 `##` / `###` H2/H3 段落标题的紧接下一个 `[N]` 段
- 次选：触发短语所在段（如"乃上书曰"所在段）

### 3.2 终点

- 优先用下一个 `##` H2 小标题前的最后一段
- 次选：原文中的"书奏"、"上览之曰"、"上善之"等收束标志
- 诏令：常在"其议之"、"布告天下"收尾

### 3.3 跨段子段号

《史记》tagged 文件中常见 `[117]`、`[117.1]`、`[117.2]` … 结构。抽取时：
- `start=117, end=117.99` → 抽 `[117]` 及全部 `[117.x]`
- `start=117, end=124.2` → 从 `[117]` 到 `[124.2]` 之间所有子段号

---

## 四、已纳入的名篇（MVP，80 篇）

| 类型 | 章节 | 标题 | 段落 |
|------|------|------|------|
| 议论 | 006 | 贾谊过秦论上 | [117]-[124.2] |
| 议论 | 006 | 贾谊过秦论中 | [125]-[134.3] |
| 议论 | 006 | 贾谊过秦论下 | [135]-[139.4] |
| 议论 | 048 | 贾谊过秦论上（褚先生引） | [17]-[17.99] |
| 奏疏 | 087 | 谏逐客书 | [4.1]-[5.1] |
| 奏疏 | 112 | 徐乐严安并上书 | [56]-[62] |
| 奏疏 | 112 | 严安论秦之失 | [70]-[76] |
| 书信 | 110 | 冒顿单于国书 | [39] |
| 书信 | 110 | 文帝回信 | [40]-[41] |
| 书信 | 106 | 吴王濞遗诸侯书 | [9] |
| 诏令 | 010 | 文帝遗诏 | [41.2] |
| 诏令 | 028 | 武帝封禅前制诏御史 | [72]-[78] |
| 诏令 | 060 | 封三王册书 | [9]-[15] |
| 檄文 | 122 | 酷吏檄告 | [37]-[43] |
| 策论 | 055 | 留侯张良献策 | [15]-[21] |
| 策论 | 092 | 广武君献策 | [13]-[19] |
| ... | ... | ...（共 80 篇） | ... |

---

## 五、扩展与维护

### 5.1 新增一条散文

1. 在 `scripts/build_sanwen_manifest.py` 的 `MANUAL_ENTRIES` 中添加
   或直接手工编辑 `data/sanwen_manifest.json`
2. 重跑：
   ```bash
   python3 scripts/build_sanwen_manifest.py
   python3 scripts/extract_sanwen.py
   python3 scripts/render_sanwen_html.py
   ```

### 5.2 剔除误判条目

在 `build_sanwen_manifest.py` 的 `DROP` 集合中加入 `(chapter_num, start_para)`。

### 5.3 调整分类

直接编辑 `data/sanwen_manifest.json` 的 `type` 字段；重跑 extract/render。

---

## 六、质量检查清单

- [ ] `data/sanwen.json` 各条 `content` 字段非空
- [ ] 过秦论四条均被抽出（006 三条 + 048 一条）
- [ ] `docs/special/sanwen.html` 在浏览器打开，实体标注高亮正确
- [ ] `sanwen.pdf` 生成成功（大小 3-5 MB）
- [ ] `special_index.html` 有"散文集"入口

---

## 七、与韵文集的对照

| 维度 | 韵文集 (02b1) | 散文集 (02b2) |
|------|---------------|---------------|
| 存储源 | `::: 赞/诗歌/赋` 块标记 | `data/sanwen_manifest.json`（段落范围）|
| 抽取依据 | fenced 块边界 | 段落号 `[N.M]` 范围 |
| 是否改 tagged.md | 是（已完成） | 否（MVP 不改） |
| 手工量 | 中（5 赋 + 11 诗歌手工标题）| 高（策论/议论需逐条审阅）|

> 后续可选：将 manifest 中的条目回写为 `::: 诏令 / ::: 奏疏 / ...` 块标记，以便与韵文集处理方式统一。由于涉及大规模修改 tagged 文件，需逐条审阅后分批执行。

---

## 八、相关文件

| 文件 | 作用 |
|------|------|
| `scripts/scan_sanwen_candidates.py` | 触发短语+H2 扫描器 |
| `scripts/build_sanwen_manifest.py` | 合并筛选 → manifest |
| `scripts/extract_sanwen.py` | manifest → sanwen.json |
| `scripts/render_sanwen_html.py` | sanwen.json → HTML/PDF |
| `labs/planning/sanwen_candidates.{json,tsv,md}` | 候选清单（参考）|
| `data/sanwen_manifest.json` | 精选清单（权威）|
| `data/sanwen.json` / `.md` | 最终数据 |
| `docs/special/sanwen.html` / `.pdf` | 展示页面 |

---

> 创建：2026-04-15
>
> MVP 版本：80 篇 · 覆盖 48 章 · 含过秦论四种
