# Butler 候选队列

> 由 bootstrap.sh 于 2026-04-22 填充.
> P0 高优 / P1 中优 / P2 低优. 每次 invocation 只做 1 条, 按 W1 优先级选.

## 来自 discover_kg (kg top-N 缺 wiki 页)

- [ ] 周文王: `create-stub` (refs=97/章=42) [源:A] [P1] [2026-04-22]
- [ ] 晋文公: `create-stub` (refs=95/章=23) [源:A] [P1] [2026-04-22]
- [ ] 黄帝: `create-stub` (refs=92/章=24) [源:A] [P1] [2026-04-22]
- [ ] 项梁: `create-stub` (refs=89/章=21) [源:A] [P1] [2026-04-22]
- [ ] 袁盎: `create-stub` (refs=86/章=14) [源:A] [P1] [2026-04-22]
- [ ] 刘舜: `create-stub` (refs=81/章=26) [源:A] [P1] [2026-04-22]
- [ ] 秦张仪: `create-stub` (refs=79/章=14) [源:A] [P1] [2026-04-22]
- [ ] 雍王: `create-stub` (refs=79/章=17) [源:A] [P1] [2026-04-22]
- [ ] 秦缪公: `create-stub` (refs=76/章=28) [源:A] [P1] [2026-04-22]
- [ ] 赵高: `create-stub` (refs=75/章=11) [源:A] [P1] [2026-04-22]
- [ ] 楚怀王: `create-stub` (refs=75/章=23) [源:A] [P1] [2026-04-22]
- [ ] 尧: `create-stub` (refs=72/章=30) [源:A] [P1] [2026-04-22]
- [ ] 张楚楚隐王: `create-stub` (refs=71/章=23) [源:A] [P1] [2026-04-22]
- [ ] 秦二世: `create-stub` (refs=70/章=14) [源:A] [P1] [2026-04-22]
- [ ] 汉孝文帝: `create-stub` (refs=69/章=24) [源:A] [P1] [2026-04-22]
- [ ] 彭越: `create-stub` (refs=69/章=21) [源:A] [P1] [2026-04-22]
- [ ] 汉孝景帝: `create-stub` (refs=69/章=20) [源:A] [P1] [2026-04-22]
- [ ] 廉颇: `create-stub` (refs=68/章=15) [源:A] [P1] [2026-04-22]
- [ ] 陈平: `create-stub` (refs=66/章=17) [源:A] [P1] [2026-04-22]
- [ ] 管仲: `create-stub` (refs=65/章=21) [源:A] [P1] [2026-04-22]
- [ ] 伍子胥: `create-stub` (refs=65/章=20) [源:A] [P1] [2026-04-22]
- [ ] 李斯: `create-stub` (refs=64/章=12) [源:A] [P1] [2026-04-22]

## 来自 discover_sku (ontology-v2 SKU 缺 topic 页)

- [ ] 司马迁的史学思想: `import-sku-as-topic` (源: `kg/ontology/ontology-v2/shiji-2026-04-05-v1/skus/facts/fact_001.md`) [P1] [2026-04-22]
- [ ] 如何阅读史记: `import-sku-as-topic` (源: `kg/ontology/ontology-v2/shiji-2026-04-05-v1/skus/skills/skill_001.md`) [P1] [2026-04-22]

---

## P0 高优 (v8 反思新增)

- [ ] 批量生成 130 章节 stub 页 (chapter type): `batch-chapter-stubs` [P0] [2026-04-23 v8]
  - 预期: link_hit_rate 20.8% → 40%+, K +~4000
  - 需同时给 compute_knowledge.py 增加 TYPE_WEIGHT["chapter"]=0.4
- [ ] bootstrap.sh 末尾调用 compute_knowledge.py 自动打快照 [P0] [2026-04-23 v8]

## P1 (v8 新增)

- [ ] 精品页 白登之围 (event) [P1] [2026-04-23 v8]
- [ ] 精品页 萧何 / 曹参 / 陈平 任选一 (person) [P1] [2026-04-23 v8]
- [ ] 主页 footer 知识量仪表板 (提案 24) [P1] [2026-04-23 v8]
- [ ] 收敛 7 个 alias_conflicts (惠公/景公/桓/桓公/简/襄公/襄王) [P1] [2026-04-23 v8]

---

## 已完成 (本轮 v8, 2026-04-23)

- [x] `wiki/scripts/compute_knowledge.py` 知识量度量 K 首版
- [x] 首个 K 快照: 13336.34 / 229 页 / 链接命中率 20.8%
- [x] 精品页 巨鹿之战 (3.5 KB, 10 成语溯源)

---

## P2 低优 (手动加入)

（留给用户手动追加的低优任务）

## P2 - 语义插件
- 设计目标: 页面任意部分（段落、引用块、表格行）可携带内联元数据
- 语法草案: `{: key=value key2=value2 }` HTML data属性，或专用注释 `<!--meta: ... -->`
- 实现方向: markdown-it 插件，解析后附加到 DOM 元素 dataset

## P3 - 成语词条
- 每个典故与成语可以成为独立的 topic 页面（如 `完璧归赵.md`, `指鹿为马.md`）
- 内容: 出处（史记原文）+ 字面义 + 引申义 + 相关人物 wikilink
- 优先级低：先完成高引用人物扩写

## P1 - 邦国与侯国系统页面
- 目标: 将《史记》年表中的邦国/侯国数据系统化为 wiki 页面
- 数据源: 018_高祖功臣侯者年表、019_惠景间侯者年表、020_建元以来侯者年表 等
- 页面类型: type=state（邦国）
- 优先级: 高引用先做（齐国、赵国、楚国等战国七雄已有），侯国按引用数排
- 工具: 可写脚本从年表数据批量生成 stub（类似 generate_chapter_pages.py）

### bot-lint 待审 (2026-04-23)
- [ ] `晁错` L34 （[[101_袁盎晁错列传|101-018]]）
 → PN 119 (conf=0.56, quote_mismatch)
