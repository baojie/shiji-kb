# 更新日志 (Changelog)

本文档记录《史记》知识库项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。记日规则是每天早上7点之前的工作计入前一日，以保障工作的连续性。以当地所在地时间为准，主要使用北京时间（UTC-8）和太平洋时间（UTC-8）。


**每日详细工作日志**: [`logs/daily/`](logs/daily/) 目录

---

## 2026-03-31

### 新增 (Added)

- **繁简体阅读切换功能**
  - 创建custom-variants.json词库（32条精准规则）
  - 解决"后"字上下文转换问题（"吕后"→"呂后"，"后世"→"後世"）
  - 本地化OpenCC.js（1.1MB），支持离线使用
  - 统一JS依赖管理（shiji-imports.js）
  - 批量更新130章HTML文件

### 文档 (Documentation)

- **新增SPEC文档**: [`doc/spec/繁简体词库构造方案.md`](doc/spec/繁简体词库构造方案.md)
  - 记录三次词库构造尝试的完整过程
  - 尝试1（失败）：自动逐字比对 → 提取到文本校勘差异
  - 尝试2（成功）：手动构建32条精准规则
  - 尝试3（失败）：模糊匹配提取 → 提取到异体字选择差异
  - 总结核心经验：维基文库不适合作为繁简词库的构建来源
- **新增分析文档**: [`doc/spec/繁简词库对比分析.md`](doc/spec/繁简词库对比分析.md)
  - 详细对比手动词库（32条）vs 自动提取（48条）
  - 验证发现：所有自动提取规则都不应添加
  - OpenCC转换验证表：8个测试案例全部为异体字差异

### 维护 (Maintenance)

- 创建Python虚拟环境（.venv）
  - 安装opencc-python-reimplemented
  - 安装beautifulsoup4
  - 用于辅助分析繁简转换差异
- 创建分析脚本
  - `scripts/compare_with_wikisource.py` - 逐字比对（已废弃）
  - `scripts/extract_variants_fuzzy.py` - 模糊匹配提取（已废弃）
  - 保留供参考，但不建议使用

---

## 2026-03-30

### 新增 (Added)

- **130章文本完整性修复完成** ([bd72b76e], [6ed59b01], [b60113e6])
  - 修复48章累计消除800+处实质差异
  - 完成率从66.9%提升至91.5%
  - 包含：错误最多的10章（282处）、中等错误30章（518处）、质量提升7章（401处）

- **拼音标注功能** ([1c6dc689])
  - 新增拼音标注开关
  - 构造特殊读音词库，解决多音字问题

