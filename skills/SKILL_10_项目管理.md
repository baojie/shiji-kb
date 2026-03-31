---
name: skill-10
title: 项目管理
description: 项目管理全流程，包括Issue分类管理、TODO任务跟踪、每日工作日志维护、团队协作规范等。确保项目有序推进、进度可追溯、价值可衡量。适用于开源项目管理、团队协作、进度跟踪等场景。
---

# SKILL 10: 项目管理 — 让项目有序运转的指挥系统

> **核心理念**：好的项目管理不是增加负担，而是减少混乱。Issue是需求入口，TODO是执行抓手，日志是项目记忆。

---

## 一、项目管理概览

### 1.1 三大支柱

本项目的管理体系建立在三大支柱之上：

```
        ┌─────────────────────────────────────┐
        │   Issue管理 — 需求的入口             │  SKILL_10a
        │   分类、跟踪、归档、联动              │
        ├─────────────────────────────────────┤
        │   TODO管理 — 执行的抓手              │  SKILL_10a
        │   分解、执行、状态同步                │
        ├─────────────────────────────────────┤
        │   日志管理 — 项目的记忆              │  SKILL_10b
        │   每日记录、微信通知、改动意义分析    │
        └─────────────────────────────────────┘
```

### 1.2 管理循环

```
社区反馈/需求产生
    ↓
创建Issue（7类分类）
    ↓
评估并添加标签
    ↓
    ├─ REF-参考 → 整理到资源库 → 关闭
    ├─ RES-项目资源 → 评估整合 → 关闭
    ├─ DOC-文档维护 → 创建TODO → 更新文档
    ├─ HELP-求助 → 提供帮助 → 关闭
    ├─ QA-提问 → 回答问题 → 关闭或转DOC
    ├─ FEAT-功能建议 → 创建TODO → 开发
    └─ BUG-缺陷报告 → 创建TODO → 修复
           ↓
    TODO任务执行（pending → in_progress → completed）
           ↓
    每日工作日志记录（详细日志 + 微信通知 + 改动意义）
           ↓
    Issue关闭（附上解决方案/commit链接）
           ↓
    定期更新CHANGELOG（月度/里程碑）
```

### 1.3 核心原则

1. **透明可追溯** - 每个变更都有Issue或TODO对应，每日工作有日志记录
2. **分类有序** - 7类Issue标签清晰分工，避免混乱堆积
3. **价值驱动** - 每日工作日志必含"改动意义"分析，理解"为什么做"
4. **轻量高效** - 不增加过多管理负担，工具自动化为主
5. **持续改进** - SKILL文档本身也在迭代，从实践中总结方法

---

## 二、子技能索引

| 编号 | 文件 | 内容 | 适用场景 |
|------|------|------|---------|
| **10a** | [SKILL_10a_TODO和Issue管理.md](SKILL_10a_TODO和Issue管理.md) | GitHub Issue七类分类管理、TODO任务对应、批量管理脚本、Issue-TODO联动 | Issue分类、需求跟踪、任务分解、团队协作 |
| **10b** | [SKILL_10b_每日工作日志维护.md](SKILL_10b_每日工作日志维护.md) | 工作日划分规则（7:00分界）、详细日志生成、微信群通知、太史公曰、改动意义分析 | 进度记录、团队沟通、工作复盘、价值澄清 |
| **10c** | [SKILL_10c_Git提交规范.md](SKILL_10c_Git提交规范.md) | Git提交消息格式、提交内容管理、原子提交原则、Pre-commit Hook处理、分支策略 | 版本控制、代码审查、提交历史管理 |
| **10d** | [SKILL_10d_CHANGELOG编写规范.md](SKILL_10d_CHANGELOG编写规范.md) | CHANGELOG格式规范、内容详略原则、Commit/Issue链接格式、Added/Changed/Fixed/Maintenance分类 | 版本管理、项目文档、对外展示 |
| **10e** | [SKILL_10e_文件组织与目录结构.md](SKILL_10e_文件组织与目录结构.md) | 目录职责分离（docs/发布 vs labs/实验）、文件决策树、logs/六子目录规范、术语统一（collation→curation） | 新文件创建、目录整理、项目重构、新人引导 |

---

## 三、Issue分类体系

### 3.1 七类标签

