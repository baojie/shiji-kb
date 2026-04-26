---
name: skill-butler-5
description: Butler 的反思与自改机制 — 进化引擎。周期性扫 actions/failures 日志, 识别 pattern, 提案对 W1-W4 的修订。本 skill 修订其他 skill, 不修订自己 (改 W5 必须人工)。修订必须写 reflections/<date>.md + skill_changes.md, 保持保守 (每次反思 ≤ 3 条修订, 优先改阈值不重写结构)。
---

# SKILL W5: 反思与自改

> Butler 的真正 "进化" 发生在这里。其他 skill 是胳膊腿, W5 是大脑皮层。

---

## 一、触发条件

反思不是 happen-every-invocation, 由以下之一触发:

| 触发 | 条件 | 动作 | 可否被批量模式跳过 |
|---|---|---|---|
| **强制周期** | `round_counter.txt` mod 29 == 0 | 自动进入反思 | **否，任何模式都不可跳过** |
| **连续失败** | `failures.jsonl` 最近 3 条同 action type | 立即进入 | 否 |
| **手动** | 用户指示或 `/reflect butler` | 立即进入 | 否 |
| **红旗聚集** | 单个 target 页一周内被标同一红旗 ≥ 3 次 | 进入（针对该页） | 否 |
| **旧触发（已废弃）** | 累计 atomic action 达 20 次 | — | — |

> **旧触发"≥20条未反思"已废弃**，原因：H4 批量模式绕过 PROMPT.md 循环，导致该条件从未被检查，W5 事实上长期不执行。改为基于 `round_counter.txt` 的强制周期（mod 29，质数），任何模式都无法绕过。

**触发时本轮不做 atomic action**，整轮用于反思。

---

## 二、反思流程 (5 步)

### 步骤 1 · 收集素材

```
最近 50 条 actions.jsonl（含 accept + fail）
全部 failures.jsonl
过去 14 天 reflections/ 输出（避免循环提议）
当前 W1–W4 的版本
最近 7 天的对话 JSONL（见步骤 2·F）
```

### 步骤 2 · 模式识别

寻找 **6 类**模式：

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

**E. 队列候选健康** ← *每次反思都必须检查，保证队列有改进候选*

**F. 系统性编辑错误** ← *每次反思都必须检查，防止内容静默丢失*

扫描最近 7 天的项目对话 JSONL（`~/.claude/projects/-home-baojie-work-knowledge-shiji-kb/*.jsonl`，按 mtime 取 ≤7天的文件），提取用户报告或 claude 承认的编辑错误：

```bash
# 找出最近 7 天的对话文件
find ~/.claude/projects/-home-baojie-work-knowledge-shiji-kb/ \
  -name "*.jsonl" -newer wiki/logs/butler/reflections/$(ls wiki/logs/butler/reflections/ | grep -v arch | sort | tail -1) \
  -not -path "*/subagents/*" | sort -t/ -k1
```

重点提取的信号词（在 user 消息中出现）：
- 丢失、删除、覆盖、缺失、没了、不见了、被清空
- lost、missing、deleted、overwritten、gone
- 恢复、还原、restore、rollback

对每类发现的错误模式判断：

| 结果 | 处置 |
|---|---|
| 已有 R 组动作可覆盖 → 只需生成队列条目 | 追加到 `housekeeping_queue.md`（`[repair]` 标记），**不计入** ≤3 条修订限额 |
| 错误重复出现但无对应 R 动作 → 提案新增 R 动作 | 计入修订限额（R 组新增动作属于谨慎的结构扩展） |
| 错误可通过加强现有 action 的前置/后置检查来预防 | 修改对应 W2/W4 条目，计入修订限额 |
| 一次性偶发错误 → 仅记录 | 写入反思底部"已排除"节 |

**G. 随机质量抽查** ← *每次反思都必须执行，模拟用户随机抽查*

