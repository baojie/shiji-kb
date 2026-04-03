# Purple Numbers (PN) 映射表说明

## 概述

本目录包含《史记》章节在PN规范化前后的编号映射表，用于将旧版本的PN引用更新到新版本。

## 版本对比

- **旧版本**: `6b20e096` - PN规范化之前（2026-04-02 02:27）
- **新版本**: `74032d6` - PN规范化之后（2026-04-02 22:33）
- **对比时间**: 2026-04-02 23:41

## 文件说明

### 1. `pn_mapping_complete.json`

完整的映射表，包含置信度等元数据信息。

**结构**:
```json
{
  "_meta": {
    "description": "文件描述",
    "old_version": { "commit": "6b20e096", "date": "...", "description": "..." },
    "new_version": { "commit": "74032d6", "date": "...", "description": "..." },
    "generated_at": "生成时间",
    "total_chapters": 73,
    "total_mappings": 1322
  },
  "mappings": {
    "章节编号": {
      "旧PN": {
        "new_pn": "新PN",
        "confidence": 置信度分数(0-100),
        "status": "changed"
      }
    }
  }
}
```

**示例**:
```json
{
  "_meta": {
    "description": "史记章节Purple Numbers (PN)映射表 - 完整版",
    "old_version": {
      "commit": "6b20e096",
      "date": "2026-04-02 02:27:56 +0800"
    },
    "new_version": {
      "commit": "74032d6",
      "date": "2026-04-02 22:33:53 +0800"
    }
  },
  "mappings": {
    "002": {
      "23": {
        "new_pn": "24",
        "confidence": 100.0,
        "status": "changed"
      }
    }
  }
}
```

### 2. `pn_mapping_simple.json`

简化版映射表，只包含PN映射关系，便于程序使用。

**结构**:
```json
{
  "_meta": {
    "description": "文件描述",
    "old_version": { "commit": "6b20e096", "date": "...", "description": "..." },
    "new_version": { "commit": "74032d6", "date": "...", "description": "..." },
    "generated_at": "生成时间",
    "total_chapters": 73,
    "total_mappings": 1322,
    "note": "说明信息"
  },
  "mappings": {
    "章节编号": {
      "旧PN": "新PN"
    }
  }
}
```

**示例**:
```json
{
  "_meta": {
    "description": "史记章节Purple Numbers (PN)映射表 - 简化版",
    "old_version": {
      "commit": "6b20e096",
      "date": "2026-04-02 02:27:56 +0800"
    },
    "new_version": {
      "commit": "74032d6",
      "date": "2026-04-02 22:33:53 +0800"
    }
  },
  "mappings": {
    "002": {
      "23": "24",
      "24": "25"
    }
  }
}
```

## 统计数据

### 总体统计

- **有变化的章节**: 73 个（占全部130章的56%）
- **总映射数**: 1322 个
- **高置信度映射 (≥95%)**: 1303 个 (98.6%)
- **中置信度映射 (80-95%)**: 19 个 (1.4%)
- **未找到匹配**: 0 个

### 变化最多的章节（Top 15）

| 章节编号 | 章节名称 | 映射数量 | 高置信度 | 中置信度 |
|---------|---------|---------|---------|---------|
| 042 | 郑世家 | 201 | 201 | 0 |
| 026 | 历书 | 201 | 201 | 0 |
| 041 | 越王句践世家 | 81 | 80 | 1 |
| 101 | 袁盎晁错列传 | 79 | 78 | 1 |
| 111 | 卫将军骠骑列传 | 78 | 78 | 0 |
| 043 | 赵世家 | 58 | 58 | 0 |
| 112 | 平津侯主父列传 | 55 | 53 | 2 |
| 067 | 仲尼弟子列传 | 52 | 52 | 0 |
| 044 | 魏世家 | 45 | 45 | 0 |
| 110 | 匈奴列传 | 43 | 42 | 1 |
| 129 | 货殖列传 | 34 | 33 | 1 |
| 123 | 大宛列传 | 30 | 28 | 2 |
| 122 | 酷吏列传 | 27 | 26 | 1 |
| 039 | 晋世家 | 24 | 23 | 1 |
| 121 | 儒林列传 | 18 | 18 | 0 |

