# 项目目录结构详解

本文档提供《史记》知识库项目的完整目录结构说明。

## 目录树

```
shiji-kb/
├── chapter_md/                # 标注后的Markdown文件（130篇）
│   ├── 001_五帝本纪.tagged.md
│   ├── 002_夏本纪.tagged.md
│   └── ...                    # 130个章节文件
│
├── docs/                      # GitHub Pages网站
│   ├── index.html             # 首页
│   ├── chapters/              # HTML格式章节（130个）
│   │   ├── 001_五帝本纪.html
│   │   └── ...
│   ├── entities/              # 实体索引页面（18类）
│   │   ├── index.html         # 实体索引总览
│   │   ├── persons.html       # 人名索引
│   │   ├── officials.html     # 官职索引
│   │   └── ...
│   └── original_text/         # 原始文本
│
├── kg/                        # 知识图谱
│   ├── events/                # 事件数据
│   │   ├── data/              # 事件索引（130章）
│   │   │   ├── 001_五帝本纪_事件索引.md
│   │   │   ├── event_relations.json  # 事件关系（7,652条）
│   │   │   └── ...
│   │   ├── chronology_review/ # 年代审查
│   │   └── scripts/           # 事件处理脚本
│   │       ├── build_metro_map_data.py  # 地铁图数据生成
│   │       └── ...
│   │
│   ├── entities/              # 实体索引与别名消歧
│   │   ├── index/             # 实体索引（18类）
│   │   │   ├── persons.json   # 人名3,638词条
│   │   │   ├── officials.json # 官职2,144词条
│   │   │   ├── locations.json # 地名1,865词条
│   │   │   └── ...            # 其他15类
│   │   ├── aliases/           # 别名合并（595条）
│   │   ├── disambiguation/    # 语义消歧（644处）
│   │   └── reflection/        # 实体反思审查
│   │
│   ├── chronology/            # 纪年系统
│   │   ├── reign_years/       # 君主在位年表（380君主）
│   │   └── ce_mapping/        # 公元年映射（1,498映射）
│   │
│   ├── genealogy/             # 家谱与世系
│   │   ├── imperial/          # 帝王世系
│   │   └── families/          # 重要家族谱系
│   │
│   ├── relations/             # 人物关系
│   │   ├── family/            # 家族关系
│   │   ├── political/         # 政治关系
│   │   └── social/            # 社会关系
│   │
│   ├── vocabularies/          # 词汇表（18类）
│   │   ├── entity_types.json  # 实体类型定义
│   │   └── ...
│   │
│   ├── biology/               # 生物实体
│   │   ├── animals/           # 动物
│   │   ├── plants/            # 植物
│   │   └── mythical/          # 神话生物
│   │
│   └── rdf/                   # RDF与本体
│       ├── ontology/          # OWL本体定义
│       └── triples/           # RDF三元组
│
├── ontology/skus/             # 知识单元（SKU）
│   ├── factual/               # 事实型知识（434个）
│   ├── procedural/            # 程序型知识（241个技能）
│   └── relational/            # 关系型知识（7,497实体关联）
│
├── skills/                    # 方法论Skills
│   ├── SKILL_00_管线总览.md
│   ├── SKILL_01_古籍校勘.md
│   ├── SKILL_02_结构分析.md
│   ├── SKILL_02a_章节切分与编号.md
│   ├── ...                    # 40个管线技能
│   ├── 00-META-00_好东西都是总结出来的.md
│   ├── 00-META-01_反思.md
│   └── ...                    # 14个元技能
│
├── doc/publications/          # 出版物与文档
│   ├── meta-skill-book/       # 元技能方法论PDF（2.6MB，425页）
│   │   ├── 大规模知识库构造元技能方法论.pdf
│   │   ├── generate_meta_skills_pdf.py
│   │   └── README.md
│   ├── pipeline-skills-book/  # 管线技能手册PDF（3.0MB，438页）
│   │   ├── 史记知识库构造管线技能手册.pdf
│   │   ├── generate_pipeline_skills_pdf.py
│   │   └── README.md
│   ├── 公众号文章/            # 公众号系列文章
│   ├── 项目初衷、愿景与未来方向.md
│   ├── agentic_ontology_101.md
│   ├── 史记语法高亮创造过程.md
│   ├── 史记阅读器重构与语义排版.md
│   └── ...
│
├── scripts/                   # 通用工具脚本
│   ├── validation/            # 数据验证脚本
│   ├── conversion/            # 格式转换工具
│   └── utilities/             # 其他实用工具
│
├── app/                       # 交互式应用
│   ├── metro/                 # 事件地铁图
│   │   ├── index.html
│   │   ├── metro.js
│   │   ├── metro.css
│   │   └── data/
│   │       └── metro_map_data.json  # 130线路，3,197站点
│   └── game/                  # 史记争霸游戏
│       └── ...
│
├── tables/                    # 十表数据
│   ├── json/                  # JSON格式表数据
│   └── html/                  # HTML可视化
│
├── doc/                       # 项目文档
│   ├── spec/                  # 技术规范
│   │   ├── 实体标注规范_v2.5.md
│   │   ├── CSS版本历史_v5.4.md
│   │   ├── 姓氏制度.md
│   │   └── ...
│   └── entities/              # 实体相关文档
│       └── 第一轮实体反思报告.md
│
├── render_shiji_html.py       # Markdown→HTML渲染器
├── generate_all_chapters.py   # 批量生成全部章节
├── publish_to_docs.sh         # 发布到GitHub Pages
├── requirements.txt           # Python依赖
├── README.md                  # 项目主页
├── PROJECT_STRUCTURE.md       # 本文档
├── CLAUDE.md                  # Claude Code 工作指南
└── LICENSE                    # CC BY-NC-SA 4.0
```

