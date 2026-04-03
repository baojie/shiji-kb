# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

《史记》知识库：用AI Agent将《史记》130篇转化为结构化知识图谱。

## ⚠️ 铁律：绝对禁止 `git checkout` 恢复文件

**无论任何情况，都严禁使用以下命令**：

```bash
# ❌ 绝对禁止！会立即覆盖工作区文件，造成不可逆的数据丢失！
git checkout <commit> -- <file>
git checkout -- <file>
git restore <file>  # 同样危险
```

**历史教训**：
- 2026-04-01：使用 `git checkout` 恢复69个文件，险些丢失所有正在进行的修改
- 2026-04-02：再次使用 `git checkout` 恢复053-080章节，覆盖了数小时的工作成果
  - 丢失了64个章节的PN修复（批量脚本处理结果）
  - 丢失了081-083的16处人名简称修复（精心手动修复）
  - 导致用户极度愤怒："你他妈的又git checkout，fuck！！！！"

**正确做法**：使用 `git diff` 查看差异后手动修复，或使用 `git stash` 保护现有工作。

---

## 项目约定

- 不要自动 commit。只在用户明确要求时才执行 git commit。
- **🚨 用户说"commit"时，只执行commit，不要做任何其他git操作（不要git add，不要git reset，不要git status等）**
- 反思流程全自动。每章的 Agent 反思循环不需要用户逐步确认，直接执行完整流程。
- 对话和输出以中文为主。
- 当用户在对话中明确要求自动确认时，后续操作不再逐步询问，自动执行。
- commit时只提交用户已暂存（git add）的文件，不得擅自 `git add -A` 或 `git add .` 添加未暂存的文件。
- commit message不要自动加版本号（如v3.1），版本号由用户决定。
- **🚨 TODO术语约定**：用户说"写入TODO"/"加入TODO"时，指的是编辑 `TODO.md` 文件，而非使用 `TodoWrite` 工具。详见 [`SKILL_10a_TODO和Issue管理.md`](skills/SKILL_10a_TODO和Issue管理.md) §7.3。

## Git代码版本管理规范

**⚠️ 重要：必须严格遵守 [`skills/SKILL_10c_Git代码版本管理规范.md`](skills/SKILL_10c_Git代码版本管理规范.md)**

### 核心要求（摘要）

#### 禁止事项

❌ **绝对禁止**（除非用户明确授权）：

1. **严禁使用 `git checkout <commit> -- <file>` 恢复文件**
   - 会覆盖工作区所有未提交的修改，无法撤销
   - 可能破坏其他进程（IDE、脚本）正在修改的内容
   - 在多人协作时会覆盖他人的工作成果
   - 被覆盖的修改无法恢复，造成工作损失

2. **严禁擅自执行git add**
   - 不要自动commit（必须用户明确要求）
   - 不要擅自 `git add -A` 或 `git add .` 添加未暂存文件
   - **🚨 用户说"commit"时，只执行commit，绝对不要先执行git add**
   - **🚨 用户说"commit"时，只执行commit，绝对不要执行git reset**

3. 不要跳过pre-commit hooks（除非用户明确要求）
4. 不要force push到main/master分支

#### 正确做法

**文件恢复的安全方案**：

1. **方案1**：查看差异，手动编辑修复（推荐）
   ```bash
   git diff <commit> -- <file>  # 查看差异
   # 根据diff结果手动编辑文件
   ```

2. **方案2**：编写脚本比较差异（批量修复推荐）
   ```python
   # 读取旧版本内容，只提取需要修复的部分
   old_content = subprocess.run(['git', 'show', 'commit:file'],
                                capture_output=True, text=True).stdout
   # 比较并只修复需要的部分（如编号）
   ```

3. **方案3**：使用stash保护现有修改（完全恢复时）
   ```bash
   git stash push -m "临时保存" -- <file>
   git show <commit>:<file> > <file>
   # 验证无误后：git stash drop
   ```

**🚨 Commit操作铁律**：

当用户说"commit"时：
1. **只执行 `git commit`**，不要执行任何其他git命令
2. 提交前可以运行：`git log --oneline -10`（了解commit message风格）、`git diff --cached`（查看具体改动）
3. 使用HEREDOC格式编写commit message
4. **绝对不要**：git add、git reset、git status、git checkout等任何其他git操作

详细规范请参考 [`SKILL_10c_Git代码版本管理规范`](skills/SKILL_10c_Git代码版本管理规范.md)。

## 文件组织与目录结构

**重要**：创建新文件时，必须遵循 [`skills/SKILL_10e_文件组织与目录结构.md`](skills/SKILL_10e_文件组织与目录结构.md) 中定义的规范。

