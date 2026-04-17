---
name: skill-10c
title: Git代码版本管理规范
description: 史记知识库项目的Git版本管理规范。包含代码恢复安全规范、提交内容管理、commit message格式、危险操作禁止等项目特定要求。
---

# SKILL 10c: Git代码版本管理规范

> **核心理念**：安全第一，最小影响，可追溯。任何Git操作都不应破坏现有工作成果。

---

## 一、安全规范（最高优先级）

### 1.1 绝对禁止的危险操作

❌ **严禁以下操作**（除非用户明确授权且理解后果）：

#### 禁止1：使用 `git checkout` 恢复文件 🚨🚨🚨

```bash
# ❌ 绝对禁止！会立即覆盖工作区，造成不可逆的数据丢失！
git checkout <commit> -- <file>
git checkout -- <file>
git checkout <commit> -- chapter_md/*.md

# ❌ 同样禁止（效果相同）
git restore <file>
git restore --source=<commit> <file>
```

**为什么禁止**：
- **破坏性**：无条件覆盖工作区文件，丢失所有未提交的修改，**无法撤销**
- **多进程风险**：可能破坏其他进程（IDE、脚本、人工编辑）正在进行的修改
- **协作冲突**：在多人协作时会覆盖他人的工作成果
- **难以追溯**：被覆盖的修改无法恢复，造成不可逆的工作损失
- **用户愤怒**：导致数小时工作成果瞬间清零，用户会极度愤怒

**历史教训**：
- 2026-04-01：错误使用 `git checkout 66d77fa7 -- <69个文件>` 恢复章节编号
  - 如果当时有其他进程正在修改这些文件，所有修改都会丢失
  - 应该使用脚本比较差异，只修复编号问题
- 2026-04-02：再次错误使用 `git checkout -- chapter_md/053-080_*.tagged.md`
  - 覆盖了刚完成的批量PN修复工作（64个章节，数小时工作量）
  - 覆盖了081-083的人名简称修复（16处精心修复）
  - 造成严重的工作成果丢失，需要全部重做
  - **教训**：任何时候都不能使用 `git checkout` 恢复文件，无论理由多么充分

#### 禁止2：擅自添加未暂存文件

```bash
# ❌ 禁止
git add -A    # 添加所有文件
git add .     # 添加当前目录所有文件
git add <任何文件>  # 除非用户明确要求
```

**为什么禁止**：
- 可能提交用户不想提交的文件（临时文件、调试代码等）
- 违反"只提交已暂存内容"原则

**🚨 Commit操作铁律**：
- **当用户说"commit"时，只执行 `git commit`，绝对不要先执行 `git add`**
- **当用户说"commit"时，只执行 `git commit`，绝对不要执行 `git reset`**
- **当用户说"commit"时，只执行 `git commit`，不要执行任何其他git操作**

#### 禁止3：跳过检查和强制推送

```bash
# ❌ 禁止（除非用户明确要求）
git commit --no-verify              # 跳过pre-commit hooks
git push --force                    # 强制推送
git push --force-with-lease         # 强制推送（带租约）
```

#### 禁止4：自动提交

- 必须用户明确要求时才执行 `git commit`
- 不要在用户不知情时提交代码

---

### 1.2 文件恢复的安全方案

当需要恢复文件到旧版本时，使用以下安全方案：

#### 方案1：查看差异，手动编辑修复（推荐）

```bash
# 1. 查看当前版本与旧版本的差异
git diff <commit> -- <file>

# 2. 根据diff结果，手动编辑文件只修复需要的部分
# 使用IDE或Edit工具精确修改
```

**优点**：
- 安全，不会丢失其他修改
- 精确控制修复范围
- 可以保留有价值的改动

**适用场景**：
- 需要修复部分内容（如编号错误）
- 不确定是否需要完全恢复

#### 方案2：编写脚本比较差异（批量修复推荐）

```python
import subprocess
import re

def safe_restore_numbering(file, old_commit):
    """安全地恢复文件的段落编号"""

    # 1. 获取旧版本内容
    result = subprocess.run(
        ['git', 'show', f'{old_commit}:{file}'],
        capture_output=True, text=True, check=True
    )
    old_content = result.stdout

    # 2. 读取当前版本内容
    with open(file, 'r', encoding='utf-8') as f:
        current_content = f.read()

    # 3. 提取旧版本的编号
    old_numbers = extract_numbering(old_content)

    # 4. 只替换编号，保留其他内容
    new_content = replace_numbering_only(current_content, old_numbers)

    # 5. 写回文件
    with open(file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True
```

