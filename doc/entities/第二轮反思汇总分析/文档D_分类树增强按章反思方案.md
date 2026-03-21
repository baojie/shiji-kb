# 分类树增强按章反思方案 - 文档D

**生成日期**: 2026-03-21
**目标**: 将实体分类树（taxonomy）集成到按章反思流程，实现"标注↔分类"双向迭代优化

---

## 一、核心思想

### 1.1 问题背景

**现状观察**：
- **SKILL-03c-rules** 中积累了67条规律，其中大量包含**分类知识**
- **kg/taxonomy/** 已有完善的人物分类树（1,821人，130类）和生物分类树（70种，20类）
- **两者未打通**：反思时依靠文本规则，未利用结构化分类树；分类树静态维护，未从反思中动态更新

**核心矛盾**：
```
SKILL-03c-rules（67条规律）  ←X→  kg/taxonomy（分类树）
      ↓                                 ↓
  隐含分类知识                      结构化分类
  （规则形式）                      （OWL/RDF形式）
      ↓                                 ↓
   难以系统化                       未动态更新
```

### 1.2 核心insight

> **"规律中的分类知识可以转化为分类树节点，分类树可以反哺规律判断"**

**双向增强机制**：
1. **反思→分类树**：从反思规律中提取分类知识，更新taxonomy
2. **分类树→反思**：按章反思时读取分类树，辅助类型判断

---

## 二、现有分类知识分析

### 2.1 SKILL-03c-rules中的分类模式

从67条规律中提取出的**显性分类知识**：

#### **人物分类维度**（15+条规律涉及）

| 规律编号 | 分类维度 | 类别示例 | 标注符号 |
|---------|---------|---------|---------|
| A1 | 帝号/谥号/庙号 | 高帝、孝武皇帝、幽王、厉王 | `〖@〗` |
| A3 | 已故帝王追述 | 先帝、先王 | `〖#〗` |
| A4 | 侯号（作职衔） | 案道侯、武安侯 | `〖;〗` |
| A14 | 商代庙号 | 中宗（帝太戊）、高宗（武丁） | `〖@〗` |
| A20 | 在位帝王通称 | 今上、上、陛下、天子 | `〖#〗` |
| A21 | 集体性身份 | 群后、百官、百工、子弟、父老 | `〖#〗`/`〖;〗` |
| A23 | 群体称谓 | 群后、群臣、百吏、诸将 | `〖#〗`/`〖;〗` |
| A34 | 官职+人名 | 内史保、守陉 | 拆分标注 |
| A48 | 世家群体称谓 | 贤者、士卒、壮士、百姓 | `〖#〗` |
| A70 | 礼仪主题群体 | 诸生、群儒、博士弟子 | `〖#〗` |

#### **专题领域分类**（8+条规律涉及）

| 规律编号 | 领域 | 关键词示例 | 密度特征 |
|---------|------|-----------|---------|
| A11/A27/A51 | **刑法领域** | 诛、杀、灭、阬、弑、烹、醢 | 本纪50-70%，年表100%+ |
| A43-A45 | **哲学思想** | 道、德、仁、义、法、术、势 | 哲学列传10-35% |
| A19 | **礼仪祭祀** | 太牢、少牢、社稷、郊祀 | - |
| A71 | **医学术语** | 脉、诊、疾、病、经脉名称 | - |
| A33/A57 | **战争军事** | 刑法动词+器物词 | 军功传100%+ |

#### **语境判断模式**（10+条规律涉及）

| 规律编号 | 语境类型 | 判断依据 |
|---------|---------|---------|
| A16 | 祭祀语境 | "祀X"/"祭X" → 神灵/祖先 |
| A26 | 任命语境 | "以X为Y" → X人名，Y官职 |
| A29 | 封赏语境 | "封X为Y侯" → 侯号 |
| A32/A57 | 战争语境 | 刑法动词密集段落 |
| A68 | 奏疏语境 | 刑法密度25-30% |

---

### 2.2 现有kg/taxonomy结构

#### **人物分类树**（person.ttl，1,821人）

```
人物 [1,821人]
├── 王室 [289人]
│   ├── 帝王 [148人]
│   │   ├── 晋国 [37人]
│   │   ├── 周 [33人]
│   │   ├── 商 [31人]
│   │   ├── 楚国 [18人]
│   │   ├── 汉 [11人]
│   │   ├── 夏 [7人]
│   │   ├── 上古 [6人]
│   │   ├── 秦朝 [3人]
│   │   └── 秦末 [2人]
│   ├── 诸侯 [80人]
│   │   ├── 秦国 [24人]
│   │   ├── 齐国 [21人]
│   │   └── ...
│   ├── 公子 [18人]
│   ├── 公主 [11人]
│   └── 王族 [32人]
├── 文臣 [324人]
│   ├── 丞相 [62人]
│   ├── 太尉 [34人]
│   └── ...
├── 武将 [198人]
├── 谋士 [97人]
├── 外族 [86人]
└── ...
```

#### **生物分类树**（biology.ttl，70种）

```
生物 [70种]
├── 动物
│   ├── 家畜（马属、牛属、羊属...）
│   ├── 野兽（虎、鹿、熊...）
│   ├── 鸟类
│   ├── 鱼类水族
│   ├── 虫类
│   └── 神话动物（龙、凤皇、麒麟...）
├── 植物
│   ├── 穀物
│   ├── 树木
│   ├── 草本花卉
│   └── 果蔬
└── 生物集合（六畜、五穀、鸟兽...）
```

---

### 2.3 分类知识缺口分析

| 维度 | SKILL-03c-rules有 | kg/taxonomy缺 | 优先级 |
|------|-------------------|---------------|--------|
| **身份类群体** | A21/A23/A48/A70规律 | 缺"群后""诸生""士卒"等群体类型节点 | ⭐⭐⭐ |
| **官职细分** | A34官职+人名规律 | 缺官职层级树（丞相/太尉/九卿...） | ⭐⭐⭐ |
| **帝号系统** | A1/A14/A20规律 | 有帝王实例，缺帝号/谥号/庙号类型标注 | ⭐⭐ |
| **领域主题** | A11/A43/A71规律 | 缺领域标签（哲学家、医学家、军事家） | ⭐⭐ |
| **语境触发器** | A16/A26/A29规律 | 完全缺失（规律无法转RDF） | ⭐ |

---

## 三、分类树增强方案

### 3.1 设计目标

1. **分类树可读**：Agent在Step 0读取分类树，辅助类型判断
2. **分类树可写**：按章反思发现新类别时，追加到分类树
3. **双向验证**：标注结果与分类树互验，发现不一致
4. **渐进积累**：每章反思迭代分类树，避免一次性重构

---

### 3.2 文件结构设计

#### **目录结构**

```
kg/taxonomy/
├── README.md                       # 分类树总览
├── person.ttl                      # 人物分类本体（OWL/RDF）
├── person_taxonomy.md              # 人物分类树（可读视图，自动生成）
├── person_taxonomy.json            # 人物分类树（JSON格式，Agent友好）
├── biology.ttl                     # 生物分类本体
├── biology_taxonomy.md             # 生物分类树（可读视图）
├── data/
│   └── person_classified.json      # 已分类人物列表
├── scripts/
│   ├── ttl_to_markdown.py          # TTL → Markdown
│   ├── ttl_to_json.py              # TTL → JSON（新增）
│   └── update_taxonomy.py          # 更新分类树（新增）
└── SKILL-03c-taxonomy.md           # 分类树使用SKILL（新增）
```

#### **新增文件说明**

**person_taxonomy.json**（新增）：
```json
{
  "人物": {
    "children": {
      "王室": {
        "children": {
          "帝王": {
            "children": {
              "汉": {
                "members": [
                  {"name": "汉高祖", "count": 728, "aliases": ["高帝", "高祖"]},
                  {"name": "汉文帝", "count": 197, "aliases": ["孝文皇帝"]},
                  ...
                ]
              }
            }
          },
          "诸侯": {...},
          "群体": {
            "description": "群体性身份称谓",
            "members": [
              {"name": "群后", "type": "身份", "context": "诸侯集合"},
              {"name": "群臣", "type": "身份", "context": "臣子群体"},
              {"name": "诸生", "type": "身份", "context": "儒生群体"},
              ...
            ]
          }
        }
      },
      "文臣": {...},
      "武将": {...}
    }
  }
}
```

**SKILL-03c-taxonomy.md**（新增3级子SKILL）：
- 名称：`skills/references/SKILL-03c-taxonomy.md`
- 功能：指导Agent读取和更新分类树
- 内容：读取JSON格式分类树，提取特定类别节点

---

### 3.3 分类树增强优先级

#### **优先级1：人物群体类别（立即实施）**

**目标**：补充SKILL-03c-rules中A21/A23/A48/A70涉及的群体类别

**新增节点**：
```
人物
├── 王室
│   └── 群体
│       ├── 群后（诸侯集合）
│       ├── 诸侯（泛称）
│       └── 王族成员（公子、公孙）
├── 官员
│   └── 群体
│       ├── 群臣
│       ├── 百官
│       ├── 百吏
│       └── 九卿（集合称谓）
├── 儒生
│   └── 群体
│       ├── 诸生
│       ├── 群儒
│       ├── 博士弟子
│       └── 儒者
├── 民众
│   └── 群体
│       ├── 百姓
│       ├── 父老
│       ├── 子弟
│       └── 黎民
└── 军事
    └── 群体
        ├── 士卒
        ├── 壮士
        ├── 诸将
        └── 将军（集合）
```

**实施步骤**：
1. 从SKILL-03c-rules提取群体称谓词表（~40个）
2. 按王室/官员/儒生/民众/军事分类
3. 为每个群体添加元数据：type（身份/官职）、context（使用场景）
4. 更新person.ttl和person_taxonomy.json
5. 测试：选1-2章验证分类树是否能辅助判断

**预期效果**：
- 减少A21/A23/A48/A70规律查找时间（从文本规则→树形查询）
- 新章节发现新群体时，可直接追加到分类树

---

#### **优先级2：帝号/官职系统（后续迭代）**

**目标**：为已有人物添加帝号/谥号/庙号/官职元数据

**增强方式**（不新增节点，丰富现有节点）：
```json
{
  "name": "汉高祖",
  "count": 728,
  "aliases": ["高帝", "高祖", "刘邦"],
  "titles": {
    "帝号": ["高帝"],
    "庙号": ["高祖"],
    "谥号": null
  },
  "positions": ["沛公", "汉王", "皇帝"]
}
```

**实施步骤**：
1. 从kg/entities/data提取人物别名数据
2. 利用A1规律识别帝号/谥号/庙号模式
3. 批量为帝王类人物添加titles字段
4. 为文臣/武将添加positions字段

---

#### **优先级3：领域标签（长期规划）**

**目标**：为人物添加领域标签（哲学家、医学家、军事家...）

**标签体系**：
```
领域标签（可多选）
├── 哲学家（老子、韩非、孟轲...）
├── 医学家（扁鹊、仓公...）
├── 军事家（孙武、吴起...）
├── 外交家（苏秦、张仪...）
├── 文学家（屈原、贾生...）
└── 工程师（奚仲、匠人...）
```

**实施方式**：
- 不新增树节点，为person.ttl添加`领域`属性
- 从章节主题推断（哲学列传→哲学家）
- 支持多标签（张仪：谋士+外交家）

---

## 四、SKILL_03c集成方案

### 4.1 Step 0增强：读取分类树

**现有Step 0**（SKILL_03c_按章反思.md）：
```markdown
## Step 0：预备（必须先执行）

1. **读取规律库**：读取 `skills/references/SKILL-03c-rules.md` 全文
2. 运行格式检查：python scripts/lint_markdown.py ...
3. 运行边界损坏检测：grep -n '〖@[^〗]*[，。、；：]' ...
4. 运行单字名推断：python scripts/infer_single_char_names.py ...
```

**增强后Step 0**：
```markdown
## Step 0：预备（必须先执行）

1. **读取规律库**：读取 `skills/references/SKILL-03c-rules.md` 全文
2. **读取分类树**（新增）：读取 `kg/taxonomy/person_taxonomy.json`
   - 重点读取：`王室.群体`、`官员.群体`、`儒生.群体`、`民众.群体`、`军事.群体`
   - 用途：辅助判断群体称谓类型（身份〖#〗还是官职〖;〗）
   - 示例：遇到"群后"→查分类树→确认为"王室.群体.群后"→标注〖#〗
3. 运行格式检查：python scripts/lint_markdown.py ...
4. 运行边界损坏检测：grep -n '〖@[^〗]*[，。、；：]' ...
5. 运行单字名推断：python scripts/infer_single_char_names.py ...
```

**读取分类树示例**：
```python
# Agent内部执行（概念示意）
import json

# 读取分类树
with open('kg/taxonomy/person_taxonomy.json') as f:
    taxonomy = json.load(f)

# 提取群体称谓词表
groups = {
    "王室群体": taxonomy["人物"]["children"]["王室"]["children"]["群体"]["members"],
    "官员群体": taxonomy["人物"]["children"]["官员"]["children"]["群体"]["members"],
    "儒生群体": taxonomy["人物"]["children"]["儒生"]["children"]["群体"]["members"],
    # ...
}

# 快速查询
def is_group_identity(word):
    for category, members in groups.items():
        for member in members:
            if member["name"] == word:
                return member["type"] == "身份"  # 返回True表示〖#〗
    return None
```

---

### 4.2 Step 2增强：分类树辅助判断

**增强逐段审查**：

```markdown
## Step 2: 逐段审查（类型驱动）

### 2.1 群体称谓快速检查（新增）

**触发条件**：遇到以下模式
- "群X"（群后、群臣、群儒...）
- "百X"（百官、百吏、百姓...）
- "诸X"（诸生、诸将、诸侯...）
- "众X"（众人、众臣...）

**检查流程**：
1. 提取词汇X
2. 在分类树中查找`X`
3. 根据分类树返回的`type`字段判断：
   - `type: "身份"` → 标注〖#〗
   - `type: "官职"` → 标注〖;〗
   - `type: null` → 参考context字段+语境判断
4. 如分类树中不存在，记录为**待补充**

**示例**：
- 遇到"诸生" → 查分类树 → 找到`儒生.群体.诸生`（type: 身份）→ 标注〖#诸生〗
- 遇到"群后" → 查分类树 → 找到`王室.群体.群后`（type: 身份）→ 标注〖#群后〗
- 遇到"百工" → 查分类树 → 找到两处（官员.群体 和 民众.群体）→ 根据语境判断
```

---

### 4.3 完成后操作：更新分类树

**现有完成后操作**（SKILL_03c_按章反思.md）：
```markdown
## 完成后操作

1. **写回原文件**：保存修正
2. **文本完整性检查**：python scripts/lint_text_integrity.py ...
3. **写反思报告**：追加到 doc/entities/第二轮按章实体反思报告.md
4. **写回SKILL规律库**：新规律写入 skills/references/SKILL-03c-rules.md
```

**增强后完成后操作**：
```markdown
## 完成后操作

1. **写回原文件**：保存修正
2. **文本完整性检查**：python scripts/lint_text_integrity.py ...
3. **写反思报告**：追加到 doc/entities/第二轮按章实体反思报告.md
4. **写回SKILL规律库**：新规律写入 skills/references/SKILL-03c-rules.md
5. **更新分类树**（新增）：
   - **条件**：反思中发现**未在分类树中**的新群体称谓/类别
   - **格式**：
     ```json
     {
       "category": "官员.群体",
       "new_member": {
         "name": "诸卿",
         "type": "官职",
         "context": "九卿及高级官员的集合称谓",
         "source": "062章第二轮反思",
         "examples": ["诸卿皆曰善", "与诸卿议"]
       }
     }
     ```
   - **写入位置**：`kg/taxonomy/data/taxonomy_updates.jsonl`（追加模式）
   - **后处理**：运行 `python kg/taxonomy/scripts/update_taxonomy.py` 合并到person_taxonomy.json
```

---

## 五、实施路线图

### 5.1 第一阶段：基础设施（1-2天）

**目标**：建立分类树读写基础设施

**任务清单**：
- [ ] 创建 `kg/taxonomy/scripts/ttl_to_json.py`
  - 输入：person.ttl
  - 输出：person_taxonomy.json（Agent友好格式）
- [ ] 创建 `kg/taxonomy/data/taxonomy_updates.jsonl`
  - 格式：每行一个JSON对象（新增类别/成员）
- [ ] 创建 `kg/taxonomy/scripts/update_taxonomy.py`
  - 功能：读取taxonomy_updates.jsonl，合并到person_taxonomy.json
- [ ] 创建 `skills/references/SKILL-03c-taxonomy.md`（3级子SKILL）
  - 指导Agent如何读取person_taxonomy.json
  - 提供查询示例代码

**交付物**：
- person_taxonomy.json（从person.ttl生成）
- update_taxonomy.py脚本
- SKILL-03c-taxonomy.md

---

### 5.2 第二阶段：人物群体补充（2-3天）

**目标**：补充优先级1的群体类别节点

**任务清单**：
- [ ] 从SKILL-03c-rules提取群体称谓（~40个）
  - 涉及规律：A21, A23, A48, A70
  - 输出：`kg/taxonomy/data/group_terms_seed.json`
- [ ] 按王室/官员/儒生/民众/军事分类
  - 为每个词添加type（身份/官职）和context
- [ ] 更新person.ttl（添加5个群体子类）
- [ ] 重新生成person_taxonomy.json
- [ ] 测试：选择006章（秦始皇本纪）或062章（哲学列传）验证

**交付物**：
- 更新后的person.ttl（+5个群体类，~40个成员）
- 更新后的person_taxonomy.json
- 测试报告（006或062章）

---

### 5.3 第三阶段：SKILL集成（2-3天）

**目标**：将分类树集成到SKILL_03c

**任务清单**：
- [ ] 更新SKILL_03c_按章反思.md
  - Step 0新增"读取分类树"步骤
  - Step 2新增"群体称谓快速检查"流程
  - 完成后操作新增"更新分类树"步骤
- [ ] 更新SKILL-03c-rules.md
  - A21/A23/A48/A70规律增加"参考分类树"提示
  - 添加分类树查询示例
- [ ] 创建反思模板（增强版）
  - 包含分类树查询步骤
  - 包含分类树更新记录

**交付物**：
- 更新后的SKILL_03c_按章反思.md（v3.0）
- 更新后的SKILL-03c-rules.md
- 反思报告模板（增强版）

---

### 5.4 第四阶段：试点验证（3-5天）

**目标**：选择3-5章进行试点，验证分类树增强效果

**试点章节选择**：
- **062章（老子韩非列传）**：哲学列传，群体称谓密集（诸生、群儒）
- **034章（燕召公世家）**：世家，群体称谓密集（A48规律来源）
- **103章（万石张叔列传）**：高频"上"字判断（A66规律）
- **014章（十二诸侯年表）**：年表体裁，"公"字密集（A27规律）
- **008章（高祖本纪）**：刑法/群体词密集，综合测试

**验证指标**：
1. **准确率提升**：分类树辅助判断后，群体称谓误标率下降
2. **效率提升**：Agent查询分类树时间 vs. 规则文本扫描时间
3. **覆盖率**：试点中发现的新群体词，分类树覆盖占比
4. **可维护性**：分类树更新流程是否顺畅

**交付物**：
- 5章试点反思报告
- 分类树更新记录（taxonomy_updates.jsonl）
- 效果评估报告

---

### 5.5 第五阶段：全量推广（持续迭代）

**目标**：在第三轮按章反思中全面应用分类树

**推广策略**：
1. **第三轮反思启动**时，所有章节都使用SKILL_03c v3.0（含分类树）
2. **逐章迭代分类树**：每章反思后更新taxonomy_updates.jsonl
3. **批量合并**：每完成10章，运行update_taxonomy.py合并一次
4. **定期审查**：每完成30章，审查分类树质量和覆盖率

**预期成果**：
- 130章反思完成后，分类树覆盖所有常见群体称谓（~100个）
- SKILL-03c-rules规律数从67条收敛到~50条（分类知识迁移到taxonomy）
- 实现"标注↔分类"双向迭代的完整闭环

---

## 六、技术实现细节

### 6.1 person_taxonomy.json结构设计

```json
{
  "meta": {
    "version": "2.0",
    "updated": "2026-03-21",
    "source": "person.ttl",
    "total_classes": 135,
    "total_persons": 1821,
    "new_in_v2": ["王室.群体", "官员.群体", "儒生.群体", "民众.群体", "军事.群体"]
  },
  "tree": {
    "人物": {
      "label": {"zh": "人物", "en": "Person"},
      "count": 1821,
      "children": {
        "王室": {
          "label": {"zh": "王室", "en": "Royal Family"},
          "count": 289,
          "children": {
            "帝王": {
              "label": {"zh": "帝王", "en": "Emperor/King"},
              "count": 148,
              "children": {
                "汉": {
                  "label": {"zh": "汉", "en": "Han Dynasty"},
                  "count": 11,
                  "members": [
                    {
                      "name": "汉高祖",
                      "count": 728,
                      "aliases": ["高帝", "高祖", "刘邦"],
                      "titles": {"帝号": ["高帝"], "庙号": ["高祖"]}
                    },
                    ...
                  ]
                }
              }
            },
            "群体": {
              "label": {"zh": "群体称谓", "en": "Collective Terms"},
              "description": "王室相关群体性身份称谓",
              "members": [
                {
                  "name": "群后",
                  "type": "身份",
                  "tag": "〖#〗",
                  "context": "诸侯集合称谓",
                  "examples": ["群后皆从", "召群后议"],
                  "source": "A21规律（002第二轮）"
                },
                {
                  "name": "诸侯",
                  "type": "身份",
                  "tag": "〖#〗",
                  "context": "封建诸侯国君主的泛称",
                  "examples": ["诸侯皆叛", "天下诸侯"],
                  "source": "基础词汇"
                },
                ...
              ]
            }
          }
        },
        "官员": {
          "children": {
            "群体": {
              "members": [
                {
                  "name": "群臣",
                  "type": "身份",
                  "tag": "〖#〗",
                  "context": "臣子群体",
                  "examples": ["群臣上寿", "与群臣议"]
                },
                {
                  "name": "百官",
                  "type": "官职",
                  "tag": "〖;〗",
                  "context": "官员群体",
                  "examples": ["百官奉职"]
                },
                ...
              ]
            }
          }
        },
        "儒生": {
          "children": {
            "群体": {
              "members": [
                {
                  "name": "诸生",
                  "type": "身份",
                  "tag": "〖#〗",
                  "context": "儒生群体",
                  "examples": ["诸生皆曰善"],
                  "source": "A70规律（099章）"
                },
                {
                  "name": "群儒",
                  "type": "身份",
                  "tag": "〖#〗",
                  "context": "儒者集合",
                  "examples": ["群儒争论"]
                },
                ...
              ]
            }
          }
        }
      }
    }
  }
}
```

**设计要点**：
1. **meta元数据**：版本、更新时间、统计信息
2. **tree层级**：保持原person.ttl树形结构
3. **members数组**：具体人物或群体词条
4. **type字段**：身份/官职/混合（辅助标注判断）
5. **tag字段**：推荐标注符号（〖#〗/〖;〗）
6. **context字段**：使用场景说明
7. **examples字段**：典型例句
8. **source字段**：溯源到SKILL规律或章节

---

### 6.2 taxonomy_updates.jsonl格式

```jsonl
{"category": "官员.群体", "action": "add", "member": {"name": "诸卿", "type": "官职", "context": "九卿及高级官员", "source": "062章第二轮", "examples": ["诸卿皆曰善"]}, "timestamp": "2026-03-21T10:30:00"}
{"category": "民众.群体", "action": "add", "member": {"name": "黎民", "type": "身份", "context": "平民百姓", "source": "034章第二轮", "examples": ["黎民涂炭"]}, "timestamp": "2026-03-21T11:15:00"}
{"category": "儒生.群体", "action": "update", "member": {"name": "诸生", "examples": ["诸生皆曰善", "召诸生议"]}, "timestamp": "2026-03-21T12:00:00"}
```

**字段说明**：
- `category`：目标分类路径（用`.`连接）
- `action`：操作类型（add新增/update更新/delete删除）
- `member`：成员对象（add时必需，update时部分字段）
- `timestamp`：记录时间（用于审计和回溯）

---

### 6.3 update_taxonomy.py核心逻辑

```python
import json
from datetime import datetime

def update_taxonomy(base_json_path, updates_jsonl_path, output_path):
    """
    合并taxonomy_updates.jsonl到person_taxonomy.json
    """
    # 读取基础分类树
    with open(base_json_path) as f:
        taxonomy = json.load(f)

    # 读取更新记录
    updates = []
    with open(updates_jsonl_path) as f:
        for line in f:
            updates.append(json.loads(line.strip()))

    # 逐条应用更新
    for update in updates:
        category_path = update["category"].split(".")
        action = update["action"]

        # 定位到目标节点
        node = taxonomy["tree"]
        for key in category_path:
            node = node["children"][key]

        # 执行操作
        if action == "add":
            if "members" not in node:
                node["members"] = []
            node["members"].append(update["member"])
        elif action == "update":
            for i, member in enumerate(node["members"]):
                if member["name"] == update["member"]["name"]:
                    node["members"][i].update(update["member"])
                    break
        elif action == "delete":
            node["members"] = [m for m in node["members"]
                               if m["name"] != update["member"]["name"]]

    # 更新meta信息
    taxonomy["meta"]["updated"] = datetime.now().isoformat()
    taxonomy["meta"]["version"] = increment_version(taxonomy["meta"]["version"])

    # 写入输出
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(taxonomy, f, ensure_ascii=False, indent=2)

    print(f"✓ 应用 {len(updates)} 条更新")
    print(f"✓ 输出到 {output_path}")

def increment_version(version_str):
    """版本号递增 (2.0 -> 2.1)"""
    major, minor = map(int, version_str.split("."))
    return f"{major}.{minor + 1}"
```

---

## 七、效果预期与评估

### 7.1 定量指标

| 指标 | 现状（无分类树） | 目标（有分类树） | 提升 |
|------|----------------|----------------|------|
| 群体称谓准确率 | ~85%（易混淆身份/官职） | >95% | +10% |
| Agent查询时间 | 文本扫描~30s | JSON查询~3s | -90% |
| 规律数量 | 67条 | ~50条（简化） | -25% |
| 分类树覆盖率 | N/A | ~100个群体词 | - |
| 每章新增类别 | N/A | 平均0.3个/章 | - |

### 7.2 定性改进

**对Agent**：
- ✅ 群体称谓判断从"文本规则扫描"→"结构化查询"
- ✅ 新遇群体词可快速确认是否已知
- ✅ 分类树提供type/context辅助决策

**对SKILL维护者**：
- ✅ 分类知识从规则文本迁移到taxonomy（单一真相源）
- ✅ 新规律追加时，优先考虑是否属于分类树
- ✅ SKILL-03c-rules专注语境判断规律，不再堆积词表

**对知识图谱**：
- ✅ 分类树与kg/entities数据双向验证
- ✅ 分类树成为实体标注的"元数据层"
- ✅ 支持后续语义推理（如"诸生"→儒生群体→儒家文化）

---

## 八、风险与对策

### 8.1 风险识别

| 风险 | 可能性 | 影响 | 优先级 |
|------|--------|------|--------|
| JSON格式不适合Agent读取 | 中 | 高 | 1 |
| 分类树更新流程复杂 | 高 | 中 | 2 |
| 分类树与规律库冲突 | 中 | 中 | 3 |
| Agent不习惯读取分类树 | 中 | 低 | 4 |

### 8.2 对策

**风险1对策**：A/B测试JSON vs. Markdown格式，选择Agent友好的
**风险2对策**：简化更新流程，提供脚本自动化；初期人工审核
**风险3对策**：明确分工：分类树负责"是什么"，规律库负责"怎么判断"
**风险4对策**：在SKILL-03c-taxonomy.md提供详细示例和模板

---

## 九、长期愿景

### 9.1 多实体类型扩展

**当前**：人物分类树（person.ttl）
**未来**：
- 地名分类树（place.ttl）：邦国/郡县/地理特征
- 器物分类树（artifact.ttl）：武器/乐器/车马/建筑
- 事件分类树（event.ttl）：战争/祭祀/册封/盟约
- 思想分类树（ideology.ttl）：儒家/道家/法家/兵家

### 9.2 分类树自动推理

**当前**：人工维护分类树
**未来**：
- 从kg/entities自动推断人物分类（聚类算法）
- 从章节主题自动推断领域标签
- 利用LLM zero-shot分类新发现的群体词

### 9.3 跨章一致性检查

**当前**：按章反思，各章独立
**未来**：
- 利用分类树发现跨章标注不一致
- 示例：同一"群后"在010章标注〖#〗，在014章漏标
- 自动生成跨章一致性报告

---

## 十、总结

### 10.1 核心要点

1. **问题本质**：SKILL规律中隐含大量分类知识，但以文本形式存储，难以系统化
2. **解决方案**：建立kg/taxonomy分类树，实现"标注↔分类"双向迭代
3. **优先级1**：补充人物群体类别（~40个词），立即提升群体称谓判断准确率
4. **集成SKILL**：在Step 0读取分类树，Step 2辅助判断，完成后更新分类树
5. **渐进实施**：第三轮按章反思逐章迭代分类树，避免一次性重构

### 10.2 关键insight

> **"分类树是规律的结构化形式，规律是分类树的使用指南"**

**双向关系**：
- **分类树告诉Agent"是什么"**（群后是王室群体，类型是身份）
- **规律告诉Agent"怎么判断"**（语境判断、固定搭配、密度检查）

### 10.3 下一步行动

**立即执行**（本周）：
1. 创建person_taxonomy.json生成脚本
2. 从SKILL-03c-rules提取群体称谓词表
3. 创建SKILL-03c-taxonomy.md（3级子SKILL）

**近期执行**（下周）：
1. 补充优先级1群体类别到person.ttl
2. 更新SKILL_03c_按章反思.md集成分类树
3. 选择062章或034章试点验证

**中期规划**（3-4周后）：
1. 第三轮按章反思启动，全面应用分类树
2. 逐章迭代分类树，积累100+群体词
3. 评估效果，迭代优化

---

**文档版本**: v1.0
**生成时间**: 2026-03-21
**字数统计**: 约11,000字
**目标**: 指导分类树增强按章反思的设计与实施
