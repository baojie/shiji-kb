# 更新日志 (Changelog)

本文档记录《史记》知识库项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## 项目整理：目录重组与文档更新 - 2026-03-18

### 更改 (Changed)

- **目录结构重组**：
  - 移动 `sections_data.json` → `kg/structure/data/sections_data.json`
  - 创建 `kg/structure/` 目录存放文本结构元数据
  - 更新6个相关脚本的路径引用（scripts/section_*.py, temp/tools/fix_sections*.py）

- **文档完善**：
  - 新增 `kg/structure/README.md` — 文本结构数据说明（约1500个小节，110章）
  - 更新 `kg/README.md` — 添加structure目录条目
  - 更新 `generate_all_chapters.py` — 修正消歧/年份映射脚本路径
    - `scripts/disambiguate_names.py` → `kg/entities/scripts/disambiguate_names.py`
    - `scripts/build_year_map.py` → `kg/events/scripts/build_year_map.py`

- **IDEA 文档更新**：
  - 新增 Koselleck概念史方法论到 `ref/IDEA.md`
  - 核心思路：概念版本化、语义关系层、概念-人物-文本三角结构
  - 应用到《史记》：已有2,072次 `〖_思想/概念〗` 标注可扩展为"语义演化地图"

### 修复 (Fixed)

- 修正HTML生成管线中预处理脚本路径错误（之前会跳过消歧和年份映射步骤）

---

## 第一轮实体反思：全书130章修正1913处（已提交） - 2026-03-17

### 修复 (Fixed)

- **章节标注质量提升**：对013-130章（118章）执行按章反思，修正标注错误约756处
  - 013 三代世表：20处（制度→典籍/思想，官职→身份，庙号消歧）
  - 014-030 年表书传（17章）：14处（制度→思想，仁义/礼义/道德等）
  - 031-120 世家列传（90章）：526处（官职→身份650次，时长去标400次）
  - 121-130 列传（9章）：196处（六经传习54处，时长60处，刑法5处）

- **高频问题修正**（全书130章总计~1913处）：
  - 官职→身份：~650次（天子/诸侯/今王/单于/王者等）
  - 时长去标注：~400次（X岁/X年/X月/万岁等）
  - 制度→思想：~200次（仁义/礼义/道德/五德等）
  - 制度→典籍：~150次（诗/书/礼/乐/易/春秋等）
  - 制度→刑法：~100次（五刑/肉刑/弃市/族诛等）

### 新增 (Added)

- `doc/entities/第一轮实体反思报告.md` — 全书130章反思详细记录
  - 总统计：1913处修正，高频问题TOP5，验证结果
  - 各章详细修正明细（001-130）
  - 章节特有发现和新规律汇总

- `scripts/batch_reflect_031_120.py` — 批量反思处理脚本

### 更改 (Changed)

- `skills/SKILL_03c_按章反思.md` — 新增4条反思规律
  - 庙号/谥号的消歧标注（013章首发现）
  - 褚先生等补记撰述者标注（013章首发现）
  - 学派vs思想概念区分（014-030章系统性发现）
  - 六经传习语境区分（121章首发现）

- **章节文件修正**（98个文件）：
  - `chapter_md/013_三代世表.tagged.md` 至 `chapter_md/130_太史公自序.tagged.md`
  - 所有修正通过原文完整性验证（100%保持原文，仅修改标注符号）

### 验证 (Verified)

- ✅ 原文完整性：100%保持（只改标注符号，不改原文字符）
- ✅ 格式验证：100%通过（无旧格式、无破损）
- ✅ 特殊章节抽查：110匈奴列传（141处）、122酷吏列传（78处）等重点章节人工复核

---

## 内联消歧语法 v2.7：扩展到所有实体类型（未提交） - 2026-03-16

### 新增 (Added)

- `scripts/test_inline_disambig.py` — 内联消歧语法端到端测试脚本（15项断言：strip_markup/remove_all_tags/convert_entities，全部通过）

### 修复 (Fixed)

- `scripts/lint_text_integrity.py` — `strip_markup()` 修复 `|` 残留 bug：`〖@台|吕台〗` → 原来错误脱标为 `台|吕台`，现在正确输出 `台`
- `kg/entities/scripts/validate_tagging.py` — `remove_all_tags()` 同上修复
- `scripts/lint_markdown.py` — 生物类型 pattern 中 `〖+` 里的 `+` 被误解为正则量词，修正为 `〖\+`

### 更改 (Changed)

- `render_shiji_html.py` — 新增12条非人名类型消歧 pattern（器物/官职/地名/时间/氏族/邦国/制度/族群/身份/天文/生物/数量），全部13种 `〖TYPE〗` 类型均支持 `〖TYPE 显示名|规范名〗` 语法，渲染输出 `data-canonical` 属性
- `skills/SKILL_03a_实体标注.md` — v2.7 节：内联消歧扩展到13种类型，含完整示例表
- `skills/SKILL_03b_实体消歧.md` — 内联消歧节：补充非人名消歧示例和各类型典型场景
- `skills/SKILL_09a_认知辅助阅读器.md` — 渲染管线更新："内联消歧人名" → "内联消歧（所有实体类型）"
- `doc/spec/标注格式规范.md` — 内联消歧格式节：列出13种类型的示例表（v2.7）

---

## 事实发现 SKILL + 姓氏推理规划（未提交） - 2026-03-16

### 新增 (Added)

- `skills/SKILL_05c_事实发现.md` — 原子事实三元组抽取工作流
  - 事实定义：1–3个三元组，独立于事件（叙事单元）和关系（持久结构）
  - SPO 全用汉字，不设谓词 schema；ctx（context）对象承载时间/地点/场合等背景条件，可扩展任意汉字键值
  - 规模估算：全库约 70,000–120,000 条事实，十表密度最高
  - 多轮抽取：规则→句法框架→LLM→验证去重
- `skills/SKILL_07b_姓氏推理.md` — 先秦人物姓/氏推理工作流（多轮迭代：直接提取→邦国推理→氏族推理→父系传播→验证；7条推理规则 R1–R7）
- `doc/spec/姓氏制度.md` — 先秦姓氏制度背景规范（姓/氏区分、氏的三大来源、主要姓族对照表、数据模型）
- `kg/entities/scripts/prompt_template_姓氏推理.md` — 姓氏推理 Agent 提示词模板（参数化 round/scope/input_files，含三个调用示例）

### 更改 (Changed)

- `skills/SKILL_05_关系构建.md` — 子工序索引表增加 05c 条目
- `skills/SKILL_07_逻辑推理.md` — 子工序索引表增加 07b 条目
- `TODO.md` — 姓氏推理提升为近期优先；事实发现整理入数据与内容

---

## 实体反思：内联消歧语法 + 006-010章标注修正 ([a788c574](https://github.com/baojie/shiji-kb/commit/a788c574)) - 2026-03-16

### 新增 (Added)

- **内联消歧语法**：标注中可直接指定消歧目标，形如 `〖@张良|韩相张良〗`，无需依赖外部 aliases 文件
- 006-010章（秦始皇/项羽/高祖/吕太后/孝文本纪）实体反思完成，消歧修正与别名补充

