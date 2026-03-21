# 元技能06: SKILL优化与演化 — 方法论文档的持续改进


---

## 一、核心思想

> **"SKILL本身也是总结出来的,在反思中不断积累和抽象"**

**SKILL优化与演化**（SKILL Optimization and Evolution）是指将实践过程中的日志、经验、模式持续总结提炼为SKILL文档,并通过结构化设计、渐进载入、版本迭代等方法保持SKILL的简洁性和有效性。

### 核心原则

1. **从实践到文档** — SKILL不是事先设计,而是从反思日志中总结
2. **持续抽象** — 新知识不断积累,旧SKILL需要提炼和简化
3. **结构化设计** — 有效拆分,支持渐进载入(Progressive Loading)
4. **模板化迭代** — Agent提示词作为模板,随SKILL演化
5. **版本管理** — 记录演化历史,支持回溯和对比

---

## 二、SKILL的生命周期

### 2.1 诞生:从日志到SKILL

**阶段0:冷启动(无SKILL)**

```
场景: 第一次标注实体

开发者行动:
  1. 手工标注3-10个样本
  2. 记录标注决策("为什么这个是人名,那个不是?")
  3. 观察模式("人名通常出现在'曰'之前")

产出: 手工样本 + 决策日志(notes.md)
```

---

**阶段1:MVP规则(最小可行SKILL)**

```markdown
# SKILL_03a_实体标注.md (v0.1)

## 基本规则(5条)

1. 人名标注:`〖@人名〗`
   - 示例:`〖@刘邦〗`、`〖@项羽〗`

2. 人名识别模式:
   - X曰 → X是人名
   - X者 → X可能是人名
   - 姓Y名X → X是人名

3. 不标注:
   - 虚词(之、而、也...)
   - 动词单独出现

4. 歧义处理:
   - 同名异人 → 后续消歧
   - 不确定 → 先标注,后review

5. 质量标准:
   - 准确率>80%
   - 召回率>70%
```

**特点**:
- 极简(1页纸)
- 仅包含核心规则
- 快速上手(10分钟读完)

---

**阶段2:试点扩展(发现新模式)**

```
试点: 标注10-20篇章节

过程:
  - 应用MVP规则
  - 遇到问题 → 记录在日志
  - 每篇标注后写反思笔记

日志示例(logs/entity_tagging_pilot.md):
  ─────────────────────────────────────
  章节: 005 秦本纪
  问题1: "武王"既指周武王,又指秦武王,MVP规则未覆盖
  决策: 临时用上下文判断,记录为"待制定规则"

  问题2: "公子"+"姓名"的组合(如"公子白")未定义
  决策: 暂时标注为〖@公子白〗,不拆分

  问题3: 官职"丞相"是否标注?
  决策: 本轮不标注官职,专注人名
  ─────────────────────────────────────

  章节: 006 秦始皇本纪
  问题1: "武王"再次出现(秦武王),确认需要消歧规则
  决策: 创建disambiguation_map.json

  问题4: "吕不韦"是人名还是"吕氏不韦"?
  决策: 查证史料,"吕不韦"是复姓+单名,标注为〖@吕不韦〗

  新模式: 发现"复姓"模式(公孙、司马、欧阳...)
  ─────────────────────────────────────
```

---

**阶段3:模式总结(形成SKILL v1.0)**

```python
# scripts/summarize_pilot_logs.py

def extract_patterns(log_file):
    """从试点日志中提取模式"""

    problems = parse_log(log_file)  # 解析问题清单

    # 按类型分组
    by_type = {
        'disambiguation': [],  # 消歧问题
        'new_entity_type': [], # 新实体类型
        'boundary': [],        # 边界判断
        'exception': []        # 例外规则
    }

    for problem in problems:
        by_type[classify_problem(problem)].append(problem)

    # 统计频次
    for ptype, items in by_type.items():
        print(f"{ptype}: {len(items)}个问题")
        # 高频问题(>3次出现) → 需要写入SKILL
        high_freq = [p for p in items if p['count'] >= 3]
        print(f"  高频({len(high_freq)}): {[p['summary'] for p in high_freq]}")

    return by_type

# 输出示例:
# disambiguation: 15个问题
#   高频(3): ['武王歧义', '王单字歧义', '公子+名组合']
# boundary: 8个问题
#   高频(2): ['公子是否独立标注', '复姓识别']
```

---

**形成SKILL v1.0**:

```markdown
# SKILL_03a_实体标注.md (v1.0)

## 一、核心规则(从MVP继承)
[5条基本规则]

## 二、消歧规则(从试点总结)

### 规则6: 短名消歧
**问题**: "武王"、"昭王"等短名指多人

**解决**:
1. 查找前置邦国:`&周&@武王@` → 周武王
2. 使用章节上下文:005章(秦本纪)中的"武王"默认为秦武王
3. 建立disambiguation_map.json

**示例**:
  - 原文:`周〖@武王〗伐纣` → 周武王
  - 原文:`〖@武王〗即位,封弟〖@平原君〗`(在赵世家) → 赵武王

### 规则7: 复姓识别
**模式**: 公孙、司马、欧阳、诸葛、令狐...

**标注**: 整体标注,不拆分
  - ✅ `〖@司马迁〗`
  - ❌ `〖@司马〗〖@迁〗`

**复姓列表**: 见`doc/spec/复姓表.md`(38个常见复姓)

## 三、边界规则(从试点总结)

### 规则8: 公子+名组合
**模式**: `公子X`(如公子白、公子无忌)

**标注**: 整体标注
  - `〖@公子白〗`、`〖@公子无忌〗`

**例外**: 如有明确全名,使用全名
  - 公子无忌 = 魏公子无忌 = 信陵君 → 统一标注为`〖@信陵君〗`

## 四、例外规则(从试点总结)

### 规则9: 神话人物
**特殊处理**: 黄帝、炎帝、蚩尤、尧、舜、禹

**考虑**: 是否需要单独类型`〖?@神话人物〗`?
**当前决策**: 暂时用`〖@人名〗`,后续可拆分

### 规则10: 官职+人名
**模式**: 丞相李斯、太尉周勃

**标注**: 分别标注
  - `〖;丞相〗〖@李斯〗`
  - `〖;太尉〗〖@周勃〗`

## 五、质量标准(更新)

- 准确率: >90% (v0.1的80% → v1.0的90%)
- 召回率: >85% (v0.1的70% → v1.0的85%)
- 一致性: 同一人物的标注在全书中一致

## 六、附录:试点统计

- 试点章节: 20篇
- 标注人名: 2,340个
- 发现新模式: 10个
- 高频问题: 25个 → 形成5条新规则(6-10)
```

