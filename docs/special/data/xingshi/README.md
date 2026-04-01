# 姓氏数据说明

本目录包含《史记》人物姓氏推理数据。

## 文件清单

| 文件 | 大小 | 说明 | 版本 | 最后更新 |
|------|------|------|------|----------|
| `xing_index.json` | 3.3KB | 先秦11大姓源流和分封诸国索引 | - | 2026-03-16 |
| `person_xingshi.json` | 604KB | 人物姓氏JSON数据（2095人） | v2.1 | 2026-03-24 |
| `person_xingshi.md` | 50KB | 人物姓氏推理详情表格（616人详细） | - | 2026-03-24 |
| `pre_qin_xingshi.md` | 50KB | 先秦姓氏制度说明文档 | - | 2026-03-17 |

## 数据状态

- **JSON 数据**: 2095人，覆盖率 57.7%（v2.1）
- **MD 详细表格**: 616人（R1 直接记载 34人 + 重要人物补充 582人）
- **更新方式**: MD→JSON 增量更新脚本（保留旧数据 + 覆盖详细记录）
- **完整版本**: 原 v1.0 包含 2053人（R1-R6c 多轮推理结果）

## 数据来源

所有数据来自项目根目录：
- 源数据：`kg/entities/data/`
- 发布脚本：`scripts/publish_xingshi_data.py`

## 建设逻辑

person_xingshi.json 的生成采用 **AI Agent 多轮迭代推理** 方法：

1. **推理规则**：`skills/SKILL_07b_姓氏推理.md`
   - R1: 直接记载（明确的姓氏文本）
   - R2: 邦国推理（根据所属国家推断姓氏）
   - R3: 氏族推理（根据氏族归属）
   - R4-R5: 父系传播（姓沿父系不变）
   - R6-R14: 各种专门规则（章节归属、帝号、谥号等）

2. **提示词模板**：`kg/entities/scripts/prompt_template_姓氏推理.md`
   - 定义每轮迭代的工作流程
   - 输入：已有 JSON + 实体索引 + 章节文本
   - 输出：增量更新的 JSON 条目

3. **执行方式**：
   - 由 AI Agent（如 Claude）按提示词模板执行
   - 每轮迭代新增已知人物，解锁下轮推理
   - 非自动化脚本，需人工/Agent 配合

## 更新方法

### 方法一：从 MD 增量更新（推荐）

当 person_xingshi.md 有新的详细记录时：

```bash
# 1. 增量更新 JSON（保留旧数据 + MD 覆盖）
python kg/entities/scripts/update_xingshi_from_md.py

# 2. 发布到 docs 目录
python scripts/publish_xingshi_data.py

# 3. 提交更新
git add kg/entities/data/person_xingshi.json docs/special/data/xingshi/
git commit -m "更新人物姓氏数据"
```

### 方法二：AI Agent 多轮推理（完整重建）

要完整重建 person_xingshi.json（2411人，所有轮次）：

1. 阅读 `skills/SKILL_07b_姓氏推理.md` 了解推理规则
2. 使用 `kg/entities/scripts/prompt_template_姓氏推理.md` 作为提示词
3. 让 AI Agent 读取实体索引和章节文本
4. 按 R1-R6c 轮次执行推理，逐步扩展
5. 生成完整的 JSON（需要人工/Agent配合）
6. 运行发布脚本

## 数据格式

### xing_index.json
```json
{
  "姓": {
    "xing": "姬",
    "origin": "黄帝，以姬水为姓",
    "ancestor": "黄帝",
    "states": ["周", "鲁", "卫", ...],
    "shi_list": ["周", "鲁", "孔", ...]
  }
}
```

### person_xingshi.json
```json
{
  "persons": {
    "人名": {
      "xing": "姓",
      "shi": "氏",
      "ming": "名",
      "zi": "字",
      "period": "pre-qin|qin-han",
      "confidence": "exact|high|medium|low",
      "rule": "R1|R2|R3...",
      "evidence": ["原文引用"],
      "source_chapter": ["章节编号"]
    }
  }
}
```

## 使用说明

- **网页展示**：`docs/special/xingshi.html` 使用 ag-Grid 展示交互式表格
- **数据更新**：修改源数据后运行发布脚本同步到 docs
- **JSON API**：可直接访问 JSON 文件作为数据 API

## 相关文档

- [姓氏制度规范](../../../../doc/spec/PLAN_姓氏制度.md)
- [SKILL 07b: 姓氏推理](../../../../skills/SKILL_07b_姓氏推理.md)
- [提示词模板](../../../../kg/entities/scripts/prompt_template_姓氏推理.md)

## 统计信息

**覆盖率进展**：
- 2026-03-16: R1-R6c 完成，2053人（56.6%）
- 2026-03-24: 补充重要人物，2411人（66.4%）
  - 新增583人（含30条楚国君主 + 328条谥号君主记录）

**推理规则分布**（R1-R6c）：
- R1（直接记载）: 34人
- R2（邦国推理）: 306人
- R3（氏族推理）: 1099人
- R4-R5（父系传播）: 30人
- R6（深度反思）: 277人
- R6b（批量规则）: 239人
- R6c（高频补充）: 68人

**置信度分布**：
- exact: 172人
- high: 87人
- medium: 1688人
- low: 106人