## 使用方法

### 1. Python脚本使用

```python
import json

# 加载映射表
with open('data/pn_mapping_simple.json') as f:
    data = json.load(f)

# 查看元数据
print(f"版本: {data['_meta']['old_version']['commit']} -> {data['_meta']['new_version']['commit']}")
print(f"总映射数: {data['_meta']['total_mappings']}")

# 查找章节042中旧PN "45" 对应的新PN
chapter = "042"
old_pn = "45"
new_pn = data['mappings'].get(chapter, {}).get(old_pn)
print(f"042章 pn-{old_pn} -> pn-{new_pn}")
```

### 2. 命令行查询

```bash
# 查看元数据
cat data/pn_mapping_simple.json | jq '._meta'

# 查看章节039的所有映射
cat data/pn_mapping_simple.json | jq '.mappings."039"'

# 查找特定映射
cat data/pn_mapping_simple.json | jq '.mappings."039"."2.3"'

# 统计某章节的映射数量
cat data/pn_mapping_simple.json | jq '.mappings."039" | length'
```

### 3. 更新HTML文件中的PN引用

使用 `scripts/update_timeline_pn.py` 脚本（或类似工具）：

```bash
python scripts/update_pn_references.py \
    --mapping data/pn_mapping_simple.json \
    --input your_file.html \
    --output updated_file.html
```

## 匹配算法

### 文本清洗

为了准确匹配新旧版本的段落，我们使用以下清洗策略：

1. 去除所有标注符号：`〖TYPE content〗` `⟦TYPE⟧`
2. 去除所有标点符号：`。，、；！？：""''《》（）`
3. 去除所有空白字符：空格、换行等
4. 取前150个字符用于匹配

### 置信度计算

- **100分**: 完全匹配（清洗后的文本完全相同）
- **80-99分**: 开头匹配（前N个字符匹配度>=80%）
- **<80分**: 不匹配（不记录）

## 注意事项

### 1. 未找到映射的情况

有些旧版本的PN在新版本中无法找到对应，可能的原因：

- 段落内容发生了较大变化
- 段落被合并或拆分
- 标注符号过多导致清洗后内容太短
- 新版本中该段落不存在

这些未映射的PN在完整版JSON中标记为 `"new_pn": null`。

### 2. 一对多映射

在某些情况下，多个旧PN可能映射到同一个新PN，这通常发生在：

- 段落合并：多个小段落合并成一个大段落
- PN编号规范化：去除了某些层级的编号

### 3. 人工验证建议

虽然大部分映射的置信度都很高（98.6%≥95%），但在关键应用中仍建议：

- 抽查一些置信度<95%的映射
- 对于重要段落，手动验证映射的正确性
- 使用diff工具对比更新前后的差异

## 生成脚本

映射表由以下脚本生成：

```bash
scripts/build_complete_pn_mapping.py
```

运行方式：

```bash
python scripts/build_complete_pn_mapping.py
```

## 更新历史

- **2026-04-02 23:41**: 初始版本，基于 6b20e096 → 74032d6 的对比
  - 生成了73个章节的1322个PN映射
  - 置信度: 98.6%高置信度，1.4%中置信度
  - 时间跨度: 约20小时（02:27 → 22:33）的PN规范化工作

## 相关文档

- [Purple Numbers规范](../skills/SKILL_02b_Purple_Numbers规范.md)
- [PN验证脚本](../scripts/verify_timeline_pn_content.py)
- [PN更新工具](../scripts/update_timeline_pn.py)

## 许可证

本映射表数据与《史记》知识库项目使用相同的许可证。
