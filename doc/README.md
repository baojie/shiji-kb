# doc/ - 项目文档总目录（ref/）

本目录是项目所有工作文档的总目录，概念上等同于 `ref/`（项目参考文档库）。

涵盖：技术规范、研究方法论、分析报告、Agent 反思记录、文本整理记录等一切有持久价值的文字记录。

## 目录结构

```
doc/
├── spec/              # 技术规范（SPEC/PLAN/GUIDE）
├── methodology/       # 研究方法论文档
├── workflow/          # 工作流程文档
├── analysis/          # 分析报告（Markdown，人类可读）
├── reports/           # 阶段性报告、成本报告
├── entities/          # 实体反思记录（多轮按章反思）
├── events/            # 事件反思记录
├── reflection/        # Agent 反思汇总
├── curation/          # 文本整理记录（校勘、底本对照）
│   └── reports/       # 系统化校对报告
├── incidents/         # 事故/问题记录
├── issues/            # 问题跟踪
├── predicate/         # 谓词/关系分析
└── pronunciation/     # 多音字分析
```

## 与其他目录的区别

| 目录 | 用途 |
|------|------|
| **doc/**（本目录）| 所有有持久价值的工作文档 |
| `docs/` | 面向外部用户的发布网站（HTML/CSS/JS，GitHub Pages）|
| `logs/` | 仅 IT 性日志（脚本输出、队列、运行记录）|
| `labs/` | 实验性工作（原型、调研、翻译实验）|
| `data/` | 结构化数据资产（标注候选 TSV、词表等）|

## 各子目录说明

### `spec/` - 技术规范

存放 `SPEC_*.md`、`PLAN_*.md`、`GUIDE_*.md`，是项目的技术决策和操作指导文件。

### `methodology/` - 研究方法论

存放研究方法总则、标注方法论、评估方法论等文档。

### `entities/` - 实体反思记录

存放多轮 Agent 按章实体反思报告（第一轮至第五轮），包括：
- 按章节的反思 JSON/MD
- 反思汇总分析
- 特殊任务记录

### `reflection/` - Agent 反思汇总

存放跨章节的 Agent 反思报告、实体边界检测与修复记录、批量审查总结等。

### `curation/` - 文本整理记录

存放人工发现的文本问题与修正记录：
- `curation_NNN_问题描述.md` - 单个问题记录
- `reports/` - 系统化校对报告

### `analysis/` - 分析报告

存放数据统计分析的 Markdown 报告（官职分析、覆盖率统计等）。

**⚠️ 注意**：TSV 数据文件（标注候选、补丁）已迁移至 `data/candidates/` 和 `data/patches/`。

### `reports/` - 阶段性报告

存放阶段性工作总结、成本报告等。

## 相关规范

- [SKILL_10e_文件组织与目录结构](../skills/SKILL_10e_文件组织与目录结构.md)
- [SKILL_10b_每日工作日志维护](../skills/SKILL_10b_每日工作日志维护.md)

---

最后更新：2026-05-14
