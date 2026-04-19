---
name: skill-06e
description: 分类树总结与维护工作流。当需要更新已有分类树（如 person.ttl / biology.ttl）、分析缺口、验证自洽、规范化输出（MD 分类树 + 统计 + 缺口报告）时使用。核心思路：TTL 是权威源，所有 MD 派生物由脚本重算；每次扩展先跑缺口分析，再把高频缺口挑出来分类归入 TTL，最后重生分类树 MD。与 SKILL_06a（从零构本体）不同，06e 聚焦"已有本体的增量维护"。
---

# SKILL 06e: 分类树总结 — 增量维护与一致性验证

> SKILL_06a 讲的是"从实体实例到 RDF 本体"的零→一过程。
> 本 SKILL 补的是另一端：本体建立之后的**增量维护**——如何在新标注到来后，以最小改动更新分类树，保证 TTL / MD / 索引 三方一致。

---

## 一、何时使用

以下任一情况触发本流程：

- 新一轮反思标注完成，`entity_index.json` 中某类实体数量大幅增长；
- `entity_aliases.json` 新增了大量消歧/别名（尤其是 4 列结构新版本）；
- 分类树 MD 与 TTL 不一致（手工编辑过 MD、或 TTL 更新后未重生）；
- 需要对外出一个"当前分类树覆盖率"的总结（如文档、博客、演示）；
- 新增实体类型的子分类（如 place 下增加"陵墓"、official 下增加"外邦职"），
  需要把新类合入已有树。

**不适用**：新建一个全新实体类型的本体——那属于 SKILL_06a 的范围。

---

## 二、核心原则

1. **TTL 是唯一权威源**。所有 MD、HTML、统计都由 TTL 派生。禁止手工编辑 MD；改动必须落到 TTL。
2. **保持基础分类稳定**。增量更新只做"添加实例 / 添加叶子子类"，不随意重组顶层分类——顶层变动须走 SKILL_06a 的反思流程。
3. **先分析缺口，再动手**。不把 4000 个人名全部一锅端重分类；用脚本分桶后，按出现次数从高到低增量处理。
4. **可重生**。任意一次全量重跑应产生与当前一致的结果，确保分类决策都固化在数据/代码中。
5. **别名归并优先于新分类**。很多"缺口"其实是已归并的 canonical 的短名/别名，不需要新类条目。

---

## 三、工作流（5 步）

### Step 1. 缺口分析

**目标**：找出"索引里有、但分类树里没有"的实体。

**脚本**：`kg/taxonomy/scripts/{type}_gap_report.py`（人物版已实现）。

**输出**：`kg/taxonomy/{type}_gap_report.md`，分桶列出缺口。

```bash
python kg/taxonomy/scripts/person_gap_report.py
# 控制台输出：
#   [索引] person: 4921
#   [分类树] person.ttl 实例: 1822
#   [缺口] 在索引但未入树: 3179
#     其中经别名可归: 1005
#     真实未分类: 2174
```

**分桶优先级**：

| 出现次数 | 处理方式 |
|---------|---------|
| ≥50 | 必须入树，通常是遗漏的高频人物或应排除的通称 |
| 20-49 | 必须入树 |
| 10-19 | 应入树 |
| 5-9 | 建议入树（需要单独看上下文） |
| 2-4 | 择优入树（很多是别名/误标） |
| 1 | 留待自动脚本批量归类；手工处理成本过高 |

### Step 2. 别名归并去重

很多缺口不是"新人物"，而是已有人物的短称或异写。在 `entity_aliases.json`（4 列结构）里查找：

```python
# 规则：如果 surface 已有 canonical，且 canonical 在 TTL 中存在，
# 则该 surface 不是"新人物"，只需确保渲染层能把短名链到 canonical 实例。
```

本步把缺口清单分成两组：
- **别名可归**（无需新分类，例如"昭王"→"秦昭王"已在 TTL）；
- **真实未分类**（需要走 Step 3）。

### Step 3. 增量归类

**对 Step 2 筛出的"真实未分类"条目，按出现次数从高到低逐条审视**：

