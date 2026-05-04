# footnote 插件

为页面提供学术脚注支持，渲染 `[^id]` 内联引用和 `[^id]: 定义` 脚注定义。

默认**关闭**，需在 `Special:Settings` 中手动启用。

---

## 语法

```markdown
曹参生年约前 257 年[^life]。

[^life]: 生年推断参见[《曹参生卒年推断》](../../doc/lifespan_inference/西汉/曹参.md)（置信度：约）。
```

渲染结果：正文中出现上标链接，页面底部出现脚注列表（含回跳箭头 ↑）。

---

## 启用方式

在 `Special:Settings` 页面将 `plugins.footnote` 设为 `true`，或手动写入 localStorage：

```js
localStorage.setItem('wiki_settings', JSON.stringify({ plugins: { footnote: true } }));
```

---

## 实现

依赖本地打包的 `markdown-it-footnote.js`（UMD 格式，无 CDN 依赖）。插件在 `init` 时动态加载该脚本并注册到 `core.md`（markdown-it 实例）。

回跳箭头从默认的 ↩︎ 替换为 ↑（更紧凑）。

---

## Hook 使用

不使用渲染 hook，直接通过 `core.md.use(plugin)` 扩展 markdown-it 解析器。

---

## CSS

内联注入，无需外部样式文件：

| 类 | 说明 |
|---|---|
| `.footnotes` | 脚注列表区块 |
| `.footnote-ref` | 正文上标引用 |
| `.footnote-backref` | 回跳箭头 ↑ |

---

## 构建依赖

`markdown-it-footnote.js` 随插件目录分发，无需 CDN。
