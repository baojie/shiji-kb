# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

《史记》知识库：用AI Agent将《史记》130篇转化为结构化知识图谱。核心产出包括语义标注文本、18类实体索引（12,380词条）、3,185个事件索引、7,652条事件关系、事件地铁图可视化，以及11个可复用方法论SKILL文档。

## 项目约定

- 不要自动 commit。只在用户明确要求时才执行 git commit。
- 反思流程全自动。每章的 Agent 反思循环不需要用户逐步确认，直接执行完整流程。
- 对话和输出以中文为主。
- 年代标记三种格式：精确`（公元前XXX年）`、推算`[公元前XXX年]`、近似`[约公元前XXX年]`。
- 当用户在对话中明确要求自动确认时，后续操作不再逐步询问，自动执行。

## 常用命令

```bash
# 生成单章HTML
python render_shiji_html.py chapter_md/001_五帝本纪.tagged.md

# 批量生成全部130章HTML
python generate_all_chapters.py

# 发布到GitHub Pages（生成HTML + 修复路径 + lint检查）
./publish_to_docs.sh

# Markdown标注格式检查
python scripts/lint_markdown.py chapter_md/001_五帝本纪.tagged.md

# HTML输出格式检查
python scripts/lint_html.py docs/chapters/

# 事件年代审查管线（三步）
python kg/events/scripts/run_review_pipeline.py --prompt NNN      # 1. 生成提示词
# （Agent执行反思，输出JSON到/tmp/reflect_NNN.json）
python kg/events/scripts/run_review_pipeline.py --ingest NNN /tmp/reflect_NNN.json  # 2. 更新状态
python kg/events/scripts/apply_reflect_fixes.py NNN               # 3. 写入事件索引

# 事件年代lint检查
python kg/events/scripts/lint_ce_years.py

# 词频统计
python scripts/analyze_word_frequency.py
```

## 架构概览

### 数据流水线

```
原始文本 → chapter_md/*.tagged.md（语义标注Markdown）
         → render_shiji_html.py → docs/chapters/*.html（语法高亮HTML）
         → kg/（知识图谱：实体、事件、关系、纪年、家谱、词表）
         → ontology/skus/（标准知识单元）
         → app/metro/（事件地铁图）、app/game/（争霸游戏）
```

### 核心渲染器

`render_shiji_html.py` — 将标注Markdown转为带CSS语法高亮的HTML。`generate_all_chapters.py` 批量调用它处理130章。`publish_to_docs.sh` 是完整的发布流水线（生成 → 路径修复 → lint）。

### 知识图谱目录 `kg/`

按知识类型组织为子目录，每个子目录含 `data/` 和 `scripts/`：

| 子目录 | 内容 |
|--------|------|
| `events/` | 事件索引（`data/NNN_*_事件索引.md`）、事件关系、年代审查管线 |
| `entities/` | 实体索引（`entity_index.json`）、别名合并、语义消歧 |
| `chronology/` | 纪年映射（`reign_periods.json`、`year_ce_map.json`） |
| `genealogy/` | 帝王世系家谱 |
| `relations/` | 人物关系、因果关系 |
| `vocabularies/` | 18类实体分类词表 |
| `biology/` | 生物实体 |

### 实体标注符号（〖〗格式 v2.5）

18类实体使用不同CJK标点符号标记：`〖@人名〗` `〖=地名〗` `〖;官职〗` `〖%时间〗` `〖'邦国〗` `〖&氏族〗` `〖#身份〗` `〖$数量〗` `〖^制度〗` `〖~族群〗` `〖*器物〗` `〖!天文〗` `〚神话〛` `〖+生物〗` `《典籍》` `〈礼仪〉` `【刑法】` `〔思想〕`

### 段落编号（Purple Numbers）

圣经式编号：`[1.2.3]` 表示第1节第2小节第3段。章标题用 `[0]`。

### SKILL文档体系 `skills/`

分层编号的方法论文档（`SKILL_00` 到 `SKILL_09`），从实践中提炼的可复用古籍处理方法论。项目根目录的 `SKILL_*.md` 文件是面向外部的版本。

### 事件年代审查管线

Agent驱动的自动反思循环，对事件索引进行系统性年代校验。核心脚本在 `kg/events/scripts/`，状态和结果存储在 `kg/events/reports/`。详见 MEMORY.md 中的工作流说明。

## 关键格式约定

- 纪年标记用 `%元朔六年%` 格式
- 全角冒号`：`和半角冒号`:`在数据中混用，脚本需兼容两者
- 事件索引文件包含概览表和详情记录两部分
- 语义区块使用 `::: fenced div` 围栏块语法（太史公曰、赞、诗歌等）
