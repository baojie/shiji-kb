# 人名反思档案

本目录沉淀《史记》person 实体分类（SKILL 03j）每轮"未分类人名反思"工作成果。完全对照 [`地名反思/`](../地名反思/) 和 [`官职反思/`](../官职反思/) 的工作流。

## 工作流

1. `python3 kg/entities/scripts/extract_aliases_from_tags.py` 抽取 chapter_md 内联消歧 → 更新 `entity_aliases.json`
2. `python3 kg/entities/scripts/classify_persons.py` 先分类一遍，输出 `kg/entities/data/person_categories.json`
3. `python3 kg/entities/scripts/dump_blank_persons.py [轮次]` 提取当前未分类条目的上下文到 `第N轮_上下文.md`
4. 人工或半自动根据上下文反思分类，把判断与规则候选记入 `第N轮_反思报告.md`
5. 规则归纳后回填到 [`skills/SKILL_03j_人名分类.md`](../../../skills/SKILL_03j_人名分类.md) 并更新 [`classify_persons.py`](../../../kg/entities/scripts/classify_persons.py)
6. 重跑 → 未分类减少 → 下一轮

## 历史轮次

| 轮次 | 上下文文件 | 反思报告 | 起始未分类 → 结束未分类 | 重点 |
|------|-----------|----------|---------------------|------|
| 第一轮 | [第一轮_上下文.md](第一轮_上下文.md) | [第一轮_反思报告.md](第一轮_反思报告.md) | 2642 (53.7%) → 2103 (42.7%) | 冷启动：L1 白名单 + person.ttl 本体 + rulers.json + alias 4 列抽取 |
| 第二轮 | [第二轮_上下文.md](第二轮_上下文.md) | [第二轮_反思报告.md](第二轮_反思报告.md) | 2103 (42.7%) → 1803 (36.6%) | L3 共现模式（为丞相/为将军/即位/崩）+ 白名单批量 + 国名+人名三字规则 + 误标/待拆分专项 |

## 分类体系

见 [`SKILL_03j_人名分类.md`](../../../skills/SKILL_03j_人名分类.md) §一（16 类 + 未分类）。

## 人名独有：alias 子工作流

与地名/官职不同，人名有大量别名（昭王 → 秦/楚/燕/魏/周昭王）。本轮从 tagged.md 的 `〖@X|Y〗` 内联消歧 + disambiguation_map + rulers.json + 鲍捷私文档抽取了 **3322 条** person 别名，新格式为 4 列数组：

```json
{
  "surface": "昭王",
  "type": "person",
  "canonical": "秦昭王",
  "refs": [["005_秦本纪","20.1"], ["071_樗里子甘茂列传","3"]]
}
```

同一 surface 按 canonical 拆分多行（歧义时），refs 记录该消歧适用的具体章节。

**歧义 surface 统计**：585 个 surface 映射到多个 canonical（如"武王"→ 楚武王/商武王/秦武王/周武王）。

## 附属工具

- `classify_persons.py` — L1-L5 分类器（人名版）
- `extract_aliases_from_tags.py` — 合并 4 种来源生成新 alias JSON
- `dump_blank_persons.py` — 导出未分类上下文
- `rebuild_person_html.py` — 重建 `docs/entities/person.html`（TODO）

## 相关文件

- 分类数据：`kg/entities/data/person_categories.json`
- 置信度数据：`kg/entities/data/person_confidence.json`
- 新别名：`kg/entities/data/entity_aliases.json`（4 列结构）
- 旧别名备份：`kg/entities/data/entity_aliases.v1.bak.json`
- 冲突报告：`kg/entities/data/alias_conflicts.json`
- 本体分类源：`kg/taxonomy/person.ttl`（1825 人已分类）
- 君主数据：`kg/relations/rulers.json`
- 谥号索引：`kg/entities/data/shihao_index.json`
- 私文档：`private/to鲍捷 史记里的人名.md`