---

## 纪年系统重建 + 实体索引更新 ([cebce93a](https://github.com/baojie/shiji-kb/commit/cebce93a) / [fbe735a4](https://github.com/baojie/shiji-kb/commit/fbe735a4) / [39660102](https://github.com/baojie/shiji-kb/commit/39660102)) - 2026-03-15

### 更改 (Changed)

- **纪年系统**：重建在位纪年→公元年映射，timeline数据大幅扩充（历代君主在位年可视化）
- **SKILL文档**：年份消歧、年代推断相关 SKILL 同步更新
- **实体索引**：年表数据重建，全量HTML重新生成

---

## 多章标注修正 + lint系统扩展 ([c5386c0e](https://github.com/baojie/shiji-kb/commit/c5386c0e) / [9cc85ae7](https://github.com/baojie/shiji-kb/commit/9cc85ae7) / [ed3c45f8](https://github.com/baojie/shiji-kb/commit/ed3c45f8) / [3275308c](https://github.com/baojie/shiji-kb/commit/3275308c) / [b03600dd](https://github.com/baojie/shiji-kb/commit/b03600dd)) - 2026-03-15

### 更改 (Changed)

- **30章批量标注修正**（两轮）：消歧修正、符号格式统一
- **lint系统扩展**：新增检测规则，130章实质差异归零（lint完整性修复）
- **001-003章修正**：五帝本纪标签错误修复、殷本纪标注修正

---

## 实体反思 SKILL 重构 ([9508de3f](https://github.com/baojie/shiji-kb/commit/9508de3f) / [28266b41](https://github.com/baojie/shiji-kb/commit/28266b41) / [4dc02f54](https://github.com/baojie/shiji-kb/commit/4dc02f54)) - 2026-03-15

### 新增 (Added)

- **新增 SKILL_02d/02e/02f/05b**：扩展实体标注和事件分析方法论体系
- **实体反思SKILL补充**：段落内一致性缺失模式检测

### 更改 (Changed)

- `SKILL_03c` 拆分为"按章反思"和"按类型反思"两个独立文档，责任边界更清晰
- 001/002章配套标注修正
- **研究方法总则** 同步更新

---

## v3.0/v3.1 SKILL体系重组 + 维基三家注 ([47fd9259](https://github.com/baojie/shiji-kb/commit/47fd9259) / [2b947ff4](https://github.com/baojie/shiji-kb/commit/2b947ff4) / [0b9a17ee](https://github.com/baojie/shiji-kb/commit/0b9a17ee) / [fdc5eaff](https://github.com/baojie/shiji-kb/commit/fdc5eaff) / [da71305c](https://github.com/baojie/shiji-kb/commit/da71305c)) - 2026-03-15

### 新增 (Added)

- **维基文库史记全文 + 三家注 epub 提取**：提取为 HTML，供校勘和注释标注使用
- **SKILL体系增强**：新增阅读器/游戏化 SKILL，合并 methodology 文档到 SKILL 体系，三Agent并行规划方案

### 更改 (Changed)

- **SKILL文档重组（v3.0）**：扁平命名结构迁移至 `skills/` 目录下分层编号体系（SKILL_XX_名称.md）；校勘修复
- **v3.1 标注文本校勘**：与维基文库版对照，540→386处差异（-154处修正）

---

## 通用分类树生成器 + v2.9 人物本体 ([298d3d1f](https://github.com/baojie/shiji-kb/commit/298d3d1f) / [798f4371](https://github.com/baojie/shiji-kb/commit/798f4371)) - 2026-03-15

### 新增 (Added)

- `kg/rdf/scripts/build_taxonomy.py` — **通用 TTL→分类树 MD 生成器**，替代人物专用脚本
  - 输入任意 OWL/RDF Turtle 文件，自动解析 owl:Class / rdfs:subClassOf / rdfs:label / :count
  - 支持 `--order` / `--unit` / `--max-show` 参数
  - 人物（130类/1821实例）和生物（20类/70实例）均验证通过
- `kg/rdf/biology_taxonomy.md` — 生物分类树（从 biology.ttl 自动生成）
- `doc/methodology/人物本体构建过程.md` — 人物本体构建全过程详细记录

### 更改 (Changed)

- **v2.9 人物本体+生物本体**：本体分类错误修正（帝王朝代/外邦汉人/吴楚国王等）；新增生物本体；Agentic Ontology 方法论整理
- `kg/rdf/scripts/build_person_taxonomy.py` 标记为已废弃

---

## Labs实验 + 文档整理 ([71bbf0c6](https://github.com/baojie/shiji-kb/commit/71bbf0c6) / [2294a7d9](https://github.com/baojie/shiji-kb/commit/2294a7d9) / [1eead04a](https://github.com/baojie/shiji-kb/commit/1eead04a) / [6ebca4ee](https://github.com/baojie/shiji-kb/commit/6ebca4ee) / [6cc97cdc](https://github.com/baojie/shiji-kb/commit/6cc97cdc)) - 2026-03-15

### 新增 (Added)

- `labs/` 目录：实验性内容统一归档（弋射说楚王排版实验、001章结构化数据等）
- **语义排版实验**：用五帝本纪做句间逻辑关系可视化原型（弹窗自动关闭交互修复）
- **逻辑推理案例**：SKILL_07 补充具体推理示例

### 更改 (Changed)

- **README精简**：过时文档链接清理，目录结构更新
- 文档路径引用同步更新

---

## v2.2 实体体系深度重构 ([73cfbf16](https://github.com/baojie/shiji-kb/commit/73cfbf16) / [d5967cdc](https://github.com/baojie/shiji-kb/commit/d5967cdc) / [1e6cf8e1](https://github.com/baojie/shiji-kb/commit/1e6cf8e1) / [4baba997](https://github.com/baojie/shiji-kb/commit/4baba997) / [53d9b987](https://github.com/baojie/shiji-kb/commit/53d9b987) / [7f768628](https://github.com/baojie/shiji-kb/commit/7f768628)) - 2026-03-14

### 更改 (Changed)

**1. 邦国/氏族/族群 三层分类体系确立**

- 🔄 **族群→氏族/邦国/官职/人名/地名**（195处）：31种氏族、14种邦国、9种族群君主称谓等重新归类
- 📊 结果：族群 231→168条，氏族 101→117条，邦国 156→161条
- 🔤 **三层分类原则**：邦国 `〖'〗`（政治体）/ 氏族 `〖&〗`（血缘宗族）/ 族群 `〖~〗`（文化族裔）

**2. 官职深度反思（2290处）**

- 🔄 **官职→时间（1497处）**：`〖;元年〗` → `〖%元年〗`
- 🔄 **官职→人名（17种，793处）**：高祖/沛公/汉王/太史公/项王/二世/武帝等皇帝专称归入人名

**3. 地名深度反思（60处）**

- 删除错误标注（无穷29处）、地名→时间/天文/器物/人名重分类；新增5组别名

