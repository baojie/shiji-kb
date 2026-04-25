---
name: SKILL_W10_Butler内务整理
title: Wiki 内务整理（Housekeeping）队列与流程
description: 发现并修复 wiki 结构性缺陷与内容空白：重复合并、链接补全、重定向、溯源、标签、列表页、引文核验、全文覆盖查验等。维护 wiki/logs/butler/housekeeping_queue.md，队列空时优先执行内务任务。
---

# SKILL W10: 内务整理（Housekeeping）

> "知识库的质量 = 内容正确性 × 结构整洁性 × 文本覆盖完整性"。W3-W9 保证内容，W10 保证结构与覆盖。

---

## 零、内务任务全类型一览

| 类型 | 名称 | 优先级 | 工具/技能 |
|---|---|---|---|
| **H1** | 重复/冗余页面融合 | P0 | W10a, discover_duplicates.py |
| **H2** | 词汇链接化（补 wikilink） | P1 | discover_kg.py |
| **H3** | 重定向页创建（REDIRECT） | P1 | reflection_scan.py |
| **H4** | 原文溯源增补（pn/sources） | P1 | find_unsourced.py |
| **H5** | 断链新建条目（create-stub） | P1 | build_backlinks.py |
| **H6** | 随机页面小幅优化增补 | P2 | 随机抽样+人工判断 |
| **H7** | 重要页面大幅增补（featured） | P1 | W8 |
| **H8** | 标签与分类增补 | P2 | add-tag（W2） |
| **H9** | 列表页建设（共属性页面群） | P2 | W12 |
| **H10** | 页面错误反思与修订 | P0 | W9 |
| **H11** | 引文出处与 PN 一致性检验 | P1 | W7, verify_quotes_agent.py |
| **H12** | 重复内容整合反思 | P2 | W10a |
| **H13** | 史记全文 wiki 覆盖查验 | P1 | **W13**（专用 skill） |
| **H14** | 元反思：改进 skill/脚本/知识库设计 | P2 | W5 |
| **H15** | 清理残留语法标注（〖〗⟦⟧泄漏） | P1 | grep + 正则替换 |
| **H16** | 实体消歧义（单字名加姓 + 变链接） | P1 | entity_index + H2 |
| **H17** | 章节 meta 语义块建设 | P2 | W2 embed-sku-excerpt |
| **H18** | Stub 页面扩展反思（或降级去 stub） | P2 | W8 / edit_page.py |
| **H19** | 正文断言真实性核验 + PN 脚注附注 | P1 | W7 / find_pn_for_quote.py |
| **H20** | 洞察问题驱动探索（实体关联假设） | P2 | **W14**（专用 skill） |

**队列为空时**：按 H1→H15→H16→H19→H13→H5→H11→H14→H20→H6 顺序，各取一条发起扫描，补入队列。

**各反思 Agent 分工**（W10 是总调度）：

| Agent | 职责 | 输出给 W10 的类型 |
|---|---|---|
| **W5** | 日志反思，修订 skill | H14 |
| **W7** | 引文核验，发现错误引注 | H11, H19 |
| **W9** | 页面图式扫描，发现结构异常 | H10 |
| **W10a** | 重复页合并操作 | H1, H12 |
| **W11** | 概念页类型/分类审查 | H10, H8 |
| **W13** | 史记全文句子覆盖查验 | H13 |
| **W14** | 实体关联洞察，生成问题假设 | H20 |

---

## 一、原有四类内务任务（详规范）

### 类型 H1：重复/冗余页面融合

**完整操作规范见** → [`SKILL_W10a_Butler去重合并.md`](SKILL_W10a_Butler去重合并.md)

**核心原则**（摘要）：
1. **先 Union**：读完所有候选页，取各自独有内容，合并为超集
2. **再反思剪裁**：去除重复段落，统一术语
3. **REDIRECT 而非删除**：冗余页必须改为 `type: redirect` 页，❌ 绝对禁止 `rm`

**发现方法**：
```bash
# W10 标准扫描（每 10 轮运行）：基于前缀 + Jaccard 相似度，写入队列
python3 wiki/scripts/butler/discover_duplicates.py --max-new 10
# 自动过滤假阳性：人物页+事件子页、系列页（张仪说X王）、已有 REDIRECT 的页
```

**处理流程**（简版，详见 W10a）：
1. 读取所有候选页 → 判断是否真重复
2. 确定规范页（短名优先）→ Union 内容 → 反思剪裁 → 写入
3. 调用 `record_revision.py` → 冗余页改 REDIRECT → 更新反向链接

