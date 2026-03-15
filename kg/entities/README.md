# 实体库 (Entity Index)

从130篇标注文件中提取的规范实体库（12,380词条、99,214次标注），含别名合并、消歧和生物实体分类。

## 数据文件

| 文件 | 说明 |
|------|------|
| `entity_index.json` | 规范实体索引（18类，别名合并后） |
| `entity_aliases.json` | 别名映射（沛公→刘邦、汉王→刘邦等，595条） |
| `disambiguation_map.json` | 按章节的人名消歧规则（"武王"→"周武王"等，644处） |
| `identity_wordlist.json` | 身份类词表（always/context_dependent/new_candidates） |
| `feudal_state_wordlist.json` | 封国类词表 |
| `person_lifespans.json` | 人物生卒年 |
| `biology/` | 生物实体（动植物分类、词表、标注指南） |

### biology/ 子目录

| 文件 | 说明 |
|------|------|
| `biology_wordlist.json` | 生物实体词表（〖+〗标注） |
| `biology_taxonomy.md` | 生物分类树 |
| `FLORA_FAUNA_TAGGING_GUIDE.md` | 动植物标注指南 |
| `FLORA_FAUNA_PROJECT_SUMMARY.md` | 生物标注项目总结 |

## 与词表的区别

本索引按**规范实体**统计（别名合并后），词表（`kg/vocabularies/`）按**表面形式**统计（不合并）。
因此索引条目数 ≤ 词表词条数（人名差异最大，因古人别名众多）。

## 脚本

| 脚本 | 功能 |
|------|------|
| `build_entity_index.py` | 构建实体索引 + 生成 `docs/entities/*.html` |
| `disambiguate_names.py` | 四层启发式人名消歧 |
| `auto_detect_aliases.py` | 自动检测别名候选 |
| `validate_tagging.py` | 标注文本完整性验证（去标记后与原文比对） |
| `biology/extract_flora_fauna.py` | 生物实体提取 |

## 常用操作

```bash
python kg/entities/scripts/build_entity_index.py    # 重建索引+HTML
python kg/entities/scripts/disambiguate_names.py    # 人名消歧
python kg/entities/scripts/validate_tagging.py --all  # 验证全部130章
```
