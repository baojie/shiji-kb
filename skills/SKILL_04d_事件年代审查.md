# SKILL: 事件年代审查管线

> 基于Agent反思的逐章年代标注审查与迭代修正工作流，适用于大规模历史事件索引的质量保障。

---

## 一、问题定义

### 1.1 为什么需要审查管线

事件索引的年代标注来自自动推断脚本（`write_inferred_years.py`），存在系统性错误：

| 错误类型 | 典型偏差 | 130章review实证 |
|---------|---------|----------------|
| 单锚点塌缩 | 60+事件共享同一年份 | 001五帝、046田敬仲完等 |
| 锚点本身计算错误 | 216-368年 | 046田和代齐偏差216年 |
| 前元/中元/后元混淆 | 7-13年 | 011孝景本纪28处修正 |
| 年号/帝王混淆 | 12-300年 | 053萧何卒、046齐桓公午 |
| 追叙事件误用当前时间 | 20+年 | 053萧何为沛吏掾 |

自动检测只能发现格式和一致性错误，**语义错误**（如"二年"指惠帝二年还是汉二年）必须由AI反思判断。

### 1.2 管线设计原则

1. **逐章审查**：每章独立反思，避免上下文过长
2. **知识累积**：每章发现的新错误模式写入SKILL，后续章节自动获得
3. **人机协作**：Agent反思 + 脚本自动应用 + 人工抽检
4. **可恢复**：管线状态持久化，中断后可从断点继续

---

## 二、管线架构

### 2.1 三步循环

```
┌────────────────────────────────────────────┐
│  Step 1: 生成提示词                         │
│  run_review_pipeline.py --prompt NNN        │
│  → 输出 review 提示词到 stdout              │
└───────────────┬────────────────────────────┘
                ▼
┌────────────────────────────────────────────┐
│  Step 2: Agent反思                          │
│  Agent工具执行反思 → 输出 JSON              │
│  包含 corrections[] + new_patterns[]        │
└───────────────┬────────────────────────────┘
                ▼
┌────────────────────────────────────────────┐
│  Step 3: 导入结果 + 应用修正                │
│  --ingest NNN result.json → 更新SKILL+提示词│
│  apply_reflect_fixes.py NNN → 写入事件索引   │
└───────────────┬────────────────────────────┘
                ▼
            下一章循环
```

### 2.2 关键脚本

| 脚本 | 用途 | 路径 |
|------|------|------|
| `run_review_pipeline.py` | 管线主控（--prompt/--ingest/--report） | `kg/events/scripts/` |
| `generate_review_prompts.py` | 批量生成130章提示词 | `kg/events/scripts/` |
| `apply_reflect_fixes.py` | 将修正写入事件索引 | `kg/events/scripts/` |

### 2.3 数据流

```
事件索引(.md)
    ↓ parse
review提示词(.md)  ←── SKILL_04c_事件年代推断.md（累积的错误模式+推理逻辑）
    ↓ Agent反思
reflect结果(.json)  →  corrections[] + new_patterns[]
    ↓ --ingest
    ├── SKILL_04c_事件年代推断.md  ← 追加new_patterns
    ├── pipeline_state.json    ← 更新进度
    └── 下一章提示词(.md)      ← 包含新学到的模式
    ↓ apply_reflect_fixes.py
事件索引(.md)  ← 概览表+详情表年份同步更新
```

---

## 三、Step 1: 生成提示词

### 3.1 命令

```bash
python kg/events/scripts/run_review_pipeline.py --prompt NNN
```

输出到 stdout，包含：
- 章节元信息（章名、时代分类）
- 该章事件索引全文
- 适用的错误模式（从SKILL中筛选该时代相关的）
- 年表中该时代的关键条目
- 输出格式要求（JSON schema）

### 3.2 提示词也可预生成

```bash
python kg/events/scripts/generate_review_prompts.py          # 全部130章
python kg/events/scripts/generate_review_prompts.py 001-012  # 指定范围
```

输出到 `kg/events/prompts/review_NNN.md`。

---

## 四、Step 2: Agent反思

### 4.1 反思任务

Agent收到提示词后，对每个事件执行：

1. **验证锚点**：查年表确认精确纪年是否正确
2. **检查reign-year换算**：纪年标记 → 基准年 → 公式换算
3. **识别"N年"归属**：从上下文判断指哪位君主
4. **检查单锚点塌缩**：多个事件共享同一推断年份
5. **检查追叙段落**：传记开头的早年经历
6. **确定性升级**：`[约公元前XXX年]` → `（公元前XXX年）`

### 4.2 输出JSON格式

