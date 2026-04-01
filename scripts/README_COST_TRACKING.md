# Claude Code 成本统计脚本使用说明

本目录包含用于统计 Claude Code Token 使用量和成本的脚本。

## 🚀 快速开始

### 1. 首次配置

成本统计脚本需要读取本地的 Claude Code 对话记录，这些记录存储在：

```
~/.claude/projects/<项目路径>/
```

由于路径中包含用户名等隐私信息，我们使用配置文件来管理这些路径。

**步骤**：

```bash
# 1. 进入项目根目录
cd /path/to/shiji-kb

# 2. 复制示例配置文件
cp .claude_cost_config.example.json .claude_cost_config.json

# 3. 编辑配置文件
nano .claude_cost_config.json
```

**配置文件示例**：

```json
{
  "claude_project_paths": [
    "-home-yourname-work-shiji-kb",
    "-home-yourname-work-knowledge-shiji-kb"
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

**如何找到你的项目路径**：

```bash
# 查看所有 Claude 项目
ls ~/.claude/projects/

# 找到包含你项目名的目录
ls ~/.claude/projects/ | grep shiji
```

### 2. 运行统计

```bash
# 查看总体统计
python scripts/analyze_claude_token_usage.py

# 生成月报
python scripts/generate_cost_report.py --period monthly --output logs/cost_reports/

# 或使用快捷脚本
bash scripts/monthly_cost_report.sh
```

## 📁 配置文件说明

### `.claude_cost_config.json`（私有配置）

- **位置**：项目根目录
- **用途**：存储用户特定的项目路径和价格配置
- **隐私**：已加入 `.gitignore`，不会提交到 Git
- **必需**：首次使用前必须创建

### `.claude_cost_config.example.json`（示例配置）

- **位置**：项目根目录
- **用途**：作为配置模板，会提交到 Git
- **内容**：使用示例路径，不包含真实用户信息

## 🔒 隐私保护

### 为什么需要配置文件？

Claude Code 的对话记录路径通常包含：
- 用户名（如 `/home/username/`）
- 项目路径（可能暴露目录结构）

将这些路径硬编码在脚本中会：
1. 泄露用户隐私
2. 使脚本无法在其他机器上使用
3. 在 Git 历史中永久保存敏感信息

### 配置文件的保护机制

1. **`.gitignore`**：`.claude_cost_config.json` 已加入忽略列表
2. **示例文件**：提供 `.example.json` 作为模板
3. **脚本检查**：脚本会检查配置文件是否存在，不存在则提示创建

## 📊 脚本说明

### `analyze_claude_token_usage.py`

**功能**：基础统计脚本

- 扫描所有对话记录
- 统计 Token 使用量
- 计算成本
- 按模型和日期分组

**使用**：
```bash
python scripts/analyze_claude_token_usage.py
```

### `generate_cost_report.py`

**功能**：生成格式化报告（周报/月报）

**使用**：
```bash
# 生成周报
python scripts/generate_cost_report.py --period weekly

# 生成月报
python scripts/generate_cost_report.py --period monthly

# 生成指定时间段报告
python scripts/generate_cost_report.py --start 2026-03-01 --end 2026-03-31
```

### `weekly_cost_report.sh` / `monthly_cost_report.sh`

**功能**：快捷脚本

**使用**：
```bash
bash scripts/weekly_cost_report.sh
bash scripts/monthly_cost_report.sh
```

## 🔧 多机器统计

如果你在多台机器上工作，需要在每台机器上：

1. 配置各自的 `.claude_cost_config.json`
2. 运行统计脚本
3. 手动汇总结果

或者，将所有机器的对话记录文件复制到一台机器上统一统计。

详细说明请参考：[`skills/SKILL_10g_项目成本统计.md`](../skills/SKILL_10g_项目成本统计.md)

## ❓ 常见问题

### Q: 配置文件丢失了怎么办？

A: 重新从示例文件复制：
```bash
cp .claude_cost_config.example.json .claude_cost_config.json
```

### Q: 如何添加新的项目路径？

A: 编辑 `.claude_cost_config.json`，在 `claude_project_paths` 数组中添加新路径。

### Q: 价格更新了怎么办？

A: 编辑 `.claude_cost_config.json` 的 `pricing` 部分，更新对应模型的价格。

### Q: 脚本报错"配置文件不存在"？

A: 运行：
```bash
cp .claude_cost_config.example.json .claude_cost_config.json
nano .claude_cost_config.json
```

## 📚 相关文档

- [SKILL_10g_项目成本统计.md](../skills/SKILL_10g_项目成本统计.md) - 完整方法论
- [logs/cost_reports/README.md](../logs/cost_reports/README.md) - 报告目录说明