- **语义高亮开关** ([#17], [68e9c8cb])
  - 新增配置面板（右上角齿轮图标）
  - 实现23类实体样式一键切换
  - 批量更新131个章节HTML文件

- **表格校勘规范** ([#35], [8f358377], [b51aa0a7])
  - 新增SKILL文档，规范年表/世家类章节校勘
  - 确立维基文库为校对底本

### 更改 (Changed)

- **HTML展示层全面更新** ([be91df1d])
  - 重新生成130章HTML及实体索引
  - 反映最新校勘成果

- **规律库扩展** ([b60113e6])
  - 新增3条标注规律（A71/A72/B4）
  - 规律库更新至72条

### 文档 (Documentation)

- **README核心数据验证** ([a0fdb95b])
  - 内容优化，数据准确性验证

**详细工作日志**: [`logs/daily/2026-03-30.md`](logs/daily/2026-03-30.md)

[1c6dc689]: https://github.com/baojie/shiji-kb/commit/1c6dc689
[a0fdb95b]: https://github.com/baojie/shiji-kb/commit/a0fdb95b
[68e9c8cb]: https://github.com/baojie/shiji-kb/commit/68e9c8cb
[8f358377]: https://github.com/baojie/shiji-kb/commit/8f358377
[be91df1d]: https://github.com/baojie/shiji-kb/commit/be91df1d
[b51aa0a7]: https://github.com/baojie/shiji-kb/commit/b51aa0a7
[6ed59b01]: https://github.com/baojie/shiji-kb/commit/6ed59b01
[bd72b76e]: https://github.com/baojie/shiji-kb/commit/bd72b76e
[b60113e6]: https://github.com/baojie/shiji-kb/commit/b60113e6
[#17]: https://github.com/baojie/shiji-kb/issues/17
[#35]: https://github.com/baojie/shiji-kb/issues/35

---

## 2026-03-29

### 新增 (Added)

- **SKILL_10项目管理体系** ([ccd9bc55])
  - 建立五件套规范：TODO/Issue管理、每日日志、Git提交、CHANGELOG编写
  - 新增SKILL_10/10a/10b/10c/10d共5个文档（2500+行）

- **SKILL_01标注规范扩展** ([ad898a77], [71adacfd])
  - 新增SKILL_01a标注完整性维护技能
  - 完善SKILL_01b多版本互校底本（补充脱字与内证校勘案例）

- **30个工作日志改动意义分析** ([58d42ecf])
  - 为全部30个工作日志添加"改动意义"章节
  - 新增INDEX.md索引导航

- **001-004章多版本互校** ([66d77fa7])
  - 标准底本校勘：筴→策、暐→檋、饹→奔等9处字符修正
  - 派生文件同步：44章全流程更新

### 修复 (Fixed)

- **标注错误修复** ([0834c21d], [d0a7fc40], [ab788033], [87356d8e], [52e10476])
  - 修复8个章节标注错误30+处（嵌套标注/地名误标/动词遗漏等）
  - 在SKILL和Script两层禁止嵌套标注 ([649c8d32])

### 更改 (Changed)

- **校对基准统一** ([ccd9bc55])
  - 从docs/original_text切换到archive/chapter目录
  - 完善SKILL索引，明确标准底本位置

### 项目维护 (Maintenance)

- **REF类Issues整合** ([ccd9bc55])
  - 整合GitHub上6个REF类Issue到参考资源库
  - 完善resources/references/README.md导航

- **目录重构规范** ([ad898a77])
  - 新增SPEC_directory_restructure.md文档

**详细工作日志**: [`logs/daily/2026-03-29.md`](logs/daily/2026-03-29.md)

[58d42ecf]: https://github.com/baojie/shiji-kb/commit/58d42ecf
[ccd9bc55]: https://github.com/baojie/shiji-kb/commit/ccd9bc55
[ad898a77]: https://github.com/baojie/shiji-kb/commit/ad898a77
[71adacfd]: https://github.com/baojie/shiji-kb/commit/71adacfd
[66d77fa7]: https://github.com/baojie/shiji-kb/commit/66d77fa7
[649c8d32]: https://github.com/baojie/shiji-kb/commit/649c8d32
[0834c21d]: https://github.com/baojie/shiji-kb/commit/0834c21d
[d0a7fc40]: https://github.com/baojie/shiji-kb/commit/d0a7fc40
[ab788033]: https://github.com/baojie/shiji-kb/commit/ab788033
[87356d8e]: https://github.com/baojie/shiji-kb/commit/87356d8e
[52e10476]: https://github.com/baojie/shiji-kb/commit/52e10476

---

## 2026-03-28

### 项目维护 (Maintenance)

- 工作日志补齐：2026-03-25.md / 2026-03-26.md / 2026-03-27.md ([0460bbde])
- README文档更新：根目录/labs/source-inference/publications四个层级 ([54cb86bf])
- 每日日志SKILL完善：新增"太史公曰"无提交日处理规则 ([0460bbde])

**详细工作日志**: [`logs/daily/2026-03-28.md`](logs/daily/2026-03-28.md)

[0460bbde]: https://github.com/baojie/shiji-kb/commit/0460bbde
[54cb86bf]: https://github.com/baojie/shiji-kb/commit/54cb86bf

---

## 2026-03-26

### 新增 (Added)

- **史记常识库体系** ([`kg/common-sense/`](kg/common-sense/)) ([81c1a5f6] / [d5ecfbf9])
  - 综合常识库 (10大类, 108+条目): 数字/时间/地理/制度/社会/军事/生理/政治/经济/文化
  - 知识库索引: 规划9个专题常识库 + 3个推理规则库 + 5个数据表格库
  - 首轮反思迭代提取报告 (8个高质量常识, 平均假阳性率<7.5%)

- **反常检测实验** ([`labs/contradiction-analysis/`](labs/contradiction-analysis/)) ([81c1a5f6])
  - 首轮反常检测报告 (10个案例, 4个高价值疑案)
  - 发现3大反常模式: 数字反常(夸大2-5倍) / 制度反常(转型期) / 时间矛盾(史源差异)

- **逻辑推理方法论体系** ([`skills/`](skills/)) ([d5ecfbf9])
  - SKILL_07e 真实性推理: 七大推理方法(医学/法律/科学/动机/逻辑/沉默证据/史源批判)
  - 矛盾检测方法论 (4大矛盾类型: DATE/DETAIL/ATTRIBUTION/SEQUENCE)
  - 矛盾→反常映射规则 (数据流转接口)

### 更新 (Changed)

- **SKILL_07c 反常推理** ([81c1a5f6])
  - 新增第七章: 常识推断方法 (Meta-Skill: 反思迭代)
  - 六轮反思迭代流程: 案例收集→普适性检验→来源标注→规则化编码→实战验证→录入常识库
  - 假阳性控制机制 (<20%合格标准)

- **矛盾分析实验室** ([81c1a5f6])
  - 整合矛盾检测 + 反常检测成果
  - 新增高价值反常汇总表

### 项目维护 (Maintenance)

- 文档结构优化 (常识库独立目录)
- 更新项目主README (新增常识库和反常检测介绍)
- 更新CHANGELOG (记录2026-03-26变更)

[81c1a5f6]: https://github.com/baojie/shiji-kb/commit/81c1a5f6
[d5ecfbf9]: https://github.com/baojie/shiji-kb/commit/d5ecfbf9

---

## 2026-03-24

### 新增 (Added)

- **十表交互式数据查看器** ([`docs/special/tables.html`](docs/special/tables.html)) ([f78bfc38] / [cc94b0de])
  - ag-Grid表格组件：搜索、筛选、排序、导出功能
  - 双标签页设计（交互式查看器 + 表格索引）
  - 11个十表JSON数据发布（约650KB）
  - 分页显示100行，固定表头和第一列
  - 横向滚动条固定在表头下方

### 更改 (Changed)

- **表格查看器显示优化** ([cc94b0de])
  - 每页显示100行（可选50/100/200/500）
  - 表头在垂直滚动时保持固定
  - 横向滚动条固定在视口顶部，纵向滚动时始终可见

### 项目维护 (Maintenance)

- 新增数据发布脚本 `scripts/publish_tables_data.py`
- 新增链接验证脚本 `scripts/verify_table_links.py`

**详细工作日志**: [`logs/daily/2026-03-24.md`](logs/daily/2026-03-24.md)

[f78bfc38]: https://github.com/baojie/shiji-kb/commit/f78bfc38
[cc94b0de]: https://github.com/baojie/shiji-kb/commit/cc94b0de

---

## 2026-03-23

### 新增 (Added)

- **谥号索引系统** ([`kg/entities/indices/shi_hao_index.json`](kg/entities/indices/shi_hao_index.json)) ([6e387021] / [7522eaa4] / [9fecf8a5] / [4fff9fb1])
  - 覆盖诸侯王、小国君主、大夫家族谥号
  - 优化专项索引页面布局
  - 扩展识别范围支持小诸侯国和大夫家族
- **语义关系索引系统** ([`kg/entities/indices/relation_index.json`](kg/entities/indices/relation_index.json)) ([c73917c4])
  - 实体间语义关系统一索引
  - 重建实体页面集成关系展示

### 修复 (Fixed)

- **009-030章第三轮实体标注反思**：22章大规模修正 ([3ef07df0] / [a6fe0a88])
  - 009-020章实体标注反思和修正（12章）
  - 021-030章实体标注反思完成（10章）
- **嵌套刑法标注错误**：修复并更新反思报告 ([ac11e279])
- **谥号索引边界错误**：完善处理顺序说明 ([9fecf8a5])

### 项目维护 (Maintenance)

- Metro.js数据一致性改进 ([5b9caa97])
- 合并PR #26 修复transfers ([c34cb982])

**详细工作日志**: [`logs/daily/2026-03-23.md`](logs/daily/2026-03-23.md)

[6e387021]: https://github.com/baojie/shiji-kb/commit/6e387021
[7522eaa4]: https://github.com/baojie/shiji-kb/commit/7522eaa4
[9fecf8a5]: https://github.com/baojie/shiji-kb/commit/9fecf8a5
[4fff9fb1]: https://github.com/baojie/shiji-kb/commit/4fff9fb1
[c73917c4]: https://github.com/baojie/shiji-kb/commit/c73917c4
[3ef07df0]: https://github.com/baojie/shiji-kb/commit/3ef07df0
[a6fe0a88]: https://github.com/baojie/shiji-kb/commit/a6fe0a88
[ac11e279]: https://github.com/baojie/shiji-kb/commit/ac11e279
[5b9caa97]: https://github.com/baojie/shiji-kb/commit/5b9caa97
[c34cb982]: https://github.com/baojie/shiji-kb/commit/c34cb982

---

## 2026-03-22

### 新增 (Added)

- **普通文本语义标注阅读系统** ([`resources/publications/draft/`](resources/publications/draft/)) ([818736e8])
  - 2055行代码：渲染引擎+样式+交互脚本
  - 15种实体类型可视化+3种标注模式
- **指代消解SKILL规范** ([`skills/SKILL_02i_指代消解.md`](skills/SKILL_02i_指代消解.md)) ([2799ca57])
  - 868行人称代词和身份指代语义消解规范
- **混合语义分析实验框架** ([`labs/hybrid-semantic-analysis/`](labs/hybrid-semantic-analysis/)) ([2bcac1ad] / [b293ab20] / [17db94f4])
  - 三种语义分析方法（LTP本地、LTP+Qwen混合、纯LLM）
  - 5种NLP工具对比文档（LTP/HanLP/Stanza/spaCy/jieba）
  - Python 3.13兼容性测试结果

### 修复 (Fixed)

- **002-008章第三轮实体标注反思**：99处修正 ([4b75ebf2] / [1975470c] / [42625df0] / [b3286a8a])
  - 时长消歧标注59处、群体身份21处、刑法动词11处
  - 标注铁律违规修正2处、断句错误修复1处
- **标注铁律强化**：明确禁止修改原文字符和标点 ([970a465c])
- **Lint工具增强**：引号规范化和白名单机制 ([4b75ebf2])

### 更改 (Changed)

- **目录结构重构**：创建resources/统一管理静态参考资料 ([02cce8db])
- **SKILL文件结构化**：为41个SKILL文件添加YAML frontmatter ([89b1c38a])
- **根目录整理**：移动脚本和报告到对应目录 ([f04b420a])

### 项目维护 (Maintenance)

- 构建生成文件更新 ([b5254746])
- 图片资源更新 ([af8563f0])

**详细工作日志**: [`logs/daily/2026-03-22.md`](logs/daily/2026-03-22.md)

[818736e8]: https://github.com/baojie/shiji-kb/commit/818736e8
[2799ca57]: https://github.com/baojie/shiji-kb/commit/2799ca57
[2bcac1ad]: https://github.com/baojie/shiji-kb/commit/2bcac1ad
[b293ab20]: https://github.com/baojie/shiji-kb/commit/b293ab20
[17db94f4]: https://github.com/baojie/shiji-kb/commit/17db94f4
[4b75ebf2]: https://github.com/baojie/shiji-kb/commit/4b75ebf2
[1975470c]: https://github.com/baojie/shiji-kb/commit/1975470c
[42625df0]: https://github.com/baojie/shiji-kb/commit/42625df0
[b3286a8a]: https://github.com/baojie/shiji-kb/commit/b3286a8a
[970a465c]: https://github.com/baojie/shiji-kb/commit/970a465c
[02cce8db]: https://github.com/baojie/shiji-kb/commit/02cce8db
[89b1c38a]: https://github.com/baojie/shiji-kb/commit/89b1c38a
[f04b420a]: https://github.com/baojie/shiji-kb/commit/f04b420a
[b5254746]: https://github.com/baojie/shiji-kb/commit/b5254746
[af8563f0]: https://github.com/baojie/shiji-kb/commit/af8563f0

---

## 2026-03-21

### 新增 (Added)

- **司马迁文风研究实验** ([`labs/sima-qian-style/`](labs/sima-qian-style/)) ([0117a825] / [c7a0d55c])
- **溯源推理分析实验** ([`skills/SKILL_07d_溯源推理.md`](skills/SKILL_07d_溯源推理.md)) ([4ebda328])
- **技术文章**《从历史书中探索知识图谱》([03685329] / [6360679d])

### 修复 (Fixed)

- **SKU本体实体分类错误** ([602c1f94])
- **时间与数量实体标注混淆** ([feb5a516]) ([Issue #1](https://github.com/baojie/shiji-kb/issues/1))
- **实体边界错误第三轮反思**：17处修饰词切分 ([1b3bc8ad])

### 更改 (Changed)

- **labs目录重组** ([0117a825])
- **归档文件整理** ([c4c568cc])

### 项目维护 (Maintenance)

- 参与指南文档 ([21582643])
- README赞助区 ([0e0f5be7])
- 每日工作日志更新 ([e96938bc])

**详细工作日志**: [`logs/daily/2026-03-21.md`](logs/daily/2026-03-21.md)

[0117a825]: https://github.com/baojie/shiji-kb/commit/0117a825
[c7a0d55c]: https://github.com/baojie/shiji-kb/commit/c7a0d55c
[4ebda328]: https://github.com/baojie/shiji-kb/commit/4ebda328
[21582643]: https://github.com/baojie/shiji-kb/commit/21582643
[03685329]: https://github.com/baojie/shiji-kb/commit/03685329
[6360679d]: https://github.com/baojie/shiji-kb/commit/6360679d
[0e0f5be7]: https://github.com/baojie/shiji-kb/commit/0e0f5be7
[602c1f94]: https://github.com/baojie/shiji-kb/commit/602c1f94
[feb5a516]: https://github.com/baojie/shiji-kb/commit/feb5a516
[1b3bc8ad]: https://github.com/baojie/shiji-kb/commit/1b3bc8ad
[c4c568cc]: https://github.com/baojie/shiji-kb/commit/c4c568cc
[e96938bc]: https://github.com/baojie/shiji-kb/commit/e96938bc

---

## 2026-03-20

### 修复 (Fixed)

- **实体边界错误综合反思**：75处切分错误 ([99af56d6])

### 更改 (Changed)

- **文件夹重组** ([172feaf4])

### 项目维护 (Maintenance)

- 文档重构 ([cc4d3d43])
- SKILL审阅 ([926d3b30])
- 每日工作日志 ([ac7e41c4])

**详细工作日志**: [`logs/daily/2026-03-20.md`](logs/daily/2026-03-20.md)

[99af56d6]: https://github.com/baojie/shiji-kb/commit/99af56d6
[cc4d3d43]: https://github.com/baojie/shiji-kb/commit/cc4d3d43
[172feaf4]: https://github.com/baojie/shiji-kb/commit/172feaf4
[926d3b30]: https://github.com/baojie/shiji-kb/commit/926d3b30
[ac7e41c4]: https://github.com/baojie/shiji-kb/commit/ac7e41c4

---

## 2026-03-19

### 新增 (Added)

- **工具脚本**：身份标注修复与动词自动标注 ([d86dd5c0])

### 修复 (Fixed)

- **身份标注符号语义漂移**：全局修正8,774处 ([4c96f109])
- **实体边界错误**：75处切分错误 ([99af56d6])
- **CSS样式优化** ([b1ed7930] / [557609d7] / [aad56029])

### 更改 (Changed)

- **动词标注完成**：002-130全部章节 ([cca73582])
- **文件夹整理** ([172feaf4] / [4c863aca])

### 项目维护 (Maintenance)

- 文档重构 ([cc4d3d43] / [c38912b0] / [ca8a6f71])
- 每日工作日志 ([ac7e41c4] / [e96938bc])
- HTML与索引重建 ([9a21080b])

**详细工作日志**: [`logs/daily/2026-03-19.md`](logs/daily/2026-03-19.md)

[d86dd5c0]: https://github.com/baojie/shiji-kb/commit/d86dd5c0
[4c96f109]: https://github.com/baojie/shiji-kb/commit/4c96f109
[cca73582]: https://github.com/baojie/shiji-kb/commit/cca73582
[b1ed7930]: https://github.com/baojie/shiji-kb/commit/b1ed7930
[557609d7]: https://github.com/baojie/shiji-kb/commit/557609d7
[aad56029]: https://github.com/baojie/shiji-kb/commit/aad56029
[c38912b0]: https://github.com/baojie/shiji-kb/commit/c38912b0
[ca8a6f71]: https://github.com/baojie/shiji-kb/commit/ca8a6f71
[4c863aca]: https://github.com/baojie/shiji-kb/commit/4c863aca
[9a21080b]: https://github.com/baojie/shiji-kb/commit/9a21080b

---

## 2026-03-18

### 新增 (Added)

- **元技能方法论PDF**：合集发布 ([2f9eb3aa] / [ff6c7cfe])
- **史记三家注原文**：繁体txt ([f66be355])

### 修复 (Fixed)

- **动词格式清理**：v3.1/v3.2迁移 ([5278645d] / [5359bf7a] / [e43a3317])

### 更改 (Changed)

- **动词标注体系升级**：v3.2→v3.3 ([4ed5cc45] / [53667d0a])
- **目录重构** ([8f2769ba] / [cd87afa9])

### 项目维护 (Maintenance)

- 元技能文档体系重构 ([31520b40])
- HTML与索引重建 ([9de8f7ea])
- SKILL统计更新 ([6ed84601])
- 每日工作日志 ([054d2944])

**详细工作日志**: [`logs/daily/2026-03-18.md`](logs/daily/2026-03-18.md)

[4ed5cc45]: https://github.com/baojie/shiji-kb/commit/4ed5cc45
[53667d0a]: https://github.com/baojie/shiji-kb/commit/53667d0a
[2f9eb3aa]: https://github.com/baojie/shiji-kb/commit/2f9eb3aa
[ff6c7cfe]: https://github.com/baojie/shiji-kb/commit/ff6c7cfe
[f66be355]: https://github.com/baojie/shiji-kb/commit/f66be355
[5278645d]: https://github.com/baojie/shiji-kb/commit/5278645d
[5359bf7a]: https://github.com/baojie/shiji-kb/commit/5359bf7a
[e43a3317]: https://github.com/baojie/shiji-kb/commit/e43a3317
[31520b40]: https://github.com/baojie/shiji-kb/commit/31520b40
[8f2769ba]: https://github.com/baojie/shiji-kb/commit/8f2769ba
[cd87afa9]: https://github.com/baojie/shiji-kb/commit/cd87afa9
[9de8f7ea]: https://github.com/baojie/shiji-kb/commit/9de8f7ea
[6ed84601]: https://github.com/baojie/shiji-kb/commit/6ed84601
[054d2944]: https://github.com/baojie/shiji-kb/commit/054d2944

---

## 2026-03-17

### 新增 (Added)

- **专项索引系统**：太史公曰、韵文(96篇)、成语 ([849d8ac1] / [cf9f4f5c] / [5ef38163] / [eb97490a] / [49b57157])
- **战争事件识别SKILL** (SKILL_05e) ([42e5fab6])
- **汉字标注覆盖率统计工具** ([f187e340])

### 更改 (Changed)

- **第二轮实体反思**：93章标注修正 ([0cd03a76] / [08a4c5bb])
- **动词标注体系升级**：v3.1格式迁移 ([4536fd58] / [01391269] / [cfb2a51d] / [7c5ab02b])
- **SKILL_03c更新** ([62d663e6])

### 修复 (Fixed)

- **注释块渲染修复** ([5b7ad5a5])

### 项目维护 (Maintenance)

- 每日工作日志系统 ([9962ead7])
- 实体统计更新 ([d5d8e3ee])
- HTML/索引重建 ([1b35876f])

**详细工作日志**: [`logs/daily/2026-03-17.md`](logs/daily/2026-03-17.md)

[849d8ac1]: https://github.com/baojie/shiji-kb/commit/849d8ac1
[cf9f4f5c]: https://github.com/baojie/shiji-kb/commit/cf9f4f5c
[5ef38163]: https://github.com/baojie/shiji-kb/commit/5ef38163
[eb97490a]: https://github.com/baojie/shiji-kb/commit/eb97490a
[49b57157]: https://github.com/baojie/shiji-kb/commit/49b57157
[42e5fab6]: https://github.com/baojie/shiji-kb/commit/42e5fab6
[0cd03a76]: https://github.com/baojie/shiji-kb/commit/0cd03a76
[08a4c5bb]: https://github.com/baojie/shiji-kb/commit/08a4c5bb
[4536fd58]: https://github.com/baojie/shiji-kb/commit/4536fd58
[01391269]: https://github.com/baojie/shiji-kb/commit/01391269
[cfb2a51d]: https://github.com/baojie/shiji-kb/commit/cfb2a51d
[7c5ab02b]: https://github.com/baojie/shiji-kb/commit/7c5ab02b
[5b7ad5a5]: https://github.com/baojie/shiji-kb/commit/5b7ad5a5
[9962ead7]: https://github.com/baojie/shiji-kb/commit/9962ead7
[f187e340]: https://github.com/baojie/shiji-kb/commit/f187e340
[62d663e6]: https://github.com/baojie/shiji-kb/commit/62d663e6
[d5d8e3ee]: https://github.com/baojie/shiji-kb/commit/d5d8e3ee
[1b35876f]: https://github.com/baojie/shiji-kb/commit/1b35876f

---

## 2026-03-16

### 新增 (Added)

- **姓氏推理首轮**：覆盖2053/3630人物（56.6%） ([edc9821e] / [4a4255bf])
- **第一轮实体反思**：全书130章修正1913处 ([38b082c6] / [7c329904] / [67e2c639])
- **内联消歧语法v2.7**：扩展到13类实体 ([0cb6fec9])

### 修复 (Fixed)

- **章节标注质量提升**：013-130章修正756处
- **单字人名消歧**：001-010章39处 ([9037f7cb] / [a788c574])
- **011章第二次反思**：32处修正 ([b468df8c])
- **012章反思**：59处修正 ([edc9821e])

### 更改 (Changed)

- **v2.8格式统一**：18类实体迁移为〖TYPE X〗 ([650aa7d3] / [d6e2b667])

### 项目维护 (Maintenance)

- 方法论规划 ([b0ab24c1])
- 实体统计更新

**详细工作日志**: [`logs/daily/2026-03-16.md`](logs/daily/2026-03-16.md)

[edc9821e]: https://github.com/baojie/shiji-kb/commit/edc9821e
[4a4255bf]: https://github.com/baojie/shiji-kb/commit/4a4255bf
[38b082c6]: https://github.com/baojie/shiji-kb/commit/38b082c6
[7c329904]: https://github.com/baojie/shiji-kb/commit/7c329904
[67e2c639]: https://github.com/baojie/shiji-kb/commit/67e2c639
[0cb6fec9]: https://github.com/baojie/shiji-kb/commit/0cb6fec9
[9037f7cb]: https://github.com/baojie/shiji-kb/commit/9037f7cb
[a788c574]: https://github.com/baojie/shiji-kb/commit/a788c574
[b468df8c]: https://github.com/baojie/shiji-kb/commit/b468df8c
[650aa7d3]: https://github.com/baojie/shiji-kb/commit/650aa7d3
[d6e2b667]: https://github.com/baojie/shiji-kb/commit/d6e2b667
[b0ab24c1]: https://github.com/baojie/shiji-kb/commit/b0ab24c1

---

## 2026-03-15

### 新增 (Added)

- **语义排版实验**：五帝本纪逻辑关系可视化 ([2294a7d9] / [71bbf0c6] / [6cc97cdc])
- **十表结构化**：013三代世表JSON/CSV ([d6e2b667])

### 修复 (Fixed)

- **人名实体跨章反思**：615处修正 ([edc9821e])
- **单字人名消歧**：001-010章39处 ([a788c574])
- **v3.1文本校勘**：540→386处差异 ([da71305c])
- **lint完整性修复**：130章实质差异归零 ([ed3c45f8])
- **多章标注修正** ([9cc85ae7] / [c5386c0e] / [3275308c] / [28266b41])

### 更改 (Changed)

- **官职反思**：2290处重分类（元年→时间、皇帝专称→人名）
- **纪年系统重建** ([cebce93a])

### 项目维护 (Maintenance)

- SKILL体系增强 ([fdc5eaff] / [4dc02f54])
- 实体反思方法论重构 ([9508de3f])
- 实体索引+年表重建 ([fbe735a4] / [39660102])
- 文档整理 ([6ebca4ee])

**详细工作日志**: [`logs/daily/2026-03-15.md`](logs/daily/2026-03-15.md)

[fdc5eaff]: https://github.com/baojie/shiji-kb/commit/fdc5eaff
[4dc02f54]: https://github.com/baojie/shiji-kb/commit/4dc02f54
[2294a7d9]: https://github.com/baojie/shiji-kb/commit/2294a7d9
[71bbf0c6]: https://github.com/baojie/shiji-kb/commit/71bbf0c6
[6cc97cdc]: https://github.com/baojie/shiji-kb/commit/6cc97cdc
[a788c574]: https://github.com/baojie/shiji-kb/commit/a788c574
[d6e2b667]: https://github.com/baojie/shiji-kb/commit/d6e2b667
[da71305c]: https://github.com/baojie/shiji-kb/commit/da71305c
[ed3c45f8]: https://github.com/baojie/shiji-kb/commit/ed3c45f8
[9cc85ae7]: https://github.com/baojie/shiji-kb/commit/9cc85ae7
[c5386c0e]: https://github.com/baojie/shiji-kb/commit/c5386c0e
[3275308c]: https://github.com/baojie/shiji-kb/commit/3275308c
[28266b41]: https://github.com/baojie/shiji-kb/commit/28266b41
[9508de3f]: https://github.com/baojie/shiji-kb/commit/9508de3f
[cebce93a]: https://github.com/baojie/shiji-kb/commit/cebce93a
[fbe735a4]: https://github.com/baojie/shiji-kb/commit/fbe735a4
[39660102]: https://github.com/baojie/shiji-kb/commit/39660102
[6ebca4ee]: https://github.com/baojie/shiji-kb/commit/6ebca4ee

---

## 2026-03-14

### 更改 (Changed)

- **实体体系深度重构**：v2.2-v2.8 ([73cfbf16] / [d5967cdc] / [1e6cf8e1] / [4baba997] / [53d9b987] / [7f768628] / [963e49bb] / [f5b17c0f] / [8c43461a] / [a1ea0950] / [c3e9b28a] / [88240e17] / [7f28fd6c])
  - 邦国/氏族/族群三层分类：195处重分类
  - 官职深度反思：2290处（元年→时间、皇帝专称→人名）
  - 地名反思60处、身份类型扩充4297次
  - lint系统建立

### 新增 (Added)

- **语义排版实验原型** ([17554cae] / [f9db9c20])

**详细工作日志**: [`logs/daily/2026-03-14.md`](logs/daily/2026-03-14.md)

[73cfbf16]: https://github.com/baojie/shiji-kb/commit/73cfbf16
[d5967cdc]: https://github.com/baojie/shiji-kb/commit/d5967cdc
[1e6cf8e1]: https://github.com/baojie/shiji-kb/commit/1e6cf8e1
[4baba997]: https://github.com/baojie/shiji-kb/commit/4baba997
[53d9b987]: https://github.com/baojie/shiji-kb/commit/53d9b987
[7f768628]: https://github.com/baojie/shiji-kb/commit/7f768628
[963e49bb]: https://github.com/baojie/shiji-kb/commit/963e49bb
[f5b17c0f]: https://github.com/baojie/shiji-kb/commit/f5b17c0f
[8c43461a]: https://github.com/baojie/shiji-kb/commit/8c43461a
[a1ea0950]: https://github.com/baojie/shiji-kb/commit/a1ea0950
[c3e9b28a]: https://github.com/baojie/shiji-kb/commit/c3e9b28a
[88240e17]: https://github.com/baojie/shiji-kb/commit/88240e17
[7f28fd6c]: https://github.com/baojie/shiji-kb/commit/7f28fd6c
[17554cae]: https://github.com/baojie/shiji-kb/commit/17554cae
[f9db9c20]: https://github.com/baojie/shiji-kb/commit/f9db9c20

---

## 2026-03-13

### 新增 (Added)

- **实体体系扩展至15类** ([f5c09dc] / [de37940] / [60d6484])
  - 新增典籍/礼仪/刑法/思想4类实体类型
- **语义区块全面升级** ([f2e2195])
  - fenced div迁移，83章自动补全太史公曰/赞标注

### 更改 (Changed)

- **v2.0实体标注符号迁移** ([b76caeb])
  - 全书130篇迁移至〖〗格式，消除与Markdown语法冲突
- **封国实体类型新增** ([0e1ee770] / [55b6c22d])
  - v2.1从朝代中剥离诸侯国/封地，使用〖'X〗符号

**详细工作日志**: [`logs/daily/2026-03-13.md`](logs/daily/2026-03-13.md)

[f5c09dc]: https://github.com/baojie/shiji-kb/commit/f5c09dc
[de37940]: https://github.com/baojie/shiji-kb/commit/de37940
[60d6484]: https://github.com/baojie/shiji-kb/commit/60d6484
[f2e2195]: https://github.com/baojie/shiji-kb/commit/f2e2195
[b76caeb]: https://github.com/baojie/shiji-kb/commit/b76caeb
[0e1ee770]: https://github.com/baojie/shiji-kb/commit/0e1ee770
[55b6c22d]: https://github.com/baojie/shiji-kb/commit/55b6c22d

---

## 2026-03-12

### 新增 (Added)

- **跨章因果推理管线** ([3a85dbe8])
  - LLM推理确认338条跨章因果关系，总关系升至7,652条
- **新增SKILL** ([a6658026])
  - 三家注标注、历史地图集成方案、词云TODO
- **史记君主列表数据** ([87813239])
  - 整理过程文档
- **地铁图交互优化** ([ba19e4d4])
  - 功能优化+001五帝本纪事件索引修正

### 更改 (Changed)

- **文档体系重构** ([769377fa] / [5d80ba77])
  - doc/分类整理，新增SKILL_年份消歧、古籍文本语义化
- **SKILL更新** ([aaf9c085])
  - 古籍实体标注/消歧+补充rulers数据

### 项目维护 (Maintenance)

- CHANGELOG整理 ([df69d6a0] / [86abcc51] / [551d7a27])

**详细工作日志**: [`logs/daily/2026-03-12.md`](logs/daily/2026-03-12.md)

[3a85dbe8]: https://github.com/baojie/shiji-kb/commit/3a85dbe8
[a6658026]: https://github.com/baojie/shiji-kb/commit/a6658026
[87813239]: https://github.com/baojie/shiji-kb/commit/87813239
[ba19e4d4]: https://github.com/baojie/shiji-kb/commit/ba19e4d4
[769377fa]: https://github.com/baojie/shiji-kb/commit/769377fa
[5d80ba77]: https://github.com/baojie/shiji-kb/commit/5d80ba77
[aaf9c085]: https://github.com/baojie/shiji-kb/commit/aaf9c085
[df69d6a0]: https://github.com/baojie/shiji-kb/commit/df69d6a0
[86abcc51]: https://github.com/baojie/shiji-kb/commit/86abcc51
[551d7a27]: https://github.com/baojie/shiji-kb/commit/551d7a27

---

## 2026-03-11

### 新增 (Added)

- **十表事件补充提取** ([45809c4])
  - 补充226个事件至十表章节
- **SKILL_事件关系发现合并** ([e96d62e])
  - 整合多个SKILL为唯一权威文档
- **五轮事件年代反思完成** ([fe34b65])
  - 累计2119处修正，数据收敛稳定

### 更改 (Changed)

- **事件关系全量重算** ([6d114e5])
  - 3185事件、7314条关系
- **地铁图系统优化** ([5971549f] / [011b827d])
  - 标签防重叠、app拆分

### 项目维护 (Maintenance)

- 实体HTML索引重建 ([6d114e5])

**详细工作日志**: [`logs/daily/2026-03-11.md`](logs/daily/2026-03-11.md)

[45809c4]: https://github.com/baojie/shiji-kb/commit/45809c4
[e96d62e]: https://github.com/baojie/shiji-kb/commit/e96d62e
[fe34b65]: https://github.com/baojie/shiji-kb/commit/fe34b65
[6d114e5]: https://github.com/baojie/shiji-kb/commit/6d114e5
[5971549f]: https://github.com/baojie/shiji-kb/commit/5971549f
[011b827d]: https://github.com/baojie/shiji-kb/commit/011b827d

---

## 2026-03-10

### 修复 (Fixed)

- **第三轮年代反思** ([039afb0])
  - 465处修正，70章有修正
- **第四轮年代反思** ([16c8f9e])
  - 167处修正，年份准确度完全收敛

**详细工作日志**: [`logs/daily/2026-03-10.md`](logs/daily/2026-03-10.md)

[039afb0]: https://github.com/baojie/shiji-kb/commit/039afb0
[16c8f9e]: https://github.com/baojie/shiji-kb/commit/16c8f9e

---

## 2026-03-09

### 新增 (Added)

- **事件年代推断体系** ([85f39591])
  - Agent反思管线，两轮完成1441处修正
- **SKILL_事件年代推断** ([85f39591])
  - 纪年换算、大事年表交叉验证方法论

### 修复 (Fixed)

- **实体消歧与标签修复** ([b07f7c8a])
  - 破损标签500+处修复，别名扩充586组

### 更改 (Changed)

- **event.html增强** ([868b09ea])
  - 实体链接、年代推断tooltip、历史分期修正
- **参考文献扩充** ([868b09ea])
  - 新增机器学习分期研究、图形化阅读价值系统

**详细工作日志**: [`logs/daily/2026-03-09.md`](logs/daily/2026-03-09.md)

[85f39591]: https://github.com/baojie/shiji-kb/commit/85f39591
[b07f7c8a]: https://github.com/baojie/shiji-kb/commit/b07f7c8a
[868b09ea]: https://github.com/baojie/shiji-kb/commit/868b09ea

---

## 2026-03-08

### 新增 (Added)

- **事件年代推断体系** ([386ac5b8] / [45a71981] / [e55c2ac7])
  - 实验推理年份，中国历史大事年表对齐130章
- **年代反思管线** ([2045a0d3] / [7202556f] / [2c2d570b])
  - 批量生成提示词、逐章反思物料、第一轮Agent执行
- **年代推断SKILL** ([318324b9])
  - 文档重写、时间索引重建
- **event.html增强** ([1971cf2f] / [a292b33f] / [99582262])
  - 事件编号、人物地点链接、年代推断tooltip、分期修正
- **实体链接改进** ([341e33db])
  - 新标签页打开、消歧人名tooltip

### 修复 (Fixed)

- **路径修复** ([72a3538f] / [73c6fdc7])
  - 移除绝对路径

### 更改 (Changed)

- **数据统一** ([e12f805])
  - 实体统计、字数口径、时代分布全面校正

### 项目维护 (Maintenance)

- 参考文献开始记录 ([903e8ac7])
- README/CHANGELOG更新 ([a757995b])

**详细工作日志**: [`logs/daily/2026-03-08.md`](logs/daily/2026-03-08.md)

[386ac5b8]: https://github.com/baojie/shiji-kb/commit/386ac5b8
[45a71981]: https://github.com/baojie/shiji-kb/commit/45a71981
[e55c2ac7]: https://github.com/baojie/shiji-kb/commit/e55c2ac7
[2045a0d3]: https://github.com/baojie/shiji-kb/commit/2045a0d3
[7202556f]: https://github.com/baojie/shiji-kb/commit/7202556f
[2c2d570b]: https://github.com/baojie/shiji-kb/commit/2c2d570b
[318324b9]: https://github.com/baojie/shiji-kb/commit/318324b9
[1971cf2f]: https://github.com/baojie/shiji-kb/commit/1971cf2f
[a292b33f]: https://github.com/baojie/shiji-kb/commit/a292b33f
[99582262]: https://github.com/baojie/shiji-kb/commit/99582262
[341e33db]: https://github.com/baojie/shiji-kb/commit/341e33db
[72a3538f]: https://github.com/baojie/shiji-kb/commit/72a3538f
[73c6fdc7]: https://github.com/baojie/shiji-kb/commit/73c6fdc7
[e12f805]: https://github.com/baojie/shiji-kb/commit/e12f805
[903e8ac7]: https://github.com/baojie/shiji-kb/commit/903e8ac7
[a757995b]: https://github.com/baojie/shiji-kb/commit/a757995b

---

## 2026-03-05

### 新增 (Added)

- **SKU实体增补** ([85df920c])
  - 为394个Factual SKU生成entities.json，关联7497个实体标注
- **知识单元（SKU）体系** ([dc8c13d1])
  - 434个事实知识、241个技能知识、ontology重命名、知识索引文档

**详细工作日志**: [`logs/daily/2026-03-05.md`](logs/daily/2026-03-05.md)

[85df920c]: https://github.com/baojie/shiji-kb/commit/85df920c
[dc8c13d1]: https://github.com/baojie/shiji-kb/commit/dc8c13d1

---

## 2026-02-10

### 项目维护 (Maintenance)

- TODO更新 ([b80c5f93])

**详细工作日志**: [`logs/daily/2026-02-10.md`](logs/daily/2026-02-10.md)

[b80c5f93]: https://github.com/baojie/shiji-kb/commit/b80c5f93

---

## 2026-02-09

### 新增 (Added)

- **时间线实体系统** ([59c3814f] / [1826fe19] / [60d67289])
  - 年份消歧扩展，覆盖全部非年表章节，历代君主在位年份数据库
- **语义消歧重构** ([2580cfcc])
  - 元数据驱动，不修改原文
- **命名实体索引系统** ([f586a618] / [3c7e5121])
  - 11类实体索引页面+正文实体链接+别名自动检测
- **十表表格渲染管线** ([b77c59fb] / [6f5a9d38])
  - 013-022完整表格渲染

### 项目维护 (Maintenance)

- README与CHANGELOG更新 ([e1140f12] / [b48bdfbc])

**详细工作日志**: [`logs/daily/2026-02-09.md`](logs/daily/2026-02-09.md)

[59c3814f]: https://github.com/baojie/shiji-kb/commit/59c3814f
[1826fe19]: https://github.com/baojie/shiji-kb/commit/1826fe19
[60d67289]: https://github.com/baojie/shiji-kb/commit/60d67289
[2580cfcc]: https://github.com/baojie/shiji-kb/commit/2580cfcc
[f586a618]: https://github.com/baojie/shiji-kb/commit/f586a618
[3c7e5121]: https://github.com/baojie/shiji-kb/commit/3c7e5121
[b77c59fb]: https://github.com/baojie/shiji-kb/commit/b77c59fb
[6f5a9d38]: https://github.com/baojie/shiji-kb/commit/6f5a9d38
[e1140f12]: https://github.com/baojie/shiji-kb/commit/e1140f12
[b48bdfbc]: https://github.com/baojie/shiji-kb/commit/b48bdfbc

---

## 2026-02-08

### 新增 (Added)

- **全部130章小节划分** ([98d97a32])
  - 完整小节ID系统，sections_data.json
- **质量检查工具** ([60cb4bbb] / [cb60f925])
  - Markdown和HTML代码检查

### 修复 (Fixed)

- **HTML渲染修复** ([fbf6b4b9] / [edcf5956])
  - 嵌套标注符号、韵文格式、对话缩进、赞格式
- **韵文自动分行** ([253e1cb5])
  - 修复项羽本纪多余>符号
- **对话缩进排版** ([e43a4076])
  - 长引号内容缩进两个汉字
- **临时脚本修复** ([e7e62877])

### 更改 (Changed)

- **项目结构重构** ([0de6edc5] / [e5d84291])
  - 工具脚本移入scripts/，文档移入doc/
- **小节提取功能增强** ([4e6687d8])
  - 支持更多格式

### 项目维护 (Maintenance)

- 开发工作流程文档 ([3d9f0cee] / [d6201aac] / [b28693a6])
- README与CHANGELOG更新 ([11d33403])
- GitHub Pages内容更新 ([578dc3eb] / [4dd597dd] / [d91410b8] / [90e5ac7c] / [fc268b00])

**详细工作日志**: [`logs/daily/2026-02-08.md`](logs/daily/2026-02-08.md)

[98d97a32]: https://github.com/baojie/shiji-kb/commit/98d97a32
[60cb4bbb]: https://github.com/baojie/shiji-kb/commit/60cb4bbb
[cb60f925]: https://github.com/baojie/shiji-kb/commit/cb60f925
[fbf6b4b9]: https://github.com/baojie/shiji-kb/commit/fbf6b4b9
[edcf5956]: https://github.com/baojie/shiji-kb/commit/edcf5956
[253e1cb5]: https://github.com/baojie/shiji-kb/commit/253e1cb5
[e43a4076]: https://github.com/baojie/shiji-kb/commit/e43a4076
[e7e62877]: https://github.com/baojie/shiji-kb/commit/e7e62877
[0de6edc5]: https://github.com/baojie/shiji-kb/commit/0de6edc5
[e5d84291]: https://github.com/baojie/shiji-kb/commit/e5d84291
[4e6687d8]: https://github.com/baojie/shiji-kb/commit/4e6687d8
[3d9f0cee]: https://github.com/baojie/shiji-kb/commit/3d9f0cee
[d6201aac]: https://github.com/baojie/shiji-kb/commit/d6201aac
[b28693a6]: https://github.com/baojie/shiji-kb/commit/b28693a6
[11d33403]: https://github.com/baojie/shiji-kb/commit/11d33403
[578dc3eb]: https://github.com/baojie/shiji-kb/commit/578dc3eb
[4dd597dd]: https://github.com/baojie/shiji-kb/commit/4dd597dd
[d91410b8]: https://github.com/baojie/shiji-kb/commit/d91410b8
[90e5ac7c]: https://github.com/baojie/shiji-kb/commit/90e5ac7c
[fc268b00]: https://github.com/baojie/shiji-kb/commit/fc268b00

---

## 2026-02-07

### 新增 (Added)

- **词频统计分析** ([952f6407])
  - 史记原文词频
- **index.html增强** ([b197f8ba] / [d4bfcb4c])
  - 可折叠功能、卡片布局、章节描述
- **史记争霸游戏** ([ea394ea2])
  - 相关文件添加

### 修复 (Fixed)

- **HTML章节导航修复** ([640b0a43] / [69f1ed85])
  - 所有章节导航链接、移除.tagged后缀

### 更改 (Changed)

- **项目结构重构** ([2f8f0ade] / [c4ee99f1] / [dc95939d] / [01e95775])
  - 文档结构、Python脚本结构整理
- **知识图谱脚本规范** ([863b6c38] / [03feca6b])
  - 统一命名和输出路径，临时脚本整理

### 项目维护 (Maintenance)

- CHANGELOG创建 ([045a112b] / [5bb03459])
- README更新 ([47522cf2] / [af47a614] / [d5c39500])
- 项目愿景更新 ([210d11d1])
- 完整build ([f379b113] / [adad334d])

**详细工作日志**: [`logs/daily/2026-02-07.md`](logs/daily/2026-02-07.md)

[952f6407]: https://github.com/baojie/shiji-kb/commit/952f6407
[b197f8ba]: https://github.com/baojie/shiji-kb/commit/b197f8ba
[d4bfcb4c]: https://github.com/baojie/shiji-kb/commit/d4bfcb4c
[ea394ea2]: https://github.com/baojie/shiji-kb/commit/ea394ea2
[640b0a43]: https://github.com/baojie/shiji-kb/commit/640b0a43
[69f1ed85]: https://github.com/baojie/shiji-kb/commit/69f1ed85
[2f8f0ade]: https://github.com/baojie/shiji-kb/commit/2f8f0ade
[c4ee99f1]: https://github.com/baojie/shiji-kb/commit/c4ee99f1
[dc95939d]: https://github.com/baojie/shiji-kb/commit/dc95939d
[01e95775]: https://github.com/baojie/shiji-kb/commit/01e95775
[863b6c38]: https://github.com/baojie/shiji-kb/commit/863b6c38
[03feca6b]: https://github.com/baojie/shiji-kb/commit/03feca6b
[045a112b]: https://github.com/baojie/shiji-kb/commit/045a112b
[5bb03459]: https://github.com/baojie/shiji-kb/commit/5bb03459
[47522cf2]: https://github.com/baojie/shiji-kb/commit/47522cf2
[af47a614]: https://github.com/baojie/shiji-kb/commit/af47a614
[d5c39500]: https://github.com/baojie/shiji-kb/commit/d5c39500
[210d11d1]: https://github.com/baojie/shiji-kb/commit/210d11d1
[f379b113]: https://github.com/baojie/shiji-kb/commit/f379b113
[adad334d]: https://github.com/baojie/shiji-kb/commit/adad334d

---

## 2026-02-06

### 新增 (Added)

- **游戏原型初版** ([79499a12])
- **006章节添加** ([ea16b8e9])

### 项目维护 (Maintenance)

- GitHub Pages更新 ([02508b48] / [631eb21f] / [70cdb0de])

**详细工作日志**: [`logs/daily/2026-02-06.md`](logs/daily/2026-02-06.md)

[79499a12]: https://github.com/baojie/shiji-kb/commit/79499a12
[ea16b8e9]: https://github.com/baojie/shiji-kb/commit/ea16b8e9
[02508b48]: https://github.com/baojie/shiji-kb/commit/02508b48
[631eb21f]: https://github.com/baojie/shiji-kb/commit/631eb21f
[70cdb0de]: https://github.com/baojie/shiji-kb/commit/70cdb0de

---

## 2026-01

### 新增 (Added)

- **核心标注系统建立** ([73c7aed])
  - 11类实体标注规范，Purple Numbers段落编号，Markdown转HTML核心工具
- **样式系统**
  - 实体语法高亮11色，对话样式，段落锚点
- **文本结构化**
  - 智能段落拆分，对话拆分，列表识别，诗歌排版

[73c7aed]: https://github.com/baojie/shiji-kb/commit/73c7aed

---

## 2025-02至03

### 新增 (Added)

- **项目启动** ([256f6cc])
  - 手工编写RDF/TTL知识图谱，创建本体文件，建立GitHub仓库
- **技术路线转型**
  - 拆分130篇原文，转向Markdown标注系统

[256f6cc]: https://github.com/baojie/shiji-kb/commit/256f6cc

---

## 标注进度统计

| Commit | 日期 | 已标注章节 | 完成度 | 里程碑 |
|--------|------|-----------|--------|--------|
| [1b3bc8ad](https://github.com/baojie/shiji-kb/commit/1b3bc8ad) | 2026-03-20 | 130/130 | 100% ✅ | 实体边界错误第三轮反思：17处修饰词切分错误 |
| [cca73582](https://github.com/baojie/shiji-kb/commit/cca73582) | 2026-03-19 | 130/130 | 100% ✅ | 动词标注完成：002-130全部章节 |
| [99af56d6](https://github.com/baojie/shiji-kb/commit/99af56d6) | 2026-03-19 | 130/130 | 100% ✅ | 实体边界错误综合反思：75处切分错误修正 |
| [4c96f109](https://github.com/baojie/shiji-kb/commit/4c96f109) | 2026-03-19 | 130/130 | 100% ✅ | 身份标注修复：8,774处符号语义漂移 |
| [08a4c5bb](https://github.com/baojie/shiji-kb/commit/08a4c5bb) | 2026-03-18 | 130/130 | 100% ✅ | 第二轮实体标注反思批量处理完成 |
| [0cd03a76](https://github.com/baojie/shiji-kb/commit/0cd03a76) | 2026-03-18 | 130/130 | 100% ✅ | 第二轮实体反思：93章标注修正 |
| [7c329904](https://github.com/baojie/shiji-kb/commit/7c329904) | 2026-03-17 | 130/130 | 100% ✅ | 第一轮实体反思总结：全书130章修正1,913处 |
| [67e2c639](https://github.com/baojie/shiji-kb/commit/67e2c639) | 2026-03-17 | 130/130 | 100% ✅ | 第一轮实体反思：013-130章修正756处 |
| [05f6e9a7](https://github.com/baojie/shiji-kb/commit/05f6e9a7) | 2026-03-17 | 130/130 | 100% ✅ | 人名实体跨章反思：615处修正 |
| [b468df8c](https://github.com/baojie/shiji-kb/commit/b468df8c) | 2026-03-16 | 130/130 | 100% ✅ | 011章第二次反思：32处修正+汉姓规则 |
| [9037f7cb](https://github.com/baojie/shiji-kb/commit/9037f7cb) | 2026-03-16 | 130/130 | 100% ✅ | 单字人名消歧反思：001-010章39处修正 |
| [53d9b987](https://github.com/baojie/shiji-kb/commit/53d9b987) | 2026-03-14 | 130/130 | 100% ✅ | v2.2身份类反思：4,297次标注恢复扩充 |
| [4baba997](https://github.com/baojie/shiji-kb/commit/4baba997) | 2026-03-14 | 130/130 | 100% ✅ | v2.2地名反思：60处重分类 |
| [1e6cf8e1](https://github.com/baojie/shiji-kb/commit/1e6cf8e1) | 2026-03-14 | 130/130 | 100% ✅ | v2.2官职反思：2,290处重分类 |
| [d5967cdc](https://github.com/baojie/shiji-kb/commit/d5967cdc) | 2026-03-14 | 130/130 | 100% ✅ | v2.2族群/氏族分类：195处重分类 |
| [fe34b654](https://github.com/baojie/shiji-kb/commit/fe34b654) | 2026-03-11 | 130/130 | 100% ✅ | 事件年代第五轮反思：46处修正 |
| [16c8f9e8](https://github.com/baojie/shiji-kb/commit/16c8f9e8) | 2026-03-10 | 130/130 | 100% ✅ | 事件年代第四轮反思：167处修正 |
| [85f39591](https://github.com/baojie/shiji-kb/commit/85f39591) | 2026-03-09 | 130/130 | 100% ✅ | 事件年代第一二轮反思：1,441处修正 |
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

**最后更新**: 2026-03-21
