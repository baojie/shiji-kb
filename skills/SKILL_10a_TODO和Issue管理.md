---
name: skill-10a
title: TODO和Issue管理
description: GitHub Issue分类管理与TODO任务对应流程。确保项目需求、缺陷、参考资源有序管理，与TODO任务系统联动。适用于项目管理、需求跟踪、社区协作等场景。
---

# SKILL 10a: TODO和Issue管理 — 项目任务的指挥中枢

> **核心理念**：Issue是需求的入口，TODO是执行的抓手。

---

## 一、Issue分类体系

### 1.1 七类标签

本项目使用七类标签对GitHub Issue进行分类管理：

| 标签 | 含义 | 颜色 | 典型用途 | 示例 |
|------|------|------|---------|------|
| **REF-参考** | 参考项目或资源 | 绿色 `#0E8A16` | 外部项目、论文、工具、平台 | 识典古籍、FoJin佛经平台、巴黎圣母院数字化项目 |
| **FEAT-功能** | 新功能建议 | 浅蓝 `#A2EEEF` | 用户需求、功能增强、新特性 | 苹果app开发、拼音注释、人物关系网 |
| **BUG-缺陷** | 缺陷报告 | 红色 `#D73A4A` | 错误、问题、不一致 | 标注错误、校勘问题 |
| **RES-资源** | 本项目资源 | 黄色 `#FBCA04` | 本项目可整合的资源 | 百衲本、三朝北盟汇编 |
| **DOC-文档** | 文档改进、说明完善 | 蓝色 `#0075CA` | README更新、SKILL完善、注释补充 | 完善安装文档、添加使用示例 |
| **HELP-求助** | 需要帮助或指导 | 青绿 `#008672` | 技术难题、方法咨询、资源请求 | 如何部署、寻找数据源 |
| **QA-提问** | 问题咨询、疑问讨论 | 紫色 `#D876E3` | 概念澄清、原理询问、使用疑问 | 标注规范是什么、为何这样设计 |

### 1.2 分类原则

**判断流程**：

```
Issue标题/内容
    │
    ├─ 包含"REF"或"by xxx"且为外部资源？ → REF-参考
    │
    ├─ 报告错误/问题/不一致？ → BUG-缺陷
    │
    ├─ 提出功能需求/建议？ → FEAT-功能
    │
    ├─ 本项目可用资源（古籍版本/数据）？ → RES-资源
    │
    ├─ 文档改进、说明完善？ → DOC-文档
    │
    ├─ 寻求帮助、请求指导？ → HELP-求助
    │
    └─ 提问、询问、概念澄清？ → QA-提问
```

**示例分类**：

```bash
# REF-参考
- Issue #24: "REF 17-z.com"
- Issue #27: "AI以经注经：如何拆分A文本群来注释B文本？by 周渊"

# FEAT-功能
- Issue #34: "开发史记知识库苹果app"
- Issue #25: "希望增加拼音注释，方便阅读"
- Issue #21: "战争路线历史地图"

# BUG-缺陷
- Issue #15: "校勘问题"
- Issue #12: "太多错误，作为实验性玩具还行"
- Issue #11: "标注错误"

# RES-资源
- Issue #23: "百衲本"
- Issue #6: "add 三朝北盟汇编 by ash"

# DOC-文档
- 完善README安装说明
- 添加SKILL使用示例

# HELP-求助
- Issue #14: "你留的微信号搜不到"

# QA-提问
- 标注符号的设计原理是什么？
- 为什么使用〖〗而不是[]？
```

---

## 二、Issue生命周期管理

### 2.1 Issue状态流转

```
Open（开放）
    │
    ├─ REF-参考 → 整理到 resources/references/README.md → Close（已完成）
    │
    ├─ RES-资源 → 评估 → 下载/整合 → Close（已完成）
    │
    ├─ FEAT-功能 → 评估 → 创建TODO → 开发 → Close（已完成）
    │
    ├─ BUG-缺陷 → 复现 → 创建TODO → 修复 → Close（已完成）
    │
    ├─ DOC-文档 → 创建TODO → 编写/更新文档 → Close（已完成）
    │
    ├─ HELP-求助 → 提供帮助/指导 → Close（已解决）或标记为"需要更多信息"
    │
    └─ QA-提问 → 回答问题 → Close（已回答）或转为DOC（需要文档化）
```

