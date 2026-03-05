# Ontology

## Quick Start

1. **Read `spec.md`** — what to build
2. **Use `mapping.md`** — navigate SKUs by feature
3. **Check `eureka.md`** — creative ideas and cross-cutting insights

## Structure

```
ontology/
├── spec.md                      # App specification
├── mapping.md                   # SKU router — find the right knowledge
├── eureka.md                    # Creative insights and feature ideas
├── ontology_manifest.json       # Assembly metadata
├── chat_log.json                # Chatbot conversation log
└── skus/
    ├── factual/                 # Facts, definitions, data (header.md + content)
    ├── procedural/              # Skills and workflows (header.md + SKILL.md)
    ├── relational/              # Label tree + glossary
    ├── postprocessing/          # Bucketing, dedup, confidence reports
    └── skus_index.json          # Master index of all SKUs
```

## SKU Types

| Type | Description | Files |
|------|-------------|-------|
| **Factual** | Facts, definitions, data points, statistics | `header.md` + `content.md` or `content.json` + `entities.json` |
| **Procedural** | Workflows, skills, step-by-step processes | `header.md` + `SKILL.md` |
| **Relational** | Category hierarchy and glossary | `label_tree.json` + `glossary.json` |

## Stats

- **Factual SKUs**: 434
- **Procedural SKUs**: 241
- **Relational knowledge**: Yes
- **Total files copied**: 1359

## 知识索引

共 **434 项知识单元**（Factual SKUs），按 14 个主题分类，详见 [facts_index.md](facts_index.md)：

| 类别 | 数量 | 涵盖内容 |
|------|------|----------|
| 人物传记 | 192 | 刺客、名将、丞相、游侠、佞幸、滑稽、医家 |
| 诸侯国与世家 | 60 | 齐鲁晋楚吴越赵魏韩燕等世家 |
| 匈奴与边疆民族 | 28 | 匈奴单于世系、和亲、张骞出使、西域 |
| 夏商周三代 | 28 | 世系谱牒、制度沿革、牧野之战 |
| 汉朝政治与制度 | 26 | 吕后、文景之治、七国之乱、武帝 |
| 军事与战役 | 24 | 长平之战、漠北之战、治军风格 |
| 思想学术 | 21 | 儒道法墨、百家争鸣、孔子弟子 |
| 秦国与秦朝 | 20 | 统一六国、郡县制、焚书坑儒 |
| 楚汉争霸 | 11 | 陈胜吴广、刘邦项羽、垓下之战 |
| 五帝与上古传说 | 7 | 黄帝、尧舜禅让、大禹治水 |
| 经济与社会 | 6 | 货殖列传、盐铁专卖、平准均输 |
| 礼乐祭祀 | 5 | 封禅、祭祀制度 |
| 史记总论与司马迁 | 5 | 著述缘起、体例、太史公自序 |
| 天文历法与地理 | 1 | 律吕 |

## 实体标注

基于项目已有的 11 类命名实体识别（人名、地名、官职、时间、朝代、制度、族群、器物、天文、神话、动植物），对 Factual SKU 内容进行了实体匹配增补：

- **已标注**：394 / 434 个 SKU（90.8%）
- **总实体标注数**：7,497（平均每个 SKU 19.0 个实体）
- **输出文件**：每个 SKU 目录下的 `entities.json`
- **40 个未标注**：内容为纯英文，无中文实体名可匹配

每个 `entities.json` 包含按类型分组的实体列表、实体总数和 top 5 高频实体。`skus_index.json` 中同步更新了 `entity_count` 和 `top_entities` 字段。

## 关系知识

结构化的领域知识图谱，详见 [relational_index.md](relational_index.md)：

- **标签体系**：20 个顶层分类（人物、事件、地理、官职、制度、典故…），层层细分
- **术语表**：978 条术语定义（从"史记"到"凿空"，每条含标签与来源）
- **实体关系**：1,336 条三元组（is-a 360、causes 359、related-to 354…）

## 技能索引

共 **241 项技能**（Procedural SKUs），按 14 个主题分类，详见 [skills_index.md](skills_index.md)：

| 类别 | 数量 | 示例 |
|------|------|------|
| 军事战略与战术 | 54 | 背水阵、围城、反间计、远交近攻 |
| 治国理政 | 57 | 郡县制、约法三章、推恩令、变法 |
| 外交与谈判 | 24 | 合纵连横、和亲、鸿门宴脱身 |
| 继承与权力交接 | 21 | 禅让、夺嫡、摄政还政 |
| 人才选拔与管理 | 14 | 礼贤下士、唯才是举、毛遂自荐 |
| 危机应对与生存 | 14 | 功成身退、伴君如伴虎、被俘逃脱 |
| 个人修养与处世 | 11 | 徙木立信、奇货可居、以退为进 |
| 天文历法与占卜 | 10 | 观象授时、龟卜、周易 |
| 说服与劝谏 | 8 | 进谏、上书、以史劝退 |
| 匈奴与边疆 | 8 | 鸣镝、骑兵战术、部落治理 |
| 礼乐与文化 | 7 | 三分损益、封禅、礼乐修身 |
| 经济与商业 | 6 | 平准法、陶朱公商道、冯谖买义 |
| 法律与司法 | 4 | 五刑、商鞅变法、废除肉刑 |
| 医学 | 3 | 望闻问切、脉诊、六不治 |

## How to Use

1. Start with `spec.md` to understand what the app should do
2. Use `mapping.md` to find relevant SKUs for each feature
3. Read SKU `header.md` files for quick summaries before loading full content
4. Reference `eureka.md` for creative ideas that connect multiple knowledge areas
