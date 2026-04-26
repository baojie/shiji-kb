# math 插件

渲染页面中的数学公式，支持行内和块级两种形式。

默认**关闭**，需在 `Special:Settings` 中手动启用。史记知识库正文较少使用公式，主要用于统计分析类页面。

---

## 语法

```markdown
行内公式：$E = mc^2$

块级公式：
$$
\sum_{i=1}^{n} x_i = X
$$
```

也支持 LaTeX 括号写法：`\(...\)` 和 `\[...\]`。

---

## 启用方式

在 `Special:Settings` 页面将 `plugins.math` 设为 `true`，或手动写入 localStorage：

```js
localStorage.setItem('wiki_settings', JSON.stringify({ plugins: { math: true } }));
```

---

## 实现

启用后动态从 CDN 加载 KaTeX：

| 资源 | URL |
|---|---|
| KaTeX CSS | `https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css` |
| KaTeX JS | `https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js` |
| auto-render | `https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js` |

渲染调用 `renderMathInElement(article, { throwOnError: false })`，公式错误时静默跳过。

---

## Hook 使用

| Hook | 作用 |
|---|---|
| `onAfterRender` | 渲染完成后在 `#article` 元素上调用 KaTeX auto-render |

---

## 注意

需要网络连接才能从 CDN 加载 KaTeX。离线环境需自行将 KaTeX 文件本地化。