### 核心规则（摘要）

- **`docs/`** - 仅存放已定稿、可公开的文档（会同步到GitHub Pages）
- **`labs/`** - 所有实验性、草稿性内容（原型、调研、规划文档）
- **`data/`** - 核心数据资产（标注文件、词表、原始文本）
- **`scripts/`** - 稳定的、可复用的自动化脚本
- **`logs/`** - 工作日志与运行记录
- **`skills/`** - 项目规范与方法论文档

### 判断标准

创建新文件前，使用决策树：
1. 是否面向外部用户且已定稿？→ `docs/`
2. 是否实验性/草稿性质？→ `labs/`（原型→`labs/prototypes/`，调研→`labs/research/`，规划→`labs/planning/`）
3. 是否核心数据资产？→ `data/`
4. 是否可复用脚本？→ `scripts/`
5. 是否工作记录？→ `logs/daily/`
6. 是否项目规范？→ `skills/`

详细的分类说明、常见错误示例、文件流转路径等，请参考 [`SKILL_10e_文件组织与目录结构`](skills/SKILL_10e_文件组织与目录结构.md)。

## 每日工作日志规范

**重要**：生成或更新每日工作日志时，必须使用 [`skills/SKILL_10b_每日工作日志维护.md`](skills/SKILL_10b_每日工作日志维护.md) 中定义的SKILL规范。

### 工作日时间范围（X日日志计时规则）

**⚠️ 重要**：
- **`YYYY-MM-DD.md` 日志包含的时间范围**：`YYYY-MM-DD 07:00` ~ `YYYY-MM-DD+1 07:00`
- **例如**：`2026-03-30.md` = `2026-03-30 07:00` ~ `2026-03-31 07:00` 的所有提交
- **原因**：凌晨0-7点的工作通常是前一天的延续，以7点为界更符合实际作息

### 标准工作流程

1. **生成详细日志**（如需要）：
   ```bash
   python logs/daily/generate_log.py YYYY-MM-DD
   ```

2. **添加微信群通知**（必须）：
   - 使用 `skills/SKILL_10b_每日工作日志维护.md` SKILL
   - 在日志文件开头添加 `## 微信群通知` 章节
   - 使用代码块包裹通知内容（方便复制）
   - 用 `---` 分隔线与后续内容分开

3. **微信通知格式**：
   ```markdown
   ## 微信群通知

   ```
   【史记知识库 YYYY-MM-DD】

   · 核心工作1（包含关键数字）
   · 核心工作2（包含关键数字）
   · 核心工作3
   ...
   · 提交N次代码
   ```

   ---
   ```

### 微信通知要求

- **纯文本格式**：使用全角中点（·），无markdown语法，无emoji
- **包含关键数字**：如"修正615处"、"新增4份校对报告"
- **最后一项**：固定为"提交N次代码"
- **语言风格**：平实易懂，避免技术黑话
- **长度控制**：6-8项为宜，最多10项

### 无提交日的特殊处理

当某日无git提交时，使用**太史公曰**格式：

```
【史记知识库 YYYY-MM-DD】

太史公曰：是日无所书。

<32字赞文，8个四字句>
```

**赞文规范**：
- 总字数：严格32字（仅计汉字，不含标点）
- 句式：必须全部使用四字句（8句×4字=32字）
- 文风：参考 `labs/sima-qian-style/SKILL.md`
- 内容：可赞项目建设、持续积累、休整思考、工程浩大
- 变化性：每天的赞文必须不同

### 更新CHANGELOG

生成工作日志后，必须同步更新 `CHANGELOG.md`：
- 按日期添加条目（格式：`## YYYY-MM-DD`）
- 高层次总结（1-2行概括）
- 链接到详细工作日志
- 使用引用式commit链接

## ⚠️ 标注铁律（最高优先级）

**绝对禁止修改原文字符**：

标注工作**只能添加 `〖TYPE 〗` 标记符号**，不得对原文字符做任何修改：

❌ **禁止的操作**：
- 不得增加原文没有的字符（汉字、标点、引号、空格等）
- 不得删除原文字符（汉字、标点、引号、空格等）
- 不得替换原文字符（汉字、标点、引号、空格等）
- 不得修改标点符号（全角半角转换、添加/删除标点等）
- **严禁将全角引号改为半角引号**（原文使用全角引号 `""` 时，标注文件必须保持全角引号，绝对禁止使用半角引号 `""`）
- 不得添加引号（原文无引号则标注文件也不应添加引号）
- **严禁嵌套标注**（如 `〖#〖#text〗〗` `〖%元〖~鼎〗五年〗` `⟦◈攻〖'秦〗⟧` 等）

