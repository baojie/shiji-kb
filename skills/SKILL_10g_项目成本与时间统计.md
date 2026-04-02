---
name: SKILL_10g_项目成本与时间统计
title: 项目成本与时间统计
description: 统计 Claude Code 的 Token 成本和用户时间投入，生成定期报告，评估项目资源消耗和工作效率
category: 项目管理
version: 2.0.0
last_updated: 2026-04-02
---

# SKILL 10g: 项目成本与时间统计

> **核心理念**：用数据驱动项目管理，量化 AI 成本和人力投入。

---

## 一、快速开始

### 何时使用

**Token 成本统计**：
- 了解项目的 AI 使用成本
- 定期生成成本报告（周报/月报）
- 优化提示词和缓存策略

**时间投入统计**：
- 了解实际工作时间投入
- 评估工作效率和工作模式
- 对比不同时期的工作量

### 核心步骤

#### 首次配置（仅一次）

```bash
# 1. 复制配置文件模板
cp .claude_cost_config.example.json .claude_cost_config.json

# 2. 编辑配置，修改项目路径
nano .claude_cost_config.json
# 将 claude_project_paths 改为你的项目路径
```

#### 日常使用

```bash
# Token 成本统计
python scripts/analyze_claude_token_usage.py          # 查看总体统计
python scripts/generate_cost_report.py --period monthly  # 生成月报

# 时间投入统计
python scripts/analyze_time_investment.py             # 查看总体统计
python scripts/generate_time_report.py --period monthly # 生成月报

# 一键生成双报告
python scripts/generate_cost_report.py --period monthly && \
python scripts/generate_time_report.py --period monthly
```

### 成功标准

**Token 统计**：
- [ ] 成本数据完整（输入/输出/缓存）
- [ ] 日期分布合理
- [ ] 报告已保存到 `logs/cost_reports/`

**时间统计**：
- [ ] 会话识别正确（间隔>30分钟为新会话）
- [ ] 有效时间 ≤ 总时长
- [ ] 报告已保存到 `logs/time_reports/`

---

## 二、工具与脚本

### 2.1 Token 成本统计

| 脚本 | 功能 | 使用场景 |
|------|------|---------|
| `analyze_claude_token_usage.py` | 总体统计，按模型/日期分组 | 日常快速查看 |
| `generate_cost_report.py` | 生成周报/月报 | 定期汇报 |
| `token_tracker.py` | 装饰器，追踪函数级别的Token | 开发时优化成本 |
| `cleanup_zero_token_logs.py` | 清理测试日志 | 日志维护 |

**快速示例**：

```bash
# 查看总体成本
python scripts/analyze_claude_token_usage.py

# 生成3月报告
python scripts/generate_cost_report.py \
  --start 2026-03-01 --end 2026-03-31 \
  --output logs/cost_reports/
```

### 2.2 时间投入统计

| 脚本 | 功能 | 使用场景 |
|------|------|---------|
| `analyze_time_investment.py` | 总体统计，识别会话，计算有效时间 | 日常快速查看 |
| `generate_time_report.py` | 生成周报/月报，分析工作模式 | 定期汇报 |

**快速示例**：

```bash
# 查看总体时间投入
python scripts/analyze_time_investment.py

# 生成本周报告
python scripts/generate_time_report.py --period weekly
```

### 2.3 配置文件

**路径**：`.claude_cost_config.json`（已加入 `.gitignore`）

**格式**：

```json
{
  "claude_project_paths": [
    "-home-username-work-project-name"
  ],
  "pricing": {
    "claude-sonnet-4-5-20250929": {
      "input": 3.0,
      "output": 15.0,
      "cache_creation": 3.75,
      "cache_read": 0.30
    }
  }
}
```

---

## 三、核心指标

### 3.1 Token 成本指标

**Token 类型与价格**：

| 类型 | 说明 | Sonnet 4.5 价格 |
|------|------|----------------|
| Input | 用户输入 | $3/MTok |
| Output | AI 输出 | $15/MTok |
| Cache Creation | 缓存写入 | $3.75/MTok |
| Cache Read | 缓存读取 | $0.30/MTok |

**关键公式**：

```
总成本 = Input成本 + Output成本 + 缓存创建成本 + 缓存读取成本

缓存节省 = 无缓存成本 - 实际成本
缓存效益 = 缓存节省 / 无缓存成本 × 100%
```

### 3.2 时间投入指标

**会话识别规则**：

```
相邻用户消息间隔 > 30分钟 → 新会话开始

示例：
用户消息:  M1 -----(35分钟)----- M2 ---(8分钟)--- M3
会话划分:  [----会话1----]      [------会话2------]
```