**4. 身份类型恢复扩充**

- `〖#X〗` 身份实体类型恢复并扩充（4,297次标注）
- 实体索引页增加所有类型定义说明框

---

## v2.4 实体类型重命名（动植物→生物） ([963e49bb](https://github.com/baojie/shiji-kb/commit/963e49bb)) - 2026-03-14

### 更改 (Changed)

- `flora-fauna` 类型重命名为 `biology`，标记符号 `〘〙` → `〖+〗`，全书批量替换
- 配套系统性实体反思

---

## v2.5 标注完整性检查 ([f5b17c0f](https://github.com/baojie/shiji-kb/commit/f5b17c0f)) - 2026-03-14

### 新增 (Added)

- **lint脚本**：标注格式完整性检查，检测未闭合标签、符号残留等问题
- **实体词表**：配合lint建立基准词表
- 批量章节修复

---

## v2.6 实体深度清理 ([8c43461a](https://github.com/baojie/shiji-kb/commit/8c43461a) / [a1ea0950](https://github.com/baojie/shiji-kb/commit/a1ea0950)) - 2026-03-14

### 更改 (Changed)

- 身份类型进一步修正，国谥号人名重分类，旧格式标注（`@X@` / `$X$` / `%X%`）彻底消除
- `v2.6.1`：脚本正则表达式更新，适配旧格式→`〖TYPE X〗`批量转换

---

## v2.7 标注残留修复 ([c3e9b28a](https://github.com/baojie/shiji-kb/commit/c3e9b28a) / [88240e17](https://github.com/baojie/shiji-kb/commit/88240e17)) - 2026-03-14

### 更改 (Changed)

- **`validate_tagging.py` 重写**：更健壮的标注校验逻辑
- 单星号/双星号残留器物标注补全（25章）
- 001章「唯」字恢复（误删修复）

---

## v2.8 嵌套标签修复 + 数量实体 ([7f28fd6c](https://github.com/baojie/shiji-kb/commit/7f28fd6c)) - 2026-03-14

### 更改 (Changed)

- 嵌套实体标签修复（`〖@X〖;Y〗〗` 类型的解析问题）
- 跨句标注清理
- 数量实体标注补充
- 事件关系数据重建（反映标注修正后的最新实体）

---

## 排版实验 + 文档整理 ([17554cae](https://github.com/baojie/shiji-kb/commit/17554cae) / [f9db9c20](https://github.com/baojie/shiji-kb/commit/f9db9c20)) - 2026-03-14

### 新增 (Added)

- `doc/spec/排版实验_弋射说楚王.html` — 句间逻辑关系可视化排版实验原型
- `kg/` 下全部9个子目录 README 文档

---

## 语义区块全面升级 ([f2e2195](https://github.com/baojie/shiji-kb/commit/f2e2195)) - 2026-03-13

### 新增 (Added)

- 📝 **SKILL_区块与韵文处理.md**：新增方法论文档，涵盖 fenced div 语法、太史公曰/赞/诗歌/引文等区块类型处理规范

### 更改 (Changed)

- 🔄 **语义区块迁移至 ::: fenced div 格式**：全书130篇从 `<h4>` 标题改为 `::: 类型` 围栏块语法
  - 区块渲染改为 title 属性（tooltip），赞/诗歌块保持硬换行（`white-space: pre-line`）
  - 83个章节自动补全 `::: 太史公曰` / `::: 赞` 标注
  - 修复区块跨节、孤立 `:::` 标记等格式问题
- 📖 **SKILL_古籍文本语义化.md**：重构，整合 fenced div 区块处理内容
- 🔧 **fmt_fix_verse.py / fmt_fix_zan.py**：适配 fenced div 格式
- 🎨 **shiji-styles.css**：新增 fenced div 区块渲染样式（tooltip、pre-line 等）
- 🔄 **重新生成全部130篇HTML**

---

## v2.0实体标注符号迁移 ([b76caeb](https://github.com/baojie/shiji-kb/commit/b76caeb)) - 2026-03-13

### 更改 (Changed)

- 🔣 **实体标注符号全面迁移至〖〗格式**（v2.0）
  - 人名 `@X@` → `〖@X〗`，地名 `=X=` → `〖=X〗`，官职 `$X$` → `〖;X〗`（符号同时从 `$` 改为 `;`）
  - 时间 `%X%` → `〖%X〗`，朝代 `&X&` → `〖&X〗`，制度 `^X^` → `〖^X〗`
  - 族群 `~X~` → `〖~X〗`，器物 `*X*` → `〖•X〗`，天文 `!X!` → `〖!X〗`
  - 全书130篇批量迁移，消除标注符号与 Markdown 语法冲突
- 📖 **SKILL_古籍实体标注.md**：升级至 v2.0，更新符号表和迁移说明
- 🔧 **render_shiji_html.py**：适配〖〗新格式解析
- 📊 **实体索引重建**：v2.0格式下 11,854词条 / 96,591次标注

---

## 实体体系扩展至15类 ([f5c09dc](https://github.com/baojie/shiji-kb/commit/f5c09dc) / [de37940](https://github.com/baojie/shiji-kb/commit/de37940) / [60d6484](https://github.com/baojie/shiji-kb/commit/60d6484)) - 2026-03-13

### 新增 (Added)

- 📚 **4类新实体类型**（v1.1扩展）
  - `〖{X〗` 典籍：古籍书名（48词条，162次）
  - `〖:X〗` 礼仪：礼仪制度、宗庙祭祀（24词条，112次）
  - `〖[X〗` 刑法：刑罚、法律条文（37词条，331次）
  - `〖_X〗` 思想：哲学概念、文体体裁（52词条，1,832次）
- 🏷️ **4类实体HTML索引页**：`docs/entities/book/ritual/legal/concept.html`

### 更改 (Changed)

- 🔄 **历史标注订正**
  - `ch130`：70处书名从 `^制度^` 迁移至 `〖{典籍〗`（春秋22/六经5/诗书4/史记2等）
  - `ch084`：`^离骚^`(6处)/`天问`等书名修正为 `〖{〗`
  - 全书14章39处 `^本纪^` 统一改为 `〖_本纪〗`（与已有`〖_世家〗`保持一致）
- 📖 **SKILL_古籍实体标注.md**：全面升级为v1.1（15类符号表、AI提示词、数据规模表、渲染顺序）
- 📊 **实体总量**：11,069词条/75,517次 → 11,606词条/100,261次（+537词条，+24,744次标注）→ v2.0迁移后：11,854词条/96,591次
- 🔧 **`build_entity_index.py`**：ENTITY_TYPES 增加4个新类型，HTML生成纯数字time过滤
- 📖 **`kg/entities/scripts/tag_new_entity_types.py`**：BOOK_WORDS +13词（楚辞/诸子/韩非子篇目），CONCEPT_WORDS +8词（礼义廉耻/大一统等）
- 📝 **README.md**：实体统计、词表、标注规则表、进展日志全面更新
- 📝 **TODO.md**：重新整理，删除已完成项详细注释，按优先级分5层组织

