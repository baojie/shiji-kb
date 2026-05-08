---
name: skill-butler-2
description: Butler 的原子行动目录 — 24 种标准操作的前置条件、执行步骤、后置检查、预期 diff 大小与工作量单位(WU)。每次 invocation 按WU批量执行同类动作直到累计1000WU，单个动作 diff ≤ 20 行。禁止自由发挥, 只能从此目录挑。新操作由 W5 反思流程追加。
---

# SKILL W2: 原子行动目录

> 每轮按"工作量单位(WU)"批量执行同类动作，目标 1000 WU/轮。本 skill 是菜单——选一类，批量做。

---

## 一、通用约定

- **单次 diff ≤ 20 行**（含空行），超则拆
- 每轮按 **WU** 批量执行同类动作，目标 1000 WU/轮（见 PROMPT.md WU 表）
- W4 **accept** → 不做 git add（staging 统一由 /wiki commit 轮执行）
- W4 **fail** → `git restore <file>` 回滚工作区
- **批量 commit**：每23轮由 `/wiki` skill 统一 commit + push（`round_counter.txt` mod 23 == 0）
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

### 可用 Skill 工具（执行动作时可调用）

| Skill | 命令 | 适用动作 |
|-------|------|---------|
| `/quote PAGE` | `python3 .claude/skills/quote/scripts/quote_page.py PAGE` | 补 `## 史记引文`：扫实体标注文件找引用，精确到年表行，过滤已引 |
| `/enrich PAGE [目标档]` | 调用 enrich skill | `enrich-biography` / `premium-upgrade`：诊断质量缺口后一键升档 |
| `/map PAGE [时代]` | `python3 .claude/skills/map/scripts/map_page.py PAGE all` | `add-war-map` / `fetch-image` 失败后：地名/事件页自动裁谭图，需 `coords` 字段 |

---

### A 组 · 内容创建与扩充（最高频）

| 动作 | WU | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|---|
| `source-with-pn` | 1 | 页面无 `sources`/`event_ids` 字段 + canonical_name ≥ 3 字 | ① `find_unsourced.py --target <slug>` 确认匹配 ② `edit_page.py` 加 frontmatter `sources:` + `event_ids:` ③ 正文加 `(NNN-MMM)` 行内引注 | frontmatter 含两字段；引注 event_id 能在章节事件表找到 | 3–6 行 |
| `create-stub` | 5 | kg canonical 无 wiki 页 + 有 lifespan / refs | 跑 `generate_entity_page.py <name>` 生成，再用 `add_page.py` 写入（自动记修订） | 页面生成，pages.json 可扫到 | 新文件 ≤ 50 行 |
| `add-event-timeline` | 5 | 人物页无"生平大事"区 + kg 有事件 | 跑 `python3 wiki/scripts/butler/enrich_timeline.py <slug>` 插入"生平大事"区 | 表格 markdown 合法，event id 可追溯 | 10–15 行 |
| `audit-completeness` | 2 | 页面存在 | ① 查 `docs/original_text/NNN_*.txt` 原文所有提及 ② 查 `kg/ontology/` 对应 entity/fact 数据 ③ 查反链页是否有未收录的关联信息 ④ 对比当前页内容，判断信息完整性；发现缺失 → 记入 queue.md（`[missing-<章节>]`）；完整则无操作 | queue 无新增缺失条目（或已记录）；页面 diff 0 | 0 行 |
| `expand-content` | 3 | 页面存在 + 正文内容稀薄（< 20 行实质内容）+ 有 kg/chapter 来源 | 用 `edit_page.py` **追加**一个新节或补充一段正文（biography/evaluation/成语/相关事件之一）；**🚨 写入前必须检查：若页面已有 `## 史记引文` 节，必须原样保留，绝不覆盖** | 节不存在才追加；不覆盖既有节；`## 史记引文` 节在写入后仍然完整存在 | 8–20 行 |
| `enrich-biography` | 15 | 人物页 quality=standard + sources 字段含 ≥1 章节 + 原文在 `docs/original_text/` 可grep到该人名 | **优先调用 `/quote PAGE` 收集引文候选**，再以**蔡哀侯页为模板**写完整传记：① 读 `docs/original_text/NNN_*.txt`，grep 人名相关句 ② 写"即位/生平"节（叙述原文事迹，加引文块）③ 若多源有矛盾，写"⚠️ 史料矛盾"节（含对照表） ④ 写"身后/太史公赞"节 ⑤ 完善 frontmatter `description` ⑥ `edit_page.py` 写入；⑦ `compute_quality.py <slug>` 验证升为 featured；**或直接调用 `/enrich PAGE featured`** | quality 升为 featured；叙述节 ≥ 3；引文 ≥ 3 条可 grep 到原文；frontmatter description 不含"出现X处" | 40–80 行 |
| `premium-upgrade` | 10 | 目标在精品页建设队列（W8/H7）+ 页面 ≥ 20 行基础内容 | **优先调用 `/quote PAGE` 补引文**，以事实收集为主：① **必须**执行跨章节互见搜索（从 `## 史记引文` 章节分布扫描非专传章节他人评语）② 优先新增**原文引文块** ③ 若需补充分析，≤ 150 字；**或直接调用 `/enrich PAGE premium`** | 新增内容有 PN 引注；含 ≥ 1 处来自**非专传章节**的他人原文评价；分析文字 ≤ 原文引用字数；单次 diff ≤ 20 行 | 10–20 行 |
| `cite-doc-report` | 2 | 页面某断言 + `doc/` 对应报告存在 | 断言后加 `[^ref]` 脚注，指向 doc/ 文件 | 脚注编号不冲突，文件可打开 | 2–4 行 |

