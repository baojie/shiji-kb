---
name: skill-butler-1
description: Butler agent 的探索与食物收集。定义 6 大食物源 (kg / ontology-v2 / doc / data / docs / logs) 的扫描策略、候选识别信号、消化方式。维护 queue.md 候选队列 (P0/P1/P2)。每轮 invocation 按 2:1 配比在"顺藤摸瓜"与"无约束探索"间选择。本 skill 决定每次 invocation 做什么, 不规定怎么做 (W2 负责)。
---

# SKILL W1: 探索与食物收集

> Butler 是消化系统, 本 skill 规定"去哪找、找什么、怎么排优先"。

---

## 一、食物地图 (6 源)

### 源 A · kg 结构化数据
**路径**：`kg/entities/data/`、`kg/events/data/`、`kg/relations/data/`
**营养**：infobox 字段 / 事件时间线 / 人物关系网
**探查信号**：
- `kg/entities/data/entity_aliases.json` 里 canonical 在 wiki 无页 → 建 stub
- `kg/entity_index.json` top-N 人物无 wiki 页 → **P0**
- 事件索引里某事件 id 在 wiki 是 broken link → 建事件页
**消化**：`enrich-infobox` / `add-event-timeline` / `link-from-relations` (见 W2)

### 源 B · 精炼 SKU
**路径**：`kg/ontology/ontology-v2/**/skus/*.md`
**营养**：直接作 topic 页 / 作"深度阅读"区
**探查信号**：
- SKU 无对应 `wiki/public/pages/<slug>.md` → 建 topic 页 (**P0**)
- SKU frontmatter 提及某实体, 该实体 wiki 页未引用此 SKU → 补"相关主题"链
**消化**：`import-sku-as-topic` / `embed-sku-excerpt`

### 源 C · 项目分析报告
**路径**：`doc/**/*.md`
**营养**：引证脚注, 如 `doc/lifespan_inference/<人名>.md` 证明某人物生卒
**探查信号**：
- wiki 页声称生卒但无引证 + doc 存在 → 加脚注
- `doc/events/*总结.md` 提及某人物 → 该页可加"相关反思"链
**消化**：`cite-doc-report` / `link-investigation`
**限制**：**不搬内容只做链接**, 摘要 ≤ 50 字

### 源 D · 原始数据
**路径**：`data/`
**营养**：后台校验用, **不面向读者**
**探查信号**：写完 wiki 字段时抽查式交叉验证
**消化**：`verify-from-data` (内部校验, 不出现在 UI)

### 源 E · 已发布文档
**路径**：`docs/entities/*.html`、`docs/chapters/*.html`
**营养**：wiki 页底"外部链接"出口
**探查信号**：新建人物/章节页时, 对应 docs 文件已存在
**消化**：`link-external-docs`
**限制**：只从 wiki 指向 docs, 不重建 docs 功能

### 源 F · 每日日志
**路径**：`logs/daily/*.md`
**营养**：最近活跃页 / 时间线入口 (可选, v2)
**探查信号**：日志高频提及某实体 → "本周热点"
**消化**：`link-daily-log` (低优先)

---

## 二、三队列体系

Butler 每轮读取三个独立队列，共同决定本轮任务：

| 队列文件 | 维护者 | 任务类型 | 优先级标记 |
|---|---|---|---|
| `queue.md` | W1（本 skill） | 内容创建/丰富 | P0/P1/P2 |
| `housekeeping_queue.md` | W10 | 内务整理 H1-H19 | P0/P1/P2 |
| `insight_queue.md` | W14 | 洞察问题 I 类 | 待调查/已处理 |

**每轮选取顺序**（完整算法见 W0 §六"三队列选取算法"）：
- **普通轮**（`round % 11 ≠ 0`）：只看 queue.md 和 housekeeping_queue.md，跳过 insight_queue
- **洞察轮**（`round % 11 == 0`）：在 P0 之后、P1 之前插入 insight_queue 最老待调查条目
- P0 永远最优先，不受洞察轮/普通轮区分影响
- 全部为空 → W1 explore / W10 扫描（洞察轮还可触发 W14 生成），本轮不空转

### 2.1 queue.md 结构（内容任务）

```markdown
# Butler 候选队列

## P0 高优
- [ ] 萧何: 建 stub (kg refs=75/30 篇, top 20) [源:A] [2026-04-22]
- [ ] 孔子页加 `论语` book 关联 [源:A]

## P1 中优
- [ ] 建 topic 页 "神话与历史的界限" [源:B] [fact_005]
- [ ] 刘邦页补生卒脚注 [源:C] [doc/lifespan_inference/刘邦.md]

## P2 低优
- [ ] 全局扫"相关邦国"都空的人物页 [源:A]
```

### 2.2 入队规则

- 每轮 invocation 可 **discover 1–3 条新候选** 加入 queue.md
- 但**本轮只执行 1 条**，队列永远在增长
- P0 = 已知入口缺失 / broken link 明显 / 主页代表人物缺内容
- P1 = 有现成食物未利用
- P2 = 全局扫描发现的不一致

### 2.3 去重

同名候选（同 target 页 + 同动作）只入一次。如重复出现，W5 反思需要看是不是前置条件常年不满足。

---

## 三、动态配比 (v0.2, 2026-04-22 W5 修订)

配比随 P1 队列规模变化:

| P1 队列 | trail:explore | 理由 |
| ---: | ---: | --- |
| > 10 | 3:1 | 队列积压, 优先消费, 少探索 |
| 5 — 10 | 2:1 | 默认平衡 (原版) |
| < 5 | 1:1 | 队列接近清空, 加大探索拉新 |
| = 0 | 0:1 (纯 explore) | 无积压, 仅探索 |

**trail** = 从 wiki 已有页出发, 扫 broken link / 缺项 / 消费队列
**explore** = 独立扫某食物源, 找从未入 wiki 的候选

### 本轮选哪个?

1. 计算当前 P1 队列规模 `n = 统计 queue.md 中 \[P1\] 数`
2. 按上表查目标比例
3. 看 `actions.jsonl` 最后 (k+1) 条的 `mode` 字段, 维持比例
   - 例: 3:1 规则 → 最后 3 条都是 trail → 本次 `explore`; 否则 `trail`

**原始 2:1 规则 (v0.1, 历史留档)**: 每 3 次 invocation = 2 trail + 1 explore. 在队列大 (>10) 或小 (<5) 时不平衡.

### 3.4 广度 vs 深度 (v0.4, 2026-04-22 user-req-4)

若 wiki 的 quality_score **中位数 < 10** (绝大多数是 stub), butler 优先做**深度动作** (enrich-infobox / cite-doc-report / embed-sku-excerpt), 推迟 create-stub.

判断标准:
- 读 pages.json 统计 median quality
- median < 10 → **深度优先**: 60% 时间做 enrich 类, 40% create-stub
- median 10-15 → 平衡: 各半
- median > 15 → 广度优先 (现状 3:1 or 原规则)

原因: 用户反馈"基本都是空骨架", 需要持续选页加信息而非一味新建.

### 3.3 源耗尽降权 (v0.3, 2026-04-22 W5 v2 加)

若近 N (=5) 次 explore 对某食物源, 输出候选 < 1 条, 该源权重 *= 0.5 保持下去, 直到产出恢复。
避免强制比例压 butler 对已经饱和的源做无效探索 (如 SKU 只有 2 个, 都建了 topic 页后应停止轮询)。

`source_access.json` 增一个字段:
```json
"B_sku": {"last": "...", "empty_streak": 3, "weight": 0.25}
```

选源时 `weight` 做 softmax 归一化。新源 / 有产出源自然胜出。

---

## 四、食物源轮换

`explore` 模式时, 按 `source_access.json` 选**最久未访问**的源：

```json
{
  "A_kg": "2026-04-22T10:00",
  "B_sku": "2026-04-20T11:00",
  "C_doc": null,
  "D_data": null,
  "E_docs": "2026-04-21T09:00",
  "F_logs": null
}
```

`null` 或最老的优先。

---

## 五、发现脚本 (discover_*)

每种源对应一段扫描脚本, butler 调用, 输出候选条目。

**规划位置**：`wiki/scripts/butler/discover_<source>.py`
- `discover_kg.py`：扫 top-N 未入 wiki 的人物
- `discover_sku.py`：扫 ontology-v2 SKU 无对应 topic
- `discover_doc.py`：扫 doc/ 与 wiki 页的不一致
- `discover_docs.py`：wiki 页 + docs/ 交叉
- `discover_logs.py`：日志高频实体

**v0 策略**：只写 `discover_kg.py` 和 `discover_sku.py`, 其他按需求逐步补。W5 反思说需要时再写。

---

## 六、何时停止探索

单次 invocation 探索时长 ≤ 2 分钟 / 扫文件 ≤ 50 个。超过则把本轮当"纯探索", **发现的全入队**, 本轮不行动 (mode=`observe`)。

---

## 七、交给 W2

本 skill 的输出 = 一个具体候选条目，格式：

```json
{
  "target": "wiki/public/pages/萧何.md",
  "action": "create-stub",
  "source": "kg/entity_aliases.json",
  "queue": "queue.md",
  "mode": "explore",
  "rationale": "萧何在 kg top-20 (refs=75), 无 wiki 页"
}
```

`queue` 字段标明来源队列（`queue.md` / `housekeeping_queue.md` / `insight_queue.md`），便于 actions.jsonl 追溯。W2 按此执行。

**若任务来自 housekeeping_queue**：W2 执行前额外检查 W10 对应 H 类型的前置条件（W10 §各类型详规范）。

**若任务来自 insight_queue**：W2 执行前先确认洞察置信度（high/medium），low 置信度跳过不执行，改记 dismissed。

---

## 八、expand-content 候选筛选条件（v0.2，2026-04-27 W5 R6823）

从 pages.json 生成 expand-content 候选时，必须同时满足：

1. `quality` ∈ {basic, standard}
2. `refs` ≥ **5**（v0.1 是 refs>0，已提升阈值聚焦高价值页面）
3. `type` ∈ {person, concept, event, overview, story, state}
4. **无生平节**：页面内容不含 `## 生平` / `## 在位` / `## 背景` 等正文节
   （已有正文节的页面 skip 率高达 32%，纳入候选属于无效占位）

筛选脚本示意（W5 §二.E 候选生成时应用）：
```python
expand_pool = sorted(
    [p for p in scored if p['quality'] in ('basic', 'standard')
     and p['refs'] >= 5 and p['type'] in EXPAND_TYPES
     and not p.get('has_bio', False)],
    key=lambda x: -x['refs'])
```

`has_bio` 判断：读页面内容，检测 `## 生平|在位|背景` 是否存在。

---

## 相关
- [W0 总则](SKILL_W0_Butler总则.md)
- [W2 原子行动目录](SKILL_W2_Butler原子行动目录.md)