| 判据 | 归类信号 | 参考 SKILL |
|-----|---------|-----------|
| 是否在 `rulers.json` 中？ | 直接进 王室/帝王/诸侯/外邦 | SKILL_03b §10 |
| 是否在 `shihao_index.json` 中？ | 谥号命中 → 诸侯君主 | SKILL_03b |
| 主出现章节是否专题列传？ | 刺客/酷吏/佞幸/游侠/货殖 等直接归类 | SKILL_03j §4.1 |
| 名称是否带身份后缀？ | 单于/贤王/夫人/公子/太子 → 对应类 | SKILL_03j §7 |
| 是否在白名单中？ | L1 白名单匹配 | SKILL_03j §3 |

**多信号叠加原则**：至少两个独立信号才可信。单信号分类（如只看"主章是本纪")历史准确率仅 12%，见 SKILL_06a §5 反思记录。

**操作方式**：把归类结果追加到 TTL，而**不**修改 MD。典型 TTL 片段：

```turtle
per:i_jinbi a per:晋国臣子 ;
    rdfs:label "晋鄙"@zh ;
    :count 22 .
```

### Step 4. TTL 自洽校验

每次编辑 TTL 后，必须通过以下三个检查：

**（4.1）语法校验**
```python
from rdflib import Graph
g = Graph(); g.parse('kg/taxonomy/person.ttl', format='turtle')
print(f'{len(g)} triples')   # 解析不报错即通过
```

**（4.2）实例去重 / 本级清理**
对每个父类，检查是否有实例被遗忘在"本级"（未归入任何子类）。SKILL_06a §5 的十条经验其中两条就是：
- 拆分后必须清理 `(本级)` 残留
- 子类实例需逐一审查，防止"国王混入臣子 / 汉人混入外邦"

**（4.3）TTL 与索引的一致性**
重跑 `person_gap_report.py` 的 "TTL 冗余" 项：
```
[疑似] TTL 中已无索引对应: N
```
N 应尽可能小（当前 80，多为早期规范名合并的残留）。>100 时须清理。

### Step 5. 重生 MD 分类树

```bash
python kg/taxonomy/scripts/build_taxonomy.py kg/taxonomy/person.ttl
# → 输出 kg/taxonomy/person_taxonomy.md（1481 行）
```

对应的 HTML 渲染（如果有）同步重跑。

---

## 四、验证清单（每次维护后必须通过）

在 commit 之前，请逐项确认：

- [ ] `entity_index.json` 中该类实体的最新计数与 TTL 基本吻合（允许一定比例的低频缺口）
- [ ] `{type}_gap_report.md` 已重生，缺口下降（≥5 频次桶应接近 0）
- [ ] `{type}.ttl` 用 `rdflib` 解析无错
- [ ] `{type}_taxonomy.md` 由 `build_taxonomy.py` 重生（不手编）
- [ ] TTL 冗余（索引中不存在的实例）< 100
- [ ] 新增的叶子子类在 `build_person_taxonomy.py` 的 `SUB_ZH` 映射中有中文标签
- [ ] 别名归并的短称在 `entity_aliases.json` 中 canonical 指向 TTL 实例
- [ ] `git diff kg/taxonomy/{type}.ttl` 只含新增三元组，没有无意义重排

---

## 五、分类树总结输出模板

当需要把分类树做成对外总结（博客、文档、报告）时，按以下结构输出：

```markdown
# {类型}分类树总结（{YYYY-MM-DD}）

## 规模
- 顶层类：{N} 个
- 全部类：{M} 个
- 实例：{K} 条
- 三元组：{T} 条

## 顶层分类（按实例数）
| 类 | 实例 | 说明 |
|----|-----:|------|
| 王室 | 289 | 帝王/诸侯/后妃/宗室 |
| 臣 | 800+ | 各时代各国臣子 |
| … |

## 覆盖率
- 索引总数：{I}
- 已入树：{T}（{T/I:.1%}）
- 经别名归并：{A}
- 真实缺口：{G}（按出现次数分桶：{...}）

## 本轮新增
| 类 | 新增实例 | 关键人物 |
|----|--------:|---------|
| 晋国臣子 | 5 | 晋鄙 (22), 栾氏 (…) |
| … |

## 已知问题
- 冗余：TTL 中 {N} 个实例在最新索引中找不到，待清理
- 混类：{…}
```

