# SKILL_10e_文件组织与目录结构

## 适用范围

本规范适用于古籍数字化知识库项目的文件组织与目录结构设计。

---

## 1. 核心原则

1. **职责分离**：区分"公开展示"与"内部工作"内容
2. **面向未来**：目录结构应具有可扩展性和通用性
3. **语义清晰**：目录命名准确反映其用途
4. **避免污染**：工作文档不应进入发布目录
5. **logs/ IT-only**：`logs/` 只放机器生成的 IT 性日志（lint 输出、队列文件、运行记录），一切人类可读的工作文档（反思记录、分析报告、整理记录）均放 `doc/`（即 `ref/`）

---

## 2. 标准目录结构

### 2.1 一级目录分类

```
项目根目录/
├── data/              # 核心数据资产（结构化知识）
├── docs/              # 公开文档（GitHub Pages等）
├── doc/               # 项目文档总目录（等同 ref/，含反思、规范、报告）
├── labs/              # 实验性工作（研究、原型、探索）
├── resources/         # 静态参考资料（出版物、演讲、草稿）
├── scripts/           # 自动化脚本与工具
├── logs/              # 仅 IT 日志（lint/runs/queue，禁止放反思或分析）
├── archive/           # 历史存档（已废弃但保留）
└── skills/            # SKILL规范与方法论
```

> **`doc/` 与 `ref/` 的关系**：两者等价，`doc/` 是当前实际目录名，`ref/` 是概念称呼。本项目未来可能将 `doc/` 正式改名为 `ref/`，规范均适用。

---

### 2.2 `data/` - 核心数据资产

**用途**：存放结构化的知识数据、标注文件、词表等核心资产

**子目录示例**：
```
data/
├── annotations/       # 标注数据（人物、地名、时间等）
├── raw/              # 原始文本（OCR结果、底本扫描等）
├── processed/        # 处理后的数据
├── vocabularies/     # 词表、术语库
├── candidates/       # 标注候选数据（TSV，由脚本生成）
├── patches/          # 标注补丁（TSV，按章节存放）
└── notes/            # 笺注、校勘数据
```

**存放内容**：
- 结构化标注文件（`.ann`、`.jsonl`等）
- 原始古籍文本（`.txt`）
- 词表、人名库、地名库
- 知识图谱数据
- 标注候选与补丁 TSV（由脚本生成，供人工审核）

**不应存放**：
- 工作笔记、研究记录
- 实验性标注方案
- 临时处理文件

---

### 2.3 `docs/` - 公开文档（发布目录）

**用途**：面向外部用户的文档，会同步到GitHub Pages或其他公开站点

**子目录示例**：
```
docs/
├── index.html        # 主页
├── chapters/         # 章节HTML（已发布）
├── guide/            # 用户指南
├── css/              # 样式文件
├── js/               # 前端脚本
└── assets/           # 公开资源（图片、字体等）
```

**存放内容**：
- 用户手册、使用指南
- 项目介绍页面
- 前端展示界面（HTML/CSS/JS）
- 已定稿的技术文档

**严格禁止**：
- 工作日志、进度记录
- 实验性功能说明
- 内部讨论文档
- 草稿、待审阅内容

**判断标准**：问自己"这个文件可以公开给不了解项目的人看吗？"如果不能，则不应放在 `docs/`。

---

### 2.4 `doc/` - 项目文档总目录（ref/）

**用途**：项目内部的全部工作文档——规范、报告、反思记录、文本整理记录

**⚠️ 重要**：`doc/` 是项目文档的总目录（概念上称为 `ref/`），包含**所有有持久价值的文字记录**，不论是人工撰写还是 Agent 生成。

**子目录分类**：
```
doc/
├── spec/             # 技术规范（SPEC/PLAN/GUIDE）
├── methodology/      # 研究方法论文档
├── workflow/         # 工作流程文档
├── analysis/         # 分析报告（Markdown，人类可读）
│   ├── candidates/   # ← 禁止：TSV 数据文件应在 data/candidates/
│   └── patch/        # ← 禁止：TSV 补丁应在 data/patches/
├── reports/          # 阶段性报告、成本报告
├── entities/         # 实体反思记录（多轮按章反思）
├── events/           # 事件反思记录
├── reflection/       # Agent 反思汇总（从 logs/reflection/ 迁入）
├── curation/         # 文本整理记录（从 logs/curation/ 迁入）
│   ├── curation_NNN_*.md    # 单个问题记录
│   └── reports/             # 系统化校对报告
├── incidents/        # 事故/问题记录
└── issues/           # 问题跟踪
```

**存放内容**：
- 技术规范文档（SPEC_*.md）
- 功能规划文档（PLAN_*.md）
- 操作指南（GUIDE_*.md）
- 分析报告（ANALYSIS_*.md、RENDER_*.md）
- **Agent 反思记录**（实体反思、事件反思、边界分析等）
- 文本整理记录（校勘、底本对照）
- 阶段性工作总结

