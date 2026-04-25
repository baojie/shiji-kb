---
name: skill-butler-2
description: Butler 的原子行动目录 — 22 种标准操作的前置条件、执行步骤、后置检查、预期 diff 大小与工作量单位(WU)。每次 invocation 按WU批量执行同类动作直到累计100WU，单个动作 diff ≤ 20 行。禁止自由发挥, 只能从此目录挑。新操作由 W5 反思流程追加。
---

# SKILL W2: 原子行动目录

> 每轮按"工作量单位(WU)"批量执行同类动作，目标 100 WU/轮。本 skill 是菜单——选一类，批量做。

---

## 一、通用约定

- **单次 diff ≤ 20 行**（含空行），超则拆
- 每轮按 **WU** 批量执行同类动作，目标 100 WU/轮（见 PROMPT.md WU 表）
- W4 **accept** → 不做 git add（staging 统一由 /wiki commit 轮执行）
- W4 **fail** → `git restore <file>` 回滚工作区
- **批量 commit**：每17轮由 `/wiki` skill 统一 commit + push（`round_counter.txt` mod 17 == 0）
- 例外：`update-wanted-pages`、`rebuild-registry` 等 observe 类动作仍需**立即 commit**
- 每个原子动作记 actions.jsonl 一行（批次内每个都记），commit 字段留空

**actions.jsonl 每行格式**：
```json
{"ts":"2026-04-25T14:00Z","mode":"trail","action":"expand-content",
 "target":"wiki/public/pages/刘邦.md","source":"kg/ontology/...",
 "rationale":"...","result":"accept|fail|rollback","commit":""}
```

---

## 二、原子动作目录（按使用频率分组）

### A 组 · 内容创建与扩充（最高频）

| 动作 | WU | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|---|
| `source-with-pn` | 1 | 页面无 `sources`/`event_ids` 字段 + canonical_name ≥ 3 字 | ① `find_unsourced.py --target <slug>` 确认匹配 ② `edit_page.py` 加 frontmatter `sources:` + `event_ids:` ③ 正文加 `(NNN-MMM)` 行内引注 | frontmatter 含两字段；引注 event_id 能在章节事件表找到 | 3–6 行 |
| `create-stub` | 5 | kg canonical 无 wiki 页 + 有 lifespan / refs | 跑 `generate_entity_page.py <name>` 生成，再用 `add_page.py` 写入（自动记修订） | 页面生成，pages.json 可扫到 | 新文件 ≤ 50 行 |
| `add-event-timeline` | 5 | 人物页无"生平大事"区 + kg 有事件 | 跑 `python3 wiki/scripts/butler/enrich_timeline.py <slug>` 插入"生平大事"区 | 表格 markdown 合法，event id 可追溯 | 10–15 行 |
| `expand-content` | 3 | 页面存在 + 正文内容稀薄（< 20 行实质内容）+ 有 kg/chapter 来源 | 用 `edit_page.py` 追加一个新节或补充一段正文（biography/evaluation/成语/相关事件之一） | 节不存在才追加；不覆盖既有节 | 8–20 行 |
| `premium-upgrade` | 10 | 目标在精品页建设队列（W8/H7）+ 页面 ≥ 20 行基础内容 | 读 `SKILL_W8_精品页建设方法论.md`，按最高价值来源（ontology v2 facts → 事件索引 → 章节原文）深化一个维度（引文/评价/成语/表格/跨章节互见） | 新增内容有 PN 溯源；多角度评价 ≥ 3 人（最终目标）；单次 diff ≤ 20 行 | 10–20 行 |
| `cite-doc-report` | 2 | 页面某断言 + `doc/` 对应报告存在 | 断言后加 `[^ref]` 脚注，指向 doc/ 文件 | 脚注编号不冲突，文件可打开 | 2–4 行 |

### B 组 · 引文质量修复（高频）

| 动作 | WU | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|---|
| `fix-citation` | 2 | `citation_issues.jsonl` 有未修复条目（类型 quote_mismatch 或 missing_pn） | **quote_mismatch**：对照章节原文修正引文文字；**missing_pn**：补充正确的 `(NNN-MMM)` 引注 | 修正后引文与原文一致；PN 编号在事件表可查 | 3–8 行 |
| `verify-citations` | 5 | `verify_state.json` 有未检查页面 | 跑 `python3 scripts/verify_quotes_agent.py`（L0缓存→L1规则→L2 LLM）检查一个页面 | issues 写入 `citation_issues.jsonl`；缓存更新 | 0行（detect）/ fix行数 |

### C 组 · frontmatter 元数据（快速批量）

| 动作 | WU | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|---|
| `add-tag` | 1 | 页面 tags 为空 / 不完整 + 合理 tag 候选存在 | **只修改 frontmatter 的 `tags:` 字段**，加 1–3 项；绝不在正文中插入 `tags:` 行 | tags 符合已有分类体系；pages.json 可更新 | 1 行 |
| `reclassify` | 1 | 页面 type 字段明显错误（W11 审计候选） | 改 frontmatter `type` 字段 | pages.json 更新；路由正确 | 1 行 |
| `enrich-infobox` | 3 | 目标页 infobox 稀疏 + kg 有新字段 | 在 frontmatter 加 1 字段（birth/death/role 等） | YAML 合法，页面可渲染 | 1–2 行 |

### D 组 · 链接与导航