**v1.0特点**:
- 从5条规则扩展到10条
- 包含试点中的真实问题和解决方案
- 质量标准提升(80%→90%)
- 有附录说明规则来源

---

### 2.2 成长:多轮反思与积累

**阶段4:全量应用(130篇) + 第一轮反思**

```
应用SKILL v1.0到全部130篇
  ↓
运行Lint检查,发现118章有错误
  ↓
第一轮反思(按章)
  ↓
生成反思日志(doc/reflection/round1_entity_tagging.md)
```

**反思日志示例**:

```markdown
# 第一轮实体标注反思总结

## 整体情况
- 修正章节: 118/130
- 修正人名: 1,247处
- 主要问题: 短名消歧失效、复姓遗漏、边界不清

## 发现的新模式(12条)

### 模式1: 别名链
**问题**: 刘邦在不同章节有不同称谓,但SKILL未处理别名
**示例**: 沛公(早期) → 汉王(中期) → 高祖(称帝) → 高帝(死后)
**影响**: 156处标注不一致
**修正方案**: 建立entity_aliases.json,统一映射到规范名

### 模式2: 女性人名模式
**问题**: 女性常用"X氏"、"X姬"、"X娥",SKILL未明确
**示例**: 吕雉(吕后)、赵姬(秦始皇母)、西施
**影响**: 67处误标或遗漏
**修正方案**: 新增女性人名识别规则

### 模式3: 单字名的误标
**问题**: "信"、"贾"、"韩"等单字既是人名又是国名
**示例**: "信陵君"的"信"(地名) vs "韩信"的"信"(人名)
**影响**: 89处误标
**修正方案**: 单字名必须有上下文约束(前有姓氏/后有动词)

... (12条模式详细描述)

## 规则更新建议

**新增规则11-15**(从12条模式中提炼5条核心):
  11. 别名映射规则
  12. 女性人名识别
  13. 单字名约束
  14. 帝号标准化
  15. 外族人名处理

**废弃规则**:
  - 规则3(X者→可能是人名) — 太宽泛,误标率高

**修订规则**:
  - 规则6(短名消歧) — 补充4层启发式策略

## 统计数据

| 问题类型 | 数量 | 占比 |
|---------|------|------|
| 别名不一致 | 456 | 36.6% |
| 消歧失败 | 312 | 25.0% |
| 边界错误 | 234 | 18.8% |
| 遗漏 | 178 | 14.3% |
| 误标 | 67 | 5.4% |

## 下一步行动

1. 更新SKILL v1.0 → v1.5(集成新规则)
2. 构建entity_aliases.json(595条别名)
3. 重新标注高错误率章节(20篇)
4. 第二轮反思(重点:别名一致性)
```

---

**形成SKILL v1.5**:

```markdown
# SKILL_03a_实体标注.md (v1.5)

## 版本历史
- v0.1 (2024-10-01): MVP,5条基本规则
- v1.0 (2024-11-05): 试点总结,10条规则
- v1.5 (2024-12-10): 第一轮反思,15条规则 + 别名系统

## 一、核心规则(1-5,继承)
[...]

## 二、消歧与别名(6-11,扩展)

### 规则6: 短名消歧(修订)
[增加4层启发式策略详细描述]

### 规则11: 别名映射(新增)
**机制**: 使用entity_aliases.json统一别名

**查询流程**:
  表面形式 → reverse_index → 规范名

**示例**:
  - "沛公" → reverse_index["沛公"] → "刘邦"
  - "汉王" → reverse_index["汉王"] → "刘邦"
  - "高祖" → reverse_index["高祖"] → "刘邦"

**维护**: 人工审查auto_detect_aliases.py的输出,确认后加入

## 三、边界规则(7-13,扩展)

### 规则13: 单字名约束(新增)
**问题**: 单字既可能是人名、地名、国名

**标注条件**(必须满足至少一个):
  1. 前有明确姓氏:`〖&韩〗〖@信〗` → 韩信(人名)
  2. 后有明确动词:`〖@信〗曰` → 信(人名)
  3. 在别名表中:`reverse_index["信"]` → "韩信"

**反例**(不标注):
  - "伐〖=韩〗" — 韩是国名,无人名上下文
  - "信陵君" — "信"是地名,不单独标注

## 四、特殊人群(14-15,新增)

### 规则14: 帝号标准化
**问题**: 帝王称谓多样(庙号/谥号/年号/尊号)

**标注原则**: 使用最常见称谓
  - 秦始皇(不用"始皇帝"、"嬴政")
  - 汉武帝(不用"武帝"、"刘彻"、"孝武皇帝")

**规范名映射**: 见person_canonical_names.json

### 规则15: 外族人名
**模式**: 匈奴、南越、朝鲜、西域人名,音译为主

**标注**: 整体标注,不拆分
  - `〖@冒顿〗`(匈奴单于)
  - `〖@尉佗〗`(南越王)

## 五、质量标准(更新)
- 准确率: >95% (v1.0的90% → v1.5的95%)
- 召回率: >90% (v1.0的85% → v1.5的90%)
- 别名一致性: 100%(全书同一人物的规范名一致)

## 六、工具支持(新增)

### 自动化工具
1. `auto_detect_aliases.py` — 别名自动检测
2. `disambiguate_names.py` — 消歧自动化
3. `lint_entity_consistency.py` — 一致性检查

### 辅助数据
1. `entity_aliases.json` — 595条别名映射
2. `disambiguation_map.json` — 644处短名消歧
3. `person_canonical_names.json` — 规范名映射

## 七、附录

### 附录A: v1.0 → v1.5变更日志
- 新增规则: 11, 13, 14, 15
- 修订规则: 6(消歧策略扩展)
- 废弃规则: 3(X者模式,误标率高)
- 质量提升: 准确率90%→95%, 召回率85%→90%

### 附录B: 第一轮反思统计
[1,247处修正的详细统计]
```

