# 人物生卒年反思流程

> **详细技术方法**参见：[SKILL_07a_人物生卒年推断.md](../../skills/SKILL_07a_人物生卒年推断.md)

---

## 概述

通过多轮反思迭代，从《史记》原文和事件索引中推断人物生卒年**区间**（而非点值），记录证据链和置信度，并与亲属关系交叉验证。

**关键特点**：
- 生卒年采用 **span（区间）格式**：`birth_min/birth_max`，`death_min/death_max`
- 区间宽度反映证据强度（exact: 0年 → legend: >50年）
- 每个推断附带证据链和置信度分级
- 与事件索引、亲属关系数据交叉验证

---

## 四轮反思流程

### 第一轮：提取年龄和在位年数证据

**任务**：从 `chapter_md/*.tagged.md` 扫描提取年龄/在位年数证据

**提取模式**（正则扫描）：
```
- "生X岁" / "年X岁立" / "年已X岁"
- "立X年卒" / "在位X年" / "为X X年"
- "德公生三十三岁而立，立二年卒"
```

**输出格式**：
```json
{
  "秦德公": {
    "evidence_text": "德公生三十三岁而立，立二年卒",
    "age_at_enthronement": 33,
    "reign_years": 2,
    "chapter": "005_秦本纪",
    "paragraph": "¶005-023"
  }
}
```

**脚本**：`kg/entities/scripts/extract_age_evidence.py`

---

### 第二轮：获取锚点事件年份

**任务**：从事件索引关联人物的关键事件年份

**关键事件类型**：
- 即位事件（在位元年）
- 卒年事件（明确卒年）
- 出奔事件（年龄下限约束）
- 仕于某君事件（活跃期约束）

**数据源**：
- `kg/events/data/{章节编号}_事件索引.md`（已含公元纪年）
- `kg/chronology/data/year_ce_map.json`（纪年换算）

**输出格式**：
```json
{
  "秦德公": {
    "enthronement_year": -677,
    "death_year": -675,
    "events": [
      {
        "type": "即位",
        "year_ce": -677,
        "event_id": "005-E023"
      },
      {
        "type": "卒",
        "year_ce": -675,
        "event_id": "005-E025"
      }
    ]
  }
}
```

**脚本**：`kg/entities/scripts/extract_anchor_events.py`

---

### 第三轮：计算生卒年区间

**任务**：综合第一轮和第二轮数据，按方法优先级推断生卒年区间

**推断方法优先级**（从高到低）：

| 优先级 | 方法 | 置信度 | 区间宽度 | 示例 |
|--------|------|--------|----------|------|
| 1 | 直接卒年记载 | exact/high | 0-5年 | "三十九年，缪公卒" + 元年已知 |
| 2 | 在位年数反推 | high | ≤5年 | "立二年卒" + 即位年已知 |
| 3 | 年龄+事件锚点 | high | ≤5年 | "年已二十一岁立" + 即位年已知 |
| 4 | 相对关系约束 | low | 20-50年 | 父子关系、同朝为官 |
| 5 | 世代数推算 | legend | >50年 | "X世孙" + 始祖年代 |

**计算示例**：
```python
# 示例：秦德公
age_at_enthronement = 33  # 第一轮提取
reign_years = 2           # 第一轮提取
enthronement_year = -677  # 第二轮提取

# 推断卒年（方法2：在位年数反推）
death_year = enthronement_year + reign_years = -675
death_min, death_max = -675, -675  # exact
confidence_death = "high"

# 推断生年（方法3：年龄+事件锚点）
birth_year = enthronement_year - age_at_enthronement = -710
birth_min, birth_max = -712, -708  # ±2年误差
confidence_birth = "high"
```