---

## 标注符号迁移完成 + 十表Purple Numbers ([4ff4f49](https://github.com/baojie/shiji-kb/commit/4ff4f49) / [a93d04c](https://github.com/baojie/shiji-kb/commit/a93d04c) / [54eea01](https://github.com/baojie/shiji-kb/commit/54eea01)) - 2026-03-12~13

### 更改 (Changed)

- 🔣 **神话符号迁移**：`?X?` → `〖?X〗`（全书130章批量替换）
- 🔣 **生物符号清理**：清理残留的 `🌿X🌿` emoji格式，统一为 `〖+X〗`
- 📑 **十表 Purple Numbers**：013-022 十篇年表 MD 行号标记、HTML锚点、事件链接全部打通
- 🔗 **关系数据重生成**：反映符号迁移后的 `all_relations.csv/json`

---

## 未标注实体分析 + 词性分析 ([d5d5946](https://github.com/baojie/shiji-kb/commit/d5d5946) / [7940a11](https://github.com/baojie/shiji-kb/commit/7940a11)) - 2026-03-12~13

### 新增 (Added)

- 📊 **词性分析**：130章488,674字未标注文本的字级分析，量化拆解可标注/不可标注成分
- 📊 **未标注实体分析报告第六节**：候选实体实测统计，支撑4类新实体类型决策
- 📝 **`SKILL_三家注标注.md`**：《史记》三家注语义化方法论（数据结构、音韵注、书名、渲染设计）

---

## 文档目录重构 + 新增SKILL_年份消歧 ([769377f](https://github.com/baojie/shiji-kb/commit/769377f)) - 2026-03-12

### 重构 (Refactored)

- 📁 **doc/ 目录重组为6个主题子目录**
  - `doc/spec/`：标注格式规范、实体标注方案、段落编号规范、紫色编号设计、校验工具使用指南、校验覆盖范围
  - `doc/workflow/`：开发工作流程、GitHub页面部署
  - `doc/methodology/`：研究方法总则、史记Markdown转化逻辑、史记文本处理过程、史记语法高亮创造过程
  - `doc/analysis/`：史记统计分析、史记高级分析计划、词频统计表/结果
  - `doc/events/`：五轮事件年代反思总结、事件年代反思创造过程详解
  - `doc/entities/`：实体消歧别名反思报告、史记君主列表整理过程、小节划分完成报告、表格结构化计划
- 🔤 **8个英文文档名统一改为中文**
  - `FORMAT_SPECIFICATION.md` → `标注格式规范.md`
  - `ENTITY_TAGGING_SCHEME.md` → `实体标注方案.md`
  - `PARAGRAPH_NUMBERING_SUMMARY.md` → `段落编号规范.md`
  - `PURPLE_NUMBERS.md` → `紫色编号设计.md`
  - `LINT_GUIDE.md` → `校验工具使用指南.md`
  - `LINTER_COVERAGE.md` → `校验覆盖范围.md`
  - `WORKFLOW.md` → `开发工作流程.md`
  - `GITHUB_PAGES_SETUP.md` → `GitHub页面部署.md`
- 📦 **`doc/shiji-styles.css` 移至项目根级 `css/shiji-styles.css`**（源码资产，非文档）
- 🗑️ **删除 `doc/disambiguation.md`**（内容拆分：人名部分已由 SKILL_实体消歧.md 覆盖，年份部分提升为新SKILL）
- 🔗 **57个文件中的路径引用全部同步更新**

### 新增 (Added)

- 📖 **`SKILL_年份消歧.md`**：在位纪年→公元年三阶段消歧管线方法论（380位君主，1,498条映射，预过滤+5级策略+编年索引）
- 📊 **`doc/analysis/未标注实体分析报告.md`**：44万字未标注文本的实体类型分析，发现典籍书名/礼仪/刑法/思想等4类新可标注实体，设计对应标注语法（《》`+` `#` `|`）
- 🔄 **`doc/workflow/开发工作流程.md` 全面重写**：从1.0版（仅覆盖HTML生成）升级为覆盖完整管线（文本标注→实体系统→事件系统→年代系统→HTML发布→质量检查）

### 更新 (Changed)

- README：doc/ 目录树更新为子目录结构，SKILL 表新增年份消歧行，SKILL 计数 7→8

---

## 跨章因果推理 + 关系统计全面更新 ([3a85dbe](https://github.com/baojie/shiji-kb/commit/3a85dbe)) - 2026-03-12

### 新增 (Added)

- 🔗 **跨章因果推理管线**
  - 新增 `kg/relations/scripts/build_causal_relations.py`：LLM二次推理管线
  - 以 cross_ref/co_person/co_location 为候选对（1,490对，过滤后1,457对）
  - 8个Agent并行推理，每批约187对
  - 确认因果关系338条，写入 `event_relations.json`（类型：cross_causal）
  - 完整推理记录输出至 `kg/relations/causal_relations.json`（含no_causal记录）
- 📊 **cross_causal 类型**：五种子类型
  - background（背景条件）：138条
  - prerequisite（必要前提）：100条
  - direct_cause（直接原因）：96条
  - trigger（导火索）：15条
  - precedent（历史先例）：3条

### 更改 (Changed)

- 🔗 **event_relations.json**：7,314条 → 7,652条（新增338条 cross_causal）
- 📖 **SKILL_事件关系发现.md** 重大更新
  - 关系类型从8种扩展至9种（新增 cross_causal）
  - 补充章内 causal 完整推理逻辑（四步判断流程 + 边界案例对照表）
  - 新增 3.7节"跨章因果推理"：候选对筛选算法、LLM提示词结构、五条否定规则
  - 更新工具链（新增 build_causal_relations.py）、执行顺序、统计数字
- 📖 **全文档统计数字同步**：README.md、kg/README.md、SKILL_古籍事件提取与关系发现.md
  - 7,314 → 7,652条，LLM 2,188 → 2,525条，8种 → 9种类型

---

## 地铁图功能优化 + 五帝本纪年代修正 ([ba19e4d](https://github.com/baojie/shiji-kb/commit/ba19e4d)) - 2026-03-12

### 新增 (Added)

- 🗺️ **地铁图交互优化**：搜索高亮、缩放平滑、实体链接、原文引用等体验改进
- ⏱️ **001五帝本纪事件年代修正**：001-001~001-008 补充历史推断逻辑
  - 001-001：传统纪年前2698年为黄帝历元年
  - 001-002~001-008：阪泉/涿鹿战后叙事顺序推算，代际逆推（颛顼前2514年即位）

---

## 事件关系重算 + 十表事件抽取 ([e96d62e](https://github.com/baojie/shiji-kb/commit/e96d62e) / [45809c4](https://github.com/baojie/shiji-kb/commit/45809c4)) - 2026-03-11

### 新增 (Added)

- 📋 **十表事件补充提取**（013-022共10章）
  - 补充226个事件至十表章节，平均每表22.6个事件
  - 新建 `十表事件提取规划.md` 记录提取方法论
  - 产出汇总表 `事件索引汇总.xlsx`
