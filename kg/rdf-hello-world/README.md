# RDF Hello World 示例

《史记》知识图谱 OWL/RDF 语义表示的入门示例文件。

## 文件

| 文件 | 说明 |
|------|------|
| `hello-world.ttl` | 入门示例 |
| `ontology.ttl` | 核心本体定义（类：人物/地点/事件，属性：父子/继承等） |
| `8.1.ttl`, `8.2.ttl` | 高祖本纪实例数据（RDF 三元组） |

## 命名空间

```
http://memect.cn/baojie/ontologies/2025/1/shiji/
```

## 相关目录

主要 RDF/OWL 本体文件已移至 [kg/taxonomy/](../taxonomy/)：
- [person.ttl](../taxonomy/person.ttl) - 人物分类本体（130类/1821实例）
- [biology.ttl](../taxonomy/biology.ttl) - 生物分类本体（20类/70实例）
- [person_taxonomy.md](../taxonomy/person_taxonomy.md) - 人物分类树
- [biology_taxonomy.md](../taxonomy/biology_taxonomy.md) - 生物分类树

生成工具：[kg/taxonomy/scripts/build_taxonomy.py](../taxonomy/scripts/build_taxonomy.py)

## 状态

实验性入门示例模块。主要本体文件已移至 kg/taxonomy/。