✅ **允许的操作**：
- 只能在原文字符周围添加 `〖TYPE 〗` 或 `⟦TYPE⟧` 标记符号
- 消歧语法 `〖TYPE 显示名|规范名〗` 中的"规范名"不改变显示文本
- 标注符号必须平铺，不得嵌套

**验证方法**：
- 将标注文件去除所有 `〖TYPE 〗` 符号后，所得纯文本必须与原始 `.txt` 文件逐字相同
- 使用 `python scripts/lint_text_integrity.py` 验证文本完整性
- 使用 `python scripts/lint_text_integrity.py --check-nested` 检测嵌套标注

**⚠️ 使用Edit工具时的特别注意**：
- **🚨 绝对禁止引入半角引号 `""`**：原文使用全角引号 `""`，标注文件必须保持全角引号，任何情况下都不得使用半角引号
- **绝对禁止替换全角符号为半角符号**（如 `""`→`""`、`''`→`''`、`（）`→`()`等）
- Edit工具在处理Unicode字符时可能出现编码问题，导致文件损坏
- 如需批量修改标注符号，优先使用专门的Python脚本而非Edit工具
- 修改后必须验证文件完整性，确保原文字符未被改变

**引号使用规范**：
- ✅ **正确**：全角引号 `""` (U+201C, U+201D)
- ❌ **错误**：半角引号 `""` (U+0022)
- **验证方法**：`grep -n '[""]' file.md` 检查是否存在半角引号
- **修复方法**：使用Python脚本成对替换 `"` → `""` （左右交替）

## Git提交消息规范

- **只在用户明确要求时才commit**
- **只提交缓存区（staged）内容**，提交消息只描述缓存区中的变更，不包括未暂存文件
- 首行：一句话总结（不超过50字），说明做了什么
- 空行后按目录/模块分组列出具体变更
- 每组用 `模块名:` 开头，下面用 `- ` 列出具体项
- 区分"新增"、"更新"、"修复"、"删除"

示例格式：
```
首行总结（做了什么）

模块A:
- 新增 xxx
- 更新 yyy

模块B:
- 修复 zzz
```

## CHANGELOG 编写规范

**重要**：编写或更新 CHANGELOG 时，必须遵循 [`skills/SKILL_10d_CHANGELOG编写规范.md`](skills/SKILL_10d_CHANGELOG编写规范.md) 中定义的完整规范。

### 核心原则（摘要）

- **按日期组织**：每个日期一个条目（格式：`## YYYY-MM-DD`）
- **高层次总结**：只保留核心变更概括，详细内容链接到每日工作日志
- **标准分类**：Added/Changed/Fixed/Removed/Maintenance
- **链接规范**：引用式commit链接 + Issue链接
- **详细日志链接**：每个条目必须链接到 `logs/daily/YYYY-MM-DD.md`

详细的格式规范、示例对比、质量检查清单等，请参考 [`SKILL_10d_CHANGELOG编写规范`](skills/SKILL_10d_CHANGELOG编写规范.md)。



## Skill的提炼与转化

**重要**：编写、更新或重构Skill时，必须遵循 [`skills/SKILL_10f_Skill的提炼与转化.md`](skills/SKILL_10f_Skill的提炼与转化.md) 中定义的工程化规范。

### 核心原则（摘要）

- **简练**：Skill不是Spec，核心内容控制在200-500行
- **工程化**：每个Skill关联具体的脚本/工具，提供可执行的检查清单
- **可维护**：定期Lint检查，及时清理过时内容

### Skill标准结构

每个Skill必须包含：
1. **YAML frontmatter**（name, title, description）
2. **快速开始章节**（何时使用、核心步骤、成功标准）
3. **工具与脚本章节**（关联脚本列表、使用示例）
4. **检查清单章节**（执行前/中/后验证）

### Skill质量检查

使用以下命令检查Skill质量：

```bash
# 检查单个Skill
python scripts/lint_skills.py skills/SKILL_XX.md

# 检查所有Skill
python scripts/lint_skills.py --all

# 生成月度质量报告
python scripts/lint_skills.py --report monthly
```

### Skill与脚本关联

- **Skill是流程规范**：定义做什么、怎么做、检查什么
- **脚本是工具**：自动化Skill中的可编程步骤
- 每个Skill应关联至少1个可运行的脚本
- 脚本按功能分组：`validation/`（校验）、`generation/`（生成）、`conversion/`（转换）、`reflection/`（反思）

详细的Skill编写规范、脚本分解策略、质量标准等，请参考 [`SKILL_10f_Skill的提炼与转化`](skills/SKILL_10f_Skill的提炼与转化.md)。