- 🔗 **SKILL_事件关系发现.md**：从原多个SKILL合并为唯一权威文档
  - 整合 `SKILL_古籍事件提取与关系发现.md`（算法细节）
  - 整合 `SKILL_事件年代推断.md`（跨章定年）
  - 整合 `SKILL_事件识别.md`（事件链）
  - 整合 `SKILL_古籍知识图谱化.md`（实体三元组）

### 更改 (Changed)

- 🔗 **event_relations.json 全量重算**：3,185事件、7,314条关系
  - concurrent从230条增至2,997条（CE年覆盖率98.7%后大幅增加）
  - co_person 714→1,071条，co_location 455→737条

---

## 重建实体HTML索引 ([6d114e5](https://github.com/baojie/shiji-kb/commit/6d114e5)) - 2026-03-11

### 更改 (Changed)

- 🏷️ **docs/entities/event.html**：更新至3,186条事件（含十表补充事件）
- 📦 **kg/entities/data/entity_index.json**：实体索引同步更新

---

## 五轮事件年代反思完成 ([fe34b65](https://github.com/baojie/shiji-kb/commit/fe34b65)) - 2026-03-11

### 新增 (Added)

- ⏱️ **第三至五轮事件年代反思审查**
  - 第三轮（收敛验证）：465处修正，70/130章有修正，0条新模式
  - 第四轮（终态验证）：167处修正，68/130章有修正，格式修正占73.6%
  - 第五轮（跨章节交叉验证）：46处修正，28/130章有修正，确认数据稳定收敛
  - 五轮累计：~2,119处修正，年份实质性修正从~80%降至~17%
- 🔀 **跨章节交叉验证机制**
  - `generate_review_prompts.py` 新增 `CHAPTER_CROSS_REFS`：约80组章节交叉引用关系
  - 每章提示词自动注入"跨章节交叉验证"步骤，列出关联章节和验证要点
  - 优先级规则：本纪 > 年表 > 世家 > 列传
- 📝 **总结文档**
  - `doc/events/第三轮事件年代反思总结.md`
  - `doc/events/第四轮事件年代反思总结.md`
  - `doc/events/第五轮事件年代反思总结.md`
  - `doc/events/事件年代反思创造过程详解.md` 从两轮更新至五轮（章节重编号、统计全面更新）

### 更改 (Changed)

- 📖 **SKILL_事件年代推断.md 完善**
  - 补全12处空缺的典型案例和识别方法（模式9/14/15/27/28/29/32/34/35）
  - 重命名3个 `002_pattern` 条目为描述性名称
  - 年表路径从 `kg/tables/` 更新为 `kg/chronology/data/`
- 🔧 **格式清理**（反思后自动扫描修复）
  - 概览表重复日期：11文件15处去重
  - 详情叙事替代日期：3文件19处同步为标准日期格式
  - 详情重复日期：11文件15处去重
- 📖 **README.md / kg/README.md 更新**
  - 反思数据从"两轮1,441处"更新为"五轮~2,119处"
  - 新增第三至五轮总结文档链接

---

## 第四轮事件年代反思 ([16c8f9e](https://github.com/baojie/shiji-kb/commit/16c8f9e)) - 2026-03-10

### 更改 (Changed)

- ⏱️ **第四轮终态验证**：167处修正，68/130章有修正，格式类修正占73.6%
  - 确定性标注升级52处、格式冗余清理48处、年代推断行错位18处
  - 年份微调仅15处（偏差1-5年），确认年份准确度已完全收敛
  - 清理脚本伪迹残留5处（前轮apply脚本指令文字误写入时间字段）
- 📝 `doc/events/第四轮事件年代反思总结.md`

---

## 第三轮事件年代反思 ([039afb0](https://github.com/baojie/shiji-kb/commit/039afb0)) - 2026-03-10

### 更改 (Changed)

- ⏱️ **第三轮收敛验证**：465处修正，70/130章有修正，0条新模式
  - 确定性标注升级303处（65%）、年份修正116处、格式统一46处
  - 批量执行优化：6批×5-20章并行，耗时约2小时
- 📝 `doc/events/第三轮事件年代反思总结.md`

---

## 事件年代推断体系 - 2026-03-09

### 新增 (Added)

- ⏱️ **事件年代推断与交叉校验**
  - 添加《中国历史大事年表》数据，作为年代交叉校验的权威来源
  - `cross_check_dates.py`：将事件索引中的年代与大事年表交叉比对
  - 全部130章事件年代对齐：用大事年表校正事件的公元纪年标注
  - 三种年代标记规范：`（公元前XXX年）`精确、`[公元前XXX年]`推算、`[约公元前XXX年]`近似
- 🤖 **逐章年代反思Agent管线** (`kg/events/scripts/run_review_pipeline.py`)
  - 批量生成130章年代修正提示词（`--prompt`）
  - Agent反思执行（输出corrections + new_patterns JSON）
  - 自动摄入反思结果并更新状态（`--ingest`）
  - `apply_reflect_fixes.py`：将反思修正应用到事件索引
  - 第一轮完整执行：五帝本纪66事件44处修正、李将军列传16事件12处修正
- 📝 **SKILL_事件年代推断.md**
  - 完整方法论文档：纪年换算、大事年表交叉验证、Agent反思工作流

### 更改 (Changed)

- 🎨 **event.html增强**
  - 事件编号后置显示
  - 人物、地点实体添加链接（跳转到实体索引页面）
  - 年代推断tooltip（悬停显示推断依据）
  - 历史分期修正
- 🔗 **实体链接改进**
  - 实体链接改为新标签页打开（`target="_blank"`）
  - 消歧人名显示tooltip（悬停显示全名）

---

## 事件关系与地铁图可视化 - 2026-03-08

### 新增 (Added)

- 🗺️ **事件地铁图可视化** (`app/metro/`)
  - 130条线路（= 130篇章节），3,092个站点（= 3,092个事件）
  - SVG viewBox 拖拽/缩放，支持鼠标和触屏
  - 侧边栏按本纪/表/书/世家/列传分组筛选
  - 事件搜索（名称、人物、地点）
  - 详情面板：事件描述、原文引用、段落链接、实体链接、关联事件
  - Zoom-dependent 标签：缩放时标签逐步显现（4级优先级）
  - 跨线换乘连线：1,876条，按类型（互见/共人/共地/同期）不同样式
- 🔗 **事件关系系统** (`kg/events/data/event_relations.json`)
  - 4,385条关系（自动计算2,198 + LLM推理2,187）
  - 8种关系类型：sequel, causal, part_of, opposition, cross_ref, co_person, co_location, concurrent
  - 自动关系提取脚本 + LLM批量推理（5个并行Agent）
- ⏱️ **公元纪年标注与质检**
  - 782个事件标注公元年（前2700年～前87年）
  - 五帝本纪世纪级标注（前2700年～前2160年）
  - `lint_ce_years.py`：时序检查、已知年份校验、跳跃检测
  - 3轮迭代修复，错误从34降至4
