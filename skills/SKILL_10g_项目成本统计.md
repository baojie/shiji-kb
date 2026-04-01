---
name: SKILL_10g_项目成本统计
title: 项目成本统计
description: Claude Code Token 使用量统计与成本分析的完整规范，包括数据收集、成本计算、报告生成
category: 项目管理
version: 1.0.0
last_updated: 2026-04-01
---

# SKILL 10g: 项目成本统计

## 概述

本 SKILL 定义如何统计和分析项目中 Claude Code 的 Token 使用量和成本，生成定期报告，帮助管理项目资源消耗。

## 何时使用

- 需要了解项目的 AI 使用成本
- 定期（每周/每月）生成成本报告
- 分析不同时期的 Token 使用趋势
- 评估缓存策略的效果
- 优化提示词以降低成本

## 核心概念

### Token 类型

Claude API 计费涉及以下 Token 类型：

1. **输入 tokens** (Input Tokens)
   - 用户发送给模型的提示词
   - 价格：$3/MTok (Sonnet 4.5)

2. **输出 tokens** (Output Tokens)
   - 模型生成的回复内容
   - 价格：$15/MTok (Sonnet 4.5)

3. **缓存创建 tokens** (Cache Creation Input Tokens)
   - 首次创建提示词缓存
   - 价格：$3.75/MTok (Sonnet 4.5)

4. **缓存读取 tokens** (Cache Read Input Tokens)
   - 从缓存中读取提示词
   - 价格：$0.30/MTok (Sonnet 4.5)

### 数据源

Claude Code 的对话记录存储位置：

```
~/.claude/projects/-<项目路径转义>/
├── <uuid-1>.jsonl
├── <uuid-2>.jsonl
└── ...
```

每个 `.jsonl` 文件是一个对话，每行是一条消息的 JSON 记录。

**⚠️ 重要说明**：
- 对话记录存储在**本地机器**的 `~/.claude/projects/` 目录
- 如果在**多台机器**上工作过，需要在每台机器上分别统计
- 本脚本只能统计**当前机器**上的对话记录
- 实际项目总成本 = 所有机器的成本之和

### 数据结构

```json
{
  "type": "assistant",
  "message": {
    "model": "claude-sonnet-4-5-20250929",
    "usage": {
      "input_tokens": 3415,
      "output_tokens": 407,
      "cache_creation_input_tokens": 0,
      "cache_read_input_tokens": 14078
    }
  },
  "timestamp": "2026-04-01T15:13:11.357Z"
}
```

## 工具与脚本

### 0. 配置文件

**配置文件路径**：`.claude_cost_config.json`（已加入 `.gitignore`，不会提交到 Git）

**首次使用配置**：

```bash
# 1. 复制示例配置文件
cp .claude_cost_config.example.json .claude_cost_config.json

# 2. 编辑配置文件，修改项目路径
nano .claude_cost_config.json
```

**配置文件格式**：

```json
{
  "claude_project_paths": [
    "-home-username-work-project-name",
    "-home-username-work-old-project-path"
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

**说明**：
- `claude_project_paths`：项目在 `~/.claude/projects/` 下的目录名列表
- `pricing`：各模型的价格配置（单位：$/MTok）
- 配置文件包含用户隐私路径，不会提交到版本控制

### 1. 基础统计脚本

**脚本路径**：`scripts/analyze_claude_token_usage.py`

**功能**：
- 扫描所有对话记录文件
- 统计各类 Token 使用量
- 计算总成本
- 按模型、日期分组统计
- 计算缓存效益

**使用方法**：

```bash
# 首次使用：配置项目路径
cp .claude_cost_config.example.json .claude_cost_config.json
nano .claude_cost_config.json  # 修改 claude_project_paths

# 基础统计
python scripts/analyze_claude_token_usage.py

# 保存报告
python scripts/analyze_claude_token_usage.py > logs/cost_reports/report_$(date +%Y%m%d).txt
```

### 2. 定期报告生成脚本

**脚本路径**：`scripts/generate_cost_report.py`

**功能**：
- 生成周报/月报格式的成本报告
- 对比不同时期的使用量
- 趋势分析和可视化
- 自动保存到指定目录

**使用方法**：

```bash
# 生成本周报告
python scripts/generate_cost_report.py --period weekly

# 生成本月报告
python scripts/generate_cost_report.py --period monthly

# 生成指定时间段报告
python scripts/generate_cost_report.py --start 2026-03-01 --end 2026-03-31