随机抽取 10 个页面（recent edits 中随机取 5 个 + 所有地名/人名页随机取 5 个），对每个页面逐项检查：

```bash
# 取最近编辑的 5 个页面
python3 -c "
import json; d=json.load(open('wiki/public/history.json' if __import__('os').path.exists('wiki/public/history.json') else '/dev/null') if False else open('wiki/logs/butler/actions.jsonl'))
" 2>/dev/null || \
python3 - << 'PYEOF'
import json, random, os
from pathlib import Path
# 随机抽样：recent 5 + random 5
actions = []
try:
    with open('wiki/logs/butler/actions.jsonl') as f:
        for line in f:
            try: a = json.loads(line)
            except: continue
            if a.get('target'): actions.append(a['target'])
except: pass
recent5 = list(dict.fromkeys(reversed(actions)))[:5]
all_pages = [p.stem for p in Path('wiki/public/pages').glob('*.md')]
random5 = random.sample(all_pages, min(5, len(all_pages)))
sample = list(dict.fromkeys(recent5 + random5))[:10]
for p in sample: print(p)
PYEOF
```

**每个抽样页面检查清单**（共7项，发现问题即记录）：

| # | 检查项 | 命令/方法 |
|---|--------|---------|
| Q1 | 史记引文节存在 | `grep -c '## 史记引文'` |
| Q2 | 声称N次 == 实际引文条数（N ≤ 10 时严格要求，N > 10 允许展示子集） | `check_citation_count.py` 逻辑 |
| Q3 | 引文格式标准（`> **出自 [[...]]（...）：** ...`） | `grep '^> \*\*出自'` |
| Q4 | frontmatter 必要字段完整（label / type / sources） | `grep '^label:\|^type:\|^sources:'` |
| Q5 | PN 引文（pn 字段中的 PN 有对应引文条目） | 对比 pn 字段与 ## 史记引文 节 |
| Q6 | 正文不为空 stub（非 stub 页面正文 > 100 字） | `wc -c` |
| Q7 | wikilink 密度（正文中 `[[...]]` ≥ 1） | `grep -c '\[\['` |

**问题分类处理**：
- 单页偶发 → 直接修复（不写规则）
- ≥2 页同类问题 → 写入 `wiki/logs/butler/quality_rules.md` + 加入 repair 队列
- 系统性问题（≥5 页同类）→ 同上，另提案 W2/W4 修订

```python
import json, os

data = json.load(open('wiki/public/pages.json'))
pages = data.get('pages', {})
pages_dir = 'wiki/public/pages'

scored = []
for pid, meta in pages.items():
    if not isinstance(meta, dict): continue
    fpath = os.path.join(pages_dir, pid + '.md')
    try: lines = open(fpath, encoding='utf-8').read().count('\n')
    except: continue
    scored.append({'id': pid, 'type': meta.get('type',''), 'lines': lines,
                   'quality': meta.get('quality', 'basic'),
                   'refs': meta.get('total_refs', 0)})

# quality 五级：stub < basic < standard < featured < premium
# 只有 premium 可上首页；编辑后必须跑 compute_quality.py 重评

# expand-content 候选：quality=basic/standard，refs > 0，重点类型
EXPAND_TYPES = {'person','concept','event','overview','story','state'}
expand_pool = sorted(
    [p for p in scored if p['quality'] in ('basic', 'standard')
     and p['refs'] > 0 and p['type'] in EXPAND_TYPES],
    key=lambda x: -x['refs'])

# premium-upgrade 候选：quality=featured，refs > 0（有图有结构，需深化达 premium）
UPGRADE_TYPES = {'person','concept','event','overview','story','sanwen'}
upgrade_pool = sorted(
    [p for p in scored if p['quality'] == 'featured'
     and p['refs'] > 0 and p['type'] in UPGRADE_TYPES],
    key=lambda x: -x['refs'])

print(f'expand 候选池: {len(expand_pool)} 页')
print(f'upgrade 候选池: {len(upgrade_pool)} 页')
print('Top 10 expand:', [p["id"] for p in expand_pool[:10]])
print('Top 10 upgrade:', [p["id"] for p in upgrade_pool[:10]])
```