| 标签 | 含义 | 颜色 | 处理流程 |
|------|------|------|---------|
| **REF-参考** | 参考项目或资源 | 绿色 `#0E8A16` | 整理到 `resources/references/README.md` → 关闭 |
| **FEAT-功能建议** | 新功能建议 | 浅蓝 `#A2EEEF` | 评估 → 创建TODO → 开发 → 关闭 |
| **BUG-缺陷报告** | 缺陷报告 | 红色 `#D73A4A` | 复现 → 创建TODO → 修复 → 关闭 |
| **RES-项目资源** | 本项目资源 | 黄色 `#FBCA04` | 评估 → 下载/整合 → 关闭 |
| **DOC-文档维护** | 文档改进、说明完善 | 蓝色 `#0075CA` | 创建TODO → 编写/更新文档 → 关闭 |
| **HELP-求助** | 需要帮助或指导 | 青绿 `#008672` | 提供帮助/指导 → 关闭或标记需要更多信息 |
| **QA-提问** | 问题咨询、疑问讨论 | 紫色 `#D876E3` | 回答问题 → 关闭或转为DOC（需要文档化） |

### 3.2 快速分类脚本

```bash
# 创建全部七类标签
gh label create "REF-参考" --description "参考项目或资源" --color "0E8A16"
gh label create "FEAT-功能建议" --description "新功能建议" --color "A2EEEF"
gh label create "BUG-缺陷报告" --description "缺陷报告" --color "D73A4A"
gh label create "RES-项目资源" --description "本项目资源" --color "FBCA04"
gh label create "DOC-文档维护" --description "文档改进、说明完善" --color "0075CA"
gh label create "HELP-求助" --description "需要帮助或指导" --color "008672"
gh label create "QA-提问" --description "问题咨询、疑问讨论" --color "D876E3"

# 批量分类示例
gh issue edit 24 --add-label "REF-参考"
gh issue edit 34 --add-label "FEAT-功能建议"
gh issue edit 11 --add-label "BUG-缺陷报告"
```

---

## 四、每日工作日志规范

### 4.1 工作日划分：早上7:00分界线

**重要**：本项目以早上7:00为工作日分界线，而非传统的午夜0:00

- `YYYY-MM-DD.md` 包含：`(YYYY-MM-DD) 07:00` 至 `(YYYY-MM-DD+1) 07:00` 的所有提交
- 原因：凌晨0-7点的工作通常是前一天的延续，以7点为界更符合实际作息

### 4.2 日志生成流程

```bash
# 1. 生成详细日志
cd logs/daily
python generate_log.py YYYY-MM-DD

# 2. 添加微信群通知和改动意义分析
# （使用SKILL_10b，由AI Agent完成）
```

### 4.3 日志三部分结构

```markdown
# 工作日志 YYYY-MM-DD

## 微信群通知

```
【史记知识库 YYYY-MM-DD】

· 核心工作1（包含关键数字）
· 核心工作2（包含关键数字）
...
· 提交N次代码
```

---

## 改动意义

**为什么做这些事？**
（背景和动机）

**要解决什么问题？**
（痛点和目标）

**会影响什么最终交付物？**
（成果和价值）

---

## 核心功能变化
（详细日志内容）
...
```

### 4.4 特殊情况：无提交日的太史公曰

当日无提交时，使用太史公文风：

```
【史记知识库 YYYY-MM-DD】

太史公曰：是日无所书。

<32字赞文，8个四字句>
```

**赞文规范**：
- 总字数：严格32字（仅计汉字，不含标点）
- 句式：必须全部使用四字句（8句×4字=32字）
- 文风：参考 `labs/sima-qian-style/SKILL.md`
- 变化性：每天的赞文必须不同

---

## 五、TODO管理规范

### 5.1 TODO状态

```
pending（待执行）→ in_progress（执行中）→ completed（已完成）
```

**原则**：
- 同一时间只有1个TODO处于in_progress状态
- 完成TODO后立即标记为completed，不批量更新
- 每个TODO应在1-4小时内完成

### 5.2 TODO与Issue关联

```json
{
  "content": "调研拼音注释技术方案 (Issue #25)",
  "status": "pending",
  "activeForm": "调研拼音注释技术方案 (Issue #25)",
  "relatedIssue": "#25"
}
```

### 5.3 TODO分解原则

