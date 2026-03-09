# 史记知识图谱 (Knowledge Graph)

从《史记》130篇中提取的结构化知识，包括事件、实体、关系、家谱、纪年和词汇表。

## 目录结构

```
kg/
├── events/              # 历史事件
│   ├── data/            # 130篇事件索引 + 事件关系数据
│   │   ├── {NNN}_{章节名}_事件索引.md   # 各章事件（3092个）
│   │   ├── event_relations.json         # 事件关系（4385条，8种类型）
│   │   └── event_relations_summary.md   # 关系统计
│   └── scripts/
│       ├── extract_events.py            # 从标注文本提取事件
│       ├── extract_event_relations.py   # 自动+LLM推理事件关系
│       ├── annotate_ce_years.py         # 公元纪年标注
│       ├── lint_ce_years.py             # 纪年质检（时序/已知年份）
│       ├── run_review_pipeline.py       # 年代反思审查管线（--prompt/--ingest/--report）
│       ├── apply_reflect_fixes.py       # 将反思修正应用到事件索引
│       ├── generate_review_prompts.py   # 批量生成审查提示词
│       ├── validate_events.py           # 事件格式验证
│       ├── build_year_map.py            # 年份消歧与公元映射
│       └── build_metro_map_data.py      # 地铁图可视化数据
│
├── entities/            # 实体库
│   ├── data/
│   │   ├── entity_index.json            # 实体索引（人名/地名/官职等）
│   │   ├── entity_aliases.json          # 实体别名表
│   │   └── disambiguation_map.json      # 歧义消解映射
│   └── scripts/
│       ├── build_entity_index.py        # 构建实体索引
│       ├── disambiguate_names.py        # 人名消歧
│       ├── auto_detect_aliases.py       # 自动检测别名
│       └── augment_sku_entities.py      # SKU实体增补
│
├── chronology/          # 纪年数据
│   └── data/
│       ├── reign_periods.json           # 君主在位年（年表解析）
│       ├── year_ce_map.json             # 章节年份→公元映射
│       └── 史记编年表.md                 # 编年对照表
│
├── genealogy/           # 帝王家谱
│   ├── data/            # 各朝代世系图（五帝/夏/商/周/秦/汉）
│   └── scripts/
│       ├── extract_family_relations.py  # 家族关系提取
│       └── extract_imperial_genealogy.py # 帝王世系构建
│
├── relations/           # 人物关系网络
│   ├── data/            # 父子/母子/兄弟/君臣等关系
│   └── scripts/
│       └── extract_all_relations.py     # 全类型关系提取
│
├── vocabularies/        # 实体词汇表
│   ├── data/            # 人名/地名/官职/时间/朝代等词表
│   └── scripts/
│       └── build_vocabularies.py        # 从标注文本提取词表
│
├── flora_fauna/         # 动植物实体
│   ├── data/            # 标注指南与项目文档
│   └── scripts/
│       └── extract_flora_fauna.py       # 动植物实体提取
│
├── rdf/                 # RDF/本体数据
│   ├── ontology.ttl     # 史记知识本体定义
│   └── *.ttl            # RDF三元组数据
│
└── README.md
```

## 数据规模

| 知识类型 | 数量 |
|---------|------|
| 事件 | 3,092个（130篇×平均24个） |
| 事件关系 | 4,385条（自动2,198 + LLM 2,187） |
| 跨线换乘 | 1,876条（互见294/共人867/共地542/同期173） |
| 公元纪年 | 3,051个事件有标注（98.7%覆盖，前2700年～前87年，经两轮反思修正1,441处） |
| 事件类型 | 11种（战争/继位/政治/改革/家族/建设/文化/经济/灾害等） |
| 关系类型 | 8种（延续/因果/包含/对立/互见/共人/共地/同期） |

## 事件关系类型

| 类型 | 说明 | 来源 | 数量 |
|------|------|------|------|
| sequel | 时间延续，B是A的后续 | LLM | 1,623 |
| co_person | 跨章事件共享≥2人物 | 自动 | 969 |
| co_location | 跨章事件共享地点+人物 | 自动 | 705 |
| causal | A是B的直接原因 | LLM | 407 |
| cross_ref | 不同章节记述同一事件 | 自动 | 294 |
| concurrent | 同年跨章事件共享人物 | 自动 | 230 |
| part_of | A是B的子事件 | LLM | 107 |
| opposition | 对立双方的行动 | LLM | 50 |

## 实体标注体系

文本中使用以下标注符号：

| 符号 | 类型 | 示例 |
|------|------|------|
| `@name@` | 人名 | `@刘邦@` |
| `=place=` | 地名 | `=长安=` |
| `$title$` | 官职 | `$丞相$` |
| `%time%` | 时间 | `%三年%` |
| `&dynasty&` | 朝代 | `&汉&` |
| `~group~` | 族群 | `~匈奴~` |

## 年代反思审查管线

事件年代标注经过两轮Agent自动化反思审查：

| 轮次 | 修正数 | 有修正章数 | 新模式发现 | 主要修正类型 |
|------|--------|---------|---------|-----------|
| 第一轮 | 1,010 | 118/130 | 25条 | 系统性年份错误+确定性标注不足 |
| 第二轮 | 431 | 105/130 | 1条 | 确定性升级+精细调校 |
| **合计** | **1,441** | **130** | **26条** | |

详见：[第一轮总结](../doc/第一轮事件年代反思总结.md) · [第二轮总结](../doc/第二轮事件年代反思总结.md) · [SKILL文档](../SKILL_事件年代推断.md)

## 常用操作

```bash
# 事件
python kg/events/scripts/lint_ce_years.py              # 纪年质检
python kg/events/scripts/lint_ce_years.py 047           # 检查指定章节
python kg/events/scripts/build_metro_map_data.py        # 生成地铁图数据

# 实体索引（含事件索引页）
python kg/entities/scripts/build_entity_index.py        # 重建全部实体索引
# → 输出：docs/entities/*.html（11类实体 + event.html事件时间索引 + index.html总览）
# → 输出：kg/entities/data/entity_index.json
# event.html 数据来源：kg/events/data/*_事件索引.md（130个文件）
# event.html 功能：按历史分期分组、事件编号显示、时间/类型/人物/地点标签、搜索筛选

python kg/entities/scripts/disambiguate_names.py        # 人名消歧

# 词汇
python kg/vocabularies/scripts/build_vocabularies.py    # 生成词表
```

## 可视化

事件知识图谱以地铁路线图形式可视化，见 `app/metro/`：
- 130条线路 = 130篇章节
- 3,092个站点 = 3,092个事件
- 换乘连线 = 跨章事件关系
- 时间轴 = 公元前2700年 ~ 前87年
