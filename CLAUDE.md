# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

《史记》知识库：用AI Agent将《史记》130篇转化为结构化知识图谱。

## 项目约定

- 不要自动 commit。只在用户明确要求时才执行 git commit。
- 反思流程全自动。每章的 Agent 反思循环不需要用户逐步确认，直接执行完整流程。
- 对话和输出以中文为主。
- 当用户在对话中明确要求自动确认时，后续操作不再逐步询问，自动执行。
- commit时只提交用户已暂存（git add）的文件，不得擅自 `git add -A` 或 `git add .` 添加未暂存的文件。
- commit message不要自动加版本号（如v3.1），版本号由用户决定。

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

### 基本原则

- **按日期组织**：每个日期一个条目（格式：`## YYYY-MM-DD`）
- **高层次总结**：只保留核心变更的总体说明，删除过多细节
- **链接详细日志**：每个日期条目底部必须链接到 `logs/daily/YYYY-MM-DD.md`
- **链接commit ID**：每个核心功能必须链接到对应的git commit（格式：`[commit_id](github_url)` 或直接使用短hash）
- **分类清晰**：使用标准分类（Added/Changed/Fixed/Removed）

### 内容详略原则

**保留在CHANGELOG中的内容**：
- 核心功能的总体描述（1-2行概括）
- 重要的新增模块/系统名称和主要链接
- 关键数字（如修复数量、完成章节数）
- 用户可见的重大变更

**移入每日工作日志的内容**：
- 详细的子项列表
- 具体的文件路径和技术细节
- 多层级的嵌套说明
- 每个SKILL/示例的完整列表
- 具体的技术实现方法

### 格式模板

```markdown
## YYYY-MM-DD

### 新增 (Added)

- **功能名称** ([主要链接]) ([commit_id](github_commit_url))
  - 核心特性概括（1行）
  - 次要说明（可选，1行）

### 修复 (Fixed)

- **问题名称** ([commit_id](github_commit_url))：简短说明+关键数字

### 更改 (Changed)

- **模块名称** ([commit_id](github_commit_url))：变更概括

**详细工作日志**: [`logs/daily/YYYY-MM-DD.md`](logs/daily/YYYY-MM-DD.md)
```

### Commit链接格式

**GitHub链接格式**：
```markdown
[0117a825](https://github.com/baojie/shiji-kb/commit/0117a825)
```

**简化格式**（推荐）：
```markdown
([0117a825])
```
说明：GitHub会自动识别commit短hash并创建链接

### 示例对比

❌ **过于详细**（应简化）：
```markdown
- **司马迁文风提炼实验** ([`labs/sima-qian-style/`](labs/sima-qian-style/))：
  - 三层SKILL架构：现代名词古化 → 白话转文言 → 太史公风格
  - 4个SKILL文件：
    - SKILL-太史公曰.md（主SKILL，高级层）
    - SKILL-白话转文言.md（基础层，9大类转换规则）
    - SKILL-现代名词古化.md（子技能，7大类名词词典）
    - SKILL-核心特征.md（太史公文笔8大维度）
  - 4个完整示例：
    - 乔布斯列传（人物传记体）
    - shiji-kb记（项目介绍，333字完整版）
    - 葛底斯堡演讲（经典演讲，272字）
    - 论Skill之道（技术概念）
  - 快速上手教程（三种使用方法）
```

✅ **精简版本**（推荐）：
```markdown
- **司马迁文风提炼实验** ([`labs/sima-qian-style/`](labs/sima-qian-style/)) ([0117a825] / [c7a0d55c])
  - 三层SKILL架构（现代名词古化 → 白话转文言 → 太史公风格）
  - 包含4个SKILL文件和4个完整示例（乔布斯列传、shiji-kb记、葛底斯堡演讲、Skill概念）
```

**说明**：
- 主要功能链接到代码目录：`[`labs/sima-qian-style/`](labs/sima-qian-style/)`
- Commit链接使用短hash：`([0117a825])` 或完整URL：`([0117a825](https://github.com/baojie/shiji-kb/commit/0117a825))`
- 多个相关commit用斜杠分隔：`([0117a825] / [c7a0d55c])`

### 更新流程

1. **修改CHANGELOG时**：先精简条目，再链接到详细日志
2. **日志已存在**：确保详细内容在 `logs/daily/YYYY-MM-DD.md` 中完整记录
3. **保持一致性**：CHANGELOG概括性描述 + 工作日志详细记录

