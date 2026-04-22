# 史记 Wiki 设计 Spec v1（Minimal，非语义）

**状态**：草稿（labs/planning）
**日期**：2026-04-22
**版本定位**：先做一个**普通 wiki**（每个实体/章节/主题一页，静态、只读、Markdown 源）；语义层（可查询、模板化推理）留给 v2。

---

## 0. 一句话目标

> 把 `kg/` 里所有值得一个页面的概念，都变成一个 `.md`，再一键生成成一个站点。

---

## 1. 设计原则

1. **MD 源 → HTML 产物**：源是 `.md` + YAML frontmatter；产物是纯静态 HTML。
2. **每个实体 = 一页**：Person / Place / State / Official / Event / Chapter / Topic 都有独立页面。
3. **构建期一次性展开**：生成脚本把 KG 数据**烧进 MD**，页面本身就是完整内容，不含运行时查询。
4. **双向链接靠 wikilink**：`[[刘邦]]` 或 `[[person/刘邦|刘邦]]`，构建期解析。
5. **无用户系统**：只读站，没有编辑器、登录、讨论页。
6. **KG 是单一事实源**：wiki 是派生物，KG 变了就重跑一遍构建。
7. **可迭代**：先跑通几十页 demo，再铺量；铺量之后再考虑加语义层。

---

## 2. 非目标（v1 不做）

- ❌ 在线编辑 / 登录 / 权限
- ❌ 运行时查询引擎
- ❌ 全文搜索（v2 可接 lunr/MiniSearch）
- ❌ 图可视化
- ❌ 多语言切换
- ❌ 评论 / 历史版本

---

## 3. 页面模型

### 3.1 源文件格式

```markdown
---
id: person/刘邦
type: person
label: 刘邦
aliases: [高祖, 沛公, 汉王, 季, 刘季]
tags: [汉朝, 开国君主]
kg_ref:
  source: entity_index
  key: 刘邦
---

# 刘邦

**别名**：高祖 · 沛公 · 汉王 · 季

## 基本属性

| 属性 | 值 |
| --- | --- |
| 生卒 | 前 256 ? — 前 195 |
| 朝代 | [[dynasty/汉|汉]]（开国） |
| 身份 | [[identity/天子|天子]] |
| 父 | [[person/刘太公|刘太公]] |

## 在史记中的记载

- [[chapter/008_高祖本纪|高祖本纪（第 8 篇）]] — 主传
- [[chapter/007_项羽本纪|项羽本纪]] — 第 12、15 段
- [[chapter/053_萧相国世家|萧相国世家]] — 第 3 段
- …（共 72 篇）

## 主要事件

- 前 209 · [[event/e2103|沛县起兵]]
- 前 206 · [[event/e2207|入关咸阳]]
- 前 206 · [[event/e2211|鸿门宴]]
- 前 202 · [[event/e2361|垓下之战]]
- 前 202 · [[event/e2365|即皇帝位]]

## 相关人物

**家族**：[[person/吕雉|吕雉]]（妻） · [[person/刘盈|刘盈]]（子） · [[person/刘肥|刘肥]]（长子，庶出）
**功臣**：[[person/萧何|萧何]] · [[person/张良|张良]] · [[person/韩信|韩信]] · …
**对手**：[[person/项羽|项羽]]

## 相关主题

- [[topic/司马迁史学思想|司马迁的史学思想]]

---

*本页主要属性区和列表区由构建脚本从 `kg/` 自动生成。*
```

**关键**：
- **不含**任何 `:::query` 或模板指令
- 每个区块的内容都是**具体的 MD**，构建脚本已经把 KG 数据展开好
- 作者可以手工在此基础上加**叙述性段落**（模板留 `<!-- 自由撰写 -->` 占位）

### 3.2 Frontmatter Schema（最小）

| 字段 | 必需 | 说明 |
| --- | --- | --- |
| `id` | ✓ | 全站唯一，`<type>/<slug>` |
| `type` | ✓ | `person` / `place` / `state` / `official` / `identity` / `dynasty` / `event` / `chapter` / `topic` / `meta` |
| `label` | ✓ | 页面标题 |
| `aliases` | | 别名数组 |
| `tags` | | 自由标签 |
| `kg_ref` | | 指向 KG 里的源 key（派生页用） |
| `stub` | | `true` 表示占位页，未人工审过 |

---

## 4. 目录结构

