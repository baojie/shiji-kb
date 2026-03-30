---
skill: SKILL-反思
version: 1.0
model_target: small-2b
last_updated: 2026-03-30
---

# 任务说明
检查"实体提取"结果是否合格。逐条执行检查清单，每条只能判断 yes 或 no。
全部 yes 输出 pass=true，任意 no 输出 pass=false 并列出失败项。

# 输入格式
```json
{"text": "...", "entities": [{"type": "person", "name": "...", "evidence": "..."}]}
```

# 输出格式
```json
{"pass": true, "errors": [{"check_id": 1, "detail": "..."}]}
```

# 检查清单
1. 文本中所有人名/称谓都被标注了吗？
2. 有没有把时间词错标为location？
3. activity的主语是说话人自己吗？（不是别人做的事）
4. emotion标注有原文词语支撑吗？
5. decision是已决定的吗？"想一想"/"也许"/"可能"不算。
6. question是未解决的吗？已回答的不算。
7. 有没有重复实体（同一人用不同name标了两次）？
8. evidence字段是否来自原文（不是凭空捏造）？
9. （开放检查）是否存在上述1-8之外的明显错误？

# 严格规则
- 输出必须是合法JSON。
- 只能输出 pass 和 errors 两个顶层字段。
- pass 只能是 true 或 false。
- errors 必须是数组，pass=true 时为空数组。
- check_id 只能使用 1 到 9。
- detail 要短，直接说明错在哪，不超过30字。
- 不要输出检查过程，只输出最终JSON。

# 示例
输入：
```json
{"text": "下午我和我妈去了医院，我想一想明天要不要再来，现在有点难过，不知道检查结果什么时候出来。", "entities": [{"type": "location", "name": "下午", "evidence": "下午"}, {"type": "activity", "name": "去了医院", "evidence": "我和我妈去了医院"}, {"type": "emotion", "name": "难过", "evidence": "有点难过"}, {"type": "decision", "name": "明天再来", "evidence": "想一想明天要不要再来"}]}
```
输出：
```json
{"pass": false, "errors": [{"check_id": 1, "detail": "遗漏person：我妈"}, {"check_id": 2, "detail": "时间词'下午'错标为location"}, {"check_id": 5, "detail": "'想一想明天要不要再来'不是已决定事项"}]}
```

# 禁止规则区
