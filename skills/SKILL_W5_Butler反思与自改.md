---
name: skill-butler-5
description: Butler 的反思与自改机制 — 进化引擎。周期性扫 actions/failures 日志, 识别 pattern, 提案对 W1-W4 的修订。本 skill 修订其他 skill, 不修订自己 (改 W5 必须人工)。修订必须写 reflections/<date>.md + skill_changes.md, 保持保守 (每次反思 ≤ 3 条修订, 优先改阈值不重写结构)。
---

# SKILL W5: 反思与自改

> Butler 的真正 "进化" 发生在这里。其他 skill 是胳膊腿, W5 是大脑皮层。

---

## 一、触发条件

反思不是 happen-every-invocation, 由以下之一触发:

| 触发 | 条件 | 动作 |
|---|---|---|
| **周期** | 累计 atomic action 达 20 次 | 自动进入反思 |
| **连续失败** | `failures.jsonl` 最近 3 条同 action type | 立即进入 |
| **手动** | 用户 `/reflect butler` 或命令行调用 | 立即进入 |
| **红旗聚集** | 单个 target 页一周内被标同一红旗 ≥ 3 次 | 进入 (针对该页) |

触发时**本轮不做 atomic action**, 整轮用于反思。

---

## 二、反思流程 (5 步)

### 步骤 1 · 收集素材

```
最近 20 条 actions.jsonl  (含 accept + fail)
最近 所有 failures.jsonl
过去 7 天 reflections/ 输出 (避免循环提议)
当前 W1–W4 的版本
```

### 步骤 2 · 模式识别

寻找 **4 类**模式:

**A. 失败聚集**
- 同 action type 连续失败 → 前置条件太松? 应禁用?
- 同 target 类型 (如所有 topic 页) 失败 → rubric 对此类型不适用?
- 同红旗反复触发 → 红旗定义过严?

**B. 成功未被规则化**
- 某特定打分组合反复成功且 score_after 高 → 该模式应变成 W2 动作 / W3 加分项
- 某种探索路径 (顺藤 → 多链 resolved) 重复奏效 → W1 可上调此策略比例

**C. 阈值失调**
- W3 量化阈值 (如 broken_ratio 0.2) 触发红旗过频 → 可能偏严
- W1 的 2:1 配比已让队列积压 → 调 explore 比例

**D. 规模失调** ← *每次反思都必须检查此类*
- 运行 `python3 wiki/scripts/butler/check_scale.py` 获取当前指标快照
- 对照下方架构阈值表，识别是否越过警戒线或临界线
- 如有越线 → 进入「架构提案」流程（§二.D 专节），**不计入** ≤3 条修订限额

#### 架构阈值表

| 指标 | 采集命令 | 警戒线 🟡 | 临界线 🔴 | 推荐应对 |
|------|---------|----------|----------|---------|
| `pages.json` 大小 | `wc -c wiki/public/pages.json` | 500 KB | 1 MB | 拆分为 `pages_index.json`（摘要）+ 按类型子文件；延迟加载详情 |
| wiki 页面总数 | `ls wiki/public/pages/*.md \| wc -l` | 800 | 1500 | "全部人物"/"全部事件"等列表页改分页/按首字筛选 |
| person 页数量 | 从 pages.json 统计 | 600 | 1000 | 人名索引页改 A-Z 分页，禁止单页渲染全量列表 |
| `history/` 文件数 | `ls wiki/public/history/ \| wc -l` | 1000 | 2000 | 考虑将历史合并为 SQLite 或年度归档 JSON |
| `recent.json` 总修订数 | `.total_revisions` 字段 | 2000 | 5000 | recent.json 改为分页 API（page=1/2/...）|
| 单次 butler 扫描耗时 | actions.jsonl 中 `duration_s` 字段 | 30s | 90s | W1 食物源扫描改增量式（记 last_seen 游标）|