```
wiki/
├── templates/                   # Jinja2 模板（构建期用，不进入产物）
│   ├── person.md.j2
│   ├── place.md.j2
│   ├── state.md.j2
│   ├── event.md.j2
│   ├── chapter.md.j2
│   ├── topic.md.j2
│   └── default.md.j2
├── pages/                       # MD 源（构建产物 + 可手工覆写）
│   ├── person/
│   │   ├── 刘邦.md
│   │   └── ...
│   ├── place/
│   ├── state/
│   ├── event/
│   ├── chapter/
│   ├── topic/
│   └── index.md                 # 站点首页
├── authored/                    # 纯人工撰写的页面（高于 pages/ 优先级）
│   └── topic/
│       └── 司马迁史学思想.md
└── build/                       # 构建产物（gitignore）
```

- `pages/` 由生成脚本写入；可被 `authored/` 下同 id 页覆盖
- `authored/` 不被脚本覆盖，只合并进最终产物

---

## 5. 页面类型与首批范围

| type | 数据源 | 预计数量 | v1 demo |
| --- | --- | ---: | --- |
| `person` | `kg/entity_index.json` + `person_lifespans.json` + `person_xingshi.json` | ~5,400 | **5**：刘邦、项羽、司马迁、吕雉、韩信 |
| `state` | `feudal_state_wordlist.json` | 206 | **3**：汉、楚、齐 |
| `place` | `place_categories.json` | ~2,100 | **2**：长安、咸阳 |
| `official` | `official_categories.json` + `hanshu_baiguan.json` | ~1,500 | **1**：丞相 |
| `event` | `kg/events/data/*_事件索引.md` | 3,198 | **3**：鸿门宴、垓下之战、即皇帝位 |
| `chapter` | `chapter_md/*.tagged.md` + `structure/sections_data.json` | 130 | **3**：007、008、130 |
| `topic` | `kg/ontology/ontology-v2/**/skus/*.md` | ~2+ | **1**：司马迁史学思想（fact_001） |

**v1 总计约 18 页**；够跑通所有模板、wikilink、构建管线。

---

## 6. 模板（构建期用）

**位置**：`wiki/templates/*.md.j2`（Jinja2）

**职责**：根据一个 dict（归一化后的 KG 记录）渲染一页完整 MD。**页面不引用模板**，模板只在生成脚本里用。

**示例骨架** `person.md.j2`：

```jinja
---
id: person/{{ e.slug }}
type: person
label: {{ e.label }}
{% if e.aliases %}aliases: [{{ e.aliases | join(', ') }}]{% endif %}
{% if e.tags %}tags: [{{ e.tags | join(', ') }}]{% endif %}
kg_ref: { source: entity_index, key: "{{ e.key }}" }
---

# {{ e.label }}

{% if e.aliases %}**别名**：{{ e.aliases | join(' · ') }}{% endif %}

## 基本属性

| 属性 | 值 |
| --- | --- |
{% for k, v in e.facts %}| {{ k }} | {{ v }} |
{% endfor %}

## 在史记中的记载

{% for ch in e.chapters %}- [[chapter/{{ ch.id }}|{{ ch.title }}]]{% if ch.paragraphs %} — 第 {{ ch.paragraphs | join('、') }} 段{% endif %}
{% endfor %}

## 主要事件

{% for ev in e.events %}- {{ ev.year_ce }} · [[event/{{ ev.id }}|{{ ev.title }}]]
{% endfor %}

## 相关人物

{% if e.family %}**家族**：{% for f in e.family %}[[person/{{ f.slug }}|{{ f.label }}]]（{{ f.rel }}）{% if not loop.last %} · {% endif %}{% endfor %}{% endif %}

{% if e.cooperators %}**同事**：{% for c in e.cooperators %}[[person/{{ c.slug }}|{{ c.label }}]]{% if not loop.last %} · {% endif %}{% endfor %}{% endif %}

{% if e.opponents %}**对手**：{% for o in e.opponents %}[[person/{{ o.slug }}|{{ o.label }}]]{% if not loop.last %} · {% endif %}{% endfor %}{% endif %}

## 相关主题

{% for t in e.topics %}- [[topic/{{ t.slug }}|{{ t.label }}]]
{% endfor %}

<!-- 自由撰写区：生成脚本不覆盖本区 -->
{{ e.authored_body | default('') }}
```

**规则**：
- 字段缺失则整段跳过（模板里用 `{% if %}` 兜底）
- `authored_body` 从 `authored/` 下同 id 文件的正文读入，已有叙述就保留
- 模板可以在后续加/删段落而无需改页面源

---

## 7. 构建管线