| Issue复杂度 | TODO数量 | 示例 |
|-----------|---------|------|
| **简单** | 1个TODO | Issue #11"标注错误" → TODO"修复002_夏本纪标注错误" |
| **中等** | 2-3个TODO | Issue #25"拼音注释" → TODO"调研方案"、"实现工具"、"标注本纪" |
| **复杂** | 5+个TODO | Issue #34"苹果app" → TODO"需求分析"、"技术选型"、"UI设计"、"数据接口"、"测试发布" |

---

## 六、团队协作规范

### 6.1 Issue回复规范

**关闭Issue时必须回复**：

```markdown
已完成[功能/修复]，见commit [abc1234]

[具体说明]

测试方法：[验证步骤]
```

**REF类Issue关闭回复**：

```markdown
已添加到参考文献: [resources/references/README.md](链接)

归档位置：[分类] > [项目名称]
```

### 6.2 Commit消息规范

参见 `CLAUDE.md` 中的Git提交消息规范：

```
首行总结（做了什么）

模块A:
- 新增 xxx
- 更新 yyy

模块B:
- 修复 zzz
```

### 6.3 CHANGELOG更新规范

参见 `CLAUDE.md` 中的CHANGELOG编写规范：

- 按日期组织（`## YYYY-MM-DD`）
- 高层次总结（1-2行概括）
- 链接到详细工作日志
- 使用引用式commit链接

---

## 七、常用工具与脚本

### 7.1 GitHub CLI命令

```bash
# Issue管理
gh issue list --state open
gh issue view 34
gh issue edit 34 --add-label "FEAT-功能建议"
gh issue comment 34 --body "已完成调研，详见..."
gh issue close 34 --reason completed

# 标签管理
gh label list
gh label create "标签名" --description "描述" --color "颜色"

# Issue统计
gh issue list --json labels --jq '[.[].labels[].name] | group_by(.) | map({label: .[0], count: length})'
```

### 7.2 工作日志脚本

```bash
# 生成详细日志
cd logs/daily
python generate_log.py YYYY-MM-DD

# 验证日志完整性
ls -lh logs/daily/YYYY-MM-DD.md
```

### 7.3 完整性检查

```bash
# 检查标注完整性（SKILL_01a）
python scripts/lint_text_integrity.py

# 检查实体统计
python scripts/update_entity_stats.py
```

---

## 八、质量控制

### 8.1 Issue质量检查

- [ ] 是否有清晰的标题和描述
- [ ] 是否已添加适当的标签
- [ ] 是否有相关Issue的交叉引用（`#数字`）
- [ ] 关闭时是否有总结和链接

### 8.2 TODO质量检查

- [ ] 是否有明确的完成标准
- [ ] 是否关联到对应的Issue
- [ ] 粒度是否适中（1-4小时）
- [ ] 状态是否及时更新

### 8.3 日志质量检查

**微信通知**：
- [ ] 是否纯文本（无markdown语法）
- [ ] 是否包含关键数字
- [ ] 是否易于非技术人员理解
- [ ] 长度是否≤150字

**改动意义**：
- [ ] 是否回答了三个核心问题
- [ ] 长度是否在150-200字范围内
- [ ] 是否从项目全局视角出发
- [ ] 语言是否平实直白

---

## 九、最佳实践

### 9.1 Issue管理最佳实践

1. **及时分类** - 新Issue创建后24小时内添加标签
2. **定期清理** - 每周检查Open Issue，关闭已完成/不计划实现的Issue
3. **详细描述** - Issue描述应包含背景、现状、期望结果
4. **关联引用** - 相关Issue之间用 `#数字` 互相引用

### 9.2 TODO管理最佳实践

1. **粒度适中** - 单个TODO应在1-4小时内完成
2. **状态同步** - TODO状态变更后立即更新
3. **单一in_progress** - 同一时间只有1个TODO处于in_progress状态
4. **完成即标记** - 完成TODO后立即标记为completed

### 9.3 日志管理最佳实践

1. **每日记录** - 即使当日无提交也要生成日志（太史公曰）
2. **价值澄清** - 改动意义分析必须回答三个核心问题
3. **微信友好** - 通知文本纯文本、无技术术语、包含关键数字
4. **及时更新** - 当日工作结束后及时生成日志

---

## 十、典型工作流

### 10.1 功能开发流程

