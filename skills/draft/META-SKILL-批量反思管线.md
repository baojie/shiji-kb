---
name: meta-batch-reflection-pipeline
description: 批量反思管线,将大规模质量审查拆解为"提示词生成→Agent执行→结果审查→批量应用"四阶段管线。适用于需要对大量文本进行系统性质量提升的场景,如实体标注审查、事件年代验证、一致性检查等。
---

# 元技能（草稿）: 批量反思管线 — 大规模质量审查的工程化方法

---

## 一、核心思想

> **"反思不是一次性的,而是可批量执行、可迭代优化的工程化流程"**

**批量反思管线**（Batch Reflection Pipeline）是将大规模质量审查工作拆解为标准化四阶段流程的方法论：

```
提示词生成 → Agent执行 → 结果审查 → 批量应用
    ↓            ↓           ↓           ↓
 模板化        自动化       人工验证    脚本化
```

### 核心洞察

```
传统反思方式:
  人工逐章阅读 → 发现问题 → 手动修改 → 无法复现

问题:
  - 130章需要100+小时人工时间
  - 质量标准不一致(前后章节标准漂移)
  - 无法追溯修改原因
  - 难以进行多轮迭代

批量反思管线:
  生成提示词 → Agent批量执行 → 审查报告 → 脚本应用

优势:
  - 10小时完成130章首轮反思
  - 标准一致(同一提示词模板)
  - 完整记录(每章反思报告)
  - 可迭代优化(多轮收敛)
```

---

## 二、四阶段详解

### 阶段1: 提示词生成（Template Generation）

#### 目标
为每个待反思单元生成标准化的提示词文件

#### 核心原则
- **模板化**: 统一的提示词结构，确保标准一致
- **上下文注入**: 每个单元注入特定上下文（章节号、标题、原文片段）
- **可复现**: 提示词文件存档，可追溯Agent输入

#### 实现模式

**核心逻辑**:
```python
# 加载模板 → 注入上下文 → 保存提示词文件
template = load_template("templates/reflect_entity_v3.md")
prompt = template.format(chapter_id, chapter_title, context, skill_doc)
save_prompt(f"prompts/reflect/{chapter_id}.md", prompt)
```

**提示词模板要素**:
```markdown
# 任务: 第{chapter_id}章《{chapter_title}》实体标注反思

## 反思目标
1. 检查实体边界错误
2. 发现消歧标注缺失
3. 识别类型分类错误

## 反思依据
{skill_doc}

## 输入数据
{context}

## 输出格式
### 问题列表
| 段落ID | 问题类型 | 原标注 | 应为 | 证据 |
|--------|---------|--------|------|------|
| ...    | ...     | ...    | ...  | ...  |

### 修正建议
- 总共发现N处问题
- 优先级分类: 高M处、中K处、低L处
```

#### 本项目实例

**事件年代反思提示词生成**:
```bash
# 生成130章年代反思提示词
python kg/events/scripts/generate_date_review_prompts.py \
  --input kg/events/data/event_index_*.json \
  --output prompts/reflect_dates/ \
  --template templates/reflect_event_dates_v2.md

# 输出:
# prompts/reflect_dates/001_五帝本纪_年代反思.md
# prompts/reflect_dates/002_夏本纪_年代反思.md
# ...
# prompts/reflect_dates/130_太史公自序_年代反思.md
```

**实体标注反思提示词生成**:
```bash
# 生成022章实体反思提示词（第三轮）
python scripts/generate_entity_review_prompts.py \
  --chapters 002-008 \
  --round 3 \
  --output prompts/reflect_entities_r3/
```

---

### 阶段2: Agent执行（Agent Execution）

#### 目标
批量调用AI Agent执行反思任务

#### 核心原则
- **并行执行**: 独立任务并行，提高效率
- **进度跟踪**: 记录执行状态，支持断点续传
- **错误处理**: API失败重试机制

#### 实现模式