---

**v1.5特点**:
- 规则数量增加(10→15),但更精确
- 集成了第一轮反思的所有发现
- 引入自动化工具支持
- 有版本历史和变更日志

---

### 2.3 成熟:抽象与简化

**问题**: SKILL越来越长(v1.5已达5000字)

**挑战**:
- Agent阅读成本高(5000字 = 7500 tokens)
- 新手学习门槛高(需要30分钟理解)
- 修改困难(规则相互依赖)

---

**解决方案:结构化拆分**

```
SKILL_03_实体构建.md (总览,500字)
  ├─ SKILL_03a_实体标注.md (核心规则,2000字)
  │   ├─ § 一、核心规则(1-5)
  │   ├─ § 二、消歧与别名(6-11)
  │   └─ § 三、边界规则(7-13)
  ├─ SKILL_03b_实体消歧.md (专项,1500字)
  │   ├─ § 一、短名消歧(4层启发式)
  │   ├─ § 二、别名映射
  │   └─ § 三、内联消歧语法
  ├─ SKILL_03c_实体标注反思.md (方法论,2000字)
  │   ├─ § 一、按章反思
  │   ├─ § 二、按类型反思
  │   └─ § 三、全局一致性
  └─ SKILL_03d_渲染与发布.md (衔接,500字)
```

---

**拆分后的SKILL_03a(精简版)**:

```markdown
# SKILL_03a_实体标注.md (v2.0)

> 本文档专注于标注规则本身,消歧/反思/渲染见对应SKILL。

## 版本历史
- v2.0 (2025-01-15): 结构化拆分,抽象核心规则

## 一、18类实体标注(v2.5规范)

| 符号 | 类型 | 示例 |
|------|------|------|
| @ | 人名 | `〖@刘邦〗` |
| = | 地名 | `〖=关中〗` |
| ; | 官职 | `〖;丞相〗` |
| ... | ... | ... |

详见: `doc/spec/标注格式规范.md`

## 二、核心标注规则(5条精华)

### 规则1: 基本语法
`〖TYPE content〗`

TYPE = 单字符前缀(@ = ; 等)
content = 实体文本(无空格、无嵌套)

### 规则2: 人名识别模式
- X曰 → X是人名
- 姓Y名X → X是人名
- 官职+人名 → 分别标注`〖;官职〗〖@人名〗`

### 规则3: 边界判断
- 复姓整体标注:`〖@司马迁〗`
- 公子+名整体:`〖@公子白〗`
- 单字名需上下文约束(见SKILL_03b)

### 规则4: 优先级
1. 先标注确定性高的(明显人名/地名)
2. 再标注歧义性高的(需消歧,见SKILL_03b)
3. 不确定的先跳过,反思阶段处理

### 规则5: 工具辅助
- 自动检测:`python scripts/auto_detect_entities.py`
- 一致性检查:`python scripts/lint_entity_consistency.py`
- 消歧工具:见SKILL_03b

## 三、快速决策树

```
遇到一个词X:
  ├─ 是否在entity_index中?
  │   ├─ 是 → 查询规范名,直接标注
  │   └─ 否 ↓
  ├─ 是否匹配基本模式(X曰/姓Y名X)?
  │   ├─ 是 → 标注为人名
  │   └─ 否 ↓
  ├─ 是否单字?
  │   ├─ 是 → 需要上下文约束(见SKILL_03b)
  │   └─ 否 ↓
  ├─ 不确定 → 跳过,标记为待review
```

## 四、质量标准

- 准确率: >95%
- 召回率: >90%
- 一致性: 100%(同一实体规范名一致)

**检查工具**:
```bash
python scripts/validate_entity_tagging.py chapter_md/001_*.tagged.md
```

## 五、进阶阅读

- 消歧规则: SKILL_03b_实体消歧.md
- 反思方法: SKILL_03c_实体标注反思.md
- 别名映射: entity_aliases.json
- 消歧数据: disambiguation_map.json

## 六、常见问题(FAQ)

**Q1: "武王"标注为哪个武王?**
A: 见SKILL_03b § 短名消歧(4层启发式)

**Q2: 单字"信"是否标注?**
A: 需要上下文约束,见规则3 + SKILL_03b § 单字名处理

**Q3: 别名如何统一?**
A: 使用entity_aliases.json,见SKILL_03b § 别名映射

**Q4: 如何反思和修正?**
A: 见SKILL_03c_实体标注反思.md
```