```
kg/*.json + chapter_md/*.tagged.md + ontology-v2/skus/*.md
        │
        ▼  build_wiki_index.py
build/cache/{person,state,place,official,event,chapter,topic}.json
        │
        ▼  generate_pages.py
wiki/pages/{type}/*.md       ←── 合并 ──← wiki/authored/**/*.md
        │
        ▼  render_html.py
build/html/**/*.html
```

**脚本**（`scripts/wiki/`）：

| 脚本 | 输入 | 输出 | 职责 |
| --- | --- | --- | --- |
| `build_wiki_index.py` | `kg/**` | `build/cache/*.json` | 把 KG 里的异构数据归一化成每类一张表 |
| `generate_pages.py` | `build/cache/*.json` + `wiki/templates/*.j2` | `wiki/pages/**/*.md` | 按模板批量渲染页面源 |
| `merge_authored.py` | `wiki/authored/**/*.md` | 覆盖/合并到 `wiki/pages/` | 保留人工撰写段落 |
| `render_html.py` | `wiki/pages/**/*.md` | `build/html/**/*.html` | MD → HTML + wikilink 解析 |
| `build.sh` | — | — | 一键串起上面 4 步 |

**渲染器**：markdown-it-py（Python，支持 frontmatter 插件，扩展 wikilink 方便）。

---

## 8. 链接（Wikilink）

**语法**：

```markdown
[[person/刘邦]]            # id 链接，文本 = label
[[person/刘邦|汉高祖]]     # id 链接 + 自定义文本
[[刘邦]]                   # 标签链接，按 label + aliases 解析，歧义警告
```

**解析**：
- 构建期一次性扫描所有页面的 frontmatter 建 `label → id` 映射
- `aliases` 也进映射；冲突时整站告警并标记第一个匹配
- 未解析链接渲染为 `<span class="broken-wikilink">刘邦</span>`，构建日志列出

---

## 9. 页面模板需要的字段（每类一览）

给生成脚本作为归一化目标：

### person
- `key`, `slug`, `label`, `aliases`, `tags`
- `facts`：生卒、朝代、身份、父、母、配偶、子嗣、谥号、籍贯
- `chapters`：出现章节列表（含段落号）
- `events`：参与事件列表
- `family / cooperators / opponents`：关系列表

### state（邦国）
- `label`, `aliases`, `founding_year`, `end_year`, `capital`
- `rulers`：君主列表（时间序）
- `key_events`：关键事件
- `chapters`：相关章节

### event
- `label`, `year_ce`, `location`, `type`, `people`（参与者）
- `preceded_by` / `followed_by`（按事件关系 sequel/causal 取）
- `source_chapters`

### chapter
- `number`, `title`, `category`（本纪/世家/列传/表/书）
- `sections`：小节列表
- `people / places / events`：含出现次数
- `intro`：正文头段（从 tagged.md 取前 N 字）
- `full_text_link`：指向 `docs/chapters/NNN_xxx.html`

### topic
- 直接从 `ontology-v2/skus/*.md` 搬过来；frontmatter 改写，body 原样

---

## 10. v1 交付物

- [ ] `wiki/templates/{person,state,place,official,event,chapter,topic,default}.md.j2`（8 个）
- [ ] `scripts/wiki/{build_wiki_index,generate_pages,merge_authored,render_html}.py`
- [ ] `scripts/wiki/build.sh`
- [ ] 18 个 demo 页面按 §5 生成
- [ ] Wikilink 解析跑通，断链打印报告
- [ ] `build/html/index.html` 本地 `python -m http.server` 可访问，点击能跳
- [ ] `wiki/README.md`（< 150 行，说明如何跑 / 如何手写 authored 页）

**验收场景**（跑通即算 v1 成功）：
> 访问刘邦页 → 点"项羽"进项羽页 → 点"项羽本纪"进章节页 → 点"鸿门宴"进事件页 → 点"司马迁"进司马迁页 → 点"司马迁的史学思想"进主题页。

---

## 11. LLM 集成策略

### 三层介入模型（按强度从轻到重）

| Level | 时机 | LLM 职责 | 产物形态 | 何时做 |
| --- | --- | --- | --- | --- |
| **L1 构建期** | 生成 MD 时 | 为选定页写 body 叙述段 | 静态 `.md`，commit 到 git | **v1** |
| **L2 增量维护** | 周期性/数据变更触发 | 升级 stub、跨页校对、链接补全 | 更新后的 `.md` | v1.5 |
| **L3 运行时** | 用户访问时 | 现场生成整页或跨页问答 | LLM inference（非文件） | v3 |