**不应存放**：
- 结构化数据文件（TSV、JSON）→ `data/`
- 实验性工作 → `labs/`
- IT 日志输出（lint、runs）→ `logs/`

**与 `docs/` 的区别**：
- `docs/` = 面向外部用户的发布网站（HTML/CSS/JS）
- `doc/` = 面向项目内部的全部工作文档（Markdown/JSON）

---

### 2.5 `labs/` - 实验性工作

**用途**：研究、探索、原型开发、方案设计等**未定稿**的工作

**子目录示例**：
```
labs/
├── prototypes/          # 功能原型（HTML demo、UI试验等）
├── research/            # 研究记录（方案对比、文献调研等）
├── experiments/         # 实验性脚本与测试
├── planning/            # 规划文档（设计草稿、待决策方案）
├── translation/         # 翻译实验（白话翻译、翻译质量研究）
├── lifespan/            # 生卒年推断实验数据
└── insight-inference/   # 基于 KG 的 insight 推理文章（样板、案例）
```

**存放内容**：
- 功能原型（如三家注展示方式对比）
- 技术调研报告
- 待评审的设计方案
- 实验性算法或标注方案
- 性能测试、A/B测试
- 翻译实验数据（`translation/`、`translation_v2/`）
- 生卒年推断数据（`lifespan/`）
- KG 驱动的 insight 推理文章（以原文+三家注+汉书为依据的深度论证）

**典型场景**：
- "我在试验几种UI布局方案" → `labs/prototypes/`
- "对比三种拼音标注算法" → `labs/experiments/`
- "调研繁简转换工具" → `labs/research/`
- "吕公为何嫁女给刘邦（基于 KG 的深度推理）" → `labs/insight-inference/`
- "白话翻译质量对比实验" → `labs/translation/`

**⛔ 禁止目录 `labs/writing/`**：
- 此目录**不存在**，也**不得新建**
- 对外传播文章草稿一律走 `resources/draft/`
- KG 驱动的 insight 推理文章走 `labs/insight-inference/`

**何时移出 `labs/`**：
- 原型确定采用 → 移至 `docs/` 或项目主代码
- 实验结论形成规范 → 编写为 `skills/SKILL_XX.md`
- 方案被否决 → 移至 `archive/`

---

### 2.6 `resources/` - 静态参考资料

**用途**：存放出版物、演讲、技术文章草稿、外部参考文献等静态资料

**子目录示例**：
```
resources/
├── draft/             # 技术文章草稿（未发布的文章）
├── publications/      # 已发布的出版物
│   ├── meta-skill-book/      # 元技能方法论手册
│   ├── pipeline-skills-book/ # 管线技能手册
│   ├── talks/                # 演讲材料（PPT/PDF）
│   └── 公众号文章/           # 公众号系列文章
├── references/        # 外部参考文献（论文、书籍）
├── community/         # 社区贡献内容
└── help/              # 写作指南、贡献指南
```

**存放内容**：
- **`draft/`**：技术文章草稿、博客文章、待发布的内容
- **`publications/`**：已发布的PDF手册、论文、演讲材料
- **`references/`**：外部参考文献、研究资料
- **`community/`**：社区贡献的内容、用户案例
- **`help/`**：项目贡献指南、写作风格指南

---

### 2.7 `scripts/` - 自动化脚本与工具

**用途**：数据处理、验证、转换等可执行脚本

**子目录示例**：
```
scripts/
├── validation/       # 校验脚本（完整性检查、格式验证）
├── conversion/       # 转换脚本（格式转换、数据迁移）
├── generation/       # 生成脚本（报告生成、统计分析）
└── utils/            # 通用工具函数
```

**存放内容**：
- Python/Shell脚本
- 数据处理工具
- 自动化测试脚本

**不应存放**：
- 一次性临时脚本（应放在 `labs/experiments/`）
- 未调试完成的脚本（应放在 `labs/`）

> **⚠️ 注意**：`logs/event_import/` 下的 `.py` 脚本（`add_pn_refs.py` 等）应迁移到 `scripts/` 下对应目录，队列 JSON 文件留在 `logs/event_import/`。

---

### 2.8 `logs/` - 仅 IT 日志

**用途**：存放机器自动生成的 IT 性日志（脚本输出、运行记录、队列状态）

**⚠️ 铁律**：`logs/` 只放 IT 性日志，任何人类可读的工作文档、反思记录、分析报告、整理记录均**不得放在 `logs/`**。

**子目录分类**：
```
logs/
├── daily/            # 每日工作日志（特例，工作流记录）
├── lint/             # 脚本运行日志与校验结果（IT）
├── runs/             # 自动化运行完成记录（IT）
└── event_import/     # 队列状态文件（仅 JSON，脚本迁到 scripts/）
```