- 📊 **数据构建脚本** (`kg/events/scripts/build_metro_map_data.py`)
  - 从事件索引和关系数据生成地铁图JSON
  - 按章节分配颜色，未标注年份事件自动插值

### 更改 (Changed)

- 📁 **KG目录重构**：`kg/` 按知识类型重组为7个子目录
  - `events/` — 事件索引 + 关系数据 + 6个脚本
  - `entities/` — 实体索引 + 别名 + 消歧 + 4个脚本
  - `chronology/` — 纪年数据（reign_periods, year_ce_map）
  - `genealogy/` — 帝王家谱 + 2个脚本
  - `relations/` — 人物关系 + 1个脚本
  - `vocabularies/` — 实体词表 + 1个脚本
  - `biology/` — 生物 + 1个脚本
  - `rdf/` — RDF/本体文件（*.ttl）
  - 每个子目录含 `data/` 和 `scripts/`，所有脚本路径已修正
- 📖 **README/CHANGELOG 更新**：反映新的目录结构和功能

---

## 数据校正与文档统一 ([e12f805](https://github.com/baojie/shiji-kb/commit/e12f805)) - 2026-03-08

### 更改 (Changed)

- 📊 **全项目数据统一**
  - 统一实体统计为130章完整数据：12,527个独立实体，71,857次标注（原52章数据：5,282/24,249）
  - 字数口径修正：576,915字（纯汉字），原"628,466字"为含标点但不含表格的错误统计
  - 表卷字数从5,010更新为70,525（包含十表表格文字）
  - 立传人物时代分布补充五帝/夏/商（约80人）和西周（约120人）两个缺失时期
- 📖 **文档更新**
  - `README.md`：更新实体统计、字数、五卷分布等核心数据
  - `doc/analysis/史记统计分析.md`：全面校正统计数据，处理进度更新为100%，版本v1.2
  - `doc/analysis/史记高级分析计划.md`：更新实体数量和进度信息

---

## SKU实体增补 ([85df920](https://github.com/baojie/shiji-kb/commit/85df920)) - 2026-03-05

### 新增 (Added)

- 🏷️ **Factual SKU 实体标注**
  - 新增 `augment_sku_entities.py`：利用 `entity_index.json` 中 10,110 个实体（含别名，8,173 个≥2字名称）对 434 个 Factual SKU 内容进行文本匹配
  - 为 394 个 SKU 生成 `entities.json`（覆盖率 90.8%），共 7,497 个实体标注，平均每个 SKU 19.0 个
  - 每个 `entities.json` 包含按 11 类分组的实体列表、实体总数、top 5 高频实体
  - 40 个未标注 SKU 为纯英文内容，无中文实体名可匹配
- 📊 **SKU 索引更新**
  - `skus_index.json` 新增 `entity_count` 和 `top_entities` 字段

### 更改 (Changed)

- 📖 **文档更新**
  - `ontology/README.md` 新增实体标注章节，SKU Types 表格增加 `entities.json`
  - `README.md` 新增 SKU 知识单元和实体增补相关内容

---

## 知识单元（SKU）体系 ([dc8c13d](https://github.com/baojie/shiji-kb/commit/dc8c13d)) - 2026-02-28

### 新增 (Added)

- 📦 **标准知识单元（SKU）**
  - 由 anything2ontology 工具生成，含 434 个事实知识（Factual）、241 个技能知识（Procedural）、1 个关系知识（Relational）
  - 事实知识：`header.md` + `content.md` 或 `content.json`，涵盖人物传记、诸侯国、军事、思想等 14 个主题
  - 技能知识：`header.md` + `SKILL.md`，涵盖军事战略、治国理政、外交等 14 个主题
  - 关系知识：标签体系（20 个顶层分类）、术语表（978 条）、实体关系（1,336 条三元组）
- 📋 **知识索引文档**
  - `ontology/facts_index.md`：434 个事实知识的中文分类索引
  - `ontology/skills_index.md`：241 个技能知识的中文分类索引
  - `ontology/relational_index.md`：关系知识概览
  - `ontology/README.md`：知识体系总览和使用指南

---

## 时间线实体与年份消歧 ([59c3814](https://github.com/baojie/shiji-kb/commit/59c3814)) - 2026-02-25

### 新增 (Added)

- ⏰ **时间线实体**
  - `build_year_map.py`：从历史年表中提取君主在位年份，构建公元纪年映射
  - `year_ce_map.json`：叙事年份→公元年份映射（288 种年份格式）
  - `reign_periods.json`：历代君主在位年份数据库
  - `timeline.html`：公元纪年索引的时间线页面
- 🎯 **年份消歧**
  - 覆盖全部非年表章节，支持先秦早期索引和纪年别名
  - 修复孝明皇帝归属、周赧王在位年、时长过滤等问题

---

## 实体别名合并与语义消歧 ([2580cfc](https://github.com/baojie/shiji-kb/commit/2580cfc)) - 2026-02-10

### 新增 (Added)

- 🔀 **同人别名合并**（19组新增）
  - 帝号统一6组：孝文帝←孝文皇帝/孝文/文（132→199次），孝景帝←孝景皇帝/孝景（119→180次）等
  - 秦王统一2组：秦昭王←昭襄王/昭襄，秦庄襄王←子楚（24→53次）
  - 吴国人物3组：夫差←吴王夫差，阖庐←阖闾/吴王阖庐等4个变体，诸樊←吴王诸樊
  - 赵国人名↔谥号2组：赵简子←赵鞅（60→72次），赵襄子←赵毋恤（40→57次）
  - 其他6组：田常合并3个旧条目，郦生食其←郦食其，刘濞←濞/吴王濞，田蚡←武安侯田蚡，平阳公主←平阳主，南宫公主←南宫主
  - 新增孝宣帝←宣帝

- 🎯 **语义消歧**（1,281处自动 + 11处手工修正）
  - 新增 `disambiguate_names.py`：歧义短名→带国名全称的自动消歧脚本
  - 4层启发式策略：共现全名 > 附近国名（80字窗口） > 前置国名 > 章节主题国
  - 主要消歧：武王(133→27)→周武王(84)/秦武王(30)，昭王(96→9)→秦昭王(+62)/燕昭王(+5)/楚昭王(+10)，惠王(77→19)→秦惠王(+25)/魏惠王(+5)/燕惠王(+9)/周惠王(+11)
  - 138处不确定案例保守跳过（如太后、梁王等多人共名情况）
  - 时代矛盾检测修正11处错误（如周本纪中`@秦昭襄王@`→`@周襄王@`，李斯列传中`@楚惠王@`→`@秦惠王@`等）
  - 新增73个带国名的canonical条目到 `entity_aliases.json`（周武王、齐景公、晋献公等各国君主）

### 更改 (Changed)

- 📊 **实体统计更新**
  - 人名别名：从~200条增至~570条canonical条目，别名映射3,009条
  - 人名索引：3,136个条目（消歧后新增的带国名条目），23,366次出现
  - 消歧覆盖率：1,281/1,419 = 90%（剩余138处为不确定案例）

