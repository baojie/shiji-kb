# Skill拆分方法论总结

**日期**：2026-04-02
**案例**：SKILL_01f 句读和标点校勘（1297行 → 475行，减少63.4%）

---

## 一、问题诊断

### 1.1 发现症状

- **文件过长**：1297行，超过理想长度（600-700行）
- **代码占比高**：43.5%是代码示例
- **信息混杂**：规范、教程、背景知识、代码示例混在一起

### 1.2 分析工具

使用Python脚本分析内容分布：

```python
import re

with open('skills/SKILL_XXX.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

sections = {}
code_block = False
code_lines = 0

for line in lines:
    if line.strip().startswith('```'):
        code_block = not code_block
    if code_block:
        code_lines += 1

    # 统计各章节行数
    if line.startswith('##'):
        current_section = line.strip('#').strip()
        sections.setdefault(current_section, {'total': 0, 'code': 0})
    sections.setdefault(current_section, {'total': 0, 'code': 0})
    sections[current_section]['total'] += 1

print(f"代码行数: {code_lines} ({code_lines/len(lines)*100:.1f}%)")
for section, stats in sorted(sections.items(), key=lambda x: x[1]['total'], reverse=True):
    print(f"{section[:50]:50s} | 总: {stats['total']:4d} | 代码: {stats['code']:4d}")
```

### 1.3 诊断结果（SKILL_01f）

| 内容类型 | 行数 | 占比 | 处理方式 |
|---------|------|------|---------|
| 代码示例 | 564 | 43.5% | → `references/SKILL_01f_code_examples.md` |
| 冗长日志输出 | 107 | 8.3% | 精简70%，保留关键示例 |
| Informative背景 | 150 | 11.6% | → `references/SKILL_01f_background.md` |
| 核心规范 | 476 | 36.7% | ✓ 保留在主文档 |

---

## 二、拆分原则

### 2.1 保留在主文档的内容

**核心判断标准**：执行任务时必须查阅的内容

✓ **保留**：
1. **规范性内容**：标点符号对照表、引号嵌套规则、基本原则
2. **工作流程**：核心步骤、场景分类、检查清单
3. **工具列表**：脚本名称、用法、状态（已实现/待开发）
4. **简洁示例**：5-10行的命令流程
5. **FAQ核心答案**：简短回答（1-2句），详细说明链接到references

✗ **移除**：
1. **详细代码**：完整的Python函数、API调用示例（>20行）
2. **冗长输出**：详细的日志示例、统计报告
3. **背景知识**：技术方案对比、学术资源、历史渊源
4. **配置说明**：详细的VSCode配置、Git配置、环境setup
5. **扩展FAQ**：深入讨论、多个案例对比

### 2.2 拆分文件命名规范

遵循三级命名规范，放在 `skills/references/` 目录：

```
skills/
├── SKILL_01f_句读和标点校勘.md          # 主文档（核心规范）
└── references/
    ├── SKILL_01f_code_examples.md       # 代码示例
    ├── SKILL_01f_background.md          # 背景信息与扩展FAQ
    └── SKILL_01f_templates.md           # 模板（如有）
```

**命名模式**：
- `SKILL_{ID}_{suffix}.md`
- 常用后缀：
  - `code_examples` - 代码示例
  - `background` - 背景信息
  - `templates` - 提示词模板/文档模板
  - `rules` - 详细规则表（如繁简词表）
  - `案例集` - 实际案例分析

---

## 三、拆分步骤

### 步骤1：备份原文件

```bash
cp skills/SKILL_XXX.md skills/SKILL_XXX.md.backup
```

### 步骤2：创建拆分文件

**2.1 创建代码示例文档**

`skills/references/SKILL_XXX_code_examples.md`：

```markdown
# SKILL XXX - 代码示例参考

本文档包含 SKILL_XXX 中提到的详细代码示例。

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

- [SKILL_XXX.md](../SKILL_XXX.md) - 主文档
- [SKILL_XXX_background.md](./SKILL_XXX_background.md) - 背景信息
```

**2.2 创建背景信息文档**

`skills/references/SKILL_XXX_background.md`：

```markdown
# SKILL XXX - 背景信息与扩展FAQ

本文档包含 SKILL_XXX 的背景信息、详细配置说明和扩展FAQ。

## 目录