### A₂ 组 · 页面重构（低频实验性）

> **实验性动作**，等待更多案例验证后正式纳入 A 组。当前 W2 §六要求 ≥3 次同类手动操作才走 W5 正式追加，此动作标记为 `[EXPERIMENTAL]`。

| 动作 | WU | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|---|
| `refactor` | 5 | 页面有结构问题（重复节/节序错乱/内容分散/冗余膨胀）+ 已通过 `audit-completeness` 确认信息完整 + 不涉及实质信息增减 | ① 若尚未执行 `audit-completeness`，先扫描信息完整性 ② **信息整合**：合并分散到各处的同一主题内容，删除完全重复的节或段 ③ **结构提升**：按逻辑流重构节序，核心原则——**`## 跨章节互见` 不应在页底**，应融入主叙述区（推荐位置：`## 地理` 之后、`## 历史评价` 之前）；参考节序：`生平`→`地理`→`跨章节互见`→`称谓考`→`历史评价`→`对照表`→固定元数据节 ④ 保留所有引文块、PN 引注、wikilink 不变 ⑤ `edit_page.py` 写入 | 无内容丢失（`check_size_loss.py` safe 或预期内减少）；无重复节；wikilink 和 PN 引注完整；跨章节互见不在页底 | −2000~−5000B（精简冗余）或持平（仅调整顺序） |

**注意**：
- `refactor` 不改变 `quality` 字段（除非 refactor 后页面的实质内容确有质变）。高频误判（如把"内容不足"当成结构问题）应记入 `failures.jsonl`。
- **叙事逻辑流**：重构时的节序应遵循"故事 → 空间背景 → 跨篇章拼合 → 评价 → 参考材料"的逻辑流。`## 跨章节互见` 不是附录，是主叙述的收束——它回答"我们从哪些来源知道这些"后，再进入历史评价。参考节序：`生平`→`地理`→`跨章节互见`→`称谓考`→`历史评价`→`对照表`→固定元数据节。