**优先级**：
- P0：同主题两个以上页面，Jaccard > 0.4
- P1：标题相似但内容差异较大，需人工判断
- P2：长标题 vs 短标题变体（如功能相同但命名不同）

---

### 类型 H2：链接补全（Wikilink 织网）

**现象**：页面正文中提及人名/事件/概念，但未用 `[[]]` 语法链接。

**发现方法**：
```bash
# 扫描页面，找未链接但已有对应页面的词汇
python3 wiki/scripts/butler/discover_kg.py --mode missing-links --target <slug>

# 或批量扫描 quality_score 低且 resolved_wikilinks 少的页面
# 从 pages.json 筛选 link_density 维度低的页面
```

**处理规则**：
1. **只加第一次出现的链接**：同一词汇在页面内只链第一次
2. **确认目标页存在**：`[[XX]]` 前先确认 `wiki/public/pages/XX.md` 存在
3. **消歧语法**：多义词用 `[[规范名|显示名]]`，如 `[[汉武帝|孝武帝]]`
4. **不改原文**：只加 `[[]]` 括号，不修改任何文字内容
5. **每次最多补 5 个链接**：控制 diff 大小（≤ 20 行不变量）

**优先级**：
- P0：主要传记章节的人物互链（同传中互相出现的人物）
- P1：高频人物（刘邦、项羽、孔子等）在非人物页中未链
- P2：已有精品页的事件/概念，在相关人物页中未链

---

### 类型 H3：重定向页创建（REDIRECT）

**现象**：同一人物/概念有多种称呼，不同页面用法不一，用户搜索某种叫法找不到页面。

**典型例子**：
- `辟阳侯` ↔ `审食其`（同一人，两种常用称呼）
- `黥布` ↔ `英布`（同一人，《史记》内前后异称）
- `司马谈论六家要旨` ↔ `司马谈论六家要指`（同一文章名，旨/指之异）

**发现方法**：
```bash
# 查看 alias_conflicts.json（自动检测别名冲突）
python3 wiki/scripts/butler/reflection_scan.py --aspect alias

# 检查 pages.json 中有 aliases 字段但无对应 REDIRECT 页的情况
python3 -c "
import json
pages = json.load(open('wiki/public/pages.json'))['pages']
import os
for pid, p in pages.items():
    for alias in p.get('aliases', []):
        if alias != pid and not os.path.exists(f'wiki/public/pages/{alias}.md'):
            print(f'MISSING REDIRECT: {alias} → {pid}')
" 2>/dev/null | head -20
```

**REDIRECT 页格式**：

```markdown
---
id: 辟阳侯
type: redirect
label: 辟阳侯
redirect_to: 审食其
---

# 辟阳侯

> **重定向**：本页重定向至 [[审食其]]。
> 
> 辟阳侯为[[审食其]]的封号，详见 [[审食其]] 页面。
```

**处理优先级**：
- P0：aliases 字段已有但无 REDIRECT 页的情况（自动可检测）
- P1：alias_conflicts.json 中同 surface 指向多页的高冲突项
- P2：用户报告找不到的页面

---

### 类型 H4：史记原文溯源增补

**现象**：person/concept/overview 等页面有内容，但缺少 `sources`、`event_ids`、`pn` 等溯源字段，无法追溯到《史记》原文具体段落。

**发现方法**：
```bash
# 扫描缺少溯源字段的页面，在原文中查找对应 PN
python3 wiki/scripts/butler/find_unsourced.py --max 20
# 只处理指定页面（调试用）
python3 wiki/scripts/butler/find_unsourced.py --target 韩王成
# 批量写入 housekeeping_queue.md
python3 wiki/scripts/butler/find_unsourced.py --max 50 --write-queue
```

**匹配规则**：
- canonical_name **≥ 3 字**才做自动匹配（1-2 字误链风险太高）
- 只返回 score ≥ 0.8 的原文段落（精确子串匹配优先）
- 工具内部调用 `find_pn_for_quote.py`，直接从 `chapter_md/*.tagged.md` 取 PN

**处理步骤**：
1. 对队列中的 H4 条目，读取建议的 `sources` / `pn` 列表
2. 人工或 butler 确认 PN 确实与页面内容相关
3. 用 `edit_page.py` 在 frontmatter 补充 `sources:` / `event_ids:`，正文加行内 PN 引注
4. 调用 W2 中的 `source-with-pn` 原子动作

