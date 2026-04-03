# 史记知识库 TODO

> 最后更新：2026-04-03 (新增CHANGELOG commit ID审查任务)
>
> **重要说明**：
> - 本文件保留核心开发任务和执行中的流程任务
> - 功能建议类任务已迁移至 [GitHub Issues](https://github.com/baojie/shiji-kb/issues)
> - Issue管理规范见 [SKILL_10a](skills/SKILL_10a_TODO和Issue管理.md)

---

## 📊 文档维护任务

### CHANGELOG commit ID 完整性审查与补充

**发现日期**: 2026-04-03

**问题描述**：
- 审查发现CHANGELOG.md中存在大量commit ID遗漏
- 总计30个日期需要补充commit ID，涉及400+个commits未被记录
- 最严重的日期：2026-03-18 (36个)、2026-03-29 (23个)、2026-02-07 (22个)

**受影响日期**（按缺失数量排序）：
1. 2026-03-18: 缺少 36个 commits
2. 2026-03-29: 缺少 23个 commits
3. 2026-02-07: 缺少 22个 commits
4. 2026-03-15: 缺少 21个 commits
5. 2026-03-08: 缺少 21个 commits
6. 2026-03-31: 缺少 20个 commits
7. 2026-02-08: 缺少 20个 commits
8. 2026-03-24: 缺少 19个 commits
9. 2026-03-21: 缺少 19个 commits
10. 2026-03-14: 缺少 18个 commits
11. 其他20个日期: 缺少 3-13个 commits

**处理策略**（待决定）：
- **选项A**: 保持现状 - CHANGELOG作为高层次总结，不必包含每个commit ID
- **选项B**: 重点补充 - 只为重要日期（2026-03至04月）补充commit ID
- **选项C**: 自动化重建 - 编写脚本从git历史自动生成完整的CHANGELOG

**审查工具**：
- 脚本位置：`scripts/audit_changelog_commits.py`
- 使用方法：`python scripts/audit_changelog_commits.py`
- 功能：检查CHANGELOG.md中每个日期是否包含了所有对应的git commits
- 输出：显示每个日期缺失的commit ID列表

**优先级**: 低（不影响项目功能）

**决策人**: @baojie

---

## 📋 待执行重构任务

### 🗂️ 结构化知识库导出

**任务**：生成标准格式的知识库汇总文件，便于机器读取和跨平台使用

**输出格式**：
- [ ] **JSON格式**：`kg/export/shiji_kb.json` - 包含实体、事件、关系、本体的完整结构
- [ ] **YAML格式**：`kg/export/shiji_kb.yaml` - 人类可读性更强的层级结构
- [ ] **RDF/Turtle格式**：`kg/export/shiji_kb.ttl` - 语义网标准格式，支持SPARQL查询

**数据结构设计**：
- 实体索引（entity_index.json）→ 统一实体表
- 动词索引（verb_index.json）→ 动词表
- 事件索引（130章事件）→ 统一事件表
- 事件关系（event_relations.json）→ 关系表
- 本体（ontology/）→ 类型层级和属性定义
- SKU（knowledge-units/）→ 知识单元表

**用途**：
- 支持外部工具导入（如Neo4j、GraphDB等）
- 便于跨项目引用和二次开发
- 提供API友好的数据接口
- 支持学术研究数据集发布

**参考规范**：
- JSON-LD for linked data
- Schema.org vocabulary
- Dublin Core metadata

**优先级**：中（可作为2026 Q2任务）

---

### 🏗️ 目录结构重构（底本终稿完成后执行）

**前置条件**：完成001-130章的多版本互校（SKILL_01b）

**任务清单**：
- [ ] **目录结构迁移**：执行 `docs/SPEC_directory_restructure.md` 中定义的新目录结构
  - 迁移 `archive/chapter/` → `archive/sources/chapter/`
  - 迁移 `curation_base/` → `curation/simplified/`
  - 迁移 `logs/curation/reports/` → `curation/reports/`
  - 创建 `archive/references/`（参考资料）
  - 创建 `final/`（底本终稿目录）
  - 备份旧目录到 `archive/legacy/`

- [ ] **繁简映射系统**：实现基于上下文的鲁棒映射机制
  - 开发 `scripts/mapping/generate_mapping.py`（生成初始映射）
  - 开发 `scripts/mapping/update_mapping.py`（文本修改后更新映射）
  - 开发 `scripts/mapping/apply_mapping.py`（简体标注→繁体渲染）
  - 开发 `scripts/mapping/validate_mapping.py`（验证映射完整性）

- [ ] **底本改进流程**：从 curation/ 生成 final/
  - 开发 `scripts/improvements/normalize_punctuation.py`（标点全角归一化）
  - 开发 `scripts/improvements/fix_paragraphs.py`（段落整合）
  - 开发 `scripts/improvements/normalize_text.py`（空格/换行符/BOM规范化）
  - 对全部130章执行改进流程
  - 生成改进日志 `final/improvements/*.md`

- [ ] **文档更新**：
  - 更新 SKILL_01 引用新目录结构
  - 更新 SKILL_01b 引用新目录结构和输出格式
  - 创建 SKILL_01c（底本改进规范）
  - 更新所有脚本的路径引用

**详细规范**：[docs/SPEC_directory_restructure.md](docs/SPEC_directory_restructure.md)

---

## 📝 近期转移到Issue的任务

### 2026-03-30: 北大考古学生反馈 (Issue #85)

根据北京大学考古文博学院师生的课堂反馈，新建和增补以下Issues：

**新建Issues (3个)**:
- [#87](https://github.com/baojie/shiji-kb/issues/87) 文本版本体系：版本信息、注释、异文集成展示
- [#88](https://github.com/baojie/shiji-kb/issues/88) 图文对照：原始典籍页面与数字文本并列展示
- [#89](https://github.com/baojie/shiji-kb/issues/89) 官制词典：辅助理解复杂官制体系

**增补到现有Issues (2个)**:
- [#41](https://github.com/baojie/shiji-kb/issues/41) 全文搜索功能 - 增补模糊搜索改进需求（提高准确度，扩展至地名、官职、典故等）
- [#60](https://github.com/baojie/shiji-kb/issues/60) AI问答(RAG) - 增补问题驱动数据库建设需求（史料溯源、作者意图分析、系统性发现）

**已完成 (1个)**:
- [#17](https://github.com/baojie/shiji-kb/issues/17) 开关面板 - ✅ 语法高亮开关已实现

**社区反馈文档**: [resources/community/2026-03-30_北大考古学生反馈_issue85.md](resources/community/2026-03-30_北大考古学生反馈_issue85.md)

---

### 2026-03-30: 功能建议大迁移

从TODO.md迁移29个任务到GitHub Issues，保持TODO专注于核心开发任务：

**BUG类 (1个)**:
- [#35](https://github.com/baojie/shiji-kb/issues/35) 【P0】修复被篡改的原文字符

**FEAT类 - 阅读体验 (12个)**:
- [#36](https://github.com/baojie/shiji-kb/issues/36) 实体悬浮预览
- [#37](https://github.com/baojie/shiji-kb/issues/37) 实体索引升级为Concordance
- [#38](https://github.com/baojie/shiji-kb/issues/38) 段落便签系统
- [#39](https://github.com/baojie/shiji-kb/issues/39) 句间逻辑关系分析与可视化
- [#40](https://github.com/baojie/shiji-kb/issues/40) 地铁图换乘设计优化
- [#41](https://github.com/baojie/shiji-kb/issues/41) 全文搜索功能
- [#42](https://github.com/baojie/shiji-kb/issues/42) 繁体支持与繁简切换
- [#43](https://github.com/baojie/shiji-kb/issues/43) 地图联动
- [#44](https://github.com/baojie/shiji-kb/issues/44) 辞典释义
- [#45](https://github.com/baojie/shiji-kb/issues/45) 实体颜色系统重设计
- [#46](https://github.com/baojie/shiji-kb/issues/46) 语法高亮整体设计
- [#47](https://github.com/baojie/shiji-kb/issues/47) 响应式设计优化（移动端）

**FEAT类 - 数据与内容 (6个)**:
- [#48](https://github.com/baojie/shiji-kb/issues/48) 与中华书局版电子版校对
- [#49](https://github.com/baojie/shiji-kb/issues/49) 韵文识别与排版
- [#50](https://github.com/baojie/shiji-kb/issues/50) 事件-实体同步更新
- [#51](https://github.com/baojie/shiji-kb/issues/51) 新实体类型评估
- [#52](https://github.com/baojie/shiji-kb/issues/52) 事件罗生门（同一事件多章节对比）
- [#53](https://github.com/baojie/shiji-kb/issues/53) 十表导出CSV

**FEAT类 - 工程与架构 (4个)**:
- [#54](https://github.com/baojie/shiji-kb/issues/54) 实体标注格式改为非对称标签
- [#55](https://github.com/baojie/shiji-kb/issues/55) 知识图谱深化：事件关系图谱
- [#56](https://github.com/baojie/shiji-kb/issues/56) Neo4j图数据库导入
- [#57](https://github.com/baojie/shiji-kb/issues/57) 自动化测试与CI/CD

**FEAT类 - 未来探索 (6个)**:
- [#58](https://github.com/baojie/shiji-kb/issues/58) 文献对勘
- [#59](https://github.com/baojie/shiji-kb/issues/59) 相似事件匹配（向量化检索）
- [#60](https://github.com/baojie/shiji-kb/issues/60) AI问答（RAG）
- [#61](https://github.com/baojie/shiji-kb/issues/61) 多维度解构阅读（主题分类）
- [#62](https://github.com/baojie/shiji-kb/issues/62) 词云生成
- [#63](https://github.com/baojie/shiji-kb/issues/63) 扩展到二十六史

**查看全部Issues**: [GitHub Issues](https://github.com/baojie/shiji-kb/issues)

---

## ✅ 近期关闭的Issue（已完成任务归档）

### 2026-03-30: 已完成任务迁移到Issues

将已完成的TODO任务转为GitHub Issues并立即关闭，便于项目历史追溯：

**最新完成任务 (2026-03-21) - 5个**:
- [#64](https://github.com/baojie/shiji-kb/issues/64) 为所有SKILL添加YAML frontmatter ([89b1c38a](https://github.com/baojie/shiji-kb/commit/89b1c38a))
- [#65](https://github.com/baojie/shiji-kb/issues/65) 司马迁文风研究实验 ([0117a825](https://github.com/baojie/shiji-kb/commit/0117a825))
- [#66](https://github.com/baojie/shiji-kb/issues/66) 溯源推理分析实验 ([4ebda328](https://github.com/baojie/shiji-kb/commit/4ebda328))
- [#67](https://github.com/baojie/shiji-kb/issues/67) 参与指南文档 ([21582643](https://github.com/baojie/shiji-kb/commit/21582643))
- [#68](https://github.com/baojie/shiji-kb/issues/68) 技术文章《从历史书中探索知识图谱》 ([6360679d](https://github.com/baojie/shiji-kb/commit/6360679d))

**历史完成任务 (2026-03-18及更早) - 16个**:
- [#69](https://github.com/baojie/shiji-kb/issues/69) 动词标注体系 v3.0 (2026-03-18, [cca73582](https://github.com/baojie/shiji-kb/commit/cca73582))
- [#70](https://github.com/baojie/shiji-kb/issues/70) 姓氏推理规划：SKILL_07b + spec + agent提示词模板 (2026-03-16)
- [#71](https://github.com/baojie/shiji-kb/issues/71) Purple Numbers 可点击复制 (2026-02)
- [#72](https://github.com/baojie/shiji-kb/issues/72) 实体交叉引用跳转 (2026-02-09)
- [#73](https://github.com/baojie/shiji-kb/issues/73) 11类→15类实体标注体系（+典籍/礼仪/刑法/思想）(2026-03-13)
- [#74](https://github.com/baojie/shiji-kb/issues/74) 实体索引15类HTML页面（含别名合并586条/消歧644处）(2026-03-13)
- [#75](https://github.com/baojie/shiji-kb/issues/75) 语义消歧（4层启发式，644处）(2026-02-10)
- [#76](https://github.com/baojie/shiji-kb/issues/76) 十表（013-022）表格渲染 (2026-02-09)
- [#77](https://github.com/baojie/shiji-kb/issues/77) 事件年代五轮反思审查（98.7%覆盖，~2,119处修正）(2026-03-11)
- [#78](https://github.com/baojie/shiji-kb/issues/78) 事件地铁图（130条线路）(2026-03-11)
- [#79](https://github.com/baojie/shiji-kb/issues/79) 事件关系（7,652条）(2026-03-11)
- [#80](https://github.com/baojie/shiji-kb/issues/80) 标注符号迁移（神话〖?〗/生物〖+〗）(2026-03-13)
- [#81](https://github.com/baojie/shiji-kb/issues/81) v2.0实体标注符号迁移（〖〗格式 + 官职符号$→;）(2026-03-13)
- [#82](https://github.com/baojie/shiji-kb/issues/82) 语义区块 ::: fenced div迁移 + 130篇太史公曰/赞标注补全 (2026-03-13)
- [#83](https://github.com/baojie/shiji-kb/issues/83) 新增SKILL_区块与韵文处理.md（方法论SKILL增至11个）(2026-03-13)
- [#84](https://github.com/baojie/shiji-kb/issues/84) 十表（013-022）事件补充提取（226个事件，平均每表22.6个）(2026-03-11)

**查看全部已关闭Issues**: [GitHub Issues (closed)](https://github.com/baojie/shiji-kb/issues?q=is%3Aissue+is%3Aclosed)

### 2026-03-30: 功能完成确认

发现已完成功能，添加commit信息后关闭：

- [#53](https://github.com/baojie/shiji-kb/issues/53) 十表导出CSV (2026-02-09, [d6e2b667](https://github.com/baojie/shiji-kb/commit/d6e2b667))
- [#47](https://github.com/baojie/shiji-kb/issues/47) 响应式设计优化（移动端）- 网站已实现响应式设计
- [#54](https://github.com/baojie/shiji-kb/issues/54) 实体标注格式改为非对称标签 (2026-03-16, [650aa7d3](https://github.com/baojie/shiji-kb/commit/650aa7d3))
- [#51](https://github.com/baojie/shiji-kb/issues/51) 新实体类型评估 - 18类实体体系完成 (v1.0→v2.8演进)

---

## 🔥 近期优先

> **说明**：阅读体验、数据与内容、工程与架构、未来探索等功能建议已迁移到 [GitHub Issues](https://github.com/baojie/shiji-kb/issues)

### 常规优先任务

- [ ] **人物生卒年反思**：四轮反思推断人物生卒年区间（span格式），记录证据链和置信度（详见 [SKILL_07a](skills/SKILL_07a_人物生卒年推断.md) / [spec](doc/spec/PLAN_人物生卒年反思.md)）
  - 第一轮：从原文提取年龄/在位年数证据（正则扫描"生X岁"/"立X年"等）
  - 第二轮：从事件索引获取锚点事件年份（即位、卒、出奔等）
  - 第三轮：计算生卒年区间（按方法1→5优先级，记录证据链和置信度）
  - 第四轮：亲属关系交叉约束验证（父卒<子生、兄弟年龄差<40年）
  - 数据升级：升级现有 `person_lifespans.json` 为区间格式（含置信度和证据链）
  - 试点验证：对前5章本纪人物试点推断（验证方法）
  - 生成推断报告：每人附带证据链+置信度+矛盾标记
  - 传说时代特殊处理：标记 legend，区间≥100年
  - **完成后更新谥号索引**：将生卒年区间同步到 `shihao_index.json` 和 HTML 页面

- [ ] **反常推理**：检测违反常识/制度/逻辑的单条事实，挖掘值得深究的历史异常点（详见 [SKILL_07c](skills/SKILL_07c_反常推理.md)）
  - 建立 `anomaly_report.json` 初始文件（从矛盾案例库迁移）
  - 优先处理六个高密度场景：长平降卒数字、秦始皇无皇后、刘邦年龄、吕后称制、项羽破釜沉舟、商鞅徙木立信
  - 编写数字异常自动扫描脚本 + LLM 批量评估流水线

- [ ] **姓氏推理**：为先秦人物建立姓/氏/名/字记录，厘清"同姓"语义（详见 [SKILL_07b](skills/SKILL_07b_姓氏推理.md) / [spec](doc/spec/PLAN_姓氏制度.md)）
  - Round 1：创建 `xing_index.json` + 直接提取20个高置信度人物写入 `person_xingshi.json`
  - Round 2：邦国推理（040楚世家、084屈原列传优先）
  - Round 3–4：氏族推理 + 父系链传播
  - 标注层：更新 SKILL_03a，增加 `〖&X|姓〗` / `〖&X|氏〗` 子类型

- [ ] **三家注标注**：裴骃集解、司马贞索隐、张守节正义嵌入（详见 [SKILL_三家注标注.md](SKILL_三家注标注.md)）
  - 获取文本 → `parse_sanjia.py` 解析 → `annotate_sanjia.py` 标注 → 渲染集成（点击展开/折叠）

- [ ] **实体标注反思管线**：参照事件年代反思管线，建立实体标注质量审查工作流
  - 每轮检查：遗漏（单字省称、泛称词）/ 消歧（同名异人）/ 别名（称谓映射）
  - 输出 corrections JSON → 写回 tagged.md → 重新生成索引，多轮迭代至收敛

- [ ] **年份时间消歧语法标注**：将year_ce_map.json中的6655条年份→公元年映射写回到130章markdown文件
  - 前提：当前year_ce_map.json已包含76.87%覆盖率的年份消歧结果
  - 目标：在原文中添加消歧语法标注（如 `〖%元年|-201〗`）
  - 方法：编写脚本读取year_ce_map.json，定位到对应章节/段落/文本，插入消歧标注
  - 验证：确保标注后的文本仍符合标注铁律（不改变原文字符）
  - 详见：[SKILL_03g_时间实体消歧.md](skills/SKILL_03g_时间实体消歧.md)

- [ ] **PN映射表更新派生产物溯源**：基于已建立的PN映射表（data/pn_mapping_complete.json），更新所有派生产物中的PN引用
  - 前提：已完成PN规范化（commit 6b20e096 → 74032d6），建立了1322条映射（覆盖73章）
  - 优先范围：
    - [ ] 更新 docs/entities/timeline.html 中的375处PN引用（44.2%已匹配，28.4%需更新）
    - [ ] 更新 kg/events/ 相关文件中的PN溯源引用
    - [ ] 检查并更新其他包含PN引用的派生文件（索引页面、关系图谱等）
  - 工具脚本：
    - `scripts/update_timeline_pn.py` - 自动更新timeline.html
    - `scripts/verify_timeline_pn_content.py` - 验证更新正确性
  - 验证标准：所有PN引用指向的内容与原文匹配（100%内容一致性）
  - 数据源：[data/pn_mapping_complete.json](data/pn_mapping_complete.json) / [README](data/PN_MAPPING_README.md)



更多请看 [Github Issues](https://github.com/baojie/shiji-kb/issues)

## Idea
* 除了段落编号，其实所有的东西（实体，事件，事实，过程……）都需要ID。要写一个ID规范文档
* 显示人物关系的图谱
* 某个地名当时的地图
* 写一个迁移指南，用另外一本书做例子，演示清楚怎么把现在的SKILL迁移到另一本书。这个迁移指南应该有一个skill（给agent看）和一个配套的doc（给人看）。实现META 13的实例化
* 校勘下加一个子skill 审音和拼音标注

03-29 ：下面有三个校勘任务
 - 首先要做一次完整性修复skill 01a，因为实体反思v3破坏了原文
 - 然后要做docs/SPEC_directory_restructure.md 约定的校勘相关文件夹重构，并更新所有相关文档和script
 - 然后要做skill 1b规定的校勘

