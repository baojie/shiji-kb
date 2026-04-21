# SKILL文档索引

> 完整的史记知识库SKILL体系索引，包含元技能（Meta-Skills）和管线技能（Pipeline Skills）

**最后更新**：2026-04-21

---

## 导航

- [元技能（Meta-Skills）](#元技能meta-skills) - 14个通用方法论
- [管线技能（Pipeline Skills）](#管线技能pipeline-skills) - 87个专项技能
  - [00 管线总览](#00-管线总览)
  - [01 古籍校勘](#01-古籍校勘)
  - [02 结构分析](#02-结构分析)
  - [03 实体构建](#03-实体构建)
  - [04 事件构建](#04-事件构建)
  - [05 关系构建](#05-关系构建)
  - [06 本体构造和知识库管理](#06-本体构造和知识库管理)
  - [07 逻辑推理](#07-逻辑推理)
  - [08 知识库管驭](#08-知识库管驭)
  - [09 应用构造](#09-应用构造)
  - [10 项目管理](#10-项目管理)
- [参考文档（References）](#参考文档references) - 28个支撑文档
- [草稿文档（Drafts）](#草稿文档drafts) - 待完善的元技能
- [归档文档（Archive）](#归档文档archive) - 3个历史文档

---

## 元技能（Meta-Skills）

> 通用知识工程方法论，适用于所有工序和类似项目

| 编号 | 文件 | 说明 | 核心概念 |
|------|------|------|---------|
| 00-M00 | [00-META-00_好东西都是总结出来的.md](00-META-00_好东西都是总结出来的.md) | 元技能的元技能，OTF+JIT+Bootstrap | 从实践到理论的升华 |
| 00-M01 | [00-META-01_反思.md](00-META-01_反思.md) | Agent驱动的质量审查通用方法论 | 按章/按类型/多轮收敛 |
| 00-M02 | [00-META-02_迭代工作流.md](00-META-02_迭代工作流.md) | MVP→生产的系统化迭代 | 2-5轮迭代方法论 |
| 00-M03 | [00-META-03_冷启动.md](00-META-03_冷启动.md) | 新工序启动方法 | 手工样本→MVP规则→试点→扩展 |
| 00-M04 | [00-META-04_柳叶刀方法.md](00-META-04_柳叶刀方法.md) | 精细分解与混合解决方案 | LLM+规则+代码分工 |
| 00-M05 | [00-META-05_知识作为上下文压缩.md](00-META-05_知识作为上下文压缩.md) | KG价值论证 | 10x-10000x压缩比 |
| 00-M06 | [00-META-06_SKILL优化与演化.md](00-META-06_SKILL优化与演化.md) | SKILL持续改进策略 | 版本迭代、渐进载入 |
| 00-M07 | [00-META-07_可读性.md](00-META-07_可读性.md) | 人类优先的数据格式设计 | Token/Markdown/Git友好 |
| 00-M08 | [00-META-08_标注体系设计.md](00-META-08_标注体系设计.md) | Token标注体系设计原则 | v1.0→v2.5演化/23类实体 |
| 00-M09 | [00-META-09_Agent提示词工程.md](00-META-09_Agent提示词工程.md) | SKILL文档驱动的提示词设计 | 五层金字塔结构 |
| 00-M10 | [00-META-10_质量控制.md](00-META-10_质量控制.md) | Lint/Validate工具链设计 | 五层质检体系 |
| 00-M11 | [00-META-11_数据体感培养.md](00-META-11_数据体感培养.md) | 直接观察数据的十层体系 | 统计无法替代观察 |
| 00-M12 | [00-META-12_数据融合.md](00-META-12_数据融合.md) | 多源数据对齐/消歧/去重 | 字符串→实体→事件→SKU |
| 00-M13 | [00-META-13_技能迁移.md](00-META-13_技能迁移.md) | SKILL跨项目迁移方法论 | 史记→汉书→通鉴 |

**PDF合集下载**：[大规模知识库构造元技能方法论.pdf](../resources/publications/meta-skill-book/大规模知识库构造元技能方法论.pdf)
（发布日期：2026-03-18，425页，2.35MB，包含14个元技能）

---

## 管线技能（Pipeline Skills）

> 古籍知识库构造完整技术栈，从校勘到应用的九步管线 + 项目管理

### 00 管线总览

| 编号 | 文件 | 说明 |
|------|------|------|
| 00 | [SKILL_00_管线总览.md](SKILL_00_管线总览.md) | 完整管线架构、工序流程、数据流转 |

### 01 古籍校勘

| 编号 | 文件 | 说明 |
|------|------|------|
| 01 | [SKILL_01_古籍校勘.md](SKILL_01_古籍校勘.md) | 底本校正，生成定本 |
| 01a | [SKILL_01a_标注完整性维护.md](SKILL_01a_标注完整性维护.md) | 标注后完整性校验，确保未篡改原文 |
| 01b | [SKILL_01b_多版本互校底本.md](SKILL_01b_多版本互校底本.md) | 多版本对照校勘方法论 |
| 01c | [SKILL_01c_表格校勘规范.md](SKILL_01c_表格校勘规范.md) | 年表/世家类章节的表格校勘规范 |
| 01d | [SKILL_01d_正音与拼音标注.md](SKILL_01d_正音与拼音标注.md) | 古音标注与拼音处理 |
| 01e | [SKILL_01e_繁简体处理.md](SKILL_01e_繁简体处理.md) | 繁简转换与异体字统一（归入校勘工序） |
| 01f | [SKILL_01f_句读和标点校勘.md](SKILL_01f_句读和标点校勘.md) | 句读断句、标点符号规范、质量控制（最前置工序） |
| 01g | [SKILL_01g_标注符号集合原则.md](SKILL_01g_标注符号集合原则.md) | 标点/标注/Markdown符号完全分离原则 |
| 01h | [SKILL_01h_白话翻译.md](SKILL_01h_白话翻译.md) | 史记章节按PN段落进行文言文到白话文的翻译规范 |

### 02 结构分析

| 编号 | 文件 | 说明 |
|------|------|------|
| 02 | [SKILL_02_结构分析.md](SKILL_02_结构分析.md) | 阶段总览 |
| 02a | [SKILL_02a_章节切分与编号.md](SKILL_02a_章节切分与编号.md) | 段落编号 + 小节划分 + 对话拆分 |
| 02b | [SKILL_02b_区块与韵文处理.md](SKILL_02b_区块与韵文处理.md) | 太史公曰/赞/策论 + 韵文检测 |
| 02c | [SKILL_02c_三家注标注.md](SKILL_02c_三家注标注.md) | 裴骃/司马贞/张守节 注释层 |
| 02d | [SKILL_02d_结构语义分析.md](SKILL_02d_结构语义分析.md) | 句间/段间/章间语义关系 + 注释对齐 |
| 02e | [SKILL_02e_词法分析.md](SKILL_02e_词法分析.md) | 字级词性标注、遗漏实体发现 |
| 02f | [SKILL_02f_文本统计.md](SKILL_02f_文本统计.md) | 字数/句长/词频/实体密度/五体对比 |
| 02g | [SKILL_02g_表格结构语义分析.md](SKILL_02g_表格结构语义分析.md) | 史记十表维度定义、关系挖掘 |
| 02h | [SKILL_02h_词表构建.md](SKILL_02h_词表构建.md) | 受控词表通用原则、surface/canonical 四列结构 |
| 02i | [SKILL_02i_指代消解.md](SKILL_02i_指代消解.md) | 人称代词、身份指代语义消解 |
| 02j | [SKILL_02j_修辞标注.md](SKILL_02j_修辞标注.md) | 〘※〙 符号规范、消歧格式、HTML 渲染 |
| 02k | [SKILL_02k_成语识别.md](SKILL_02k_成语识别.md) | 成语识别工作流：四轮反思、双轨架构、验证四分类 |

### 03 实体构建

| 编号 | 文件 | 说明 |
|------|------|------|
| 03 | [SKILL_03_实体构建.md](SKILL_03_实体构建.md) | 阶段总览 |
| 03a | [SKILL_03a_实体标注.md](SKILL_03a_实体标注.md) | 23类实体NER标注（19类名词+4类动词） |
| 03b | [SKILL_03b_人名消歧.md](SKILL_03b_人名消歧.md) | 同名异人/异名同人消歧 |
| 03c | [SKILL_03c_按章反思.md](SKILL_03c_按章反思.md) | 按章反思审查，系统性误标修正 |
| 03d | [SKILL_03d_渲染与发布.md](SKILL_03d_渲染与发布.md) | HTML渲染与结构语义表现（衔接SKILL 09a） |
| 03e | [SKILL_03e_按类型反思.md](SKILL_03e_按类型反思.md) | 按类型反思总入口（路由到 03e1/03e2） |
| 03e1 | [references/SKILL_03e1_跨类型迁移.md](references/SKILL_03e1_跨类型迁移.md) | 跨类型迁移：源头标错类的整体迁移（三阶段法 always/context/new_candidates） |
| 03e2 | [references/SKILL_03e2_按类型反思纠错.md](references/SKILL_03e2_按类型反思纠错.md) | 按类型反思纠错：对一级实体类型做多轮反思+纠错（L1-L5 分层 + R1-R7 反思），子类设计为起点。方法论见 doc/entities/实体细分分类与纠错方法论.md |
| 03f | [SKILL_03f_实体边界错误综合反思.md](SKILL_03f_实体边界错误综合反思.md) | 实体边界错误专项反思 |
| 03g | [SKILL_03g_时间实体消歧.md](SKILL_03g_时间实体消歧.md) | 相对年份→公元年（76.8%覆盖率，6648条） |
| 03h | [SKILL_03h_地名地段分类.md](SKILL_03h_地名地段分类.md) | place 实体"地段"二级分类（水域/山脉/城邑/郡/县/建筑…，14类） |
| 03i | [SKILL_03i_官职分类.md](SKILL_03i_官职分类.md) | official 实体"职类"二级分类（三公/九卿/军职/爵位/王号…，21类） |
| 03j | [SKILL_03j_人名分类.md](SKILL_03j_人名分类.md) | person 实体"身份类"二级分类（帝王/将相/谋臣/学者…，16类）+ alias 合并工作流 |

### 04 事件构建

| 编号 | 文件 | 说明 |
|------|------|------|
| 04 | [SKILL_04_事件构建.md](SKILL_04_事件构建.md) | 阶段总览 |
| 04a | [SKILL_04a_事件识别.md](SKILL_04a_事件识别.md) | 事件定义/Schema/类型/提取 |
| 04b | [SKILL_04b_十表事件处理.md](SKILL_04b_十表事件处理.md) | 十表（013-022）专用补充 |
| 04c | [SKILL_04c_事件年代推断.md](SKILL_04c_事件年代推断.md) | 分层纪年解析 |
| 04d | [SKILL_04d_事件年代审查.md](SKILL_04d_事件年代审查.md) | Agent反思审查工作流 |
| 04e | [SKILL_04e_年份消歧.md](SKILL_04e_年份消歧.md) | 年号/纪年消歧 |
| 04f | [SKILL_04f_动词标注.md](SKILL_04f_动词标注.md) | 动词标注方法论（谓词提取） |

### 05 关系构建

| 编号 | 文件 | 说明 |
|------|------|------|
| 05 | [SKILL_05_关系构建.md](SKILL_05_关系构建.md) | 阶段总览（7,637条关系，9种类型） |
| 05a | [SKILL_05a_事件关系发现.md](SKILL_05a_事件关系发现.md) | 9种关系类型/自动+LLM发现 |
| 05b | [SKILL_05b_实体关系构建.md](SKILL_05b_实体关系构建.md) | 地点/制度/事物关系 + SPO三元组 |
| 05c | [SKILL_05c_人物关系构建.md](SKILL_05c_人物关系构建.md) | 人物共现→家族推理→政治社会关系 |
| 05d | [SKILL_05d_事实发现.md](SKILL_05d_事实发现.md) | 原子事实三元组（~10万条） |
| 05e | [SKILL_05e_战争事件识别.md](SKILL_05e_战争事件识别.md) | 战争事件专项提取（736个） |

### 06 本体构造和知识库管理

| 编号 | 文件 | 说明 |
|------|------|------|
| 06 | [SKILL_06_本体构造和知识库管理.md](SKILL_06_本体构造和知识库管理.md) | 阶段总览 |
| 06a | [SKILL_06a_实体到本体.md](SKILL_06a_实体到本体.md) | 实体词表 → 分类树 → OWL/RDF |
| 06b | [SKILL_06b_属性关系约束构建.md](SKILL_06b_属性关系约束构建.md) | 属性/关系/约束定义、OWL properties和constraints（规划） |
| 06c | [SKILL_06c_规则构建.md](SKILL_06c_规则构建.md) | 领域规则/推理规则/验证规则（规划） |
| 06d | [SKILL_06d_推理机构建.md](SKILL_06d_推理机构建.md) | 本体/规则推理、约束检查、冲突检测（规划） |
| 06e | [SKILL_06e_概念分类树构建.md](SKILL_06e_概念分类树构建.md) | Bottom-Up 分类树构建、实例→归纳→TTL→MD、颗粒度动态调整 |

### 07 逻辑推理

| 编号 | 文件 | 说明 |
|------|------|------|
| 07 | [SKILL_07_逻辑推理.md](SKILL_07_逻辑推理.md) | 矛盾检测 + 洞见挖掘 + 本体/时间/关系推理 |
| 07a | [SKILL_07a_人物生卒年推断.md](SKILL_07a_人物生卒年推断.md) | 人物生卒年区间推断 |
| 07b | [SKILL_07b_姓氏推理.md](SKILL_07b_姓氏推理.md) | 先秦人物姓/氏区分，多轮迭代推理 |
| 07c | [SKILL_07c_反常推理.md](SKILL_07c_反常推理.md) | 单条事实违反常识/制度/规律的异常点检测 |
| 07d | [SKILL_07d_溯源推理.md](SKILL_07d_溯源推理.md) | 历史事件的溯源推理方法论 |
| 07e | [SKILL_07e_真实性推理.md](SKILL_07e_真实性推理.md) | 历史记载真实性推理方法论 |
| 07f | [SKILL_07f_历史专著方法提炼.md](SKILL_07f_历史专著方法提炼.md) | 从历史学专著中提炼研究方法论 |

### 08 知识库管驭

| 编号 | 文件 | 说明 |
|------|------|------|
| 08 | [SKILL_08_知识库管驭.md](SKILL_08_知识库管驭.md) | 知识库工程化管理（粒度/覆盖度/成本/质量） |
| 08a | [SKILL_08a_知识颗粒度管理.md](SKILL_08a_知识颗粒度管理.md) | SKU标准知识单元设计（Factual/Procedural/Relational）（规划） |
| 08b | [SKILL_08b_知识覆盖度评估.md](SKILL_08b_知识覆盖度评估.md) | 覆盖度评估、测试样本构建、缺口识别（规划） |
| 08c | [SKILL_08c_成本管控和Token节约.md](SKILL_08c_成本管控和Token节约.md) | LLM成本优化、Token节约策略（规划） |
| 08d | [SKILL_08d_正确性评估.md](SKILL_08d_正确性评估.md) | 质量评估方法、正确性指标体系（规划） |
| 08e | [SKILL_08e_表格数据反思迭代提取方法.md](SKILL_08e_表格数据反思迭代提取方法.md) | 表格数据反思迭代提取方法 |
| 08f | [SKILL_08f_置信度函数设计.md](SKILL_08f_置信度函数设计.md) | 通用置信度函数设计：反思归纳→分层信号→阈值标定 |

### 09 应用构造

| 编号 | 文件 | 说明 |
|------|------|------|
| 09 | [SKILL_09_应用构造.md](SKILL_09_应用构造.md) | 阶段总览 |
| 09a | [SKILL_09a_语法高亮辅助阅读.md](SKILL_09a_语法高亮辅助阅读.md) | 语法高亮渲染 + 实体配色 + 段落锚点 + 发布 |
| 09b | [SKILL_09b_知识库游戏化.md](SKILL_09b_知识库游戏化.md) | 知识库→游戏：SKU→技能卡、事件→剧情 |
| 09c | [SKILL_09c_个性化阅读支持.md](SKILL_09c_个性化阅读支持.md) | 语法高亮/繁简/拼音/Purple Numbers个性化阅读 |
| 09d | [SKILL_09d_语义搜索和探索.md](SKILL_09d_语义搜索和探索.md) | 基于知识图谱的语义搜索和知识探索（规划） |
| 09e | [SKILL_09e_故事创作.md](SKILL_09e_故事创作.md) | 公众号文章/博客/剧本/小说创作（规划） |
| 09f | [SKILL_09f_音频创作.md](SKILL_09f_音频创作.md) | AI朗读/播客/有声书/音频课程（规划） |
| 09g | [SKILL_09g_视频创作.md](SKILL_09g_视频创作.md) | 短视频/中长视频/纪录片/电影（规划） |
| 09h | [SKILL_09h_图片与漫画创作.md](SKILL_09h_图片与漫画创作.md) | 插图/头像/四格漫画/长篇漫画/表情包（规划） |
| 09i | [SKILL_09i_信息图与可视化.md](SKILL_09i_信息图与可视化.md) | 信息图/交互图表/时间线/关系网络/地理可视化（规划） |
| 09j | [SKILL_09j_历史地图.md](SKILL_09j_历史地图.md) | 静态/交互/时空/3D地图、专题地图（规划） |
| 09k | [SKILL_09k_专业文献写作.md](SKILL_09k_专业文献写作.md) | 学术论文/研究报告/专著章节/百科条目（规划） |
| 09l | [SKILL_09l_考古辅助.md](SKILL_09l_考古辅助.md) | 出土文本校勘/考古报告对照/文物推理/断代（规划） |
| 09m | [SKILL_09m_排版和电子书构造.md](SKILL_09m_排版和电子书构造.md) | 古籍专业排版、PDF/EPUB生成、紫色编号锚点（规划） |

### 10 项目管理

| 编号 | 文件 | 说明 |
|------|------|------|
| 10 | [SKILL_10_项目管理.md](SKILL_10_项目管理.md) | 阶段总览（Issue/TODO/日志/Git/CHANGELOG） |
| 10a | [SKILL_10a_TODO和Issue管理.md](SKILL_10a_TODO和Issue管理.md) | 7类Issue分类、TODO任务对应、批量管理脚本 |
| 10b | [SKILL_10b_每日工作日志维护.md](SKILL_10b_每日工作日志维护.md) | 工作日划分、微信通知、太史公曰、改动意义分析 |
| 10c | [SKILL_10c_Git代码版本管理规范.md](SKILL_10c_Git代码版本管理规范.md) | Git提交消息格式、原子提交、Pre-commit Hook处理、分支策略 |
| 10d | [SKILL_10d_CHANGELOG编写规范.md](SKILL_10d_CHANGELOG编写规范.md) | CHANGELOG格式、详略原则、Commit/Issue链接 |
| 10e | [SKILL_10e_文件组织与目录结构.md](SKILL_10e_文件组织与目录结构.md) | 项目目录结构规范、文件分类决策树、流转路径 |
| 10f | [SKILL_10f_Skill的提炼与转化.md](SKILL_10f_Skill的提炼与转化.md) | Skill工程化规范、质量检查、脚本关联 |
| 10g | [SKILL_10g_项目成本与时间统计.md](SKILL_10g_项目成本与时间统计.md) | Token成本统计、用户时间投入统计、工作效率分析、定期报告生成 |

**PDF合集下载**：[史记知识库构造管线技能手册.pdf](../resources/publications/pipeline-skills-book/史记知识库构造管线技能手册.pdf)
（发布日期：2026-03-19，438页，3.01MB，包含40个管线SKILL）

---

## 参考文档（References）

> 支撑主SKILL的详细规则库、方法论细节与数据表，按关联一级SKILL分组

### 01 古籍校勘相关

| 文件 | 说明 | 关联SKILL |
|------|------|----------|
| [SKILL_01a1_标注格式规范.md](references/SKILL_01a1_标注格式规范.md) | 史记知识库 Markdown 和 HTML 格式完整规范 | SKILL_01a |
| [SKILL_01d1_词表设计原则详解.md](references/SKILL_01d1_词表设计原则详解.md) | 特殊读音词表设计原则、版本演化、典型案例分析 | SKILL_01d |
| [SKILL_01d2_史记正义提取方法.md](references/SKILL_01d2_史记正义提取方法.md) | 从《史记正义》提取特殊读音的方法论与质检流程 | SKILL_01d |
| [SKILL_01d3_技术实现细节.md](references/SKILL_01d3_技术实现细节.md) | 前端 Ruby 标注技术、性能优化、故障排除 | SKILL_01d |
| [SKILL_01d4_拼音标注质量规范v3.0.md](references/SKILL_01d4_拼音标注质量规范v3.0.md) | 拼音标注质量规范与评估指标 v3.0 | SKILL_01d |
| [SKILL_01d5_多音字处理分析.md](references/SKILL_01d5_多音字处理分析.md) | 多音字处理方案总结、基础统计与策略 | SKILL_01d |
| [SKILL_01d6_拼音注释功能规范.md](references/SKILL_01d6_拼音注释功能规范.md) | HTML5 `<ruby>` 拼音注释功能完整规范 | SKILL_01d |
| [SKILL-01e-rules-繁简词表构造规则.md](references/SKILL-01e-rules-繁简词表构造规则.md) | 繁简词表完整构造规则 | SKILL_01e |
| [SKILL_01f_background.md](references/SKILL_01f_background.md) | 句读与标点校勘背景、换行配置、技术方案对比、FAQ | SKILL_01f |
| [SKILL_01f_code_examples.md](references/SKILL_01f_code_examples.md) | gj.cool API / 本地模型断句 / 标点规范化代码示例 | SKILL_01f |

### 02 结构分析相关

| 文件 | 说明 | 关联SKILL |
|------|------|----------|
| [SKILL_02a1_Purple_Numbers编号详细规范.md](references/SKILL_02a1_Purple_Numbers编号详细规范.md) | PN 三级编号格式、父子关系、连续性规则 | SKILL_02a |
| [SKILL_02a2_回车规则.md](references/SKILL_02a2_回车规则.md) | 标注文件段落内换行与合并规则 | SKILL_02a |
| [SKILL_02b1_韵文识别规则.md](references/SKILL_02b1_韵文识别规则.md) | 赞/诗歌/赋自动识别与标题提取规则 | SKILL_02b |
| [SKILL_02b2_散文识别规则.md](references/SKILL_02b2_散文识别规则.md) | 诏令/奏疏/书信/檄文/策论/议论识别 + manifest 维护 | SKILL_02b |
| [SKILL_02b2_赞文排版质量控制.md](references/SKILL_02b2_赞文排版质量控制.md) | 赞文四言韵文排版规范、格式检查与自动修复 | SKILL_02b |
| [SKILL_02e1_动词标注规范.md](references/SKILL_02e1_动词标注规范.md) | 动词标注完整语法规范、分类体系（v3.3） | SKILL_02e |

### 03 实体构建相关

| 文件 | 说明 | 关联SKILL |
|------|------|----------|
| [SKILL_03a1_标注符号迁移.md](references/SKILL_03a1_标注符号迁移.md) | 标注符号系统级迁移实战方法论 | SKILL_03a |
| [SKILL_03c1-v2-rules.md](references/SKILL_03c1-v2-rules.md) | 按章反思规律库 v2（134 条，压缩版；v1 见 archive） | SKILL_03c |
| [SKILL_03e1_跨类型迁移.md](references/SKILL_03e1_跨类型迁移.md) | 跨类型迁移：源头标错类的整体迁移（always/context/new_candidates 三阶段法） | SKILL_03e |
| [SKILL_03e2_按类型反思纠错.md](references/SKILL_03e2_按类型反思纠错.md) | 按类型反思纠错：一级类型 L1-L5 分层 + R1-R7 多轮反思（方法论见 doc/entities/实体细分分类与纠错方法论.md） | SKILL_03e |

### 04–05 事件与关系相关

| 文件 | 说明 | 关联SKILL |
|------|------|----------|
| [SKILL_04f1-rules.md](references/SKILL_04f1-rules.md) | 动词标注规律库 V.1-V.8 + E 系列格式残留扫描 | SKILL_04f |
| [SKILL_05d1_rules.md](references/SKILL_05d1_rules.md) | 事实抽取四大核心原则（v1.0） | SKILL_05d |

### 08 知识库管驭相关

| 文件 | 说明 | 关联SKILL |
|------|------|----------|
| [SKILL_08b1_标注完成情况统计.md](references/SKILL_08b1_标注完成情况统计.md) | 字级/实体级/章节级/专题级四类标注统计方法 | SKILL_08b |

### 10 项目管理相关

| 文件 | 说明 | 关联SKILL |
|------|------|----------|
| [SKILL_10c1_禁止命令清单.md](references/SKILL_10c1_禁止命令清单.md) | `.claude/settings.json` deny 列表分析与建议 | SKILL_10c |
| [SKILL_10f1_模板库.md](references/SKILL_10f1_模板库.md) | Skill 标准结构模板库 | SKILL_10f |
| [SKILL_10f2_精简拆分案例库.md](references/SKILL_10f2_精简拆分案例库.md) | Skill 超过 500 行的精简与拆分案例 | SKILL_10f |
| [SKILL_10f3_更新维护指南.md](references/SKILL_10f3_更新维护指南.md) | Skill 更新触发条件、标准流程、验证方法 | SKILL_10f |
| [SKILL_10f4_脚本分解示例.md](references/SKILL_10f4_脚本分解示例.md) | 大型脚本拆分为可复用小脚本的方法与案例 | SKILL_10f |

---

## 草稿文档（Drafts）

> 待完善的元技能，尚在实验阶段

| 文件 | 说明 | 状态 |
|------|------|------|
| [META-SKILL-结构颗粒度光谱.md](draft/META-SKILL-结构颗粒度光谱.md) | 不同粒度的结构化方法选择 | 实验中 |
| [META-SKILL-批量反思管线.md](draft/META-SKILL-批量反思管线.md) | 批量自动化反思流程设计 | 实验中 |
| [META-SKILL-增量式数据更新.md](draft/META-SKILL-增量式数据更新.md) | 增量式数据更新策略 | 实验中 |
| [META-SKILL-建设逻辑留痕.md](draft/META-SKILL-建设逻辑留痕.md) | 决策记录与方法论演化追踪 | 实验中 |
| [META-SKILL-候选列表.md](draft/META-SKILL-候选列表.md) | 待提炼的元技能候选列表 | 实验中 |

---

## 归档文档（Archive）

> 历史文档，记录失败案例和废弃方案

| 文件 | 说明 | 归档原因 |
|------|------|---------|
| [SKILL_01f_繁简词库构造分析.md](archive/SKILL_01f_繁简词库构造分析.md) | 繁简体词库自动构造的方法论探索 | 三次尝试均失败，记录经验教训 |
| [SKILL_03c1-v1-rules.md](archive/SKILL_03c1-v1-rules.md) | 按章反思规律库 v1（完整版） | 已压缩为 v2（见 references/SKILL_03c1-v2-rules.md） |
| [SKILL_10f_Skill的提炼与转化_20260402.md](archive/SKILL_10f_Skill的提炼与转化_20260402.md) | Skill 工程化规范早期完整版 | 已精简拆分为 10f + 10f1/10f2/10f3/10f4 |

---

## 帮助文档（Help）

| 文件 | 说明 |
|------|------|
| [claude-skill-spec.md](help/claude-skill-spec.md) | Claude Skill构造规范 |

---

## 统计数据

**截至2026-04-21**：
- **元技能**：14个
- **管线技能**：87个（含子SKILL）
  - 一级SKILL（总览）：11个（00-10）
  - 二级SKILL（专项）：76个
- **参考文档**：28个（三级SKILL，references/ 子目录）
- **草稿文档**：5个（待完善）
- **归档文档**：3个（失败案例 / 历史版本）

**总计**：129个SKILL文档（不含草稿和归档）

---

## 使用指南

### 快速入口

- **新人onboarding**：先读 [SKILL_00_管线总览](SKILL_00_管线总览.md)，再根据工作内容读对应阶段的SKILL
- **执行具体任务**：直接查找对应的二级SKILL（如 SKILL_03a、SKILL_04c）
- **学习方法论**：按顺序阅读14个元技能（00-META-00 → 00-META-13）
- **跨项目迁移**：重点关注 [00-META-13_技能迁移](00-META-13_技能迁移.md)

### SKILL命名规范

- **一级SKILL**：`SKILL_NN_中文名.md`（如 SKILL_03_实体构建.md）
  - 编号：两位数字（00-10）
  - 位置：skills/ 根目录
  - 用途：顶层任务/阶段划分

- **二级SKILL**：`SKILL_NNx_中文名.md`（如 SKILL_03a_实体标注.md）
  - 编号：数字+小写字母（03a, 03b, 03c...）
  - 位置：skills/ 根目录
  - 用途：一级SKILL的子任务

- **三级SKILL**：`SKILL-NNx-英文名.md`（如 SKILL_03c1-rules.md）
  - 编号：数字+小写字母+英文名（用短横线连接）
  - 位置：skills/references/ 子目录
  - 用途：二级SKILL的支撑文档/规则库/工具集

### 渐进载入模型

根据 [00-META-06_SKILL优化与演化](00-META-06_SKILL优化与演化.md) 的设计：

**Layer 1（总是加载）**：
- SKILL的name + description（< 100词）
- 当前：所有SKILL已符合

**Layer 2（触发时加载）**：
- SKILL主文档（< 500行）
- 包含核心规则和快速决策树

**Layer 3（执行时按需）**：
- references/下的支撑文档
- 详细规则库、示例库、数据表

---

## 相关资源

- **方法论书籍**：
  - [大规模知识库构造元技能方法论.pdf](../resources/publications/meta-skill-book/)（425页）
  - [史记知识库构造管线技能手册.pdf](../resources/publications/pipeline-skills-book/)（438页）
- **技术文章**：
  - [从历史书中探索知识图谱](../resources/publications/draft/2026-03-19_从历史书中探索知识图谱/从历史书中探索知识图谱.pdf)（14页）
- **SKILL系统更新规划**：
  - [SKILL系统更新规划_2026-03-31.md](../doc/methodology/SKILL系统更新规划_2026-03-31.md)

---

**维护说明**：本索引应随SKILL系统演化同步更新。如需添加新SKILL，请遵循命名规范并更新本索引。
