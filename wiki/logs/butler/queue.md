# Butler 候选队列

> 由 bootstrap.sh 于 2026-04-22 填充.
> P0 高优 / P1 中优 / P2 低优. 每次 invocation 只做 1 条, 按 W1 优先级选.

## ⭐ 用户想要 (P0)
- [x] **[想要]** 楚: `create-stub` [P0] [2026-04-23] [用户请求] ✓ 已存在
- [x] **[想要]** 齐: `create-stub` [P0] [2026-04-23] [用户请求] ✓ 已存在

## ⛔ P0 [ARCH] — 等待用户批准

- [ ] **[ARCH] wiki 全部页面显示重构** [P0] [2026-04-23] [等待批准]
  - 反思文档：`logs/wiki_butler/reflections/arch_2026-04-23.md`
  - 问题：renderAll + renderCategory 全量渲染，671 页已出现体验问题，800 页后明显恶化
  - 待批准方案（三选其一）：
    - **A+B+C**（推荐）：首字过滤栏 + 类型折叠 + person 排序维度，共约 100 行改动
    - **仅 A**：只加首字过滤栏，最小改动
    - **T2**：直接做按需渲染（懒加载），更彻底但工作量更大
  - Butler 在收到批准前不会自动修改 renderer.js

## W11 R960 新发现 (P1)

- [x] 晋: `create-stub` ✓ R961
- [x] 代: `create-stub` ✓ R962
- [x] 吴: `create-stub` ✓ R963
- [x] 鲁: `create-stub` (wanted=22链接) [源:W11] [P1] [2026-04-24] ✓ 已存在
- [x] 禹: redirect→大禹 ✓ R966
- [x] 常山王: redirect→张耳 ✓ R978
- [x] 北平康侯: `create-redirect`→张苍 (refs=30) [源:discover_kg R983] [P1] [2026-04-24] ✓ 已存在
- [x] 王子城父: `create-stub` (refs=30/章=4) [源:discover_kg R993] [P1] [2026-04-24] ✓ 已存在
- [x] 殷: `create-stub` ✓ R968
- [x] 舜: `enrich-stub` ✓ R969
- [x] 汤: `create-stub` (wanted=16链接，成汤，人物) [源:W11 R970] [P1] [2026-04-24] ✓ 已存在
- [x] 梁: `create-redirect`→魏 或 stub (wanted=18链接) [源:W11 R970] [P1] [2026-04-24] ✓ 已存在
- [x] 陈: `create-stub` (wanted=15链接，春秋陈国) [源:explore R964] [P1] [2026-04-24] ✓ 已存在
- [x] 卫: `create-stub` (wanted=14链接，卫国) [源:explore R964] [P1] [2026-04-24] ✓ 已存在
- [x] 郑: `create-stub` (wanted=14链接，郑国) [源:explore R964] [P1] [2026-04-24] ✓ 已存在

## 来自 discover_kg (kg top-N 缺 wiki 页)

- [x] 周文王: `create-stub` (refs=97/章=42) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 晋文公: `create-stub` (refs=95/章=23) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 黄帝: `create-stub` (refs=92/章=24) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 项梁: `create-stub` (refs=89/章=21) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 袁盎: `create-stub` (refs=86/章=14) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 刘舜: `create-stub` (refs=81/章=26) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 秦张仪: `create-stub` (refs=79/章=14) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 雍王: `create-stub` (refs=79/章=17) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 秦缪公: `create-stub` (refs=76/章=28) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 赵高: `create-stub` (refs=75/章=11) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 楚怀王: `create-stub` (refs=75/章=23) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 尧: `create-stub` (refs=72/章=30) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 张楚楚隐王: `create-stub` (refs=71/章=23) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 秦二世: `create-stub` (refs=70/章=14) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 汉孝文帝: `create-stub` (refs=69/章=24) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 彭越: `create-stub` (refs=69/章=21) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 汉孝景帝: `create-stub` (refs=69/章=20) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 廉颇: `create-stub` (refs=68/章=15) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 陈平: `create-stub` (refs=66/章=17) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 管仲: `create-stub` (refs=65/章=21) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 伍子胥: `create-stub` (refs=65/章=20) [源:A] [P1] [2026-04-22] ✓ 已存在
- [x] 李斯: `create-stub` (refs=64/章=12) [源:A] [P1] [2026-04-22] ✓ 已存在

