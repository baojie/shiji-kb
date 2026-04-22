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

寻找 3 类模式:

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

### 步骤 3 · 提案

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

- **每次反思 ≤ 3 条修订**。多了超过人脑 review 容量。
- **优先改阈值 / 规则条目, 次之改流程, 最后改结构**。重写 skill 结构必须先有 5 次反思铺垫。
- **不改 W0 的"六不变量"章节**。那是契约, 只能人工 review。
- **不改 W5 自己**。"自改自"容易死循环。W5 升级需用户 review。

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
- `logs/wiki_butler/reflections/` — 反思输出沉淀
- `logs/wiki_butler/skill_changes.md` — 修订 changelog