### 2.2 REF-参考的处理流程

**标准流程**（参见本次操作示例）：

1. **识别REF类Issue**：标题包含"REF"或明确是参考资源
2. **整理到README**：添加到 `resources/references/README.md`
   - 按类别归档（数字人文项目、古籍数字化平台、历史地图可视化等）
   - 记录关键信息（网址、开发方、核心功能、技术栈）
   - 添加"与本项目关联"说明
3. **关闭Issue并回复**：
   ```markdown
   已添加到参考文献: [resources/references/README.md](链接)

   归档位置：{分类} > {项目名称}
   ```

**示例操作**：

```bash
# 1. 创建标签（首次）
gh label create "REF-参考" --description "参考项目或资源" --color "0E8A16"

# 2. 批量分类（见下节脚本）

# 3. 关闭REF类Issue
gh issue comment 32 --body "已添加到参考文献: [resources/references/README.md](链接)\n\n归档位置：古籍数字化平台 > 巴黎圣母院数字化项目（e-NDP）"
gh issue close 32 --reason completed
```

### 2.3 FEAT/BUG的TODO对应

**原则**：每个需要执行的FEAT/BUG Issue都应对应一个或多个TODO任务。

**对应关系**：

| Issue类型 | TODO示例 | 状态同步 |
|----------|---------|---------|
| FEAT-功能 | "调研拼音注释方案"、"实现拼音标注" | Issue关闭 ↔ TODO全部completed |
| BUG-缺陷 | "复现标注错误"、"修复002_夏本纪标注" | Issue关闭 ↔ TODO全部completed |

---

## 三、批量Issue管理

### 3.1 创建标签

```bash
# 一次性创建全部七类标签
gh label create "REF-参考" --description "参考项目或资源" --color "0E8A16"
gh label create "FEAT-功能" --description "新功能建议" --color "A2EEEF"
gh label create "BUG-缺陷" --description "缺陷报告" --color "D73A4A"
gh label create "RES-资源" --description "本项目资源" --color "FBCA04"
gh label create "DOC-文档" --description "文档改进、说明完善" --color "0075CA"
gh label create "HELP-求助" --description "需要帮助或指导" --color "008672"
gh label create "QA-提问" --description "问题咨询、疑问讨论" --color "D876E3"
```

### 3.2 批量分类脚本

```bash
#!/bin/bash
# issue_classification.sh

# REF-参考 (标题包含REF或明确是参考资源)
gh issue edit 24 --add-label "REF-参考"
gh issue edit 27 --add-label "REF-参考"

# FEAT-功能 (功能请求)
gh issue edit 34 --add-label "FEAT-功能"
gh issue edit 25 --add-label "FEAT-功能"
gh issue edit 21 --add-label "FEAT-功能"
# ... 更多

# BUG-缺陷 (问题报告)
gh issue edit 15 --add-label "BUG-缺陷"
gh issue edit 12 --add-label "BUG-缺陷"
# ... 更多

# RES-资源 (本项目资源)
gh issue edit 23 --add-label "RES-资源"
gh issue edit 6 --add-label "RES-资源"

# DOC-文档 (文档改进)
# (待添加具体Issue)

# HELP-求助 (需要帮助)
gh issue edit 14 --add-label "HELP-求助"

# QA-提问 (问题咨询)
# (待添加具体Issue)
```

### 3.3 查看分类结果

```bash
# 按标签查看
gh issue list --label "REF-参考"
gh issue list --label "FEAT-功能"
gh issue list --label "BUG-缺陷"
gh issue list --label "RES-资源"

# 查看全部issue及其标签
gh issue list --state open --json number,title,labels | \
  jq -r '.[] | "\(.number)\t\(.title)\t\(.labels | map(.name) | join(", "))"' | \
  sort -n
```