## 来自 discover_sku (ontology-v2 SKU 缺 topic 页)

- [x] 司马迁的史学思想: `import-sku-as-topic` ✓ 已存在
- [x] 如何阅读史记: `import-sku-as-topic` ✓ 已存在

---

## P0 高优 (v8 反思新增)

- [ ] 批量生成 130 章节 stub 页 (chapter type): `batch-chapter-stubs` [P0] [2026-04-23 v8]
  - 预期: link_hit_rate 20.8% → 40%+, K +~4000
  - 需同时给 compute_knowledge.py 增加 TYPE_WEIGHT["chapter"]=0.4
- [ ] bootstrap.sh 末尾调用 compute_knowledge.py 自动打快照 [P0] [2026-04-23 v8]

## P1 — add-tag (R976 explore, discover_tags)

- [x] 张仪: `add-tag` (+ 世家人物) ✓ 已存在
- [x] 赵襄子: `add-tag` ✓ 已存在
- [x] 董仲舒: `add-tag` ✓ 已存在
- [x] 公孙弘: `add-tag` ✓ 已存在
- [x] 陈平: `add-tag` ✓ 已存在
- [x] 窦太后: `add-tag` ✓ 已存在
- [x] 墨子: `add-tag` ✓ 已存在
- [x] 文种: `add-tag` ✓ 已存在
- [x] 周宣王: `add-tag` ✓ 已存在
- [x] 傅说: `add-tag` ✓ 已存在
- [x] 司马穰苴: `add-tag` ✓ 已存在
- [x] 邹阳: `add-tag` ✓ 已存在
- [注] discover_tags 总计 536 页有新标签建议，后续批量处理

## P2 — cite-doc-report (寿命推断报告引用，R973 explore)

- [ ] 扶苏: `cite-doc-report` [源: doc/lifespan_inference/秦/扶苏.md] [P2] [2026-04-24]
- [ ] 蒙恬: `cite-doc-report` [源: doc/lifespan_inference/秦/蒙恬.md] [P2] [2026-04-24]
- [ ] 太子丹: `cite-doc-report` [源: doc/lifespan_inference/秦/太子丹.md] [P2] [2026-04-24]
- [ ] 陈胜: `cite-doc-report` [源: doc/lifespan_inference/秦/陈胜.md] [P2] [2026-04-24]

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
- [x] `晁错` L34 （[[101_袁盎晁错列传|101-018]]）→ 拆为 101-118 + 101-119

