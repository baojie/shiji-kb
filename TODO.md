# 史记知识库 TODO

> 最后更新：2026-04-25（Ontology v2 全部 130 章清零完成）
>
> **重要说明**：
> - 本文件保留核心开发任务和执行中的流程任务
> - 功能建议类任务已迁移至 [GitHub Issues](https://github.com/baojie/shiji-kb/issues)
> - Issue 管理规范见 [SKILL_10a](skills/SKILL_10a_TODO和Issue管理.md)

---

## 🗂️ Ontology v2 完成进度

计划文档：[labs/planning/ontology_v2_完成计划.md](labs/planning/ontology_v2_完成计划.md)

- [x] **第 1 轮 001-005**（2026-04-22）：18 骨架文件填充完成，5 章 skeleton=0，新增 ~173KB
- [x] **第 2 轮 009-018**（2026-04-22）：14 骨架文件填充完成，10 章 skeleton=0，新增 ~162KB
- [x] **第 3 轮 021-030**（2026-04-22）：37 骨架文件填充完成，10 章 skeleton=0，新增 ~255KB
- [x] **第 4 轮 033-046**（2026-04-22）：62 骨架/占位文件 + 16 章全面清零，新增 ~650KB；含 REPORT 迁移至 logs/（20 文件中文重命名）
- [x] **第 5 轮 048-058**（2026-04-22）：99 骨架/占位文件 + 12 章全部清零，新增 ~1.1MB；拆 5a（048-053 已单独 commit fbd9132a）+ 5b（054-058）
- [x] **第 6 轮 059-067**（2026-04-25）：9 章全部清零（059/060/062/063/064/066/067 完成填充，061/065 已完备），新增 ~456KB
- [x] **第 7 轮 069-079**（2026-04-25）：11 章全部清零（069/070/071/072/074/075/076/077/079 完成填充，073/078 已完备），新增 ~339KB
- [x] **第 8 轮 080-090**（2026-04-25）：11 章全部清零（080/082/083/085/088/089/090 完成填充，081/084/086/087 已完备），新增 ~373KB
- [x] **第 9 轮 092-101**（2026-04-25）：10 章全部清零（092/095/096/097/098/099/100/101 完成填充，091/093/094 已完备），新增 ~271KB
- [x] **第 10 轮 102-110**（2026-04-25）：9 章全部清零（102/103/104/105/106/107/108/109/110 完成填充），新增 ~307KB
- [x] **第 11 轮 111-120**（2026-04-25）：10 章全部清零（111/112/113/114/115/116/117/118/119/120 完成填充），新增 ~393KB
- [x] **第 12 轮 121-130**（2026-04-25）：10 章全部清零（121/122/123/124/125/126/127/128/129/130 完成填充），新增 ~470KB
- [x] **顶层 8 个主题级 SKU**（2026-04-25）：fact_002-007 + skill_002/003 全部完成，新增 ~34KB
- [x] **最终清理轮**（2026-04-25）：清除全部剩余骨架/小文件，涉及 001/004/005/009-012/014-023/024/032/033-038/040/042/043/069/075-077/081/084/091-092/123 等章；删除无效 JSON 存根，补写 fact/skill/eureka/mapping，**达成 130/130 全部清零** ✅

---

## 🔥 近期优先

### 💡 抽象概念词条新建队列（来自 idea.md，2026-04-25）

**背景**：史记中有大量"具象→抽象"的典故概念（如仓中鼠/厕中鼠），应建 `concept` 类型独立词条。已系统扫描原文，以下为确认有原文出处、尚未建页的候选：

| 词条 | 出处章节 | 原文关键句 |
|------|---------|-----------|
| 仓中鼠 | 李斯列传 | "观仓中鼠，食积粟，居大庑之下，不见人犬之忧" |
| 厕中鼠 | 李斯列传 | "见吏舍厕中鼠食不絜，近人犬，数惊恐之" |
| 沐猴而冠 | 项羽本纪 | "人言楚人沐猴而冠耳，果然" |
| 项庄舞剑 | 项羽本纪 | 鸿门宴项庄以剑舞名欲刺沛公 |
| 匹夫之勇 | 淮阴侯列传 | "项王喑噁叱咤，千人皆废……此特匹夫之勇耳" |
| 妇人之仁 | 淮阴侯列传 | "项王见人恭敬慈爱……此所谓妇人之仁也" |
| 千金之子不死于市 | 货殖列传、袁盎列传 | "千金之子，不死於市" |
| 一饭之德必偿，睚眦之怨必报 | 范雎列传 | "一饭之德必偿，睚眦之怨必报" |
| 分一杯羹 | 项羽本纪 | "必欲烹而翁，则幸分我一桮羹" |
| 一沐三捉发，一饭三吐哺 | 鲁周公世家 | "我一沐三捉发，一饭三吐哺，起以待士" |

**执行方式**：逐条创建 `concept` 类型 wiki 页面，包含原文引文、典故解析、哲学内涵。

- [ ] 仓中鼠（concept 页）
- [ ] 厕中鼠（concept 页）
- [ ] 沐猴而冠（concept 页）
- [ ] 项庄舞剑（concept 页）
- [ ] 匹夫之勇（concept 页）
- [ ] 妇人之仁（concept 页）
- [ ] 千金之子不死于市（concept 页）
- [ ] 一饭之德必偿（concept 页）
- [ ] 分一杯羹（concept 页）
- [ ] 一沐三捉发一饭三吐哺（concept 页）

---

### 📖 《读史记十表》OCR 整理（阶段一完成，阶段二待启动）

**记录日期**：2026-04-22
**背景**：`corpus/shiji/读史记十表.txt`（四库本 OCR）无标点、有 OCR 噪声、影印排版需重建。

**阶段一：句读 + 排版（已完成 2026-04-22）**：
- ✅ 方法论沉淀：[SKILL_01i OCR影印古籍句读排版](skills/SKILL_01i_OCR影印古籍句读排版.md)
- ✅ 全书十卷 + 提要 + 总论完整句读与 Markdown 排版：[corpus/shiji/读史记十表.md](corpus/shiji/读史记十表.md)
- ✅ OCR 可疑字全书扫描报告（"防"字 13 种语义 + 零星单字）：[logs/curation/reports/读史记十表_OCR可疑字.md](logs/curation/reports/读史记十表_OCR可疑字.md)
- ✅ 项目复盘：[logs/curation/reports/读史记十表_整理复盘.md](logs/curation/reports/读史记十表_整理复盘.md)

**阶段二：多版本互校订正 + 工具化（待启动）**：
- [ ] 找到《读史记十表》点校本或其他四库翻印本，逐条订正 OCR 可疑字
- [ ] 表格正文从影印 PDF 还原（OCR 丢失的年表列）
- [ ] 工具化：`scripts/curation/verify_ocr_preserve.py`（字符完整性）、`clean_ocr_raw.py`（阶段 1 清洗）、`fix_quotes_scoped.py`（作用域栈引号修复）
- [ ] HTML 渲染器接入（让 `.md` 出现在站内目录）

**关联 Skill**：SKILL_01i（方法论，含 OCR 错字归纳/作用域栈算法/LLM 偏差前置提示）/ 01f（标点规范主文档）/ 01b（互校订正）

---

### 📝 全库白话翻译 v2 重译（Phase 6 pilot 已通过评估）

**记录日期**：2026-04-22
**背景**：基于 hunterhug 段译 + 白话史记外部白话双参考做 v2 提示词迭代。pilot 评估 002/067 两章：067 年龄"岁"误译 23 处全部修复，与 hunterhug 相似度 +2.5pt，所有指标无退化。

**任务**：用 v2 提示词（当前 [SKILL_01h 白话翻译](skills/SKILL_01h_白话翻译.md)）全量重译 130 章，替换现有 `doc/translation/`。

**工作量估算**：
- Agent 并行：~6-10 小时 agent 时间
- 人工抽检：10-20 章重点章节（含 067/087/129 等已知高缺陷章）
- 下游重跑：`sync_translation_disambig.py` → `translate_surface.py` → `generate_translation_json.py`

**执行步骤**：
1. 按章分批（参考 2026-04-22 首次 130 章翻译方法，超长章 006/007/008/128/130 分 part）
2. 输出到 `doc/translation_v2/`，与 v1 共存以便 diff
3. 对每章跑 `scripts/evaluate_v2.py NNN` 自动指标对比
4. 抽检无退化后，覆盖 `doc/translation/`，重跑下游
5. 记录到 `doc/translation_quality/v2_fullrun_log.md`（见下方附注）

**关联文档**：
- SPEC：[doc/spec/SPEC_白话翻译质量提升.md](doc/spec/SPEC_白话翻译质量提升.md)
- 分析与评估：[doc/translation_quality/](doc/translation_quality/)
  - v2_分析.md / v2_diff.md（hunterhug 派生规则）
  - v2b_白话史记补充.md（白话史记补充规则）
  - v2_evaluation.md / v2_evaluation_summary.md（pilot 回归指标）

**依赖**：建议先完成"纪年消歧"与"完整性修复"后再跑（避免 v2 重译与标注更新撞车）。

---

### 🗓️ 纪年消歧到公元年份（实体标注）

**记录日期**：2026-04-16
**触发**：第四轮按章反思 004_周本纪 纪年消歧专项

**当前状态**：004 章已 pilot 79 处 `〖%XX年|纪年〗`（在位/编年纪年的显式标注），其余章节默认不显式标。

**最终目标**：所有 `〖%XX年|纪年〗` 应进一步消歧到**具体公元年份**，便于跨章时间线对齐与机器年代检索。
- 形式待定：`〖%XX年|纪年:前BCE〗` 或 `〖%XX年|前BCE〗`
- 范围：130 章全部含纪年的标注

**为何现在不做**：
- 任务量大（全书数千处），需先稳定 `|纪年` 标注本身
- 公元换算需可靠的王年表/即位年表数据源
- 标签格式需先与 `|时长`/`|年龄` 体系协调

**前置任务**：
1. 完成全书 `|纪年` 显式化（参考 004 pilot）
2. 整理王年表数据源（《史记》本纪/年表 + 现代工具书）
3. 设计标签格式（与既有消歧体系兼容）

---

### 🔍 常规优先任务

- [ ] **人物生卒年反思**：四轮反思推断人物生卒年区间（span 格式），记录证据链和置信度（详见 [SKILL_07a](skills/SKILL_07a_人物生卒年推断.md) / [spec](doc/spec/PLAN_人物生卒年反思.md)）
  - 第一轮：从原文提取年龄/在位年数证据（正则扫描"生X岁"/"立X年"等）
  - 第二轮：从事件索引获取锚点事件年份（即位、卒、出奔等）
  - 第三轮：计算生卒年区间（按方法1→5优先级，记录证据链和置信度）
  - 第四轮：亲属关系交叉约束验证（父卒<子生、兄弟年龄差<40年）
  - 数据升级：升级现有 `person_lifespans.json` 为区间格式（含置信度和证据链）
  - 试点验证：对前 5 章本纪人物试点推断（验证方法）
  - 生成推断报告：每人附带证据链+置信度+矛盾标记
  - 传说时代特殊处理：标记 legend，区间≥100 年
  - **完成后更新谥号索引**：将生卒年区间同步到 `shihao_index.json` 和 HTML 页面

- [ ] **反常推理**：检测违反常识/制度/逻辑的单条事实，挖掘值得深究的历史异常点（详见 [SKILL_07c](skills/SKILL_07c_反常推理.md)）
  - 建立 `anomaly_report.json` 初始文件（从矛盾案例库迁移）
  - 优先处理六个高密度场景：长平降卒数字、秦始皇无皇后、刘邦年龄、吕后称制、项羽破釜沉舟、商鞅徙木立信
  - 编写数字异常自动扫描脚本 + LLM 批量评估流水线

- [ ] **姓氏推理**：为先秦人物建立姓/氏/名/字记录，厘清"同姓"语义（详见 [SKILL_07b](skills/SKILL_07b_姓氏推理.md) / [spec](doc/spec/PLAN_姓氏制度.md)）
  - Round 1：创建 `xing_index.json` + 直接提取 20 个高置信度人物写入 `person_xingshi.json`
  - Round 2：邦国推理（040 楚世家、084 屈原列传优先）
  - Round 3–4：氏族推理 + 父系链传播
  - 标注层：更新 SKILL_03a，增加 `〖&X|姓〗` / `〖&X|氏〗` 子类型

- [ ] **实体标注反思管线**（大部分完成，余下零散）
  - ✅ 人名分类多轮反思（1832→3682 人，未分类 1461→1319）
  - ✅ 官职分类第一～六轮反思（18→21 类，加级别维度）
  - ✅ 地名分类第一～七轮反思（加梯度策略 + 置信度 UI + 白名单审计）
  - ✅ 邦国分类首轮落地（11 类体系 + 侯国并入邦国，204 条 100% 分类）
  - ✅ 谥号公消歧下游重建（年表 ruler 改消歧格式）
  - ⏳ 剩余：按章实体反思的常态化运行（遗漏/消歧/别名的轮次扫描）
  - ⏳ 跨类型联合反思（如"人名-官职"同指、"谥号-人名"消歧链）

- [ ] **年份时间消歧语法标注**：将 `year_ce_map.json` 中的 6655 条年份→公元年映射写回到 130 章 markdown 文件
  - 前提：当前 year_ce_map.json 已包含 76.87% 覆盖率的年份消歧结果
  - 目标：在原文中添加消歧语法标注（如 `〖%元年|-201〗`）
  - 方法：编写脚本读取 year_ce_map.json，定位到对应章节/段落/文本，插入消歧标注
  - 验证：确保标注后的文本仍符合标注铁律（不改变原文字符）
  - 详见：[SKILL_03g_时间实体消歧.md](skills/SKILL_03g_时间实体消歧.md)

- [ ] **PN 映射表更新派生产物溯源**：基于已建立的 PN 映射表（`data/pn_mapping_complete.json`），更新所有派生产物中的 PN 引用
  - 前提：已完成 PN 规范化（commit 6b20e096 → 74032d6），建立了 1322 条映射（覆盖 73 章）
  - 优先范围：
    - [ ] 更新 `docs/entities/timeline.html` 中的 375 处 PN 引用（44.2% 已匹配，28.4% 需更新）
    - [ ] 更新 `kg/events/` 相关文件中的 PN 溯源引用
    - [ ] 检查并更新其他包含 PN 引用的派生文件（索引页面、关系图谱等）
  - 工具脚本：
    - `scripts/update_timeline_pn.py` - 自动更新 timeline.html
    - `scripts/verify_timeline_pn_content.py` - 验证更新正确性
  - 验证标准：所有 PN 引用指向的内容与原文匹配（100% 内容一致性）
  - 数据源：[data/pn_mapping_complete.json](data/pn_mapping_complete.json) / [README](data/PN_MAPPING_README.md)

### 🔊 多音字分析任务

**背景**：已建立 21 个高/中频多音字的上下文模板，其中 5 个已完成标注版（王、为、与、将、占）。特殊读音词表 [`docs/data/special-pronunciation.json`](docs/data/special-pronunciation.json) 活跃维护中（2026-04-20 更新，1197 行）。实际产物位于 [`data/pronunciation_templates/`](data/pronunciation_templates/)。

- [ ] **【优先级1 - 最高】完成剩余高频多音字标注（5 个）**
  - 范围：使(2,444)、相(2,076)、行(1,495)、长(1,121)、数(1,021)
  - 已完成 annotated：王(8,209)、为(7,386)、与(2,660)、将(2,417)+ 占（额外）
  - 模板已自动生成于 `data/pronunciation_templates/*_pronunciation.md`
  - 工作量：每个字约 2-4 小时人工审核（读音分类、频率统计、词表方案、例句补充）
  - 产出：`data/pronunciation_templates/X_pronunciation_annotated.md`（参考 `王_pronunciation_annotated.md`）

- [ ] **【优先级2 - 高】补充特殊读音词表**
  - 目标：为高频但词表覆盖不足的多音字补充词条
  - 范围：
    - 使(2,444 次) - 0 条 → 补充"使者"等
    - 间(454 次) - 0 条 → 补充"离间"、"反间"等
    - 好(359 次) - 0 条 → 补充"好学"、"好色"、"好战"等
    - 与(2,660 次) - 1 条 → 补充更多词条
    - 为(7,386 次) - 1 条 → 补充更多词条
  - 预计新增词条：20-30 条
  - 产出：更新 `docs/data/special-pronunciation.json`

- [ ] **【优先级3 - 中】扩展到更多多音字**
  - 目标：统计并分析中低频多音字（出现次数 <1000 但 >50 次）
  - 范围：过、还、重、应、便、宿、处、差、殷、系、解、种、称、从、冠、当、度、分、复、供、假、禁、觉、落、没、蒙、难、宁、强、塞、舍、胜、识、恶、要、曾、正、只、属等 50+ 个
  - 方法：使用 `scripts/analyze_polyphone_statistics.py` 批量生成草稿
  - 产出：草稿文档 + 统计报告

**工具脚本**:
- `scripts/analyze_polyphone_statistics.py` - 自动化统计分析
- `scripts/polyphone_list.py` - 多音字列表定义

**参考文档**:
- [data/pronunciation_templates/](data/pronunciation_templates/) - 多音字上下文模板库
- [skills/SKILL_01d_正音与拼音标注.md](skills/SKILL_01d_正音与拼音标注.md) - 设计原则

---

## 📋 待执行重构任务

### 🗂️ 结构化知识库导出

**任务**：生成标准格式的知识库汇总文件，便于机器读取和跨平台使用

**输出格式**：
- [ ] **JSON 格式**：`kg/export/shiji_kb.json` - 包含实体、事件、关系、本体的完整结构
- [ ] **YAML 格式**：`kg/export/shiji_kb.yaml` - 人类可读性更强的层级结构
- [ ] **RDF/Turtle 格式**：`kg/export/shiji_kb.ttl` - 语义网标准格式，支持 SPARQL 查询

**数据结构设计**：
- 实体索引（entity_index.json）→ 统一实体表
- 动词索引（verb_index.json）→ 动词表
- 事件索引（130 章事件）→ 统一事件表
- 事件关系（event_relations.json）→ 关系表
- 本体（ontology/）→ 类型层级和属性定义
- SKU（knowledge-units/）→ 知识单元表

**用途**：
- 支持外部工具导入（如 Neo4j、GraphDB 等）
- 便于跨项目引用和二次开发
- 提供 API 友好的数据接口
- 支持学术研究数据集发布

**参考规范**：
- JSON-LD for linked data
- Schema.org vocabulary
- Dublin Core metadata

**优先级**：中（可作为 2026 Q2 任务）

---

### 🗄️ 目录结构重构（归档·已作废）

**状态**：规划已过时，不再推进。

**实际演化**：
- 核心诉求"语料目录统一"已于 2026-04-05 commit [458a6323](https://github.com/baojie/shiji-kb/commit/458a6323) 以更轻量的方式完成：`archive/` → `corpus/archive/` + 路径常量管理
- 阅读端的简/繁双轨需求已于 2026-04-22 commit [4f434fd3](https://github.com/baojie/shiji-kb/commit/4f434fd3) 通过"简体标注主 + 繁体点校本副"解决，不再需要 `final/` 目录与底本改进流程
- 原 SPEC 文档 `docs/SPEC_directory_restructure.md` 随规划退场一并移除

**原规划中未采用的子项**（仅存档，不再作为 TODO）：`curation/` 三级切分、`final/` 底本终稿、`scripts/mapping/`（繁简映射系统）、`scripts/improvements/`（标点/段落/空格归一化流水线）

**若未来重新需要**：重写 SPEC，不建议复用旧文档的设计。

---

## 📊 文档维护任务

### CHANGELOG commit ID 完整性审查与补充

**发现日期**: 2026-04-03

**问题描述**：
- 审查发现 CHANGELOG.md 中存在大量 commit ID 遗漏
- 总计 30 个日期需要补充 commit ID，涉及 400+ 个 commits 未被记录
- 最严重的日期：2026-03-18 (36 个)、2026-03-29 (23 个)、2026-02-07 (22 个)

**处理策略**（待决定）：
- **选项 A**: 保持现状 - CHANGELOG 作为高层次总结，不必包含每个 commit ID
- **选项 B**: 重点补充 - 只为重要日期（2026-03 至 04 月）补充 commit ID
- **选项 C**: 自动化重建 - 编写脚本从 git 历史自动生成完整的 CHANGELOG

**审查工具**：
- 脚本位置：`scripts/audit_changelog_commits.py`
- 使用方法：`python scripts/audit_changelog_commits.py`

**优先级**: 低（不影响项目功能）

**决策人**: @baojie

---

### Wiki 消歧义页扫描与整理（Housekeeping）

**发现日期**: 2026-04-24

**任务描述**：
扫描 wiki/public/pages/ 中需要消歧义处理的页面，识别同名但含义不同的条目，统一加 hatnote 或建消歧义页。

**铁律（必须遵守）**：
- ❌ **禁止删除现有页面的已有内容**（引文、君主表、事件等）
- ✅ 主要含义保留原页 + 在顶部加 blockquote 消歧义提示（hatnote）
- ✅ 次要含义另建新页（如 X邑、X地、X（人名）等）
- ✅ 只有当原页是纯 redirect 或空页时，才可直接改为 `type: disambiguation`

**Hatnote 模板**：
```
> **消歧义**：此页讨论 X（主要含义）。关于 Y，见[[Y页面]]。
```

**已处理示例**：
- `商` → type: state（朝代），顶部 hatnote 指向 `商邑`（秦地名）和 `商於`
- `商邑` → 新建 type: place（秦国商鞅封地）

**待扫描范围**：
- 所有 `type: redirect` 页面——被重定向的词是否有其他含义？
- 高频单字/双字词（齐、燕、赵、楚、韩、魏、陈、宋、卫、蔡等）——是否兼指地名和国名？
- 人名与地名重叠（如"蒙"既是人名又是地名）

**优先级**: 低（日常 housekeeping，butler 空闲时处理）

---

## ✅ 近期关闭的 Issue / 里程碑归档

### 2026-04-22（二）：《读史记十表》OCR 整理阶段一完成

**阶段一一次性交付**：
- OCR 影印古籍方法论沉淀为 [SKILL_01i](skills/SKILL_01i_OCR影印古籍句读排版.md)（含"防"字 13 种语义、引号作用域栈算法、LLM 偏差前置提示）
- 《读史记十表》全书十卷 + 提要 + 总论完整句读与 Markdown 排版
- OCR 可疑字全书扫描
- 项目复盘（时间线、未完成事项）
- SKILL_01 主文档更新，新增 01i 引用；01i 与 01f 边界表更新

**产物**：
- [corpus/shiji/读史记十表.md](corpus/shiji/读史记十表.md)（10 万字级完整整理）
- [logs/curation/reports/读史记十表_OCR可疑字.md](logs/curation/reports/读史记十表_OCR可疑字.md)
- [logs/curation/reports/读史记十表_整理复盘.md](logs/curation/reports/读史记十表_整理复盘.md)

### 2026-04-22（一）：白话翻译与三家注落地

- [#13](https://github.com/baojie/shiji-kb/issues/13) 注释 — **已关闭**
  - ✅ 三家注（集解/索隐/正义）行下展示 + 段落锚定（[bf9a1fdf](https://github.com/baojie/shiji-kb/commit/bf9a1fdf)）
  - ✅ 白话翻译 130 章全库落地（[1bbe93ad](https://github.com/baojie/shiji-kb/commit/1bbe93ad) / [93cd6337](https://github.com/baojie/shiji-kb/commit/93cd6337)）
- [#16](https://github.com/baojie/shiji-kb/issues/16) 【建议】加入白话文 — **已关闭**
  - ✅ 130 章白话翻译落地 + 外部语料入库（[1bbe93ad](https://github.com/baojie/shiji-kb/commit/1bbe93ad) / [93cd6337](https://github.com/baojie/shiji-kb/commit/93cd6337) / [4f434fd3](https://github.com/baojie/shiji-kb/commit/4f434fd3)）
  - 规范：[SKILL_01h_白话翻译.md](skills/SKILL_01h_白话翻译.md) / [SPEC_白话翻译质量提升.md](doc/spec/SPEC_白话翻译质量提升.md)

### 2026-04-16 ～ 04-22：大规模反思与标注基础设施

（72 个 commit，主要工作归类如下）

**实体标注反思（分类树化）**：
- 人名分类：1832 → 3682 人，4 列结构 + 时序排序（[65d2ee59](https://github.com/baojie/shiji-kb/commit/65d2ee59) / [600e6aae](https://github.com/baojie/shiji-kb/commit/600e6aae) / [2eb14ebd](https://github.com/baojie/shiji-kb/commit/2eb14ebd) / [dc6a5557](https://github.com/baojie/shiji-kb/commit/dc6a5557) / [6bfcc671](https://github.com/baojie/shiji-kb/commit/6bfcc671)）
- 官职分类：18 → 21 类 + 级别分类（[f23377bd](https://github.com/baojie/shiji-kb/commit/f23377bd) / [d6781d49](https://github.com/baojie/shiji-kb/commit/d6781d49) / [188b624e](https://github.com/baojie/shiji-kb/commit/188b624e) / [2a3f4580](https://github.com/baojie/shiji-kb/commit/2a3f4580)）
- 地名分类：四-七轮反思，梯度策略 + 置信度 UI（[d43be851](https://github.com/baojie/shiji-kb/commit/d43be851) / [367443d6](https://github.com/baojie/shiji-kb/commit/367443d6) / [9503f8e0](https://github.com/baojie/shiji-kb/commit/9503f8e0)）
- 邦国分类：11 类体系 + 侯国并入邦国，204 条 100% 分类（[b77dbce5](https://github.com/baojie/shiji-kb/commit/b77dbce5)）
- 谥号公消歧：年表 ruler 改消歧格式，HTML/索引全库刷新（[d2e9dd70](https://github.com/baojie/shiji-kb/commit/d2e9dd70)）

**新标注层与方法论**：
- 修辞标注层 `〘※〙`（成语等）首次引入 + HTML 朱批圈点渲染（[5e2f528c](https://github.com/baojie/shiji-kb/commit/5e2f528c) / [7f2364ce](https://github.com/baojie/shiji-kb/commit/7f2364ce) / [a1b42e38](https://github.com/baojie/shiji-kb/commit/a1b42e38) / [42f55918](https://github.com/baojie/shiji-kb/commit/42f55918)）
- 成语识别工作流 + 双轨数据架构（[c637dcd0](https://github.com/baojie/shiji-kb/commit/c637dcd0)）
- SKILL_03e 按类型反思重构为父子结构（[349d970a](https://github.com/baojie/shiji-kb/commit/349d970a)）
- SKILL_08f 置信度函数设计 + 按章反思规律库 v2（[7df4ada9](https://github.com/baojie/shiji-kb/commit/7df4ada9)）
- 本地 skill `/msg` 生成 git 缓存区中文提交消息草稿（[552f6c05](https://github.com/baojie/shiji-kb/commit/552f6c05)）

**阅读与数据基础设施**：
- 年表反思：014 / 015 深度消歧与漏标补全（[c04cb210](https://github.com/baojie/shiji-kb/commit/c04cb210) / [7c3578b3](https://github.com/baojie/shiji-kb/commit/7c3578b3)）
- 年表 CSS 路径与 `|` 分隔冲突修复（[d018ab3f](https://github.com/baojie/shiji-kb/commit/d018ab3f) / [8d6f96d8](https://github.com/baojie/shiji-kb/commit/8d6f96d8)）
- 全库知识索引重建（[f6da11a8](https://github.com/baojie/shiji-kb/commit/f6da11a8) / [d6782142](https://github.com/baojie/shiji-kb/commit/d6782142)）
- 读音词典补 10 条（[987ab5a8](https://github.com/baojie/shiji-kb/commit/987ab5a8)）
- 实体标注统计目录规整 + v4.1 报告（[15acfccf](https://github.com/baojie/shiji-kb/commit/15acfccf)）

### 2026-04-16：部分完成

- [#41](https://github.com/baojie/shiji-kb/issues/41) 全文模糊搜索功能 — **模糊搜索已追加**（[1c05e2f1](https://github.com/baojie/shiji-kb/commit/1c05e2f1)；仍保持 Open 以评估按实体类型/章节筛选）
  - ✅ 全文检索：客户端子串匹配、空格分词 AND、中文友好
  - ✅ UI：首页下拉（30 条）+ `search.html` 全部结果页（50 条/页 + 分页）
  - ✅ 构建脚本：`scripts/build_search_index.py`（剥离标注 + 按 Purple Number 切段）
  - ✅ **新增**：别名模糊搜索落地 + 搜索系统 SPEC 化 + 发布脚本挂入索引构建
  - ❌ 未做：按实体类型筛选、按章节筛选

---

## 📝 早期迁移记录（2026-03-30）

### 北大考古学生反馈 (Issue #85)

根据北京大学考古文博学院师生的课堂反馈，新建和增补以下 Issues：

**新建 Issues (3 个)**:
- [#87](https://github.com/baojie/shiji-kb/issues/87) 文本版本体系：版本信息、注释、异文集成展示
- [#88](https://github.com/baojie/shiji-kb/issues/88) 图文对照：原始典籍页面与数字文本并列展示
- [#89](https://github.com/baojie/shiji-kb/issues/89) 官制词典：辅助理解复杂官制体系

**增补到现有 Issues (2 个)**:
- [#41](https://github.com/baojie/shiji-kb/issues/41) 全文搜索功能 - 增补模糊搜索改进需求
- [#60](https://github.com/baojie/shiji-kb/issues/60) AI 问答 (RAG) - 增补问题驱动数据库建设需求

**已完成 (1 个)**:
- [#17](https://github.com/baojie/shiji-kb/issues/17) 开关面板 - ✅ 语法高亮开关已实现

**社区反馈文档**: [resources/community/2026-03-30_北大考古学生反馈_issue85.md](resources/community/2026-03-30_北大考古学生反馈_issue85.md)

### 功能建议大迁移

从 TODO.md 迁移 29 个任务到 GitHub Issues（#35 ~ #63），保持 TODO 专注于核心开发任务。详细列表见 [GitHub Issues](https://github.com/baojie/shiji-kb/issues)。

### 已完成任务归档

2026-03-18 ～ 2026-03-21 间的 16 个已完成任务（#64 ～ #84），以及 #53 #47 #54 #51 四个功能完成确认，详情见 [GitHub Issues (closed)](https://github.com/baojie/shiji-kb/issues?q=is%3Aissue+is%3Aclosed)。

---

## 🛠️ W13 待实现脚本（史记全文覆盖查验）

> Skill 设计见 [SKILL_W13](skills/SKILL_W13_史记全文覆盖查验.md)

- [ ] `wiki/scripts/butler/insight_scan.py` — W14 自动洞察扫描（cooccur/overlap/isolation 三模式），生成 insight_queue.md 候选
- [ ] `wiki/scripts/butler/build_sentence_index.py` — 从 chapter_md/*.tagged.md 分句，生成 `wiki/logs/butler/sentence_index/` 目录（130 个 JSONL 文件）
- [ ] `wiki/scripts/butler/build_coverage_map.py` — 读 sentence_index + wiki pages，生成 `wiki/logs/butler/coverage_map/`（quote/para/entity 三层覆盖信号）
- [ ] `wiki/scripts/butler/coverage_report.py` — 汇总统计、分章覆盖率、输出 gap 缺口队列

---

## 💡 Idea 池

- 除了段落编号，其实所有的东西（实体、事件、事实、过程……）都需要 ID。要写一个 ID 规范文档
- 显示人物关系的图谱
- 某个地名当时的地图
- 写一个迁移指南，用另外一本书做例子，演示清楚怎么把现在的 SKILL 迁移到另一本书。这个迁移指南应该有一个 skill（给 agent 看）和一个配套的 doc（给人看）。实现 META 13 的实例化
- 校勘下加一个子 skill 审音和拼音标注
- OCR 影印古籍批量处理工具链：gj.cool API + 字符完整性脚本（SKILL_01i 延伸）

---

## 🏷️ 校勘双任务（2026-03-29 锚点更新版）

> 原「三大任务」中的"目录重构"已由 commit 458a6323 以更轻量方式完成，见上方归档记录。剩余两项仍是底本终稿的必经路径：

1. **完整性修复（[SKILL_01a](skills/SKILL_01a_标注完整性维护.md)）**：因实体反思 v3 曾破坏原文，需一次系统修复；可借助 `scripts/lint_text_integrity.py` 全量扫描
2. **多版本互校（[SKILL_01b](skills/SKILL_01b_多版本互校底本.md)）**：按 SKILL_01b 规范完成 130 章互校，产出底本终稿；点校本繁体语料已就位

---

更多请看 [GitHub Issues](https://github.com/baojie/shiji-kb/issues)
