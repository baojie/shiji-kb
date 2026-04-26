# semantic-block 插件

处理页面中所有 `:::` 语义块，提供 `infobox`、`meta`、`seealso` 三种内置类型，并通过 `core.semanticBlock` 把块缓存暴露给其他插件（`semantic-query`）。

---

## 块类型

### `:::infobox`

在 sidebar 渲染结构化信息框；第一个 infobox 注入 sidebar，之后的以折叠卡片渲染在正文内。

```markdown
::: infobox
label: 曹参
birth_ce: -257
death_ce: -190
title: 平阳侯
office: 相国
:::
```

支持字段见源码 `INFOBOX_FIELD_MAP`。非标准字段自动追加为附加行。

---

### `:::meta`

机器可读元数据块，渲染为隐藏的 `<div data-block-type="meta">`，不在页面显示。供脚本/构建工具提取扩展字段。

```markdown
::: meta
pn: (054-5)
event_type: 战争
location: 齐
chapter: [曹相国世家]
:::
```

---

### `:::seealso`

渲染「详细参见」卡片（绿色左边框 + 📖 图标），每行一个 wikilink，用于章节页引导读者跳转专题页。

```markdown
::: seealso
[[曹参征战时间线]] — 从龙起兵到击平陈豨的完整征战时序（054-001 ~ 054-008）
[[曹参起事——从沛狱掾到攻城野战之冠]] — 深度分析
:::
```

多条链接时每行一条；单条链接渲染为单行段落，多条渲染为无序列表。

> **注**：`:::seealso` 的内容在 `onBeforeRender` 阶段提取，此时 wikilink 尚未被 `protectWikilinks` 替换；插件在 `onAfterRender` 中自行展开 `[[...]]` 为 `<a>` 标签。

---

## 其他 `:::` 类型

不属于以上三种的块被提取为占位符，`onAfterRender` 中渲染为：

```html
<div class="semantic-block" data-block-type="TYPE" data-meta='...' hidden></div>
```

`semantic-query` 插件依赖此机制拦截 `:::query` 块（返回原占位符，不由本插件展开）。

---

## 暴露 API

```js
core.semanticBlock.getBlocks(pid)   // 返回该页面所有块 [{idx, blockType, meta, rawContent}]
core.semanticBlock.PH_OPEN          // 占位符起始字符（供 semantic-query 使用）
core.semanticBlock.PH_CLOSE         // 占位符结束字符
```

---

## Hook 使用

| Hook | 作用 |
|---|---|
| `onBeforeRender` | 提取所有 `:::` 块，替换为占位符 |
| `onAfterRender` | 展开 `infobox` / `seealso` 占位符；`meta` 置空；`query` 保留给 semantic-query |
| `onInfobox` | 将第一个 infobox 的非系统字段注入 sidebar 行 |

---

## CSS 类

| 类 | 说明 |
|---|---|
| `.infobox` | sidebar 信息框 |
| `.infobox.inline` | 折叠式行内信息框 |
| `.seealso-block` | 详细参见卡片（绿色左边框） |
| `.seealso-label` | 卡片标题「📖 详细参见」 |
| `.semantic-block` | 隐藏的机器可读块容器 |

---

## 构建依赖

无外部依赖；`seealso` 块展开依赖 `../../js/registry.js` 中的 `resolvePageId`。