```
1. 用户提交Issue #25: "希望增加拼音注释，方便阅读"
   ↓
2. 添加标签 "FEAT-功能建议"
   ↓
3. 创建TODO任务：
   - 调研拼音注释技术方案
   - 设计拼音标注语法
   - 实现拼音标注工具
   - 为001-012本纪添加拼音
   ↓
4. 执行TODO（逐个完成）
   ↓
5. 每日工作日志记录进展
   ↓
6. 全部TODO完成后，关闭Issue #25
   ↓
7. 在Issue下回复：
   "已完成拼音注释功能，见commit [abc1234]"
```

### 10.2 缺陷修复流程

```
1. 用户报告Issue #11: "标注错误"
   ↓
2. 添加标签 "BUG-缺陷报告"
   ↓
3. 创建TODO：
   - 复现Issue #11标注错误
   - 修复标注错误
   - 验证修复结果
   ↓
4. 执行修复
   ↓
5. 关闭Issue并回复：
   "已修复标注错误，见commit [abc1234]

   修复内容：
   - 002_夏本纪.tagged.md:195 '五子之歌' → '五子作歌'
   - 通过 python scripts/lint_text_integrity.py 002 验证"
```

### 10.3 参考资源归档流程

```
1. 用户提交Issue #32: "REF 巴黎圣母院数据化项"
   ↓
2. 添加标签 "REF-参考"
   ↓
3. 整理到 resources/references/README.md
   - 按分类归档（古籍数字化平台）
   - 记录关键信息（网址、核心功能、技术栈）
   - 添加"与本项目关联"说明
   ↓
4. 关闭Issue并回复：
   "已添加到参考文献: [resources/references/README.md](链接)

   归档位置：古籍数字化平台 > 巴黎圣母院数字化项目（e-NDP）"
```

---

## 十一、常见问题

### Q1: Issue何时关闭？

**A**: 满足以下任一条件即可关闭：

- REF类：已整理到参考文献库
- RES类：已评估并下载/归档
- FEAT类：功能已开发完成并测试通过
- BUG类：问题已修复并验证
- DOC类：文档已更新并发布
- HELP类：已提供帮助或解决方案
- QA类：问题已回答

### Q2: 一个Issue对应多少个TODO？

**A**: 取决于复杂度：

- 简单任务（标注错误修复）：1个TODO
- 中等任务（拼音注释功能）：2-3个TODO
- 复杂任务（苹果app开发）：5+个TODO，建议分阶段拆分

### Q3: 为什么要写改动意义？

**A**: 改动意义分析的三个价值：

1. **价值澄清** - 理解"为什么做"，避免盲目执行
2. **决策依据** - 为未来的优先级排序提供参考
3. **项目记忆** - 复盘时快速理解当时的背景和动机

### Q4: 工作日志必须每天生成吗？

**A**: 是的，即使当日无提交也要生成：

- 有提交：常规微信通知 + 改动意义
- 无提交：太史公曰（32字赞文）+ 简要改动意义

这样可以保持日志的连续性，避免断档。

---

## 十二、与其他SKILL的关系

```
SKILL_10 项目管理
    ├─ 依赖 SKILL_01a（标注完整性维护）的lint工具
    ├─ 输出到 logs/daily/（每日工作日志）
    ├─ 输出到 CHANGELOG.md（项目变更记录）
    ├─ 输出到 resources/references/README.md（参考资源库）
    └─ 所有其他SKILL都会产生Issue/TODO/日志
```

**项目管理是横向支撑SKILL**，贯穿所有工序：

- SKILL_01-09的执行都会产生Issue、TODO、日志
- SKILL_10提供统一的管理规范和工具
- 元技能（00-META-*）指导SKILL_10的优化演化

---

## 十三、相关资源

- GitHub CLI文档: https://cli.github.com/manual/gh_issue
- GitHub Issues最佳实践: https://docs.github.com/en/issues/tracking-your-work-with-issues
- 太史公文风参考: `labs/sima-qian-style/SKILL.md`
- Git提交规范: `CLAUDE.md`
- CHANGELOG规范: `CLAUDE.md`

---

## 结语

**项目管理不是为了管理而管理，而是为了让混乱变得有序，让价值变得可见，让进展变得可追溯。**

Issue是需求的入口，TODO是执行的抓手，日志是项目的记忆。三者结合，形成完整的项目管理闭环——从需求到执行，从执行到记录，从记录到价值澄清。

好的项目管理应该是无感的——当它运转良好时，你感受到的不是管理的负担，而是项目的有序推进。
