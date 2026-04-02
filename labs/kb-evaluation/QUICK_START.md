# 快速开始指南

## 概述

本指南帮助你快速了解和使用史记知识库测试问题集。

## 5分钟快速上手

### 1. 了解项目结构

```
labs/kb-evaluation/
├── README.md                    # 项目概述
├── QUICK_START.md              # 本文件：快速开始
├── question-design-spec.md     # 详细设计规范
├── questions/                  # 10组问题集（JSON格式）
│   └── set01_person_basic.json # 示例：第1组
├── answers/                    # 对应的答案集
│   └── set01_person_basic_answers.json
├── scripts/                    # 验证和测试脚本
│   ├── validate_coverage.py   # 验证章节覆盖率
│   └── validate_uniqueness.py # 验证问题互斥性
└── reports/                    # 自动生成的报告
```

### 2. 查看示例问题

查看第1组示例问题（20个）：

```bash
cat questions/set01_person_basic.json | python -m json.tool | head -50
```

或直接用文本编辑器打开 `questions/set01_person_basic.json`

### 3. 查看答案格式

```bash
cat answers/set01_person_basic_answers.json | python -m json.tool | head -50
```

### 4. 运行验证脚本

验证示例问题集的章节覆盖率：

```bash
cd scripts/
python validate_coverage.py --set set01_person_basic
```

## 10组问题分类一览

| 组号 | 名称 | 文件名 | 覆盖维度 | 状态 |
|-----|------|--------|---------|------|
| 1 | 人物基本信息 | set01_person_basic.json | 姓名、字号、籍贯、家世、成就 | ✓ 示例已完成(20题) |
| 2 | 人物关系网络 | set02_person_relations.json | 君臣、师徒、亲属、朋友、敌对 | ⏳ 待开发 |
| 3 | 重大历史事件 | set03_events_major.json | 战争、政变、改革、灾害 | ⏳ 待开发 |
| 4 | 时间与年代 | set04_chronology.json | 纪年、时长、时序、历法 | ⏳ 待开发 |
| 5 | 地理信息 | set05_geography.json | 地名、都城、封地、战场 | ⏳ 待开发 |
| 6 | 制度与官职 | set06_institutions.json | 官职、礼仪、法律、经济、军事 | ⏳ 待开发 |
| 7 | 思想与文化 | set07_culture_ideology.json | 哲学、典籍、太史公评论 | ⏳ 待开发 |
| 8 | 器物与自然 | set08_objects_nature.json | 器物、生物、天文、神话 | ⏳ 待开发 |
| 9 | 成语与典故 | set09_idioms_allusions.json | 成语来源、典故、名言 | ⏳ 待开发 |
| 10 | 综合推理 | set10_reasoning_complex.json | 因果推理、对比分析、综合评价 | ⏳ 待开发 |

## 问题格式示例

### 问题JSON格式

```json
{
  "id": "Q001",
  "question": "孔子的字是什么？",
  "type": "factual",
  "difficulty": "easy",
  "category": "person_basic_name",
  "subcategory": "字号",
  "target_chapters": ["047"],
  "keywords": ["孔子", "字", "仲尼"]
}
```

**字段说明**：
- `id`: 问题唯一标识，格式为 Q001-Q100
- `question`: 问题文本
- `type`: 问题类型（factual/relational/inferential/comparative/evaluative）
- `difficulty`: 难度（easy/medium/hard）
- `category`: 主类别（如 person_basic_name）
- `subcategory`: 子类别（如 字号）
- `target_chapters`: 目标章节列表（使用3位数字格式，如 "047"）
- `keywords`: 关键词列表，用于检索和验证

### 答案JSON格式

```json
{
  "question_id": "Q001",
  "answer": "仲尼",
  "answer_type": "short_text",
  "sources": [
    {
      "chapter": "047_孔子世家",
      "location": "chapter_start",
      "quote": "孔子生鲁昌平乡陬邑...字仲尼，姓孔氏。"
    }
  ],
  "explanation": "孔子名丘，字仲尼。史记明确记载'字仲尼，姓孔氏'",
  "related_entities": ["@孔子"],
  "confidence": "high"
}
```

