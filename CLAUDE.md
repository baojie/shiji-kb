# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

《史记》知识库：用AI Agent将《史记》130篇转化为结构化知识图谱。

---

# ⛔ 绝对禁止的行为（NEVER DO THESE）

**以下行为会造成不可逆的数据损失或破坏工作流，无论任何理由都不得执行。执行前必须三思并征得用户明确同意。**

## 1. 严禁使用破坏性Git命令

```bash
# ❌ 绝对禁止！会立即覆盖工作区文件，造成不可逆的数据丢失！
git checkout <commit> -- <file>
git checkout -- <file>
git restore <file>
git reset --hard
```

**🚨 如果你想恢复文件或重置工作区，必须先问我确认，不得自行执行。**

**血泪教训**：
- 2026-04-01：擅自使用 `git checkout` 恢复69个文件，险些丢失所有正在进行的修改
- 2026-04-02：再次擅自使用 `git checkout` 恢复053-080章节，覆盖了数小时的工作成果
  - 丢失了64个章节的PN修复（批量脚本处理结果）
  - 丢失了081-083的16处人名简称修复（精心手动修复）
  - 导致用户极度愤怒："你他妈的又git checkout，fuck！！！！"

**✅ 正确做法**：
1. **查看差异**：`git diff <commit> -- <file>` 查看需要修复什么
2. **手动编辑**：根据diff结果用Edit工具修复
3. **脚本修复**：编写Python脚本提取旧版本的特定内容（如编号）
4. **紧急情况**：先用 `git stash` 保护现有修改，然后征求用户同意

## 2. 严禁擅自执行Git Add/Commit

**绝对禁止**：
- ❌ 不得自动commit（必须用户明确要求）
- ❌ 不得擅自 `git add -A` 或 `git add .` 添加未暂存文件
- ❌ 不得跳过pre-commit hooks（除非用户明确要求）
- ❌ 不得force push到main/master分支

**🚨 当用户说"commit"时的铁律**：
1. **只执行 `git commit`**，不要执行任何其他git命令
2. 提交前可以运行：`git log --oneline -10`（了解commit message风格）、`git diff --cached`（查看具体改动）
3. 使用HEREDOC格式编写commit message
4. **绝对不要**：git add、git reset、git status、git checkout等任何其他git操作

## 3. 严禁修改原文字符（标注工作）

标注工作**只能添加 `〖TYPE 〗` 标记符号**，不得对原文字符做任何修改：

**❌ 绝对禁止的操作**：
- 不得增加/删除/替换原文字符（汉字、标点、引号、空格等）
- **🚨🚨🚨 严禁引入半角引号 `""`**：这是最常见的错误！原文使用全角引号 `""`（U+201C/U+201D），标注文件必须保持全角引号，**任何情况下都绝对禁止使用半角引号 `""`（U+0022）**
- **严禁全角/半角符号转换**（`""`→`""`、`''`→`''`、`（）`→`()`等）
- **严禁嵌套标注**（如 `〖#〖#text〗〗` `〖%元〖~鼎〗五年〗` `⟦◈攻〖◆秦〗⟧`）

**✅ 允许的操作**：
- 只能在原文字符周围添加 `〖TYPE 〗` 或 `⟦TYPE⟧` 标记符号
- 消歧语法 `〖TYPE 显示名|规范名〗` 中的"规范名"不改变显示文本
- 标注符号必须平铺，不得嵌套

**验证方法**：
- 将标注文件去除所有 `〖TYPE 〗` 符号后，所得纯文本必须与原始 `.txt` 文件逐字相同
- `python scripts/lint_text_integrity.py` 验证文本完整性
- `python scripts/lint_text_integrity.py --check-nested` 检测嵌套标注

**🚨 使用Edit工具时的特别警告**：
- **绝对禁止引入半角引号 `""`**：Edit工具在处理时极易将全角引号 `""` 自动转换为半角引号 `""`，这是**绝对禁止**的
- **任何情况下都不得使用半角引号**：原文使用全角引号 `""`，标注文件必须保持全角引号，任何情况下都不得使用半角引号 `""`
- **绝对禁止全角/半角符号转换**（如 `""`→`""`、`''`→`''`、`（）`→`()`等）
- Edit工具在处理Unicode字符时可能出现编码问题，导致文件损坏
- 如需批量修改标注符号，优先使用专门的Python脚本而非Edit工具
- 修改后必须验证文件完整性，确保原文字符未被改变
- **验证方法**：`grep -n '[""]' file.md` 检查是否存在半角引号（U+0022）

## 4. *.tagged.md 编辑规范

**⛔ 编辑任何 `*.tagged.md` 或 `data/chapters/*.md` 文件时的铁律**：

**✅ 只允许使用中文全角引号**：
- 左双引号：`"` （U+201C）
- 右双引号：`"` （U+201D）
- 左单引号：`'` （U+2018）
- 右单引号：`'` （U+2019）