**✅ 应放在 `logs/`（IT 性）**：
- 脚本校验输出（`lint/*.txt`）
- 自动化运行完成记录（`runs/*.md`）
- 队列状态文件（`event_import/queue*.json`）
- 每日工作日志（`daily/YYYY-MM-DD.md`，特例保留）

**❌ 不应放在 `logs/`，改放 `doc/`**：
- Agent 反思报告 → `doc/reflection/`
- 文本整理记录 → `doc/curation/`
- 分析报告（人类可读）→ `doc/analysis/`
- 成本报告 → `doc/reports/`
- 批量审查总结 → `doc/reflection/`

**参考文档**：详细目录说明见 [`logs/README.md`](../logs/README.md)

---

### 2.9 `archive/` - 历史存档

**用途**：已废弃但需保留的文件（供回溯参考）

**子目录示例**：
```
archive/
├── deprecated/       # 已废弃的脚本/数据格式
├── old-versions/     # 旧版本文件
└── experiments/      # 失败的实验（保留以避免重蹈覆辙）
```

---

### 2.10 `skills/` - SKILL规范与方法论

**用途**：项目执行规范、工作流程、最佳实践

**命名规范**：`SKILL_编号_简短描述.md`

**存放内容**：
- 工作流程规范
- 质量标准
- 技术约定
- 方法论总结

---

## 3. 文件创建决策树

当需要创建新文件时，按以下流程判断：

```
新文件是什么？
│
├─ 是核心数据（标注、词表、TSV候选/补丁等）？
│  └─ 放入 data/
│
├─ 是面向外部用户的网站内容？
│  ├─ 已定稿、可公开 → docs/
│  └─ 草稿、待审阅 → labs/planning/
│
├─ 是工作文档（规范/报告/反思/整理记录）？
│  ├─ 技术规范 → doc/spec/
│  ├─ 分析报告（Markdown）→ doc/analysis/
│  ├─ Agent 反思记录 → doc/entities/ 或 doc/reflection/
│  ├─ 文本整理记录 → doc/curation/
│  └─ 阶段性报告 → doc/reports/
│
├─ 是技术文章或对外传播内容？
│  ├─ 草稿阶段 → resources/draft/
│  ├─ 已发布 → resources/publications/
│  └─ 演讲材料 → resources/publications/talks/
│
├─ 是实验性工作？
│  ├─ 功能原型 → labs/prototypes/
│  ├─ 技术调研 → labs/research/
│  ├─ 实验性脚本 → labs/experiments/
│  ├─ 翻译实验 → labs/translation/
│  ├─ 生卒年推断 → labs/lifespan/
│  └─ KG 驱动的 insight 推理文章 → labs/insight-inference/
│
├─ 是可复用脚本？
│  └─ scripts/
│
├─ 是机器生成的 IT 日志（lint/run/queue）？
│  └─ logs/
│
├─ 是项目规范？
│  └─ skills/
│
└─ 已废弃但需保留？
   └─ archive/
```

---

## 4. 常见错误与纠正

### ❌ 错误1：工作笔记放在 `docs/`
- **错误**：`docs/三家注展示方式对比.md`
- **纠正**：`labs/research/三家注展示方式对比.md`

### ❌ 错误2：原型HTML放在 `docs/`
- **错误**：`docs/prototype_v1.html`
- **纠正**：`labs/prototypes/001_sanjia_sidebar.html`

### ❌ 错误3：临时脚本放在 `scripts/`
- **错误**：`scripts/test_pinyin.py`（一次性测试）
- **纠正**：`labs/experiments/test_pinyin.py`

### ❌ 错误4：任何文章放在 `labs/writing/`
- **错误**：`labs/writing/2026-04-03_史记知识库介绍.md`
- **纠正（对外传播文章）**：`resources/draft/2026-04-03_史记知识库介绍.md`
- **纠正（KG 驱动的 insight 推理）**：`labs/insight-inference/insight_reasoning_template_吕公嫁女.md`
- **原因**：`labs/writing/` **不存在也不得新建**

### ❌ 错误5：内部技术文档放在 `docs/spec/`
- **错误**：`docs/spec/智能分段功能_说明.md`
- **纠正**：`doc/spec/智能分段功能_说明.md`
- **原因**：`docs/` 只放发布网站（HTML/CSS/JS），技术文档放 `doc/`

### ❌ 错误6：Agent 反思记录放在 `logs/`
- **错误**：`logs/reflection/entity_boundary_reflection_2026-03-19.md`
- **纠正**：`doc/reflection/entity_boundary_reflection_2026-03-19.md`
- **原因**：反思记录是有持久价值的工作文档，属于 `doc/`；`logs/` 只放 IT 性日志

