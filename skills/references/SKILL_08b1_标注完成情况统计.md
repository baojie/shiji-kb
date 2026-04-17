---
name: skill-08b1
title: 标注完成情况统计
description: 量化《史记》标注工作进度与覆盖度。汇总字级、实体级、章节级、专题级四类统计视角与对应脚本，支持周/月度进度追踪。
---

# SKILL 08b1: 标注完成情况统计

> **核心理念**：用稳定、可复跑的脚本持续量化"标注完成了多少"，替代人工估算。  
> **上级**：[SKILL_08b 知识覆盖度评估](../SKILL_08b_知识覆盖度评估.md)

---

## 一、快速开始

### 何时使用

- 月度/季度进度汇报，需要给出"当前覆盖率"
- 某批标注任务完成后，回答"标注率涨了多少"
- 怀疑某章/某类实体覆盖不足，需要定位
- 专题索引（成语、战争、避讳等）更新后，需要重算覆盖章数
- 想要回答"这章还有什么该标但没标"（→ §3.5 候选发现）

### 核心步骤（三条命令拿全量报告）

```bash
# 1. 字级覆盖率（总字数 / 已标注字数 / 未标注字数）
python scripts/compute_annotation_coverage.py

# 2. 实体索引（18类 + 4动词，条目数、出现数、每类分布）
python kg/entities/scripts/build_entity_index.py

# 3. 文本完整性校验（保证标注未破坏原文）
python scripts/lint_text_integrity.py
```

三个命令全通过，即代表数据处于可统计状态。

### 成功标准

- `compute_annotation_coverage.py` 跑完无错，输出 `doc/analysis/汉字标注覆盖率统计报告_{YYYYMMDD}.md`
- 字级标注率在 **35%–45%** 合理区间（低于 35% 说明有重大回归，高于 45% 需复查去重逻辑）
- `lint_text_integrity.py` 输出 `✓ 全部通过`（否则有原文字符被改动，统计不可信）

---

## 二、四个统计视角

### 2.1 字级覆盖率（总体健康度）

| 维度 | 脚本 | 输出 | 频率 |
|------|------|------|------|
| 已标注字数 / 总字数 | `scripts/compute_annotation_coverage.py` | `doc/analysis/汉字标注覆盖率统计报告_{YYYYMMDD}.md` | 月度 |

**回答的问题**：整本书被标注了多少字？虚词助词有多少是故意不标的？

**典型数字**（2026-04-18）：
- 总字数 576,900 · 已标注 219,259（**38.01%**）· 未标注 357,641（61.99%）
- 前 5 类占已标注 70%：人名 32.1%、官职 11.4%、时间 9.9%、地名 9.0%、邦国 8.1%

**历史趋势**：2026-03-19 为 35.40%，30 天内 +2.6%。

### 2.2 实体级统计（条目与出现）

| 维度 | 脚本 | 输出 | 频率 |
|------|------|------|------|
| 去重后条目数 · 总出现次数 · 各类分布 | `kg/entities/scripts/build_entity_index.py` | `kg/entities/data/entity_index.json` + `docs/entities/*.html` | 每次实体标注改动后 |
| 周度快照（趋势图） | `data/entity_stats_weekly.md`（手动维护） | 同名 md | 每周 |

**回答的问题**：去重后有多少"不同的"人名、地名等？每类平均出现多少次？

**典型数字**（2026-04-17）：
- 条目 **15,674** · 出现 **130,177** 次 · 平均每条目出现 8.3 次
- 周增：+546 条目 / +3,601 次出现（主要来自第四轮反思）

### 2.3 章节级分布（定位短板）

字级脚本同时输出**覆盖率 TOP 10 / BOTTOM 10 章**，可直接拿来制定下一轮重点标注计划。

**规律**：
- TOP（55%+）：表类章节、简洁世家列传
- BOTTOM（15%–25%）：乐书、历书、天官书等「书」体；龟策、日者、扁鹊仓公等「专题列传」；司马相如辞赋
- 「书」体覆盖率低是预期的（议论性、抽象性强），**不应强行追求 40%**

### 2.4 专题级覆盖（专项索引）

每个专题配有独立扫描脚本，输出"N 条实例 / 覆盖 M 章"：