---

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
| `rename-page` | 3 | 页面名称是短称/歧义名（如"意"）+ SKILL_03b 能确定规范名（如"周意"）+ 无同名页面冲突 | ① 按 SKILL_03b §六确认规范名（优先"国+谥号"或"姓+名"，核对上下文邦国） ② 读取原页全文 ③ `add_page.py <规范名> <content_file> --author butler` 建新页 ④ `edit_page.py <原名>` 将原页内容替换为单行 `#REDIRECT [[规范名]]` ⑤ `wiki/public/backlinks.json`：为原页（REDIRECT）加条目 `{"原名": [{"id":"规范名","label":"规范名","type":"<type>"}]}`（REDIRECT 页需计入反链） ⑥ `wiki/public/pages.json`：加新页条目 + `alias_index[原名] = 规范名` | 新页存在；原页仅含 `#REDIRECT`；backlinks.json 含 REDIRECT 页反链；pages.json 无断链 | 新文件 ≤ 50 行 + 1 行 REDIRECT |
| `delete-page` | 5 | 页面重复/错误/合并 + 有用户或 W11 授权 | ① `record_revision.py <slug> --action delete` ② `git rm wiki/public/pages/<slug>.md` ③ history JSON 保留 | history JSON 含 `deleted:true`；pages.json 重建后无此页 | 删文件 |
| `rebuild-registry` | — | 前述动作涉及 frontmatter 变动 | 跑 `build_registry.py` + `build_backlinks.py` | pages.json 注入 semantic 成功 | 2 文件 |
| `rollback` | — | 前一动作评估为 fail | `git restore <file>` + failures.jsonl | 工作区干净 | 自动 |
| `observe-only` | 1 | 本轮探索到候选但已达批次上限 | 仅更新 queue.md | queue.md 新增条目 | 1–3 行 |

### G 组 · 配图（quality=featured 或 premium 页面专用）

> 仅对 `quality=featured` 或 `quality=premium` 的页面执行。stub/basic/standard 页面不做此类动作。
> 配图是 `featured` → `premium` 晋级的必要条件之一。

| 动作 | WU | 前置 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|---|
| `fetch-image` | 5 | 页面 `quality=featured` 或 `quality=premium` + frontmatter 无 `image` 字段 | ① 跑 `python3 wiki/scripts/butler/fetch_image.py <slug>` ② 解析输出 JSON ③ **found=true**：用 `edit_page.py` 在 frontmatter 追加 `image`/`image_caption`/`image_credit` 三字段 ④ **found=false**：触发 `gen-image-prompt` 动作（写提示词队列） | `image` 字段存在；`wiki/public/images/<label>.jpg` 文件存在；`images/sources.json` 已更新 | 3–4 行 frontmatter |
| `gen-image-prompt` | 3 | `fetch-image` 已执行但返回 found=false（或页面无图且 Wikimedia 无合适来源）| ① 读取 `fetch_image.py` 返回的 `prompt` 字段 ② 追加到 `wiki/logs/butler/image_prompts.md`（格式见下）③ 在页面 frontmatter 追加 `image_prompt:` 占位字段（供人工确认后生成图片） | `image_prompts.md` 新增一条；页面有 `image_prompt:` 字段 | 1–2 行 frontmatter + 1 行日志 |
| `add-war-map` | 5 | 页面 `event_type: 战争` + 无 `image` 字段 + H24 队列任务 | **若页面 frontmatter 有 `coords` 字段 → 直接调用 `/map PAGE`**（自动裁切，输出 images 片段写入 frontmatter）。否则走手动流程：① 读取 `location`（主战场）② 查 `place_index.json` ③ 选谭图分区图 ④ 目视定位裁切 ⑤ 用 `edit_page.py` 追加 `image`/`image_caption`/`image_credit` | 图片文件存在；页面 frontmatter 有 `image`/`images` 字段 | 3–4 行 frontmatter + 1 张图 |

**`image_prompts.md` 条目格式**：
```markdown
- [ ] [[<slug>]] (<type>) — <label>
  prompt: <AI生成提示词>
  added: <YYYY-MM-DD>
```

**执行顺序**：先 `fetch-image`，若失败则 `gen-image-prompt`；两者不并行。
**决策树补充**：在 W2 §四决策树"2. fix-citation"之前插入：
- 页面在首页候选 + 无 `image` 字段 → **优先执行 `fetch-image`**

---

### R 组 · 错误修复（最高优先级，发现即执行）