> **数量级心智模型**：
> - N < 500：纯静态 JSON + 客户端渲染，无问题
> - 500–1500：需要**分页**与**懒加载**，但仍可不用数据库
> - 1500–5000：需要**预建索引**（lunr.js / 静态搜索），或引入本地 SQLite
> - 5000+：需要**后端查询层**（FastAPI + SQLite / DuckDB），静态站点不再适合

### 步骤 3 · 提案

若步骤 2·D 有架构越线 → **先写** `arch_YYYY-MM-DD.md`，再写普通反思（两者独立）。

写 `logs/wiki_butler/reflections/YYYY-MM-DD.md`:

```markdown
# 反思 2026-04-22

## 素材
- actions 第 20–40 号 (20 条)
- failures 共 4 条

## 识别的模式

### 模式 1: topic 页连续 3 次 create-stub 后, 无人 embed-sku-excerpt
- 现象: action 22, 28, 34 都 create-stub, 但后续未链回实体页
- 假设: W1 候选入队时只入创建, 未入关联
- 提案: W1 §二 "入队规则" 加: 每次 create-stub 同时入队关联 action

### 模式 2: readability 维度常年满分
- 现象: 15 次评估中 14 次给 2 分
- 假设: 此维度阈值过松, 无区分度
- 提案: W3 v0.2 readability 量化阈值收紧

## 修订清单 (≤3 条)
1. W1 §二 新增 "入队-联动" 规则
2. W3 §二 readability 改 max_sentence_length 80 → 65
3. W3 §一 新增 "引证覆盖" 维度 (v0.2)
```

### 步骤 4 · 应用修订

逐条应用, 每条:
- 单独一个 commit, message: `butler/reflect-<date>: W<N> §<M> <摘要>`
- 同时在 `skill_changes.md` 追加:

```markdown
2026-04-22  W3 v0.1→v0.2  readability 阈值收紧 · 新增引证维度 [reflection/2026-04-22.md]
```

### 步骤 5 · 清理

- 把反思中"已确认无效的 pattern"记入反思底部 "已排除"节, 避免下次重复识别
- 若队列有基于旧规则的候选, 可保留 (新规则只对未来新增生效, 老账不追)

---

## 三、保守原则 (必须遵守)

- **每次反思 ≤ 3 条修订**。多了超过人脑 review 容量。（架构提案不计入此限额，见 §三.D）
- **优先改阈值 / 规则条目, 次之改流程, 最后改结构**。重写 skill 结构必须先有 5 次反思铺垫。
- **不改 W0 的"六不变量"章节**。那是契约, 只能人工 review。
- **不改 W5 自己**。"自改自"容易死循环。W5 升级需用户 review。

---

## 三.D 架构提案专项流程

> **触发条件**：步骤 2·D 中任一指标越过警戒线 🟡 或临界线 🔴。

架构变更不同于 skill 参数调整——它影响文件结构、前端渲染机制、数据存储方式，**必须经用户明确批准**，Butler 不得自动应用。

### 架构提案输出格式

写 `logs/wiki_butler/reflections/arch_YYYY-MM-DD.md`（与普通反思分开存放）:

```markdown
# 架构提案 2026-MM-DD

## 触发指标
- pages.json: 1.2 MB（超过临界线 1 MB）
- person 页数: 720（超过警戒线 600）

## 当前问题描述
"全部人物"页在客户端需加载完整 pages.json（1.2MB），
首屏渲染约 4 秒，随人物页增加线性变差。

## 推荐方案

### 方案 A（最小改动）：拆分索引 + 分页
- 新增 `pages_persons_index.json`（仅含 id/label/tags，约 80KB）
- "全部人物"改为按首字筛选（A-Z / 按姓氏）
- 主 pages.json 保留，仅用于详情页加载
- 工作量：≈ 2h，无需改渲染引擎

### 方案 B（中等改动）：引入 lunr.js 预建搜索索引
- 构建时生成 `search_index.json`（lunr 格式）
- 搜索框直接查询索引，不依赖 pages.json 全量
- 工作量：≈ 4h

### 方案 C（较大改动）：本地 SQLite
- 将 pages.json + history/ + recent.json 迁移到 SQLite
- 需要轻量后端（FastAPI / 静态预查询脚本）
- 工作量：≈ 2 天，适合 N > 3000 时考虑

## 建议时间窗口
方案 A 建议在 person 页超过 800 时执行，
方案 B 建议在总页面超过 1500 时同步引入。

## 等待用户批准
Butler 不会自动执行以上任何方案。
请用户回复"批准方案 A/B/C"或"暂不处理"后，Butler 再行动。
```

