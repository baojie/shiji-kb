# 史记通用词表(General Glossary)构建计划

## 一、项目概述

### 1.0 工序定位 ⚠️

**通用词表构建是实体消歧(03b)的先决工序**：

**正确的流程顺序**：
```
实体标注(03a) → 通用词表构建(02h) → 实体消歧(03b) → 专项词表深化
```

**为什么通用词表要先于消歧？**

1. **提供消歧依据**：
   - 通用词表汇总了每个实体的**所有出现位置和上下文**
   - 消歧工作需要这些上下文来判断"项羽"和"项籍"是否同一人
   - 例如：看到"项籍，字羽"就知道两者是同一人

2. **发现消歧候选**：
   - 通过统计分析，发现哪些名称可能是别名
   - 例如："丞相"和"相国"在相同语境出现频繁 → 可能是同义词
   - 例如："咸阳"出现在不同语境 → 可能是同名异地，需要消歧

3. **建立消歧基础数据**：
   - 通用词表 = 初步的实体索引（未消歧版本）
   - 消歧工作 = 在这个索引基础上，合并重复项、拆分歧义项

**工作流示例**：

**阶段1: 通用词表构建**（初稿，未消歧）
```json
[
  {"word": "项羽", "occurrences": 320, "contexts": [...]},
  {"word": "项籍", "occurrences": 85, "contexts": [...]},
  {"word": "西楚霸王", "occurrences": 45, "contexts": [...]}
]
```

**阶段2: 实体消歧**（分析上下文，判断关系）
```json
{
  "canonical": "项羽",
  "aliases": ["项籍", "西楚霸王"],
  "evidence": "项籍者，下相人也，字羽"
}
```

**阶段3: 词表更新**（应用消歧结果，合并条目）
```json
{
  "word": "项羽",
  "aliases": ["项籍", "西楚霸王"],
  "total_occurrences": 450,  // 320 + 85 + 45
  "contexts": [...]  // 合并后的所有上下文
}
```

### 1.1 目标

构建一个包含1万+条目的史记通用词表（初始版本，未消歧），覆盖史记全文中所有重要名词，为每个词条提供：

**第一阶段目标**（通用词表初稿）：
- **词条本身**：从标注文件提取的原始词形
- **出现位置**：所有出现的章节与段落
- **上下文汇总**：每次出现的前后文（±15字）
- **词条分类**：人名、地名、官职、事件、制度、器物等
- **初步释义**：基于上下文的AI生成释义

**第二阶段目标**（消歧后更新）：
- **规范化词形**：应用消歧结果后的canonical name
- **别名合并**：将同一实体的不同表述合并
- **上下文整合**：包含所有别名的出现
- **消歧说明**：标注哪些词条被合并、为什么

### 1.2 与其他词表的关系

```
通用词表(General Glossary)
├── 专项词表(Specialized Glossaries)
│   ├── 成语典故(Idioms) - 已完成 340条
│   ├── 官职词表(Official Titles) - 规划中
│   ├── 地名词表(Place Names) - 规划中
│   ├── 礼制术语(Ritual Terms) - 规划中
│   ├── 度量衡(Measurement Units) - 规划中
│   └── 族群词表(Ethnic Groups) - 规划中
└── 底层支撑
    └── 已标注实体(Tagged Entities) - 约X万条
```

**定位**：
- 通用词表是**全局索引**，覆盖面广但深度适中
- 专项词表是**深度挖掘**，针对特定领域提供详细释义和知识组织
- 通用词表为专项词表提供**候选词源**和**交叉索引**

### 1.3 学术价值

1. **Concordance功能**：提供古汉语用法索引，帮助理解同一词在不同语境下的用法
2. **知识图谱基础**：为后续本体构建和知识图谱建设提供术语基础
3. **辅助阅读**：支持悬浮释义、词条注释等认知辅助功能
4. **学术研究**：为史学、语言学、文献学研究提供结构化数据

## 二、数据来源

### 2.1 已标注实体（优先级最高）

从现有标注文件中提取：
```bash
# 统计已标注实体
grep -oP '〖[@=^%•{&\'~#+?;!$:\[\]_\\][^〗]+〗' chapter_md/*.tagged.md \
  | sed 's/〖[@=^%•{&'"'"'~#+?;!$:\[\]_\\]//' \
  | sed 's/〗//' \
  | sort | uniq -c | sort -rn
```