> **R 组优先于一切常规扩充操作。** `check_size_loss.py` 返回 critical、用户报告内容丢失、或 `housekeeping_queue.md` 有 `[repair]` 标记时，必须先清空 R 组队列，再做其他动作。

| 动作 | WU | 触发条件 | 做什么 | 后置检查 | 典型 diff |
|---|---|---|---|---|---|
| `restore-lost-section` | 2 | 当前页缺少某节（`## 史记引文`、`## 原文`、`## 故事` 等）+ 历史版本 revisions[1..] 含该节 | ① 从 history JSON 提取最近含目标节的版本内容 ② 用 `edit_page.py --allow-citation-edit`（若目标节为引文节）或普通 `edit_page.py` 将节插回当前页，插入位置在 `## 相关章节` 之前 | 节在写入后存在；`check_size_loss.py` 返回 safe | 5–30 行 |
| `restore-citation-body` | 3 | `## 史记引文` 节存在但内容稀薄（只有标题+链接列表，无 `> 出自` 引文摘录）+ 历史版本有完整引文 | ① 从 history 定位最近一个含 `> 出自` 的版本 ② 提取完整引文内容 ③ 用 `edit_page.py --allow-citation-edit` 替换当前空洞的引文节 | 节含 `> 出自` 引文摘录 + PN 引注；字数 > 前版 | 10–30 行 |
| `revert-expand-loss` | 3 | `check_size_loss.py` 输出 critical + 最近一次操作为 expand/narrative + 历史版本有当前版本缺失的节 | ① `check_size_loss.py <slug>` 确认 critical 及 `lost_sections` 列表 ② 对每个缺失节执行 `restore-lost-section` ③ 保留 expand 写入的 narrative 正文，仅追加缺失节 | `check_size_loss.py` 返回 safe；所有历史节均存在 | 5–40 行 |
| `fix-timeline-entry` | 2 | 页面"生平大事"节含事件 + 某条事件人名/时代明显属于其他实体（如单字别名误匹配导致）| ① 逐条核验事件 event_id 是否出现在该实体的 kg/entities 记录中 ② 删除归属错误的行；若有缺失正确事件，从 `enrich_timeline.py` 补回 | 剩余每条事件的 event_id 在 kg 可追溯到本页实体 | 1–5 行 |
| `audit-repair-queue` | 1 | 每 11 轮或用户触发 | 对最近 N 轮 expand/narrative 操作页面批量运行 `check_size_loss.py`；将 critical 结果追加到 `housekeeping_queue.md`（`[repair]` 标记）；**不修改任何页面** | queue 新增条目；failures.jsonl 无新增 | 0 行（扫描） |

**R 组使用说明**：

- `restore-lost-section` 和 `restore-citation-body` 是最常用的两个，可批量串行执行
- `revert-expand-loss` 是 `restore-lost-section` 的组合版，针对单页多节全部丢失的情况
- `fix-timeline-entry` 针对 enrich_timeline 单字别名误匹配问题（2026-04-22 血泪教训）
- `audit-repair-queue` 是扫描动作，不直接修复，产出的 queue 条目供后续轮次处理

**已有辅助脚本**：

```bash
# 批量扫描并修复史记引文丢失（R 组 restore-lost-section 的批量版）
python3 wiki/scripts/butler/restore_shiji_citations.py [--slug SLUG] [--dry-run]

# 单页字数损失检测（R 组所有动作的前置诊断）
python3 wiki/scripts/butler/check_size_loss.py <slug>
```

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

## 三·一、铁律：`## 史记引文` 节永久保护

> **任何原子操作都不得删除或替换 `## 史记引文` 节。**

| 操作类型 | 对史记引文节的权限 |
|---|---|
| `fix-citation`（B组纠错） | ✅ 可编辑节内引文内容（修正错误文字/补充PN），需加 `--allow-citation-edit` |
| `H1` 去重合并（`SKILL_W10a`） | ✅ 可合并两个版本的引文节，需加 `--allow-citation-edit` |
| **其他所有原子操作** | ⛔ **永远禁止触碰此节**，违反则 `edit_page.py` 拒绝写入（退出码2） |

