# 实体分类树

《史记》实体的层级分类体系。

## 文件

### 本体文件 (TTL)

| 文件 | 说明 | 类数 | 实例数 | 三元组 |
|------|------|------|--------|--------|
| `person.ttl` | 人物分类本体（OWL/RDF格式） | 130 | 1,821 | ~5,826 |
| `biology.ttl` | 生物分类本体（OWL/RDF格式） | 20 | 70 | 294 |

### 分类树 (Markdown)

| 文件 | 说明 |
|------|------|
| `person_taxonomy.md` | 人物分类树（可读视图，自动生成） |
| `biology_taxonomy.md` | 生物分类树（可读视图，自动生成） |

### 辅助数据

| 文件 | 说明 |
|------|------|
| `data/person_classified.json` | 人物分类中间数据（JSON格式） |

## 脚本

| 脚本 | 说明 |
|------|------|
| `scripts/build_taxonomy.py` | 通用分类树生成器（从 TTL 生成 Markdown） |
| `scripts/build_person_taxonomy.py` | [已废弃] 人物分类专用生成器 |

## 用法

### 生成分类树

```bash
# 从 RDF/OWL 本体生成人物分类树
python kg/taxonomy/scripts/build_taxonomy.py kg/taxonomy/person.ttl -o kg/taxonomy/person_taxonomy.md

# 从 RDF/OWL 本体生成生物分类树
python kg/taxonomy/scripts/build_taxonomy.py kg/taxonomy/biology.ttl -o kg/taxonomy/biology_taxonomy.md

# 自定义参数
python kg/taxonomy/scripts/build_taxonomy.py kg/taxonomy/person.ttl \
  --unit 人 \
  --max-show 30 \
  --order "王室,臣,策士,诸子百家,社会人物,方术,外邦,虚构人物,疑似误标"
```

### 参数说明

- `--unit`: 计数单位（人/种/条），默认自动推断
- `--max-show`: 每个叶子类最多显示的实例数（默认 20）
- `--order`: 根子类显示顺序（逗号分隔的中文标签）

## 数据来源

- **权威数据源**: `*.ttl` 文件（Turtle 格式的 OWL/RDF 本体）
  - `person.ttl` - 人物分类本体（130类/1821实例）
  - `biology.ttl` - 生物分类本体（20类/70实例）
- **解析内容**:
  - 类层次（`owl:Class` + `rdfs:subClassOf`）
  - 实例归类（`a <class>`）
  - 中文标签（`rdfs:label "X"@zh`）
  - 出现次数（`:count N`）
- **辅助数据**: `data/person_classified.json` - 人物分类中间数据（JSON格式）

## 设计原则

- **单一数据源**: TTL 本体是唯一权威，分类树 MD 文件为自动生成的可读视图
- **类型无关**: 同一脚本可处理人物/生物/地名/官职等任意实体类型
- **自动推断**: 根类、计数单位等自动识别，无需手动配置

## 相关目录

- [kg/rdf-hello-world/](../rdf-hello-world/) - RDF/OWL 入门示例（hello-world、高祖本纪等）
- [kg/ontology/](../ontology/) - 核心本体定义
- [kg/entities/](../entities/) - 实体数据
