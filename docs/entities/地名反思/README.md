# 地名反思档案

本目录沉淀《史记》place 实体分类（SKILL 03h）每轮"未分类地名反思"工作成果。

## 工作流

1. `python3 kg/entities/scripts/classify_places.py` 先分类一遍，输出 `kg/entities/data/place_categories.json`
2. `python3 kg/entities/scripts/dump_blank_places.py [轮次]` 提取当前未分类条目的上下文到 `第N轮_上下文.md`（无参数则写入 `待反思_上下文.md`）
3. 人工或半自动根据上下文反思分类，把判断与规则候选记入 `第N轮_反思报告.md`
4. 规则归纳后回填到 [`skills/SKILL_03h_地名地段分类.md`](../../../skills/SKILL_03h_地名地段分类.md) 并更新 [`classify_places.py`](../../../kg/entities/scripts/classify_places.py)
5. 重跑 → 未分类减少 → 下一轮

## 历史轮次

| 轮次 | 上下文文件 | 反思报告 | 起始未分类 → 结束未分类 |
|------|-----------|----------|---------------------|
| 第一轮 | [第一轮_上下文.md](第一轮_上下文.md) | [第一轮_反思报告.md](第一轮_反思报告.md) | 462 → 0 |
