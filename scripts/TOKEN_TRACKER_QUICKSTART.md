# Token Tracker 快速入门

## 一行代码开始使用

```python
from scripts.token_tracker import track_tokens

@track_tokens()
def my_function():
    # 你的代码
    pass
```

## 常用场景

### 场景 1：只想看统计，不保存日志

```python
@track_tokens()
def analyze_text():
    # 执行完会自动打印 Token 使用统计
    pass
```

### 场景 2：需要保存日志供后续分析

```python
@track_tokens(log_to_file=True)
def batch_processing():
    # 统计结果会保存到 logs/cost_reports/session_logs/
    pass
```

### 场景 3：静默运行，只保存日志不打印

```python
@track_tokens(print_stats=False, log_to_file=True)
def silent_job():
    # 不打印统计，只保存到文件
    pass
```

### 场景 4：自定义日志目录

```python
@track_tokens(log_to_file=True, log_dir="logs/my_custom_dir")
def custom_job():
    pass
```

## 测试

```bash
# Hello World 测试
python scripts/test_token_tracker.py

# 实际应用示例
python scripts/example_token_tracking.py
```

## 输出示例

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

## 日志文件位置

- **路径**：`logs/cost_reports/session_logs/`
- **格式**：`token_usage_YYYYMMDD_HHMMSS.json`
- **内容**：JSON 格式的详细统计数据

## 实际应用建议

1. **开发阶段**：用 `@track_tokens()` 快速查看成本
2. **生产运行**：用 `@track_tokens(log_to_file=True)` 记录日志
3. **批量处理**：统计整个批次的总成本
4. **成本优化**：对比优化前后的成本变化

## 完整文档

详细说明请参考：[SKILL_10g_项目成本统计](../skills/SKILL_10g_项目成本统计.md)

## 常见问题

**Q: 为什么测试日志的 Token 都是 0？**

A: 这是**正常现象**！详细解释请参考：[WHY_TOKEN_ZERO.md](WHY_TOKEN_ZERO.md)

**简短回答**：
- 装饰器只统计**函数执行期间**的 Token
- 测试脚本运行时间短（几秒），且没有实际调用 Claude API
- Agent 的 AI 工作发生在函数**外面**，装饰器捕获不到

**什么时候 Token 不为 0**：
- ✅ 函数内部调用 Claude API（使用 Anthropic SDK）
- ✅ 长时间运行的批处理任务（几分钟到几小时）
- ✅ 反思流程等多次 AI 交互的场景

**推荐的统计方式**：
```bash
# 查看总体统计（推荐）
python scripts/analyze_claude_token_usage.py

# 生成周报
python scripts/generate_cost_report.py --period weekly
```

📖 **完整解释**：[WHY_TOKEN_ZERO.md](WHY_TOKEN_ZERO.md)

**Q: 日志文件保存在哪里？**

A: 默认保存在 `logs/cost_reports/session_logs/`，可通过 `log_dir` 参数自定义。

**Q: 可以统计多个函数的总成本吗？**

A: 可以！在最外层函数上添加装饰器，它会统计包括内部调用在内的所有 Token 使用。

**Q: 统计数据准确吗？**

A: 装饰器通过时间戳筛选本地对话记录，准确度取决于系统时钟精度。通常误差在秒级范围内。