### 架构提案的后续跟踪

- 提案写入后，Butler 在 `queue.md` 顶部加一条 **P0 [ARCH]** 条目，标注提案文件路径
- 每次反思仍检查该 P0 是否已批准：若已批准则升级为普通 P0 行动，按步骤正常执行
- 若用户回复"暂不处理"，Butler 将临界线调高 20%（记入 `logs/wiki_butler/arch_snooze.json`），避免反复提醒

---

## 四、回滚提案

反思也会错。若某次 skill 修订 (如 W3 v0.2) 应用后, 接下来 20 次 invocation 数据更差了 (fail 率上升 / 分数平均下降), 下次反思应**提案回滚该版本**:

```markdown
## 模式: W3 v0.2 收紧后 fail 率上升 40%
## 提案: W3 回退到 v0.1, 但保留 "引证覆盖" 维度
```

保留可取部分, 回退有害部分。

---

## 五、用户介入口

用户可随时直接写 `reflections/<date>-user.md` 表达意见:

```markdown
# 用户反思 2026-04-22

Butler 近期页面都太短。我认为 W3 字数下限应提到 300。

建议: W3 §二 word_count_range [200, 2000] → [300, 2000].
```

W5 下次 (或立即) 触发, 优先评估用户提案。

---

## 六、反思报告的长度

一次反思 (`reflections/YYYY-MM-DD.md`) 建议 **50–200 行**:
- 太短 = 敷衍 (一个 action type 可能值不了一次反思, 推迟)
- 太长 = 想改太多 (拆成多次反思, 一次 3 条)

---

## 七、示例 · 第一次反思 (v0.2 提案预期)

20 次 action 后, 预期的典型反思:

```markdown
# 反思 2026-05-12 (第一次)

## 素材
actions #1–20, failures 5 条

## 模式
1. create-stub 12 次, 无一次加 infobox 生卒 → infobox 缺 lifespan 字段
2. 所有 topic 页 source_diversity = 1 (只 sku) → 跨源未建立
3. readability 评分均 2, 无区分度

## 修订
1. W2 `enrich-infobox` 前置加: "lifespan 缺 + kg 有数据" 时优先
2. W1 topic 页 create 后, 自动入队 "embed-sku-excerpt" 到 >=2 相关实体页
3. W3 readability 量化阈值收紧 (单句 80→65)
```

---

## 相关
- [W0 总则](SKILL_W0_Butler总则.md)
- [W3 质量标准](SKILL_W3_Butler质量标准.md) — 主要的修订目标
- `logs/wiki_butler/reflections/` — 反思输出沉淀（普通：`YYYY-MM-DD.md`，架构：`arch_YYYY-MM-DD.md`）
- `logs/wiki_butler/skill_changes.md` — 修订 changelog
- `logs/wiki_butler/arch_snooze.json` — 用户暂缓的架构阈值覆盖
- `wiki/scripts/butler/check_scale.py` — 规模指标快照工具（每次反思必跑）

---

## KB 写入规则

反思结束后，将定论写入 `logs/wiki_butler/kb/w5_ops.md`：

- **写什么**：在 ≥2 次反思中重复出现、被 W5 修订采纳的操作规则
- **不写什么**：单次失败、偶发异常、未经 ≥2 次验证的猜测
- **格式**：`- [R<N> 确认] <条件> → <结论>` 追加到对应分组（行动成功模式 / 行动失败模式 / 已废弃路径）
- **更新旧规则**：改写原行，加 `[R<N> 更新，原见 R<M>]` 标注
