---
name: skill-10f2
title: Skill精简拆分案例库
description: Skill超过500行时的精简与拆分方法，包含完整案例和检查清单。
---

# SKILL 10f2: Skill精简拆分案例库

> 当Skill超过500行时，按三级命名规范拆分，保持主文档简练可读。

---

## 一、何时需要精简

**触发条件**（满足任一即需精简）：

- [ ] Skill文件超过500行（推荐阈值）
- [ ] 代码示例超过200行（>15%篇幅）
- [ ] 详细配置说明超过100行
- [ ] 扩展FAQ或学术资源超过50行
- [ ] 用户反馈"太长，找不到重点"

---

## 二、精简诊断

### 2.1 内容分布分析

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

### 2.2 识别可拆分内容

| 内容类型 | 判断标准 | 处理方式 |
|---------|---------|---------|
| **代码示例** | >20行的完整函数 | → `references/SKILL_XXa1_` |
| **背景知识** | 理论、历史、方案对比 | → `references/SKILL_XXa2_` |
| **详细配置** | 环境setup、工具配置 | → `references/SKILL_XXa3_` |
| **扩展FAQ** | 深入讨论、多案例对比 | → 主文档精简，链接到详细说明 |
| **模板** | 提示词、文档模板 | → `references/SKILL_XXa1_模板库.md` |
| **详细规则** | 大型词表、映射表 | → `references/SKILL_XXa1_规则库.md` |

---

## 三、拆分流程

### 步骤1：备份原文件

```bash
cp skills/SKILL_XX.md skills/SKILL_XX.md.backup
```

### 步骤2：创建拆分文档

按三级命名规范创建：

```bash
# 创建规则库（第三级）
touch skills/references/SKILL_XXa1_规则库.md

# 创建模板库（第三级）
touch skills/references/SKILL_XXa2_模板库.md

# 创建背景资料（第三级）
touch skills/references/SKILL_XXa3_背景资料.md
```

**命名规范**：
- 格式：`SKILL_XXa{数字}_{名称}.md`
- 位置：`skills/references/`（扁平结构）
- 数字编号：a1, a2, a3...（与二级Skill关联）

### 步骤3：编写拆分文档结构

```markdown
---
name: skill-XXa1
title: [规则库/模板库/背景资料]
description: [一句话说明]
---

# SKILL XXa1: [标题]

> [简短说明：本文档包含哪些内容]

---

## 使用说明

[如何使用本文档]

---

## 内容章节

[详细内容...]

---

## 相关文档

- 主文档：[SKILL_XXa.md](../SKILL_XXa.md)
- 其他参考：[SKILL_XXa2.md](./SKILL_XXa2.md)
```

### 步骤4：精简主文档

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