# 指定输出目录
python scripts/generate_cost_report.py --period monthly --output logs/cost_reports/
```

### 3. Token 使用统计装饰器

**脚本路径**：`scripts/token_tracker.py`

**功能**：
- 为任何 Python 函数添加 Token 使用统计
- 自动捕获函数执行期间的 Claude API 调用
- 打印详细的 Token 使用报告
- 可选择保存统计日志到文件

**使用方法**：

```python
from scripts.token_tracker import track_tokens

# 基本用法：只打印统计信息
@track_tokens()
def my_function():
    # 你的代码
    pass

# 带日志记录：统计信息会保存到文件
@track_tokens(log_to_file=True)
def process_data():
    # 你的代码
    pass

# 自定义日志目录
@track_tokens(log_to_file=True, log_dir="logs/my_custom_logs")
def another_function():
    # 你的代码
    pass

# 不打印统计，只保存到文件
@track_tokens(print_stats=False, log_to_file=True)
def silent_tracking():
    # 你的代码
    pass
```

**测试方法**：

```bash
# 运行测试脚本（包含 Hello World 示例）
python scripts/test_token_tracker.py
```

**输出示例**：

```
============================================================
📊 Token 使用统计
============================================================
⏱️  执行时间: 12.34 秒
💬 消息数: 5

📦 Token 使用量:
   输入:              8,523
   输出:              1,245
   缓存创建:         15,678
   缓存读取:         45,234
   ──────────────────────────────
   总计:             25,446

💰 成本分析:
   输入成本:           $0.0256
   输出成本:           $0.0187
   缓存创建成本:       $0.0588
   缓存读取成本:       $0.0136
   ───────────────────────────────────
   总成本:             $0.1167

🤖 模型使用:
   sonnet-4-5:
      消息: 5 | Token: 25,446 | 成本: $0.1167
============================================================
```

**日志文件格式**：

日志保存在 `logs/cost_reports/session_logs/token_usage_YYYYMMDD_HHMMSS.json`：

```json
{
  "timestamp": "2026-04-02T00:20:55.058224",
  "function": "my_function",
  "stats": {
    "messages": 5,
    "tokens": {
      "input": 8523,
      "output": 1245,
      "cache_creation": 15678,
      "cache_read": 45234,
      "total": 25446
    },
    "cost": {
      "input": 0.0256,
      "output": 0.0187,
      "cache_creation": 0.0588,
      "cache_read": 0.0136,
      "total": 0.1167
    },
    "by_model": {
      "claude-sonnet-4-5-20250929": {
        "messages": 5,
        "tokens": 25446,
        "cost": 0.1167
      }
    }
  }
}
```

**适用场景**：

1. **脚本开发阶段**：了解不同实现方案的成本差异
2. **批量处理任务**：统计处理大量数据时的 Token 消耗
3. **成本优化**：对比优化前后的成本变化
4. **实验追踪**：记录每次实验的资源使用情况

**重要说明**：

装饰器统计的是**本地 Claude Code 对话记录**中的 Token 使用量：

- ✅ **会统计**：函数执行期间通过 Claude Code 的交互、调用 Claude API 的操作
- ❌ **不统计**：纯 Python 代码执行、不涉及 AI 的本地计算
- 📌 **测试脚本**（`test_token_tracker.py`、`example_token_tracking.py`）Token 为 0 是**正常的**，因为它们只是演示装饰器用法，不涉及真实的 AI 调用

**真实应用场景示例**：
```python
# 场景：调用 Claude API 进行文本标注
@track_tokens(log_to_file=True)
def annotate_with_claude_api(text):
    # 使用 Anthropic SDK 或类似工具调用 API
    # 这里会产生真实的 Token 消耗
    response = client.messages.create(...)
    return response

# 场景：在 Claude Code 会话中执行的交互式任务
@track_tokens(log_to_file=True)
def interactive_analysis():
    # 如果在此函数执行期间与 Claude Code 有交互
    # 装饰器会捕获这些交互产生的 Token
    pass
```

## 操作流程

### 日常统计

```bash
# 1. 快速查看总体统计
python scripts/analyze_claude_token_usage.py

# 2. 查看最近7天的使用情况
python scripts/generate_cost_report.py --period weekly
```

### 周报生成（每周一）

```bash
# 1. 生成上周报告
python scripts/generate_cost_report.py --period weekly --output logs/cost_reports/

# 2. 检查报告内容
cat logs/cost_reports/weekly_report_$(date +%Y%W).md

# 3. 如需要，添加分析和建议
```

### 月报生成（每月1日）

```bash
# 1. 生成上月报告
python scripts/generate_cost_report.py --period monthly --output logs/cost_reports/

