---
name: skill-04
title: 事件构建
description: 从标注文本到结构化事件
---

# SKILL 04: 事件构建 — 从标注文本到结构化事件

> 从标注文本中提取结构化事件，标注公元纪年，通过Agent反思审查年代准确性。

---

## 一、工序位置

```
标注文本 (chapter_md/*.tagged.md)
    │
    ▼ 04a 事件识别
事件索引 (kg/events/data/NNN_*_事件索引.md)
    │
    ▼ 04c 事件年代推断
公元纪年标注
    │
    ▼ 04d 事件年代审查
年代修正 (Agent反思)
    │
    ▼ 04e 年份消歧
年号/纪年消歧
```

十表（013-022）有专用补充流程（04b），与主流程并行。

---

## 二、方法论

### 为什么用LLM提取事件？

古籍事件不同于新闻事件：
- 一个"事件"可能跨越数段叙述（"鸿门宴"跨十余段）
- 事件粒度需要语义判断（"秦灭六国"是一个事件还是六个？）
- 因果关系深藏在叙事逻辑中，非字面可提取

### 自动 vs LLM 分工

| 任务 | 方法 | 原因 |
|------|------|------|
| 事件提取 | LLM | 需理解叙事语义和粒度判断 |
| 公元纪年标注 | 规则 | 年号表+在位年可计算 |
| 纪年审查 | LLM (Agent) | 需综合判断年代合理性 |

---

## 三、执行流程

```bash
# 1. 提取事件
python kg/events/scripts/extract_events.py

# 2. 构建年份映射
python kg/events/scripts/build_year_map.py

# 3. 标注公元纪年
python kg/events/scripts/annotate_ce_years.py

# 4. 纪年质检（迭代修复）
python kg/events/scripts/lint_ce_years.py

# 5. Agent反思审查（按章循环）
python kg/events/scripts/run_review_pipeline.py --prompt NNN

# 6. 格式验证
python kg/events/scripts/validate_events.py
```

---

## 四、产出统计

| 指标 | 数值 |
|------|------|
| 总事件数 | 3,185 |
| 覆盖章节 | 130/130 (100%) |
| 事件类型 | 11种 |
| 有CE标注 | 3,051 (98.7%) |
| 战争事件 | 736 |
| 时间范围 | 前2700年 ~ 前87年 |
| 年代修正 | ~2,119次（五轮反思） |

---

## 五、子工序索引

| 编号 | 文件 | 内容 |
|------|------|------|
| 04a | SKILL_04a_事件识别.md | 事件定义/Schema/11种类型/体裁策略 |
| 04b | SKILL_04b_十表事件处理.md | 十表（013-022）专用补充提取 |
| 04c | SKILL_04c_事件年代推断.md | 分层纪年解析/君主在位数据库 |
| 04d | SKILL_04d_事件年代审查.md | Agent反思审查工作流 |
| 04e | SKILL_04e_年份消歧.md | 同一年号在不同语境中的消歧 |