**代码示例**：参见 [SKILL_XXa1_模板库 - API调用](./references/SKILL_XXa1_模板库.md#api调用)
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
# ✅ 001_文件.md - 修复 34 处错误
# 📊 修复完成: 125个文件，14955处
```

**4.3 压缩FAQ，链接到详细说明**

```markdown
<!-- 精简前 -->
### Q: 详细问题？

**答案**：详细回答... (40行)

<!-- 精简后 -->
### Q: 详细问题？

**答案**：简短回答（1-2句）

**详细说明**：参见 [SKILL_XXa3_背景资料](./references/SKILL_XXa3_背景资料.md#详细问题)
```

### 步骤5：更新链接

```markdown
# 主文档 → references
[SKILL_XXa1_规则库](./references/SKILL_XXa1_规则库.md)

# references → 主文档
[SKILL_XXa主文档](../SKILL_XXa.md)

# references之间互相引用
[SKILL_XXa2_模板库](./SKILL_XXa2_模板库.md)
```

### 步骤6：验证完整性

```bash
# 1. 检查行数减少
wc -l skills/SKILL_XX.md.backup skills/SKILL_XX.md

# 2. 检查章节结构完整
grep "^## " skills/SKILL_XX.md

# 3. 检查引用链接数量
grep -c "references/SKILL_XX" skills/SKILL_XX.md

# 4. 验证核心内容未丢失
required_sections=("快速开始" "核心步骤" "成功标准")
for section in "${required_sections[@]}"; do
    grep -q "$section" skills/SKILL_XX.md || echo "Missing: $section"
done
```

---

## 四、拆分质量标准

### 主文档要求

- [ ] **长度**：控制在300-500行
- [ ] **结构完整**：快速开始、规范、流程、工具、检查清单
- [ ] **代码少**：代码块≤5个（仅核心示例）
- [ ] **链接充足**：引用references文档≥3处
- [ ] **自包含**：不查阅references也能理解核心流程

### 拆分文档要求

- [ ] **独立性**：可以单独阅读，有完整上下文
- [ ] **完整性**：包含frontmatter、标题、目录、相关文档链接
- [ ] **互链性**：与主文档、其他拆分文档互相链接
- [ ] **命名规范**：遵循 `SKILL_XXa{数字}_{名称}.md`
- [ ] **位置规范**：放在 `skills/references/`，扁平结构

---

## 五、常见错误与避免

### 错误1：过度拆分

❌ **症状**：主文档变成目录索引，失去自包含性

```markdown
<!-- 错误示例 -->
## 二、操作流程

详见 [SKILL_XXa1_操作流程](./references/SKILL_XXa1_操作流程.md)
```

✅ **避免**：
- 保留核心流程概述（3-5步）
- 保留核心规范表格
- 保留基本判断标准
- 详细说明才移到references

### 错误2：目录结构混乱

❌ **错误**：
```
✗ skills/SKILL_01f/code_examples.md
✗ labs/references/SKILL_01f_code_examples.md
✗ skills/references/code_examples/SKILL_01f.md
```

✅ **正确**：
```
✓ skills/references/SKILL_01f1_代码示例.md
✓ skills/references/SKILL_01f2_背景资料.md
```

### 错误3：内容重复

❌ **症状**：同一内容在主文档和references都有完整版本

✅ **避免**：
- 主文档：简短回答（1-2句）+ 链接
- References：详细说明（完整内容）
- 绝对不要两处都保留完整内容

---

## 六、实际案例

### 案例1：SKILL_01f（古籍校勘反思）

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
| API代码 | 29行 | 移除 | code_examples.md |
| 本地模型代码 | 32行 | 移除 | code_examples.md |
| 反思提示词 | 23行 | 移除 | code_examples.md |
| Windows换行符FAQ | 51行 | 移除 | background.md |
| 示例3详细输出 | 107行 | 精简到40行 | 主文档保留关键步骤 |

**拆分结果**：
```
✓ 主文档：1297行 → 475行（减少63.4%）
✓ code_examples.md：250行
✓ background.md：331行
✓ 引用链接：14处
✓ 核心章节：9个，全部保留
```

### 案例2：SKILL_10f（本文档）

**拆分前分析**：
```
总行数: 1581
主要冗余：
- 完整模板示例（159行）
- 精简拆分详解（310行）
- 更新维护指南（343行）
- 脚本分解示例（62行）
```

**拆分方案**：
```
主文档保留（350行）：
- 问题诊断
- 编写规范（含三级命名）
- 工程化要点
- 质量标准
- 检查清单

拆分文档（4个）：
- SKILL_10f1_模板库.md（模板示例）
- SKILL_10f2_精简拆分案例库.md（本文档）
- SKILL_10f3_更新维护指南.md（更新流程）
- SKILL_10f4_脚本分解示例.md（脚本示例）
```

---

## 七、拆分检查清单

### 执行前

- [ ] 原Skill超过500行
- [ ] 有明确的可拆分内容（代码/案例/配置>100行）
- [ ] 已备份原文件（`.backup`后缀）

### 执行中

- [ ] 按三级命名创建references文件
- [ ] 主文档保留核心流程（<400行）
- [ ] 每个拆分文档有完整frontmatter
- [ ] 所有references文档包含"相关文档"章节

### 执行后

- [ ] 主文档独立可读（不依赖references理解核心）
- [ ] 所有Markdown链接有效（相对路径）
- [ ] 引用链接≥3处
- [ ] 运行 `wc -l` 确认行数减少≥40%

---

## 相关文档

- 主文档：[SKILL_10f_Skill的提炼与转化.md](../SKILL_10f_Skill的提炼与转化.md)
- 模板库：[SKILL_10f1_模板库.md](./SKILL_10f1_模板库.md)
- 更新维护：[SKILL_10f3_更新维护指南.md](./SKILL_10f3_更新维护指南.md)
- 脚本分解：[SKILL_10f4_脚本分解示例.md](./SKILL_10f4_脚本分解示例.md)