### bot-lint 待审 (2026-04-23)
- [ ] `二世皇帝` L31 （006-083）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `勾践` L44 （[[041_越王句践世家|041-012]]）
 → PN 21 (conf=0.63, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `卫灵公` L48 （047-024）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `吴王阖闾` L64 （031-032）
 → PN 30.2 (conf=0.79, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `夫差` L47 （[[041_越王句践世家|041-009]]）
 → PN 17 (conf=0.79, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `姬旦` L39 （033-002）
 → PN ? (conf=0.00, missing_pn)
- [ ] `姬旦` L60 （033-005意旨）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `宋义` L49 （007-015）
 → PN 35.2 (conf=0.75, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `平原君` L42 （[[076_平原君虞卿列传|076-006]]）
 → PN 5 (conf=0.94, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `张仪` L32 （070-003）
 → PN 2 (conf=0.68, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `张耳` L63 （[[089_张耳陈馀列传|089-030]]）
 → PN 29 (conf=0.76, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `彭越` L60 （汉王）与韩信、彭越期会击楚……乃皆来。"*（008-063）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `扶苏` L30 （[[006_秦始皇本纪|006-041]]）
 → PN 72.1 (conf=0.76, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `晋平公` L50 （024-004）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `晋悼公` L38 （039-118）
 → PN 117 (conf=0.57, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `李斯` L66 （087-006）
 → PN ? (conf=0.00, missing_pn)
- [ ] `李斯` L87 （087-023）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `樊哙` L46 （[[007_项羽本纪|007-018]]）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `毛遂` L54 （[[076_平原君虞卿列传|076-006]]）
 → PN 5 (conf=0.84, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `汉文帝` L40 （010-001）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `王离` L54 （007-030）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `田单` L51 （082-006）
 → PN 6.3 (conf=0.67, missing_pn)
- [ ] `田单` L73 （082-009）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `田常` L33 （046-016）
 → PN ? (conf=0.00, missing_pn)
- [ ] `田常` L55 （046-017）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `秦始皇` L71 （006-015）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `秦子婴` L65 （006-104）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `箕子` L56 （038-010）
 → PN 9 (conf=0.91, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `聂政` L48 （[[086_刺客列传|086-019]]）
 → PN 22 (conf=0.56, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `范增` L36 （007-009）
 → PN ? (conf=0.00, missing_pn)
- [ ] `范增` L46 （007-025）
 → PN ? (conf=0.00, missing_pn)
- [ ] `范增` L66 （007-049）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `荆轲` L48 （[[086_刺客列传|086-039]]）
 → PN 56 (conf=0.59, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `蒙毅` L45 （[[088_蒙恬列传|088-010]]）
 → PN 8 (conf=0.59, quote_mismatch)
- [ ] `蒙毅` L53 （[[088_蒙恬列传|088-012]]）
 → PN 10 (conf=0.76, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `虞姬` L30 （[[007_项羽本纪|007-040]]）
 → PN 168.2 (conf=0.48, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `赵括` L35 （081-017）
 → PN 25.3 (conf=0.64, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `陆贾` L40 （097-011）
 → PN 10 (conf=0.64, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `陈馀` L42 （089-015）
 → PN 14 (conf=0.56, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `项梁` L41 （007-003） → PN 5.2 (conf=0.67, missing_pn)
- [ ] `项梁` L51 （007-005）
 → PN ? (conf=0.00, missing_pn)
- [ ] `项梁` L69 （007-009）
 → PN ? (conf=0.00, missing_pn)
- [ ] `项梁` L78 （007-013）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `高渐离` L37 （[[086_刺客列传|086-037]]）
 → PN 53 (conf=0.55, quote_mismatch)

### bot-lint 待审 (2026-04-23)
- [ ] `鲁仲连` L38 （083-005）
 → PN 4.3 (conf=0.76, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `鲁哀公` L43 （047-044）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `齐威王` L37 （046-006）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `齐简公` L47 （046-033）
 → PN ? (conf=0.00, missing_pn)
- [ ] `齐简公` L57 （047-039）
 → PN ? (conf=0.00, missing_pn)
- [ ] `齐简公` L62 （047-039）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `李斯` L66 （087-006）
 → PN ? (conf=0.00, missing_pn)
- [ ] `李斯` L87 （087-023）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `秦始皇` L71 （006-015）
 → PN ? (conf=0.00, missing_pn)

### bot-lint 待审 (2026-04-23)
- [ ] `项梁` L41 （007-003） → PN 5.2 (conf=0.67, missing_pn)
- [ ] `项梁` L51 （007-005）
 → PN ? (conf=0.00, missing_pn)
- [ ] `项梁` L69 （007-009）
 → PN ? (conf=0.00, missing_pn)
- [ ] `项梁` L78 （007-013）
 → PN ? (conf=0.00, missing_pn)

## W11 R1020 新发现（2026-04-24）

### P1 create-stub
- [ ] 王：KG refs=40/章=11，需调查具体含义（人名？职位？）→ 可能需消歧页或调查KG canonical

### R1021 调查结论：「王」KG bug
- 「王」canonical 是 KG 侧 bug：田儋/田安/田市/田广/田荣/田都/申阳/英布/韩信 均被错误归入 canonical="王"（因为都封了王）
- **结论**：不创建 wiki 页面；需 KG 侧修复（discover_kg 应将其加入 bad canonical 跳过列表）
- ✓ R1021 已调查，标记为 skip

## explore 发现 - cite-doc-report 真阳性 (2026-04-25)

（discover_doc.py 有大量假阳性；以下为手工验证的真阳性）

- [x] 项羽: `cite-doc-report` ✓ R4957
- [x] 秦始皇: `cite-doc-report` ✓ R4995 假阳性（页面已有[^life]）
- [x] 韩信: `cite-doc-report` ✓ R4995 假阳性（页面已有[^life]）
- [x] 张良: `cite-doc-report` ✓ R4995 假阳性（页面已有[^life]）
- [x] 司马迁: `cite-doc-report` ✓ R4995 假阳性（页面已有[^life]）
- [x] 孔子: `cite-doc-report` ✓ R4995 假阳性（页面已有[^life]）