**输出格式**：
```json
{
  "秦德公": {
    "birth_min": -712,
    "birth_max": -708,
    "death_min": -675,
    "death_max": -675,
    "birth_label": "[约公元前710年]",
    "death_label": "（公元前675年）",
    "confidence": "high",
    "evidence": [
      "《史记·秦本纪》：德公生三十三岁而立，立二年卒",
      "年表：德公元年=前677年，即位后2年卒=前675年"
    ],
    "method": "在位年数反推(卒年) + 年龄+事件锚点(生年)"
  }
}
```

**脚本**：`kg/entities/scripts/calculate_lifespan_intervals.py`

---

### 第四轮：亲属关系交叉约束验证

**任务**：用亲属关系约束验证生卒年区间的合理性，标记矛盾

**验证规则**：
1. **父卒 < 子生**：父亲卒年必须早于子女生年
2. **兄弟年龄差 < 40年**：同父兄弟生年差异通常不超过40年
3. **生育年龄 20-60岁**：父母生育时年龄应在合理范围
4. **在世期间约束**：人物活跃事件应在其生卒年区间内

**数据源**：
- `kg/entities/data/person_relations.json`（亲属关系）
- `kg/events/data/*_事件索引.md`（事件年份）

**矛盾检测示例**：
```json
{
  "contradictions": [
    {
      "type": "父卒早于子生",
      "father": "秦德公",
      "father_death": -675,
      "child": "秦某子",
      "child_birth_min": -680,
      "severity": "critical",
      "note": "需重新检查生卒年或父子关系"
    },
    {
      "type": "兄弟年龄差异常",
      "person1": "秦成公",
      "person1_birth": -710,
      "person2": "秦缪公",
      "person2_birth": -665,
      "age_gap": 45,
      "severity": "warning",
      "note": "可能为同父异母或养子关系"
    }
  ]
}
```

**输出**：
- 验证通过的生卒年区间 → 标记 `validated: true`
- 有矛盾的条目 → 标记 `has_contradictions: true`，附带矛盾详情
- 矛盾报告：`kg/entities/data/lifespan_contradictions.json`

**脚本**：`kg/entities/scripts/validate_lifespan_constraints.py`

---

## 数据升级计划

### 现有数据状态
- **文件**：`kg/entities/data/person_lifespans.json`
- **规模**：约60人
- **格式**：点值格式 `{"birth": -551, "death": -479}`
- **来源**：外部百科，非从史记文本推断
- **问题**：无置信度、无推断依据、无区间

### 升级步骤

**Step 1**: 点值转区间（保守估计）
```python
# 将现有点值转为区间，标记为"外部来源，待验证"
for person, data in old_data.items():
    new_data[person] = {
        "birth_min": data["birth"] - 5,
        "birth_max": data["birth"] + 5,
        "death_min": data["death"] - 5,
        "death_max": data["death"] + 5,
        "confidence": "external",  # 待验证
        "evidence": ["来自外部百科，需从史记验证"],
        "validated": False
    }
```

**Step 2**: 批量提取年龄证据
- 运行第一轮脚本，扫描130章
- 提取所有"生X岁"/"立X年"等证据

**Step 3**: 试点验证（前5章本纪）
- 对001-005章的君主人物逐一推断
- 验证方法的准确性和覆盖率
- 调整算法参数

**Step 4**: 全量推断
- 扩展到130章所有人物
- 生成完整的 `person_lifespans_v2.json`

**Step 5**: 交叉验证
- 运行第四轮验证脚本
- 修正矛盾条目
- 生成验证报告

---

## 输出文件

### 主数据文件
```
kg/entities/data/person_lifespans_v2.json
```
格式见上文"第三轮"输出示例。

### 推断报告
```
doc/entities/人物生卒年推断报告.md
```
内容包括：
- 总体统计（覆盖人数、置信度分布）
- 各章节推断情况（覆盖率、证据类型分布）
- 矛盾案例列表
- 高置信度案例示例
- 低置信度案例（需人工审核）

### 矛盾检测报告
```
kg/entities/data/lifespan_contradictions.json
```
格式见上文"第四轮"示例。