**输出示例**：

```
3	字典 by 三花猫	FEAT-功能
5	加插图 by 元治	FEAT-功能
6	add 三朝北盟汇编 by ash	RES-资源
11	标注错误	BUG-缺陷
14	你留的微信号搜不到	HELP-求助
24	REF 17-z.com	REF-参考
27	AI以经注经：如何拆分A文本群来注释B文本？by 周渊	REF-参考
```

---

## 四、Issue与TODO联动

### 4.1 从Issue创建TODO

**典型流程**：

```markdown
1. 用户提交Issue #25: "希望增加拼音注释，方便阅读"
   ↓
2. 评估可行性，添加标签 "FEAT-功能"
   ↓
3. 创建TODO任务：
   - 调研拼音注释技术方案
   - 设计拼音标注语法
   - 实现拼音标注工具
   - 为001-012本纪添加拼音
   ↓
4. 执行TODO任务（status: pending → in_progress → completed）
   ↓
5. 全部TODO完成后，关闭Issue #25
   ↓
6. 在Issue下回复：
   "已完成拼音注释功能，见commit [abc1234]"
```

**TODO示例**：

```json
{
  "content": "调研拼音注释技术方案",
  "status": "in_progress",
  "activeForm": "调研拼音注释技术方案",
  "relatedIssue": "#25"
}
```

### 4.2 TODO任务分解原则

| Issue复杂度 | TODO数量 | 示例 |
|-----------|---------|------|
| **简单** | 1个TODO | Issue #11"标注错误" → TODO"修复002_夏本纪标注错误" |
| **中等** | 2-3个TODO | Issue #25"拼音注释" → TODO"调研方案"、"实现工具"、"标注本纪" |
| **复杂** | 5+个TODO | Issue #34"苹果app" → TODO"需求分析"、"技术选型"、"UI设计"、"数据接口"、"测试发布" |

### 4.3 TODO状态与Issue状态映射

```
TODO状态          Issue状态
────────────────────────────
全部pending      → Open (未开始)
部分in_progress  → Open (进行中)
全部completed    → Close (已完成)
```

---

## 五、实战案例

### 5.1 案例1: REF类Issue批量处理

**背景**：2026-03-29，有4个REF类Issue需要整理

**操作步骤**：

```bash
# 1. 查看REF类Issue
gh issue list --state open --limit 100 --json number,title | \
  jq -r '.[] | select(.title | test("ref"; "i")) | "\(.number)\t\(.title)"'

# 输出:
# 32	REF  巴黎圣母院数据化项
# 31	REF 识典古籍
# 30	REF  https://chinawarfare.pages.dev/
# 22	add ref

# 2. 获取详细信息并整理到README
gh issue view 32 --json title,body,url
# ... 编辑 resources/references/README.md

# 3. 关闭Issue并回复
gh issue comment 32 --body "已添加到参考文献: [resources/references/README.md](链接)\n\n归档位置：古籍数字化平台 > 巴黎圣母院数字化项目（e-NDP）"
gh issue close 32 --reason completed

# 4. 重复步骤3处理Issue #31, #30, #22
```

**结果**：4个REF类Issue全部归档并关闭，参考文献库增加4个项目

### 5.2 案例2: FEAT类Issue → TODO任务

**背景**：Issue #34 "开发史记知识库苹果app"

**TODO分解**：

```json
[
  {
    "content": "需求分析：明确app核心功能",
    "status": "pending",
    "activeForm": "需求分析：明确app核心功能"
  },
  {
    "content": "技术选型：iOS/macOS开发框架",
    "status": "pending",
    "activeForm": "技术选型：iOS/macOS开发框架"
  },
  {
    "content": "数据接口设计：知识图谱API",
    "status": "pending",
    "activeForm": "数据接口设计：知识图谱API"
  },
  {
    "content": "UI/UX设计：多维度导航界面",
    "status": "pending",
    "activeForm": "UI/UX设计：多维度导航界面"
  },
  {
    "content": "MVP开发：基础阅读器",
    "status": "pending",
    "activeForm": "MVP开发：基础阅读器"
  }
]
```