**v2.0特点**:
- 精简到2000字(vs v1.5的5000字)
- 聚焦核心规则(5条精华)
- 进阶内容拆分到其他SKILL
- 有快速决策树和FAQ
- 渐进学习路径清晰

---

### 2.4 演化:版本管理与回溯

**版本演化记录**:

```
v0.1 (2024-10-01): 冷启动MVP
  - 5条基本规则
  - 覆盖率: 70%
  - 准确率: 80%

v1.0 (2024-11-05): 试点总结
  - 10条规则(+5条消歧/边界)
  - 覆盖率: 85%
  - 准确率: 90%

v1.5 (2024-12-10): 第一轮反思
  - 15条规则(+5条别名/特殊人群)
  - 引入entity_aliases.json
  - 覆盖率: 90%
  - 准确率: 95%

v2.0 (2025-01-15): 结构化拆分
  - 精简为5条核心规则(主文档)
  - 详细规则拆分到03b/03c
  - 覆盖率: 92%
  - 准确率: 97%

v2.5 (2025-03-10): 类型扩展
  - 18类实体(vs v2.0的15类)
  - 新增:数量/典籍/礼仪/刑法/思想
  - 覆盖率: 95%
  - 准确率: 98%
```

**版本对比工具**:

```bash
# 比较v1.0 vs v2.0的规则差异
diff skills/SKILL_03a_v1.0.md skills/SKILL_03a_v2.0.md

# 输出示例:
# - 规则3: X者 → 可能是人名 (废弃,误标率高)
# + 规则3: 边界判断(复姓/公子+名/单字约束)
# + § 进阶阅读: SKILL_03b/03c(新增结构化拆分)
```

---

## 三、结构化设计原则

### 3.1 模块化拆分策略

**拆分维度**:

```
按复杂度拆分:
  核心规则(必读) ← 5-10条精华
    ├─ 基础规则(简单场景)
    ├─ 进阶规则(复杂场景,链接到专项SKILL)
    └─ 例外规则(罕见情况,链接到附录)

按职能拆分:
  标注 (SKILL_03a) — 如何标注
  消歧 (SKILL_03b) — 如何消歧
  反思 (SKILL_03c) — 如何反思
  渲染 (SKILL_03d) — 如何渲染

按阶段拆分:
  冷启动 (00-META_冷启动.md) — 从0到1
  迭代 (00-META_迭代工作流.md) — 从1到N
  收敛 (SKILL_XXc_反思.md) — 从N到稳定
```

---

**拆分阈值**:

| 指标 | 阈值 | 行动 |
|------|------|------|
| 文档长度 | >5000字 | 考虑拆分 |
| 规则数量 | >15条 | 按类型拆分 |
| 嵌套层次 | >3层 | 拆分为独立文档 |
| 阅读时间 | >30分钟 | 拆分+导航 |
| Agent Token | >7500 tokens | 拆分+渐进载入 |

---

### 3.2 渐进载入(Progressive Loading)

**原理**:不要一次性加载所有SKILL,按需载入

**三层载入模型**:

```
Layer 1: 总览(必读,500字)
  - 工序概述
  - 核心原则
  - 导航地图

Layer 2: 核心规则(按需,2000字)
  - 基本标注规则
  - 快速决策树
  - 常见问题FAQ

Layer 3: 专项深入(按需,各1500字)
  - 消歧规则(复杂场景)
  - 反思方法(迭代优化)
  - 特殊案例(罕见情况)
```

---

**Agent Prompt模板**:

```python
def load_skill_progressive(task_type, complexity):
    """渐进载入SKILL文档"""

    # Layer 1: 总是加载总览
    skill_content = read_file("SKILL_03_实体构建.md")  # 500字

    # Layer 2: 根据任务加载核心规则
    if task_type == 'tagging':
        skill_content += read_file("SKILL_03a_实体标注.md")  # +2000字

    # Layer 3: 根据复杂度加载专项
    if complexity == 'disambiguation':
        skill_content += read_file("SKILL_03b_实体消歧.md")  # +1500字
    elif complexity == 'reflection':
        skill_content += read_file("SKILL_03c_实体标注反思.md")  # +2000字

    return skill_content

# 示例:简单标注任务
skill = load_skill_progressive('tagging', 'simple')
# 载入: Layer 1 (500字) + Layer 2 (2000字) = 2500字

# 示例:复杂消歧任务
skill = load_skill_progressive('tagging', 'disambiguation')
# 载入: Layer 1 (500字) + Layer 2 (2000字) + Layer 3 (1500字) = 4000字

# vs 一次性加载全部: 10,000字
# 节省: 60% tokens
```

---

**收益**:

```
简单任务(80%的场景):
  载入2500字 vs 全量10,000字
  节省: 75% tokens
  成本: $0.025 vs $0.10

复杂任务(20%的场景):
  载入4000字 vs 全量10,000字
  节省: 60% tokens
  成本: $0.04 vs $0.10

平均节省:
  0.8 × 75% + 0.2 × 60% = 72%
```

---

### 3.3 导航与交叉引用

**设计原则**:文档间清晰链接