**优先级**：
- P1：person 页有3行以上内容但无任何溯源字段
- P2：concept/overview 页缺溯源

---

## 二、Housekeeping 队列格式

文件：`wiki/logs/butler/housekeeping_queue.md`

```markdown
# Housekeeping 队列

最后更新: YYYY-MM-DD

## P0（立即处理）

- [ ] H1 合并 司马谈论六家要指 + 司马谈论六家要旨 + 司马谈六家论
      → 三页均指同一篇文章，需合并为一页，其余改 REDIRECT
      → 发现于: 2026-04-23 用户报告
- [ ] H3 创建 REDIRECT: 辟阳侯 → 审食其
      → 发现于: alias_conflicts 2026-04-23

## P1（本周内处理）

- [ ] H2 补链: 鸿门宴.md 中 曹无伤/项庄/靳彊 未全部链接
- [ ] H3 创建 REDIRECT: 黥布 → 英布（或反向）
- [ ] **H4** 溯源增补：`韩王成`
      建议 sources: [项羽本纪, 留侯世家]
      建议 pn: [(007-96.1), (007-105.1), (055-7), (055-11)]
      → 发现: find_unsourced 扫描

## P2（积压）

- [ ] H1 检查 七国之乱 / 吴楚七国之乱 / 七国叛乱 是否重复
```

**队列字段说明**：
- `H1/H2/H3`：任务类型
- `[ ]`/`[x]`：未完成/已完成
- 发现方式和时间（便于追溯）

---

## 二·五、H5–H14 扩展类型简述

### H5：断链新建条目
- **发现**：`python3 -c "import json; [print(t) for p in json.load(open('wiki/public/pages.json'))['pages'].values() for t in p.get('broken_wikilinks',[])]" | sort | uniq -c | sort -rn | head -20`
- **处理**：对高频断链（≥3 页引用），调用 W2 `create-stub` 动作建 stub 页

### H6：随机页面小幅优化
- **发现**：`shuf wiki/public/pages/*.md | head -5`，人工浏览，判断是否有 missing infobox / 未链词汇 / 空白节
- **处理**：归入对应的 H2/H4/H8 条目，下轮执行

### H7：重要页面大幅增补
- **发现**：pages.json 中 `quality_score < 0.4` 且 `featured=false` 的 person/concept 页
- **处理**：移入 W8 精品页建设流程；在 housekeeping_queue 记录一行后转交

### H8：标签与分类增补
- **发现**：`python3 -c "import json; [print(k) for k,v in json.load(open('wiki/public/pages.json'))['pages'].items() if not v.get('tags')]" | head -20`
- **处理**：W2 `add-tag` 原子动作，每次 1 个页面补 1-3 个标签

### H9：列表页建设
- **发现**：在 pages.json 里发现有共同 tag/type 属性的页面簇（≥5 页同标签且无列表页汇总）
- **处理**：移入 W12 语义查询列表页流程

### H10：页面错误反思
- **发现**：W9 图式扫描输出 `schema_patterns/` 中标记的异常；用户报告；引文核验 issues
- **处理**：P0 立即修复（edit_page.py）；P1 写入队列

### H11：引文出处与 PN 一致性检验
- **发现 & 处理**：调用 W7 `verify-citations` 动作，处理一个页面；issues 写入 `citation_issues.jsonl`

### H12：重复内容整合反思
- **发现**：Jaccard < 0.4 但人工看出内容重叠的页面对；或同一段引文出现在两个页面
- **处理**：先记录到 P2 队列，待 H1 合并时一并处理

### H13：史记全文 wiki 覆盖查验
- **发现 & 处理**：独立 skill **W13**；输出 `coverage_map.json` + 未覆盖段落队列 → 本队列接收并按 P2 入列

### H14：元反思（改进 skill/脚本/知识库设计）
- **触发**：读取最近 5 轮 `/wiki` commit 报告 + `failures.jsonl`，提出结构性改进建议
- **处理**：走 W5 流程，写 `reflections/YYYY-MM-DD.md`，经用户确认后修改 skill 文件

### H15：清理残留语法标注

**现象**：wiki 页面正文中残留了从 tagged.md 带入的标注符号，如 `〖◆刘邦〗`、`⟦○攻〗`、`〖;丞相〗`，影响渲染和可读性。

**发现方法**：
```bash
# 扫描所有 wiki 页面，找含标注符号的页面
grep -rl '〖\|⟦\|〗\|⟧' wiki/public/pages/ | head -20

# 统计各类标注符号出现次数
grep -oh '〖[^〗]*〗\|⟦[^⟧]*⟧' wiki/public/pages/*.md | sort | uniq -c | sort -rn | head -30
```