```json
{
  "chapter_id": "046",
  "corrections": [
    {
      "event_id": "046-008",
      "original_time": "[约公元前602年]",
      "suggested_year": "（公元前386年）",
      "reason": "年表前386年明确记载'田和列为诸侯'",
      "error_type": "锚点计算错误",
      "confidence": "high"
    }
  ],
  "new_patterns": [
    {
      "name": "世代数≠年数",
      "description": "世家类章节不能把世代数直接换算成年数",
      "example": "046-008：从陈完到田和约十代286年，原计算为53年",
      "detection": "检查世代间隔是否在25-30年/代范围内"
    }
  ]
}
```

### 4.3 字段说明

**corrections[]**：
- `event_id`：事件编号（如 `046-008`）
- `original_time`：原时间标注
- `suggested_year`：建议修正值，使用三级标注格式
- `reason`：修正理由（必须引用具体依据）
- `error_type`：对应SKILL中的错误模式名
- `confidence`：`high`（年表确认）/ `medium`（reign-year换算）/ `low`（推断）

**new_patterns[]**：
- 本章发现的、SKILL中尚未记录的新错误模式
- 会被 `--ingest` 追加到 `SKILL_04c_事件年代推断.md`

---

## 五、Step 3: 导入与应用

### 5.1 导入反思结果

```bash
python kg/events/scripts/run_review_pipeline.py --ingest NNN /tmp/reflect_NNN.json
```

执行：
1. 解析JSON，验证格式
2. 将 `new_patterns` 追加到 `SKILL_04c_事件年代推断.md`
3. 更新 `pipeline_state.json`（进度、累积统计）
4. 生成下一章提示词（自动包含新学到的模式）

### 5.2 应用修正到事件索引

```bash
python kg/events/scripts/apply_reflect_fixes.py NNN
```

执行：
1. 读取 `kg/events/reports/reflect_NNN.json`
2. 逐条匹配事件索引中的概览表和详情表
3. 同步更新概览表时间列 + 详情的时间字段
4. 保留原有的纪年标记（`%N年%`），只替换公元年部分
5. 输出修改统计

### 5.3 修正应用规则

```
原时间字段: "%秦昭王十三年% [约公元前307年]"
suggested_year: "（公元前294年）"
结果: "%秦昭王十三年% （公元前294年）"
```

- 纪年标记（`%...%`）保留
- 旧的公元年标注被替换
- 新标注使用 `suggested_year` 的原始格式（含括号类型）

---

## 六、管线状态管理

### 6.1 状态文件

`kg/events/reports/pipeline_state.json`：

```json
{
  "last_chapter": "046",
  "completed_chapters": ["001", "109"],
  "total_corrections": 56,
  "total_new_patterns": 26,
  "accumulated_patterns": ["单锚点塌缩", "锚点计算错误", ...]
}
```

### 6.2 断点恢复

```bash
python kg/events/scripts/run_review_pipeline.py --resume
```

从 `last_chapter` 的下一章继续。

### 6.3 查看报告

```bash
python kg/events/scripts/run_review_pipeline.py --report
```

输出各章审查统计汇总。

---

## 七、自动检测模式（无需Agent）

管线也支持纯脚本自动检测（快速，无API调用）：

```bash
python kg/events/scripts/run_review_pipeline.py 001-130
```

自动检测项：
- 概览表与详情表年份不一致
- 同一年份被多个事件共享（塌缩嫌疑）
- 时间字段格式不规范
- 纪年标记与公元年不匹配
- 事件时间超出合理范围

---

## 八、实证统计

### 130章review结果

| 指标 | 数量 |
|------|------|
| 年代推断条目总数 | 2,018 |
| 修正错误 | ~400+ |
| 新增错误模式 | 26种 |
| 新增推理逻辑 | 12种 |
| 新增标注（原无标注） | 161 |

### 已完成的Agent反思章节

| 章节 | 事件数 | 修正数 | 关键发现 |
|------|--------|--------|---------|
| 001 五帝本纪 | 66 | 44 | 单锚点塌缩到前2290年 |
| 109 李将军列传 | 16 | 12 | 详情塌缩到前166年 |

---

## 九、参考文件

| 文件 | 用途 |
|------|------|
| `SKILL_04c_事件年代推断.md` | 累积的错误模式和推理逻辑（Agent反思的知识库） |
| `kg/events/data/NNN_*_事件索引.md` | 130章事件索引（审查对象） |
| `kg/events/prompts/review_NNN.md` | 130章预生成的审查提示词 |
| `kg/events/reports/review_NNN.json` | 自动检测结果 |
| `kg/events/reports/reflect_NNN.json` | Agent反思结果 |
| `kg/events/reports/pipeline_state.json` | 管线状态 |
| `kg/chronology/data/中国历史大事年表.md` | 交叉验证的ground truth |
