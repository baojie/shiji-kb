---
name: SKILL_W12_语义查询与列表页
title: 语义查询与列表页
description: 在 Wiki 中创建 type:list 页面，使用 ::: query 块对页面/块 metadata 执行语义查询，生成动态列表
---

# SKILL_W12 — 语义查询与列表页

## 何时使用

- 需要对知识库中的页面按条件筛选、排序、汇总时
- 创建索引页（如"所有精品人物"、"楚国相关条目"）
- 替代手工维护的枚举列表

---

## 列表页格式

```markdown
---
id: 列表页名称
type: list
label: 列表页显示名
description: 简要说明
tags: [列表, 人物]   # 可选分类标签
---

# 列表页名称

正文说明（可选）。

::: query
type: person
featured: true
sort: total_refs
order: desc
limit: 50
display: table
fields: [label, tags, total_refs, total_chapters]
title: 精品人物（按引用次数排序）
:::
```

---

## ::: query 语法参考

### 过滤参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `type` | 字符串 | 页面类型相等 | `type: person` |
| `tags` | 字符串 | tags 数组包含 | `tags: 楚国` |
| `featured` | 布尔 | 是否精品 | `featured: true` |
| `total_refs_min` | 数字 | 引用次数下限 | `total_refs_min: 10` |
| `total_refs_max` | 数字 | 引用次数上限 | `total_refs_max: 100` |
| `total_chapters_min` | 数字 | 涉及章节数下限 | `total_chapters_min: 3` |
| `quality_score_min` | 数字 | 质量分下限 | `quality_score_min: 20` |

**过滤规则**：
- 字符串字段 → 精确相等
- 页面字段为数组、查询值为字符串 → 检查数组是否包含该值
- `field_min` / `field_max` 后缀 → 数值范围过滤

### 显示参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `sort` | `label` | 排序字段 |
| `order` | `asc` | `asc` 升序 / `desc` 降序 |
| `limit` | `200` | 最多返回条数 |
| `display` | `list` | `list`（项目符号）或 `table`（表格）|
| `fields` | `[label,type,tags,total_refs]` | `table` 模式的列 |
| `title` | 无 | 结果区块标题 |

### 可查询字段（来自 registry）

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 页面类型 |
| `tags` | array | 标签列表 |
| `featured` | bool | 是否精品 |
| `total_refs` | number | 被引用次数 |
| `total_chapters` | number | 涉及章节数 |
| `quality_score` | number | 质量分（综合计算） |
| `lifespan` | string | 人物活跃期（如"战国"） |

> **注意**：`birth_ce`、`death_ce`、`event_type` 等细粒度字段**尚未进入 registry**，
> 需扩展 `build_registry.py` 后才可查询。详见下方"扩展 registry"节。

---

## 内置示例页

| 页面 ID | 查询内容 |
|---------|---------|
| `精品人物列表` | `type:person + featured:true`，按引用次数排序 |
| `章节列表` | `type:chapter`，全部 130 章 |

---

## 在普通页面中嵌入查询

`::: query` 不限于 `type:list` 页，任何页面都可嵌入。例如在 `楚国` 概念页末尾附加：

```
::: query
tags: 楚国
type: person
sort: total_refs
order: desc
limit: 20
display: list
title: 相关人物
:::
```

---

## 扩展 registry 以支持更多字段

当前 `registry.json` 只含基础字段。若需查询 `birth_ce`、`death_ce`、`event_type` 等，
需修改 `wiki/scripts/build_registry.py`，在提取 frontmatter 时额外写入所需字段：

```python
# build_registry.py 中 entry 构建处新增：
EXTRA_FIELDS = ['birth_ce', 'death_ce', 'event_type', 'date', 'location']
for f in EXTRA_FIELDS:
    if f in meta:
        entry[f] = meta[f]
```

修改后重新运行：

```bash
python3 wiki/scripts/build_registry.py wiki/public/pages --out wiki/public/data/registry.json
```

---

## 技术实现

- **执行位置**：客户端，`semantic-block` 插件的 `onAfterRender` hook
- **数据来源**：`core.registry.pages`（全量加载，约 400 条，纯内存过滤）
- **渲染时机**：随页面 MD 渲染同步完成，无额外网络请求
- **实现文件**：`wiki/public/plugins/semantic-block/index.js`（`executeQuery` / `renderQueryBlock`）
