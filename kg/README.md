# 史记知识图谱 (Knowledge Graph)

从《史记》130篇中提取的结构化知识，包括事件、实体、关系、家谱、纪年和词汇表。

## 目录结构

```
kg/
├── events/              # 历史事件
│   ├── data/            # 130篇事件索引 + 事件关系数据
│   │   ├── {NNN}_{章节名}_事件索引.md   # 各章事件（3185个）
│   │   ├── event_relations.json         # 事件关系（7637条，9种类型）
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
│       ├── build_metro_map_data.py      # 地铁图可视化数据
│       ├── agent_review_batch.sh        # 批量年代审查脚本
│       ├── batch_fix_collapsed_dates.py # 批量修复折叠日期
│       ├── cross_validate_dates.py      # 跨章节年代交叉验证
│       ├── extract_wars.py              # 提取战争事件
│       ├── fix_by_chronology.py         # 基于编年表修正年代
│       ├── fix_undated_known_events.py  # 修复已知事件的缺失年代
│       └── write_inferred_years.py      # 写入推断的年份
│
├── entities/            # 实体库
│   ├── data/
│   │   ├── entity_index.json            # 实体索引（人名/地名/官职等）
│   │   ├── entity_aliases.json          # 实体别名表
│   │   ├── disambiguation_map.json      # 歧义消解映射
│   │   ├── verb_index.json              # 动词索引（军事/刑罚/政治/经济）
│   │   ├── verb_taxonomy.md             # 动词分类体系
│   │   ├── biology/                     # 生物实体数据
│   │   └── ...                          # 其他实体数据文件
│   └── scripts/
│       ├── build_entity_index.py        # 构建实体索引
│       ├── disambiguate_names.py        # 人名消歧
│       ├── auto_detect_aliases.py       # 自动检测别名
│       ├── augment_sku_entities.py      # SKU实体增补
│       ├── build_verb_index.py          # 构建动词索引
│       ├── query_verbs_by_type.py       # 按类型查询动词
│       ├── validate_verb_tagging.py     # 验证动词标注
│       ├── auto_annotate_verbs.py       # 自动标注动词
│       └── migrate_verb_tags.py         # 迁移动词标注格式
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
│   ├── data/            # 人名/地名/官职/时间/朝代等词表（11个MD文件）
│   └── scripts/
│       └── build_vocabularies.py        # 从标注文本提取词表
│
├── quantity/            # 数量实体
│   └── data/
│       └── quantity_wordlist.json          # 数量词表（军队/距离/度量/金额）
│
├── structure/           # 文本结构
│   ├── data/
│   │   └── sections_data.json            # 130篇章节小节数据（约1500个小节）
│   └── README.md
│
├── taxonomy/            # 实体分类树
│   ├── data/
│   │   └── person_classified.json       # 人物分类中间数据
│   ├── person.ttl       # 人物分类本体（130类/1821实例）
│   ├── biology.ttl      # 生物分类本体（20类/70实例）
│   ├── person_taxonomy.md    # 人物分类树
│   ├── biology_taxonomy.md   # 生物分类树
│   └── scripts/
│       └── build_taxonomy.py            # 分类树生成器
│
├── ontology/            # 知识本体定义
│   ├── ontology-v1/     # SKU知识单元（675个）
│   ├── ontology-v2/     # 第二版本体设计
│   └── README.md
│
├── common-sense/        # 史记常识库
│   ├── README.md        # 常识规则（10大类，用于反常推理）
│   ├── INDEX.md         # 常识索引
│   └── extracted_knowledge_2026-03-26.md
│
├── facts/               # 知识事实库
│   ├── data/            # 结构化事实数据
│   ├── markdown/        # 事实Markdown文档
│   └── scripts/         # 事实提取脚本
│
├── rdf-hello-world/     # RDF/OWL入门示例
│   └── ...              # 示例本体文件
│
├── entity_index.json    # 实体索引（5MB，根目录）
├── disambiguation_map.json  # 歧义消解映射（根目录）
└── README.md
```

## 数据规模（2026-04-18）

| 知识类型 | 数量 |
|---------|------|
| **实体（名词 18 类）** | **15,120 条目 / 115,999 次标注** |
| **实体（动词 4 类）** | **211 条目 / 10,102 次标注** |
| **实体合计** | **15,331 条目 / 126,101 次标注**（22 类）|
| 事件 | 3,198 个（130 篇 × 平均 24.6 个）|
| 事件关系 | 7,652 条（自动 + LLM 推断）|
| 跨线换乘 | 2,111 条（并发 2,990 / 互见 320 / 共人 1,064 / 共地 737）|
| 公元纪年 | 3,051 个事件有标注（98.7% 覆盖，前 2700 年～前 87 年，经五轮反思修正约 2,100 处）|
| 事件类型 | 11 种（战争/继位/政治/改革/家族/建设/文化/经济/灾害等）|
| 关系类型 | 9 种（延续/因果/跨章因果/包含/对立/并发/互见/共人/共地）|
| 规律库 | 134 条（按章反思 SKILL_03c1）|