---

## 命名实体索引系统 ([f586a61](https://github.com/baojie/shiji-kb/commit/f586a61)) - 2026-02-09

### 新增 (Added)

- 🏷️ **命名实体索引系统**
  - 新增 `build_entity_index.py`：扫描130篇tagged.md，提取实体并生成索引页面
  - 新增 `entity_aliases.json`：实体别名合并配置（~200条人名别名，含单字简称推断）
  - 生成 `entity_index.json`：中间数据文件，供后续分析使用
  - 生成 `docs/entities/` 下12个HTML索引页面（11类实体 + 总览页）
  - 每类索引页含拼音排序、字母导航栏、搜索过滤功能
- 🔗 **正文实体链接**
  - 修改 `render_shiji_html.py`，为正文中所有实体添加 `<a>` 链接，点击跳转到索引条目
  - 别名→规范名映射：正文中的"沛公"链接到索引中的"刘邦"条目
  - 处理嵌套标注（如 `$@安国君@$`），避免生成嵌套 `<a>` 标签
- 🎨 **索引页样式和交互**
  - 新增 `docs/css/entity-index.css`：索引页面样式（卡片网格、条目布局、拼音导航等）
  - 新增 `docs/js/entity-filter.js`：客户端搜索过滤（按名称和别名过滤，自动隐藏空分节）
- 👤 **西汉刘氏人名别名推断**
  - 系统梳理王国/皇室姓氏对照表，推断单字简称的全名
  - 安全合并10条（刘戊、刘如意、刘端、刘泽、刘爽、刘无采、刘辟光、刘雄渠、刘将庐、刘彭离）
  - 跳过歧义名称（卬、安、遂、濞等多人共用的短名）
  - 新增10条规范名条目（刘贾、刘仲、刘濞、刘舍、刘武、刘安、刘迁、刘礼、刘向、刘敬）

### 更改 (Changed)

- 🔧 **发布流程更新**
  - `publish_to_docs.sh` 新增 `docs/entities/` 目录创建、entity CSS/JS 复制、实体索引质量检查
  - `generate_all_chapters.py` 集成 `build_entity_index.py` 调用（子进程方式）
- 📊 **实体统计更新**
  - 人名索引：3,076 个条目，23,366 次出现
  - 地名索引：1,818 个条目，12,921 次出现
  - 官职索引：1,368 个条目，9,197 次出现
  - 全部11类合计约 9,700+ 个条目，67,000+ 次出现

---

## 十表完整表格渲染管线 ([b77c59f](https://github.com/baojie/shiji-kb/commit/b77c59f)) - 2026-02-09

### 新增 (Added)

- 📊 **十表（013-022）表格渲染管线**
  - 将十篇年表的HTML表格转换为Markdown并嵌入 `chapter_md/`，替换原有（表略）占位符
  - `render_shiji_html.py` 新增 Markdown 表格→HTML 转换功能，支持表格单元格实体标注
  - `shiji-styles.css` 新增年表样式：全视口宽度突破、sticky 表头、交替行背景、首列加粗
- 🏷️ **表格实体标注**
  - 对十表中 961 个单元格进行实体标注（朝代、人名、地名、官职等）
  - 表头使用 `&朝代&` 标记，渲染后自动高亮
- 📄 **独立主题表格HTML**
  - 新增 `resources/table_html/` 下十篇独立表格HTML页面（Ocean Depths 主题风格）

### 修复 (Fixed)

- 🐛 **表头修复**
  - 修复 015/017/018/019 表头缺失问题（原HTML无 `<thead>`，首行数据被误用为表头）
  - 修复 021/022 表头及首列多余句号
- 🔧 **016 秦楚之际月表结构修复**
  - 原31列合并表拆分为两个独立子表，匹配原始数据结构
  - 表1：秦二世时期（10列，32行）
  - 表2：项羽分封后（21列，59行），含西楚、衡山、临江、九江、常山等分封国

### 更改 (Changed)

- 🗑️ 清理 `chapter_md/` 下遗留的 `.tagged.html` 中间文件（21个）
- 📁 `doc/TODO.md` 移至根目录 `TODO.md`
- 📁 处理报告移至 `temp/`

---

## 项目文件结构整理 ([e5d8429](https://github.com/baojie/shiji-kb/commit/e5d8429)) - 2026-02-08

### 更改 (Changed)

- 📁 **工具脚本统一到 `scripts/` 目录**
  - 移入lint_markdown.py、lint_html.py、fix_verse_format.py等18个工具脚本
  - 根目录仅保留 render_shiji_html.py 和 generate_all_chapters.py 两个核心脚本
- 📝 **文档统一到 `doc/` 目录**
  - 移入TODO.md、标注格式规范.md、开发工作流程.md等技术文档
  - 移入小节划分完成报告.md等中文文档
  - CHANGELOG.md保留在根目录
- 📖 **README.md更新**
  - 目录结构重写，反映scripts/和doc/新组织
  - 更新最新进展和文档链接

---

## HTML渲染修复 ([fbf6b4b](https://github.com/baojie/shiji-kb/commit/fbf6b4b)) - 2026-02-08

### 修复 (Fixed)

- 🐛 **标注符号泄露修复**
  - 修复嵌套实体标注时 `$`、`@` 等标记符号泄露到HTML的问题
  - 调整ENTITY_PATTERNS处理顺序：外层标记（`**`、`*`）先于内层标记（`@`最后）
  - 添加安全网清理：最终移除所有残留标注符号
- 🎵 **韵文格式修复**
  - 修复秦始皇本纪等章节的韵文/诗歌格式（verse类）
- 💬 **对话缩进**
  - 为引语内容添加CSS缩进样式（`.quoted`类）

---

## 全部130章小节划分 ([98d97a3](https://github.com/baojie/shiji-kb/commit/98d97a3)) - 2026-02-08

### 新增 (Added)

- 📑 **为全部130章完成有意义的小节划分**
  - 每章按内容语义划分为多个小节
  - 小节数据保存到 sections_data.json
  - index页面各章卡片显示可点击的小节链接

---

## 项目结构重构 ([2f8f0ad](https://github.com/baojie/shiji-kb/commit/2f8f0ad)) - 2026-02-08

### 新增 (Added)
- 📁 **项目结构大幅重构**
  - 创建 `kg/` 目录统一管理知识图谱相关内容
  - 创建 `doc/` 目录管理技术文档
  - 创建 `temp/` 目录存放历史开发文件
  - 创建 `private/` 目录存放隐私敏感脚本
- 🎮 **史记争霸游戏**
  - 初始版本包含4个章节的互动游戏
  - Netlify部署包创建脚本
  - 游戏设计文档和说明

### 更改 (Changed)
- 🔧 **Python脚本整理**
  - 5个知识图谱脚本移至 `kg/` 目录并统一 `kg_` 前缀
  - 6个历史开发工具移至 `temp/` 目录
  - 根目录保留6个核心HTML生成工具
  - 移除所有脚本中的个人路径信息