# 2. 生成趋势图（如需要）
python scripts/generate_cost_report.py --period monthly --plot

# 3. 归档报告
mv logs/cost_reports/monthly_report_$(date +%Y%m).md \
   logs/cost_reports/archive/$(date +%Y)/
```

## 报告模板

### 周报格式

```markdown
# Claude Code Token 使用周报

**统计周期**：YYYY-MM-DD ~ YYYY-MM-DD

## 📊 本周概览

- 对话数：XX 个
- 消息数：XX,XXX 条
- Token 总计：XX.XM
- 总成本：$XXX.XX

## 💰 成本明细

| 项目 | Token 数 | 单价 | 成本 |
|------|----------|------|------|
| 输入 | X.XXM | $3/MTok | $XX.XX |
| 输出 | X.XXM | $15/MTok | $XX.XX |
| 缓存创建 | XX.XM | $3.75/MTok | $XX.XX |
| 缓存读取 | XXX.XM | $0.30/MTok | $XX.XX |

## 📈 日均统计

- 日均对话数：XX
- 日均成本：$XX.XX

## 🔍 对比分析

与上周相比：
- Token 使用量：↑/↓ XX%
- 总成本：↑/↓ XX%

## 💡 建议

- [根据数据给出优化建议]
```

### 月报格式

```markdown
# Claude Code Token 使用月报

**统计月份**：YYYY 年 MM 月

## 📊 月度概览

...

## 📅 每周趋势

| 周次 | 对话数 | Token数 | 成本 |
|------|--------|---------|------|
| W1   | XX     | XX.XM   | $XX  |
| W2   | XX     | XX.XM   | $XX  |
| W3   | XX     | XX.XM   | $XX  |
| W4   | XX     | XX.XM   | $XX  |

## 🎯 模型使用分布

...

## 💡 月度总结与建议

...
```

## 检查清单

### 执行前

- [ ] 确认 `~/.claude/projects/` 目录可访问
- [ ] 确认 Python 环境可用
- [ ] 确认输出目录存在：`logs/cost_reports/`

### 执行中

- [ ] 脚本无报错，成功读取所有 `.jsonl` 文件
- [ ] Token 统计数据合理（无异常大数值）
- [ ] 成本计算准确

### 执行后

- [ ] 报告已保存到指定目录
- [ ] 报告格式正确，数据完整
- [ ] 如需要，报告已分享给团队
- [ ] 历史报告已归档

## 成本优化建议

### 降低输入成本

1. **精简提示词**
   - 移除冗余的 CLAUDE.md 内容
   - 优化 Skill 文档长度
   - 避免重复发送大文件内容

2. **使用 `.claudeignore`**
   - 排除不必要的大文件
   - 排除临时文件和日志

### 降低输出成本

1. **明确指令**
   - 避免冗长的解释性输出
   - 使用 "简洁回复" 指令

2. **分步执行**
   - 将大任务拆分为小任务
   - 避免一次性生成大量代码

### 优化缓存策略

1. **评估缓存效益**
   - 计算 `缓存节省 = 无缓存成本 - 实际成本`
   - 如果缓存成本高于节省，考虑关闭部分缓存

2. **调整缓存配置**
   - 根据项目特点调整缓存策略
   - 定期清理过期缓存

### 模型选择

1. **任务分级**
   - 简单任务：使用 Haiku ($1/MTok input)
   - 中等任务：使用 Sonnet ($3/MTok input)
   - 复杂任务：使用 Opus (更高成本)

2. **批量处理**
   - 相似任务合并处理
   - 减少对话切换

## 日志维护

### 清理测试日志

测试和示例脚本会产生大量 Token 为 0 的日志文件，建议定期清理：

```bash
# 预览将要删除的文件
python scripts/cleanup_zero_token_logs.py

# 实际删除
python scripts/cleanup_zero_token_logs.py --execute

# 保留最近 30 天的文件（即使 Token 为 0）
python scripts/cleanup_zero_token_logs.py --execute --keep-days 30
```

**清理策略建议**：
- 开发阶段：每周清理一次测试日志
- 生产环境：保留最近 30-90 天的真实日志
- 归档重要日志：将高成本会话的日志单独归档

### 日志分析

```bash
# 查看所有日志文件
ls -lh logs/cost_reports/session_logs/