**❌ 绝对禁止以下引号**：
- 半角引号：`"` `'` `` ` `` （U+0022, U+0027, U+0060）
- 直角引号：`"` `"` `'` `'` （U+FF02, U+FF07）
- 日文引号：`「」` `『』` （U+300C-U+300F）
- 任何其他形式的引号

**🚨 每次使用 Edit 工具编辑标注文件后，必须立即运行验证**：
```bash
# 检查是否引入了半角引号（U+0022）
grep -n '["'"'"'`]' chapter_md/NNN_*.tagged.md

# 或使用完整性检查脚本
python scripts/lint_text_integrity.py chapter_md/NNN_*.tagged.md
```

**如果检测到半角引号**：
1. **立即停止其他操作**
2. 使用 Python 脚本批量修复（不要手动逐个替换）
3. 重新验证文件完整性

**修复脚本示例**：
```python
# scripts/fix_halfwidth_quotes.py
import re
import sys

def fix_quotes(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计半角引号数量（必须是偶数）
    count = content.count('"')
    if count % 2 != 0:
        print(f"警告：{file_path} 中半角引号数量为奇数({count})，无法自动配对")
        return False

    # 成对替换：第1/3/5...个 " 替换为 "，第2/4/6...个 " 替换为 "
    result = []
    quote_index = 0
    for char in content:
        if char == '"':
            result.append('"' if quote_index % 2 == 0 else '"')
            quote_index += 1
        else:
            result.append(char)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(''.join(result))

    print(f"✓ 修复完成：{file_path}，替换了 {count} 个半角引号")
    return True

if __name__ == '__main__':
    fix_quotes(sys.argv[1])
```

---

# 项目工作规范

## 执行命令前的自检清单

1. 这个命令在"禁止列表"里吗？→ 在则停止，告知用户
2. 这个命令会不可逆地修改文件吗？→ 是则先确认

## 项目约定

- 反思流程全自动。每章的 Agent 反思循环不需要用户逐步确认，直接执行完整流程。
- 对话和输出以中文为主。
- 当用户在对话中明确要求自动确认时，后续操作不再逐步询问，自动执行。
- commit message不要自动加版本号（如v3.1），版本号由用户决定。
- **🚨 TODO术语约定**：用户说"写入TODO"/"加入TODO"时，指的是编辑 `TODO.md` 文件，而非使用 `TodoWrite` 工具。详见 [`SKILL_10a_TODO和Issue管理.md`](skills/SKILL_10a_TODO和Issue管理.md) §7.3。

## Git代码版本管理规范

**重要**：必须严格遵守 [`skills/SKILL_10c_Git代码版本管理规范.md`](skills/SKILL_10c_Git代码版本管理规范.md)

### 文件恢复的安全方案

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

### Git提交消息规范

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

## 文件组织与目录结构

**重要**：创建新文件时，必须遵循 [`skills/SKILL_10e_文件组织与目录结构.md`](skills/SKILL_10e_文件组织与目录结构.md) 中定义的规范。

### 核心规则（摘要）

- **`docs/`** - 仅存放已定稿、可公开的文档（会同步到GitHub Pages）
- **`labs/`** - 所有实验性、草稿性内容（原型、调研、规划文档）
- **`data/`** - 核心数据资产（标注文件、词表、原始文本）
- **`scripts/`** - 稳定的、可复用的自动化脚本
- **`logs/`** - 工作日志与运行记录
- **`skills/`** - 项目规范与方法论文档

### 决策树

创建新文件前，使用决策树：
1. 是否面向外部用户且已定稿？→ `docs/`
2. 是否实验性/草稿性质？→ `labs/`（原型→`labs/prototypes/`，调研→`labs/research/`，规划→`labs/planning/`）
3. 是否核心数据资产？→ `data/`
4. 是否可复用脚本？→ `scripts/`
5. 是否工作记录？→ `logs/daily/`
6. 是否项目规范？→ `skills/`

## 每日工作日志规范

**重要**：生成或更新每日工作日志时，必须遵循 [`skills/SKILL_10b_每日工作日志维护.md`](skills/SKILL_10b_每日工作日志维护.md) 中定义的完整规范。

### 核心要点（摘要）

- **时间范围**：X日日志 = `X日 07:00` ~ `X+1日 07:00`（凌晨0-7点算前一天）
- **生成命令**：`python logs/daily/generate_log.py YYYY-MM-DD`
- **微信通知**：必须在日志开头添加，使用全角中点（·），包含关键数字，以"提交N次代码"结尾
- **无提交日**：使用"太史公曰"格式 + 32字赞文（8个四字句）
- **同步更新**：生成日志后必须同步更新 `CHANGELOG.md`

## CHANGELOG 编写规范

**重要**：编写或更新 CHANGELOG 时，必须遵循 [`skills/SKILL_10d_CHANGELOG编写规范.md`](skills/SKILL_10d_CHANGELOG编写规范.md) 中定义的完整规范。

### 核心原则（摘要）

- **按日期组织**：每个日期一个条目（格式：`## YYYY-MM-DD`）
- **高层次总结**：只保留核心变更概括，详细内容链接到每日工作日志
- **标准分类**：Added/Changed/Fixed/Removed/Maintenance
- **链接规范**：引用式commit链接 + Issue链接
- **详细日志链接**：每个条目必须链接到 `logs/daily/YYYY-MM-DD.md`

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
