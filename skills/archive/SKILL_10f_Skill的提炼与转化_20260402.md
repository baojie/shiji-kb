---
name: skill-10f
title: Skill的提炼与转化
description: 规范化Skill的编写、工程化、质量维护流程。从Spec到可执行Skill的转化标准，脚本与Skill的关联管理，以及Skill的定期审查与优化。
---

# SKILL 10f: Skill的提炼与转化

> **核心理念**：Skill不是Spec，而是可执行的工程规范。简练、可测、可维护。

---

## 一、问题诊断

### 1.1 当前问题

我们的Skill存在以下问题：

❌ **过于冗长**：
- 部分Skill像技术文档/Spec，而非操作手册
- 大量背景说明、理论描述，缺乏直接的操作步骤
- AI Agent阅读负担重，理解成本高

❌ **缺乏工程化**：
- Skill与Script脱节，缺乏关联
- 没有可验证的检查清单
- 缺少成功/失败的明确标准

❌ **维护不足**：
- 缺少定期审查机制
- 没有质量度量标准
- 无法识别过时或冗余的Skill

### 1.2 理想状态

✅ **简练**：
- 核心内容控制在200-500行
- 开门见山，直接给出操作步骤
- 背景说明精简到最小

✅ **工程化**：
- 每个Skill关联具体的脚本/工具
- 提供可执行的检查清单
- 明确输入/输出/成功标准

✅ **可维护**：
- 定期Lint检查
- 版本化管理
- 及时清理过时内容

---

## 二、Skill编写规范

### 2.1 标准结构（模板）

```markdown
---
name: skill-XX
title: [简短标题]
description: [一句话说明：做什么，为谁服务]
version: 1.0
last_updated: YYYY-MM-DD
---

# SKILL XX: [标题]

> **核心理念**：[一句话核心原则]

---

## 一、快速开始（必需）

### 何时使用此Skill

- 场景1：[简短描述]
- 场景2：[简短描述]

### 核心步骤（3-5步）

1. **步骤1**：[动作] → [结果]
2. **步骤2**：[动作] → [结果]
3. **步骤3**：[动作] → [结果]

### 成功标准

- [ ] 标准1：[可验证]
- [ ] 标准2：[可验证]

---

## 二、详细说明（可选）

### 2.1 关键概念

[仅列出必要概念，每个不超过3行]

### 2.2 注意事项

- ❌ 禁止：[反模式]
- ✅ 推荐：[最佳实践]

---

## 三、工具与脚本（必需）

### 关联脚本

- `scripts/xxx.py` - [用途]
- `scripts/yyy.py` - [用途]

### 使用示例

```bash
# 示例1：[说明]
python scripts/xxx.py --arg value

# 示例2：[说明]
python scripts/yyy.py input.txt
```

---

## 四、检查清单（必需）

### 执行前检查

- [ ] 条件1
- [ ] 条件2

### 执行中验证

- [ ] 步骤1完成
- [ ] 步骤2完成

### 执行后验证

- [ ] 输出文件生成
- [ ] 质量指标达标

---

## 五、FAQ（可选）

### Q1: [常见问题]
**A**: [简短回答]

### Q2: [常见问题]
**A**: [简短回答]

---

## 附录：关联文档（可选）

- 相关Skill：`SKILL_XX.md`
- 参考文档：`docs/xxx.md`
```

### 2.2 三级命名规范

**设计理念**：扁平化目录结构，便于人类理解，无需翻阅多层文件夹。

#### 命名层级

```
skills/
├── SKILL_03_实体构建.md              # 第一级：工作阶段总览
├── SKILL_03a_实体标注.md             # 第二级：具体工作步骤
├── SKILL_03b_人名消歧.md             # 第二级：具体工作步骤
└── references/
    ├── SKILL_03a1_标注规则库.md      # 第三级：步骤的具体规则/数据
    └── SKILL_03a2_实体类型定义.md    # 第三级：步骤的具体规则/数据
```

**层级说明**：

| 层级 | 命名格式 | 位置 | 用途 | 示例 |
|------|---------|------|------|------|
| **一级** | `SKILL_XX_工作名` | `skills/` | 阶段总览，串联流程 | `SKILL_03_实体构建.md` |
| **二级** | `SKILL_XXa_步骤名` | `skills/` | 具体操作步骤，可独立执行 | `SKILL_03a_实体标注.md` |
| **三级** | `SKILL_XXa1_规则名` | `skills/references/` | 规则库、词表、配置数据 | `SKILL_03a1_标注规则库.md` |

#### 与Anthropic官方结构的差异

**Anthropic标准结构**（多层嵌套）：
```
skills/
├── entity-construction/
│   ├── skill.md              # 总览
│   ├── annotation/
│   │   ├── skill.md          # 标注步骤
│   │   └── rules/
│   │       └── types.md      # 规则库
│   └── disambiguation/
│       └── skill.md          # 消歧步骤
```

**本项目结构**（扁平化）：
```
skills/
├── SKILL_03_实体构建.md       # 总览
├── SKILL_03a_实体标注.md      # 标注步骤
├── SKILL_03b_人名消歧.md      # 消歧步骤
└── references/
    └── SKILL_03a1_标注规则库.md  # 规则库
```

**为什么不用官方结构**：

✅ **扁平化优势**：
- 人类阅读更友好：无需在多层目录中跳转
- 文件名即层级：`SKILL_03a` 清楚表示属于 `SKILL_03`
- 引用路径简洁：`[SKILL_03a](SKILL_03a_实体标注.md)` vs `[annotation](entity-construction/annotation/skill.md)`
- IDE搜索高效：直接搜索 `SKILL_03` 即可找到所有相关文件