**清理规则**（严格保留显示文本，只剥离标注符号）：

| 标注格式 | 替换为 | 示例 |
|---|---|---|
| `〖◆实体名〗` | `实体名` | `〖◆刘邦〗` → `刘邦` |
| `〖◆显示名\|规范名〗` | `显示名` | `〖◆沛公\|刘邦〗` → `沛公` |
| `〖;职位〗` | `职位` | `〖;丞相〗` → `丞相` |
| `⟦○动词〗` | `动词` | `⟦○攻〗` → `攻` |
| `〖%地名〗` | `地名` | `〖%咸阳〗` → `咸阳` |
| `〘※成语〙` | `成语` | `〘※破釜沉舟〙` → `破釜沉舟` |

**禁止**：不得修改非标注内容；清理后若发现实体名，应顺手转为 wikilink（见 H16）。

**处理**：用 `edit_page.py` 写入清理后内容，diff ≤ 20 行（标注密集页拆多轮）。

**优先级**：P1（影响正常阅读）；一次最多清一个页面的一个节。

---

### H16：实体消歧义（单字名加姓，变 wikilink）

**现象**：wiki 页面正文中出现孤立的单字或双字人名（如"亮曰"、"羽大怒"、"邦称帝"），没有补全姓氏，也没有 wikilink，读者无法判断所指。

**发现方法**：
```bash
# 从 entity_index.json 取所有 person 类型的 canonical_name
# 找 1-2 字的规范名，在 wiki 页面中搜索无链接的孤立出现
python3 -c "
import json, re, glob

idx = json.load(open('kg/entities/data/entity_index.json'))
# 取 1-2 字人名
short_persons = {k for k in idx.get('person', {}) if 1 <= len(k) <= 2}

hits = []
for f in glob.glob('wiki/public/pages/*.md'):
    txt = open(f).read()
    for name in short_persons:
        # 出现但未被 [[]] 包围
        pattern = rf'(?<!\[)(?<!\|){re.escape(name)}(?!\|)(?!\])'
        if re.search(pattern, txt):
            hits.append((f.split('/')[-1], name))
print('\n'.join(f'{f}: {n}' for f,n in hits[:30]))
"
```

**消歧义规则**：

1. **确认规范名**：在 `entity_index.json` 中查找 canonical name（含姓）
2. **确认 wiki 页存在**：`wiki/public/pages/{canonical}.md` 必须存在
3. **消歧义链接格式**：`[[完整规范名|显示名]]`，如 `[[诸葛亮|亮]]`、`[[项羽|羽]]`
4. **同页只改首次出现**（H2 原则）
5. **上下文优先**：若同段已有 `[[项羽]]` 出现，后续 `羽` 不重复链

**歧义处理**：若 1-2 字名对应多个 person（如"亮"可能是诸葛亮或其他），上下文不能确定时**跳过**，记为 P2 队列供人工判断。

**优先级**：P1（影响理解）；每次一个页面不超过 5 处修改。

---

### H17：章节 meta 语义块建设

**现象**：章节页（`type: chapter`，slug 如 `070_张仪列传`）缺少结构化的元信息摘要块，搜索和列表查询无法按"主角/时段/主题/类型"筛选章节。

**目标**：为每个章节页追加 `## 章节概览` 节，格式固定，机器可读。

**`## 章节概览` 标准格式**：

```markdown
## 章节概览

| 属性 | 内容 |
|---|---|
| **类型** | 本纪 / 世家 / 列传 / 书 / 表 |
| **时段** | 上古 / 先秦 / 战国 / 秦 / 汉初 / 西汉 |
| **主角** | [[张仪]] · [[苏秦]] |
| **核心主题** | 外交 · 纵横策略 · 连横 |
| **关键事件** | [[合纵连横]] · [[秦惠文王称王]] |
| **段落数** | 62（含 `[N]` 段落） |
| **字数** | 约 5,400 字 |
```

**frontmatter 同步**（可选，便于 `:::query` 筛选）：
```yaml
chapter_type: 列传
period: [战国, 秦]
protagonists: [张仪, 苏秦]
themes: [外交, 纵横]
```