**实体类型映射**：
- `〖@人名〗` → 人名词条
- `〖=地名〗` → 地名词条
- `〖;官职〗` → 官职词条
- `〖%时间〗` → 时间词条
- `〖^事件〗` → 事件词条
- 其他类型...

**预估规模**：
- 人名：约5000-8000条
- 地名：约2000-3000条
- 官职：约500-1000条
- 其他：约2000-3000条
- **合计**：约1-1.5万条

### 2.2 候选词（待审核）

从词法分析（SKILL_02e）获取未标注但疑似重要名词的候选词：
- 名词性词组
- 高频专有名词
- 古汉语常用虚词

### 2.3 外部知识（辅助）

参考权威工具书：
- 《史记索隐》《史记正义》（三家注）
- 《汉语大词典》
- 《中国古代官职词典》
- 《史记辞典》

## 三、数据结构

### 3.1 JSON格式（第一阶段：未消歧版本）

```json
{
  "word": "项羽",                   // 从标注文件提取的原始词形
  "type": "person",
  "occurrences": [
    {
      "chapter_num": "007",
      "chapter_title": "项羽本纪",
      "paragraph": "15.2",
      "context_before": "汉王与诸侯兵共击",
      "matched_text": "项羽",
      "context_after": "，羽兵不利，走"
    },
    {
      "chapter_num": "008",
      "chapter_title": "高祖本纪",
      "paragraph": "25.3",
      "context_before": "与诸侯兵共击",
      "matched_text": "项羽",
      "context_after": "，羽军溃"
    }
    // ... 更多出现位置（只包含"项羽"这个词形）
  ],
  "total_occurrences": 320,        // "项羽"这个词形的出现次数
  "definition": {
    "brief": "秦末起义军领袖",
    "detailed": "项羽，秦末起义军领袖...",
    "sources": ["《史记·项羽本纪》"]
  },
  "related_entities": {
    "persons": ["刘邦", "范增"],    // 共现人物
    "events": ["007-015"],          // 相关事件
    "places": ["彭城", "垓下"]
  },
  "notes": null,
  "disambiguation_status": "pending"  // 待消歧
}
```

**注意**：此阶段，"项羽"、"项籍"、"西楚霸王"是**三个独立的词条**，尚未合并。

### 3.2 JSON格式（第二阶段：消歧后更新）

在实体消歧(03b)完成后，词表会被更新：

```json
{
  "word": "项羽",                   // 规范名（来自消歧）
  "canonical": "项羽",
  "entity_id": "person_xiangyu",    // 消歧后的唯一ID
  "type": "person",
  "aliases": ["项籍", "西楚霸王", "霸王"],  // 消歧识别的别名
  "disambiguation": "秦末起义军领袖，名籍，字羽",
  "occurrences": [
    {
      "chapter_num": "007",
      "chapter_title": "项羽本纪",
      "paragraph": "1.1",
      "matched_text": "项籍",        // 原文是"项籍"
      "context_before": "项籍者，下相人也，字",
      "context_after": "。初起时，年二十四"
    },
    {
      "chapter_num": "007",
      "chapter_title": "项羽本纪",
      "paragraph": "15.2",
      "matched_text": "项羽",        // 原文是"项羽"
      "context_before": "汉王与诸侯兵共击",
      "context_after": "，羽兵不利，走"
    },
    {
      "chapter_num": "007",
      "chapter_title": "项羽本纪",
      "paragraph": "58.1",
      "matched_text": "西楚霸王",    // 原文是"西楚霸王"
      "context_before": "项王自立为",
      "context_after": "，王九郡"
    }
    // ... 合并了所有别名的出现
  ],
  "total_occurrences": 456,         // 总计：320(项羽) + 85(项籍) + 45(西楚霸王) + 6(霸王)
  "occurrence_by_alias": {          // 各别名出现频次
    "项羽": 320,
    "项籍": 85,
    "西楚霸王": 45,
    "霸王": 6
  },
  "definition": {
    "brief": "秦末起义军领袖，西楚霸王",
    "detailed": "项羽（前232-前202），名籍，字羽，下相（今江苏宿迁）人...",
    "sources": ["《史记·项羽本纪》", "《汉书·项籍传》"]
  },
  "related_entities": {
    "persons": ["刘邦", "范增", "虞姬"],
    "events": ["007-015", "007-058"],
    "places": ["下相", "彭城", "垓下"]
  },
  "notes": "字羽，故称项羽；自立为西楚霸王，故称西楚霸王或霸王",
  "disambiguation_status": "completed",
  "merged_from": ["项籍", "西楚霸王", "霸王"]  // 记录被合并的词条
}
```

