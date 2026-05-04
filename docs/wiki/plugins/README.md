# 插件系统

> 灵感来自 MediaWiki extensions。插件在 core 的 hook 点注册回调, 改变 wiki 行为。
> 未来的**语义层**（`:::query` 指令、KG 查询、模板推理）将作为一个插件实现。

## 清单（`plugins.json`）

```json
{
  "plugins": [
    "plugins/semantic/index.js",
    "plugins/search/index.js"
  ]
}
```

路径相对于 wiki 根目录。加载顺序 = 清单顺序。

## 插件模块约定

每个插件是一个 **ES Module**, 默认导出一个对象:

```js
// plugins/<name>/index.js
export default {
  name: 'semantic',
  version: '0.1.0',
  init(core) {
    // 注册 hook handler
    core.hooks.onBeforeRender.add((body, ctx) => {
      // 返回新 body, 或 undefined 保持不变
    });
  },
};
```

`init(core)` 可以是 async 的。在所有插件 init 完成后, `onBoot` hook 才触发。

## 可用 Hook

| Hook | 签名 | 返回语义 | 用途举例 |
| --- | --- | --- | --- |
| `onBoot` | `(core) → *` | 忽略 | 插件初始化二阶段 |
| `onRoute` | `(raw: string, core) → string \| null \| undef` | `string`=改写 raw; `null`=已自行处理; 其他=保持 | 特殊页面 `special/…` |
| `onBeforeRender` | `(body: string, ctx: {pid,meta,front}) → string` | 返回新 body | 解析 `:::query` 指令 |
| `onAfterRender` | `(html: string, ctx: {pid,meta,front}) → string` | 返回新 html | 添加脚注 / 图谱注入 |
| `onInfobox` | `(rows: string[], front, meta) → rows` | 返回新 rows 数组 | 追加自定义属性行 |

`ctx.meta` = `pages.json` 里的页面条目; `ctx.front` = 页面 frontmatter。

## `core` 对象

```ts
core = {
  hooks:    { onBoot: Hook, onRoute: Hook, onBeforeRender: Hook, ... },
  registry: { pages: {...}, alias_index: {...} },
  md:       MarkdownIt 实例,
  plugins:  [{ name, version }, ...],
}
```

插件可以 `import { resolvePageId } from '../js/registry.js'` 等复用核心模块。

## 预定的 `semantic` 插件

v2 引入时计划实现:

1. `onBeforeRender`: 识别 `:::query kind="..."  ...:::` 代码块, 对接 KG JSON / TTL / SPARQL, 把查询结果拼成 MD 片段回填。
2. `onInfobox`: 从 KG 自动补充属性行。
3. 注册一组内置 query kind: `entity_facts` / `events_of` / `mentions_in` / ...

## 开发建议

- **一个插件 = 一个目录**: `plugins/<name>/index.js`, 可以再拆子模块
- **副作用只在 init**: 避免模块顶层直接改 DOM
- **容错**: handler 内部 try/catch, 失败时返回 undefined, 让页面继续渲染
- **版本**: 写清 `version`, 方便将来兼容性判断