### ❌ 错误7：文本整理记录放在 `logs/`
- **错误**：`logs/curation/curation_016_项羽分封后表头.md`
- **纠正**：`doc/curation/curation_016_项羽分封后表头.md`
- **原因**：同上，人类可读的工作文档属于 `doc/`

### ❌ 错误8：标注候选 TSV 放在 `doc/`
- **错误**：`doc/analysis/candidates/007_candidates.tsv`
- **纠正**：`data/candidates/007_candidates.tsv`
- **原因**：TSV 数据文件是结构化数据资产，属于 `data/`

### ❌ 错误9：脚本放在 `logs/event_import/`
- **错误**：`logs/event_import/add_pn_refs.py`
- **纠正**：`scripts/import/add_pn_refs.py`（队列 JSON 保留在 `logs/event_import/`）
- **原因**：`logs/` 只放数据/日志文件，可执行脚本属于 `scripts/`

---

## 5. 特殊文件的位置

### 5.1 项目根目录文件

仅以下文件应位于根目录：

- `README.md` - 项目概述
- `CHANGELOG.md` - 变更记录
- `CLAUDE.md` - AI Agent工作指令
- `LICENSE` - 许可证
- `.gitignore` - Git忽略规则
- 配置文件（`package.json`、`pyproject.toml`等）

### 5.2 不应放在根目录的文件

- 工作笔记 → `logs/daily/`
- 设计文档 → `labs/planning/`
- 临时文件 → `labs/experiments/` 或 `.gitignore`

---

## 6. Git管理建议

### 6.1 应纳入版本管理

- `data/` - 核心数据资产
- `docs/` - 公开文档
- `doc/` - 工作文档（含反思记录）
- `resources/` - 静态参考资料（包括 draft/ 和 publications/）
- `scripts/` - 稳定脚本
- `skills/` - 规范文档
- `labs/` - 实验性工作（选择性）

### 6.2 可排除版本管理

- `logs/runs/` - 自动生成的运行日志
- `logs/lint/` - 机器生成的校验输出（可选）
- `archive/` - 历史存档（视情况而定）
- 临时文件、缓存文件

---

## 7. 版本演进策略

当项目发展到新阶段，目录结构应如何演进：

1. **新增数据类型** → 在 `data/` 下新增子目录
2. **新增功能模块** → 先在 `labs/` 试验，成熟后迁移
3. **新增规范** → 编写 `skills/SKILL_XX.md`
4. **废弃旧方案** → 移至 `archive/`，保留README说明废弃原因

---

## 8. 示例：新功能从构思到发布的文件流转

**阶段1：构思与设计**
```
labs/planning/
└── 智能段落划分功能设计.md
```

**阶段2：原型开发**
```
labs/prototypes/
└── smart_paragraph_demo.html
```

**阶段3：实验验证**
```
labs/experiments/
└── test_paragraph_rules.py
```

**阶段4：规范化**
```
skills/
└── SKILL_15_智能段落划分规范.md
```

**阶段5：正式发布**
```
docs/
└── features/
    └── smart-paragraph.html

scripts/
└── generation/
    └── generate_paragraphs.py

data/
└── paragraph_rules.json
```

---

## 附录：文档类型速查表

| 文档类型 | 放在哪里 | 理由 |
|---------|---------|------|
| 技术规范（SPEC/PLAN/GUIDE）| `doc/spec/` | 内部工作文档 |
| 分析报告（Markdown）| `doc/analysis/` | 内部工作文档 |
| Agent 反思记录 | `doc/entities/` 或 `doc/reflection/` | 有持久价值的工作文档 |
| 文本整理记录 | `doc/curation/` | 有持久价值的工作文档 |
| 标注候选 TSV | `data/candidates/` | 结构化数据资产 |
| 标注补丁 TSV | `data/patches/` | 结构化数据资产 |
| 翻译实验 | `labs/translation/` | 实验性工作 |
| 生卒年推断数据 | `labs/lifespan/` | 实验性工作 |
| lint 校验输出 | `logs/lint/` | IT 日志 |
| 队列状态 JSON | `logs/event_import/` | IT 日志 |
| 导入/处理脚本 | `scripts/` | 可复用工具 |
| 发布用前端 | `docs/` | 公开站点 |

---

## 附录：古籍数字化项目通用扩展建议

对于其他古籍数字化项目，可考虑增加：

```
corpus/            # 多文本语料库（如果项目包含多部古籍）
├── shiji/
├── hanshu/
└── ...

models/            # 机器学习模型（如NER模型、OCR模型）
├── ner/
├── ocr/
└── ...

benchmarks/        # 评测基准与测试集
├── ner_test/
├── ocr_test/
└── ...

ontology/          # 本体与知识图谱schema
└── shiji_ontology.ttl
```

根据项目具体需求选择性采用。
