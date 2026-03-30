---
skill: SKILL-人物追踪
version: 1.0
model_target: small-2b
last_updated: 2026-03-30
---

# 任务说明
把多个片段里提到的人物指代归并到同一实体。
第一人称场景中，同一个人可能被叫做不同的名字或用不同称谓指代。
不确定时保持独立，不强行归并。

# 输入格式
```json
{"persons": [{"name": "...", "segment_id": 1, "context": "..."}]}
```
persons 是从多个片段收集到的所有 person 实体，可能包含重复或别名。

# 输出格式
```json
{"groups": [{"canonical_name": "...", "aliases": ["...", "..."], "evidence": "..."}]}
```
- canonical_name：这组人物的规范名称，优先用真实姓名，无姓名时用最具体的称谓。
- aliases：这组人物的所有别名/指代，包括 canonical_name 本身。
- evidence：归并依据，一句话说明为什么认为是同一人。

# 归并规则（按优先级）
1. 完全相同的名字 → 同一人。
2. 姓名 + 称谓匹配：例如"老王"和"王工"可能同一人（需要上下文支撑）。
3. 代词归并：在同一场景/片段中，"他/她"指向最近出现的同性别人物。
4. 关系词一致：两次提到"同事"且上下文相似（同一公司、同一话题）→ 可能同一人。
5. 不同场景中的模糊人物 → 不归并，保持独立。

# 严格规则
- 输出必须是合法JSON。
- 只能输出一个对象，键名固定为 groups。
- 每个 person 必须出现在且仅出现在一个 group 中。
- 宁可多建 group 也不要错误归并。
- 跨场景出现的匿名人物（"他"、"那个人"）默认不归并，除非有强证据。

# 示例
输入：
```json
{"persons": [{"name": "老王", "segment_id": 1, "context": "我跟老王开会"}, {"name": "王工", "segment_id": 3, "context": "王工说下周来"}, {"name": "他", "segment_id": 3, "context": "他说下周来"}, {"name": "我妈", "segment_id": 5, "context": "我妈打电话来"}, {"name": "同事甲", "segment_id": 7, "context": "同事甲帮我改了代码"}]}
```
输出：
```json
{"groups": [{"canonical_name": "老王", "aliases": ["老王", "王工", "他"], "evidence": "segment3中'他说下周来'紧接'王工说下周来'，指同一人"}, {"canonical_name": "我妈", "aliases": ["我妈"], "evidence": "单次出现，唯一指代"}, {"canonical_name": "同事甲", "aliases": ["同事甲"], "evidence": "单次出现，唯一指代"}]}
```

# 禁止规则区
- 禁止把说话人自己（"我"）归入任何group。
- 禁止仅凭性别相同就归并两个不同场景的人物。
