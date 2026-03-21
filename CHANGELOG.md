# 更新日志 (Changelog)

本文档记录《史记》知识库项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

**每日详细工作日志**: [`logs/daily/`](logs/daily/) 目录

---

## 2026-03-20

### 新增 (Added)

- **司马迁文风提炼实验** ([`labs/sima-qian-style/`](labs/sima-qian-style/)) ([0117a825](https://github.com/baojie/shiji-kb/commit/0117a825) / [c7a0d55c](https://github.com/baojie/shiji-kb/commit/c7a0d55c))
  - 三层SKILL架构（现代名词古化 → 白话转文言 → 太史公风格）
  - 包含4个SKILL文件和4个完整示例

- **溯源推理分析实验** ([`skills/SKILL_07d_溯源推理.md`](skills/SKILL_07d_溯源推理.md)) ([4ebda328](https://github.com/baojie/shiji-kb/commit/4ebda328))
  - 案例分析：鸿门宴、荆轲刺秦等十大故事传播链

- **参与指南** ([`docs/help/CONTRIBUTING.md`](docs/help/CONTRIBUTING.md)) ([21582643](https://github.com/baojie/shiji-kb/commit/21582643))

- **技术文章**《从历史书中探索知识图谱》([03685329](https://github.com/baojie/shiji-kb/commit/03685329) / [6360679d](https://github.com/baojie/shiji-kb/commit/6360679d))

### 修复 (Fixed)

- **时间与数量实体标注混淆** ([feb5a516](https://github.com/baojie/shiji-kb/commit/feb5a516) / [602c1f94](https://github.com/baojie/shiji-kb/commit/602c1f94)) (Issue #1)：46处错误
- **SKILL审阅** ([926d3b30](https://github.com/baojie/shiji-kb/commit/926d3b30))

### 更改 (Changed)

- **labs目录重组** ([0117a825](https://github.com/baojie/shiji-kb/commit/0117a825))
- **归档整理** ([c4c568cc](https://github.com/baojie/shiji-kb/commit/c4c568cc))

**详细工作日志**: [`logs/daily/2026-03-20.md`](logs/daily/2026-03-20.md)

---

## 2026-03-19

### 新增 (Added)

- **每日工作日志系统** ([ac7e41c4](https://github.com/baojie/shiji-kb/commit/ac7e41c4))：3月18-19日工作日志

### 修复 (Fixed)

- **身份标注符号语义漂移** ([4c96f109](https://github.com/baojie/shiji-kb/commit/4c96f109))：全局修正8,774处
- **实体边界错误** ([99af56d6](https://github.com/baojie/shiji-kb/commit/99af56d6))：75处切分错误
- **CSS修复** ([b1ed7930](https://github.com/baojie/shiji-kb/commit/b1ed7930))：v5.4版本样式

### 更改 (Changed)

- **文档重构** ([cc4d3d43](https://github.com/baojie/shiji-kb/commit/cc4d3d43) / [c38912b0](https://github.com/baojie/shiji-kb/commit/c38912b0))：主页、SKILL编号规范化
- **临时文件夹整理** ([4c863aca](https://github.com/baojie/shiji-kb/commit/4c863aca))：tmp → temp
- **动词标注完成** ([cca73582](https://github.com/baojie/shiji-kb/commit/cca73582))：002-130全部章节

**详细工作日志**: [`logs/daily/2026-03-19.md`](logs/daily/2026-03-19.md)

---

## 2026-03-18

### 新增 (Added)

- **动词标注体系升级** ([4ed5cc45](https://github.com/baojie/shiji-kb/commit/4ed5cc45) / [53667d0a](https://github.com/baojie/shiji-kb/commit/53667d0a))：规范v3.2→v3.3
- **元技能方法论PDF** ([2f9eb3aa](https://github.com/baojie/shiji-kb/commit/2f9eb3aa))：PDF合集发布

### 修复 (Fixed)

- **动词格式清理** ([5278645d](https://github.com/baojie/shiji-kb/commit/5278645d) / [5359bf7a](https://github.com/baojie/shiji-kb/commit/5359bf7a) / [e43a3317](https://github.com/baojie/shiji-kb/commit/e43a3317))：v3.1/v3.2格式迁移

### 更改 (Changed)

- **项目整理** ([cd87afa9](https://github.com/baojie/shiji-kb/commit/cd87afa9))：目录重组、路径修复

**详细工作日志**: [`logs/daily/2026-03-18.md`](logs/daily/2026-03-18.md)

---

## 2026-03-17

### 新增 (Added)

- **专项索引系统** ([849d8ac1](https://github.com/baojie/shiji-kb/commit/849d8ac1) / [cf9f4f5c](https://github.com/baojie/shiji-kb/commit/cf9f4f5c) / [5ef38163](https://github.com/baojie/shiji-kb/commit/5ef38163) / [eb97490a](https://github.com/baojie/shiji-kb/commit/eb97490a) / [49b57157](https://github.com/baojie/shiji-kb/commit/49b57157))：太史公曰、韵文(96篇)、成语，多格式输出+PDF导出
- **战争事件识别SKILL** ([42e5fab6](https://github.com/baojie/shiji-kb/commit/42e5fab6)) (`SKILL_05e`)：系统化识别军事冲突事件
- **每日工作日志系统** ([9962ead7](https://github.com/baojie/shiji-kb/commit/9962ead7))：自动生成脚本
- **汉字标注覆盖率统计** ([f187e340](https://github.com/baojie/shiji-kb/commit/f187e340))：量化标注进度

### 更改 (Changed)

- **第二轮实体反思** ([0cd03a76](https://github.com/baojie/shiji-kb/commit/0cd03a76) / [08a4c5bb](https://github.com/baojie/shiji-kb/commit/08a4c5bb))：93章标注修正及增删字审查
- **动词标注体系升级** ([4536fd58](https://github.com/baojie/shiji-kb/commit/4536fd58) / [01391269](https://github.com/baojie/shiji-kb/commit/01391269) / [cfb2a51d](https://github.com/baojie/shiji-kb/commit/cfb2a51d) / [7c5ab02b](https://github.com/baojie/shiji-kb/commit/7c5ab02b))：v3.1格式迁移

**详细工作日志**: [`logs/daily/2026-03-17.md`](logs/daily/2026-03-17.md)

---

## 2026-03-16

### 新增 (Added)

- **姓氏推理首轮** ([05f6e9a7](https://github.com/baojie/shiji-kb/commit/05f6e9a7) / [4a4255bf](https://github.com/baojie/shiji-kb/commit/4a4255bf))：覆盖2053/3630人物（56.6%）
- **第一轮实体反思** ([38b082c6](https://github.com/baojie/shiji-kb/commit/38b082c6) / [7c329904](https://github.com/baojie/shiji-kb/commit/7c329904) / [67e2c639](https://github.com/baojie/shiji-kb/commit/67e2c639))：全书130章修正1913处
- **v2.8格式统一** ([650aa7d3](https://github.com/baojie/shiji-kb/commit/650aa7d3) / [d6e2b667](https://github.com/baojie/shiji-kb/commit/d6e2b667))：18类实体迁移为〖TYPE X〗格式

### 修复 (Fixed)

- **章节标注质量提升**：013-130章修正756处

### 更改 (Changed)

- **实体统计更新**：15,190词条 / 102,851次标注

**详细工作日志**: [`logs/daily/2026-03-16.md`](logs/daily/2026-03-16.md)

---

## 2026-03-15

### 新增 (Added)

- **人名实体跨章反思** ([edc9821e](https://github.com/baojie/shiji-kb/commit/edc9821e) / [b468df8c](https://github.com/baojie/shiji-kb/commit/b468df8c) / [9037f7cb](https://github.com/baojie/shiji-kb/commit/9037f7cb))：615处修正
- **单字人名消歧** ([a788c574](https://github.com/baojie/shiji-kb/commit/a788c574))：001-010章39处修正
- **十表结构化** ([d6e2b667](https://github.com/baojie/shiji-kb/commit/d6e2b667))：013三代世表，生成JSON/CSV

### 更改 (Changed)

- **章节级反思**：012章59处修正，011章32处修正

**详细工作日志**: [`logs/daily/2026-03-15.md`](logs/daily/2026-03-15.md)

## 2026-03-16

### 新增 (Added)

- **内联消歧语法 v2.7** ([0cb6fec9](https://github.com/baojie/shiji-kb/commit/0cb6fec9))：扩展到所有13种实体类型，支持 `〖TYPE 显示名|规范名〗` 语法
- **方法论规划** ([b0ab24c1](https://github.com/baojie/shiji-kb/commit/b0ab24c1))：新增事实发现、姓氏推理、反常推理三个SKILL
- **十表结构化** ([d6e2b667](https://github.com/baojie/shiji-kb/commit/d6e2b667))：修复013三代世表，生成JSON/CSV，新增SKILL_02g

### 更改 (Changed)

- **单字人名消歧反思** ([9037f7cb](https://github.com/baojie/shiji-kb/commit/9037f7cb))：001-010章第二轮，修正39处
- **v2.8格式统一** ([650aa7d3](https://github.com/baojie/shiji-kb/commit/650aa7d3))：18类实体全部迁移为〖TYPE X〗格式
- **011章第二次反思** ([b468df8c](https://github.com/baojie/shiji-kb/commit/b468df8c))：补充汉姓规则，新增32处修正

**详细工作日志**: [`logs/daily/2026-03-16.md`](logs/daily/2026-03-16.md)

## 2026-03-14

### 更改 (Changed)

- **v2.2-v2.8实体体系深度重构** ([73cfbf16](https://github.com/baojie/shiji-kb/commit/73cfbf16) / [d5967cdc](https://github.com/baojie/shiji-kb/commit/d5967cdc) / [1e6cf8e1](https://github.com/baojie/shiji-kb/commit/1e6cf8e1) / [4baba997](https://github.com/baojie/shiji-kb/commit/4baba997) / [53d9b987](https://github.com/baojie/shiji-kb/commit/53d9b987) / [7f768628](https://github.com/baojie/shiji-kb/commit/7f768628) / [963e49bb](https://github.com/baojie/shiji-kb/commit/963e49bb) / [f5b17c0f](https://github.com/baojie/shiji-kb/commit/f5b17c0f) / [8c43461a](https://github.com/baojie/shiji-kb/commit/8c43461a) / [a1ea0950](https://github.com/baojie/shiji-kb/commit/a1ea0950) / [c3e9b28a](https://github.com/baojie/shiji-kb/commit/c3e9b28a) / [88240e17](https://github.com/baojie/shiji-kb/commit/88240e17) / [7f28fd6c](https://github.com/baojie/shiji-kb/commit/7f28fd6c))：
  - 邦国/氏族/族群三层分类体系确立（195处重分类）
  - 官职深度反思（2290处：元年→时间、皇帝专称→人名）
  - 地名反思（60处），身份类型恢复扩充（4297次标注）
  - 动植物→生物类型重命名
  - lint系统建立，标注残留修复
  - 嵌套标签修复，数量实体补充

### 新增 (Added)

- **排版实验与文档** ([17554cae](https://github.com/baojie/shiji-kb/commit/17554cae) / [f9db9c20](https://github.com/baojie/shiji-kb/commit/f9db9c20))：句间逻辑关系可视化原型，kg/子目录README

**详细工作日志**: [`logs/daily/2026-03-14.md`](logs/daily/2026-03-14.md)

---

## 2026-03-13

### 新增 (Added)

- **实体体系扩展至15类** ([f5c09dc] / [de37940] / [60d6484])：新增典籍/礼仪/刑法/思想4类实体类型
- **语义区块全面升级** ([f2e2195])：fenced div迁移，83章自动补全太史公曰/赞标注

### 更改 (Changed)

- **v2.0实体标注符号迁移** ([b76caeb])：全书130篇迁移至〖〗格式，消除与Markdown语法冲突
- **封国实体类型新增** ([0e1ee770](https://github.com/baojie/shiji-kb/commit/0e1ee770) / [55b6c22d](https://github.com/baojie/shiji-kb/commit/55b6c22d))：v2.1从朝代中剥离诸侯国/封地，使用〖'X〗符号

**详细工作日志**: [`logs/daily/2026-03-13.md`](logs/daily/2026-03-13.md)

---

## 2026-03-12

### 新增 (Added)

- **跨章因果推理管线** ([3a85dbe])：LLM推理确认338条跨章因果关系，扩展至9种关系类型
- **文档目录重构** ([769377f])：doc/重组为6个主题子目录，新增SKILL_年份消歧
- **地铁图交互优化** ([ba19e4d])：搜索高亮、缩放平滑、实体链接等功能

### 更改 (Changed)

- **事件关系数据更新**：7314条→7652条（新增338条cross_causal）
- **五帝本纪年代修正**：001-001~001-008补充历史推断逻辑

**详细工作日志**: [`logs/daily/2026-03-12.md`](logs/daily/2026-03-12.md)

---

## 2026-03-11

### 新增 (Added)

- **十表事件补充提取** ([45809c4])：补充226个事件至十表章节
- **SKILL_事件关系发现合并** ([e96d62e])：整合多个SKILL为唯一权威文档
- **五轮事件年代反思完成** ([fe34b65])：累计2119处修正，数据收敛稳定

### 更改 (Changed)

- **事件关系全量重算**：3185事件、7314条关系
- **实体HTML索引重建** ([6d114e5])：更新至3186条事件
- **地铁图系统优化** ([5971549f](https://github.com/baojie/shiji-kb/commit/5971549f) / [011b827d](https://github.com/baojie/shiji-kb/commit/011b827d))：标签防重叠、app拆分

**详细工作日志**: [`logs/daily/2026-03-11.md`](logs/daily/2026-03-11.md)

---

## 2026-03-10

### 更改 (Changed)

- **第三轮年代反思** ([039afb0])：465处修正，70章有修正
- **第四轮年代反思** ([16c8f9e])：167处修正，年份准确度完全收敛

**详细工作日志**: [`logs/daily/2026-03-10.md`](logs/daily/2026-03-10.md)

---

## 2026-03-09

### 新增 (Added)

- **事件年代推断体系** ([85f39591](https://github.com/baojie/shiji-kb/commit/85f39591))：Agent反思管线，两轮完成1441处修正
- **SKILL_事件年代推断** ([85f39591](https://github.com/baojie/shiji-kb/commit/85f39591))：纪年换算、大事年表交叉验证方法论
- **实体消歧与标签修复** ([b07f7c8a](https://github.com/baojie/shiji-kb/commit/b07f7c8a))：破损标签500+处修复，别名扩充586组

### 更改 (Changed)

- **event.html增强**：实体链接、年代推断tooltip、历史分期修正
- **参考文献扩充** ([868b09ea](https://github.com/baojie/shiji-kb/commit/868b09ea))：新增机器学习分期研究、图形化阅读价值系统

**详细工作日志**: [`logs/daily/2026-03-09.md`](logs/daily/2026-03-09.md)

---

## 2026-03-08

### 新增 (Added)

- **事件地铁图可视化**：130线路、3092站点，支持拖拽缩放、事件搜索
- **事件关系系统**：4385条关系，8种类型，LLM批量推理
- **公元纪年标注**：782事件标注公元年，质检修复

### 更改 (Changed)

- **KG目录重构**：按知识类型重组为8个子目录（events/entities/chronology等）
- **数据统一** ([e12f805])：实体统计、字数口径、时代分布全面校正

**详细工作日志**: [`logs/daily/2026-03-08.md`](logs/daily/2026-03-08.md)

## 2026-03 (上旬)

### 新增 (Added)

- **SKU实体增补** ([85df920])：为394个Factual SKU生成entities.json，关联7497个实体标注
- **知识单元（SKU）体系** ([dc8c13d])：434个事实知识、241个技能知识、知识索引文档

---

## 2026-02

### 新增 (Added)

- **时间线实体与年份消歧** ([59c3814])：公元纪年映射288种格式，历代君主在位年份数据库
- **实体别名合并与语义消歧** ([2580cfc])：19组同人别名合并，1281处自动消歧，覆盖率90%
- **命名实体索引系统** ([f586a61])：12个HTML索引页，9700+条目，67000+次出现，正文实体链接
- **十表完整表格渲染管线** ([b77c59f])：十表961单元格实体标注，Markdown表格转HTML，sticky表头
- **全部130章小节划分** ([98d97a3])：完整小节ID系统，sections_data.json
- **项目结构重构** ([2f8f0ad] / [e5d8429])：创建kg/、doc/、temp/目录，脚本路径统一
- **知识图谱系统完善** ([863b6c3])：kg_前缀规范，知识图谱输出统一
- **HTML展示系统完善** ([02508b4])：引号修复，小节链接，index.html改进
- **完整HTML生成系统** ([02508b4])：130章HTML生成，批量工具，研究方法体系文档

### 更改 (Changed)

- **标注进度**：完成99/130章（76.2%）

---

## 2026-01

### 新增 (Added)

- **核心标注系统建立** ([73c7aed])：11类实体标注规范，Purple Numbers段落编号，Markdown转HTML核心工具
- **样式系统**：实体语法高亮11色，对话样式，段落锚点
- **文本结构化**：智能段落拆分，对话拆分，列表识别，诗歌排版

---

## 2025-02至03

### 新增 (Added)

- **项目启动** ([256f6cc])：手工编写RDF/TTL知识图谱，创建本体文件，建立GitHub仓库
- **技术路线转型**：拆分130篇原文，转向Markdown标注系统

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

**最后更新**: 2026-03-21
**当前版本**: v0.9.0