```markdown
# SKILL_03a_实体标注.md

## 二、核心标注规则

### 规则3: 边界判断
- 复姓整体标注:`〖@司马迁〗`
- 单字名需上下文约束

**详见**: [SKILL_03b § 单字名处理](SKILL_03b_实体消歧.md#单字名处理)

### 规则5: 工具辅助
- 消歧工具:见[SKILL_03b](SKILL_03b_实体消歧.md)
- 反思流程:见[SKILL_03c](SKILL_03c_实体标注反思.md)
```

**导航地图**(在总览文档):

```markdown
# SKILL_03_实体构建.md

## 文档导航

┌─────────────────────────────────────────┐
│  SKILL_03 实体构建(总览)                 │
├─────────────────────────────────────────┤
│  ├─ 03a 实体标注(核心规则)               │
│  │   ├─ 基本标注语法                     │
│  │   ├─ 人名识别模式                     │
│  │   └─ 边界判断 → 详见03b               │
│  ├─ 03b 实体消歧(专项)                   │
│  │   ├─ 短名消歧(4层启发式)              │
│  │   ├─ 别名映射                         │
│  │   └─ 内联消歧语法                     │
│  ├─ 03c 实体标注反思(方法论)             │
│  │   ├─ 按章反思                         │
│  │   ├─ 按类型反思                       │
│  │   └─ 全局一致性                       │
│  └─ 03d 渲染与发布(衔接)                 │
└─────────────────────────────────────────┘

## 快速入口

**新手**: 阅读03a(核心规则) + FAQ
**进阶**: 阅读03b(消歧) + 03c(反思)
**维护**: 检查版本历史 + 反思日志
```

---

## 四、Agent提示词模板化

### 4.1 提示词与SKILL的对应

**关系**:
```
SKILL文档 = 人类可读的方法论
Agent提示词 = 机器可执行的指令

SKILL文档 → [模板化] → Agent提示词
```

---

**示例**:

**SKILL_03a § 规则2(人名识别模式)**:
```markdown
### 规则2: 人名识别模式
- X曰 → X是人名
- 姓Y名X → X是人名
- 官职+人名 → 分别标注
```

**对应的Agent Prompt模板**:

```python
ENTITY_TAGGING_PROMPT = """
你是一个古文实体标注专家。请按以下规则标注人名:

## 识别模式
1. 如果文本匹配"X曰",则X是人名,标注为〖@X〗
2. 如果文本匹配"姓Y名X",则X是人名,标注为〖@X〗
3. 如果文本匹配"官职+人名",分别标注:〖;官职〗〖@人名〗

## 示例
输入: 刘邦曰:"天下..."
输出: 〖@刘邦〗曰:"天下..."

输入: 丞相李斯
输出: 〖;丞相〗〖@李斯〗

## 任务
请标注以下文本中的人名:

{text}
"""
```

---

### 4.2 模板参数化

**可变部分抽离为参数**:

```python
# 模板定义
ENTITY_TAGGING_PROMPT_TEMPLATE = """
你是一个古文实体标注专家。请按以下规则标注{entity_type}:

## 识别模式
{patterns}

## 示例
{examples}

## 边界规则
{boundary_rules}

## 任务
请标注以下文本中的{entity_type}:

{text}
"""

# 参数配置
ENTITY_TYPE_CONFIGS = {
    'person': {
        'entity_type': '人名',
        'patterns': [
            '如果文本匹配"X曰",则X是人名',
            '如果文本匹配"姓Y名X",则X是人名'
        ],
        'examples': [
            '输入: 刘邦曰 → 输出: 〖@刘邦〗曰'
        ],
        'boundary_rules': [
            '复姓整体标注:〖@司马迁〗',
            '单字名需上下文约束'
        ]
    },
    'place': {
        'entity_type': '地名',
        'patterns': [
            '如果X在地名词表中,标注为〖=X〗',
            '如果文本匹配"X郡"、"X县",则X是地名'
        ],
        # ...
    }
}

# 动态生成prompt
def generate_prompt(entity_type, text):
    config = ENTITY_TYPE_CONFIGS[entity_type]
    return ENTITY_TAGGING_PROMPT_TEMPLATE.format(
        entity_type=config['entity_type'],
        patterns='\n'.join(config['patterns']),
        examples='\n'.join(config['examples']),
        boundary_rules='\n'.join(config['boundary_rules']),
        text=text
    )
```

---

### 4.3 提示词版本管理

**与SKILL同步版本**:

```python
# prompts/entity_tagging_v2.0.py

"""
Entity Tagging Prompt Template v2.0

对应SKILL: SKILL_03a v2.0
更新日期: 2025-01-15
变更: 精简为5条核心规则,拆分消歧到SKILL_03b
"""

ENTITY_TAGGING_PROMPT_V2_0 = """
[模板内容]
"""

# 版本历史
PROMPT_VERSION_HISTORY = {
    'v1.0': {
        'date': '2024-11-05',
        'skill_version': 'SKILL_03a v1.0',
        'rules_count': 10,
        'avg_tokens': 1500
    },
    'v1.5': {
        'date': '2024-12-10',
        'skill_version': 'SKILL_03a v1.5',
        'rules_count': 15,
        'avg_tokens': 2200
    },
    'v2.0': {
        'date': '2025-01-15',
        'skill_version': 'SKILL_03a v2.0',
        'rules_count': 5,  # 精简
        'avg_tokens': 800  # 渐进载入
    }
}
```

---

### 4.4 A/B测试与迭代

**测试不同prompt版本的效果**:

```python
# tests/test_prompt_versions.py

def ab_test_prompts(test_data, prompt_v1, prompt_v2):
    """对比两个prompt版本的效果"""

    results = {
        'v1': {'precision': [], 'recall': [], 'cost': []},
        'v2': {'precision': [], 'recall': [], 'cost': []}
    }

    for sample in test_data:
        # 测试v1
        output_v1 = run_agent(prompt_v1, sample['text'])
        results['v1']['precision'].append(
            evaluate_precision(output_v1, sample['gold'])
        )
        results['v1']['cost'].append(count_tokens(prompt_v1))

        # 测试v2
        output_v2 = run_agent(prompt_v2, sample['text'])
        results['v2']['precision'].append(
            evaluate_precision(output_v2, sample['gold'])
        )
        results['v2']['cost'].append(count_tokens(prompt_v2))

    # 统计对比
    print("## A/B测试结果\n")
    for version in ['v1', 'v2']:
        print(f"### Prompt {version}")
        print(f"- 准确率: {np.mean(results[version]['precision']):.2%}")
        print(f"- 召回率: {np.mean(results[version]['recall']):.2%}")
        print(f"- 平均成本: {np.mean(results[version]['cost'])} tokens")

# 输出示例:
# ## A/B测试结果
#
# ### Prompt v1.5
# - 准确率: 95.3%
# - 召回率: 89.7%
# - 平均成本: 2200 tokens
#
# ### Prompt v2.0
# - 准确率: 97.1% (+1.8%)
# - 召回率: 91.2% (+1.5%)
# - 平均成本: 800 tokens (-64%)
#
# 结论: v2.0在质量和成本上都优于v1.5,采纳v2.0
```

---

## 五、反思日志的系统化

### 5.1 日志结构标准化

**统一模板**:

```markdown
# 第N轮XXX反思总结

## 元数据
- 反思轮次: N
- 反思对象: XXX(实体标注/事件年代/关系发现)
- 开始日期: YYYY-MM-DD
- 完成日期: YYYY-MM-DD
- 涉及章节: M/130
- Agent: Claude 3.5 Sonnet
- SKILL版本: vX.Y

## 整体情况

| 指标 | 数值 |
|------|------|
| 修正章节 | M/130 |
| 修正条目 | N条 |
| 主要问题 | [3-5类] |
| 平均置信度 | X% |

## 发现的新模式(K条)

### 模式1: [模式名称]
**问题**: [问题描述]
**示例**: [具体案例]
**影响**: [影响范围]
**修正方案**: [解决方案]
**频次**: [出现次数]

### 模式2: ...

## 规则更新建议

**新增规则**: [编号列表]
**废弃规则**: [编号列表]
**修订规则**: [编号列表]

## 统计数据

| 问题类型 | 数量 | 占比 |
|---------|------|------|
| [类型1] | N1 | X% |
| [类型2] | N2 | Y% |

## 典型案例(Top 10)

[详细描述10个代表性案例]

## 下一步行动

1. [行动1]
2. [行动2]
3. ...

## 附录

### 附录A: 完整修正清单
[所有修正的详细列表,可选]

### 附录B: 脚本输出
[Agent反思的原始输出,可选]
```

---

### 5.2 日志自动生成

```python
# scripts/generate_reflection_report.py

def generate_reflection_report(round_num, corrections, patterns):
    """自动生成反思报告"""

    template = load_template("templates/reflection_report.md")

    # 统计数据
    stats = {
        'total_corrections': len(corrections),
        'affected_chapters': len(set(c['chapter'] for c in corrections)),
        'problem_types': Counter(c['type'] for c in corrections),
        'avg_confidence': np.mean([c['confidence'] for c in corrections])
    }

    # 提取模式
    patterns_summary = []
    for pattern in patterns:
        patterns_summary.append({
            'name': pattern['name'],
            'problem': pattern['description'],
            'examples': pattern['examples'][:3],  # Top 3示例
            'impact': pattern['affected_count'],
            'frequency': pattern['occurrences']
        })

    # 规则更新建议
    rule_updates = suggest_rule_updates(patterns)

    # 渲染模板
    report = template.format(
        round_num=round_num,
        date_start=corrections[0]['date'],
        date_end=corrections[-1]['date'],
        stats=stats,
        patterns=patterns_summary,
        rule_updates=rule_updates,
        top_cases=select_top_cases(corrections, n=10)
    )

    # 保存
    output_path = f"doc/reflection/round{round_num}_summary.md"
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"反思报告已生成: {output_path}")
```

---

### 5.3 从日志到SKILL的自动提炼

```python
# scripts/extract_rules_from_logs.py

def extract_rules_from_reflection_logs(log_files):
    """从多轮反思日志中提取规则"""

    all_patterns = []

    for log_file in log_files:
        patterns = parse_patterns_from_log(log_file)
        all_patterns.extend(patterns)

    # 按频次排序
    pattern_freq = Counter(p['name'] for p in all_patterns)

    # 高频模式(≥3次出现) → 转化为规则
    frequent_patterns = [
        p for p in pattern_freq.items() if p[1] >= 3
    ]

    # 生成规则草稿
    rules_draft = []
    for pattern_name, freq in frequent_patterns:
        pattern_details = [p for p in all_patterns if p['name'] == pattern_name][0]

        rule_draft = {
            'rule_name': pattern_name,
            'description': pattern_details['problem'],
            'solution': pattern_details['修正方案'],
            'examples': pattern_details['examples'],
            'frequency': freq,
            'confidence': 'high' if freq >= 5 else 'medium'
        }

        rules_draft.append(rule_draft)

    # 输出为Markdown
    output_rules_to_markdown(rules_draft, "doc/drafts/new_rules_draft.md")

    return rules_draft

# 输出示例(doc/drafts/new_rules_draft.md):
# ## 新规则草稿(从反思日志提炼)
#
# ### 规则候选1: 别名链处理
# **来源**: 第1/2/3轮反思日志(频次:5)
# **问题**: 同一人物在不同章节有不同称谓
# **解决方案**: 建立entity_aliases.json,统一映射到规范名
# **示例**:
#   - 沛公 → 刘邦
#   - 汉王 → 刘邦
#   - 高祖 → 刘邦
# **置信度**: high(频次≥5)
#
# **建议**: 加入SKILL_03a v1.5作为规则11
```