| 专题 | 脚本 | 报告 | 统计口径 |
|------|------|------|----------|
| 成语典故 | `scripts/extract_chengyu.py` · `scripts/render_chengyu_html.py` | `data/chengyu.md` · `data/chengyu.json` | 条数·覆盖章·定位率 |
| 战争事件 | `scripts/export_wars_special.py` · `scripts/render_wars_html.py` | `data/wars.md` · `data/wars.json` | 场数·覆盖章·多源融合 |
| 太史公曰 | `scripts/extract_taishigongyue.py` · `scripts/render_taishigongyue_html.py` | `data/taishigongyue.md` · `data/taishigongyue.json` | 篇数·覆盖率 |
| 韵文集 | `scripts/extract_yunwen.py` · `scripts/render_yunwen_html.py` | `data/yunwen.md` · `data/yunwen.json` | 篇数·分类分布 |
| 散文集 | `scripts/extract_sanwen.py` · `scripts/build_sanwen_manifest.py` · `scripts/render_sanwen_html.py` | `data/sanwen.md` · `data/sanwen.json` | 篇数·文体分布 |
| 谥号索引 | `kg/entities/scripts/build_shihao_index.py` | `kg/entities/data/shihao_index.json` · `docs/special/shihao.html` | 种数·人数 |
| 避讳改字 | `scripts/scan_taboo_characters.py` · `scripts/render_bihui_html.py` | `data/taboo_characters.md` · `data/taboo_characters.json` | 规则数·实例数·覆盖章 |

> 注：`docs/special/jun_titles.html` 君号索引专题尚无专门的统计脚本，计数靠人工维护，暂不纳入本 Skill。

**汇总视图**：[docs/special/special_index.html](../../docs/special/special_index.html) 列出 11 项完成专题的计数。

---

## 三、工具与脚本

### 3.1 字级统计（本节核心）

**[scripts/compute_annotation_coverage.py](../../scripts/compute_annotation_coverage.py)** — 唯一真相源

- 复用 `scripts/semantic_tags.py` 的 `strip_markup` 剥离 Markdown 结构
- 正则覆盖完整 **18 名词 + 4 动词** 类
- 输出按类型、按章节的双视图
- 自带"与上次对比"段，月度进度一目了然

**历史脚本**：`scripts/analyze_tagged.py` 已于 2026-04-18 标记 DEPRECATED（路径硬编码失效 + 正则漏 `◆邦国` 与动词类），直接运行会 fail-fast 并指向新脚本。

### 3.2 实体级统计

- **[kg/entities/scripts/build_entity_index.py](../../kg/entities/scripts/build_entity_index.py)** — 扫描所有 tagged.md，按类型聚合，合并别名（`entity_aliases.json`），生成 JSON + 各类 HTML 索引页
- 产出：`kg/entities/data/entity_index.json` · `docs/entities/person.html` 等 20+ 类型页
- 周度汇总：`data/entity_stats_weekly.md`（人工从 git 历史采样）

### 3.3 完整性校验（前置条件）

- **[scripts/lint_text_integrity.py](../../scripts/lint_text_integrity.py)** — 确保 tagged.md 去除标注后与原始 txt 逐字相同
- **必须在字级统计之前运行**，否则如有半角引号污染、嵌套标注等异常，字数统计会偏移

```bash
python scripts/lint_text_integrity.py              # 基本校验
python scripts/lint_text_integrity.py --check-nested  # 附加嵌套标注检测
```

### 3.4 专题扫描

见 §2.4 表格，每个专题各自幂等重跑。

### 3.5 未标注候选实体发现（回答"还有什么漏标"）

三个互补的候选发现脚本，从不同角度暴露漏标：

| 脚本 | 对象 | 输出 | 典型用法 |
|------|------|------|----------|
| [`scripts/scan_untagged_aliases.py`](../../scripts/scan_untagged_aliases.py) | 已知实体的漏标（`entity_index.json` 已有的正名/别名在正文中未被标） | `doc/analysis/patch/NNN_别名补标.tsv` | `python scripts/scan_untagged_aliases.py --all --types person place` |
| [`scripts/scan_sanwen_candidates.py`](../../scripts/scan_sanwen_candidates.py) | 散文候选（按触发短语与长度识别未收入 `sanwen.json` 的书信/诏令/策论） | `labs/planning/sanwen_candidates.{tsv,md}` | `python scripts/scan_sanwen_candidates.py` |
| [`scripts/find_candidate_entities.py`](../../scripts/find_candidate_entities.py) | 未知候选（未标文本中按 n-gram 频次 + 可选词表过滤发现新候选） | `doc/analysis/candidates/{chapter}_candidates.tsv` + `summary.md` | `python scripts/find_candidate_entities.py --all --filter mingwu --min-freq 3` |