**有效时间计算**：

```
有效时间 = 首消息缓冲(5分钟)
         + Σ(消息间隔, 最多10分钟)
         + 末消息缓冲(5分钟)

限制：有效时间 ≤ 会话总时长
```

**主动参与率**：

```
主动参与率 = 有效工作时间 / 会话总时长 × 100%

- > 70%：高度交互（频繁指导）
- 30-70%：混合模式（自动化+指导）
- < 30%：自动化模式（Claude自动执行为主）
```

---

## 四、报告模板

### 4.1 周报格式

```markdown
# 项目成本与时间周报

**统计周期**：YYYY-MM-DD ~ YYYY-MM-DD

## 💰 成本投入
- Token 总计：X.XXM
- 总成本：$XX.XX
- 日均成本：$X.XX

## ⏱️ 时间投入
- 有效工作时间：XX小时
- 主动参与率：XX%
- 日均工作时间：X.X小时

## 📊 效率分析
- 每小时成本：$X.XX
- 工作模式：[高度交互/混合/自动化]
```

### 4.2 月报格式

两个独立报告：
- `logs/cost_reports/monthly_report_YYYYMM.md` - Token 成本报告
- `logs/time_reports/monthly_report_YYYYMM.md` - 时间投入报告

可手动合并为综合报告。

---

## 五、检查清单

### 执行前

- [ ] 配置文件 `.claude_cost_config.json` 已创建
- [ ] `claude_project_paths` 包含正确的项目路径
- [ ] 输出目录存在：`logs/cost_reports/` 和 `logs/time_reports/`

### 执行中

- [ ] 脚本无报错，成功读取 `.jsonl` 文件
- [ ] Token 统计数据合理（无异常大数值）
- [ ] 时间统计：有效时间 ≤ 总时长

### 执行后

- [ ] 报告已保存到指定目录
- [ ] 数据完整，格式正确
- [ ] 历史报告已归档到 `archive/YYYY/MM/`

---

## 六、常见问题

### Q1：为什么缓存成本反而增加了总成本？

**A**：当缓存创建和读取的总成本 > 直接输入成本时会出现。

**原因**：
- 提示词变化频繁，缓存命中率低
- 单次对话较短，缓存创建成本未被摊销

**建议**：
- 评估缓存策略，考虑关闭部分缓存
- 增加单次对话工作量，提高缓存利用率

### Q2：为什么有效时间比总时长少很多？

**A**：这是正常的！有效时间只计算你主动参与的时段，不包括 Claude 长时间自动执行的时间。

**低参与率（< 30%）的含义**：
- Claude 在执行长时间的批量任务
- 你设定任务后等待结果
- 说明你在有效利用 AI 自动化能力

**不一定是坏事**。

### Q3：参与率超过100%怎么办？

**A**：偶尔出现是正常的（多个会话的缓冲时间重叠导致）。如果经常出现，可以调整参数：

```python
# 编辑 scripts/analyze_time_investment.py
MESSAGE_BUFFER = 3  # 从5分钟改为3分钟
```

### Q4：如何统计多台机器的成本/时间？

**A**：对话记录存储在本地，需要合并多台机器的数据。

**方法1：在每台机器上分别运行**
```bash
# 机器A
python scripts/analyze_claude_token_usage.py > machine_a_cost.txt

# 机器B
python scripts/analyze_claude_token_usage.py > machine_b_cost.txt

# 手动汇总
```

**方法2：合并对话记录（推荐）**
```bash
# 将机器B的对话记录复制到机器A
scp -r ~/.claude/projects/<project-path>/ \
    machine-a:~/.claude/projects/<project-path>-machine-b/

# 在机器A上，更新配置文件包含新路径
nano .claude_cost_config.json
# 添加 "-home-...-machine-b" 到 claude_project_paths
```

---

## 七、优化建议

### 7.1 降低 Token 成本

**精简提示词**：
- 移除冗余的 CLAUDE.md 内容
- 优化 Skill 文档长度
- 使用 `.claudeignore` 排除大文件

**优化缓存策略**：
- 计算缓存效益：`缓存节省 / 无缓存成本`
- 如果缓存成本 > 节省，考虑关闭

**模型选择**：
- 简单任务：Haiku ($1/MTok)
- 中等任务：Sonnet ($3/MTok)
- 复杂任务：Opus ($15/MTok)

### 7.2 优化时间投入