# 统计总成本（需要 jq）
cat logs/cost_reports/session_logs/*.json | \
  jq '.stats.cost.total' | \
  awk '{sum+=$1} END {print "Total: $" sum}'

# 查找高成本会话
cat logs/cost_reports/session_logs/*.json | \
  jq -r '"\(.function): $\(.stats.cost.total)"' | \
  sort -t'$' -k2 -rn | head -10
```

## 常见问题

### Q1：为什么缓存成本反而增加了总成本？

**A**：当缓存创建和读取的总成本超过直接输入成本时会出现这种情况。这通常发生在：
- 提示词变化频繁，缓存命中率低
- 单次对话较短，缓存创建成本未被摊销

**建议**：
- 评估缓存策略，考虑关闭部分缓存
- 增加单次对话的工作量，提高缓存利用率

### Q2：如何验证统计数据的准确性？

**A**：
1. 检查对话文件总数是否与报告一致
2. 随机抽查几个对话文件，手动验证 Token 数
3. 对比 Anthropic Console 的官方账单（如有访问权限）

### Q3：报告保存在哪里？

**A**：
- 默认输出到终端
- 使用 `--output` 参数指定目录
- 推荐路径：`logs/cost_reports/`
- 历史报告归档：`logs/cost_reports/archive/YYYY/`

### Q4：如何统计多台机器的总成本？

**A**：
由于对话记录存储在本地，需要在每台机器上分别统计：

**方法1：在每台机器上运行脚本**
```bash
# 机器A
python scripts/analyze_claude_token_usage.py > machine_a_report.txt

# 机器B
python scripts/analyze_claude_token_usage.py > machine_b_report.txt

# 手动汇总两个报告的成本
```

**方法2：合并对话记录文件（推荐）**
```bash
# 在机器B上，将对话记录复制到机器A
scp -r ~/.claude/projects/-home-baojie-work-knowledge-shiji-kb/ \
    machine-a:~/.claude/projects/-home-baojie-work-knowledge-shiji-kb-machine-b/

# 在机器A上，更新脚本以包含新路径
# 编辑 scripts/analyze_claude_token_usage.py 的 CLAUDE_DIRS 列表
```

**方法3：定期导出汇总**
```bash
# 定期将所有机器的 .jsonl 文件集中到一台机器
# 使用统一的脚本统计
```

## 相关资源

### 脚本文件

- `scripts/analyze_claude_token_usage.py` - 基础统计脚本
- `scripts/generate_cost_report.py` - 报告生成脚本
- `scripts/token_tracker.py` - Token 使用统计装饰器
- `scripts/test_token_tracker.py` - 装饰器测试脚本（Hello World）
- `scripts/example_token_tracking.py` - 装饰器实际应用示例
- `scripts/demo_real_token_tracking.py` - 真实场景演示（说明如何捕获真实 Token）
- `scripts/test_real_api_call.py` - 真实 API 调用示例（需要 Anthropic SDK）
- `scripts/cleanup_zero_token_logs.py` - 清理 Token 为 0 的测试日志
- `scripts/TOKEN_TRACKER_QUICKSTART.md` - 快速入门指南
- `scripts/WHY_TOKEN_ZERO.md` - 为什么测试日志 Token 为 0？（重要说明）

### 报告目录

```
logs/cost_reports/
├── archive/              # 历史报告归档
│   ├── 2026/
│   │   ├── 03/
│   │   │   ├── weekly_report_202610.md
│   │   │   ├── weekly_report_202611.md
│   │   │   └── monthly_report_202603.md
│   │   └── 04/
│   └── ...
├── session_logs/         # 会话级别的 Token 统计日志
│   ├── token_usage_20260402_001234.json
│   ├── token_usage_20260402_005678.json
│   └── ...
├── weekly_report_latest.md
└── monthly_report_latest.md
```

### 相关 SKILL

- [`SKILL_10b_每日工作日志维护`](SKILL_10b_每日工作日志维护.md) - 工作日志规范
- [`SKILL_10d_CHANGELOG编写规范`](SKILL_10d_CHANGELOG编写规范.md) - 变更日志规范
- [`SKILL_10f_Skill的提炼与转化`](SKILL_10f_Skill的提炼与转化.md) - Skill 编写规范

## 价格参考

### Claude 3.5/4.x 系列（2026年价格）

| 模型 | 输入 | 输出 | 缓存写入 | 缓存读取 |
|------|------|------|----------|----------|
| Sonnet 4.5 | $3 | $15 | $3.75 | $0.30 |
| Haiku 4.5 | $1 | $5 | $1.25 | $0.10 |
| Opus 4.6 | $15 | $75 | $18.75 | $1.50 |

*单位：$/MTok (百万 Token)*

## 更新历史

- **v1.0.0** (2026-04-01)
  - 初始版本
  - 定义统计流程和报告格式
  - 创建基础统计脚本