- 📝 **文档整理**
  - 技术规范文档移至 `doc/` 目录
  - 知识图谱相关文档移至 `kg/` 目录
  - 游戏设计文档移至 `game/` 目录
  - 根目录仅保留 `README.md` 和 `TODO.md`
- 📖 **README.md重大更新**
  - 更新目录结构说明
  - 更新所有文档路径引用
  - 添加脚本使用说明

### 修复 (Fixed)
- 🐛 修复知识图谱脚本输出路径错误
- 🔒 移除所有脚本中的隐私路径信息

---

## 知识图谱系统完善 ([863b6c3](https://github.com/baojie/shiji-kb/commit/863b6c3)) - 2026-02-07

### 新增 (Added)
- 📊 **知识图谱系统完善**
  - 知识图谱脚本统一命名规范（kg_前缀）
  - 知识图谱输出统一到 `kg/` 子目录
  - 创建 `kg/README.md` 详细文档
- 📂 **scripts/目录规范**
  - 特定章节处理脚本移至 `temp/`
  - 保留6个通用工具脚本

### 更改 (Changed)
- 🔄 **批处理脚本整理**
  - 46个临时批处理文件移至 `temp/` 目录
  - 创建 `temp/README.md` 说明文档
- 📋 **文档路径更新**
  - 更新所有知识图谱脚本使用说明
  - 统一输出路径为相对路径

---

## HTML展示系统完善 ([02508b4](https://github.com/baojie/shiji-kb/commit/02508b4)) - 2026-02-06

### 新增 (Added)
- 🌐 **HTML展示系统完善**
  - 引号格式修复工具 `fix_quote_issues.py`
  - 小节链接提取工具 `extract_sections.py`
  - 索引页小节链接更新工具 `update_index_with_sections.py`
  - 章节内部section ID添加工具
  - 完整的 `sections_data.json` 数据文件
- 📝 **index.html重大改进**
  - 添加未来开发路线图
  - 每章添加可点击的小节链接
  - 移除统计部分（设计优化）
  - 实体标签示例简化（仅显示颜色）

### 修复 (Fixed)
- 🐛 **引号格式问题**
  - 修复56章及其他40章的引号HTML渲染错误
  - 使用负向后顾断言避免匹配HTML属性
  - 批量重新生成所有受影响章节

---

## 完整HTML生成系统 ([02508b4](https://github.com/baojie/shiji-kb/commit/02508b4)) - 2026-02-06

### 新增 (Added)
- 🏗️ **完整HTML生成系统**
  - 130章节全部生成HTML
  - 批量生成工具 `generate_all_chapters.py`
  - 统一的HTML渲染框架
- 📊 **研究方法体系**
  - 《研究方法总则.md》
  - 《史记高级分析计划.md》
  - 《史记统计分析.md》
  - 《史记编年表.md》

### 更改 (Changed)
- 📈 **标注进度**
  - 完成99/130章节标注（76.2%）
  - 涵盖本纪12篇、表10篇、书8篇、世家30篇、列传39篇

---

## 核心标注系统建立 ([73c7aed](https://github.com/baojie/shiji-kb/commit/73c7aed)) - 2026-01-23

### 新增 (Added)
- 📚 **核心标注系统建立**
  - 11类实体标注规范（人名、地名、官职、时间等）
  - Purple Numbers段落编号系统
  - Markdown转HTML核心工具 `render_shiji_html.py`
- 🎨 **样式系统**
  - 实体语法高亮（11种不同颜色）
  - 对话内容样式（斜体+网纹阴影）
  - 段落编号小黄框样式
  - 可点击的段落锚点和hash URL分享
- 📖 **文本结构化**
  - 长段落智能拆分逻辑
  - 对话内容拆分规则
  - 列表结构识别
  - 诗歌按行排版

### 更改 (Changed)
- 🔄 **文件重命名**
  - `*.simple.md` → `*.tagged.md`

---

## 项目启动/RDF试验 ([256f6cc](https://github.com/baojie/shiji-kb/commit/256f6cc)) - 2025-02至03

### 新增 (Added)
- 🚀 **项目启动** (2025-02-04)
  - 手工编写RDF/TTL知识图谱（高祖本纪8.1、8.2节）
  - 创建本体定义文件 `ontology.ttl`
  - 建立GitHub仓库
- 📝 **技术路线转型** (2026-01-22起)
  - 拆分130篇《史记》原始文本
  - 转向Markdown标注系统
  - 完成五帝本纪、夏本纪初步转化

---

## 标注进度统计

| Commit | 日期 | 已标注章节 | 完成度 | 里程碑 |
|--------|------|-----------|--------|--------|
| [b77c59f](https://github.com/baojie/shiji-kb/commit/b77c59f) | 2026-02-09 | 130/130 | 100% ✅ | 十表表格渲染管线 |
| [e5d8429](https://github.com/baojie/shiji-kb/commit/e5d8429) | 2026-02-08 | 130/130 | 100% ✅ | 文件结构整理+文档更新 |
| [fbf6b4b](https://github.com/baojie/shiji-kb/commit/fbf6b4b) | 2026-02-08 | 130/130 | 100% ✅ | HTML渲染修复 |
| [98d97a3](https://github.com/baojie/shiji-kb/commit/98d97a3) | 2026-02-08 | 130/130 | 100% ✅ | 130章小节划分 |
| [2f8f0ad](https://github.com/baojie/shiji-kb/commit/2f8f0ad) | 2026-02-08 | 130/130 | 100% ✅ | 项目结构重构 |
| [863b6c3](https://github.com/baojie/shiji-kb/commit/863b6c3) | 2026-02-07 | 130/130 | 100% ✅ | 知识图谱系统 |
| [02508b4](https://github.com/baojie/shiji-kb/commit/02508b4) | 2026-02-06 | 130/130 | 100% ✅ | HTML展示完善 |
| [02508b4](https://github.com/baojie/shiji-kb/commit/02508b4) | 2026-02-06 | 130/130 | 100% ✅ | 完整HTML生成 |
| [73c7aed](https://github.com/baojie/shiji-kb/commit/73c7aed) | 2026-01-23 | 52/130 | 40% | 核心系统建立 |
| [256f6cc](https://github.com/baojie/shiji-kb/commit/256f6cc) | 2025-02至03 | 2/130 | 1.5% | 项目启动+RDF/TTL |

---

## 技术栈变更

### 当前技术栈
- Python 3.9+
- JavaScript (ES6+)
- HTML5/CSS3
- Markdown
- Git/GitHub

### 未来计划
- Neo4j（知识图谱数据库）
- D3.js（可视化）
- React（前端框架）
- FastAPI（后端API）

---

## 贡献者

- [@baojie](https://github.com/baojie) - 项目创建者和主要维护者
- Claude Sonnet 4.5 / Opus 4.6 - AI助手（标注工具开发、文档编写）

---

## 许可证变更

- **v0.1.0+**:
  - 内容：CC BY-NC-SA 4.0
  - 代码：MIT License

---

**最后更新**: 2026-03-16
**当前版本**: v0.9.0
