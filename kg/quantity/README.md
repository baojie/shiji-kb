# 数量实体 (Quantity)

非时间性计量表达的词表和标注规则。

## 数据文件

| 文件 | 说明 |
|------|------|
| `quantity_wordlist.json` | 分类词表（always_quantity / context_dependent / exclude_patterns） |

## 标注格式

`〖$X〗`（v2.5 新增）

## 分类

- 军队：万人、千人、百人
- 距离：千里、百里
- 度量：寸、尺、丈、斤
- 金额：金、钱
- 行政：户、石、社

## 与时间的区分

`exclude_patterns` 列出应归入 `〖%时间〗` 的表达（元年、二月等），避免混淆。

纯数据模块，标注脚本在 `scripts/tag_quantity_entities.py`。
