# 史记知识图谱 (Knowledge Graph)

本目录存放史记知识图谱相关的输出数据，包括实体词汇表、关系网络、家谱图谱和事件索引。

## 目录结构

```
kg/
├── vocabularies/    # 实体词汇表（人名、地名、官职等11类）
├── relations/       # 人物关系网络（父子、母子、君臣等）
├── genealogy/       # 帝王家谱（各朝代世系图）
└── events/          # 历史事件索引（战争、改革、政变等）
```

## 知识图谱构建脚本

所有知识图谱相关的Python脚本统一使用 `kg_` 前缀，位于项目根目录：

### 1. 实体词汇表构建
**脚本**: `kg_build_vocabularies.py`
**输出**: `kg/vocabularies/`
**功能**: 从标注文本中提取11类实体，生成分类词汇表

```bash
python kg_build_vocabularies.py
```

生成文件：
- 人名词典.md
- 地名词典.md
- 官职词典.md
- 时间词典.md
- 朝代词典.md
- 制度词典.md
- 族群词典.md
- 器物词典.md
- 天文词典.md
- 神话词典.md
- 动植物词典.md

### 2. 人物关系提取
**脚本**: `kg_extract_all_relations.py`
**输出**: `kg/relations/`
**功能**: 提取所有人物间的关系（家族、政治、师徒等）

```bash
python kg_extract_all_relations.py
```

### 3. 家族关系提取
**脚本**: `kg_extract_family_relations.py`
**输出**: `kg/relations/`
**功能**: 专门提取家族关系（父子、母子、兄弟、姻亲等）

```bash
python kg_extract_family_relations.py
```

### 4. 帝王家谱构建
**脚本**: `kg_extract_imperial_genealogy.py`
**输出**: `kg/genealogy/`
**功能**: 构建各朝代帝王世系图

```bash
python kg_extract_imperial_genealogy.py
```

生成文件：
- 五帝朝帝王家谱.md
- 夏朝帝王家谱.md
- 商朝帝王家谱.md
- 周朝帝王家谱.md
- 秦朝帝王家谱.md
- 汉朝帝王家谱.md
- imperial_genealogy.json

### 5. 动植物实体提取
**脚本**: `kg_extract_flora_fauna.py`
**输出**: `kg/vocabularies/动植物词典.md`
**功能**: 提取文本中的动植物实体

```bash
python kg_extract_flora_fauna.py
```

## 数据格式

### 词汇表格式 (Markdown)
```markdown
# 人名词典

## 统计信息
- 总词条数: 1234
- 高频人物 (出现>10次): 56人

## 词条列表

### 高频词条
1. **刘邦** (356次)
   - 别名: 汉高祖、沛公
   - 相关章节: ...

### 按首字母排序
...
```

### 关系数据格式 (Markdown/JSON)
```markdown
# 父子关系

## 刘邦 → 刘盈
- 关系类型: 父子
- 出处: 高祖本纪 [23]
- 上下文: "太子盈，仁弱..."
```

### 家谱格式 (Markdown)
```markdown
# 汉朝帝王家谱

## 世系图
```
刘邦 (汉高祖)
├─ 刘盈 (汉惠帝)
├─ 刘恒 (汉文帝)
...
```
```

## 使用场景

1. **学术研究**: 人物关系分析、社会网络研究
2. **可视化**: 构建交互式知识图谱界面
3. **智能问答**: 支持"刘邦的儿子是谁"等问题
4. **文本分析**: 实体统计、共现分析、网络中心性分析

## 技术栈

- **实体提取**: 基于规则的标注（@人名@, =地名= 等）
- **关系抽取**: 模式匹配 + 语义分析
- **数据格式**: Markdown (人类可读) + JSON (机器可读)
- **可视化**: 计划使用 D3.js / Cytoscape.js

## 未来计划

- [ ] 完善事件索引系统
- [ ] 构建完整的人物关系图谱
- [ ] 添加时空信息（地理坐标、时间轴）
- [ ] 开发交互式可视化界面
- [ ] 支持图数据库（Neo4j）导入
- [ ] 提供 SPARQL 查询接口

## 相关文档

- [实体标注方案](../ENTITY_TAGGING_SCHEME.md)
- [动植物标注指南](../FLORA_FAUNA_TAGGING_GUIDE.md)
- [项目README](../README.md)
