---
name: skill-butler-2
description: Butler 的原子行动目录 — 18 种标准操作的前置条件、执行步骤、后置检查、预期 diff 大小。每次 invocation 只执行 1 个原子操作, diff ≤ 20 行。accept 后只 git add 暂存，每5轮由 /wiki 批量 commit。禁止自由发挥, 只能从此目录挑。新操作由 W5 反思流程追加。
---

# SKILL W2: 原子行动目录

> 每轮 invocation 做**一次**小改动。本 skill 是"菜单", 选一道做一道。

---

## 一、通用约定

- diff ≤ 20 行 (含空行), 超则拆
- W4 **accept** → `git add <file>` 暂存，**不立即 commit**
- W4 **fail** → `git restore <file>` 回滚工作区，un-stage 若已暂存
- **批量 commit**：每5轮由 `/wiki` skill 统一 commit + push（`round_counter.txt` mod 5 == 0）
- 例外：`update-wanted-pages`、`rebuild-registry` 等 observe 类动作仍需**立即 commit**（见各动作备注）
- 行动前必须写 `actions.jsonl` 一行，commit 字段留空，批量 commit 后无需回填

**actions.jsonl 每行格式**：
```json
{"ts":"2026-04-22T14:00","mode":"trail","action":"add-link",
 "target":"wiki/public/pages/刘邦.md","source":"kg/entities/data/..",
 "rationale":"...","result":"accept|fail|rollback","commit":""}
```

---

## 二、18 个原子动作 (按食物源分组)

### A 组 · kg 结构化数据

| 动作 | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|
| `enrich-infobox` | 目标页存在 + kg 有新字段不在 infobox | 在 frontmatter 加 1 字段 | YAML 合法, 页面仍能渲染 | 1–2 行 |
| `add-event-timeline` | 人物页无"生平大事"区 + kg 有事件 | 插入"生平大事" 表 (5–10 项) | 表格 markdown 合法, event id 来源可追溯 | 10–15 行 |
| `link-from-relations` | 人物 A 页已存在 + kg 有 A-B 关系 + B 页存在/建 stub | A 页"相关人物"加一条 `[[B]]` 及关系 | B 页也互链 (可留队列) | 1–3 行 |
| `create-stub` | kg canonical 无 wiki 页 + 有 lifespan / refs | 跑 `generate_entity_page.py <name>` | 页面 md 生成, pages.json 可扫到 | 新文件 50 行内 |
| `merge-alias` | 两个 canonical 明显同人 (如 汉高祖/刘邦) | 在 `seed.js` CANONICAL_MERGE 加一行 | 重跑 seed, 新 semantic.json 只出现一个 | 1 行 |

### B 组 · SKU

| 动作 | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|
| `import-sku-as-topic` | SKU 存在 + 无对应 topic 页 | 建 `pages/topic/<slug>.md`, frontmatter `type: topic` + `source: ontology-v2/fact_XXX`, body 引用 SKU | 页面可渲染, 保留 source 反溯链 | 新文件 20 行内 (主要是 frontmatter + 引用说明) |
| `embed-sku-excerpt` | 实体页已存在 + 相关 SKU 存在 | 页末加"深度阅读"区, 链 SKU + ≤ 150 字摘要 | 摘要不超字数, 链接指向 topic 页 | 5–8 行 |

### C 组 · doc 分析报告

| 动作 | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|
| `cite-doc-report` | 页面某断言 + doc/ 对应报告存在 | 断言后加 `[^ref]` 脚注, 脚注指 doc/ 文件 | 脚注编号不冲突, 文件可 open | 2–4 行 |
| `link-investigation` | 页面"外部资源"区存在 / 可建 | 加链接到 `doc/lifespan_inference/<name>.md` 等 | 链接可到达 | 1–2 行 |

### D 组 · 数据校验 (后台)

| 动作 | 前置 | 做什么 | 后置检查 | diff |
|---|---|---|---|---|
| `verify-from-data` | 页面某字段 + data/ 可交叉验证 | 抽查 n=10 条, 记 `actions.jsonl`, 不改 UI | 一致 → 无动作; 不一致 → 建 P0 队列条目 | 0 行 (仅 log) |
| `verify-citations` | `verify_state.json` 有未检查页面，或 queue 为空 | 跑 `python3 scripts/verify_quotes_agent.py`，处理一个页面（L0缓存→L1规则→L2 LLM） | issues 写入 `citation_issues.jsonl`，缓存更新 | 0行（detect）或 fix 行数 |