反思时向 `queue.md` 写入 **≥ 30 个 expand-content** + **≥ 10 个 premium-upgrade** 候选（按 refs 高低排序，去掉已在队列中的重复条目）。格式：
```
- [ ] P1 | [[人名]] | 35行 · refs=42 · type=person | action: expand-content
- [ ] P1 | [[人名]] | 89行 · refs=108 · type=person | action: premium-upgrade
```
此步骤**不计入** ≤3 条修订限额（是观察/补充，不是规则修订）。

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

写 `wiki/logs/butler/reflections/YYYY-MM-DD.md`:

```markdown
# 反思 YYYY-MM-DD（第 R<N> 次，round=<N>）

## 素材
- actions 最近 50 条（R<A>–R<B>）
- failures 共 N 条
- 对话日志：YYYY-MM-DD.jsonl 等 N 个文件

## 识别的模式

### 模式 A/B/C/D/E 类（略，同前）

### 模式 F: 编辑错误（本次反思新增）
- 现象：[对话日志中用户报告的具体错误]
- 影响范围：[N 个页面 / 某类操作]
- 根因：[操作缺乏什么约束 / 检查]
- 已有修复动作：R 组 restore-xxx / 无

### 模式 G: 随机抽查结果
- 抽样页面：[列出10页]
- Q1–Q7 各项通过率：[X/10]
- 发现问题：[具体问题及页面]
- 是否达到规则沉淀阈值（≥2页同类问题）：是/否

## 质量规则沉淀（模式 G 发现 ≥2 页同类问题时写入）

新增/更新 `wiki/logs/butler/quality_rules.md` 条目：
```
- [R<N> 发现] <规则描述> → 检查方法：<Q几> （案例：页面1, 页面2）
```

## 修订清单（skill 修改，≤3 条）
1. [W2/W4 具体修改]
2. ...

## R 组队列补充（不计入修订限额）
- [ ] [repair] P0 | [[页面]] | 原因：史记引文节在 expand 后丢失 | action: restore-lost-section
- [ ] [repair] P0 | [[页面]] | 原因：引文体被覆盖只剩标题 | action: restore-citation-body

## 已排除
- [一次性偶发错误，不做修订]
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

写 `wiki/logs/butler/reflections/arch_YYYY-MM-DD.md`（与普通反思分开存放）:

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
- 若用户回复"暂不处理"，Butler 将临界线调高 20%（记入 `wiki/logs/butler/arch_snooze.json`），避免反复提醒

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
- `wiki/logs/butler/reflections/` — 反思输出沉淀（普通：`YYYY-MM-DD.md`，架构：`arch_YYYY-MM-DD.md`）
- `wiki/logs/butler/skill_changes.md` — 修订 changelog
- `wiki/logs/butler/arch_snooze.json` — 用户暂缓的架构阈值覆盖
- `wiki/scripts/butler/check_scale.py` — 规模指标快照工具（每次反思必跑）
- `wiki/logs/butler/quality_rules.md` — 质量规则库（Pattern G 沉淀，≥2页同类问题才写入）
- `wiki/scripts/butler/check_citation_count.py` — Q2 引文数量检查工具

---

## KB 写入规则

反思结束后，将定论写入 `wiki/logs/butler/kb/w5_ops.md`：

- **写什么**：在 ≥2 次反思中重复出现、被 W5 修订采纳的操作规则
- **不写什么**：单次失败、偶发异常、未经 ≥2 次验证的猜测
- **格式**：`- [R<N> 确认] <条件> → <结论>` 追加到对应分组（行动成功模式 / 行动失败模式 / 已废弃路径）
- **更新旧规则**：改写原行，加 `[R<N> 更新，原见 R<M>]` 标注