**执行机制**：`edit_page.py` 在写入前自动检查。若旧版有此节、新版无此节，且未传 `--allow-citation-edit`，脚本直接报错退出，不写入任何内容。

**血泪教训（2026-04-26）**：H4-narrative扩写批量覆盖全量页面内容，导致354个页面的 `## 史记引文` 节被静默删除，需专项脚本逐一恢复。

---

## 四、选哪个动作（决策树）

由 W1 的候选决定。若候选有 `action` 字段，直接用。

若候选无 action，按优先顺序：

**⚠️ R 组优先检查（每轮第一步）**：
- `housekeeping_queue.md` 有 `[repair]` 标记条目，或 `check_size_loss.py` 返回 critical → **本轮 WU 配额优先分配给 R 组**；配额用完即止，剩余 repair 条目留到下轮，不阻塞常规动作
- 具体触发规则：
  - `[repair]` 队列有条目 → `revert-expand-loss` 或 `restore-lost-section`（视缺失内容而定）
  - 页面有 `## 史记引文` 节但无 `> 出自` 引文摘录 → `restore-citation-body`
  - 页面"生平大事"节含明显错误归属事件 → `fix-timeline-entry`

**常规动作（R 组清空后）**：

1. 页面不存在 → `create-stub`
2. 页面在**首页候选**（H21逻辑选出）+ 无 `image` 字段 → `fetch-image`（找不到则 `gen-image-prompt`）
2b. 页面 `event_type: 战争` + 无 `image` 字段 + H24 队列有该页 → `add-war-map`
3. `citation_issues.jsonl` 有该页未修复条目 → `fix-citation`
4. 页面存在 + 无 `sources` 字段 → `source-with-pn`
5. 页面存在 + 无"生平大事"区 + 是人物页 → `add-event-timeline`
6. 页面在精品页建设队列 → `premium-upgrade`
7. 页面正文 < 20 行实质内容 → `expand-content`
7b. 页面有结构问题需重构 → 先执行 `audit-completeness`（确认信息完整后再走 refactor）
8. frontmatter infobox 稀疏 → `enrich-infobox`
9. 页面有 aliases 但缺 REDIRECT → `create-redirect`
10. 页面有 broken link → `fix-broken-link`
11. 页面名称是短称/歧义名 + SKILL_03b 上下文（所属邦国/姓氏）能确定规范名 → `rename-page`
12. 其他 → `observe-only`，加 queue

---

## 五、执行步骤模板（批量模式）

```
0. 查 WU 表，确定本轮 action 类型；batch_n = ceil(500 / WU)
1. total_wu = 0, accept_cnt = 0, fail_cnt = 0, consec_fail = 0
2. 循环 batch_n 次（或队列同类耗尽）：
   a. 取下一个候选
   b. 检查前置条件 → 不满足：failures.jsonl + skip，consec_fail++
   c. actions.jsonl 追加一行（result 留空）
   d. 执行，检查 diff ≤ 20 行（超则拆/skip）
   e. **revision 检查（accept 前必须）**：本轮若写入了 `wiki/public/pages/<slug>.md`
      （无论通过 edit_page.py、add_page.py、Edit 工具还是其他方式），
      必须确认 `wiki/public/history/<slug>.json` 的 `latest_rev_id` 已更新到本轮。
      验证：`python3 -c "import json; d=json.load(open('wiki/public/history/<slug>.json')); print(d['latest_rev_id'])"`
      若未更新 → 立即补调：`python3 wiki/scripts/butler/record_revision.py <slug> --summary "<action>: ..." --author <author>`
      然后再继续 W4 评估。
   f. W4 评估：
      accept → total_wu += WU; accept_cnt += 1; consec_fail = 0
      fail   → git restore; actions → rollback; fail_cnt += 1; consec_fail += 1
   f. 若 total_wu ≥ 500 或 consec_fail ≥ 3：退出循环
3. 若有 frontmatter 变动，触发 rebuild-registry
4. 每23轮由 /wiki 批量 commit
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