**字段说明**：
- `question_id`: 对应问题的ID
- `answer`: 简短答案
- `answer_type`: 答案类型（short_text/long_text/number/list等）
- `sources`: 原文出处列表
  - `chapter`: 章节名称
  - `location`: 位置描述（chapter_start/mid_chapter/chapter_end/taishigongyue）
  - `quote`: 原文引用
- `explanation`: 补充说明
- `related_entities`: 相关实体（使用标注符号）
- `confidence`: 置信度（high/medium/low）

## 使用验证脚本

### 1. 验证章节覆盖率

验证单个问题集：

```bash
python scripts/validate_coverage.py --set set01_person_basic
```

验证所有问题集：

```bash
python scripts/validate_coverage.py --all
```

输出示例：

```
# 章节覆盖率报告

## 问题集：set01_person_basic

### 总体统计
- 总问题数：20
- 覆盖章节数：16/130 (12.3%)
- 平均每章问题数：0.15
- 标准差：0.42

### 本纪覆盖 (12篇)
- 覆盖章节：4/12 (33.3%)
...
```

### 2. 验证问题互斥性

```bash
python scripts/validate_uniqueness.py --all
```

检查10组问题之间是否有重复或交叉。

## 如何贡献问题

### 第1步：选择一个问题组

查看上面的"10组问题分类一览"表格，选择一个"待开发"的问题组。

### 第2步：阅读设计规范

仔细阅读 [question-design-spec.md](question-design-spec.md) 中对应问题组的设计指南。

### 第3步：设计问题

按照以下步骤设计问题：

1. **确定子类型分布**（参考设计规范）
2. **选择目标章节**（确保覆盖均衡）
3. **编写问题文本**（清晰、明确、无歧义）
4. **标注难度级别**（简单40% / 中等40% / 困难20%）
5. **提取关键词**（用于检索和验证）

### 第4步：编写答案

为每个问题编写答案，必须包含：

1. **简短答案**：核心回答
2. **原文引用**：史记原文出处
3. **章节位置**：具体章节和位置
4. **补充说明**：必要的背景解释
5. **置信度**：high/medium/low

### 第5步：验证质量

运行验证脚本：

```bash
# 验证覆盖率
python scripts/validate_coverage.py --set set0X_your_set

# 验证与其他组的互斥性
python scripts/validate_uniqueness.py --all
```

确保：
- ✓ 章节覆盖率 > 80%
- ✓ 分布标准差 < 3.0
- ✓ 与其他组完全互斥

## 常见问题 (FAQ)

### Q1: 问题数量必须是100个吗？

A: 是的。每组必须正好100个问题，这是设计要求。示例中只有20个是为了演示格式。

### Q2: 如何确保与其他组互斥？

A: 使用验证脚本 `validate_uniqueness.py`。主要原则：
- 问题文本不能重复
- 同一核心实体不要在多个组中作为主要查询对象
- 关注的知识维度要不同

### Q3: 难度如何判断？

A: 参考以下标准：
- **简单**：直接查询单一事实，答案在单章明确记载
- **中等**：需要理解上下文，或答案分散在同章不同位置
- **困难**：需要跨章节整合信息，或需要复杂推理

### Q4: target_chapters 可以有多个吗？

A: 可以。简单问题通常1个章节，中等问题1-2个，困难问题可能3个以上。

### Q5: 如何处理史记中有争议的内容？

A: 以史记原文为准，在explanation中说明争议。置信度标记为medium或low。

## 下一步

- 阅读完整的 [README.md](README.md) 了解项目背景
- 查看 [question-design-spec.md](question-design-spec.md) 学习详细设计规范
- 参考 `set01_person_basic.json` 开始设计你的第一组问题
- 加入项目讨论（如有协作平台）

## 技术支持

如有问题，请：
1. 查阅 [question-design-spec.md](question-design-spec.md) 中的详细说明
2. 参考已完成的示例问题集
3. 运行验证脚本检查问题

---

**文档版本**: v1.0
**创建日期**: 2026-04-02
**维护者**: 史记知识库项目组