| 动作 | WU | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|---|
| `fix-broken-link` | 1 | 页面有 broken wikilink + target 有 alias 可对上 | 改 wikilink 到正确 id | 构建后无断链 | 1 行 |
| `create-redirect` | 1 | 页面有 aliases 字段 + 别名无对应 REDIRECT 页 | 建 `pages/{别名}.md`，内容仅一行：`#REDIRECT [[规范名]]` | REDIRECT 页存在，跳转正确 | 新文件 1 行 |
| `link-from-relations` | 2 | 人物 A 页存在 + kg 有 A-B 关系 + B 页存在/stub | A 页"相关人物"加一条 `[[B]]` 及关系描述 | B 页可互链（可留队列）| 1–3 行 |
| `link-external-docs` | 2 | wiki 人物/章节页 + 对应 docs/ 文件存在 | 页底"外部资源"加 1 链接 | 链接目标存在 | 1–2 行 |

### E 组 · SKU 食物

| 动作 | WU | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|---|
| `import-sku-as-topic` | 5 | SKU 存在 + 无对应 topic 页 | 建 `pages/topic/<slug>.md`，frontmatter `type: topic` + `source: ontology-v2/fact_XXX`，body 引用 SKU | 页面可渲染，保留 source 反溯链 | 新文件 ≤ 20 行 |
| `embed-sku-excerpt` | 3 | 实体页已存在 + 相关 SKU 存在 | 页末加"深度阅读"区，链 SKU + ≤ 150 字摘要 | 不超字数，链接指向 topic 页 | 5–8 行 |
| `merge-alias` | 2 | 两个 canonical 明显同人（如汉高祖/刘邦） | 在 seed.js CANONICAL_MERGE 加一行 | 重跑 seed，新 semantic.json 只出现一个 | 1 行 |

### F 组 · 维护与系统

| 动作 | WU | 前置 | 做什么 | 后置检查 | diff |
|---|---|---|---|---|---|
| `delete-page` | 5 | 页面重复/错误/合并 + 有用户或 W11 授权 | ① `record_revision.py <slug> --action delete` ② `git rm wiki/public/pages/<slug>.md` ③ history JSON 保留 | history JSON 含 `deleted:true`；pages.json 重建后无此页 | 删文件 |
| `rebuild-registry` | — | 前述动作涉及 frontmatter 变动 | 跑 `build_registry.py` + `build_backlinks.py` | pages.json 注入 semantic 成功 | 2 文件 |
| `rollback` | — | 前一动作评估为 fail | `git restore <file>` + failures.jsonl | 工作区干净 | 自动 |
| `observe-only` | 1 | 本轮探索到候选但已达批次上限 | 仅更新 queue.md | queue.md 新增条目 | 1–3 行 |

---

## 三、禁止事项

- ❌ 改 frontmatter 的 `id` 或 `type`（`reclassify` 例外，且必须有 W11 授权）
- ❌ **替换/覆盖既有节**：节不存在才追加；节已存在必须跳过
- ❌ 改 SKU 原文 / 改 kg/ 任何内容
- ❌ 单次 diff > 20 行（拆，不是跳过）
- ❌ 一次动作同时写多个 wiki 页面（`rebuild-registry` 的 pages.json + backlinks.json 除外）
- ❌ **直接 Edit/Write wiki/public/pages/*.md**，必须通过脚本：
  - 新建 → `python3 wiki/scripts/butler/add_page.py <slug> <content_file> --author butler`
  - 编辑 → `python3 wiki/scripts/butler/edit_page.py <slug> <content_file> --author butler`
  - 删除 → `python3 wiki/scripts/butler/delete_page.py <slug> --author butler`

---

## 四、选哪个动作（决策树）

由 W1 的候选决定。若候选有 `action` 字段，直接用。

若候选无 action，按优先顺序：

1. 页面不存在 → `create-stub`
2. `citation_issues.jsonl` 有该页未修复条目 → `fix-citation`
3. 页面存在 + 无 `sources` 字段 → `source-with-pn`
4. 页面存在 + 无"生平大事"区 + 是人物页 → `add-event-timeline`
5. 页面在精品页建设队列 → `premium-upgrade`
6. 页面正文 < 20 行实质内容 → `expand-content`
7. frontmatter infobox 稀疏 → `enrich-infobox`
8. 页面有 aliases 但缺 REDIRECT → `create-redirect`
9. 页面有 broken link → `fix-broken-link`
10. 其他 → `observe-only`，加 queue

---

## 五、执行步骤模板（批量模式）

```
0. 查 WU 表，确定本轮 action 类型；batch_n = ceil(100 / WU)
1. total_wu = 0, accept_cnt = 0, fail_cnt = 0, consec_fail = 0
2. 循环 batch_n 次（或队列同类耗尽）：
   a. 取下一个候选
   b. 检查前置条件 → 不满足：failures.jsonl + skip，consec_fail++
   c. actions.jsonl 追加一行（result 留空）
   d. 执行，检查 diff ≤ 20 行（超则拆/skip）
   e. W4 评估：
      accept → total_wu += WU; accept_cnt += 1; consec_fail = 0
      fail   → git restore; actions → rollback; fail_cnt += 1; consec_fail += 1
   f. 若 total_wu ≥ 100 或 consec_fail ≥ 3：退出循环
3. 若有 frontmatter 变动，触发 rebuild-registry
4. 每17轮由 /wiki 批量 commit
```

---

## 六、追加新动作

必须经 W5 反思流程（不能凭直觉加）：
- ≥ 3 次同类手动操作 → 写提案到 `reflections/<date>.md`
- 用户确认 → 追加到本目录 + 更新 PROMPT.md WU 表

---

## 相关

- [W0 总则](SKILL_W0_Butler总则.md)
- [W1 探索与食物](SKILL_W1_Butler探索与食物收集.md)
- [W3 质量标准](SKILL_W3_Butler质量标准.md)
- [W4 评估与检验](SKILL_W4_Butler评估与检验.md)
- [W8 精品页建设方法论](SKILL_W8_精品页建设方法论.md) — `premium-upgrade` 的执行指引