**执行流程**：

1. Issue #34创建
2. 添加标签"FEAT-功能"
3. 创建5个TODO任务
4. 逐步执行（pending → in_progress → completed）
5. 全部TODO完成后关闭Issue #34

### 5.3 案例3: BUG类Issue快速修复

**背景**：Issue #11 "标注错误"

**TODO分解**：

```json
[
  {
    "content": "复现Issue #11标注错误",
    "status": "in_progress",
    "activeForm": "复现Issue #11标注错误"
  },
  {
    "content": "修复标注错误",
    "status": "pending",
    "activeForm": "修复标注错误"
  },
  {
    "content": "验证修复结果",
    "status": "pending",
    "activeForm": "验证修复结果"
  }
]
```

**关闭Issue时回复**：

```markdown
已修复标注错误，见commit [abc1234]

修复内容：
- 002_夏本纪.tagged.md:195 "五子之歌" → "五子作歌"
- 通过 python scripts/lint_text_integrity.py 002 验证
```

### 5.4 案例4: TODO→Issue大迁移 (2026-03-30实战)

**背景**：TODO.md积累了大量功能建议，需要整理迁移到GitHub Issues

**操作步骤**：

#### 第一阶段：功能建议迁移 (29个)

```bash
# 1. 分析TODO.md，识别功能建议类任务
# 分类：
# - BUG类: 1个 (P0级缺陷)
# - FEAT类 - 阅读体验: 12个
# - FEAT类 - 数据与内容: 6个
# - FEAT类 - 工程与架构: 4个
# - FEAT类 - 未来探索: 6个

# 2. 批量创建Issues
gh issue create --label "BUG-缺陷" \
  --title "【P0】修复被篡改的原文字符" \
  --body "..."

gh issue create --label "FEAT-功能" \
  --title "实体悬浮预览" \
  --body "..."

# ... 重复29次

# 3. 更新TODO.md
# - 删除已迁移的功能建议章节
# - 添加"近期转移到Issue的任务"章节，包含全部29个Issue链接
```

#### 第二阶段：已完成任务归档 (21个)

```bash
# 1. 识别已完成任务
# - "最新完成 (2026-03-21)": 5个
# - "历史完成 (2026-03-18)": 1个
# - "已完成"表格: 15个

# 2. 创建Issue并立即关闭
for task in completed_tasks; do
  # 创建Issue
  issue_url=$(gh issue create --label "FEAT-功能" \
    --title "$task_title" \
    --body "$task_body_with_commits")

  # 提取Issue编号
  issue_num=$(echo $issue_url | grep -oP '\d+$')

  # 立即关闭
  gh issue close $issue_num --reason completed \
    --comment "✅ 已完成于$date\n\n相关Commit:\n- [$commit_id](...)"
done

# 示例：
# Issue #64: 为所有SKILL添加YAML frontmatter (89b1c38a)
# Issue #65: 司马迁文风研究实验 (0117a825)
# Issue #69: 动词标注体系 v3.0 (cca73582)
# ... #64-#84 共21个
```

#### 第三阶段：进展追踪更新 (9个)

```bash
# 1. 检查open issues，查找已有工作进展的
git log --oneline --all --grep="关键词" | head -10

# 2. 为有进展的Issues添加评论
gh issue comment 49 --body "## 工作进展

✅ **已完成部分**：
- 太史公曰/赞已完成 fenced div 标注（130篇全部完成）
- 韵文专项索引已建立（96篇赞/诗歌/赋）

⏳ **待完成部分**：
- 歌谣/骚体识别与统一缩进排版

## 相关Commit
- [5ef38163](...)
- [cf9f4f5c](...)"

# 示例Issues:
# #49 韵文识别与排版 - ✅ 部分完成
# #35 修复被篡改的原文字符 - ⚠️ 已识别
# #21 战争路线历史地图 - 📋 已规划
# #40 地铁图换乘设计优化 - 🚧 进行中
# #9, #46 排版实验 - ✅ 已有实验
# #52 事件罗生门 - 📋 方法已建立
# #62 词云生成 - 📋 已规划
# #12 错误修复 - 🔧 持续修复中
```