**优点**：
- 安全，只修改目标内容
- 可批量处理
- 可验证修改范围

**适用场景**：
- 批量修复问题（如69个文件的编号错误）
- 需要恢复特定部分（编号、格式等）

#### 方案3：使用stash保护现有修改（完全恢复时）

```bash
# 仅在确认需要完全恢复文件时使用

# 1. 保存当前修改
git stash push -m "临时保存：准备恢复<file>到<commit>" -- <file>

# 2. 提取旧版本内容
git show <commit>:<file> > <file>

# 3. 验证恢复是否正确
git diff <file>

# 4a. 如果正确，删除stash
git stash drop

# 4b. 如果错误，恢复之前的修改
git stash pop
```

**优点**：
- 有后悔药，可以恢复
- 适合完全恢复场景

**缺点**：
- 仍然会丢失未stash的修改
- 需要手动管理stash

**适用场景**：
- 确认需要完全恢复文件
- 当前文件没有重要未提交修改

---

### 1.3 操作前的安全检查

**任何可能修改工作区文件的操作前**，必须：

```bash
# 1. 检查工作区状态
git status

# 2. 如果有未提交的修改，先确认是否需要保留
git diff

# 3. 如果需要保留，先提交或stash
git stash push -m "保存：执行<操作>前的状态"

# 4. 然后再执行操作
```

---

## 二、提交内容管理

### 2.1 只提交已暂存内容原则

**规则**：commit时只提交缓存区（staged）内容，提交消息只描述缓存区中的变更。

```bash
# ✅ 正确做法（假设用户已经手动git add了需要提交的文件）
git status                    # 确认暂存区内容
git diff --cached             # 查看具体改动
git commit -m "..."           # 只提交已暂存内容

# ❌ 错误做法
git add -A                    # 擅自添加所有文件
git commit -m "更新"          # 不清楚具体提交了什么
```

### 2.2 提交前必做检查

在执行commit前，**必须**先运行：

```bash
# 1. 查看未暂存的文件和已暂存的文件
git status

# 2. 查看已暂存文件的具体改动（将要提交的内容）
git diff --cached

# 3. 查看最近的commit历史（学习commit message风格）
git log --oneline -10
```

### 2.3 敏感文件检查

**禁止提交**：

- `.env` 文件（包含密钥）
- `credentials.json`（凭证文件）
- `*.key`、`*.pem`（私钥文件）
- 临时文件（`*.tmp`、`*.swp`、`*.bak`）
- 大型二进制文件（除非必要）

**提示**：如果用户尝试提交敏感文件，应警告并询问确认。

---

## 三、Commit Message格式（本项目规范）

### 3.1 标准格式

```
首行总结（做了什么，不超过50字）

模块A:
- 新增 xxx
- 更新 yyy

模块B:
- 修复 zzz

```

### 3.2 使用HEREDOC传递

**重要**：为确保格式正确，commit message必须通过HEREDOC传递：

```bash
git commit -m "$(cat <<'EOF'
首行总结（做了什么）

模块A:
- 新增 xxx
- 更新 yyy

EOF
)"
```

### 3.3 格式要求

#### 首行总结

- **长度**：不超过50字
- **内容**：一句话说明做了什么（动宾结构）
- **禁止**：不要自动添加版本号（如v3.1），版本号由用户决定

#### 详细描述

**按模块分组**：

```
章节标注:
- 完成001_五帝本纪实体标注
- 完成002_夏本纪实体标注

反思工具:
- 新增按类型反思脚本
- 更新反思报告格式
```

**分类动词**：

| 分类 | 动词 | 示例 |
|------|------|------|
| 新增 | 新增、添加、创建 | 新增SKILL_10c文档 |
| 更新 | 更新、修改、完善、优化 | 更新实体统计脚本 |
| 修复 | 修复、修正、解决 | 修复615处人名标注错误 |
| 删除 | 删除、移除、清理 | 删除过时的临时文件 |

---

## 四、常见场景处理

### 4.1 发现批量修改错误

**场景**：用 `git checkout` 错误地覆盖了文件

**补救措施**（有限）：