**v1 只做 L1**，且只选一部分页（§5 里的 5-8 个 demo）。其余页 body 留空（stub 化）。产物仍是可审、可 diff、可引用的静态 `.md`——站点依然是"真 wiki"。

### L1 的脚本接口

`scripts/wiki/llm_authoring.py`，一次处理一页：

```
输入:
  - page_id              (如 person/刘邦)
  - kg_record            (build/cache/{type}.json 里的一行)
  - source_excerpts      (相关章节原文片段，按 chapters+段落号取)
  - sku_excerpts         (相关 SKU 节选，若有)
  - link_whitelist       (已存在的 page id 全集)

输出:
  - wiki/authored/<type>/<id>.md  (frontmatter 只保留 id + type)
  - 300-800 字 Markdown 叙述
  - 顶部插入元数据注释 (model/date/input_hash)
```

### L1 的硬约束（写进 system prompt）

1. **禁止编造**：只写 KG + 原文支持的内容；不确定处加"据《史记》载"/"疑"
2. **必须引用**：事实性断言带章节锚点，如"入关咸阳（[[chapter/008_高祖本纪|高祖本纪·§12]]）"
3. **wikilink 白名单**：只能链到 `link_whitelist` 里的 id；越界视为错误
4. **风格**：平白叙述，避免列表（列表由模板生成，防重复）；偏古雅但不仿古
5. **不写属性表**：表格由模板生成，LLM 只写叙事段

### 选谁做 L1？

| 页类型 | L1 优先级 | 原因 |
| --- | --- | --- |
| person（核心人物） | ⭐⭐⭐ | 最能体现 LLM 价值；KG 只有属性，叙述稀缺 |
| event（有叙事弧） | ⭐⭐⭐ | 鸿门宴这类需要叙事还原 |
| chapter | ⭐⭐ | 做导读，把 130 篇每篇写 400 字简介 |
| state | ⭐⭐ | 邦国兴衰需要综合 |
| topic | — | 直接用 ontology-v2 的 SKU，不重写 |
| place / official / 器物 | ⭐ | KG 信息稀薄，LLM 增益小，先跳过 |

### 版本化与重跑

每份 LLM 产出物顶部记录：

```markdown
<!-- llm-authored: model=claude-opus-4-7, date=2026-04-22, input_hash=abc123 -->
```

- `input_hash` = KG 记录 + 章节片段的哈希
- KG 变更后 hash 变 → 触发重跑
- 人工修订过的页在 frontmatter 加 `human_edited: true`，重跑时跳过

### 与 Karpathy LLM Wiki 的距离

Karpathy 的激进设想是 **L3**：wiki 内容不预存，访问即生成。这本质上把"wiki"变成了"LLM 查询系统"。我们 v1 不走这条路，原因：

- **可审性**：静态 `.md` 能 diff、能 review、能被学术引用；LLM inference 不能
- **成本**：每次访问都调 LLM 不现实，也没必要
- **一致性**：跨页事实对齐、人名消歧需要"看得到全站"，静态产物天然做到

v1 的 L1 = 让 LLM 当**作者**，不当**运行时**。以后想升 L3，L1 产出的 `.md` 就是最好的 few-shot 样本。

---

## 12. 向 v2（Semantic Wiki）的升级路径

v1 **故意**把 KG 数据烧进 MD，代价是：KG 一变就得全量重跑。

v2 引入语义层时，只需：
1. 在 `wiki/templates/*.j2` 里把表格/列表改成 `:::query kind="..."` 指令
2. 写 `expand_queries.py`，运行时（或构建时）解析
3. 页面源保持不变——作者看到的仍是 MD

所以 v1 的模板**就是 v2 的查询骨架**；现在把数据"预热"烧进去，以后变成查询。

---

## 13. 开放问题（v1 启动前需确认）

1. **chapter 页与 `docs/chapters/*.html` 关系**：v1 暂以 link-out 形式并存，不嵌入正文
2. **person 页 id 如何消歧**：倾向 `person/刘邦` + `person/刘邦_楚元王`；需和 `disambiguation_map.json` 对齐
3. **event id**：沿用 `kg/events/data/` 里现有的编号，还是重新分配？倾向沿用
4. **产物放哪里**：`docs/wiki/` 还是 `build/html/`？v1 倾向 `docs/wiki/`，顺便走现有发布脚本
5. **MD 渲染器**：markdown-it-py vs mistune；前者插件生态好，倾向 it

---

**下一步**：确认 §12 → 实现 `build_wiki_index.py` 的 person 部分 → 跑通刘邦单页 → 扩展到全部 18 个 demo 页 → 铺量。