**高参与率（> 70%）优化**：
- 问题：重复性工作过多
- 方案：提炼工作流程，编写脚本，减少手动干预

**低参与率（< 20%）优化**：
- 问题：任务过于粗放，缺乏质量控制
- 方案：增加检查点，分步验证，适度增加指导

**理想范围**：30-70%（混合模式）

### 7.3 综合优化策略

**基于成本和时间的四象限分析**：

| 象限 | 成本 | 时间 | 分析 | 优化方向 |
|------|------|------|------|---------|
| 1 | 高 | 长 | 核心开发阶段 | 正常，关注质量 |
| 2 | 高 | 短 | 高效自动化 | 理想状态 |
| 3 | 低 | 长 | 低效工作 | **需要优化** |
| 4 | 低 | 短 | 轻度维护 | 正常 |

**示例优化路径**：

```
象限3（低成本+长时间）→ 分析原因：
  - 大量手动操作但未使用AI？→ 增加AI辅助
  - AI响应慢但Token少？→ 检查网络/模型选择
  - 等待时间过长？→ 优化工作流程
```

---

## 八、参数调优

### 8.1 时间统计参数

编辑 `scripts/analyze_time_investment.py` 和 `scripts/generate_time_report.py`：

```python
# 会话超时（分钟）
SESSION_TIMEOUT = 30
# 建议：高强度项目 20，轻度维护 60

# 最大间隔计时（分钟）
MAX_INTERVAL_COUNT = 10
# 建议：快速交互 5，长任务 15

# 消息缓冲时间（分钟）
MESSAGE_BUFFER = 5
# 建议：熟练用户 3，学习探索 8
```

### 8.2 验证参数设置

调整后运行测试：

```bash
python scripts/analyze_time_investment.py

# 检查关键指标：
# - 平均会话时长：应该在 10-60 分钟之间
# - 主动参与率：应该在 20-80% 之间
# 如果异常，调整参数后重新测试
```

---

## 九、相关资源

### 9.1 脚本文件

**Token 成本统计**：
- `scripts/analyze_claude_token_usage.py` - 总体统计
- `scripts/generate_cost_report.py` - 报告生成
- `scripts/token_tracker.py` - 函数级追踪装饰器
- `scripts/cleanup_zero_token_logs.py` - 日志清理

**时间投入统计**：
- `scripts/analyze_time_investment.py` - 总体统计
- `scripts/generate_time_report.py` - 报告生成

### 9.2 快速入门文档

- `scripts/TOKEN_TRACKER_QUICKSTART.md` - Token 追踪快速入门
- `scripts/TIME_TRACKING_QUICKSTART.md` - 时间统计快速入门
- `scripts/WHY_TOKEN_ZERO.md` - 为什么测试日志Token为0？

### 9.3 报告目录结构

```
logs/
├── cost_reports/              # Token 成本报告
│   ├── archive/
│   │   └── 2026/
│   │       ├── 03/
│   │       └── 04/
│   ├── session_logs/          # 会话级Token日志
│   ├── weekly_report_*.md
│   └── monthly_report_*.md
│
└── time_reports/              # 时间投入报告
    ├── archive/
    │   └── 2026/
    │       ├── 03/
    │       └── 04/
    ├── weekly_report_*.md
    └── monthly_report_*.md
```

### 9.4 相关 SKILL

- [`SKILL_10b_每日工作日志维护`](SKILL_10b_每日工作日志维护.md) - 工作日志规范
- [`SKILL_10d_CHANGELOG编写规范`](SKILL_10d_CHANGELOG编写规范.md) - 变更日志规范
- [`SKILL_10f_Skill的提炼与转化`](SKILL_10f_Skill的提炼与转化.md) - Skill 编写规范

---

## 十、价格参考

### Claude 3.5/4.x 系列（2026年价格）

| 模型 | 输入 | 输出 | 缓存写入 | 缓存读取 |
|------|------|------|----------|----------|
| Sonnet 4.5 | $3 | $15 | $3.75 | $0.30 |
| Haiku 4.5 | $1 | $5 | $1.25 | $0.10 |
| Opus 4.6 | $15 | $75 | $18.75 | $1.50 |

*单位：$/MTok (百万 Token)*

---

## 更新历史

- **v2.0.0** (2026-04-02)
  - 合并 Token 成本统计和时间投入统计
  - 按 SKILL_10f 规范精简结构
  - 增加综合优化建议和四象限分析
  - 完善快速开始章节

- **v1.0.0** (2026-04-01)
  - 初始版本（仅 Token 统计）
  - 定义统计流程和报告格式
  - 创建基础统计脚本