❌ **嵌套结构劣势**：
- 需要频繁切换目录
- 文件名缺乏上下文（多个 `skill.md` 难以区分）
- 引用路径冗长

#### 拆分与精简策略

当Skill超过500行时，按三级命名拆分：

**示例：SKILL_03a_实体标注（原1200行）**

拆分前：
```markdown
# SKILL_03a 实体标注

## 一、标注规范（300行）
[18类实体定义、标注语法...]

## 二、操作流程（200行）
[步骤1-8详细说明...]

## 三、规则库（500行）
[人名规则、地名规则、官职规则...]

## 四、案例库（200行）
[案例1-50...]
```

拆分后：
```markdown
# SKILL_03a 实体标注（主文件，300行）
→ 快速开始 + 核心流程 + 工具使用

references/SKILL_03a1_实体类型定义.md（200行）
→ 18类实体的详细定义和边界判定

references/SKILL_03a2_标注规则库.md（500行）
→ 按类型组织的详细标注规则

labs/examples/SKILL_03a_cases.md（200行）
→ 50个典型案例和边界情况
```

**拆分检查清单**：

执行前：
- [ ] 原Skill超过500行
- [ ] 有明确的规则库/数据部分（>100行）
- [ ] 有大量案例/示例（>100行）

执行中：
- [ ] 主文件保留核心流程（<300行）
- [ ] 规则库移至 `references/SKILL_XXa1_`
- [ ] 案例库移至 `labs/examples/`
- [ ] 更新主文件的引用链接

执行后：
- [ ] 主文件独立可读（不依赖规则库即可理解流程）
- [ ] 规则库独立可查（可作为工具文档使用）
- [ ] 所有链接有效

#### 命名约定

**数字编号规则**：

```
SKILL_03_实体构建           # 一级：两位数（01-99）
  ├─ SKILL_03a_实体标注     # 二级：字母后缀（a-z）
  ├─ SKILL_03b_人名消歧     # 二级：字母后缀（a-z）
  │   └─ references/SKILL_03b1_消歧规则库   # 三级：字母+数字（a1-z9）
  └─ SKILL_03c_按章反思     # 二级：字母后缀（a-z）
```

**文件名要求**：

- ✅ 使用下划线分隔：`SKILL_03a_实体标注.md`
- ✅ 中文标题：便于人类理解
- ✅ 编号连续：`03a`, `03b`, `03c`（不跳号）
- ❌ 不使用驼峰：`SKILL_03a实体标注.md`
- ❌ 不使用中划线：`SKILL-03a-实体标注.md`

**一级Skill命名模式**：

- 阶段型：`SKILL_03_实体构建`（适用于流程性工作）
- 工具型：`SKILL_10a_Git代码版本管理规范`（适用于横向支撑）
- 主题型：`SKILL_04_关系构建`（适用于知识领域）

**二级Skill命名模式**：

- 动作型：`SKILL_03a_实体标注`（强调操作）
- 对象型：`SKILL_03b_人名消歧`（强调处理对象）
- 方法型：`SKILL_03c_按章反思`（强调方法论）

**三级规则库命名模式**：

- 规则库：`SKILL_03a1_标注规则库`
- 词表：`SKILL_03a2_实体类型定义`
- 配置：`SKILL_03a3_标注配置`

---

### 2.4 长度控制

| 内容类型 | 推荐长度 | 最大长度 |
|---------|---------|---------|
| 快速开始 | 30-50行 | 100行 |
| 详细说明 | 50-100行 | 200行 |
| 工具与脚本 | 20-30行 | 50行 |
| 检查清单 | 10-20行 | 30行 |
| FAQ | 20-50行 | 100行 |
| **总计** | **200-300行** | **500行** |