- [技术方案对比](#技术方案对比)
- [详细配置说明](#详细配置说明)
- [扩展FAQ](#扩展faq)
- [学术参考资源](#学术参考资源)

---

## 技术方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|-----|------|------|---------|
| ... | ...  | ...  | ...     |

---

## 相关文档

- [SKILL_XXX.md](../SKILL_XXX.md) - 主文档
- [SKILL_XXX_code_examples.md](./SKILL_XXX_code_examples.md) - 代码示例
```

### 步骤3：精简主文档

**3.1 删除详细代码，保留引用**

```markdown
<!-- 删除前 -->
### 3.2 gj.cool API 使用方法

\```python
import requests

def auto_punctuate_gj(text: str) -> str:
    """调用 gj.cool API 自动断句"""
    url = "https://gj.cool/api/punctuate"
    payload = {"text": text, "model": "default"}
    response = requests.post(url, json=payload)
    ...
    return response.json()["result"]
\```

<!-- 精简后 -->
### 3.2 gj.cool API 使用方法

**技术方案**：
- **推荐**：gj.cool API（https://gj.cool）- 准确率92-99%
- **备选**：本地模型（Qwen/GLM-4）- 准确率90-95%

**代码示例**：参见 [references/SKILL_XXX_code_examples.md - gj.cool API调用](./references/SKILL_XXX_code_examples.md#gjcool-api-调用)
```

**3.2 精简冗长输出，保留关键行**

```markdown
<!-- 删除前 -->
# 输出示例：
# 📁 找到 130 个文件
# ✅ 001_五帝本纪.tagged.md
#    修复 34 处半角引号
#    - 行95: 2处（双引号2，单引号0）
#    - 行102: 5处（双引号1，单引号4）
#    ... (省略100行)
# 📊 修复完成:
#    - 修复文件数: 125
#    - 修复引号数: 14955

<!-- 精简后 -->
# 输出示例：
# ✅ 001_五帝本纪.tagged.md
#    修复 34 处半角引号
# 📊 修复完成: 125个文件，14955处引号
```

**3.3 压缩FAQ，链接到详细说明**

```markdown
<!-- 删除前 -->
### Q7: Windows用户如何处理换行符问题？

**答案**：Windows用户可以使用LF格式...

**VSCode设置**：
\```json
{
  "files.eol": "\n",
  "files.autoGuessEncoding": false
}
\```

**Git设置**：
\```bash
git config --global core.autocrlf input
\```

... (省略40行详细说明)

<!-- 精简后 -->
### Q6: Windows用户如何处理换行符问题？

**答案**：推荐使用LF格式，配置 `core.autocrlf=input`。现代Windows编辑器完全支持LF。

**详细说明**：参见 [references/SKILL_XXX_background.md - Windows用户换行符处理](./references/SKILL_XXX_background.md#windows用户如何处理换行符问题)
```

### 步骤4：更新链接

确保所有拆分文档之间的链接正确：

```markdown
# 主文档 → references
[references/SKILL_XXX_code_examples.md](./references/SKILL_XXX_code_examples.md)

# references → 主文档
[SKILL_XXX.md](../SKILL_XXX.md)

# references之间互相引用
[SKILL_XXX_background.md](./SKILL_XXX_background.md)
```

### 步骤5：验证完整性

```bash
# 1. 检查行数减少
wc -l skills/SKILL_XXX.md.backup skills/SKILL_XXX.md

# 2. 检查章节结构完整
grep "^## " skills/SKILL_XXX.md

# 3. 检查引用链接数量
grep -c "references/SKILL_XXX_" skills/SKILL_XXX.md

# 4. 验证核心内容未丢失
python scripts/verify_skill_integrity.py skills/SKILL_XXX.md
```

---

## 四、质量标准

### 4.1 主文档要求

- [ ] **长度**：控制在600-700行以内
- [ ] **结构完整**：快速开始、规范、流程、工具、示例、FAQ、相关文档
- [ ] **代码少**：Python代码块≤3个（仅配置示例）
- [ ] **链接充足**：至少10处引用到references文档
- [ ] **自包含**：不查阅references也能理解核心规范

### 4.2 拆分文档要求

- [ ] **独立性**：可以单独阅读，不依赖主文档上下文
- [ ] **完整性**：包含标题、目录、章节、相关文档链接
- [ ] **互链性**：与主文档、其他拆分文档互相链接
- [ ] **命名规范**：遵循三级命名（SKILL_{ID}_{suffix}.md）
- [ ] **位置规范**：放在 `skills/references/` 目录，扁平结构

### 4.3 验证清单

- [ ] 备份文件已创建（`.backup`后缀）
- [ ] 主文档行数减少50%+
- [ ] 核心章节结构完整
- [ ] 所有代码示例已转移或精简
- [ ] FAQ已压缩，详细说明已链接
- [ ] 所有链接可点击且正确
- [ ] Git暂存区仅包含必要文件

---

## 五、常见错误与避免

### 错误1：过度拆分

**症状**：主文档变成目录索引，失去自包含性

**避免**：
- 保留核心规范表格（如标点符号对照表）
- 保留基本原则和判断标准
- 保留简洁的工作流程（5-10行命令）

### 错误2：目录结构混乱

**症状**：拆分文件放在多层子目录中

**正确做法**：
```
✓ skills/references/SKILL_01f_code_examples.md
✗ skills/SKILL_01f/code_examples.md
✗ labs/references/SKILL_01f/code_examples.md
```

### 错误3：链接失效

**症状**：拆分后链接404

**检查方法**：
```bash
# 检查所有markdown链接
grep -r "\[.*\](\./" skills/ | grep -v ".backup"
```

### 错误4：内容重复

**症状**：同一内容在主文档和references都有

**避免**：
- 主文档：简短回答 + 链接
- References：详细说明
- 绝对不要两处都保留完整内容

### 错误5：丢失核心内容

**症状**：拆分后核心规范也被移除

**验证**：
```python
# 检查核心章节是否存在
required_sections = ["快速开始", "核心步骤", "成功标准", ...]
with open('skills/SKILL_XXX.md') as f:
    content = f.read()
    for section in required_sections:
        assert section in content
```

---

## 六、应用指南

### 何时拆分

- [ ] Skill文件超过800行
- [ ] 包含大量代码示例（>200行）
- [ ] 包含详细配置说明（>100行）
- [ ] 包含扩展FAQ或学术资源（>50行）

### 何时不拆分

- [ ] Skill文件<600行
- [ ] 内容高度耦合，难以独立理解
- [ ] 是纯规范文档（如标注铁律）
- [ ] 是简洁的检查清单或快速参考

### 拆分优先级

1. **代码示例** - 最先拆分，最容易独立
2. **背景知识** - 次要拆分，informative内容
3. **详细配置** - 可选拆分，setup类内容
4. **扩展FAQ** - 可选拆分，保留核心FAQ

---

## 七、实际案例：SKILL_01f

### 拆分前分析

```
总行数: 1297
代码行数: 564 (43.5%)

各章节行数分布（Top 10）:
示例3：批量修复半角符号（实际案例）      140行 (107行代码)
Q7: Windows用户如何处理换行符问题？     51行
2.1a 换行符规范                        47行
4.2 反思提示词模板                     43行
3.2 gj.cool API 使用方法               42行
Q5: 韵文应该如何断句和换行？            42行
3.3 本地模型方案（高级）                38行
Q6: 长对话分段时，引号应该如何使用？     38行
```

### 拆分决策

| 内容 | 行数 | 决策 | 去向 |
|-----|------|------|------|
| gj.cool API代码 | 29行 | 移除 | code_examples.md |
| 本地模型代码 | 32行 | 移除 | code_examples.md |
| 质量检查代码 | 24行 | 移除 | code_examples.md |
| 反思提示词 | 23行 | 移除 | code_examples.md |
| Windows换行符FAQ | 51行 | 移除 | background.md |
| 换行符详细说明 | 47行 | 压缩到10行 | 主文档保留要点 |
| gj.cool准确率评估 | 16行 | 移除 | background.md |
| 示例3详细输出 | 107行 | 精简到40行 | 主文档保留关键步骤 |

### 拆分结果

```
✓ 主文档：1297行 → 475行（减少63.4%）
✓ code_examples.md：250行（代码示例 + 模板）
✓ background.md：331行（背景 + 扩展FAQ + 学术资源）
✓ 引用链接：14处
✓ 核心章节：9个，全部保留
```

---

## 八、总结

### 核心原则

1. **主文档 = 执行指南**：包含规范、流程、工具列表、简洁示例
2. **References = 深入阅读**：包含代码、背景、详细说明、模板
3. **保持自包含**：主文档不依赖references也能理解核心
4. **充分链接**：主文档频繁链接到references获取详细信息

### 成功标准

- [ ] 主文档长度减少50%+
- [ ] 核心内容100%保留
- [ ] 所有链接正确可用
- [ ] 章节结构清晰完整
- [ ] 符合SKILL_10e和10f规范

### 下一步

将本方法论融合进 `skills/SKILL_10f_Skill的提炼与转化.md`，成为标准工序。