## 核心目录说明

### 1. chapter_md/ - 标注源文件
包含130篇《史记》章节的Markdown源文件，每个文件都包含完整的18类实体标注。

**标注格式示例：**
```markdown
〖@黄帝〗者，少典之子，姓〖$公孙〗，名〖$曰轩辕〗。生而神灵，弱而能言，
幼而徇齐，长而敦敏，成而聪明。轩辕之时，〖;神农氏〗世衰。
```

### 2. docs/ - 在线网站
GitHub Pages托管的在线阅读器，包含：
- **chapters/**: 130个HTML章节，带语法高亮和交互功能
- **entities/**: 18类实体索引页面，支持跳转和搜索
- **index.html**: 项目首页

### 3. kg/ - 知识图谱核心
结构化知识的存储中心：

#### kg/events/
- **data/**: 3,198个事件的完整数据
  - 每章一个事件索引文件
  - event_relations.json: 7,652条事件关系（9种类型）
- **chronology_review/**: 年代推断审查记录
- **scripts/**: 事件处理工具，包括地铁图数据生成

#### kg/entities/
- **index/**: 18类实体的JSON索引
  - 人名、官职、地名、朝代、器物等
  - 包含频次统计和别名信息
- **aliases/**: 595条别名合并规则
- **disambiguation/**: 644处同名消歧记录
- **reflection/**: 实体标注反思审查日志

#### kg/chronology/
- **reign_years/**: 380位君主的在位年表
- **ce_mapping/**: 1,498条在位纪年到公元年的映射

### 4. ontology/skus/ - 知识单元
按SKU（Stock Keeping Unit）模式组织的知识：
- **factual/**: 事实型知识，如"项羽自刎于乌江"
- **procedural/**: 程序型知识，如"如何进行古籍实体标注"
- **relational/**: 关系型知识，如"刘邦-张良：君臣关系"

### 5. skills/ - 方法论文档
可复用的知识工程方法论：
- **40个管线技能** (SKILL_00-09系列)：从古籍校勘到应用构造的完整流程
- **14个元技能** (00-META系列)：通用知识工程方法论

### 6. app/ - 交互应用

#### app/metro/ - 事件地铁图
将3,198个事件可视化为地铁线路图：
- 130条线路（对应130章）
- 3,197个站点（对应事件）
- 1,876个跨章换乘站
- 支持缩放、拖拽、搜索、实体链接

#### app/game/ - 史记争霸游戏
基于知识图谱的历史策略游戏（开发中）

### 7. doc/publications/ - 出版物
包含两本PDF手册和系列文章：
- **大规模知识库构造元技能方法论.pdf** (2.6MB, 425页)
- **史记知识库构造管线技能手册.pdf** (3.0MB, 438页)
- 系列文章和公众号推文

## 数据规模总览

| 类别 | 数量 | 位置 |
|------|------|------|
| 章节文件 | 130篇 | chapter_md/ |
| 标注字数 | 57.7万字 | - |
| 实体词条 | 15,190个 | kg/entities/index/ |
| 实体标注 | 102,851次 | chapter_md/ |
| 事件 | 3,198个 | kg/events/data/ |
| 事件关系 | 7,652条 | kg/events/data/event_relations.json |
| SKU知识单元 | 675个 | ontology/skus/ |
| 方法论Skills | 54个 | skills/ |
| HTML页面 | 150+个 | docs/ |

## 文件命名规范

### 章节文件
- 格式：`{编号}_{章节名}.{类型}.md`
- 示例：`001_五帝本纪.tagged.md`

### 事件索引
- 格式：`{编号}_{章节名}_事件索引.md`
- 示例：`001_五帝本纪_事件索引.md`

### 实体索引
- 格式：`{实体类型}.json`
- 示例：`persons.json`, `officials.json`

### Skills文件
- 管线技能：`SKILL_{编号}_{名称}.md`
- 元技能：`00-META-{编号}_{名称}.md`

## 生成与发布流程

### 1. 单章渲染
```bash
python render_shiji_html.py chapter_md/001_五帝本纪.tagged.md
```

### 2. 批量生成
```bash
python generate_all_chapters.py
```

### 3. 发布到网站
```bash
./publish_to_docs.sh
```

### 4. 生成PDF手册
```bash
# 元技能方法论
cd doc/publications/meta-skill-book
python3 generate_meta_skills_pdf.py

# 管线技能手册
cd doc/publications/pipeline-skills-book
python3 generate_pipeline_skills_pdf.py
```

## 依赖关系

### Python依赖
详见 [requirements.txt](requirements.txt)

### 核心依赖
- Python 3.8+
- markdown
- weasyprint
- beautifulsoup4
- lxml

### 可选依赖
- rdflib (RDF/本体操作)
- networkx (图分析)

## 版本控制

### 重要版本标记
- **v2.5**: 实体标注规范第二版（18类实体）
- **v5.4**: CSS渲染系统最新版（2026-03-19）
- **v1.0**: 第一轮实体反思完成（2026-03-17）

### 备份策略
重要文件修改前会自动创建 `.backup-{日期}` 备份文件

## 扩展计划

### 近期目录扩展
- `kg/calendar/`: 历法转换系统
- `kg/geography/`: 地理信息系统
- `app/qa/`: 问答机器人

### 中期扩展
- `二十六史/`: 扩展到二十六史（约4,000万字）
- `资治通鉴/`: 资治通鉴系列（600-700万字）

### 远期规划
- `诸子百家/`: 诸子百家典籍
- `四库全书/`: 四库全书选集
- `佛道经典/`: 佛道经典数字化

## 相关文档

- [README.md](README.md) - 项目主页
- [CLAUDE.md](CLAUDE.md) - Claude Code 工作指南
- [doc/spec/实体标注规范_v2.5.md](doc/spec/实体标注规范_v2.5.md) - 实体标注详细规范
- [doc/spec/CSS版本历史_v5.4.md](doc/spec/CSS版本历史_v5.4.md) - CSS渲染系统版本历史

---

**文档维护**: 本文档随项目更新而更新，最后更新时间：2026-03-19
