# Butler 记忆系统设计

> 设计目标：极简 + 可进化。记忆本身是第一类公民，可被反思、修正、淘汰。

---

## 一、参考系与出发点

现有类似设计的核心思路：

- **Herms**（Hierarchical Episodic & Reflective Memory）：把记忆分层——工作记忆（短期）、情节记忆（发生了什么）、语义记忆（知道什么）。反思将情节提炼为语义。
- **OpenClaw**：每条记忆有置信度和来源，定期 decay，反思时 promote 或 prune。
- **MemGPT / Letta**：记忆分"核心记忆"（始终在上下文）和"存档记忆"（按需检索）；两者边界动态调整。

这些系统共同的最小内核：

```
记忆 = 内容 + 置信度 + 来源 + 时间戳
反思 = 读情节 → 抽模式 → 更新语义 → 清理过时
```

---

## 二、Butler 的记忆分类

Butler 实际上已有四类记忆，但散落在不同地方、缺乏统一治理：

| 类型 | 含义 | 当前载体 | 问题 |
|---|---|---|---|
| **工作记忆** | 本次 invocation 在做什么 | 上下文 + queue.md | 无状态，每次重建 |
| **情节记忆** | 做了什么、结果怎样 | actions.jsonl / failures.jsonl | 只增不减，无提炼 |
| **语义/程序记忆** | 如何做事的规则 | SKILL_W*.md | 更新靠人工，非系统化 |
| **自反记忆** | 我犯了什么错、学了什么 | reflections/ | 写了但不被读回来 |

**核心问题**：情节记忆从不提炼到语义记忆，语义记忆（Skill）从不被情节触发更新。记忆是单向流入，不循环。

---

## 三、极简设计

### 3.1 记忆文件结构

```
wiki/memory/
├── MEMORY.md          # 索引文件（单条 ≤ 150 字符，只有指针）
├── rules/             # 语义/程序记忆：从经验提炼的行为规则
│   └── rule_NNN.md    # 一条规则一个文件
└── reflections/       # 自反记忆：每次反思的输出摘要
    └── YYYY-MM-DD.md
```

情节记忆继续用现有的 `actions.jsonl` / `failures.jsonl`，不新建文件。

### 3.2 单条记忆的格式

```markdown
---
id: rule_042
confidence: high      # high / medium / low
source: failures.jsonl R934-R936（三次相同错误）
created: 2026-04-20
last_updated: 2026-04-24
---

修改 pn 字段时不得联动修改 event_ids，两者是完全独立的体系。

**Evidence:** 2026-04-24 将 (097-3.1)→(097-6) 时错误地同步改了 event_ids
**Scope:** 所有 wiki 页面编辑操作
```

关键字段只有三个：**置信度、来源证据、适用范围**。

### 3.3 MEMORY.md 索引

```markdown
# Butler Memory Index

- [rule_042](rules/rule_042.md) high · pn 与 event_ids 字段互相独立，不联动修改
- [rule_041](rules/rule_041.md) high · :::meta 块 pn 值全局替换括号为全角
- [rule_015](rules/rule_015.md) medium · 合并页面时 story_id 冲突用 merged_story_ids
```

索引是唯一要"始终被读"的文件，控制在 50 条以内。

---

## 四、记忆生命周期

```
情节记忆（actions/failures）
    ↓  [反思触发：每 20 轮 or 3 次同类失败]
模式识别
    ↓
新建/更新 rule_NNN.md（置信度 medium）
    ↓  [下 10 轮无反例]
升为 high
    ↓  [发现反例]
降为 low → 触发人工复核 or 删除
```

**三个状态**：
- `high`：已验证，直接写入 SKILL 对应禁止/规范条目
- `medium`：初步归纳，Butler 遵守但标注待验证
- `low`：有疑问，下次反思时重点审查，60 轮无强化则删除

---

## 五、反思机制（最小可行）

每 20 轮触发一次，Butler 自己执行以下步骤：

1. **读最近 20 条情节**：`tail -20 actions.jsonl` + `failures.jsonl` 里新增的
2. **找 pattern**：相同 action_type 连续失败 ≥ 2 次 → 候选新规则
3. **对比现有 rules/**：是否已有覆盖？有则更新 last_updated；无则新建
4. **更新置信度**：high rule 有反例 → 降 medium；medium 无反例 10 轮 → 升 high
5. **清理 low**：`low` 超过 60 轮未强化 → 删除，写 reflections/ 存档
6. **Promote to Skill**：`high` 且适用范围广 → 写入对应 SKILL 文件的禁止清单

整个流程写一个 `reflect.py` 脚本驱动，输出 diff 供人工确认后执行。

---

## 六、与现有系统的关系

```
SKILL_W*.md  ←─── promote ───── memory/rules/   ←─── extract ──── actions.jsonl
（长期程序记忆）                 （中间态规则）                     （原始情节）
      ↑                               ↑
   人工 review                    自动反思
```

- **SKILL 文件**：只收录 `high` 规则，是经过验证的"定论"
- **memory/rules/**：是 SKILL 的"草稿池"，高置信度才毕业
- **情节记忆**：是 rules 的"原材料"，不直接被操作参考

---

## 七、极简实现路径

### Phase 1（立即可做，手动）
- 建 `wiki/memory/` 目录和 `MEMORY.md`
- 把已知的几条高置信规则（如 pn/event_ids 独立、全角括号等）迁移为 rule_NNN.md
- Butler invocation 开始时读 `MEMORY.md`（加入 W0 初始化流程）

### Phase 2（下一步，半自动）
- 写 `scripts/butler/reflect.py`：扫 failures.jsonl → 输出候选规则草稿
- Butler 每 20 轮自动调用，输出 diff 待确认

### Phase 3（未来，全自动）
- 置信度升降、规则 promote 到 Skill、过期规则清理全部脚本化
- 加入 `memory_health.json`：追踪规则数量、平均置信度、未强化天数

---

## 八、设计原则总结

1. **一个索引文件统领**：`MEMORY.md` 是唯一入口，控制行数上限
2. **每条记忆独立文件**：便于增删、版本追踪、置信度更新
3. **三级置信度**：high/medium/low，驱动 promote 和 prune
4. **情节→规则→Skill 的单向提炼管道**：记忆不直接被"用"，先经过反思提炼
5. **反思是第一类操作**：不是事后补充，是 Butler 闭环的必要步骤

---

*草稿，2026-04-24*
*参考：Herms, OpenClaw, MemGPT/Letta 记忆架构；Claude Code auto-memory 设计*
