# W11 分类知识库

对应 Skill：SKILL_W11_概念分类元反思
写入时机：W11 审计确认某分类规则后追加
读取时机：每次 butler invocation 启动时；reclassify 动作前必读

---

## 类型判断规则

### person
<!-- [R<N> 确认] 条件 → 判为 person -->

### event
<!-- [R<N> 确认] 条件 → 判为 event -->

### concept
<!-- [R<N> 确认] 条件 → 判为 concept -->
- [R122 确认] 单一抽象概念（如"远交近攻"、"刎颈之交"）且无具体史事展开 → concept

### overview（综述）
<!-- [R<N> 确认] 条件 → 判为 overview -->
- [R122 确认] 方法论类页面（标题含"方法论/完整分析/框架/步骤"）→ overview
- [R122 确认] ontology 导入的综合分析页（无具体历史人物主线）→ overview

### sanwen
<!-- [R<N> 确认] 条件 → 判为 sanwen -->

## 已完成批量分类修正

<!-- 记录已处理的批次，避免重复扫描 -->
- [R122] 152个无类型页面 → overview
- [R122] topic类型全部迁移（5→concept，2→overview）