**核心逻辑**:
```python
# 并行调用AI Agent → 保存反思报告 → 更新进度
for prompt_file in prompt_files:
    response = claude_api(load_file(prompt_file))
    save_report(f"reports/{chapter_id}_反思报告.md", response)
    update_progress(chapter_id, status="completed")
```

**关键技术**:
- 异步并行执行（max_concurrent=5）
- 进度跟踪（progress.json）
- 错误重试机制

**进度跟踪文件**:
```json
// progress/reflect_entities_r3.json
{
  "total": 130,
  "completed": 87,
  "failed": 2,
  "pending": 41,
  "details": {
    "002": {"status": "completed", "timestamp": "2026-03-22T10:30:00"},
    "003": {"status": "completed", "timestamp": "2026-03-22T10:31:00"},
    "005": {"status": "failed", "error": "API timeout", "retry_count": 2},
    "006": {"status": "pending"}
  }
}
```

#### 本项目实例

**事件年代五轮反思**:
```bash
# 第一轮: 基础年代检查
python scripts/batch_reflect_dates.py --round 1
# 输出: 1441处修正建议

# 第二轮: 基于第一轮修正后重新检查
python scripts/batch_reflect_dates.py --round 2
# 输出: 465处修正建议

# 第三轮: 深度验证
python scripts/batch_reflect_dates.py --round 3
# 输出: 167处修正建议

# 第四轮: 边界情况检查
python scripts/batch_reflect_dates.py --round 4
# 输出: 46处修正建议

# 第五轮: 最终验证
python scripts/batch_reflect_dates.py --round 5
# 输出: 0处新问题，收敛完成
```

**实体标注第三轮反思**:
```bash
# 批量执行002-030章反思（22章）
python scripts/batch_reflect_entities.py \
  --chapters 002-030 \
  --round 3 \
  --output doc/entities/第三轮按章实体反思/

# 输出:
# doc/entities/第三轮按章实体反思/002_夏本纪_第三轮反思报告.md
# doc/entities/第三轮按章实体反思/003_殷本纪_第三轮反思报告.md
# ...
# doc/entities/第三轮按章实体反思/030_平津侯主父列传_第三轮反思报告.md
```

---

### 阶段3: 结果审查（Report Review）

#### 目标
人工审查Agent生成的反思报告，确认修正建议的正确性

#### 核心原则
- **分级审查**: 高优先级问题优先审查
- **证据验证**: 检查修正建议的证据是否充分
- **标记决策**: 接受/拒绝/修改每条建议

#### 实现模式

**反思报告结构**:
```markdown
# 002_夏本纪_第三轮反思报告

## 反思概要
- 检查范围: 002章全文（37段落）
- 发现问题: 12处
- 问题分类:
  - 实体边界错误: 5处
  - 消歧标注缺失: 4处
  - 类型分类错误: 3处

## 问题详情

### 问题1: 实体边界错误（高优先级）
- **段落**: 002-003
- **原标注**: `〖@禹〗〖@名〗〖@鲧〗`
- **应为**: `〖@禹〗，名〖@鲧〗`（"名"不是人名实体）
- **证据**: SKILL_03c规则3.2"'名'/'字'/'姓'等身份标记词不标注"
- **人工决策**: ✅ 接受

### 问题2: 消歧标注缺失（中优先级）
- **段落**: 002-015
- **原标注**: `〖@舜〗`
- **应为**: `〖@舜|虞舜〗`（消歧，区别于"有虞氏"）
- **证据**: 全文有"有虞氏"和人名"舜"两处，需消歧
- **人工决策**: ✅ 接受

### 问题3: 类型分类错误（低优先级）
- **段落**: 002-025
- **原标注**: `〖&夏后氏&〗`
- **应为**: `〖◆夏'〗`（邦国，非氏族）
- **证据**: SKILL_03c规则2.8"朝代/诸侯国用〖◆X'〗"
- **人工决策**: ❌ 拒绝（"夏后氏"是氏族称呼，保留原标注）