#### 第四阶段：功能完成确认 (4个)

```bash
# 发现多个已完成但Issue仍open的功能

# 示例1: #53 十表导出CSV
ls data/tables/data/*.csv  # 确认CSV文件存在
git log --oneline --all -- "data/tables/data/*.csv"
gh issue close 53 --reason completed

# 示例2: #47 响应式设计
grep "max-width" css/shiji-styles.css  # 确认响应式CSS
grep "viewport" docs/chapters/*.html  # 确认viewport meta标签
gh issue close 47 --reason completed

# 示例3: #54 非对称标签
grep "〖@" chapter_md/001_*.tagged.md  # 确认〖TYPE X〗格式
git log --oneline --grep="v2.8"  # 找到v2.8格式迁移commit
gh issue close 54 --reason completed

# 示例4: #51 新实体类型评估
# 确认18类实体体系完整性
git log --oneline --grep="v2\.[0-9]"
gh issue close 51 --reason completed --body "18类实体体系v1.0→v2.8演进完成"
```

**成果统计**：

| 操作类型 | 数量 | Issue编号 |
|---------|------|-----------|
| 创建Open Issues | 29个 | #35-#63 |
| 创建并关闭（已完成任务归档）| 21个 | #64-#84 |
| 关闭已完成功能 | 4个 | #53, #47, #54, #51 |
| 添加进展评论 | 9个 | #9,#12,#21,#35,#40,#46,#49,#52,#62 |
| **总计** | **63次操作** | **50个Issues** |

**更新TODO.md**：

```markdown
## 📝 近期转移到Issue的任务

### 2026-03-30: 功能建议大迁移
从TODO.md迁移29个任务到GitHub Issues...
- [#35-#63] 完整列表

## ✅ 近期关闭的Issue（已完成任务归档）

### 2026-03-30: 已完成任务迁移到Issues
- [#64-#84] 21个已完成任务

### 2026-03-30: 功能完成确认
- [#53] 十表导出CSV
- [#47] 响应式设计优化（移动端）
- [#54] 实体标注格式改为非对称标签
- [#51] 新实体类型评估（18类实体体系）
```

**经验总结**：

1. **批量操作效率**：使用脚本批量创建15个Issues，避免重复操作
2. **commit链接价值**：为已完成任务标注commit，方便追溯实现细节
3. **进展评论重要**：为open issues添加进展评论，避免重复开发
4. **定期整理**：TODO积累到200行+时应及时整理迁移
5. **分类清晰**：按BUG/FEAT/DOC等7类标签分类，便于优先级管理

---

## 六、项目专用脚本

### 6.1 TODO与Issue关联脚本

```python
# scripts/sync_todo_issue.py

import json

def create_todos_from_issue(issue_number, issue_title, tasks):
    """从Issue创建TODO任务列表"""
    todos = []
    for task in tasks:
        todos.append({
            "content": f"{task} (Issue #{issue_number})",
            "status": "pending",
            "activeForm": f"{task} (Issue #{issue_number})",
            "relatedIssue": f"#{issue_number}"
        })
    return todos

# 示例用法
tasks = [
    "需求分析：明确app核心功能",
    "技术选型：iOS/macOS开发框架",
    "数据接口设计：知识图谱API"
]

todos = create_todos_from_issue(34, "开发史记知识库苹果app", tasks)
print(json.dumps(todos, indent=2, ensure_ascii=False))
```

---

## 七、本项目特定规范

### 7.1 史记项目的Issue管理要点

1. **REF类Issue必须归档到 `resources/references/README.md`**，不得遗漏
2. **标注错误类BUG必须通过 `python scripts/lint_text_integrity.py` 验证修复**
3. **关闭Issue时注明commit链接和归档位置**

### 7.2 TODO与Issue联动要点