## 事件关系类型

| 类型 | 说明 | 来源 | 数量 |
|------|------|------|------|
| concurrent | 同年跨章事件共享人物 | 自动 | 2,990 |
| sequel | 时间延续，B是A的后续 | LLM | 1,624 |
| co_person | 跨章事件共享≥2人物 | 自动 | 1,064 |
| co_location | 跨章事件共享地点+人物 | 自动 | 737 |
| causal | A是B的直接原因 | LLM | 407 |
| cross_causal | 跨章节因果关系 | LLM | 338 |
| cross_ref | 不同章节记述同一事件 | 自动 | 320 |
| part_of | A是B的子事件 | LLM | 107 |
| opposition | 对立双方的行动 | LLM | 50 |

## 实体标注体系

### 名词实体（18 类，2026-04-18 实测）

文本中使用以下标注符号（v4.0，18 类 + 4 类动词）：

| 符号 | 类型 | 条目 | 出现 | 示例 |
|------|------|-----:|-----:|------|
| `〖@name〗` | 人名 | 5,362 | 36,393 | `〖@刘邦〗` |
| `〖◆state〗` | 邦国 | 206 | 16,897 | `〖◆汉〗`、`〖◆齐〗` |
| `〖;title〗` | 官职 | 1,533 | 11,283 | `〖;丞相〗` |
| `〖=place〗` | 地名 | 2,123 | 10,712 | `〖=长安〗` |
| `〖#role〗` | 身份 | 564 | 9,686 | `〖#天子〗` |
| `〖%time〗` | 时间 | 565 | 9,392 | `〖%三年〗` |
| `〖•artifact〗` | 器物 | 1,080 | 3,853 | `〖•宝鼎〗` |
| `〖^wumu〗` | 名物 | 707 | 3,283 | `〖^郡县〗`、`〖^封禅〗`（2026-04-13 由"制度"重命名）|
| `〖$qty〗` | 数量 | 817 | 3,201 | `〖$三万人〗` |
| `〖_concept〗` | 思想 | 307 | 2,710 | `〖_仁义〗` |
| `〖[legal〗` | 刑法 | 418 | 2,688 | `〖[腰斩〗` |
| `〖~group〗` | 族群 | 187 | 1,577 | `〖~匈奴〗` |
| `〖+bio〗` | 生物 | 455 | 1,476 | `〖+龙〗` |
| `〖&clan〗` | 氏族 | 261 | 1,125 | `〖&姬〗` |
| `〖!astro〗` | 天文 | 259 | 987 | `〖!岁星〗` |
| `〖{book〗` | 典籍 | 203 | 598 | `〖{春秋〗` |
| `〖?myth〗` | 神话 | 49 | 103 | `〖?鬼神〗`（D12 后大幅收敛）|
| `〖:ritual〗` | 礼仪 | 24 | 35 | `〖:宗庙〗` |
| **名词小计** | | **15,120** | **115,999** | — |

### 动词实体（4 类，v3.0 上线，v4.0 全量统计）

动词标注使用不同的外层符号 `⟦⟧`（数学双方括号 U+27E6/27E7）：

| 符号 | 类型 | 条目 | 出现 | 典型示例 |
|------|------|-----:|-----:|---------|
| `⟦◈verb⟧` | 军事动词 | 106 | 5,300 | `⟦◈伐⟧`、`⟦◈攻⟧`、`⟦◈击⟧` |
| `⟦◉verb⟧` | 刑罚动词 | 52 | 2,464 | `⟦◉杀⟧`、`⟦◉诛⟧`、`⟦◉斩⟧` |
| `⟦○verb⟧` | 政治动词 | 40 | 2,314 | `⟦○封⟧`、`⟦○立⟧`、`⟦○赐⟧` |
| `⟦◇verb⟧` | 经济动词 | 13 | 24 | `⟦◇贡⟧`、`⟦◇赋⟧`（试点）|
| **动词小计** | | **211** | **10,102** | — |

**支持消歧**：`⟦TYPE动词|消歧说明⟧`，如 `⟦◈败|击败⟧`

**铁律 A70**（最高优先级）：动词标注格式 `⟦⟧` 与名词标注格式 `〖〗` **严禁**互转；反思与修订过程中动词格式保持 100% 零违规。详见 [`skills/references/SKILL_03c1-rules.md`](../skills/references/SKILL_03c1-rules.md)。

**区分原则**：
- 刑罚动词（单字）：`⟦◉杀⟧` `⟦◉诛⟧`
- 刑罚制度（多字名词）：`〖[腰斩〗` `〖[夷三族〗`（保留原标注）

## 实体标注按章反思管线

实体标注经过**四轮** Agent 自动化按章反思审查：