这个模板同样适用于地名、官职等其他实体类型（SKILL_03h / SKILL_03i）。

---

## 六、与其他 SKILL 的分工

| 场景 | 使用的 SKILL |
|------|------------|
| 新建一个实体类型的本体 | **06a**（实体到本体，零→一） |
| 已有本体的增量维护 + 总结 | **06e**（本 SKILL） |
| 属性/关系/约束定义 | 06b |
| 规则与推理 | 06c / 06d |
| 人名短称→全名消歧 | 03b |
| 人名身份二级分类规则 | 03j |
| 地名地段二级分类规则 | 03h |
| 官职职类二级分类规则 | 03i |

**关系**：03h/03i/03j 提供"分类规则"（L1-L5 层级决策）；06a 提供"从零构本体"的管线；06e 提供"已有本体的维护"流程。三者衔接如下：

```
03j 产出 → classify_persons.py → person_categories.json
                                      ↓
06a/06e 用来驱动 → 追加到 person.ttl
                                      ↓
                  build_taxonomy.py → person_taxonomy.md
```

---

## 七、工具清单

| 脚本 | 用途 |
|------|------|
| `kg/taxonomy/scripts/build_taxonomy.py` | TTL → Markdown 分类树（通用） |
| `kg/taxonomy/scripts/person_gap_report.py` | 人物缺口分析与报告 |
| `kg/entities/scripts/classify_persons.py` | 人物身份分类（L1-L5 决策），来自 SKILL_03j |
| `kg/entities/scripts/classify_places.py` | 地名地段分类，来自 SKILL_03h |
| `kg/entities/scripts/classify_officials.py` | 官职职类分类，来自 SKILL_03i |
| `kg/entities/scripts/extract_aliases_from_tags.py` | 别名抽取（tagged.md 的内联消歧 + disambiguation_map + rulers + 私文档） |

**待建**（按优先级）：
- `place_gap_report.py` / `official_gap_report.py` — 模仿 `person_gap_report.py`
- `rebuild_ttl_from_categories.py` — 从 `{type}_categories.json` 追加新实例到 TTL
- `validate_taxonomy.py` — 一键跑完 Step 4 的所有校验

---

## 八、典型场景速查

**场景 A：新一轮标注完成，人物新增了 ~3000 条**
1. 跑 `person_gap_report.py` → 查看分桶
2. 阅读高频桶（≥10）逐条判断：是新人物还是已有 canonical 的别名
3. 别名归并的：更新 `entity_aliases.json`
4. 真实新人物：按 SKILL_03j 的 L1-L5 决策链归类，追加到 `person.ttl`
5. 重跑 `build_taxonomy.py` 生成新 MD
6. 按 §四 验证清单逐项检查
7. 写一份总结（§五模板）作为反思文档

**场景 B：MD 分类树与 TTL 不一致（有人手工改过 MD）**
1. **以 TTL 为准**：直接重跑 `build_taxonomy.py` 覆盖 MD
2. 如果手工改动有价值：先提取改动，改到 TTL 里，再重跑
3. 永远不要反向"用 MD 修正 TTL"

**场景 C：TTL 中有实例，但新索引中找不到**
1. 多为规范名合并后的旧实例（如"厉王胡"→"周厉王"）
2. 检查 `entity_aliases.json` 确认是否是合并关系
3. 如确认过时，从 TTL 中删除；如还有价值，改为旧名列入别名
4. 保留小部分（<100）允许，作为历史痕迹

---

## 九、成功标准

一次合格的分类树维护，应满足：

- **缺口收敛**：高频桶（≥10 次）缺口 ≤ 5%
- **TTL 一致**：冗余实例 < 100，语法无错
- **MD 可重生**：`build_taxonomy.py` 重跑后，`git diff` 只有数据层面的差异
- **文档对外**：有一份符合 §五模板的总结报告
- **规则留痕**：每次新增归类背后的判据（白名单、章节、后缀）在对应 SKILL 的"规则累积日志"中有记录

---

*本 SKILL 提炼自 2026-04-19 人物分类树缺口分析实践：人物索引 4921 → 分类树 1822，缺口 3179（经别名归并后真实未分类 2174；按出现次数分桶后 ≥5 频次仅需新增 66 条）。*