### E 组 · 外部链接

| 动作 | 前置 | 做什么 | 后置检查 | diff |
|---|---|---|---|---|
| `link-external-docs` | wiki 人物/章节页 + 对应 docs/ 文件存在 | 页底"外部资源"加 1 链接 | HTTP 可访问 (本地发包测) | 1–2 行 |

### F 组 · 日志 (可选)

| 动作 | 前置 | 做什么 | 后置检查 | diff |
|---|---|---|---|---|
| `link-daily-log` | 日志文件提及该实体 ≥ 3 次 | 页面加"最近关注"一行 + 日志链 | 不抢主信息位 | 1–2 行 |

### 维护类

| 动作 | 前置 | 做什么 | 后置检查 | diff |
|---|---|---|---|---|
| `fix-broken-link` | 页面中 broken wikilink + target 已有 alias 可对上 | 改 wikilink 到正确 id | 构建后无断链 | 1 行 |
| `add-tag` | 页面 tags 为空 + 合理 tag 候选存在 | frontmatter `tags:` 加 1–3 项 | pages.json 更新 | 1 行 |
| `rebuild-registry` | 前述动作涉及 frontmatter 变动 | 跑 `build_registry.py` 再跑 `build_backlinks.py` | pages.json 注入 semantic 成功；backlinks.json 同步更新 | 2 文件 (pages.json + backlinks.json) |
| `rollback` | 前一动作评估为 fail | `git revert HEAD` | 工作区干净, failures.jsonl 追加 | 自动 |
| `observe-only` | 本轮探索到候选但达探索上限 | 仅更新 queue.md, 不改 wiki | queue.md 新增条目 | queue 1–3 行 |

---

## 三、每类的边界

**永远禁止的**：
- ❌ 改 frontmatter 的 `id` 或 `type` (两者决定路由, 改动传染多页)
- ❌ 删既有 section (只能加, 除非明确 rollback)
- ❌ 改 SKU 原文
- ❌ 改 kg/ 任何内容
- ❌ 一次动作同时写多个文件 (除了 `rebuild-registry` 的 `pages.json` + `backlinks.json`)

---

## 四、选哪个动作

由 W1 的候选决定。候选里的 `action` 字段就是本目录的 key。

若候选无 action (只指定 target), 按下列启发式：
- 目标页不存在 → `create-stub`
- 目标页存在 + infobox 稀疏 → `enrich-infobox`
- 目标页存在 + 无事件区 + kg 有事件 → `add-event-timeline`
- 目标页有多个 broken link → `fix-broken-link`

若不匹配 → 归入 `observe-only`, 加 queue。

---

## 五、执行步骤模板

```
1. 读 W1 给的候选 json
2. 对照本目录找 action 定义
3. 检查前置条件 (逐条 assert, 不满足 → failures.jsonl + 退出)
4. 在 actions.jsonl 追加一行 (result 先留空, commit 留空)
5. 做 diff
6. 检查 diff ≤ 20 行 (否则 rollback + 拆)
7. 跑 W4 评估
8. W4 accept → `git add <file>`（暂存，不 commit）; W4 fail → `git restore <file>` + actions 改为 rollback
9. 更新 actions.jsonl 的 result 字段
10. 若需 pages.json 更新, 触发 rebuild-registry（`git add wiki/public/pages.json`，同样不单独 commit）
11. 每5轮由 /wiki 批量 commit，commit message 汇总本批次所有 action
```

---

## 六、追加新动作

新动作不能凭直觉加。必须经 W5 反思流程：
- 至少 3 次同类手动操作出现 → 提案
- 提案写 `reflections/<date>.md`
- 经 1 次用户确认 (人工 review) 追加到本目录
- 编号：在本目录表格最后追加, skill_changes.md 记一笔

---

## 相关
- [W0 总则](SKILL_W0_Butler总则.md)
- [W1 探索与食物](SKILL_W1_Butler探索与食物收集.md)
- [W3 质量标准](SKILL_W3_Butler质量标准.md) — 前置检查的一部分
- [W4 评估与检验](SKILL_W4_Butler评估与检验.md) — 后置评估