1. **创建TODO时在content字段注明Issue编号**（如"修复标注错误 (Issue #11)"）
2. **关闭Issue前确保所有相关TODO已completed**
3. **标注类Issue的TODO必须包含验证步骤**

### 7.3 用户术语约定

**重要**：用户使用"TODO"一词时，具体含义取决于上下文：

| 用户说法 | 实际含义 | 对应操作 |
|---------|---------|---------|
| "写入TODO" | 写入TODO.md文件 | 编辑 `TODO.md` 文件，添加任务条目 |
| "加入TODO" | 写入TODO.md文件 | 编辑 `TODO.md` 文件，添加任务条目 |
| "添加到TODO" | 写入TODO.md文件 | 编辑 `TODO.md` 文件，添加任务条目 |
| "使用TodoWrite工具" | 创建临时追踪任务 | 使用 `TodoWrite` 工具创建会话级TODO列表 |

**关键区别**：
- **TODO.md文件**：持久化的项目任务列表，git跟踪，面向项目管理
- **TodoWrite工具**：会话级临时任务跟踪，不持久化，面向当前工作流程

**最佳实践**：
1. 当用户说"写入TODO"/"加入TODO"时，默认操作 `TODO.md` 文件
2. 只有明确说"使用TodoWrite工具"时，才调用 `TodoWrite` 工具
3. 对话结束后，TodoWrite工具的内容会消失，TODO.md文件的内容会保留

---

## 八、TODO文件整理规范

### 8.1 TODO.md的定位

**核心原则**：TODO.md保留核心开发任务和执行中的流程任务，功能建议类任务迁移到GitHub Issues。

**TODO.md适合保留的内容**：
- 🏗️ **大型重构任务**：有详细spec文档的系统性改造（如目录结构重构）
- 🔥 **执行中的流程任务**：有完整SKILL和spec的反思管线（如人物生卒年反思、姓氏推理）
- 📋 **内部开发任务**：技术实现细节、脚本开发、数据处理（如繁简映射系统）
- ⚙️ **流程改进任务**：工作流优化、工具链建设（如实体标注反思管线）

**应迁移到GitHub Issues的内容**：
- 🎨 **阅读体验功能**：UI/UX改进、交互设计（如实体悬浮预览、段落便签）
- 📚 **数据与内容功能**：内容增强、数据整合（如与中华书局版校对、韵文排版）
- 🔧 **工程与架构功能**：架构升级、技术选型（如Neo4j导入、CI/CD）
- 💡 **未来探索功能**：前瞻性研究、创新实验（如文献对勘、RAG问答）
- 🐛 **用户报告的BUG**：来自社区的问题报告

### 8.2 定期整理TODO.md

**整理频率**：每月1次，或当TODO.md超过200行时

**整理步骤**：

1. **审查待办任务**：
   ```bash
   # 检查TODO.md中的待办任务
   grep -c "^- \[ \]" TODO.md
   ```

2. **分类识别**：
   - 标记哪些是"核心开发任务"（保留在TODO.md）
   - 标记哪些是"功能建议"（迁移到Issues）

3. **迁移到Issues**：
   ```bash
   # 按分类批量创建Issues（见下节8.3）
   ```

4. **更新TODO.md**：
   - 删除已迁移的任务
   - 添加说明："功能建议类任务已迁移至 [GitHub Issues](链接)"
   - 更新"最后更新"时间戳

5. **归档已完成任务**：
   - 将"✅ 最新完成"移到"✅ 历史完成"
   - 保持"✅ 最新完成"只显示近期（如最近1个月）

### 8.3 批量创建Issues（TODO→Issue迁移）

**迁移脚本示例**（2026-03-30实战）：