**发现方法**：
```bash
# 找所有 type=chapter 但无 ## 章节概览 节的页面
python3 -c "
import json, glob
pages = json.load(open('wiki/public/pages.json'))['pages']
for slug, meta in pages.items():
    if meta.get('type') == 'chapter':
        txt = open(f'wiki/public/pages/{slug}.md').read()
        if '## 章节概览' not in txt:
            print(slug)
" | head -20
```

**处理**：用 W2 `add-event-timeline` 类似流程，从 kg/events + chapter_md 提取主角/主题，用 `edit_page.py` 追加节。每次一章。

**优先级**：P2；本纪/世家优先，表类最低。

### H18：Stub 页面扩展反思（或降级去 stub）

**现象**：`stub: true` 或 `quality_score < 0.2` 的页面长期未被扩展，占用命名空间但提供信息极少，需主动判断去向：**可扩展 → 扩充**，**确实无源 → 去掉 stub 标记并标注原因**。

**发现方法**：
```bash
# 找所有 stub 页面，按最后修改时间排序（最久未动的优先）
python3 -c "
import json, os
pages = json.load(open('wiki/public/pages.json'))['pages']
stubs = [(slug, meta) for slug, meta in pages.items()
         if meta.get('stub') or meta.get('quality_score', 1) < 0.2]
# 按修改时间升序（最旧优先）
stubs.sort(key=lambda x: os.path.getmtime(f'wiki/public/pages/{x[0]}.md'))
for slug, meta in stubs[:20]:
    print(f'{slug}  qs={meta.get(\"quality_score\",\"?\"):.2f}')
" 2>/dev/null
```

**判断流程**（每次处理 1 个 stub）：

```
1. 读页面内容
2. 在 entity_index / chapter_md / kg 中检索该实体：
   a. 找到有价值的引文或事件 → 执行 W2 enrich-infobox / embed-sku-excerpt → 扩充
   b. 找到 ≥ 3 处 PN 引用 → 执行 W2 add-event-timeline → 扩充
   c. 搜索无结果，或仅 1 处浅引用，且无法综合叙述：
      → "无扩展源"结论：移除 stub: true，加 note: "史记仅 N 处浅引，无独立条目价值"
      → 若页面内容 < 3 行且无 wikilink 指向它，考虑 H1 合并到上级页面
3. 记录到 actions.jsonl，result 为 expanded / demoted / merged
```

**去 stub 后的 frontmatter 处理**：
- 移除 `stub: true`
- 加 `stub_reviewed: "YYYY-MM-DD"` 字段（记录已审核，避免重复扫描）
- 若确实稀薄但保留，加 `note: "史记仅N处引用，暂无扩展源"`

**优先级**：P2；最久未动的 stub 优先；每 10 轮处理一批 5 个。

---

### H19：正文断言真实性核验 + PN 脚注附注

**现象**：wiki 页面正文中的叙述句（非引文）缺乏来源标注——读者无法验证"刘邦被封为汉王"这类断言出自《史记》哪一段。W7 核验已有引注的正确性，H19 的任务是**主动给无引注的断言找原文出处，并附上 PN 脚注**。

**发现方法**：
```bash
# 找有正文叙述但正文中 PN 引注密度低的页面
# 判据：正文句子数 / PN 引注数 > 5（即平均每5句才有一个PN）
python3 -c "
import glob, re
pn_re = re.compile(r'\(\d{3}-[\d.r]+\)')
sent_re = re.compile(r'[。！？]')
for f in sorted(glob.glob('wiki/public/pages/*.md')):
    txt = open(f).read()
    # 去掉 frontmatter 和引文节
    body = re.sub(r'^---.*?---\n', '', txt, flags=re.DOTALL)
    body = re.sub(r'## 史记引文.*', '', body, flags=re.DOTALL)
    sents = len(sent_re.findall(body))
    pns = len(pn_re.findall(body))
    if sents >= 5 and (pns == 0 or sents / max(pns,1) > 5):
        print(f'{f.split(\"/\")[-1][:-3]:30s} sents={sents:3d} pns={pns:2d}')
" | head -20
```

**核验与附注流程**（每次处理 1 个断言，最多 3 个/轮）：

```
1. 选目标页面（优先 person/overview，sents/pns 比值最高的）
2. 摘取正文中一个无引注的断言句（优先含人名/事件/地名的实质性陈述）
3. 用 find_pn_for_quote.py 在 chapter_md 中搜索最匹配的 PN：
   python3 wiki/scripts/butler/find_pn_for_quote.py "断言文本关键词" --top 3
4. 人工或 butler 确认 PN 对应原文确实支持该断言
5. 在断言句末追加行内 PN 引注：
   - 格式：`（见 [[070_张仪列传|张仪列传]] §39）` 或 `(070-39)`
   - 若有多处出处，取最直接的一处
6. 用 edit_page.py 写入
```