| 轮次 | 修正数 | 有修正章数 | 新模式发现 | 主要修正类型 |
|------|-------:|-----------:|-----------:|-------------|
| 第一轮（2026-03-15） | ~1,913 | 127/130 | 40+ 条 | 官职→身份/时长去标注/制度→思想/制度→典籍/制度→刑法 |
| 第二轮（2026-03-17） | ~9,955 | 127/130 | 10 条 | 旧格式残留/身份类遗漏/刑法动词遗漏/人名省称遗漏/器物类遗漏 |
| 第三轮（2026-03-21～04-15） | ~890 | 72/130 | 23 条（含 A70）| 时长消歧 A8 批量 770+ / 动词格式保护 / 领域专项 D1-D11 |
| **第四轮（2026-04-16～04-18）** | **~8,684** | **~125/130** | **34 条** | B7 邦国+人名总则 / A110 主人公消歧无豁免 / E3 半角引号全库扫描 / D12-D15 领域扩展 |
| **合计** | **~21,442** | **130** | **107+ 条** | |

**规律库规模**：134 条（A 类型 116 + B 邦国氏族 7 + C 单字消歧 5 + D 领域专项 15 + E 格式残留 5），详见 [`skills/references/SKILL_03c1-rules.md`](../skills/references/SKILL_03c1-rules.md)。

第四轮汇总报告：[`doc/entities/第四轮反思汇总分析/`](../doc/entities/第四轮反思汇总分析/)。

**平均修正密度**: 98.1处/章

**关键规律**:
- 规律A70（第三轮新增）：严禁修改动词标注格式 `⟦◈⟧`/`⟦◉⟧` ↔ `〖[〗`
- 规律A8：时长消歧标注 `〖%X年|时长〗`（第三轮系统性修正）
- "上"字判断：传记中"上"100%指皇帝 → 身份类`〖#〗`

详见：[第一轮报告](../doc/entities/第一轮按章实体反思/第一轮按章实体反思报告.md) · [第二轮报告](../doc/entities/第二轮按章实体反思/第二轮按章实体反思报告.md) · [第三轮报告](../doc/entities/第三轮按章实体反思/第三轮反思总体完成报告_20260324.md) · [SKILL文档](../skills/SKILL_03c_按章反思.md)

## 年代反思审查管线

事件年代标注经过五轮Agent自动化反思审查：

| 轮次 | 修正数 | 有修正章数 | 新模式发现 | 主要修正类型 |
|------|--------|---------|---------|-----------|
| 第一轮 | 1,010 | 118/130 | 25条 | 系统性年份错误+确定性标注不足 |
| 第二轮 | 431 | 105/130 | 1条 | 确定性升级+精细调校 |
| 第三轮 | 465 | 70/130 | 0条 | 收敛验证+残留清理 |
| 第四轮 | 167 | 68/130 | 0条 | 终态验证+格式统一 |
| 第五轮 | 46 | 28/130 | 0条 | 跨章节交叉验证+确定性升级 |
| **合计** | **~2,119** | **130** | **26条** | |

详见：[第一轮总结](../doc/events/第一轮事件年代反思总结.md) · [第二轮总结](../doc/events/第二轮事件年代反思总结.md) · [第三轮总结](../doc/events/第三轮事件年代反思总结.md) · [第四轮总结](../doc/events/第四轮事件年代反思总结.md) · [第五轮总结](../doc/events/第五轮事件年代反思总结.md) · [SKILL文档](../skills/SKILL_04c_事件年代推断.md)

## 常用操作

```bash
# 事件
python kg/events/scripts/lint_ce_years.py              # 纪年质检
python kg/events/scripts/lint_ce_years.py 047           # 检查指定章节
python kg/events/scripts/build_metro_map_data.py        # 生成地铁图数据

# 实体索引（含事件索引页 + 动词关系页）
python kg/entities/scripts/build_entity_index.py        # 重建全部实体索引
# → 输出：docs/entities/*.html（20个HTML文件）
#   - 18类实体页面（person.html、place.html等）
#   - event.html（事件时间索引）
#   - relations.html、relations-military.html、relations-penalty.html（动词关系页）
#   - index.html（总览）
# → 输出：kg/entity_index.json（根目录，5MB）
# event.html 数据来源：kg/events/data/*_事件索引.md（130个文件）
# event.html 功能：按历史分期分组、事件编号显示、时间/类型/人物/地点标签、搜索筛选

python kg/entities/scripts/disambiguate_names.py        # 人名消歧

# 动词
python kg/entities/scripts/query_verbs_by_type.py --type all           # 统计动词频次
python kg/entities/scripts/query_verbs_by_type.py --chapter 040        # 分析040章动词
python kg/entities/scripts/validate_verb_tagging.py                    # 验证动词标注
python kg/entities/scripts/validate_verb_tagging.py --report verb_report.md  # 生成验证报告

# 词汇
python kg/vocabularies/scripts/build_vocabularies.py    # 生成词表
```

## 可视化

事件知识图谱以地铁路线图形式可视化，见 `app/metro/`：
- 130条线路 = 130篇章节
- 3,185个站点 = 3,185个事件
- 换乘连线 = 跨章事件关系
- 时间轴 = 公元前2700年 ~ 前87年
