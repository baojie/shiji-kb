---
name: skill-w14
title: 洞察发现（实体关联假设与问题生成）
description: 主动提出实体间的关联假设与开放性问题（如"刘肥与曹参可能有什么关系？"），检索史记原文和 kg 寻找证据，将有价值的洞察写入 insight_queue.md，驱动新页面创建或现有页面增补。W14 是知识库的"好奇心"——不等待任务分配，主动发现尚未被表达的知识连接。
---

# SKILL W14: 洞察发现

> W1 找已知的候选，W14 提出还没人问过的问题。知识图谱的深度取决于被提出的问题的质量。

---

## 一、洞察类型

| 类型 | 英文标记 | 问题模式 | 示例 |
|---|---|---|---|
| 共事关系 | `COLLAB` | A 与 B 是否在同一政治场域共事？ | 刘肥与曹参都在齐国，关系如何？ |
| 对抗关系 | `CONFLICT` | A 与 B 有无直接冲突或竞争？ | 张仪与苏秦真的势不两立？ |
| 师承/亲属 | `LINEAGE` | A 与 B 是否有师承、亲缘或传承关系？ | 孔子弟子中谁承继了礼学？ |
| 平行比较 | `COMPARE` | A 与 B 在类似处境下有何异同？ | 商鞅与吴起的变法命运为何相似？ |
| 关联链 | `CHAIN` | A→B→C，中间的 B 角色是什么？ | 刘邦封韩信 → 韩信封陈豨 → 陈豨叛乱 |
| 空白推断 | `BLANK` | 史记提到 A 做了 X，但接受者/影响者 B 无页面 | 范雎献计，但秦昭王的反应未被 wiki 表达 |
| 跨章重现 | `CROSSREF` | 同一人物在 N 个章节分别出现，全貌是什么？ | 郦食其在高祖本纪/郦生陆贾列传/齐世家各扮演什么角色？ |
| 反常解读 | `ANOMALY` | 史记的某段记载与常识或其他章节矛盾，为何？ | 太史公曰"项羽无政治才能"，但其军事成就如何解释？ |

---

## 二、问题生成方法

### 2.1 自动触发（每 10 轮，轻量扫描）

```bash
# 方法 A：共现分析 — 同章出现 ≥3次 但无 wikilink 互连的实体对
python3 wiki/scripts/butler/insight_scan.py --mode cooccur --top 10

# 方法 B：时空重叠 — 生卒年/任职期重叠的人物对，但无关系记录
python3 wiki/scripts/butler/insight_scan.py --mode overlap --top 10

# 方法 C：孤立节点 — 入度/出度差距悬殊的页面（被引多但自身少引他人）
python3 wiki/scripts/butler/insight_scan.py --mode isolation --top 10
```

### 2.2 手动触发（Butler 主动思考）

Butler 读当前处理的页面，结合 kg/events 和 entity_index，自问：
1. 这个人物的同时代人是谁？他们是否互动过？
2. 这个事件的受益者/受害者还有谁没有被提及？
3. 这段话提到了 A，但紧接着提到 B，他们的关联是否已被 wiki 表达？
4. 两个功能相似的历史人物（同为谋士/同为将领/同为王后）有没有对比页面？

### 2.3 随机激发（队列空时）

```bash
# 随机取2个 person 页，LLM 判断值得提问的关联角度
python3 -c "
import random, json, glob
pages = [f.split('/')[-1][:-3] for f in glob.glob('wiki/public/pages/*.md')]
persons = [p for p in json.load(open('wiki/public/pages.json'))['pages']
           if json.load(open('wiki/public/pages.json'))['pages'][p].get('type') == 'person']
a, b = random.sample(persons, 2)
print(f'随机实体对: {a} × {b}')
"
# 输出后由 Butler 判断是否值得提问
```

---

## 三、洞察问题格式

文件：`wiki/logs/butler/insight_queue.md`

```markdown
# 洞察问题队列

最后更新: YYYY-MM-DD

## 待调查

- [ ] I042 COLLAB 刘肥与曹参是否有直接政治合作？
      实体: [[刘肥]] × [[曹参]]
      背景线索: 刘肥封齐王(前201)，曹参为齐相(前201-前193)，共事约8年
      出处提示: [[052_齐悼惠王世家]] §3-8；[[054_曹相国世家]] §12-18
      → 建议动作: enrich 曹参页 + 刘肥页各加对方互链；或新建"刘肥与曹参"关系页
      → 发现于: W14 时空重叠扫描 2026-04-25
      → 置信度: high（史记明确记载同期共事）

- [ ] I043 COMPARE 商鞅与吴起：变法者的相似命运
      实体: [[商鞅]] × [[吴起]]
      背景线索: 两人均推行激进变法，均在君主去世后被杀，均成就了国家但毁灭了自己
      出处提示: [[068_商君列传]] [[065_孙子吴起列传]]
      → 建议动作: 新建"变法者命运"concept页 或 在两页各加"相似命运"段落
      → 发现于: W14 平行比较 2026-04-25
      → 置信度: medium（关联需综合叙述，非史记直接记载）

- [ ] I044 ANOMALY 郦食其游说齐王为何被韩信视为障碍？
      实体: [[郦食其]] × [[韩信]] × [[田广]]
      背景线索: 郦食其已说服齐王降汉，韩信仍乘机攻齐，导致郦食其被烹
      出处提示: [[092_淮阴侯列传]] §41；[[097_郦生陆贾列传]] §8
      → 建议动作: 在郦食其页加"被烹始末"节；在韩信页加"攻齐争议"节
      → 发现于: W14 反常解读 2026-04-25
      → 置信度: high

## 已处理

- [x] I031 COLLAB 萧何与曹参的政策传承 → enrich 曹参页 §萧规曹随 (2026-04-20)
- [x] I032 BLANK 秦二世胡亥的老师赵高：教育关系未 wiki 化 → 新建"赵高与胡亥"段 (2026-04-21)
```

