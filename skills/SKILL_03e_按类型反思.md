---
name: skill-03e
description: 按类型反思的总入口，分两个子 skill：03e1（跨类型迁移）用于源头标错了类的整体迁移（如 〖^制度〗→〖:礼仪〗）；03e2（按类型反思纠错）用于对一级实体类型做多轮反思，系统性发现并修正误标、分类错归、白名单冲突。先读本文判断场景，再跳转到对应子 skill。
---


# SKILL 03e: 按类型反思（总入口）

> 本 skill 是路由。具体工作流在两个子 skill：
> - [SKILL_03e1 跨类型迁移](references/SKILL_03e1_跨类型迁移.md)
> - [SKILL_03e2 按类型反思纠错](references/SKILL_03e2_按类型反思纠错.md)

---

## 一、两种场景选哪一个？

| 维度 | 03e1 跨类型迁移 | 03e2 按类型反思纠错 |
|------|--------------|----------------|
| 问题形式 | 某类实体整体搬到另一类 | 在一个类型内部发现并修正误标/错归 |
| 典型例 | `〖^制度〗→〖:礼仪〗`、`〖=地名〗→〖◆邦国〗` | 官职 "太后" 被误标 → 发现 + 归入 cat-identity-mis + 源头改回 identity |
| 改动对象 | `chapter_md/*.tagged.md` 中的**源头标记** | 主要是 `kg/entities/data/TYPE_categories.json`（规则/白名单/Guard），部分动源头 |
| 主方法 | 三阶段法（always/context/new_candidates） | 多轮反思 R1-R7 + L1-L5 分层诊断 |
| 主脚本 | `scripts/migrate_*.py`、`scripts/tag_new_entity_types.py` | `kg/entities/scripts/classify_*.py` + `dump_blank` + `audit_*` |
| 反思轮数 | 通常 1-2 轮 | 3-7 轮 |
| 核心产出 | 批量迁移的 always_list + TSV 上下文审查表 | 误标发现清单 + 规则调整 + 误标子类 |
| 历史 | v2.1-v2.5 主模式（14 轮 ~15,400 处） | v2.6+ 主模式（2026-04 三条工作流） |

### 场景判断三问

1. **问题是类型错还是分类错？**
   - 源头的类型标记本身错了（如"天子"被标为官职而非身份）→ 整批 **03e1**
   - 类型标对但内部分类错归（如"长乐卫尉"归列卿应归九卿）→ **03e2**

2. **是否两者都需要？**
   - 是 → **先 03e1（清源头）再 03e2（反思纠错）**。避免在错误源头上反思
   - 03e2 在诊断 A（源头错）时会反过来触发 03e1 迁移

3. **有没有具体待办？**
   - 查 [SKILL_03e1 §六 TODO](references/SKILL_03e1_跨类型迁移.md#六已知存量错误-todo) 是否有仍 pending 的迁移
   - 查 [SKILL_03e2 §十二 候选](references/SKILL_03e2_按类型反思纠错.md#十二下一个待反思的实体候选) 是否有下一个待反思的实体

---

## 二、当前活跃工作

### 03e1 跨类型迁移 — 仍 pending 的 TODO

| 系统性错误 | 估计规模 | 优先级 |
|-----------|---------|-------|
| `〖^制度〗→〖:礼仪〗`（礼/宗庙/社稷/封禅/郊 等） | ~500 处 | 中 |
| `〖=地名〗→〖◆邦国〗` 残余 | ~200 处 | 低 |

详见 [SKILL_03e1 §六](references/SKILL_03e1_跨类型迁移.md#六已知存量错误-todo)。

### 03e2 按类型反思纠错 — 已完成/进行中的工作流

| 实体 | Skill | 主要误标类型 |
|-----|------|----------|
| 地名 place | [SKILL_03h](SKILL_03h_地名地段分类.md) | 诊断 A：29 条误标剔除 + 20 处复合拆分；诊断 B：R6 发现 9 条 cohort |
| 官职 official | [SKILL_03i](SKILL_03i_官职分类.md) | 诊断 C：新增 5 个 mis 子类（person/identity/shihao/split/mis） |
| 人名 person | [SKILL_03j](SKILL_03j_人名分类.md) + [SKILL_06e](SKILL_06e_概念分类树构建.md) | 诊断 B：白名单扩 500+ 条 + 姓氏前缀规则（姬/熊/姒/嬴）+ L4.5 章节兜底 + alias-only 补全，未分类 2642→**0**（2026-04-22 清零）|
| 邦国 feudal-state | [SKILL_03k](SKILL_03k_邦国分类.md) | 11 类体系（上古/朝代/周代诸侯/秦末/汉王国/汉侯国/外邦/合称/3 条 mis）；`朝代 cat-dynasty` 与 `合称 cat-collective` 为合法子类；**侯国也算邦国** → `cat-han-marquis`；真·误标仅 tribe-mis/place-mis/split 三条。**首轮 2026-04-22 落地：204 条 100% 分类，12 条误标候选反向触发 03e1** |

### 03e2 按类型反思纠错 — 候选下一个

典籍 book / 器物 artifact / 时间 time / 思想 concept / 修辞 rhetoric。详见 [SKILL_03e2 §十二](references/SKILL_03e2_按类型反思纠错.md#十二下一个待反思的实体候选)。

---

## 三、原则（两场景共用）

1. **新增实体类型前先做 03e1 存量清理** —— v2.5 数量类型新增时，存量迁移 1,894 处远多于新标 690 处
2. **先 03e1 清源头，再 03e2 做反思纠错** —— 不在错误源头上反思
3. **03e2 发现诊断 A 反向触发 03e1** —— 反思中浮出的源头误标批量交给 03e1
4. **每轮改动后必跑 lint** —— `python scripts/lint_text_integrity.py` + `python scripts/lint_markdown.py`
5. **两者完成后重建索引** —— `python kg/entities/build_entity_index.py`，然后更新 HTML

---

## 四、组合策略

| 阶段 | 推荐工作流 |
|-----|----------|
| 发现系统性误标 | **SKILL_03e1** |
| 新增实体类型初标 | [SKILL_03a](SKILL_03a_实体标注.md) → [SKILL_03c](SKILL_03c_按章反思.md) |
| 一级类型稳定后 | **SKILL_03e2**（反思纠错主线）|
| 多类交叉清理 | SKILL_03e1 → [SKILL_03f](SKILL_03f_实体边界错误综合反思.md) → SKILL_03e2 |
| 发布前质检 | SKILL_03c 抽检 + SKILL_03e2 R7 白名单审计 |

---

## 五、详细方法论

- 跨类型迁移：[SKILL_03e1 跨类型迁移](references/SKILL_03e1_跨类型迁移.md)
- 按类型反思纠错：[SKILL_03e2 按类型反思纠错](references/SKILL_03e2_按类型反思纠错.md)
- 03e2 的详细方法论：[`doc/entities/实体细分分类与纠错方法论.md`](../doc/entities/实体细分分类与纠错方法论.md)