**`find_candidate_entities.py` 的关键点**：
- 先剥离所有已标片段（连内容一并移除，用换行占位切断跨标注 n-gram），所以只扫描真正的未标文本
- 内置 `MINGWU_KEYWORDS` 词表（律历/五行/五色/节气/礼仪/度量衡等约 80 词），适合名物漏标排查；也可 `--filter-file` 自定义词表
- 按章节单独输出 TSV，附原文上下文，便于人工逐条审核决定是否要标注

**与其他候选发现脚本的分工**：
- [`scripts/pos_analysis.py`](../../scripts/pos_analysis.py) — 字级词性分析（虚词/动词/形容词/数词/候选实体五分类 + 夹心型复合实体 lint）；输出 `doc/analysis/pos/*.json` 与 `doc/analysis/pos_summary.md`。适合做"候选实体占比"的宏观分析与字级审查。
- [`scripts/analyze_tagged.py`](../../scripts/analyze_tagged.py) — 老牌多功能脚本，字级覆盖率部分已被 `compute_annotation_coverage.py` 取代；独有功能是**基于词表的模式匹配**（礼仪/刑法/思想/度量衡等典型词表扫描）与**字频/n-gram 频次**。
- **历史报告**：[doc/analysis/未标注实体分析报告.md](../../doc/analysis/未标注实体分析报告.md)（2026-03 的 44 万未标注字分析）、[doc/analysis/pos_summary.md](../../doc/analysis/pos_summary.md)（字级 POS 统计），由上述两个脚本生成，仍可重跑刷新。

---

## 四、检查清单

### 执行前

- [ ] Git 工作区干净或已 stash（避免未提交改动影响结果）
- [ ] 已跑 `lint_text_integrity.py` 且无错
- [ ] 若刚合并了新批次标注，先让 `build_entity_index.py` 跑一遍确保别名表同步

### 执行中

- [ ] `compute_annotation_coverage.py` 输出无 `[warn]` / `[error]`
- [ ] 报告中总字数与上期相差 `< 0.5%`（大幅波动 → 可能有文件丢失或结构被破坏）
- [ ] 覆盖率变化与当期工作量方向一致（刚做完人名批量标注，人名类字数应上升）

### 执行后

- [ ] 新报告放入 `doc/analysis/` 并 commit
- [ ] 同步更新 `data/entity_stats_weekly.md` 的本周一行
- [ ] 若触达里程碑（如首次突破 40%），更新 `README.md` 顶部统计块

---

## 五、常见陷阱

| 陷阱 | 症状 | 排查 |
|------|------|------|
| 半角引号污染 | 总字数骤增 200+ | `grep -n '\"' chapter_md/*.tagged.md`（参见 CLAUDE.md §2.4 规则） |
| 嵌套标注 | 某类字数偏高、条目不合理 | `python scripts/lint_text_integrity.py --check-nested` |
| 动词 `⟦⟧` 被误当文本符号 | 动词类 0 条 | 确认 `compute_annotation_coverage.py` 的 `VERB_TYPES` 包含 `◈◉○◇` |
| 统计包含 backup 文件 | 章数 > 130 | 扫描时排除 `*backup*` 文件（新脚本已排除） |
| 旧路径硬编码 | `FileNotFoundError` | 禁用 `analyze_tagged.py`，改用 `compute_annotation_coverage.py` |

---

## 六、产出物

| 文件 | 内容 | 更新者 |
|------|------|--------|
| `doc/analysis/汉字标注覆盖率统计报告_{YYYYMMDD}.md` | 总体/类型/章节三视图 | 脚本自动 |
| `kg/entities/data/entity_index.json` | 18+4 类实体条目表 | 脚本自动 |
| `data/entity_stats_weekly.md` | 周度趋势 | 手工维护 |
| `data/{chengyu,wars,...}.md` | 专题覆盖报告 | 各专题脚本 |
| `docs/special/special_index.html` | 专题汇总入口 | 手工维护 |

---

## 七、相关技能

| 关联 | 说明 |
|------|------|
| [SKILL_08b 知识覆盖度评估](../SKILL_08b_知识覆盖度评估.md) | 父 Skill，本文的统计产出是其第二节「实体/关系/属性覆盖度」的数据基础 |
| [SKILL_02f 文本统计](../SKILL_02f_文本统计.md) | 同级，侧重「五体分布、词频、句长」等文本定量分析，与本文互补 |
| [SKILL_01a 标注完整性维护](../SKILL_01a_标注完整性维护.md) | 上游，其完整性校验是本文统计的前置条件 |
| [SKILL_10b 每日工作日志维护](../SKILL_10b_每日工作日志维护.md) | 下游，日志中的「关键数字」可直接复用本文产出 |

---

**创建日期**: 2026-04-18  
**最后更新**: 2026-04-18  
**版本**: v1.0