**置信度定义**：
- `high`：史记有明确文本依据，关联基本确定
- `medium`：需综合多处文本，有合理推论空间
- `low`：纯推测/跨文本类比，需标注为假说

---

## 四、调查与处置流程

```
1. 取 insight_queue.md 中最老的一条"待调查"问题
2. 从出处提示的章节/段落读原文（chapter_md 或 pages.json）
3. 在 kg/events / entity_index 补充检索
4. 判断置信度 → 选择处置路径：

   [high] 直接证据存在
     → 在相关实体页追加节（enrich-infobox / link-from-relations / add-event-timeline）
     → 若关联内容 > 20 行，考虑新建 relationship / concept / story 页

   [medium] 间接证据，需综合叙述
     → 新建 concept 页（type: concept, 标注"综合推论"）或在主要实体页加段落
     → 段落加 note: "W14 洞察，基于综合推论，见源引文"

   [low] 纯推测，无文本支撑
     → 不创建页面；在 insight_queue 标注 [dismissed: no evidence]；记 failures.jsonl

5. 处置后 insight_queue 条目标为 [x]，附处置说明
6. 若创建了新页面，走 W2 create-stub 或 add_page.py 流程
```

---

## 五、新页面类型建议

洞察发现可能催生以下类型的新页面：

| 洞察类型 | 可能创建的页面类型 | frontmatter type |
|---|---|---|
| COLLAB / CONFLICT | 关系页（两人互动的专题） | `relation` |
| COMPARE | 比较/专题页 | `concept` |
| CHAIN | 事件链页（A→B→C 因果链） | `story` |
| CROSSREF | 人物专题深化（跨章综述） | `person`（丰富现有页） |
| ANOMALY | 解读/分析页 | `concept`（建设后可晋级 featured/premium）|
| LINEAGE | 师承/家族专题 | `concept` 或 `list` |

**关系页（`type: relation`）标准格式**：

```markdown
---
id: 刘肥与曹参
type: relation
label: 刘肥与曹参
entities: [刘肥, 曹参]
relation_type: 君臣
period: 前201-前193
sources: [052_齐悼惠王世家, 054_曹相国世家]
tags: [汉初, 齐国, 君臣关系]
generated_by: W14
---

# 刘肥与曹参

[[刘肥]]与[[曹参]]在齐国共事约八年（前201—前193年）。刘肥以高祖庶长子封齐王，曹参以功臣出任齐相…

## 史记引文

…
```

---

## 六、与其他 Skill 的关系

| Skill | 交互方式 |
|---|---|
| **W1** | W14 的 high 置信度洞察可直接作为 W1 候选，进入 queue.md（非 insight_queue） |
| **W2** | 处置时调用 `link-from-relations`、`create-stub`、`add-event-timeline` 等原子动作 |
| **W10** | 洞察以 H20 类型写入 housekeeping_queue，或直接在 insight_queue 自管理 |
| **W8** | ANOMALY / COMPARE 类高质量洞察可升级为精品页建设任务 |
| **W13** | W13 发现的"有实体出现但无 wiki 页面"的句子，可交给 W14 作 BLANK 类洞察起点 |

---

## 七、禁止事项

- ❌ 不为 low 置信度洞察创建页面（假说不应写成事实页）
- ❌ 不在正文以肯定口吻表达未被史记支持的关联（可写"据推测"/"或许"）
- ❌ 不一次处理多于 1 条洞察（每轮 1 条，遵守 W0 小步原则）
- ❌ 不修改已有页面的核心断言——只追加新节（append-only 原则）

---

## 相关路径

- `wiki/logs/butler/insight_queue.md` — 洞察问题队列
- `wiki/scripts/butler/insight_scan.py` — 自动洞察扫描（待实现：cooccur/overlap/isolation 三模式）
- `kg/entities/data/entity_index.json` — 实体库（W14 的主要检索对象）
- `kg/events/` — 事件数据（时序关联的依据）
- `skills/SKILL_W10_Butler内务整理.md` — H20 在内务体系中的位置
- `skills/SKILL_W8_精品页建设方法论.md` — 高质量洞察升级为精品页
- `skills/SKILL_W13_史记全文覆盖查验.md` — BLANK 类洞察的来源
