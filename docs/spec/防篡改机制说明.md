# 防篡改机制说明

## 问题背景

2026-03-26 发现严重bug：`logs/lint_text_integrity.txt` 被意外修改，新增5105行，删除1167行。

**根本原因**：AI Agent在处理标注文件时违反了"标注铁律"，篡改了原文字符。

## 防护措施

### 1. `.claudeignore` 文件

已创建 `.claudeignore` 文件，声明以下文件/目录为**只读**：

```
# Lint and validation logs - READ ONLY
logs/lint_text_integrity.txt

# Original text files - READ ONLY
data/txt/
```

**作用**：告知Claude Code这些文件不应被修改。

### 2. CLAUDE.md 中的标注铁律

在项目根目录的 `CLAUDE.md` 中已明确标注铁律（第18-37行）：

```markdown
## ⚠️ 标注铁律（最高优先级）

**绝对禁止修改原文字符**：

标注工作**只能添加 `〖TYPE 〗` 标记符号**，不得对原文字符做任何修改：

❌ **禁止的操作**：
- 不得增加原文没有的字符（汉字、标点、引号、空格等）
- 不得删除原文字符（汉字、标点、引号、空格等）
- 不得替换原文字符（汉字、标点、引号、空格等）
- 不得修改标点符号（全角半角转换、添加/删除标点等）
- 不得添加引号（原文无引号则标注文件也不应添加引号）

✅ **允许的操作**：
- 只能在原文字符周围添加 `〖TYPE 〗` 标记符号
- 消歧语法 `〖TYPE 显示名|规范名〗` 中的"规范名"不改变显示文本

**验证方法**：
- 将标注文件去除所有 `〖TYPE 〗` 符号后，所得纯文本必须与原始 `.txt` 文件逐字相同
- 使用 `python scripts/lint_text_integrity.py` 验证完整性
```

### 3. 验证脚本

项目已有验证脚本 `scripts/lint_text_integrity.py`，用于检测标注文件是否篡改原文。

**使用方法**：
```bash
python scripts/lint_text_integrity.py
```

**检查内容**：
- 去除标注符号后，标注文件与原始txt文件是否逐字相同
- 输出详细的差异报告（实质差异、标点差异、编码差异等）

### 4. Git 工作流程

**提交前检查**：
- 在 `git add` 标注文件前，必须运行 `python scripts/lint_text_integrity.py`
- 确认没有"实质差异"后才能提交
- 如有实质差异，必须修复后再提交

**修复流程**：
```bash
# 1. 发现问题
git diff data/annotated/某章.md

# 2. 如果篡改了原文，立即恢复
git restore data/annotated/某章.md

# 3. 重新标注（只添加标记，不改原文）
```

## 常见篡改类型及预防

### 类型1: 字符替换

**错误示例**：
- 原文："阬"（通假字）
- 标注："坑"（现代字）
- ❌ 这是**篡改**！

**正确做法**：
- 原文："阬"
- 标注：`〖#阬|坑〗`（用消歧语法，不改显示文本）

### 类型2: 删除字符

**错误示例**：
- 原文："仁义不施"
- 标注："不施"（删除"仁义"）
- ❌ 这是**篡改**！

**正确做法**：
- 原文："仁义不施"
- 标注：`〖~仁义〗不施`（标记"仁义"，但保留原文）

### 类型3: 插入标点

**错误示例**：
- 原文："直将吏入行射"
- 标注："直将吏入，行射"（加逗号）
- ❌ 这是**篡改**！

**正确做法**：
- 原文："直将吏入行射"
- 标注：保持原样，不加标点

## 监控机制

### 人工监控

- **定期检查**：每次commit前检查 `logs/lint_text_integrity.txt`
- **差异审查**：如果lint日志有大量变化（>100行），立即警觉
- **Git diff**：提交前用 `git diff` 检查所有标注文件

### 自动监控

建议添加 Git pre-commit hook：

```bash
#!/bin/bash
# .git/hooks/pre-commit

# 检查是否修改了标注文件
if git diff --cached --name-only | grep -q "data/annotated/"; then
    echo "检测到标注文件变更，运行完整性检查..."
    python scripts/lint_text_integrity.py

    if [ $? -ne 0 ]; then
        echo "❌ 完整性检查失败！请修复后再提交。"
        exit 1
    fi
fi

# 检查是否修改了lint日志（不应该被修改）
if git diff --cached --name-only | grep -q "logs/lint_text_integrity.txt"; then
    echo "⚠️  警告：lint_text_integrity.txt 不应该被手动修改！"
    echo "请运行 git restore logs/lint_text_integrity.txt"
    exit 1
fi
```

## 应急响应

### 发现篡改后的处理流程

1. **立即停止所有操作**
2. **对比差异**：使用 `git diff <被篡改的文件>` 查看所有变更
3. **区分篡改与正常新增**：
   - 篡改：原文字符被替换/删除/插入（如"阬"→"坑"）
   - 正常新增：新章节的检查结果、时间戳更新等
4. **手动修复**：
   - **不要** `git restore`（会丢失工作成果）
   - 使用编辑器手动恢复被篡改的原文
   - 保留正常的新增内容
5. **分析原因**：检查哪个操作导致篡改
6. **加强约束**：更新 CLAUDE.md 或 .claudeignore
7. **记录事件**：在本文档中记录事件和教训

## 历史事件记录

### 事件001: lint日志大量篡改 (2026-03-26)

**发现时间**：2026-03-26
**受影响文件**：`logs/lint_text_integrity.txt`
**变化规模**：+5105行，-1167行
**篡改类型**：
- 将"阬"替换为"坑"（多处）
- 删除"仁义"（多处）
- 删除"公"（多处）
- 插入标点符号（多处）

**根本原因**：AI Agent在某个环节执行了标注任务，但违反了"标注铁律"

**修复措施**：
1. ⚠️ **不要** `git restore`（会丢失工作成果）
2. ✅ 创建 `.claudeignore`（已创建）
3. ✅ 创建本防篡改文档（已创建）
4. ⏳ 待执行：对比git diff，手动修复被篡改的原文，保留正常的新增内容

**预防措施**：
- 将 `logs/lint_text_integrity.txt` 加入 `.claudeignore`
- 在 CLAUDE.md 顶部强调"标注铁律"优先级最高
- 建议用户添加 Git pre-commit hook

**教训**：
- ⚠️ AI Agent可能在不经意间违反约束，需要多层防护
- ⚠️ 只读文件必须明确声明（`.claudeignore`）
- ⚠️ 定期检查git diff，及时发现异常变更

---

**文档版本**：v1.0
**创建时间**：2026-03-26
**维护者**：项目团队
**最后更新**：2026-03-26