```bash
# 1. 立即检查git status
git status

# 2. 如果文件在暂存区，可以取消暂存
git restore --staged <file>

# 3. 如果已经覆盖且未暂存，无法恢复
# 只能从其他来源恢复（备份、IDE历史等）
```

**预防措施**（重要）：

```bash
# 每次批量操作前先stash
git stash push -m "批量修改前备份: $(date +%Y%m%d_%H%M%S)"

# 执行批量修改...

# 验证无误后删除stash
git stash drop

# 如果出错，恢复
git stash pop
```

### 4.2 关联Issue

**在commit message中引用Issue**：

```
修复标注完整性检查的编码问题

工具修复:
- 修复lint_text_integrity.py的UTF-8编码问题
- 添加BOM检测和处理逻辑

Fixes #15

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**关键词**：
- `Fixes #N` - 此commit修复了Issue #N（自动关闭Issue）
- `Closes #N` - 此commit关闭了Issue #N
- `Refs #N` - 此commit引用了Issue #N（不自动关闭）

---

## 五、提交检查清单

### 5.1 提交前检查

在执行commit前，确认：

- [ ] 已查看 `git status` 确认暂存区内容
- [ ] 已查看 `git diff --cached` 确认具体改动
- [ ] 已查看 `git log` 了解commit message风格
- [ ] commit message符合本项目格式规范
- [ ] 首行总结清晰准确（不超过50字）
- [ ] 详细描述按模块分组
- [ ] 使用了准确的动词（新增/更新/修复/删除）
- [ ] 包含了Co-Authored-By（使用AI助手时）
- [ ] 未包含敏感文件（.env、credentials等）
- [ ] 未自动添加版本号

### 5.2 提交后验证

提交完成后，验证：

- [ ] `git status` 显示working tree clean
- [ ] `git log -1` 显示的commit message正确
- [ ] 必要时push到remote：`git push`

---

## 六、与其他SKILL的关系

```
SKILL_10c Git代码版本管理规范
    ├─ 输入：暂存区内容（git add后的文件）
    ├─ 输出：commit历史
    │
    ├─ 依赖：
    │   └─ SKILL_10a（Issue管理）- commit关联Issue
    │
    └─ 支撑：
        ├─ SKILL_10b（每日工作日志）- commit是日志的数据源
        └─ SKILL_10d（CHANGELOG）- commit是CHANGELOG的数据源
```

---

## 七、FAQ

### Q1: 发现提交了错误的文件怎么办？

**A**: 如果还未push到remote：

```bash
# 方案1: 撤销commit，保留改动
git reset HEAD~1
# 重新add正确的文件
git add 正确的文件
git commit -m "..."

# 方案2: 使用amend（仅限未push）
git reset HEAD 错误的文件  # 从暂存区移除
git commit --amend
```

**如果已push到remote**：不建议修改，创建新commit修复。

### Q2: commit message写错了怎么办？

**A**: 如果还未push：

```bash
git commit --amend -m "$(cat <<'EOF'
正确的commit message
...
EOF
)"
```

**如果已push**：不建议修改，接受错误或创建新commit说明。

### Q3: 如何撤销commit？

**A**:

```bash
# 撤销最近1次commit，保留改动
git reset HEAD~1

# 撤销最近2次commit，保留改动
git reset HEAD~2

# 完全撤销commit和改动（危险！需用户明确授权）
git reset --hard HEAD~1
```

---

## 结语

**安全第一，最小影响，可追溯。**

本规范的核心是保护工作成果：
1. 禁止破坏性操作（`git checkout`恢复文件）
2. 提供安全替代方案（diff查看、脚本修复、stash保护）
3. 建立检查流程（提交前检查、提交后验证）

遵守这些规范，可以避免不可逆的工作损失，确保项目历史清晰可追溯。

---

**相关文档**：
- 项目Git规范总览：`CLAUDE.md`
- Issue管理：`SKILL_10a_Issue管理.md`
- 每日工作日志：`SKILL_10b_每日工作日志维护.md`
- CHANGELOG维护：`SKILL_10d_CHANGELOG编写规范.md`
- **事故复盘与恢复 playbook**：[`doc/incidents/2026-04-17_chapter_md_loss_and_recovery.md`](../doc/incidents/2026-04-17_chapter_md_loss_and_recovery.md)——50 章丢失后的完整恢复路径，主力工具 `scripts/git_restore_latest_blob.py`
