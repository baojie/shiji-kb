# Claude Code 成本报告目录

本目录存储史记知识库项目的 Claude Code Token 使用量统计和成本分析报告。

## ⚙️ 首次使用配置

在生成报告前，需要配置项目路径（包含用户隐私信息，不会提交到 Git）：

```bash
# 1. 复制示例配置文件
cp .claude_cost_config.example.json .claude_cost_config.json

# 2. 编辑配置文件，修改 claude_project_paths 为你的实际路径
nano .claude_cost_config.json

# 3. 运行统计脚本
python scripts/analyze_claude_token_usage.py
```

配置文件示例：
```json
{
  "claude_project_paths": [
    "-home-username-work-project-name"
  ]
}
```

## 📊 报告类型

### 1. 总体统计报告

**文件**：`total_report_latest.txt`

**内容**：
- 所有时间的累计统计
- 按模型分类统计
- 最近30天的每日统计

**更新方法**：
```bash
python scripts/analyze_claude_token_usage.py > logs/cost_reports/total_report_latest.txt
```

### 2. 定期报告（周报/月报）

**文件格式**：
- 周报：`weekly_report_YYYYWW.md`（如 `weekly_report_202613.md`）
- 月报：`monthly_report_YYYYMM.md`（如 `monthly_report_202603.md`）
- 自定义：`report_YYYYMMDD_YYYYMMDD.md`

**内容**：
- 指定时间段的统计数据
- 成本明细表格
- 模型使用分布
- 每日趋势
- 分析与建议

**生成方法**：
```bash
# 生成本周报告
python scripts/generate_cost_report.py --period weekly --output logs/cost_reports/

# 生成本月报告
python scripts/generate_cost_report.py --period monthly --output logs/cost_reports/

# 生成指定时间段报告
python scripts/generate_cost_report.py --start 2026-03-01 --end 2026-03-31 --output logs/cost_reports/
```

## 📈 项目累计统计（截至 2026-04-01）

> ⚠️ **统计范围说明**：本统计仅包含当前机器上的 Claude Code 对话记录。如果在其他机器上也使用过 Claude Code 工作，实际成本会更高。

| 指标 | 数值 |
|------|------|
| **对话数** | 173 个 |
| **消息数** | 96,751 条 |
| **Token 总计** | 268.59M (不含缓存读取) |
| **总成本** | **$2,352.39** (当前机器) |

### 成本分解

| 项目 | Token 数 | 单价 | 成本 |
|------|----------|------|------|
| 输入 | 3.49M | $3/MTok | $10.48 |
| 输出 | 11.08M | $15/MTok | $166.23 |
| 缓存创建 | 254.02M | $3.75/MTok | $952.57 |
| 缓存读取 | 4077.05M | $0.30/MTok | $1,223.11 |
| **总计** | - | - | **$2,352.39** |

### 模型使用分布

| 模型 | 消息数 | 占比 | 成本占比 |
|------|--------|------|---------|
| Sonnet 4.5 | 27,395 | 56.4% | 76.3% |
| Opus 4.6 | 10,528 | 21.7% | 14.8% |
| Sonnet 4.6 | 6,850 | 14.1% | 8.7% |
| Haiku 4.5 | 247 | 0.5% | 0.1% |

## 📅 定期报告流程

### 每周一（周报）

```bash
# 1. 生成上周报告
python scripts/generate_cost_report.py --period weekly --output logs/cost_reports/

# 2. 检查报告内容
cat logs/cost_reports/weekly_report_$(date -d "last monday" +%Y%W).md

# 3. 如需要，添加分析和建议（手动编辑）
```

### 每月1日（月报）

```bash
# 1. 生成上月报告
python scripts/generate_cost_report.py --period monthly --output logs/cost_reports/

# 2. 生成总体统计
python scripts/analyze_claude_token_usage.py > logs/cost_reports/total_report_latest.txt

# 3. 归档历史报告
mkdir -p logs/cost_reports/archive/$(date -d "last month" +%Y)/
mv logs/cost_reports/monthly_report_$(date -d "last month" +%Y%m).md \
   logs/cost_reports/archive/$(date -d "last month" +%Y)/
```

## 💡 成本优化建议

### 当前发现

1. **缓存策略问题**
   - 缓存总成本（$2,175.68）高于无缓存成本（$938.76）
   - 增加了 131.7% 的额外成本
   - 原因：提示词变化频繁，缓存命中率不理想

2. **模型使用**
   - Sonnet 4.5 是主力模型（76.3%成本）
   - Opus 4.6 用于复杂任务（14.8%成本）
   - Haiku 4.5 使用较少（仅0.1%成本）

### 优化方向

1. **评估缓存策略**
   - 考虑关闭部分频繁变化的提示词缓存
   - 增加单次对话的工作量，提高缓存利用率
   - 定期清理过期缓存

2. **优化提示词**
   - 精简 CLAUDE.md 和 SKILL 文档长度
   - 使用 `.claudeignore` 排除不必要的大文件
   - 避免重复发送大文件内容

3. **合理选择模型**
   - 简单任务：使用 Haiku（$1/MTok input）
   - 中等任务：使用 Sonnet（$3/MTok input）
   - 复杂任务：使用 Opus（$15/MTok input）

4. **减少输出成本**
   - 使用更精确的指令，减少冗长输出
   - 避免要求详细解释性输出
   - 分步执行大任务

## 🔗 相关文档

- [SKILL_10g_项目成本统计.md](../../skills/SKILL_10g_项目成本统计.md) - 完整的成本统计方法论
- [scripts/analyze_claude_token_usage.py](../../scripts/analyze_claude_token_usage.py) - 基础统计脚本
- [scripts/generate_cost_report.py](../../scripts/generate_cost_report.py) - 报告生成脚本

## 📝 报告文件列表

### 当前报告

- `total_report_latest.txt` - 最新的总体统计报告
- `report_20260101_20260401.md` - 2026年1-4月完整报告
- `total_cost_report_20260401.txt` - 2026-04-01 快照报告

### 历史报告归档

```
archive/
├── 2026/
│   ├── 03/
│   │   ├── weekly_report_202610.md
│   │   ├── weekly_report_202611.md
│   │   └── monthly_report_202603.md
│   └── 04/
│       └── ...
└── ...
```

---

**维护说明**：
- 每周一生成周报
- 每月1日生成月报并归档
- 重大成本变化时生成专项报告
- 定期更新本 README 的累计统计数据
