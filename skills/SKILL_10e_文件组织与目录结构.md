# SKILL_10e_文件组织与目录结构

## 适用范围

本规范适用于古籍数字化知识库项目的文件组织与目录结构设计。

---

## 1. 核心原则

1. **职责分离**：区分"公开展示"与"内部工作"内容
2. **面向未来**：目录结构应具有可扩展性和通用性
3. **语义清晰**：目录命名准确反映其用途
4. **避免污染**：工作文档不应进入发布目录

---

## 2. 标准目录结构

### 2.1 一级目录分类

```
项目根目录/
├── data/              # 核心数据资产（结构化知识）
├── docs/              # 公开文档（GitHub Pages等）
├── doc/               # 工作文档（规范、说明、报告）
├── labs/              # 实验性工作（研究、原型、探索）
├── resources/         # 静态参考资料（出版物、演讲、草稿）
├── scripts/           # 自动化脚本与工具
├── logs/              # 运行日志与工作记录
├── archive/           # 历史存档（已废弃但保留）
└── skills/            # SKILL规范与方法论
```

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
└── notes/            # 笺注、校勘数据
```

**存放内容**：
- 结构化标注文件（`.ann`、`.jsonl`等）
- 原始古籍文本（`.txt`）
- 词表、人名库、地名库
- 知识图谱数据

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

### 2.4 `doc/` - 工作文档（内部使用）

**用途**：项目内部的技术规范、功能说明、开发文档、分析报告

**子目录示例**：
```
doc/
├── spec/             # 技术规范（SPEC/PLAN/GUIDE）
├── reports/          # 分析报告、工作总结
└── pronunciation/    # 多音字分析（工作文件）
```

**存放内容**：
- 技术规范文档（SPEC_*.md）
- 功能规划文档（PLAN_*.md）
- 操作指南（GUIDE_*.md）
- 分析报告（ANALYSIS_*.md、RENDER_*.md）
- 工作数据文件（DATA_*.json）

**与 `docs/` 的区别**：
- `docs/` = 面向外部用户的发布网站（HTML/CSS/JS）
- `doc/` = 面向项目内部的技术文档（Markdown/JSON）

---

### 2.5 `labs/` - 实验性工作

**用途**：研究、探索、原型开发、方案设计等**未定稿**的工作

**子目录示例**：
```
labs/
├── prototypes/       # 功能原型（HTML demo、UI试验等）
├── research/         # 研究记录（方案对比、文献调研等）
├── experiments/      # 实验性脚本与测试
└── planning/         # 规划文档（设计草稿、待决策方案）
```

**存放内容**：
- 功能原型（如三家注展示方式对比）
- 技术调研报告
- 待评审的设计方案
- 实验性算法或标注方案
- 性能测试、A/B测试

**典型场景**：
- "我在试验几种UI布局方案" → `labs/prototypes/`
- "对比三种拼音标注算法" → `labs/experiments/`
- "调研繁简转换工具" → `labs/research/`

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

**与其他目录的区别**：
- 与 `docs/` 的区别：`docs/` 是面向用户的在线文档（GitHub Pages），`resources/` 是离线资料和出版物
- 与 `labs/` 的区别：`labs/` 是实验性工作，`resources/draft/` 是准备发表的文章草稿
- 与 `logs/` 的区别：`logs/` 是工作记录，`resources/draft/` 是对外传播的内容

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

---

### 2.8 `logs/` - 运行日志与工作记录

**用途**：记录项目执行过程、工作进度、变更历史

**子目录示例**：
```
logs/
├── daily/            # 每日工作日志（YYYY-MM-DD.md）
├── reflection/       # Agent反思与审查报告
├── lint/             # 脚本运行日志与校验结果
├── curation/         # 文本整理记录
│   ├── curation_XXX_问题.md    # 单个问题记录
│   └── reports/                # 系统化校对报告
├── analysis/         # 数据分析报告
└── runs/             # 其他运行日志
```

**存放内容**：
- 每日工作日志（`YYYY-MM-DD.md`）
- Agent自动反思报告（实体边界检测、批量审查等）
- 脚本校验日志（文本完整性检查等）
- 人工文本整理记录（校勘、底本对照、文字修正）
  - 单个问题记录：`curation/curation_XXX_问题.md`
  - 系统化校对报告：`curation/reports/NNN_篇名_校对报告.md`
- 数据分析报告（统计分析、模式挖掘）

**参考文档**：
- 详细目录说明见 [`logs/README.md`](../logs/README.md)

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
├─ 是核心数据（标注、词表等）？
│  └─ 放入 data/
│
├─ 是面向外部用户的网站内容？
│  ├─ 已定稿、可公开 → docs/
│  └─ 草稿、待审阅 → labs/planning/
│
├─ 是内部技术文档（规范、报告）？
│  ├─ 技术规范 → doc/spec/
│  └─ 分析报告 → doc/reports/
│
├─ 是技术文章或对外传播内容？
│  ├─ 草稿阶段 → resources/draft/
│  ├─ 已发布 → resources/publications/
│  └─ 演讲材料 → resources/publications/talks/
│
├─ 是实验性工作？
│  ├─ 功能原型 → labs/prototypes/
│  ├─ 技术调研 → labs/research/
│  └─ 实验性脚本 → labs/experiments/
│
├─ 是可复用脚本？
│  └─ scripts/
│
├─ 是工作记录？
│  └─ logs/daily/
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

### ❌ 错误4：技术文章草稿放在 `labs/writing/`
- **错误**：`labs/writing/2026-04-03_史记知识库介绍.md`
- **纠正**：`resources/draft/2026-04-03_史记知识库介绍.md`
- **原因**：`labs/` 用于技术实验，`resources/draft/` 用于对外传播内容

### ❌ 错误5：内部技术文档放在 `docs/spec/`
- **错误**：`docs/spec/智能分段功能_说明.md`
- **纠正**：`doc/spec/智能分段功能_说明.md`
- **原因**：`docs/` 只放发布网站（HTML/CSS/JS），技术文档放 `doc/`

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
- `doc/` - 工作文档
- `resources/` - 静态参考资料（包括 draft/ 和 publications/）
- `scripts/` - 稳定脚本
- `skills/` - 规范文档
- `labs/` - 实验性工作（选择性）

### 6.2 可排除版本管理

- `logs/runs/` - 自动生成的运行日志
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