### 3.3 输出文件

```
data/glossary/
├── general_glossary.json         # 完整词表（1万+条）
├── glossary_by_type/
│   ├── persons.json              # 人名词表
│   ├── places.json               # 地名词表
│   ├── officials.json            # 官职词表
│   └── ...
├── glossary_stats.json           # 统计数据
└── glossary_index.html           # 可视化索引

docs/special/
└── glossary.html                 # Web版通用词表
```

## 四、构建流程（第一阶段：未消歧版本）

### 4.1 Phase 1: 实体提取（第1周）

**任务**：
1. 从所有 `*.tagged.md` 文件提取已标注实体
2. 按原始词形去重并统计频次
3. 记录每次出现的位置（章节、段落）

**脚本**：
```bash
python scripts/extract_all_entities.py \
  --input "chapter_md/*.tagged.md" \
  --output data/glossary/entities_raw.json
```

**输出**：
- `entities_raw.json`：原始实体数据（约1-1.5万条，未消歧）

**数据示例**：
```json
[
  {
    "word": "项羽",
    "type": "person",
    "occurrences": [
      {"chapter": "007", "paragraph": "15.2"},
      {"chapter": "008", "paragraph": "25.3"}
    ],
    "count": 320
  },
  {
    "word": "项籍",        // 此阶段是独立词条
    "type": "person",
    "occurrences": [
      {"chapter": "007", "paragraph": "1.1"}
    ],
    "count": 85
  },
  {
    "word": "西楚霸王",    // 也是独立词条
    "type": "person",
    "occurrences": [
      {"chapter": "007", "paragraph": "58.1"}
    ],
    "count": 45
  }
]
```

### 4.2 Phase 2: 上下文提取（第2周）

**任务**：
1. 对每个词条，提取所有出现位置的上下文（±15字）
2. 清理文本（移除标注符号、段落编号）
3. 为每个词条汇总其上下文

**脚本**：
```bash
python scripts/extract_contexts.py \
  --entities data/glossary/entities_raw.json \
  --chapters chapter_md/*.tagged.md \
  --output data/glossary/entities_with_contexts.json
```

**输出**：
- `entities_with_contexts.json`：带上下文的实体数据

**数据增强**：
```json
{
  "word": "项羽",
  "type": "person",
  "total_occurrences": 320,
  "contexts": [
    {
      "chapter_num": "007",
      "paragraph": "15.2",
      "context_before": "汉王与诸侯兵共击",
      "matched_text": "项羽",
      "context_after": "，羽兵不利，走"
    }
    // ... 320条上下文
  ],
  "disambiguation_status": "pending"
}
```

### 4.3 Phase 3: 释义生成（第3-4周）

**任务**：
1. 使用AI Agent批量生成释义初稿
2. 基于上下文和外部知识生成释义
3. 人工校对关键词条（高频词、重要人物/地名/官职）

**Agent提示词**：
```
以下是《史记》中的词条，请根据其所有出现的上下文，生成简明释义。

词条：丞相
类型：官职
出现次数：45次
上下文样例：
1. [008] 高祖本纪：高祖乃立【丞相】萧何为相国
2. [053] 萧相国世家：何为【丞相】，功第一
3. ...

输出格式：
- brief（20字以内）：秦汉最高行政长官，辅佐皇帝处理政务
- detailed（100-200字）：丞相为秦汉时期最高行政长官，位列三公之首...
- notes（可选）：秦称'丞相'，楚汉时期刘邦称'相国'，汉初复称'丞相'
```

**脚本**：
```bash
python scripts/generate_definitions.py \
  --input data/glossary/entities_with_contexts.json \
  --output data/glossary/general_glossary.json \
  --model qwen-plus  # 或其他LLM
```

### 4.4 Phase 4: 关联构建（第5周）

**任务**：
1. 建立词条间关联（人物-官职、人物-事件、事件-地点等）
2. 识别词条异体/别名
3. 构建交叉索引

**脚本**：
```bash
python scripts/build_relations.py \
  --glossary data/glossary/general_glossary.json \
  --entities data/entities/*.json \
  --events data/events/*.json \
  --output data/glossary/general_glossary.json  # 更新原文件
```

### 4.5 Phase 5: 可视化与发布（第6周）

**任务**：
1. 生成HTML索引页面
2. 实现搜索、筛选、排序功能
3. 集成到专项索引总页