---

## 六、质量度量与收敛判断

### 6.1 SKILL质量指标

```python
def evaluate_skill_quality(skill_doc, test_data):
    """评估SKILL文档质量"""

    metrics = {}

    # 指标1: 规则覆盖率
    total_cases = len(test_data)
    covered_cases = sum(
        1 for case in test_data
        if case_covered_by_skill(case, skill_doc)
    )
    metrics['coverage'] = covered_cases / total_cases

    # 指标2: 规则冲突率
    rules = extract_rules(skill_doc)
    conflicts = detect_rule_conflicts(rules)
    metrics['conflict_rate'] = len(conflicts) / len(rules)

    # 指标3: 文档可读性
    metrics['readability'] = {
        'word_count': count_words(skill_doc),
        'rule_count': len(rules),
        'avg_rule_length': np.mean([len(r) for r in rules]),
        'nesting_depth': max_nesting_depth(skill_doc)
    }

    # 指标4: Agent执行成功率
    success_count = 0
    for case in test_data:
        output = run_agent_with_skill(skill_doc, case['input'])
        if evaluate(output, case['gold']):
            success_count += 1
    metrics['agent_success_rate'] = success_count / total_cases

    return metrics

# 输出示例:
# {
#   'coverage': 0.92,  # 92%案例被规则覆盖
#   'conflict_rate': 0.03,  # 3%规则有冲突
#   'readability': {
#       'word_count': 2340,
#       'rule_count': 15,
#       'avg_rule_length': 156,
#       'nesting_depth': 2
#   },
#   'agent_success_rate': 0.95  # 95%案例Agent执行成功
# }
```

---

### 6.2 收敛判断标准

**何时停止迭代?**

```python
def check_skill_convergence(history):
    """判断SKILL是否收敛"""

    # 标准1: 新发现模式减少
    recent_patterns = [h['new_patterns'] for h in history[-3:]]
    if all(p < 5 for p in recent_patterns):
        print("✓ 新模式发现减少(<5/轮)")

    # 标准2: 修正数量递减
    recent_corrections = [h['corrections'] for h in history[-3:]]
    if is_decreasing(recent_corrections):
        print("✓ 修正数量递减")

    # 标准3: 准确率稳定
    recent_accuracy = [h['accuracy'] for h in history[-3:]]
    if np.std(recent_accuracy) < 0.01:  # 标准差<1%
        print("✓ 准确率稳定")

    # 标准4: 规则数量稳定
    recent_rule_counts = [h['rule_count'] for h in history[-3:]]
    if len(set(recent_rule_counts)) == 1:  # 连续3轮规则数不变
        print("✓ 规则数量稳定")

    # 综合判断
    converged = (
        all(p < 5 for p in recent_patterns) and
        is_decreasing(recent_corrections) and
        np.std(recent_accuracy) < 0.01 and
        len(set(recent_rule_counts)) == 1
    )

    return converged

# 示例:
# 第1轮: 新模式25, 修正1247, 准确率90%, 规则10
# 第2轮: 新模式12, 修正456, 准确率93%, 规则13
# 第3轮: 新模式8, 修正234, 准确率95%, 规则15
# 第4轮: 新模式4, 修正89, 准确率96%, 规则15
# 第5轮: 新模式2, 修正34, 准确率96.5%, 规则15
#
# check_skill_convergence(history) → True
# 结论: SKILL已收敛,可以发布v2.0
```

---

## 七、跨项目SKILL迁移的优化

### 7.1 SKILL的可迁移性设计

**设计原则**:

```
高可迁移性规则:
  - 通用模式(文言文共性)
  - 抽象方法(不依赖具体数据)
  - 参数化配置(朝代/文体可替换)

低可迁移性规则:
  - 项目特定(史记特有人名)
  - 硬编码数据(章节映射)
  - 临时解决方案(workaround)
```

---

**标记可迁移性**:

```markdown
# SKILL_03a_实体标注.md

## 二、核心标注规则

### 规则2: 人名识别模式
**可迁移性**: ★★★★★ (通用)
**适用范围**: 所有文言文

- X曰 → X是人名
- 姓Y名X → X是人名

### 规则6: 短名消歧
**可迁移性**: ★★★★☆ (高度通用,需调整参数)
**适用范围**: 纪传体史书

**迁移说明**:
  - 4层启发式策略通用
  - CHAPTER_STATE映射需根据目标史书调整
  - 示例:汉书需更新为100+章的映射

### 规则11: 别名映射
**可迁移性**: ★★★☆☆ (中等,需重建数据)
**适用范围**: 任何有人物别名的文本

**迁移说明**:
  - 映射机制通用
  - entity_aliases.json需为目标史书重新构建
  - 示例:汉书需建立新的别名表(预计800+条)
```

---

### 7.2 SKILL差异文档

**迁移时生成差异清单**:

```markdown
# doc/transfer/史记SKILL→汉书SKILL差异清单.md

## 一、直接复用(80%)

| SKILL | 复用度 | 说明 |
|-------|--------|------|
| 00-META_反思.md | 100% | 完全通用 |
| 00-META_质量控制.md | 100% | 完全通用 |
| SKILL_03a_实体标注.md(核心规则1-5) | 95% | 微调示例 |

## 二、需要调整(15%)

| SKILL | 复用度 | 调整内容 |
|-------|--------|---------|
| SKILL_03b_实体消歧.md | 70% | CHAPTER_STATE映射(120章) |
| SKILL_04c_事件年代推断.md | 60% | 年号体系(汉代年号) |

## 三、需要重建(5%)

| 数据文件 | 复用度 | 说明 |
|---------|--------|------|
| entity_aliases.json | 20% | 部分重叠人物(刘邦/项羽等),其余需重建 |
| disambiguation_map.json | 10% | 章节不同,需重新构建 |

## 四、新增内容

| 类型 | 说明 |
|------|------|
| 年号解析 | 汉代大量使用年号纪年,史记时代较少 |
| 表格文献 | 汉书的"表"为二维矩阵,史记为时间线 |
| 西汉官制 | 三公九卿体系,需扩展官职词表 |
```

---

## 八、总结

### 核心要点

1. **SKILL从实践中来** — 冷启动→试点→反思→总结→抽象
2. **持续演化** — v0.1→v1.0→v1.5→v2.0,不断优化
3. **结构化拆分** — 超过5000字/15条规则就拆分
4. **渐进载入** — 三层模型(总览→核心→专项),节省70%+ tokens
5. **版本管理** — 记录演化历史,支持回溯对比
6. **模板化prompt** — SKILL与Agent提示词同步迭代
7. **日志系统化** — 标准化模板,自动生成报告
8. **质量度量** — 覆盖率/冲突率/成功率/收敛判断
9. **迁移优化** — 标记可迁移性,生成差异清单

### 哲学洞察

> **"好东西都是总结出来的"**

- SKILL不是事先设计的完美方案,而是**从失败中学习的结果**
- 反思日志是**知识的原材料**,SKILL是**提炼后的精华**
- 版本演化体现**认知的深化**:从具体案例→一般规律
- 结构化设计支持**渐进学习**:新手看核心,专家看全貌
- 模板化使**知识可复制**:SKILL→Prompt→自动化

### 与其他元技能的关系

- **← 反思**: SKILL演化的核心驱动力
- **← 冷启动**: SKILL的v0.1诞生于冷启动
- **← 迭代工作流**: SKILL在迭代中不断积累
- **← 可读性**: SKILL本身必须人类可读
- **← 知识压缩**: SKILL是对经验的压缩
- **→ 技能迁移**: 优化后的SKILL更易迁移

**SKILL优化与演化是项目"自我学习"能力的体现** — 通过系统化总结,项目不仅积累数据,更积累方法论本身。

---

## 附录:检查清单

### SKILL文档质量检查清单

**内容质量**:
- [ ] 规则来源明确(从哪次反思/试点总结?)
- [ ] 规则可执行(Agent能理解并执行?)
- [ ] 示例充分(每条规则至少1个示例)
- [ ] 例外明确(什么情况下规则不适用?)
- [ ] 质量标准量化(准确率/召回率目标)

**结构质量**:
- [ ] 文档长度<5000字(否则考虑拆分)
- [ ] 规则数量<15条(否则按类型拆分)
- [ ] 嵌套层次<3层(否则拆分为独立文档)
- [ ] 有导航地图(快速定位)
- [ ] 有交叉引用(链接到相关SKILL)

**命名与组织规范**:
- [ ] **一级SKILL**: `SKILL_NN_中文名.md` (如 `SKILL_03_实体构建.md`)
  - 编号：两位数字（00-99）
  - 位置：`skills/` 根目录
  - 用途：顶层任务/阶段划分
- [ ] **二级SKILL**: `SKILL_NNx_中文名.md` (如 `SKILL_03a_实体标注.md`)
  - 编号：数字+小写字母（03a, 03b, 03c...）
  - 位置：`skills/` 根目录
  - 用途：一级SKILL的子任务
- [ ] **三级SKILL**: `SKILL-NNx-英文名.md` (如 `SKILL-03c-rules.md`)
  - 编号：数字+小写字母+英文名（用短横线连接）
  - 位置：`skills/references/` 子目录
  - 用途：二级SKILL的支撑文档/规则库/工具集
- [ ] **元数据完整**（三级SKILL必须，二级SKILL推荐）:
  ```yaml
  ---
  name: SKILL-identifier
  description: 触发时机 + 功能说明（要详细且有推动性）
  compatibility: 依赖工具（可选）
  ---
  ```
- [ ] **多领域/多框架组织**:
  ```
  SKILL_NNx_任务名.md           ← 主流程 + 选择逻辑
  references/
    ├── SKILL-NNx-variant1.md   ← 变体1
    ├── SKILL-NNx-variant2.md   ← 变体2
    └── SKILL-NNx-variant3.md   ← 变体3
  ```

**可维护性**:
- [ ] 有版本历史(记录演化轨迹)
- [ ] 有变更日志(v1→v2改了什么?)
- [ ] 有可迁移性标记(★评级)
- [ ] 有对应的prompt模板
- [ ] 有A/B测试结果(验证改进效果)

**可用性**:
- [ ] 新手10分钟能上手(核心规则简洁)
- [ ] 专家能快速查询(有FAQ/索引)
- [ ] Agent能正确理解(测试成功率>90%)
- [ ] 支持渐进载入(三层模型)
