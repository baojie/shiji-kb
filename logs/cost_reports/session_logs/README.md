# 会话 Token 统计日志

本目录存放使用 `@track_tokens` 装饰器生成的会话级别 Token 统计日志。

## 日志文件格式

- **文件名**：`token_usage_YYYYMMDD_HHMMSS.json`
- **格式**：JSON

示例：
```json
{
  "timestamp": "2026-04-02T00:23:11.723358",
  "function": "batch_process_chapters",
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

## 为什么有些日志文件的 Token 为 0？

这是**正常现象**！装饰器统计的是**本地 Claude Code 对话记录**中的 Token。

### Token 为 0 的情况（正常）

1. **测试脚本**（如 `test_token_tracker.py`、`example_token_tracking.py`）
   - 这些脚本只是演示装饰器的用法
   - 它们不涉及真实的 Claude API 调用
   - Token 为 0 是**预期行为**

2. **纯 Python 计算**
   - 只进行本地数据处理
   - 不调用 AI API
   - 不与 Claude Code 交互

### Token 有值的情况（真实使用）

1. **调用 Claude API**
   ```python
   @track_tokens(log_to_file=True)
   def annotate_text():
       # 使用 Anthropic SDK 调用 API
       response = client.messages.create(...)
   ```

2. **Claude Code 交互式会话**
   - 在函数执行期间与 Claude Code 有交互
   - 比如让 Claude 读取文件、分析代码、生成报告等

3. **批量 AI 处理任务**
   ```python
   @track_tokens(log_to_file=True)
   def batch_process_with_ai():
       for item in items:
           # 调用 AI 处理每个项目
           process_with_claude_api(item)
   ```

## 如何验证装饰器正常工作？

### 方法 1：检查日志文件是否生成

```bash
ls -lh logs/cost_reports/session_logs/
```

如果看到新的 JSON 文件，说明装饰器正常工作了。

### 方法 2：查看控制台输出

运行带装饰器的函数时，应该看到类似输出：

```
============================================================
📊 Token 使用统计
============================================================
⏱️  执行时间: 12.34 秒
💬 消息数: 5 或 ⚠️  此次会话没有检测到新的 Token 使用
...
============================================================
```

### 方法 3：运行测试脚本

```bash
python scripts/test_token_tracker.py
```

即使 Token 为 0，只要能看到统计输出和日志文件生成，就说明装饰器工作正常。

## 实际应用建议

### 开发阶段

```python
@track_tokens()  # 只打印，不保存日志
def test_function():
    pass
```

### 生产运行

```python
@track_tokens(log_to_file=True)  # 打印 + 保存日志
def production_task():
    pass
```

### 静默模式

```python
@track_tokens(print_stats=False, log_to_file=True)  # 只保存，不打印
def background_job():
    pass
```

## 日志分析

查看所有日志文件：
```bash
ls -lh logs/cost_reports/session_logs/
```

统计总成本：
```bash
cat logs/cost_reports/session_logs/*.json | \
  jq '.stats.cost.total' | \
  awk '{sum+=$1} END {print "Total: $" sum}'
```

查找高成本会话：
```bash
cat logs/cost_reports/session_logs/*.json | \
  jq -r '"\(.function): $\(.stats.cost.total)"' | \
  sort -t'$' -k2 -rn
```

## 清理旧日志

建议定期清理旧的测试日志：

```bash
# 删除 Token 为 0 的日志文件
for f in logs/cost_reports/session_logs/*.json; do
  if jq -e '.stats.messages == 0' "$f" > /dev/null; then
    echo "删除测试日志: $f"
    rm "$f"
  fi
done

# 或者保留最近 30 天的日志
find logs/cost_reports/session_logs/ -name "*.json" -mtime +30 -delete
```

## 相关文档

- [SKILL_10g_项目成本统计](../../../skills/SKILL_10g_项目成本统计.md) - 完整规范
- [TOKEN_TRACKER_QUICKSTART.md](../../../scripts/TOKEN_TRACKER_QUICKSTART.md) - 快速入门
- [token_tracker.py](../../../scripts/token_tracker.py) - 装饰器源代码

## 常见问题

**Q: 所有日志文件的 Token 都是 0，是不是装饰器有问题？**

A: 不是！如果：
- ✅ 日志文件正常生成
- ✅ 控制台有统计输出
- ✅ JSON 格式正确

说明装饰器**完全正常**。Token 为 0 只是说明这些函数执行时没有调用 Claude API。

**Q: 如何测试装饰器能否捕获真实 Token？**

A: 在实际调用 Claude API 的函数上添加装饰器，比如：
```python
@track_tokens(log_to_file=True)
def real_api_call():
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(...)
```

**Q: Token 统计不准确怎么办？**

A: 装饰器通过时间戳筛选本地对话记录，精度取决于：
1. 系统时钟准确性
2. 函数执行时间（很短的函数可能漏掉部分统计）
3. 对话记录文件更新延迟

建议在执行时间较长的函数上使用装饰器。