**行内引注两种格式**：
```markdown
# 简洁格式（适合密集叙述段）
张仪游说秦惠文王，主张连横破合纵(070-5)。

# 详细格式（适合精品页/重要断言）
张仪游说秦惠文王，主张连横破合纵（见 [[070_张仪列传|张仪列传]] §5）。
```

**不做的事**：
- ❌ 不改断言本身的文字（只加引注，不修改原句）
- ❌ 找不到匹配 PN 时不附注（宁缺毋错；记 `failures.jsonl`）
- ❌ 不为太史公曰等评论段附 PN（评论无"原文出处"）

**优先级**：P1（所有断言最终应有出处）；每轮处理 ≤ 3 句，diff ≤ 10 行。

---

## 三、触发时机

| 时机 | 行动 |
|---|---|
| **每 10 轮**一次 | ① `discover_duplicates.py` → H1 候选写入队列<br>② `find_unsourced.py --max 20 --write-queue` → H4 候选<br>③ W13 增量扫描（`--incremental`）→ H13 未覆盖段落 P2 条目<br>④ 处理队列里最老的一条 P0 任务 |
| **每轮末尾**（轻量）| 检查当轮新建页面是否触发 H3（aliases 是否有 REDIRECT） |
| **用户指出**（即时）| 将用户报告的问题直接加入 P0 |
| **trail 队列空时** | 按"零、全类型一览"顺序，依次触发各类扫描，补入队列，取 P0/P1 一条执行 |

---

## 四、H1 融合操作规范

**完整步骤（8步）详见 [`SKILL_W10a_Butler去重合并.md`](SKILL_W10a_Butler去重合并.md)**

**核心禁忌**：
- ❌ **禁止 `rm` 删除文件**——冗余页必须改为 REDIRECT（URL 有效 + 历史保留）
- ❌ **禁止批量替换链接**——每次只改一个文件（diff ≤ 20 行）
- ❌ **禁止合并内容差异 >50 行的页面**——需人工裁决
- ✅ **REDIRECT 页格式固定**，`type: redirect` + `redirect_to` 字段缺一不可

---

## 六、首次扫描（初始化 Housekeeping 队列）

首次运行时，执行以下扫描建立初始队列：

```bash
# 1. 重复标题扫描
python3 wiki/scripts/butler/reflection_scan.py --aspect dup > /tmp/dup_scan.txt

# 2. alias 冲突扫描
python3 wiki/scripts/butler/reflection_scan.py --aspect alias > /tmp/alias_scan.txt

# 3. 生成缺失 REDIRECT 列表
python3 -c "..." 2>/dev/null | head -50 > /tmp/missing_redirects.txt
```

将扫描结果分类后填入 `wiki/logs/butler/housekeeping_queue.md`。

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — 任务队列
- `wiki/scripts/butler/discover_duplicates.py` — **标题相似度扫描，每 10 轮运行**（含假阳性过滤）
- `wiki/scripts/butler/find_unsourced.py` — **溯源缺失扫描，每 10 轮运行**（调用 find_pn_for_quote 在原文中取 PN）
- `wiki/data/alias_conflicts.json` — 自动检测的 alias 冲突
- `wiki/scripts/butler/reflection_scan.py` — 扫描工具（--aspect dup/alias）
- `wiki/scripts/butler/record_revision.py` — 写入 revision（融合后必须调用）
- `skills/SKILL_W10a_Butler去重合并.md` — H1 详细操作规范
- `skills/SKILL_W13_史记全文覆盖查验.md` — **H13 专用 skill（W13）**
- `skills/SKILL_W5_Butler反思与自改.md` — 系统级反思（H14）
- `skills/SKILL_W7_引文真实性核验.md` — H11 引文核验
- `skills/SKILL_W8_精品页建设方法论.md` — H7 重要页增补
- `skills/SKILL_W9_Butler页面图式反思.md` — H10 页面错误反思
- `skills/SKILL_W12_语义查询与列表页.md` — H9 列表页建设
- `skills/SKILL_W11_概念分类元反思.md` — H10 概念分类审查
- `skills/SKILL_W14_洞察发现.md` — **H20 专用 skill（W14）**
- `wiki/logs/butler/insight_queue.md` — W14 洞察问题队列（H20 专用）