**脚本**：
```bash
python scripts/render_glossary_html.py \
  --input data/glossary/general_glossary.json \
  --output docs/special/glossary.html
```

## 五、质量控制

### 5.1 数据完整性

- **覆盖率**：≥95% 已标注实体纳入词表
- **上下文提取**：100% 词条有至少1个上下文
- **释义覆盖**：≥90% 词条有释义（部分罕见词可标注"待考"）

### 5.2 释义准确性

**分层校对**：
1. **AI生成**：所有词条（1万+）
2. **人工抽检**：高频词（前1000条）+ 关键词条（官职、地名等）
3. **专家审核**：争议词条（约100条）

**校对标准**：
- 释义与上下文一致
- 引用权威工具书
- 标注争议性问题

### 5.3 数据一致性

- **章节编号**：三位数格式（001-130）
- **段落编号**：Purple Numbers格式（[N] 或 [N.M]）
- **实体类型**：与 `kg/entities/` 数据一致
- **JSON格式**：统一字段命名和数据类型

## 六、技术细节

### 6.1 文本清理算法

```python
def clean_text(text):
    """清理实体标注、标点、段落编号"""
    # 移除实体标注但保留内容：〖@人名〗 → 人名
    text = re.sub(r'〖[@=^%•{&\'~#+?;!$:\[\]_\\]([^〗]+)〗', r'\1', text)
    # 移除段落编号 [N] 或 [N.M]
    text = re.sub(r'\[\d+(?:\.\d+)?\]\s*', '', text)
    # 统一标点、引号
    text = re.sub(r'["""\'\'\'`]', '', text)
    return text.strip()
```

### 6.2 上下文窗口

- **窗口大小**：前后各15字（约一句话的长度）
- **边界处理**：不跨段落提取
- **特殊情况**：对话、引文内的实体，扩展到引号边界

### 6.3 消歧处理

- **同名消歧**：参考 `kg/entities/disambiguation/` 数据
- **多义词**：在释义中标注不同含义（如"中"可指官职"中官"或方位"中原"）

## 七、与专项词表的协同

### 7.1 数据流向

```
通用词表 --[筛选]--> 专项词表候选词
                         ↓
                     [深度标注]
                         ↓
                     专项词表
                         ↓
                  [反馈改进]
                         ↓
                     通用词表
```

### 7.2 优先级排序

根据Issue #89的需求，专项词表开发顺序：
1. **官职词表**（优先级最高，已有Issue #89）
2. **地名词表**（与历史地图联动，Issue #43）
3. **礼制术语**（学术价值高）
4. **度量衡**（需要现代换算）
5. **族群词表**（补充史记世界观）

### 7.3 交叉索引

- 通用词表中标注哪些词条已纳入专项词表
- 专项词表中链接回通用词表的完整上下文

## 八、里程碑与时间表

| 周次 | 任务 | 输出 |
|------|------|------|
| W1 | 实体提取 | `entities_raw.json` (1-1.5万条) |
| W2 | 上下文提取 | `entities_with_contexts.json` |
| W3-W4 | 释义生成（AI + 人工） | `general_glossary.json` |
| W5 | 关联构建 | 更新 `general_glossary.json` |
| W6 | 可视化与发布 | `docs/special/glossary.html` |

**总计**：6周（约1.5个月）

## 九、后续扩展

### 9.1 多语言版本

- 英文释义（International Scholars）
- 日文训读（Japanese Research）
- 拉丁化拼音（Wade-Giles Romanization）

### 9.2 动态更新

- 随着标注工作进展，自动更新词表
- 支持用户贡献释义改进
- 定期与权威工具书同步

### 9.3 知识图谱集成

- 导入Neo4j图数据库
- 支持SPARQL查询
- 构建本体(Ontology)

## 十、相关资源

### 10.1 参考SKILL

- [SKILL_02h_词表构建](../../skills/SKILL_02h_词表构建.md)
- [SKILL_02e_词法分析](../../skills/SKILL_02e_词法分析.md)
- [SKILL_03a_实体标注](../../skills/SKILL_03a_实体标注.md)

### 10.2 相关Issue

- #89 官制词典：辅助理解复杂官制体系
- #3 字典
- #44 辞典释义
- #37 实体索引升级为Concordance

### 10.3 工具书

- 《史记索隐》《史记正义》
- 《汉语大词典》
- 《中国古代官职词典》
- 《史记辞典》
- 谭其骧《中国历史地图集》

---

**计划编写时间**：2026-03-31
**预计启动时间**：待定
**负责人**：待定
**审核人**：待定
