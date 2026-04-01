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

### 2.2 长度控制

| 内容类型 | 推荐长度 | 最大长度 |
|---------|---------|---------|
| 快速开始 | 30-50行 | 100行 |
| 详细说明 | 50-100行 | 200行 |
| 工具与脚本 | 20-30行 | 50行 |
| 检查清单 | 10-20行 | 30行 |
| FAQ | 20-50行 | 100行 |
| **总计** | **200-300行** | **500行** |

**超过500行的Skill**：
- 考虑拆分为多个子Skill
- 将详细案例移至 `labs/examples/`
- 将背景理论移至 `docs/theory/`

### 2.3 写作原则

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

## 十一、附录：Skill模板

详见 `skills/templates/SKILL_template.md`

---

## 相关文档

- 文件组织规范：`SKILL_10e_文件组织与目录结构.md`
- Git版本管理：`SKILL_10c_Git代码版本管理规范.md`
- 每日工作日志：`SKILL_10b_每日工作日志维护.md`
