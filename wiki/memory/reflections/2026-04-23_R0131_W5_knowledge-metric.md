# Butler 反思 v8 · 知识量度量 + 诊断链接缺口

**日期**: 2026-04-23
**上轮**: v7-bug (鲁桓公严格匹配)
**本轮主题**: 引入总知识量 K、首次快照、诊断暴露的最大缺口

---

## 1. 背景

用户要求："给史记 wiki 定义一个总'知识量'的度量，以跟踪知识的增长"。

此前 butler 的评估维度是 per-page (`quality_score`)，没有全站总量度量。
引入 K 后可以：

- 每次写入/反思后打一个时间点快照
- 观察"本次行动带来了多少知识增量"
- 诊断系统性缺口（如链接命中率、低型量覆盖）

---

## 2. 度量定义

```
K = Σ_page  page_k
page_k = log2(1 + bytes) × (1 + min(links_density, 5)) × type_weight × quality_norm

type_weight = {person/event/place/state:1.0, topic:0.8, surface:0.5, other:0.6}
quality_norm = clamp(quality_score / 30, 1.0, 3.0)
links_density = wikilinks / (bytes / 1000)
```

### 设计权衡

- **log2(bytes)** 而非线性：防止一个 3000 行巨页压过 30 个 100 行页
- **links_density** 加成：链接多的页面"嵌入网络"程度高，更有价值
- **type_weight**: person/event/place 是一等公民；surface 是辅助索引
- **quality_norm** 1-3 倍：quality_score 差的页面不被"体积奖励"掩盖

## 3. 首次快照（2026-04-23 01:05）

```
K              = 13336.34
pages          = 229  (+1, 新增巨鹿之战)
featured       = 10
total_bytes    = 268,430
wikilinks      = 1995 total / 414 resolved
link_hit_rate  = 20.8%     ← 核心诊断
revisions      = 1307
top3           = 项羽(189), 刘邦(186), 孔子(166)
```

**上轮末态 (未打快照, 从 pages.json 反推)**:
- pages = 228, featured = 9, K ≈ 13259

**本轮 ΔK = +77 (+0.58%)**, 来自：
- 新增 1 event 精品页 (巨鹿之战, 3.5 KB)
- 2 person 页扩写 (张良 / 韩信) 的 refs 累加

---

## 4. 最大诊断：链接命中率仅 20.8%

wiki 里每 5 个 wikilink 就有 4 个指向不存在页面。top 缺失：

| 次数 | 目标 | 类型 |
| --- | --- | --- |
| 54 | 014_十二诸侯年表 | chapter |
| 53 | 008_高祖本纪 | chapter |
| 43 | 130_太史公自序 | chapter |
| 32 | 015_六国年表 | chapter |
| 32 | 018_高祖功臣侯者年表 | chapter |
| 32 | 007_项羽本纪 | chapter |
| 31 | 006_秦始皇本纪 | chapter |
| 30 | 005_秦本纪 | chapter |
| 29 | 039_晋世家 | chapter |
| 29 | 033_鲁周公世家 | chapter |

**观察**: 前 25 名**全部是"章节页" (NNN_章名)** —— 目前 wiki 根本没建章节类型页面。
所有精品页里的"相关章节"链接都是死链。

这是一个系统性缺口：只要批量生成 130 个章节 stub（每篇极短、指向 `data/chapters/NNN_*.tagged.md`
的外部索引），命中率可一步从 20% → 40%+。

---

## 5. 提案 (≤3)

### 提案 23：批量生成 130 章"章节页" (stub)

**操作**：新增 `wiki/scripts/butler/generate_chapter_pages.py`，扫描 `data/chapters/NNN_*.tagged.md`
生成 130 个 `wiki/public/pages/NNN_章名.md`，每篇：

```yaml
---
id: NNN_章名
type: chapter
label: 章名  # 如"项羽本纪"
chapter_no: NNN
aliases: ["NNN", "章名"]
tags: [本纪/世家/列传/表/书]
---

# NNN 章名

[[章名]]为《史记》第 N 篇，属XX体。全文 X 段，记 ...（从 tags/sku 提炼一句话 lead）。

*查看原文*: [data/chapters/NNN_章名.tagged.md](...)
*人物*: [[X]] · [[Y]]
```

**预期**：K 一次增加 ~4000 (130 × 30 avg page_k)，link_hit_rate 跃升至 40-50%。

**风险**：章节页"体积虚增" K。对策：在 `TYPE_WEIGHT` 里 chapter 给 0.4，避免淹没人物页。

### 提案 24：知识量仪表板 (homepage footer)

在 `renderHome` 的 footer 新增一个 `<div class="k-panel">`：

```
📊 知识量 13,336 · 229 页 (10 精品) · 链接命中 20.8% · 2026-04-23
```

点击展开 top10 贡献页。JSON 源文件 `wiki/data/knowledge_latest.json`。

### 提案 25：K 时间线小图

主页 `#?stats` 路由渲染 `wiki/data/knowledge_timeline.jsonl` 的折线图，
纯 SVG + 无依赖（~50 行 JS）。每次 butler 反思后 ΔK 一目了然。

---

## 6. 下轮优先级（queue 调整）

- **P0** 新增：批量章节 stub（提案 23）→ 一次推高 link_hit_rate
- **P0** 新增：`compute_knowledge.py` 集成到 `bootstrap.sh`，每轮末自动打快照
- **P1**：继续建 1 个战役 (白登之围) + 1 个政治人物 (萧何/曹参/陈平)
- **P1**：收敛 alias_conflicts（惠公/景公/桓/桓公/简/襄公/襄王），用 @NAME 消歧或删冗余 alias

---

## 7. 本轮动作清单

- ✅ `wiki/scripts/compute_knowledge.py` 新增
- ✅ `wiki/data/knowledge_latest.json` + `knowledge_timeline.jsonl` 首个快照
- ✅ 新增精品页 `巨鹿之战` (212 行, 3.5 KB, type=event, featured=true)
- ✅ `pages.json` rebuild (228 → 229)
- ✅ record_revision (rev 20260423-010542)
- ✅ 反思 v8 (本文件)

K 增长记录 → `wiki/data/knowledge_timeline.jsonl`
