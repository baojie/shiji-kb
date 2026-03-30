---
skill: SKILL-实体提取
version: 1.1
model_target: small-2b
last_updated: 2026-03-30
---

# 任务说明
从单个第一人称文本片段中提取实体。只提取6类实体。
输入文本是单个片段，长度小于500字。不要做跨片段推理，不要补全原文没有的信息。

# 输入格式
{"text": "..."}

# 输出格式
{"entities": [{"type": "person", "name": "老王", "evidence": "原文中的依据"}]}

# 严格规则
- 每个实体必须包含 type、name、evidence 三个字段。
- type 只能是：person / activity / location / emotion / decision / question
- evidence 必须直接来自原文，使用最短可支持片段。

# 禁止规则区
- 禁止把时间词标为location。
- "他/她/它"单独出现不算person，需有上下文支撑。
- 情绪必须有词语证据，不能凭感觉推断。
- [v1.0 2026-03-30] decision必须是已决定事项，不确定表达不算：'打算回国发展 还没想好 不知道是留'是不确定表达，不是已决定事项