```bash
#!/bin/bash
# 从TODO.md批量创建Issues

# BUG类
gh issue create --label "BUG-缺陷" \
  --title "【P0】修复被篡改的原文字符" \
  --body "## 问题描述

\`logs/lint_text_integrity.txt\` 被篡改 +5105行/-1167行，违反「标注铁律」。

## 篡改类型
- 将「阬」替换为「坑」
- 删除「仁义」、「公」等原文字符
- 插入标点符号

## 优先级
**P0 - 最高优先级**"

# FEAT类 - 阅读体验
gh issue create --label "FEAT-功能" \
  --title "实体悬浮预览" \
  --body "## 功能描述

鼠标悬停在实体标注上时，侧边栏显示：
- 实体简介
- 全书所有出现的上下文

## 分类
阅读体验增强"

gh issue create --label "FEAT-功能" \
  --title "段落便签系统" \
  --body "## 功能描述

每段正文右侧显示彩色小便签，集成段落摘要与事件关联。

## 设计要点
### Markdown扩展语法
\`\`\`markdown
【黄帝战蚩尤·001-005】
@黄帝@闻@蚩尤@作乱，乃征师诸侯...
\`\`\`

## 分类
阅读体验增强"

# FEAT类 - 数据与内容
gh issue create --label "FEAT-功能" \
  --title "与中华书局版电子版校对" \
  --body "## 功能描述

对照点校本，核查正文文字差异。

## 优先级
优先年表 013-022

## 分类
数据与内容"

# FEAT类 - 工程与架构
gh issue create --label "FEAT-功能" \
  --title "Neo4j图数据库导入" \
  --body "## 功能描述

将知识图谱导入Neo4j，支持图查询。

## 分类
工程与架构"

# FEAT类 - 未来探索
gh issue create --label "FEAT-功能" \
  --title "文献对勘" \
  --body "## 功能描述

史记与《左传》《战国策》《汉书》重叠段落对照。

## 分类
未来探索"
```

**迁移后更新TODO.md**：

```markdown
> **重要说明**：
> - 本文件保留核心开发任务和执行中的流程任务
> - 功能建议类任务已迁移至 [GitHub Issues](https://github.com/baojie/shiji-kb/issues)
> - Issue管理规范见 [SKILL_10a](skills/SKILL_10a_TODO和Issue管理.md)

## 🔥 近期优先

> **说明**：阅读体验、数据与内容、工程与架构、未来探索等功能建议已迁移到 [GitHub Issues](链接)

### 常规优先任务

- [ ] **人物生卒年反思**：四轮反思推断...（保留）
- [ ] **反常推理**：检测违反常识...（保留）
- [ ] **姓氏推理**：为先秦人物...（保留）
```

### 8.4 迁移时的Issue模板

**功能建议类Issue模板**：

```markdown
## 功能描述
{简短描述功能}

## 使用场景
{用户使用场景}

## 设计要点
{关键设计点}

## 相关Issue
{如有关联Issue，列出编号}

## 分类
{阅读体验增强/数据与内容/工程与架构/未来探索}
```

**BUG类Issue模板**：

```markdown
## 问题描述
{问题现象}

## 复现步骤
{如何复现}

## 修复方法
{建议修复方案}

## 优先级
{P0/P1/P2}
```

### 8.5 迁移记录

**建议在TODO.md中保留迁移记录**：

```markdown
## 📝 Issue迁移记录

### 2026-03-30: 功能建议大迁移

从TODO.md迁移29个功能建议到GitHub Issues：
- BUG类: 1个 (#35)
- FEAT类 - 阅读体验: 12个 (#36-#47)
- FEAT类 - 数据与内容: 6个 (#48-#53)
- FEAT类 - 工程与架构: 4个 (#54-#57)
- FEAT类 - 未来探索: 6个 (#58-#63)

**查看全部Issues**: [GitHub Issues](https://github.com/baojie/shiji-kb/issues)
```

---

## 结语

**Issue是需求的入口，TODO是执行的抓手。** 通过七类标签体系和TODO联动机制，将社区反馈、功能需求、缺陷报告有序转化为可执行的任务。

**定期整理TODO.md，保持任务列表清晰。** 将功能建议迁移到GitHub Issues，让TODO.md专注于核心开发和流程任务。

每个Issue都应有明确归宿，每个TODO都应有清晰来源。
