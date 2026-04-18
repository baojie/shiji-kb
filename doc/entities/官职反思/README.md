# 官职反思档案

本目录沉淀《史记》official 实体分类（SKILL 03i）每轮"未分类官职反思"工作成果。完全对照 [`地名反思/`](../地名反思/) 的工作流。

## 工作流

1. `python3 kg/entities/scripts/classify_officials.py` 先分类一遍，输出 `kg/entities/data/official_categories.json`
2. `python3 kg/entities/scripts/dump_blank_officials.py [轮次]` 提取当前未分类条目的上下文到 `第N轮_上下文.md`（无参数则写入 `待反思_上下文.md`）
3. 人工或半自动根据上下文反思分类，把判断与规则候选记入 `第N轮_反思报告.md`
4. 规则归纳后回填到 [`skills/SKILL_03i_官职分类.md`](../../../skills/SKILL_03i_官职分类.md) 并更新 [`classify_officials.py`](../../../kg/entities/scripts/classify_officials.py)
5. 重跑 → 未分类减少 → 下一轮

## 历史轮次

| 轮次 | 上下文文件 | 反思报告 | 起始未分类 → 结束未分类 | 重点 |
|------|-----------|----------|---------------------|------|
| 第一轮 | [第一轮_上下文.md](第一轮_上下文.md) | [第一轮_反思报告.md](第一轮_反思报告.md) | 458 → 260 | 基础白名单 + 后缀启发式规则挖掘 |
| 第二轮 | [第二轮_上下文.md](第二轮_上下文.md) | [第二轮_反思报告.md](第二轮_反思报告.md) | 260 → **0** | 人名误标/简称/古官大规模扩充；全量覆盖 |
| 第三轮 | —— | [第三轮_反思报告.md](第三轮_反思报告.md) | 0 → 0 | 细分误标（身份/谥号）+ 诸侯国官归郡 + 置信度透明度 |
| 第四轮 | —— | [第四轮_反思报告.md](第四轮_反思报告.md) | 0 → 0 | 低置信度条目抽样：规则扩充 + merge 优先级重排（L1/L2.5/L3/L4/L2）|
| 第五轮 | —— | [第五轮_反思报告.md](第五轮_反思报告.md) | 0 → 0 | 多标签审查：修复 L2/L3 误叠，30 → 16 多标签 |
| 第六轮 | [审计报告](第六轮_白名单审计.md) | [第六轮_反思报告.md](第六轮_反思报告.md) | 0 → 0 | 全量 EXPLICIT_* 白名单审计：35 → 11 冲突；新增 audit 脚本 |

## 分类体系

见 [`SKILL_03i_官职分类.md`](../../../skills/SKILL_03i_官职分类.md) §一（16 类 + 未分类）。

## 附属工具

- `classify_officials.py` — L1-L5 分类器
- `extract_hanshu_baiguan.py` — 从《汉书·百官公卿表》提取白名单
- `rebuild_official_html.py` — 重建 `docs/entities/official.html`
- `dump_blank_officials.py` — 导出未分类上下文

## 相关文件

- 分类数据：`kg/entities/data/official_categories.json`
- 置信度数据：`kg/entities/data/official_confidence.json`
- 《百官公卿表》白名单：`kg/entities/data/hanshu_baiguan.json`
