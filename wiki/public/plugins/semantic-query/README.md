# semantic-query 插件

将页面中的 `:::query` 块渲染为动态表格或列表，查询数据来自 `core.registry`（即 `pages.json`）。

依赖 `semantic-block` 插件先注册（`:::query` 块由 semantic-block 在 `onBeforeRender` 提取为占位符，本插件在 `onAfterRender` 接管渲染）。

---

## 语法

```markdown
::: query
type: person
tags_any: [楚汉之际, 开国功臣]
tags_not: [争议]
sort: birth_ce
order: asc
limit: 20
display: table
fields: [label, birth_ce, death_ce, tags]
field_labels:
  label: 姓名
  birth_ce: 生年
  death_ce: 卒年
title: 楚汉之际开国功臣
:::
```

---

## 过滤参数

| 参数 | 说明 | 示例 |
|---|---|---|
| `type` | 精确匹配页面类型 | `type: person` |
| `type_any` | 类型列表，匹配任一 | `type_any: [person, event]` |
| `tags` | 精确包含该 tag | `tags: 楚汉之际` |
| `tags_any` | 包含列表中任一 tag | `tags_any: [楚汉之际, 春秋]` |
| `tags_not` | 排除包含列表中任一 tag | `tags_not: [stub]` |
| `featured` | 是否为精品页 | `featured: true` |
| `{field}_min` | 数值字段下界（含） | `birth_ce_min: -250` |
| `{field}_max` | 数值字段上界（含） | `death_ce_max: -200` |
| 其他字段 | 精确相等匹配 | `quality: premium` |

---

## 显示参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `display` | `list` | `list`（链接列表）或 `table`（表格） |
| `fields` | `[label]` | 表格显示的字段列表 |
| `field_labels` | — | 字段名 → 列标题的映射 |
| `sort` | `label` | 排序字段 |
| `order` | `asc` | `asc` 或 `desc` |
| `limit` | `200` | 最多显示条数 |
| `title` | — | 表格/列表标题 |

---

## computed 字段

支持对 registry 字段做算术表达式，结果作为虚拟字段：

```yaml
computed:
  lifespan: death_ce - birth_ce
```

表达式支持 `+` `-` `*` `/` 和括号，变量为 registry 中的数值字段名。

---

## Hook 使用

| Hook | 作用 |
|---|---|
| `onAfterRender` | 从 `core.semanticBlock` 取缓存，展开 `query` 占位符为 HTML |

---

## 数据来源

`core.registry.pages`（即 `wiki/public/pages.json`），由构建脚本 `wiki/scripts/build_registry.py` 生成。查询结果为运行时动态过滤，无需预构建查询索引。