---

## 传说时代特殊处理

**范围**：五帝至夏（001-003章）

**原则**：
- 所有传说人物统一标记 `"confidence": "legend"`
- 区间宽度 ≥ 100年
- 不用生卒年中点作为事件锚点（见 SKILL_04c 错误模式30）
- 优先用朝代起止年作为定位
  - 夏始：前2070年
  - 汤灭夏：前1600年

**示例**：
```json
{
  "黄帝": {
    "birth_min": -2817,
    "birth_max": -2617,
    "death_min": -2699,
    "death_max": -2499,
    "birth_label": "[约公元前2717年]",
    "death_label": "[约公元前2599年]",
    "confidence": "legend",
    "evidence": ["现代学界推算，传说时代无可靠记载"],
    "note": "区间极宽，仅供参考定位，不用于精确计算"
  }
}
```

---

## 与谥号索引的关联

**完成生卒年推断后需更新谥号索引**：

1. **数据同步**：
   - 将 `person_lifespans_v2.json` 中的生卒年区间同步到谥号索引
   - 更新 `kg/entities/data/shihao_index.json` 中的 `lifespan` 字段

2. **HTML页面更新**：
   - 重新生成 `docs/special/shihao.html`
   - 显示生卒年区间（如"前424-前362年"）和置信度标记

3. **置信度可视化**：
   - 高置信度（exact/high）：正常显示
   - 中等置信度（medium）：添加"约"字前缀
   - 低置信度（low/legend）：添加"[推测]"标记

**更新脚本**：
```bash
# 生卒年推断完成后运行
python kg/entities/scripts/build_shihao_index.py --use-lifespans-v2
```

---

## 与其他工序的关系

| 方向 | 工序 | 说明 |
|------|------|------|
| **输入** | SKILL_04c 事件年代推断 | 提供锚点事件的公元纪年 |
| **输入** | SKILL_05b 实体关系构建 | 提供亲属关系（用于交叉约束） |
| **输出→** | SKILL_07 矛盾检测 | 生卒年区间用于检测年龄矛盾、同时代人冲突 |
| **输出→** | SKILL_04c 事件年代推断 | 反向校验：事件年份应落在当事人生卒区间内 |
| **输出→** | 应用 09 | 人物时间轴可视化 |
| **输出→** | 谥号索引 | 补充生卒年数据到谥号索引页面 |

---

## 实施时间表

| 阶段 | 任务 | 预计工时 | 输出 |
|------|------|----------|------|
| 准备 | 设计反思流程，编写脚本框架 | 2小时 | 脚本骨架 |
| 第一轮 | 提取年龄/在位年数证据 | 3小时 | age_evidence.json |
| 第二轮 | 提取锚点事件年份 | 2小时 | anchor_events.json |
| 第三轮 | 计算生卒年区间 | 4小时 | person_lifespans_v2.json |
| 第四轮 | 亲属关系交叉验证 | 3小时 | lifespan_contradictions.json |
| 数据升级 | 升级现有60人数据 | 1小时 | - |
| 试点验证 | 前5章本纪人物推断 | 2小时 | 验证报告 |
| 文档输出 | 生成推断报告 | 2小时 | 推断报告.md |
| 特殊处理 | 传说时代人物标记 | 1小时 | - |
| **总计** | | **20小时** | |

---

## 相关文档

- **方法论SKILL**：[SKILL_07a_人物生卒年推断.md](../../skills/SKILL_07a_人物生卒年推断.md)
- **姓氏制度**：[doc/spec/姓氏制度.md](姓氏制度.md)（亲属关系推断）
- **事件年代反思**：[kg/events/reports/](../../kg/events/reports/)（参考流程）
- **谥号索引需求**：[doc/spec/谥号索引需求说明.md](谥号索引需求说明.md)

---

**创建时间**: 2026-03-23
**状态**: 待实施
**优先级**: Medium
**预计工作量**: 20小时