**超过500行的Skill**：
- 考虑拆分为多个子Skill（参见[2.2节三级命名规范](#22-三级命名规范)）
- 将详细案例移至 `labs/examples/`
- 将背景理论移至 `docs/theory/`

### 2.5 写作原则

#### 原则1：开门见山

❌ **错误示例**：
```markdown
## 背景
本体是知识工程的重要组成部分，源自哲学中的概念...
[200行背景介绍]

## 操作步骤
1. 打开文件...
```

✅ **正确示例**：
```markdown
## 快速开始

### 核心步骤
1. 打开文件
2. 执行标注
3. 验证结果

### 详细背景（可选）
[精简到50行内]
```

#### 原则2：可执行优先

每个步骤必须是**可直接执行的动作**：

| 类型 | 示例 |
|-----|------|
| ✅ 可执行 | "运行 `python scripts/lint.py`" |
| ✅ 可执行 | "打开文件 `chapter_md/001.md`" |
| ❌ 不可执行 | "确保数据质量" |
| ❌ 不可执行 | "理解本体结构" |

#### 原则3：检查清单必需

每个Skill必须包含：
- **执行前检查**：环境、依赖、前置条件
- **执行中验证**：关键步骤完成标志
- **执行后验证**：输出质量、成功标准

---

## 三、Skill工程化

### 3.1 Skill与脚本关联

每个Skill应关联具体的脚本/工具，形成闭环：

```
SKILL_01_古籍校勘.md
    ├─ scripts/validation/lint_text_integrity.py
    ├─ scripts/curation/compare_versions.py
    └─ scripts/curation/generate_collation_report.py

SKILL_03a_实体标注.md
    ├─ scripts/validation/validate_entities.py
    ├─ scripts/generation/entity_stats.py
    └─ scripts/reflection/entity_boundary_check.py
```

**Skill中应明确列出**：
```markdown
## 工具与脚本

### 校验工具
- `scripts/validation/lint_text_integrity.py` - 检查文本完整性
  - 输入：`.tagged.md` 文件
  - 输出：错误报告（如有）
  - 用法：`python scripts/validation/lint_text_integrity.py chapter_md/001*.md`

### 统计工具
- `scripts/generation/entity_stats.py` - 生成实体统计报告
  - 输入：`.tagged.md` 文件
  - 输出：JSON统计数据
  - 用法：`python scripts/generation/entity_stats.py --all`
```

### 3.2 脚本组织规范

脚本应按功能分组，便于Skill引用：

```
scripts/
├── validation/       # 校验脚本（对应Skill检查清单）
│   ├── lint_*.py
│   └── validate_*.py
├── generation/       # 生成脚本（对应Skill输出）
│   ├── generate_*.py
│   └── export_*.py
├── conversion/       # 转换脚本（对应Skill数据处理）
│   ├── convert_*.py
│   └── transform_*.py
└── reflection/       # 反思脚本（对应Skill质量检查）
    ├── check_*.py
    └── review_*.py
```

**命名规范**：
- `lint_*.py` - 静态检查，不修改文件
- `validate_*.py` - 验证数据格式/约束
- `generate_*.py` - 生成报告/统计
- `convert_*.py` - 转换数据格式
- `check_*.py` - 深度检查（可能需要AI）
- `fix_*.py` - 自动修复问题

### 3.3 脚本分解策略

**大型Skill应拆解为多个小脚本**：

❌ **反模式**：一个3000行的 `process_all.py`
```python
# 反模式：all-in-one脚本
def process_all(chapter):
    # 200行：读取文件
    # 500行：实体标注
    # 300行：格式转换
    # 400行：生成报告
    # 600行：质量检查
    ...
```

✅ **最佳实践**：拆分为独立脚本
```
scripts/
├── validation/
│   ├── lint_entities.py          # 100行：实体格式检查
│   └── validate_entity_types.py  # 80行：实体类型验证
├── generation/
│   ├── generate_entity_stats.py  # 120行：统计生成
│   └── export_to_json.py         # 90行：JSON导出
└── reflection/
    ├── check_entity_boundaries.py  # 150行：边界检查
    └── review_entity_coverage.py   # 130行：覆盖率审查
```

**拆分标准**：
- 每个脚本不超过300行
- 单一职责（只做一件事）
- 可独立运行
- 清晰的输入/输出

---

## 四、Skill质量标准

### 4.1 Lint检查项

创建 `scripts/lint_skills.py`，定期检查：

```python
def lint_skill(skill_file):
    """检查Skill质量"""
    checks = [
        # 结构检查
        has_frontmatter(),        # 是否有YAML frontmatter
        has_quick_start(),        # 是否有"快速开始"章节
        has_tools_section(),      # 是否有"工具与脚本"章节
        has_checklist(),          # 是否有检查清单

        # 长度检查
        total_lines() < 600,      # 总行数不超过600
        quick_start_lines() < 150,  # 快速开始不超过150行

        # 链接检查
        all_script_links_valid(), # 脚本路径是否存在
        all_skill_refs_valid(),   # 引用的Skill是否存在

        # 内容检查
        has_success_criteria(),   # 是否有明确的成功标准
        has_examples(),           # 是否有使用示例
        no_broken_links(),        # 无失效链接
    ]
    return all(checks)
```

### 4.2 质量度量

每个Skill应定期评估：

| 指标 | 计算方式 | 目标值 |
|-----|---------|-------|
| 可读性 | Flesch Reading Ease（中文适配） | > 60 |
| 完整性 | 必需章节齐全率 | 100% |
| 有效性 | 关联脚本存在率 | 100% |
| 实用性 | 最近30天引用次数 | > 5 |
| 时效性 | 距上次更新天数 | < 90 |

### 4.3 定期审查机制

**月度审查**（每月1日）：
```bash
# 生成Skill健康度报告
python scripts/lint_skills.py --report monthly

# 输出示例：
# SKILL_01_古籍校勘.md - ✅ PASS (score: 95/100)
# SKILL_03a_实体标注.md - ⚠️  WARN (长度超标: 620行)
# SKILL_10c_Git规范.md - ✅ PASS (score: 100/100)
# SKILL_XX_过时技术.md - ❌ FAIL (90天未更新，0次引用)
```

**季度审查**（每季度末）：
- 识别过时Skill（90天未更新 + 引用次数<3）
- 识别冗余Skill（内容重复度>70%）
- 更新Skill依赖关系图

---

## 五、从Spec到Skill的转化流程

### 5.1 转化标准

| 转化前（Spec） | 转化后（Skill） |
|--------------|---------------|
| 长篇理论说明 | 精简到50行内，移至附录 |
| 案例分析 | 提炼为3-5个典型示例 |
| 多种方案对比 | 推荐最佳方案，其他方案移至FAQ |
| 大段代码 | 提取为独立脚本，Skill中只保留调用示例 |
| 背景知识 | 移至 `docs/theory/` 或外部链接 |

### 5.2 转化步骤

**步骤1：提取核心流程**
```markdown
# 从Spec中识别关键步骤
原Spec: [1000行文档]
↓
核心流程:
1. 准备数据
2. 执行标注
3. 验证结果
4. 生成报告
```

**步骤2：识别可脚本化部分**
```markdown
# 哪些步骤可以自动化？
步骤1: 准备数据 → scripts/prepare_data.py
步骤3: 验证结果 → scripts/validation/validate_output.py
步骤4: 生成报告 → scripts/generation/generate_report.py
```

**步骤3：编写Skill骨架**
```markdown
# 使用标准模板
## 快速开始
[核心流程]

## 工具与脚本
[关联脚本列表]

## 检查清单
[验证标准]
```

**步骤4：脚本开发**
```bash
# 开发关联脚本
scripts/
├── prepare_data.py         # 新建
├── validation/
│   └── validate_output.py  # 新建
└── generation/
    └── generate_report.py  # 新建
```

**步骤5：验证与优化**
```bash
# 实际执行一遍流程
python scripts/prepare_data.py
[手动步骤2]
python scripts/validation/validate_output.py
python scripts/generation/generate_report.py

# 根据执行情况优化Skill
```

### 5.3 转化示例

**转化前（Spec风格）**：
```markdown
# 实体标注规范（1200行）

## 背景
实体标注是NLP领域的重要任务...
[300行理论]

## 标注体系设计
我们采用多层次标注体系...
[400行设计思路]

## 标注流程
[200行详细说明]

## 案例分析
案例1: 人名标注
[100行案例]
案例2: 地名标注
[100行案例]
...
```

**转化后（Skill风格）**：
```markdown
# SKILL 03a: 实体标注（350行）

## 快速开始

### 核心步骤
1. 运行预标注：`python scripts/pre_annotate.py chapter_md/001*.md`
2. 人工审查：使用IDE打开文件，修正错误
3. 验证格式：`python scripts/validation/lint_entities.py chapter_md/001*.md`
4. 生成统计：`python scripts/generation/entity_stats.py chapter_md/001*.md`

### 成功标准
- [ ] 所有实体符合格式规范
- [ ] 覆盖率 > 95%
- [ ] 人工审查通过

---

## 工具与脚本

### 预标注
- `scripts/pre_annotate.py` - 自动预标注人名、地名
  - 输入：`.md` 文件
  - 输出：`.tagged.md` 文件
  - 准确率：~85%（需人工审查）

### 验证
- `scripts/validation/lint_entities.py` - 格式检查
  - 检查：括号匹配、类型有效性、嵌套错误

### 统计
- `scripts/generation/entity_stats.py` - 统计报告
  - 输出：各类实体数量、覆盖率、分布图

---

## 检查清单
[...]

---

## 附录

### 标注体系
[精简到100行]

### 典型案例
[3个代表性示例，各20行]

### 详细理论
参考：`docs/theory/entity_annotation.md`
```

---

## 六、Skill精简与拆分

### 6.1 何时需要精简

**触发条件**（满足任一即需精简）：

- [ ] Skill文件超过800行
- [ ] 代码示例超过200行（>15%篇幅）
- [ ] 详细配置说明超过100行
- [ ] 扩展FAQ或学术资源超过50行
- [ ] 用户反馈"太长，找不到重点"

### 6.2 精简诊断

**步骤1：内容分布分析**

使用脚本分析各章节行数和代码占比：

```python
import re

def analyze_skill_content(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    sections = {}
    current_section = "header"
    code_block = False
    code_lines = 0

    for i, line in enumerate(lines, 1):
        if line.strip().startswith('```'):
            code_block = not code_block
        if code_block:
            code_lines += 1
            sections.setdefault(current_section, {'total': 0, 'code': 0})
            sections[current_section]['code'] += 1

        if line.startswith('##'):
            current_section = line.strip('#').strip()
            sections.setdefault(current_section, {'total': 0, 'code': 0})

        sections.setdefault(current_section, {'total': 0, 'code': 0})
        sections[current_section]['total'] += 1

    print(f"总行数: {len(lines)}")
    print(f"代码行数: {code_lines} ({code_lines/len(lines)*100:.1f}%)\n")

    for section, stats in sorted(sections.items(), key=lambda x: x[1]['total'], reverse=True):
        print(f"{section[:50]:50s} | 总: {stats['total']:4d} | 代码: {stats['code']:4d}")
```

**步骤2：识别可拆分内容**

| 内容类型 | 判断标准 | 处理方式 |
|---------|---------|---------|
| **代码示例** | >20行的完整函数 | → `references/SKILL_XX_code_examples.md` |
| **背景知识** | 理论、历史、方案对比 | → `references/SKILL_XX_background.md` |
| **详细配置** | 环境setup、工具配置 | → `references/SKILL_XX_background.md` |
| **扩展FAQ** | 深入讨论、多案例对比 | → `references/SKILL_XX_background.md` |
| **模板** | 提示词、文档模板 | → `references/SKILL_XX_templates.md` |
| **详细规则** | 大型词表、映射表 | → `references/SKILL_XX_rules.md` |

### 6.3 拆分流程

**步骤1：备份原文件**

```bash
cp skills/SKILL_XX.md skills/SKILL_XX.md.backup
```

**步骤2：创建拆分文档**

在 `skills/references/` 目录创建扁平结构的拆分文档：

```bash
# 创建代码示例文档
touch skills/references/SKILL_XX_code_examples.md

# 创建背景信息文档
touch skills/references/SKILL_XX_background.md
```

**命名规范**：
- `SKILL_{ID}_{suffix}.md`
- 常用后缀：`code_examples`, `background`, `templates`, `rules`
- **扁平结构**：直接放在 `references/` 下，不建子目录

**步骤3：编写拆分文档结构**

```markdown
# SKILL XX - 代码示例参考

本文档包含 SKILL_XX 中提到的详细代码示例。

## 目录

- [功能A代码](#功能a代码)
- [功能B代码](#功能b代码)

---

## 功能A代码

### Python实现

\```python
# 详细代码
\```

---

## 相关文档

- [SKILL_XX.md](../SKILL_XX.md) - 主文档
- [SKILL_XX_background.md](./SKILL_XX_background.md) - 背景信息
```

**步骤4：精简主文档**

**4.1 删除详细代码，保留引用**

```markdown
<!-- 精简前 -->
### API使用方法

\```python
import requests

def call_api(text: str) -> str:
    """调用API"""
    url = "https://example.com/api"
    payload = {"text": text}
    response = requests.post(url, json=payload)
    return response.json()["result"]
\```

<!-- 精简后 -->
### API使用方法

**技术方案**：推荐使用XX API - 准确率92-99%

**代码示例**：参见 [references/SKILL_XX_code_examples.md - API调用](./references/SKILL_XX_code_examples.md#api调用)
```

**4.2 精简冗长输出，保留关键行**

```markdown
<!-- 精简前 -->
# 输出示例：
# 📁 找到 130 个文件
# ✅ 001_文件.md
#    修复 34 处错误
#    - 行95: 2处
#    - 行102: 5处
#    ... (省略100行)
# 📊 修复完成: 修复文件数 125, 修复总数 14955

<!-- 精简后 -->
# 输出示例：
# ✅ 001_文件.md
#    修复 34 处错误
# 📊 修复完成: 125个文件，14955处
```

**4.3 压缩FAQ，链接到详细说明**

```markdown
<!-- 精简前 -->
### Q: 详细问题？

**答案**：详细回答...

**配置示例**：
\```json
{ "config": "value" }
\```
... (省略40行)

<!-- 精简后 -->
### Q: 详细问题？

**答案**：简短回答（1-2句）

**详细说明**：参见 [references/SKILL_XX_background.md - 详细问题](./references/SKILL_XX_background.md#详细问题)
```

**步骤5：更新链接**

确保所有拆分文档之间的链接正确：

```markdown
# 主文档 → references
[references/SKILL_XX_code_examples.md](./references/SKILL_XX_code_examples.md)

# references → 主文档
[SKILL_XX.md](../SKILL_XX.md)

# references之间互相引用
[SKILL_XX_background.md](./SKILL_XX_background.md)
```

**步骤6：验证完整性**

```bash
# 1. 检查行数减少
wc -l skills/SKILL_XX.md.backup skills/SKILL_XX.md

# 2. 检查章节结构完整
grep "^## " skills/SKILL_XX.md

# 3. 检查引用链接数量
grep -c "references/SKILL_XX_" skills/SKILL_XX.md

# 4. 验证核心内容未丢失
required_sections=("快速开始" "核心步骤" "成功标准")
for section in "${required_sections[@]}"; do
    grep -q "$section" skills/SKILL_XX.md || echo "Missing: $section"
done
```

### 6.4 拆分质量标准

**主文档要求**：

- [ ] **长度**：控制在600-700行以内
- [ ] **结构完整**：快速开始、规范、流程、工具、示例、FAQ、相关文档
- [ ] **代码少**：Python代码块≤3个（仅配置示例）
- [ ] **链接充足**：至少10处引用到references文档
- [ ] **自包含**：不查阅references也能理解核心规范

**拆分文档要求**：

- [ ] **独立性**：可以单独阅读，不依赖主文档上下文
- [ ] **完整性**：包含标题、目录、章节、相关文档链接
- [ ] **互链性**：与主文档、其他拆分文档互相链接
- [ ] **命名规范**：遵循 `SKILL_{ID}_{suffix}.md`
- [ ] **位置规范**：放在 `skills/references/` 目录，扁平结构

### 6.5 常见错误与避免

**错误1：过度拆分**

❌ **症状**：主文档变成目录索引，失去自包含性

✅ **避免**：
- 保留核心规范表格（如标点符号对照表）
- 保留基本原则和判断标准
- 保留简洁的工作流程（5-10行命令）

**错误2：目录结构混乱**

❌ **错误**：
```
✗ skills/SKILL_01f/code_examples.md
✗ labs/references/SKILL_01f/code_examples.md
```

✅ **正确**：
```
✓ skills/references/SKILL_01f_code_examples.md
```

**错误3：内容重复**

❌ **症状**：同一内容在主文档和references都有

✅ **避免**：
- 主文档：简短回答 + 链接
- References：详细说明
- 绝对不要两处都保留完整内容

### 6.6 实际案例：SKILL_01f

**拆分前分析**：
```
总行数: 1297
代码行数: 564 (43.5%)

各章节行数分布（Top 5）:
示例3：批量修复半角符号      140行 (107行代码)
Q7: Windows换行符问题        51行
2.1a 换行符规范             47行
4.2 反思提示词模板           43行
3.2 gj.cool API使用         42行
```

**拆分决策**：
| 内容 | 行数 | 决策 | 去向 |
|-----|------|------|------|
| gj.cool API代码 | 29行 | 移除 | code_examples.md |
| 本地模型代码 | 32行 | 移除 | code_examples.md |
| 反思提示词 | 23行 | 移除 | code_examples.md |
| Windows换行符FAQ | 51行 | 移除 | background.md |
| gj.cool准确率评估 | 16行 | 移除 | background.md |
| 示例3详细输出 | 107行 | 精简到40行 | 主文档保留关键步骤 |

**拆分结果**：
```
✓ 主文档：1297行 → 475行（减少63.4%）
✓ code_examples.md：250行（代码示例 + 模板）
✓ background.md：331行（背景 + 扩展FAQ + 学术资源）
✓ 引用链接：14处
✓ 核心章节：9个，全部保留
```

**详细方法论**：参见 `logs/skill_splitting_methodology_20260402.md`

---

## 七、工作流程

### 7.1 新建Skill

```bash
# 1. 使用模板创建
cp skills/templates/SKILL_template.md skills/SKILL_XX_新功能.md

# 2. 填写frontmatter
vim skills/SKILL_XX_新功能.md

# 3. 编写核心步骤（快速开始章节）

# 4. 开发关联脚本
mkdir -p scripts/xxx
touch scripts/xxx/main.py

# 5. 编写检查清单

# 6. 测试执行流程（完整走一遍）

# 7. Lint检查
python scripts/lint_skills.py skills/SKILL_XX_新功能.md

# 8. 提交
git add skills/SKILL_XX_新功能.md scripts/xxx/
git commit -m "新增SKILL XX: 新功能"
```

### 7.2 重构Skill

```bash
# 1. 评估现有Skill
python scripts/lint_skills.py skills/SKILL_03a_实体标注.md

# 2. 识别问题
# - 长度：620行（超标）
# - 缺少关联脚本
# - 检查清单不完整

# 3. 提取脚本
# 将大段代码提取为 scripts/xxx.py

# 4. 精简内容
# - 背景理论移至 docs/theory/
# - 案例移至 labs/examples/
# - 保留核心流程

# 5. 验证
python scripts/lint_skills.py skills/SKILL_03a_实体标注.md

# 6. 提交
git add skills/SKILL_03a_实体标注.md scripts/ docs/
git commit -m "重构SKILL 03a: 精简至350行，新增3个关联脚本"
```

### 7.3 废弃Skill

```bash
# 1. 确认废弃原因
# - 90天未更新
# - 0次引用
# - 或被其他Skill替代

# 2. 检查依赖
grep -r "SKILL_XX" skills/

# 3. 移至archive
mkdir -p archive/skills/
git mv skills/SKILL_XX_过时技术.md archive/skills/
echo "废弃原因：被SKILL_YY替代" > archive/skills/SKILL_XX_废弃说明.txt

# 4. 更新关联文档
# 在其他Skill中移除对SKILL_XX的引用

# 5. 提交
git commit -m "废弃SKILL XX: 已被SKILL YY替代"
```

---

## 八、检查清单

### Skill编写检查

- [ ] 包含YAML frontmatter（name, title, description）
- [ ] 包含"快速开始"章节（核心步骤+成功标准）
- [ ] 包含"工具与脚本"章节（至少1个关联脚本）
- [ ] 包含"检查清单"章节（执行前/中/后）
- [ ] 总长度不超过600行
- [ ] 所有脚本路径有效
- [ ] 所有Skill引用有效
- [ ] 至少1个使用示例
- [ ] 明确的成功标准

### 脚本开发检查

- [ ] 脚本文件存在且可执行
- [ ] 有清晰的docstring（功能、输入、输出）
- [ ] 有使用示例（`--help` 或脚本开头注释）
- [ ] 单一职责（不超过300行）
- [ ] 有错误处理
- [ ] 有日志输出
- [ ] 在Skill中被引用

### 定期维护检查

- [ ] 月度Lint通过
- [ ] 近30天有引用记录
- [ ] 关联脚本可正常运行
- [ ] 无失效链接
- [ ] 无过时内容

---

## 九、示例：脚本分解

### 示例1：大型标注脚本拆分

**原始脚本**（`annotate_all.py`, 800行）：
```python
def annotate_all(chapter):
    # 读取文件（100行）
    # 人名标注（200行）
    # 地名标注（150行）
    # 时间标注（120行）
    # 格式验证（100行）
    # 生成报告（130行）
```

**拆分后**：
```
scripts/annotation/
├── pre_annotate_person.py     # 200行：人名预标注
├── pre_annotate_place.py      # 150行：地名预标注
├── pre_annotate_time.py       # 120行：时间预标注
├── validation/
│   └── validate_format.py     # 100行：格式验证
└── generation/
    └── annotation_report.py   # 130行：报告生成

# 工作流脚本（orchestration）
scripts/workflows/
└── annotate_chapter.sh        # 30行：调用上述脚本
```

**Skill中引用**：
```markdown
## 工具与脚本

### 完整流程
```bash
# 一键执行完整标注流程
bash scripts/workflows/annotate_chapter.sh chapter_md/001*.md
```

### 单步执行
```bash
# 步骤1: 人名预标注
python scripts/annotation/pre_annotate_person.py chapter_md/001*.md

# 步骤2: 地名预标注
python scripts/annotation/pre_annotate_place.py chapter_md/001*.md

# 步骤3: 时间预标注
python scripts/annotation/pre_annotate_time.py chapter_md/001*.md

# 步骤4: 验证格式
python scripts/validation/validate_format.py chapter_md/001*.tagged.md

# 步骤5: 生成报告
python scripts/generation/annotation_report.py chapter_md/001*.tagged.md
```
```

---

## 十、FAQ

### Q1: 什么时候需要创建新Skill？

**A**: 满足以下任一条件：
- 有完整的工作流程（3步以上）
- 需要多次重复执行
- 有明确的输入/输出
- 涉及多个工具/脚本

**不需要**创建Skill的情况：
- 一次性任务（放在 `labs/`）
- 简单的单步操作（写在README中）
- 纯理论说明（写在 `docs/theory/`）

### Q2: Skill与脚本的关系是什么？

**A**:
- **Skill是流程规范**：定义"做什么、怎么做、检查什么"
- **脚本是工具**：自动化Skill中的可编程步骤
- **关系**：Skill引用脚本，脚本支撑Skill

一个Skill可以引用多个脚本，一个脚本也可以被多个Skill引用。

### Q3: 如何判断Skill是否需要重构？

**A**: 出现以下信号时考虑重构：
- 长度超过600行
- 最近30天引用次数<3
- 关联脚本失效
- 内容与其他Skill重复>50%
- 有用户反馈"难以理解"

### Q4: Skill与文档的区别？

**A**:
| 类型 | 目标读者 | 内容 | 位置 |
|-----|---------|------|------|
| Skill | AI Agent + 开发者 | 可执行的操作规范 | `skills/` |
| 用户文档 | 终端用户 | 功能说明、使用指南 | `docs/` |
| 理论文档 | 研究者 | 背景、设计思路 | `docs/theory/` |
| 工作日志 | 项目组内部 | 进度、问题记录 | `logs/` |

---

## 十一、Skill的更新与维护

### 11.1 何时需要更新Skill

**触发条件**（满足任一即需更新）：

- [ ] **数据规模变化**：实体数量、章节覆盖率等统计数据有显著变化（>10%）
- [ ] **文件路径变更**：引用的文件/目录被重命名或移动
- [ ] **脚本逻辑更新**：关联脚本的输入输出格式发生变化
- [ ] **工具链升级**：新增或替换了关键工具
- [ ] **过时内容**：文档中提到的版本号、日期、状态描述不符合当前实际
- [ ] **用户反馈**：有明确的错误报告或改进建议

### 11.2 更新流程（标准化）

#### 步骤1：触发更新

```bash
# 场景：文件重命名触发更新需求
git mv skills/SKILL_03b_实体消歧.md skills/SKILL_03b_人名消歧.md
# → 需要更新所有引用此文件的地方
```

#### 步骤2：全面检查需要更新的内容

使用系统化的检查清单：

**2.1 统计数据检查**
```bash
# 检查Skill中的数字是否过时
grep -n "条\|个\|章\|组" skills/SKILL_XX.md | head -20

# 验证实际数据
python3 << 'EOF'
import json
# 读取实际数据文件，统计当前数字
with open('kg/entities/data/entity_index.json') as f:
    data = json.load(f)
    print(f"实体数: {len(data.get('person', []))}")
# ...
EOF
```

**2.2 文件路径检查**
```bash
# 检查Skill中引用的所有文件路径
grep -n "\.md\|\.json\|\.py\|\.csv" skills/SKILL_XX.md

# 验证路径是否存在
for path in $(grep -o "[a-z/]*/[a-zA-Z_]*.md" skills/SKILL_XX.md); do
    [ -f "$path" ] || echo "Missing: $path"
done
```

**2.3 脚本逻辑检查**
```bash
# 检查Skill中提到的脚本
grep -n "scripts/" skills/SKILL_XX.md

# 验证脚本的docstring与Skill描述一致
head -20 scripts/xxx/yyy.py
```

**2.4 索引文件检查**
```bash
# 检查是否需要更新索引文件
grep "SKILL_XX" skills/INDEX.md
grep "SKILL_XX" skills/SKILL_00_管线总览.md
grep "SKILL_XX" skills/SKILL_YY_相关技能.md
```

**2.5 引用脚本检查**
```bash
# 检查哪些脚本引用了这个Skill
grep -r "SKILL_XX" scripts/
```

#### 步骤3：批量更新

**3.1 更新统计数据**

示例（基于SKILL_03b的实际更新）：

```markdown
<!-- 更新前 -->
人名实体数 | 3,797条
全部实体数 | （未记录）
别名组 | 586组
君主数据 | 651条

<!-- 更新后 -->
人名实体数 | 4,418条 (+621, +16.4%)
全部实体数 | 17,483条（19类）
别名关系数 | 591条（11个分类）
君主数据 | 656条 (+5)
```

**关键点**：
- ✅ 使用实际脚本统计，不手动猜测
- ✅ 更新所有相关数字（摘要、章节、表格）
- ✅ 保持数字格式一致（千位分隔符、单位）

**3.2 更新文件路径**

```bash
# 批量替换文件名引用
sed -i 's/SKILL_03b_实体消歧.md/SKILL_03b_人名消歧.md/g' \
    skills/INDEX.md \
    skills/SKILL_00_管线总览.md \
    skills/SKILL_03_实体构建.md

# 更新子目录引用
# 错误: doc/entities/史记君主列表整理过程.md
# 正确: doc/entities/特殊任务/史记君主列表整理过程.md
```

**3.3 更新脚本引用**

检查脚本中硬编码的Skill名称：

```python
# scripts/update_skill_frontmatter.py
DESCRIPTIONS = {
    "SKILL_03b_实体消歧.md": "...",  # ← 需要更新为 SKILL_03b_人名消歧.md
}
```

**3.4 更新版本说明**

在Skill末尾更新变更日志：

```markdown
*最后更新：2026-04-02*
*v1.3 更新内容：*
- 统计数据：人名实体 3,797 → 4,418条，全部实体新增统计（17,483条）
- 君主数据：651 → 656条
- 文件路径：修正 doc/entities/ 子目录结构
- 文件重命名：实体消歧 → 人名消歧
```

#### 步骤4：验证完整性

**4.1 链接验证**
```bash
# 检查所有Markdown链接是否有效
python scripts/check_markdown_links.py skills/SKILL_XX.md
# 或手动检查
for link in $(grep -o "\[.*\](.*\.md)" skills/SKILL_XX.md | sed 's/.*(\(.*\))/\1/'); do
    [ -f "skills/$link" ] || [ -f "$link" ] || echo "Broken: $link"
done
```

**4.2 数字一致性验证**
```bash
# 检查同一数字在不同位置是否一致
# 例如："4418" 应该在摘要、表格、描述中出现多次
grep -n "4418\|4,418" skills/SKILL_XX.md
# 确保所有出现都已更新
```

**4.3 格式一致性**
```bash
# 检查格式规范
# - 千位分隔符：4,418 vs 4418
# - 单位统一：条/个/章
# - 日期格式：YYYY-MM-DD
```

#### 步骤5：更新检查清单

```markdown
### Skill更新检查清单

执行前：
- [ ] 确认更新触发条件（数据变化/路径变更/脚本升级）
- [ ] 备份原文件（`cp SKILL_XX.md SKILL_XX.md.backup`）
- [ ] 读取实际数据文件，获取准确统计

执行中：
- [ ] 更新所有统计数字（摘要、章节、表格）
- [ ] 更新所有文件路径（绝对路径、相对路径、子目录）
- [ ] 更新所有索引文件引用（INDEX.md、管线总览、相关Skill）
- [ ] 更新脚本中的硬编码引用
- [ ] 更新版本说明和日期

执行后：
- [ ] 验证所有Markdown链接有效
- [ ] 验证数字在多处出现的一致性
- [ ] 验证格式统一（千位分隔符、单位、日期）
- [ ] 运行 `git diff` 检查改动范围
- [ ] 暂存所有相关文件
```

### 11.3 更新示例：SKILL_03b人名消歧

**背景**：文件重命名 + 数据规模增长

**触发条件**：
1. 文件重命名：`SKILL_03b_实体消歧.md` → `SKILL_03b_人名消歧.md`
2. 统计数据过时：人名实体数从3,797增长到4,418

**执行过程**：

```bash
# 1. 重命名文件
git mv skills/SKILL_03b_实体消歧.md skills/SKILL_03b_人名消歧.md

# 2. 更新frontmatter
# 标题：古籍人名消歧 → 人名消歧
# 描述：〖PER 显示名|规范名〗 → 〖@显示名|规范名〗（符号v2.0规范）

# 3. 获取实际统计数据
python3 << 'EOF'
import json
with open('kg/entities/data/entity_index.json') as f:
    index = json.load(f)
    person = len(index.get('person', {}))
    total = sum(len(v) for v in index.values() if isinstance(v, dict))
    print(f"人名: {person}, 总计: {total}")

with open('kg/entities/data/entity_aliases.json') as f:
    aliases = json.load(f)
    total_aliases = sum(len(v) if isinstance(v, dict) else 1 for v in aliases.values())
    print(f"别名: {total_aliases}, 分类: {len(aliases)}")

with open('kg/relations/rulers.json') as f:
    rulers = json.load(f)
    print(f"君主: {len(rulers.get('rulers', []))}")
EOF
# 输出: 人名: 4418, 总计: 17483
#      别名: 591, 分类: 11
#      君主: 656

# 4. 批量更新Skill内容
vim skills/SKILL_03b_人名消歧.md
# 更新位置：
# - 第9行：摘要中的人名数（3,797 → 4,418）
# - 第26行：数据规模描述（新增全部实体统计）
# - 第447行：别名组数（586 → 591）
# - 第449-450行：实体统计表格（新增全部实体数）
# - 第524行：entity_index.json说明（11,069 → 17,483）
# - 第536行：君主数据规模（651 → 656）
# - 第618行：rulers.json规模（651 → 656）

# 5. 更新索引文件
vim skills/INDEX.md             # 第100行
vim skills/SKILL_03_实体构建.md  # 第16行
vim skills/SKILL_00_管线总览.md  # 第164行

# 6. 更新脚本引用
vim scripts/update_skill_frontmatter.py  # 第65行

# 7. 修正文档路径
# doc/entities/史记君主列表整理过程.md
#   → doc/entities/特殊任务/史记君主列表整理过程.md
# doc/entities/实体消歧别名反思报告.md
#   → doc/entities/实体分类修正/实体消歧别名反思报告.md

# 8. 验证
git status
git diff --cached
```

**更新内容总结**：
- 文件重命名：1个
- 内容修改：5处（标题、描述、路径×2、统计数据）
- 统计数据更新：7处（3,797→4,418、586→591、651→656、新增17,483等）
- 索引文件更新：3个（INDEX.md、SKILL_03、SKILL_00）
- 脚本更新：1个（update_skill_frontmatter.py）

**经验教训**：

✅ **做得好的**：
- 使用脚本统计实际数据，而非估算
- 系统化检查所有需要更新的位置（grep搜索关键数字）
- 同步更新所有索引文件和引用脚本

⚠️ **可改进的**：
- 应该有自动化脚本检测Skill中的过时数据
- 应该有Skill版本管理机制（记录每次更新的具体改动）
- 应该定期（如每月）扫描所有Skill的统计数据新鲜度

### 11.4 自动化工具

**建议开发的辅助工具**：

```python
# scripts/check_skill_freshness.py
"""检查Skill中的统计数据是否过时"""

import re
import json

def check_skill_stats(skill_file):
    """
    提取Skill中的所有数字，与实际数据对比

    输出：
    - ✅ PASS: 数字一致
    - ⚠️  WARN: 数字偏差<20%
    - ❌ FAIL: 数字偏差>20%
    """
    # 读取Skill中的统计数字
    with open(skill_file) as f:
        content = f.read()

    numbers = re.findall(r'(\d{1,3}(?:,\d{3})*|\d+)(?:条|个|章|组)', content)

    # 读取实际数据
    actual_stats = get_actual_stats()

    # 对比差异
    for num_str, unit in numbers:
        num = int(num_str.replace(',', ''))
        # 根据unit判断对应的实际数据
        # ...

# scripts/update_skill_stats.py
"""批量更新所有Skill的统计数据"""

def update_all_skills():
    """扫描所有Skill，自动更新统计数字"""
    # 实现自动化更新逻辑
    pass
```

**使用示例**：

```bash
# 检查单个Skill
python scripts/check_skill_freshness.py skills/SKILL_03b_人名消歧.md

# 检查所有Skill
python scripts/check_skill_freshness.py --all

# 输出示例：
# ✅ SKILL_01_古籍校勘.md - 统计数据最新
# ⚠️  SKILL_03b_人名消歧.md - 人名实体数过时（3797 vs 4418, +16%)
# ❌ SKILL_05_关系构建.md - 关系数严重过时（200 vs 1500, +650%)
```

---

## 十二、附录：Skill模板

详见 `skills/templates/SKILL_template.md`

---

## 相关文档

- 文件组织规范：`SKILL_10e_文件组织与目录结构.md`
- Git版本管理：`SKILL_10c_Git代码版本管理规范.md`
- 每日工作日志：`SKILL_10b_每日工作日志维护.md`