## 审查结果
- 接受: 10处
- 拒绝: 2处
- 修改: 0处
- **最终修正数**: 10处

## 修正脚本
```python
# 生成修正脚本
python scripts/generate_fix_script.py \
  --report doc/entities/第三轮按章实体反思/002_夏本纪_第三轮反思报告.md \
  --output scripts/fixes/fix_002_r3.py
```
```

#### 审查工作流

```
1. 阅读反思报告 (10分钟/章)
   ↓
2. 验证证据充分性
   - 检查原文上下文
   - 对照SKILL规则
   ↓
3. 标记决策
   ✅ 接受 (正确的修正)
   ❌ 拒绝 (误判)
   ✏️ 修改 (部分正确，需调整)
   ↓
4. 生成修正脚本
   ↓
5. 更新进度跟踪
```

#### 本项目实例

**022章实体反思审查统计**:
```
第三轮反思（022章）:
- 报告总数: 22份
- 发现问题总数: 189处
- 审查时间: 5小时
- 最终接受: 99处
- 拒绝: 78处（误判）
- 修改: 12处

常见误判类型:
1. 将修饰词误判为实体边界错误 (32%)
2. 过度消歧（已有消歧但Agent未识别）(25%)
3. 类型分类的边界情况判断不一致 (20%)
```

**五轮年代反思审查**:
```
第一轮: 1441处建议 → 人工审查 → 接受1420处
第二轮: 465处建议 → 人工审查 → 接受450处
第三轮: 167处建议 → 人工审查 → 接受165处
第四轮: 46处建议 → 人工审查 → 接受46处
第五轮: 0处建议 → 收敛完成

累计修正: 2081处
误判率: 第一轮1.5% → 第五轮0% (逐轮下降)
```

---

### 阶段4: 批量应用（Batch Application）

#### 目标
将审查通过的修正建议批量应用到源文件

#### 核心原则
- **原子性**: 每个修正操作可回滚
- **幂等性**: 重复执行不会重复修改
- **可追溯**: 记录每次修改的来源和原因

#### 实现模式

**核心逻辑**:
```python
# 加载审查通过的修正 → 定位段落 → 验证原文 → 执行替换 → 记录日志
fixes = load_approved_fixes("doc/entities/第三轮按章实体反思/")
for fix in fixes:
    content = load_file(fix['file_path'])
    new_content = content.replace(fix['old'], fix['new'])
    backup_file(fix['file_path'])
    save_file(fix['file_path'], new_content)
    log_change(fix)
```

**关键原则**:
- 原子性：每个修正可回滚（备份文件）
- 幂等性：重复执行不会重复修改
- 可追溯：记录每次修改的来源（logs/fixes/）

**修正日志格式**:
```json
// logs/fixes/reflect_r3_changes.json
{
  "timestamp": "2026-03-22T15:30:00",
  "source": "reflect_entities_r3",
  "total_fixes": 99,
  "details": [
    {
      "fix_id": "002-003-01",
      "file": "chapter_md/002.tagged.md",
      "paragraph_id": "002-003",
      "old": "〖@禹〗〖@名〗〖@鲧〗",
      "new": "〖@禹〗，名〖@鲧〗",
      "reason": "实体边界错误：'名'不应标注为人名",
      "evidence": "SKILL_03c规则3.2",
      "status": "success"
    },
    // ...
  ]
}
```

#### 本项目实例

**事件年代批量修正**:
```bash
# 应用第一轮反思修正（1420处）
python scripts/apply_date_fixes.py \
  --input reports/reflect_dates_r1/ \
  --approved_list approved_fixes_r1.json \
  --output kg/events/data/

# 输出:
# ✅ 成功应用: 1418处
# ⏭️  跳过(原文已变): 2处
# ❌ 失败: 0处

