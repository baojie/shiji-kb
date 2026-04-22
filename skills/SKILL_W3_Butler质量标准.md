---
name: skill-butler-3
description: Butler 的 wiki 质量标准 (rubric) — 一个页面怎样算"好"。5 维度 + 量化信号 + 红旗。本 skill 是 mutable — W5 反思后可修订 (改 rubric 本身是核心进化之一)。W2 行动前用作前置检查, W4 评估用作打分依据。顶部保留 version 字段跟踪变更。
---

# SKILL W3: 质量标准 (Rubric)

> **本 skill 会变**。W5 反思会修订本文, 改动记 `logs/wiki_butler/skill_changes.md`。

---

## 版本

- **v0.1** (2026-04-22) · 初版, 5 维度, 量化阈值偏松
- v0.2 预期 (10 次反思后) · 收紧阈值, 加"引证完整性"维度

---

## 一、五维度

好的 wiki 页应在以下维度都不差 (**及格线**), 其中 1-2 维度优秀则算好页。

| 维度 | 简述 | 量化信号 (v0.1) |
|---|---|---|
| **1. 完整性** | 关键结构区都有内容 | frontmatter 必填字段齐; 至少 3 个 section; 字数 200–2000 |
| **2. 准确性** | 事实有源 | 无编造; 生卒/出处有 kg / doc 可追溯 |
| **3. 链接密度** | 页内 wikilink 多 + 少 broken | resolved wikilink ≥ 5; broken 比例 ≤ 20% |
| **4. 信息来源分布** | 跨多源引用 | 至少 2 个食物源 (kg + SKU, 或 kg + doc 等); 纯 kg 信息是浅页 |
| **5. 可读性** | 人能顺畅读 | 句不过长 (< 80 字); 属性表 + 段落交替; 无机器痕迹 |

---

## 二、量化阈值 (v0.1)

```yaml
completeness:
  frontmatter_required: [id, type, label, aliases, canonical_name]
  min_sections: 3
  word_count_range: [200, 2000]

accuracy:
  forbidden_phrases: []  # v0 暂不 hardcode, 靠 6-不变量的"禁编造"
  required_citation: false  # v0.2 起改 true

link_density:
  min_resolved_wikilinks: 5
  max_broken_ratio: 0.20

source_diversity:
  min_sources: 2   # 即至少 2 个食物源有输入
  allowed_sources: [kg, sku, doc, docs]

readability:
  max_sentence_length: 80
  prefer_pattern: alternate_table_and_paragraph
```

---

## 三、红旗 (fail 信号, 见 W4)

任一红旗 → 该页当前版本不可接受, 需要修:

- 🚩 frontmatter `id` 为空或与文件名不符
- 🚩 body 全为机器生成表格, 无一段叙述文字
- 🚩 broken wikilink 比例 > 50%
- 🚩 单一源 (完全来自 kg 或完全来自 SKU), 无跨源
- 🚩 frontmatter `auto_generated: true` 持续 > 30 天未被二次加工
- 🚩 页面字数 < 50 (空壳)

---

## 四、加分项 (rubric bonus)

在五维度及格基础上, 出现以下加分 (W4 评估可+1 分):

- ➕ infobox 含生卒 / 别名 / 身份 全套
- ➕ 事件时间线按年代排序
- ➕ 有脚注引证 doc/ 报告
- ➕ 有"相关主题"区链到 topic 页
- ➕ 跨食物源 ≥ 3 个

---

## 五、本版本的已知短板

v0.1 刻意**宽松**, 目的是早期 butler 能产出量, 别被 rubric 卡住。**v0.2 计划收紧**:

- 字数下限 200 → 350
- 至少 2 段叙述 (现版没要求)
- 必须至少 1 条脚注
- auto_generated 连续存在天数阈值 30 → 14

时间表：**20 次 invocation 之后** W5 反思自动提案 v0.2。

---

## 六、修订流程 (self-mutation)

W5 可修订本 skill, 但需:

1. 写 `reflections/<date>.md`, 说明修订动因 + 涉及的 actions 日志编号
2. 新增条目在 §一 / §二 中明确插入
3. 顶部 "版本" 块追加新版本, 列出变更摘要
4. `skill_changes.md` 加一行 `YYYY-MM-DD W3 v0.x→v0.y [摘要]`
5. 本版更严 → old_accepted 的页**不追溯**, 仅新页按新版。若要 re-evaluate 老页, 单独做一轮。

---

## 七、非目标

**不追求**:
- 统一风格 / 编辑语气 (那属于校对, 不属于 butler)
- 完美的语言 (butler 不改措辞)
- 绝对全覆盖 (butler 是渐进式, 不是一次性补完)

---

## 相关
- [W4 评估与检验](SKILL_W4_Butler评估与检验.md) — 用本 rubric 打分
- [W5 反思与自改](SKILL_W5_Butler反思与自改.md) — 修订本 skill 的入口
