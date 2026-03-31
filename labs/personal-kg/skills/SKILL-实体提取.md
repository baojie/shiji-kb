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
```json
{"text": "..."}
```

# 输出格式
```json
{"entities": [{"type": "person", "name": "老王", "evidence": "原文中的依据"}]}
```

# 严格规则
- 输出必须是合法JSON。
- 每个实体必须包含 type、name、evidence 三个字段。
- type 只能是：person / activity / location / emotion / decision / question
- evidence 必须直接来自原文，使用最短可支持片段。
- name 不超过15字，超过则截取核心部分。
- 同一实体不要重复输出两次。
- 不确定时不要标。

# 实体定义

## person
文本中提到的他人。可用名字、称谓、关系描述。
不知道真实姓名时用关系描述：我妈、同事甲、领导、房东。

## activity
说话人自己正在做、刚做过、或明确计划要做的事。
主语必须是"我"，不能是别人做的事。
name 用简短动作短语：开会、去医院看我妈、改PPT。

## location
文本中出现的地点、场所、空间位置。
例如：公司、医院、杭州、家里、咖啡馆。
时间词不是地点。

## emotion
说话人的情绪状态。必须有明确情绪词支撑。
例如：开心、紧张、烦、难过、兴奋、焦虑。
没有情绪词时，不要凭感觉推断。

## decision
说话人已经做出的决定，或明确成形的计划。
原文要有决定性表达：决定、打算、准备、要去、要做。
模糊想法不算：想一想、也许、可能。

## question
仍未解决的问题、疑问或困惑。
原文要有：不知道、不确定、怎么、为什么。
已经得到答案的问题不算。

# 示例1
输入：
```json
{"text": "今天我跟老王开会，决定下周去杭州出差，心里有点紧张，不知道报销怎么走。"}
```
输出：
```json
{"entities": [{"type": "person", "name": "老王", "evidence": "老王"}, {"type": "activity", "name": "开会", "evidence": "我跟老王开会"}, {"type": "location", "name": "杭州", "evidence": "去杭州出差"}, {"type": "emotion", "name": "紧张", "evidence": "心里有点紧张"}, {"type": "decision", "name": "下周去杭州出差", "evidence": "决定下周去杭州出差"}, {"type": "question", "name": "报销怎么走", "evidence": "不知道报销怎么走"}]}
```

# 示例2
输入：
```json
{"text": "晚上我妈给我打电话，我打算明天去医院看看她，感觉有点焦虑。"}
```
输出：
```json
{"entities": [{"type": "person", "name": "我妈", "evidence": "我妈"}, {"type": "activity", "name": "明天去医院看我妈", "evidence": "我打算明天去医院看看她"}, {"type": "location", "name": "医院", "evidence": "去医院看看她"}, {"type": "emotion", "name": "焦虑", "evidence": "感觉有点焦虑"}, {"type": "decision", "name": "明天去医院", "evidence": "我打算明天去医院看看她"}]}
```

# 禁止规则区
- [v1.0] 禁止把时间词标为location。
- [v1.0] "他/她/它"单独出现不算person，需有上下文支撑。
- [v1.0] 情绪必须有词语证据，不能凭感觉推断。
- [v1.1] decision必须是已决定事项，"打算但还没想好"、"可能"、"也许"不算。