# 重建事件索引
python kg/events/export_events.py
```

**实体标注批量修正**:
```bash
# 应用第三轮反思修正（99处）
python scripts/apply_entity_fixes.py \
  --chapters 002-030 \
  --round 3 \
  --dry-run  # 先预览，不实际修改

# 预览无误后执行
python scripts/apply_entity_fixes.py \
  --chapters 002-030 \
  --round 3 \
  --execute

# 验证修改
python scripts/lint_text_integrity.py chapter_md/*.tagged.md
```

---

## 三、多轮迭代策略

### 3.1 收敛判断

**收敛标准**:
```
第N轮反思发现的新问题数 < 阈值（如5%首轮问题数）
  或
连续两轮问题数下降幅度 < 10%
  或
误判率 > 50%（Agent失效，需调整提示词）
```

**本项目实例**:
```
事件年代五轮反思收敛过程:
  R1: 1441处 (基线)
  R2: 465处 (-67.7%)  ← 大幅下降，继续
  R3: 167处 (-64.1%)  ← 大幅下降，继续
  R4: 46处 (-72.5%)   ← 大幅下降，继续
  R5: 0处 (-100%)     ← 收敛完成 ✅

实体边界错误三轮反思:
  R1: 1913处 (全书130章)
  R2: 756处 (013-130章) ← 局部重审
  R3: 99处 (002-030章)  ← 针对性重审
  收敛判断: 第三轮覆盖章节仅22章，非全局收敛，但问题密度已低
```

### 3.2 提示词演化

每轮反思后根据误判类型优化提示词

**演化策略**:
```markdown
第一轮提示词:
  - 通用规则
  - 基础示例

发现问题:
  - 误判类型1: 将修饰词误判为实体边界错误

第二轮提示词优化:
  + 新增规则: "修饰词(如'大'/'小'/'东'/'西')通常不是实体边界"
  + 新增反例: 展示正确的修饰词用法

发现问题:
  - 误判类型2: 过度消歧

第三轮提示词优化:
  + 新增检查步骤: "先检查是否已有消歧标注，避免重复建议"
  + 新增消歧判断标准
```

### 3.3 分批策略

对于大规模任务，分批执行降低风险

**分批模式**:
```
策略1: 按章节顺序分批
  Batch 1: 001-010章 (10章) → 验证流程可行性
  Batch 2: 011-050章 (40章) → 扩大规模
  Batch 3: 051-130章 (80章) → 全量覆盖

策略2: 按优先级分批
  Batch 1: 本纪+世家 (30章) → 核心内容优先
  Batch 2: 列传 (70章) → 主体内容
  Batch 3: 表+书 (30章) → 次要内容

策略3: 按问题类型分批
  Batch 1: 实体边界错误 → 优先修正高频问题
  Batch 2: 消歧标注缺失 → 次优先级
  Batch 3: 类型分类错误 → 低优先级
```

---

## 四、核心优势

### 4.1 效率提升

| 维度 | 传统方式 | 批量反思管线 | 提升倍数 |
|-----|---------|-------------|---------|
| **时间成本** | 100小时 (人工逐章) | 10小时 (生成+审查) | **10x** |
| **标准一致性** | 低 (人工标准漂移) | 高 (同一提示词) | **N/A** |
| **可复现性** | 无 (难以追溯) | 完整 (全程记录) | **N/A** |
| **迭代能力** | 困难 (重复劳动) | 简单 (重新执行) | **5x** |

### 4.2 质量保障

**多重验证机制**:
```
1. Agent反思 (自动化，100%覆盖)
   ↓
2. 人工审查 (专家验证，关键决策)
   ↓
3. Lint检查 (自动化，格式验证)
   ↓
4. 多轮迭代 (收敛验证，直到问题数<阈值)
```

### 4.3 可追溯性

**完整记录链**:
```
提示词文件 → Agent输出 → 反思报告 → 审查决策 → 修正日志 → Git commit
    ↓           ↓           ↓           ↓           ↓           ↓
 可复现      可审计      可验证      可质疑      可回滚      可追溯
```

---

## 五、适用场景

### 高度适用

- ✅ **大规模文本质量审查** (100+章节/文档)
- ✅ **标注体系一致性检查** (实体/关系/事件标注)
- ✅ **数据验证和清洗** (年代/地名/人名一致性)
- ✅ **多轮迭代优化** (需要逐步提升质量)

### 中度适用

- 🟡 **中等规模文本** (10-100章节) - 效率提升不明显
- 🟡 **非结构化问题** (需要深度人类判断) - Agent能力有限

### 不适用

- ❌ **小规模文本** (<10章节) - 人工反思更快
- ❌ **一次性任务** (无需迭代) - 工程化成本高
- ❌ **完全主观判断** (如文学鉴赏) - Agent无法替代

---

## 六、与其他元技能的关系

### 关联元技能

- **← META-01 (反思)**: 批量反思管线是反思方法的工程化实现
- **← META-02 (迭代工作流)**: 多轮反思是迭代工作流的具体应用
- **← META-09 (Agent提示词工程)**: 提示词生成是提示词工程的批量化
- **→ META-10 (质量控制)**: 反思管线是质量控制的核心手段
- **→ META-18 (Lint工具链)**: Lint检查是反思管线的后验证环节

### 协同使用

**典型工作流**:
```
1. 柳叶刀方法 (META-04) 拆解反思任务
   ↓
2. 批量反思管线 (META-15) 执行反思
   ↓
3. Lint工具链 (META-18) 验证修正结果
   ↓
4. 建设逻辑留痕 (META-19) 记录反思过程
```

---

## 七、反模式（Anti-patterns）

### 反模式1: 盲目信任Agent输出

**错误做法**:
```python
# ❌ 直接应用所有Agent建议，不经人工审查
batch_apply_fixes(agent_outputs)
```

**正确做法**:
```python
# ✅ 人工审查 → 标记决策 → 批量应用
approved_fixes = human_review(agent_outputs)
batch_apply_fixes(approved_fixes)
```

**原因**: Agent误判率10-30%，直接应用会引入新错误

---

### 反模式2: 单轮反思后停止

**错误做法**:
```
第一轮反思 → 发现1000处问题 → 修正 → 结束 ✅
```

**正确做法**:
```
第一轮 → 1000处 → 修正 → 第二轮 → 300处 → 修正 → ... → 收敛
```

**原因**: 第一轮修正可能引入新问题，或第一轮提示词未覆盖所有情况

---

### 反模式3: 忽略提示词演化

**错误做法**:
```
所有轮次使用同一提示词模板
```

**正确做法**:
```
第一轮提示词 → 分析误判类型 → 优化提示词 → 第二轮
```

**原因**: 固定提示词会重复相同误判，无法收敛

---

### 反模式4: 缺乏进度跟踪

**错误做法**:
```python
# ❌ 无状态执行，失败后从头开始
for chapter in all_chapters:
    reflect_chapter(chapter)
```

**正确做法**:
```python
# ✅ 进度跟踪，支持断点续传
progress = load_progress()
pending_chapters = [c for c in all_chapters if c not in progress['completed']]
for chapter in pending_chapters:
    reflect_chapter(chapter)
    update_progress(chapter)
```

**原因**: API调用可能中断，无进度跟踪会浪费已完成工作

---

## 八、本项目应用总结

### 应用实例统计

| 反思任务 | 覆盖范围 | 轮数 | 总修正数 | 耗时 | commit链接 |
|---------|---------|-----|---------|------|-----------|
| **事件年代反思** | 130章 | 5轮 | 2119处 | 3天 | [85f39591](https://github.com/baojie/shiji-kb/commit/85f39591) |
| **实体标注第一轮** | 130章 | 1轮 | 1913处 | 2天 | [7c329904](https://github.com/baojie/shiji-kb/commit/7c329904) |
| **实体标注第二轮** | 118章 | 1轮 | 756处 | 1天 | [0cd03a76](https://github.com/baojie/shiji-kb/commit/0cd03a76) |
| **实体标注第三轮** | 22章 | 1轮 | 99处 | 0.5天 | [3ef07df0](https://github.com/baojie/shiji-kb/commit/3ef07df0) |
| **实体边界错误** | 130章 | 1轮 | 75处 | 0.5天 | [99af56d6](https://github.com/baojie/shiji-kb/commit/99af56d6) |
| **姓氏推理** | 2053人 | 6轮 | 覆盖56.6% | 1周 | [4a4255bf](https://github.com/baojie/shiji-kb/commit/4a4255bf) |

**累计效果**:
- 总修正数: **5000+处**
- 总耗时: **8天** (vs 传统方式估计100+天)
- 效率提升: **12倍以上**

### 核心脚本

| 脚本 | 功能 | 代码位置 |
|-----|------|---------|
| `generate_date_review_prompts.py` | 事件年代反思提示词生成 | `kg/events/scripts/` |
| `batch_reflect_dates.py` | 年代批量反思执行 | `scripts/` |
| `apply_date_fixes.py` | 年代修正批量应用 | `scripts/` |
| `generate_entity_review_prompts.py` | 实体反思提示词生成 | `scripts/` |
| `batch_reflect_entities.py` | 实体批量反思执行 | `scripts/` |
| `apply_entity_fixes.py` | 实体修正批量应用 | `scripts/` |

---

## 九、迁移指南

### 迁移到其他项目

**步骤1: 识别反思对象**
- 确定需要反思的单元（章节/文档/数据记录）
- 定义反思目标（质量标准/一致性要求）

**步骤2: 设计提示词模板**
```markdown
# 反思提示词模板要素

## 1. 任务定义
- 明确反思目标
- 定义问题类型

## 2. 反思依据
- 质量标准文档（类似SKILL）
- 正例和反例

## 3. 输入数据
- 待反思的文本/数据
- 上下文信息

## 4. 输出格式
- 结构化问题列表
- 修正建议格式
```

**步骤3: 开发四阶段脚本**
```bash
scripts/
├── generate_prompts.py      # 阶段1: 提示词生成
├── batch_reflect.py          # 阶段2: Agent执行
├── review_reports.py         # 阶段3: 辅助审查
└── apply_fixes.py            # 阶段4: 批量应用
```

**步骤4: 建立进度跟踪**
```json
{
  "task": "质量反思",
  "round": 1,
  "total_units": 100,
  "progress": {
    "completed": 50,
    "failed": 2,
    "pending": 48
  }
}
```

**步骤5: 执行多轮迭代**
- 第一轮: 发现基础问题
- 第二轮: 修正后验证
- 持续迭代直到收敛

---

## 十、进一步阅读

### 相关文档

- `doc/events/事件年代反思创造过程详解.md`: 五轮年代反思完整流程
- `doc/entities/第三轮按章实体反思/`: 22章实体反思报告
- `SKILL_03c_按章反思.md`: 实体反思的方法论SKILL
- `SKILL_04d_事件年代审查.md`: 年代审查的方法论SKILL

### 相关commit

- [85f39591](https://github.com/baojie/shiji-kb/commit/85f39591): 事件年代第一二轮反思
- [fe34b654](https://github.com/baojie/shiji-kb/commit/fe34b654): 事件年代第五轮反思
- [7c329904](https://github.com/baojie/shiji-kb/commit/7c329904): 实体标注第一轮反思总结
- [3ef07df0](https://github.com/baojie/shiji-kb/commit/3ef07df0): 实体标注第三轮反思（009-020章）

---

**创建日期**: 2026-03-26
**版本**: v1.0
**作者**: 基于《史记》知识库项目实践总结
