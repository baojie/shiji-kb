# 为什么测试日志的 Token 都是 0？

## 快速回答

这是**正常现象**！装饰器统计的是**函数执行期间**发生的 Claude API 调用，不是整个对话的 Token。

## 详细解释

### 装饰器的工作原理

```python
@track_tokens()
def my_function():
    # 装饰器记录：开始时间 = now()

    # 你的代码
    time.sleep(3)

    # 装饰器记录：结束时间 = now()
    # 然后读取 JSONL，筛选这 3 秒内的消息
```

装饰器只能看到**函数执行的那几秒内**写入 JSONL 的消息。

### 为什么测试脚本 Token 为 0？

#### 场景 1：纯 Python 测试脚本

```python
@track_tokens()
def test_function():
    print("Hello World")  # 没有调用 Claude API
    time.sleep(1)
    print("Done")
```

**结果**：Token = 0
**原因**：函数内部没有 AI 调用，完全正常！

#### 场景 2：Agent 测试脚本

```
时间轴：
├─ 00:37:40 - 你：启动 agent 测试 token tracker
├─ 00:37:41 - Agent 启动，开始工作
├─ 00:37:44 - [装饰器开始] test_function() 开始
│   ├─ print("测试中...")
│   ├─ time.sleep(3)
│   └─ [装饰器结束] 00:37:47 函数结束
├─ 00:37:48 - Agent 继续：读取文件（Claude 在工作）
├─ 00:37:50 - Agent：分析数据（Claude 在工作）
├─ 00:38:00 - Agent：生成报告（Claude 在工作）
└─ 00:38:05 - Agent 完成任务

装饰器监测窗口：00:37:44 ~ 00:37:47 (3秒)
实际 AI 工作时间：00:37:48 ~ 00:38:05 (17秒)
```

**结果**：Token = 0
**原因**：Agent 的 AI 工作都在函数**外面**进行！

### 什么时候 Token 不为 0？

#### ✅ 情况 1：函数内部调用 Claude API

```python
@track_tokens(log_to_file=True)
def annotate_text():
    import anthropic
    client = anthropic.Anthropic()

    # 这里会产生 Token！
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        messages=[{"role": "user", "content": "分析这段文本"}]
    )

    return response
```

**结果**：Token > 0
**原因**：API 调用在函数内部，装饰器能捕获！

#### ✅ 情况 2：长时间运行的批处理

```python
@track_tokens(log_to_file=True)
def batch_process_all_chapters():
    for chapter in all_130_chapters:
        # 假设每章处理需要 30 秒
        # 使用 Claude API 进行标注
        annotate_chapter(chapter)

    # 总耗时：130章 × 30秒 = 65分钟
```

**结果**：Token > 0
**原因**：执行时间够长，能捕获到 JSONL 写入的消息！

#### ✅ 情况 3：在 Claude Code 会话中实时交互

```python
@track_tokens(log_to_file=True)
def interactive_task():
    print("请 Claude 帮我分析 README.md")
    input("按回车继续...")  # 此时你与 Claude 交互

    print("请 Claude 生成一个报告")
    input("按回车继续...")  # 此时你与 Claude 交互

    time.sleep(60)  # 等待足够长时间，让 JSONL 写入
```

**结果**：可能 Token > 0（如果 JSONL 及时写入）
**原因**：交互发生在函数内部，且等待时间够长！

### 实际验证：本次对话的真实 Token

虽然测试日志显示 0，但 Agent 使用调试脚本验证了：

**本次对话（最近 5 分钟）真实消耗**：
- 消息数：13 条
- 总 Token：161,692
- 总成本：$0.9457

**这些 Token 在哪里？**
- 在 `~/.claude/projects/` 的 JSONL 文件中
- 用 `python scripts/analyze_claude_token_usage.py` 可以看到
- 但装饰器捕获不到，因为**不在函数执行的那几秒内**

## 结论

### ❌ 装饰器不适合的场景

1. **短时间函数**（几秒钟）- JSONL 写入延迟
2. **纯 Python 计算** - 没有 AI 调用
3. **测试脚本** - 只是演示用法
4. **Agent 调用** - AI 工作在函数外

### ✅ 装饰器适合的场景

1. **长时间批处理**（几分钟到几小时）
   ```python
   @track_tokens(log_to_file=True)
   def batch_annotate_all_130_chapters():
       # 运行时间：几小时
       pass
   ```

2. **实际调用 Claude API**
   ```python
   @track_tokens(log_to_file=True)
   def call_claude_api():
       client.messages.create(...)
   ```

3. **反思流程**（执行时间长，多次 API 调用）
   ```python
   @track_tokens(log_to_file=True)
   def reflection_workflow():
       # 运行时间：30-60分钟
       # 多次调用 Claude API
       pass
   ```

### 📊 推荐的统计方式

对于日常成本统计，不要依赖装饰器，而是使用**专门的分析脚本**：

```bash
# 查看总体统计
python scripts/analyze_claude_token_usage.py

# 生成周报
python scripts/generate_cost_report.py --period weekly

# 生成月报
python scripts/generate_cost_report.py --period monthly
```

这些脚本会分析**所有对话记录**，给出完整的 Token 统计。

## 验证装饰器功能

如果你想验证装饰器是否正常工作，可以：

1. **查看是否生成日志文件**
   ```bash
   ls -lh logs/cost_reports/session_logs/
   ```
   如果有新文件，说明装饰器正常运行。

2. **查看控制台输出**
   ```
   ============================================================
   📊 Token 使用统计
   ============================================================
   ⚠️  此次会话没有检测到新的 Token 使用
   ============================================================
   ```
   能看到这个输出，说明装饰器正常工作！

3. **运行调试脚本**
   ```bash
   python scripts/debug_token_tracker.py
   ```
   会显示最近 5 分钟的真实 Token 消耗。

## 总结

**Token 为 0 ≠ 装饰器有问题**

Token 为 0 只是说明：
- 函数执行的那几秒内，没有新的 Claude 对话记录写入 JSONL
- 这在测试场景下是**完全正常**的

装饰器的真正价值在于：
- 长时间运行的批处理任务
- 实际调用 Claude API 的生产代码
- 配合日志分析，优化成本

如果你只是想查看总体 Token 使用情况，请使用：
```bash
python scripts/analyze_claude_token_usage.py
```
