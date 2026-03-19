# 《史记》知识库 - 用AI让历史书活起来

> 让历史研究不再是钻故纸堆，让"皓首穷经"不再必需

[![在线访问](https://img.shields.io/badge/在线访问-GitHub%20Pages-blue)](https://baojie.github.io/shiji-kb)
[![许可证](https://img.shields.io/badge/许可证-CC%20BY--NC--SA%204.0-orange)](LICENSE)

**在线Demo**：[首页](https://baojie.github.io/shiji-kb) · [五帝本纪](https://baojie.github.io/shiji-kb/chapters/001_五帝本纪.html) · [项羽本纪](https://baojie.github.io/shiji-kb/chapters/007_项羽本纪.html) · [秦楚之际月表](https://baojie.github.io/shiji-kb/chapters/016_秦楚之际月表.html) · [孔子世家](https://baojie.github.io/shiji-kb/chapters/047_孔子世家.html) · [刺客列传](https://baojie.github.io/shiji-kb/chapters/086_刺客列传.html)

---

## 项目简介

用AI Agent将《史记》130篇、57.7万字古文转化为结构化知识图谱。最终目标是用机器的力量辅助历史考据——从百万份文献中自动发现历史事实、识别矛盾、归纳规则，将传统"皓首穷经"的研究过程从数十年压缩到数周。

《史记》是第一个试验田。当前阶段聚焦于基础设施建设：实体标注、事件提取、年代推断、关系发现、本体构建。这些结构化数据是未来自动化考据推理的前提。

> 现在没有人再会读没有标点符号的文章，未来也不会有人愿意读没有语法加亮的文章。

语法高亮是认知辅助的第一步——为18类实体赋予不同颜色，降低古文阅读门槛。但更重要的是背后的知识图谱：当实体、事件、关系被结构化后，机器就能进行跨文献的交叉验证、矛盾检测和规律发现。

> **免责声明**：本项目由AI辅助生成，标注和知识提取中不可避免地存在错误和疏漏。我们正在与AI一起持续修正和完善这些问题。如发现错误，欢迎提交Issue帮助改进。本知识库严格局限于《史记》本身的文本内容，不涉及史实考证。

---

## 核心成果

| 类别 | 数量 | 说明 |
|------|------|------|
| 文本标注 | 130篇，57.7万字 | 18类实体语义标注，100%覆盖 |
| 实体 | 15,190词条，102,851次标注 | 人名3,638、官职2,144、地名1,865等18类 |
| 实体索引 | 18类索引页面，11,992条目 | 别名合并595条，语义消歧644处，正文可点击跳转 |
| 事件 | 3,198个，11类事件类型 | 130章全覆盖，98.7%事件已标注公元纪年 |
| 事件关系 | 7,652条，9种类型 | 延续/因果/包含/对立/互见等，1,876个跨章换乘 |
| 事件地铁图 | 130条线路 | 支持缩放/拖拽/搜索/实体链接/原文引用 |
| SKU知识单元 | 434事实 + 241技能 | 7,497个实体关联，含关系知识 |
| 方法论Skills | 26个文档，9大阶段 | 可复用方法论，适用于其他古籍项目 |
| **元技能方法论** | **14个文档，PDF合集** | **通用知识工程方法论** → [PDF下载](doc/publications/meta-skill-book/大规模知识库构造元技能方法论.pdf) |

### 标注质量

- ✅ **第一轮实体反思**（2026-03-17）：全书130章系统审查，修正1913处标注错误，原文完整性100%验证通过
- ✅ **CSS渲染升级v5.4**（2026-03-19）：增强视觉效果，典籍/神话波浪线，朝代/思想下划线加粗
- 📊 详见 [第一轮实体反思报告](doc/entities/第一轮实体反思报告.md) | [CSS版本历史](doc/spec/CSS版本历史_v5.4.md)

---

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/baojie/shiji-kb.git
cd shiji-kb

# 2. 安装依赖
pip install -r requirements.txt

# 3. 生成HTML（单章或全部）
python render_shiji_html.py chapter_md/001_五帝本纪.tagged.md
python generate_all_chapters.py

# 4. 查看结果
# 在线：https://baojie.github.io/shiji-kb
# 本地：打开 docs/chapters/ 下的HTML文件
```

---

## 目录结构

```
shiji-kb/
├── chapter_md/                # 标注后的Markdown文件（130篇）
├── docs/                      # GitHub Pages网站
│   ├── index.html             #   首页
│   ├── chapters/              #   HTML格式章节
│   ├── entities/              #   实体索引页面（18类）
│   └── original_text/         #   原始文本
├── kg/                        # 知识图谱
│   ├── events/                #   事件（3,185个）+ 关系 + 年代审查
│   ├── entities/              #   实体索引 + 别名/消歧
│   ├── chronology/            #   纪年（君主在位年 + 公元映射）
│   ├── genealogy/             #   家谱（帝王世系）
│   ├── relations/             #   人物关系
│   ├── vocabularies/          #   词汇表（18类）
│   ├── biology/               #   生物实体
│   └── rdf/                   #   RDF/本体
├── ontology/skus/             # 知识单元（SKU）
├── skills/                    # 方法论Skills（26个）
├── publication/               # 出版物
│   └── meta-skill-book/       #   元技能方法论PDF（2.6MB）
├── scripts/                   # 通用工具脚本
├── app/                       # 交互式应用
│   ├── metro/                 #   事件地铁图
│   └── game/                  #   史记争霸游戏
├── tables/                    # 十表数据（JSON + HTML）
├── doc/                       # 项目文档
├── render_shiji_html.py       # Markdown→HTML渲染器
├── generate_all_chapters.py   # 批量生成全部章节
└── publish_to_docs.sh         # 发布到GitHub Pages
```

---

## 方法论Skills

从《史记》知识图谱化实践中提炼的29个可复用方法论文档（9大阶段+子工序），适用于其他古籍项目：

| 阶段 | SKILL | 说明 |
|------|-------|------|
| 总览 | [00 管线总览](skills/SKILL_00_管线总览.md) | 九大阶段工序依赖与总控 |
| 校勘 | [01 古籍校勘](skills/SKILL_01_古籍校勘.md) | 底本校正，生成定本 |
| 结构 | [02 结构分析](skills/SKILL_02_结构分析.md) | Token vs XML设计决策 |
| | [02a 章节切分与编号](skills/SKILL_02a_章节切分与编号.md) | Purple Numbers + 段落修复 + 小节划分 |
| | [02b 区块与韵文处理](skills/SKILL_02b_区块与韵文处理.md) | 太史公曰/赞/诗歌围栏块 + 对话分析 |
| | [02c 三家注标注](skills/SKILL_02c_三家注标注.md) | 集解/索隐/正义注释层 |
| | [02d 结构语义分析](skills/SKILL_02d_结构语义分析.md) | 句间/段间/章间语义关系 + 注释对齐 + 排版映射 |
| | [02e 词法分析](skills/SKILL_02e_词法分析.md) | 字级词性标注、遗漏实体发现 |
| | [02f 文本统计](skills/SKILL_02f_文本统计.md) | 字数/句长/词频/实体密度/五体对比 |
| 实体 | [03 实体构建](skills/SKILL_03_实体构建.md) | 阶段总览 |
| | [03a 实体标注](skills/SKILL_03a_实体标注.md) | 18类实体NER（v2.5） |
| | [03b 实体消歧](skills/SKILL_03b_实体消歧.md) | 4层启发式（3,797人名，644处消歧） |
| | [03c 实体标注反思](skills/SKILL_03c_实体标注反思.md) | 按章/按类型多轮反思审查 |
| | [03d 渲染与发布](skills/SKILL_03d_渲染与发布.md) | HTML渲染衔接（详见09a） |
| 事件 | [04a 事件识别](skills/SKILL_04a_事件识别.md) | 事件Schema/类型/提取 |
| | [04b 十表事件处理](skills/SKILL_04b_十表事件处理.md) | 十表专用补充 |
| | [04c 事件年代推断](skills/SKILL_04c_事件年代推断.md) | 分层纪年解析 |
| | [04d 事件年代审查](skills/SKILL_04d_事件年代审查.md) | Agent反思审查工作流 |
| | [04e 年份消歧](skills/SKILL_04e_年份消歧.md) | 在位纪年→公元年（380君主，1,498映射） |
| 关系 | [05a 事件关系发现](skills/SKILL_05a_事件关系发现.md) | 9种事件关系（7,652条） |
| | [05b 实体关系构建](skills/SKILL_05b_实体关系构建.md) | 人物关系（家族/政治/社会）+ 家谱 + SPO三元组 |
| | [05c 事实发现](skills/SKILL_05c_事实发现.md) | 原子事实三元组（~10万规模，SPO全汉字，含ctx上下文） |
| 本体 | [06a 实体到本体](skills/SKILL_06a_实体到本体.md) | 词表→分类树→OWL/RDF + 人物本体实战案例 |
| 推理 | [07 逻辑推理](skills/SKILL_07_逻辑推理.md) | 分类推理/时间推理/矛盾检测 |
| | [07a 人物生卒年推断](skills/SKILL_07a_人物生卒年推断.md) | 生卒年区间推断，置信度分级 |
| | [07b 姓氏推理](skills/SKILL_07b_姓氏推理.md) | 先秦姓/氏区分，多轮迭代推理（spec: [姓氏制度](doc/spec/姓氏制度.md)） |
| SKU | [08 SKU构造](skills/SKILL_08_SKU构造.md) | Factual/Procedural/Relational知识单元 |
| 应用 | [09 应用构造](skills/SKILL_09_应用构造.md) | 阅读器/地铁图/游戏/问答机器人 |
| | [09a 认知辅助阅读器](skills/SKILL_09a_认知辅助阅读器.md) | 语法高亮渲染 + 18类配色 + 交互功能 |
| | [09b 知识库游戏化](skills/SKILL_09b_知识库游戏化.md) | SKU→技能卡、事件→剧情、实体→角色 |

---

## 扩展计划

- **近期**：十表交互式查看器、Neo4j图数据库导入、知识图谱深化（历法转换、多级时间粒度）
- **中期**：从史记扩展到二十六史（约4,000万字）及资治通鉴系列（约600-700万字）
- **远期**：推广到诸子百家、四库全书、佛道经典等大规模古籍数字化（总规模数亿字），方法可复制、Agent驱动、Skills可复用

---

## 贡献 / 许可 / 致谢

欢迎各种形式的贡献：知识图谱完善、代码改进、学术讨论、可视化设计、Bug报告。

- GitHub Issues：<https://github.com/baojie/shiji-kb/issues>
- 微信：baojiexigua

**许可证**：标注数据采用 [CC BY-NC-SA 4.0](LICENSE)，分析脚本采用 MIT License。《史记》原文为公有领域作品。

**致谢**：感谢[维基文库](https://zh.wikisource.org/wiki/史記)提供原始文本，感谢 Claude Code 及 Claude Sonnet 4.5 / Opus 4.6 作为项目主要开发工具和AI助手。

---

**项目维护者**：[baojie](https://github.com/baojie)
