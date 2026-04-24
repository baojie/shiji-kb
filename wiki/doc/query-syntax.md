# ::: query 语义查询语法

Wiki 页面中可嵌入 `::: query` 块，对 `registry.json` 中的页面 metadata 执行客户端查询。

## 基本格式

```
::: query
type: person
featured: true
sort: total_refs
order: desc
limit: 50
display: table
fields: [label, tags, total_refs, total_chapters]
title: 精品人物
:::
```

## 过滤参数

| 参数 | 匹配方式 | 示例 |
|------|---------|------|
| `type` | 字符串相等 | `type: person` |
| `tags` | 数组包含 | `tags: 楚国` |
| `featured` | 布尔相等 | `featured: true` |
| `<field>_min` | 数值下限（≥） | `total_refs_min: 10` |
| `<field>_max` | 数值上限（≤） | `total_refs_max: 100` |

**规则**：字符串字段精确相等；若页面字段为数组、查询值为字符串，检查数组是否包含该值；`_min`/`_max` 后缀做数值范围过滤。

## 显示参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `sort` | `label` | 排序字段 |
| `order` | `asc` | `asc` 升序 / `desc` 降序 |
| `limit` | `200` | 最多返回条数 |
| `display` | `list` | `list`（项目符号两列）/ `table`（表格）|
| `fields` | `[label,type,tags,total_refs]` | table 模式列名 |
| `title` | 无 | 结果区块标题 |

## 可查询字段（来自 registry.json）

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 页面类型 |
| `tags` | array | 标签列表 |
| `featured` | bool | 是否精品 |
| `total_refs` | number | 被引用次数 |
| `total_chapters` | number | 涉及章节数 |
| `quality_score` | number | 质量分 |
| `lifespan` | string | 活跃期 |

> `birth_ce`、`death_ce`、`event_type` 等字段尚未进入 registry，需扩展
> `wiki/scripts/build_registry.py` 后才可查询。

## 技术实现

- **执行位置**：`wiki/public/plugins/semantic-block/index.js`（`executeQuery` / `renderQueryBlock`）
- **数据来源**：`core.registry.pages`（随页面加载，纯内存过滤）
- **触发时机**：`onAfterRender` hook，同步执行
