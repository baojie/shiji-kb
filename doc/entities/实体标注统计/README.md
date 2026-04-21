# 实体标注统计

本目录收录《史记》知识库的实体标注规模统计，分两条口径：

- **时点快照**（版本报告）：某一日对全库 130 章 `*.tagged.md` 做一次扫描，给出当期总量与类别分布。
- **时间序列**（每周趋势）：按周从 git 历史中抽样 `docs/entities/index.html`，观察长期增长与结构演化。

## 目录文件

| 文件 | 口径 | 生成方式 | 数据源 |
| ---- | ---- | -------- | ------ |
| [实体标注统计报告_v4.1.md](实体标注统计报告_v4.1.md) | 时点快照（2026-04-21，最新） | [`scripts/generate_entity_stats_report.py`](../../../scripts/generate_entity_stats_report.py) | `chapter_md/*.tagged.md` |
| [实体标注统计报告_v4.0.md](实体标注统计报告_v4.0.md) | 时点快照（2026-04-18，**已被 v4.1 取代**） | 一次性手工扫描（v4.1 起已固化脚本） | `chapter_md/*.tagged.md` |
| [实体标注统计报告_v3.0.md](实体标注统计报告_v3.0.md) | 时点快照（2026-03-18，**已被 v4.1 取代**） | 早期一次性手工扫描 | 130 章标注文本 |
| [每周实体数量统计.md](每周实体数量统计.md) | 时间序列（每周趋势 + 里程碑） | 手工从 git 历史采样（见下） | `docs/entities/index.html` 各提交版本 |

## 两条口径的差异（重要）

两套数据**不可直接比较**：

| 口径 | 条目数含义 | 数据源 | 典型数值（2026-04-20/21） |
| ---- | ---------- | ------ | --- |
| **tagged.md 原始扫描** | 按消歧规范名（`|` 左侧）去重，**不做别名合并** | `chapter_md/*.tagged.md` | 人名 5,347 · 合计 15,141 |
| **entity_index.json（别名合并）** | 合并同一实体的多个别名（如沛公/汉王/高祖 → 刘邦） | `kg/entities/data/entity_index.json` | 人名 4,559 · 合计 约 12k |
| **docs/entities/index.html** | 别名合并后的条目 + 编年/事件聚合条目 | 渲染自 entity_index.json | 合计 15,071 |

**出现数**两条口径基本一致（正则命中次数），但 **条目数** 差异显著。版本报告用"原始扫描"口径；周趋势用"index.html"口径。

## 生成方法

### 一、时点快照（版本报告）

脚本：[`scripts/generate_entity_stats_report.py`](../../../scripts/generate_entity_stats_report.py)

```bash
# 生成最新版本报告（按日期命名）
python scripts/generate_entity_stats_report.py

# 指定版本号（写入 doc/entities/实体标注统计/实体标注统计报告_v4.2.md）
python scripts/generate_entity_stats_report.py --version v4.2

# 只打印到 stdout
python scripts/generate_entity_stats_report.py --stdout

# 同时导出原始数据 JSON（便于跨版本 diff）
python scripts/generate_entity_stats_report.py --version v4.2 --json /tmp/stats-v4.2.json
```

脚本输出：

- 一、名词实体（18 类）· 条目数 + 出现数 + 示例
- 二、动词实体（4 类）· 条目数 + 出现数 + 示例
- 三、总体统计（合计表 + 平均密度）
- 四、Top 10（按出现数）
- 五、版本更新（占位，**由人工填写与上一版的对比与反思归纳**）

发版流程：

1. 跑脚本生成新版骨架（一~四节）
2. 人工对照上一版本，补写"五、版本更新"
3. 将上一版顶部改为"已被 vX.Y 取代"
4. 同步更新 [每周实体数量统计.md](每周实体数量统计.md) 的"tagged.md 直接扫描"小节

### 二、字级覆盖率（辅助报告）

脚本：[`scripts/compute_annotation_coverage.py`](../../../scripts/compute_annotation_coverage.py)

```bash
python scripts/compute_annotation_coverage.py
# → doc/analysis/汉字标注覆盖率统计报告_{YYYYMMDD}.md
```

与本目录报告互补：给出**汉字级**覆盖率（已标注汉字 / 总汉字），以及按类型的汉字数占比。
非 distinct 条目统计口径，不适合替代版本报告。

### 三、HTML 索引（别名合并口径）

脚本：[`kg/entities/scripts/build_entity_index.py`](../../../kg/entities/scripts/build_entity_index.py)

```bash
python kg/entities/scripts/build_entity_index.py
# → kg/entities/data/entity_index.json
# → docs/entities/*.html（人名/地名/官职 等 20+ 类型页面 + index.html）
```

加载 `entity_aliases.json` 做别名合并，生成 JSON + 可浏览的 HTML 索引页。
**周趋势**表中的数据即来自各历史版本的 `docs/entities/index.html`。

### 四、时间序列（每周趋势）

目前为手工维护。采样逻辑：

```bash
# 1. 获取 index.html 所有提交
git log --format="%H %ai" -- docs/entities/index.html

# 2. 按自然周（周一~周日），取每周最后一次提交
# 3. 用 git show <commit>:docs/entities/index.html 读取当时的 HTML
# 4. 抽取每个类型卡片的条目数与出现数（正则匹配 `<a class="entity-type-card">...</a>`）
# 5. 汇总入表，关键提交（符号迁移、类型新增、全量重建）作为里程碑单独记录
```

> 自动化待办：见 [`skills/references/SKILL_08b1_标注完成情况统计.md`](../../../skills/references/SKILL_08b1_标注完成情况统计.md)。
> 已废弃/重命名类型（如"制度"→"名物"、"朝代"→"邦国+编年"）另表说明。

## 更新节奏

- **版本报告**：每轮反思或重大批量修正后出一版（v3.0 → v4.0 → v4.1 间隔约 1 个月）。
- **每周趋势**：每周日/周一追加一行，同时更新里程碑表。

## 相关入口

- 实体索引主页：[docs/entities/index.html](../../../docs/entities/index.html)
- 标注设计文档：[kg/entities/data/verb_taxonomy.md](../../../kg/entities/data/verb_taxonomy.md)
- 规律库：[skills/references/SKILL_03c1-rules.md](../../../skills/references/SKILL_03c1-rules.md)
- 标注完成情况统计（方法论）：[skills/references/SKILL_08b1_标注完成情况统计.md](../../../skills/references/SKILL_08b1_标注完成情况统计.md)
