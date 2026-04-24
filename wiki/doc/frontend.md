# Wiki 前端架构说明

> 面向 coding agent 的开发参考文档。
> 如需修改 wiki 功能、新增插件，请先读本文。

---

## 1. 运行时架构

wiki 是纯客户端 SPA（Single Page Application）。服务器只提供静态文件，
所有渲染均在浏览器中完成。

```
index.html
  └─ 加载依赖（markdown-it, js-yaml, KaTeX...）
  └─ import js/core.js
       ├─ loadRegistry()      ← 读 pages.json（全量页面索引）
       ├─ loadPlugins()       ← 读 plugins.json，动态 import 各插件
       ├─ hooks.onBoot.run()  ← 插件初始化完成
       └─ setupRouter()       ← 监听 URL hash，响应导航
```

### 页面渲染流程

URL hash 变化 → router 调用 `mountPage(pid)` → renderer.js：

```
fetch pages/<pid>.md
  │
  ▼ parser.js: parseMarkdown(core, mdText, {pid, meta, front})
  │
  ├── splitFrontmatter()          → {front, body}
  ├── hooks.onBeforeRender(body)  → body     ← 插件在此预处理 MD 源
  ├── protectWikilinks(body)      → 占位符
  ├── markdownIt.render()         → HTML
  ├── expandWikilinks()           → 占位符 → <a>
  └── hooks.onAfterRender(html)   → html     ← 插件在此后处理 HTML
  │
  ▼ renderer.js: mountPage()
  ├── renderInfobox(core, front, meta)
  │     └── hooks.onInfobox(rows, front, meta)  ← 插件在此注入 sidebar 行
  └── 更新 DOM (#title, #infobox, #article, #footer)
```

---

## 2. 核心文件一览

| 文件 | 职责 |
|------|------|
| `core.js` | 启动入口；定义 `core` 对象（hooks / registry / md / plugins） |
| `hooks.js` | Hook 系统；`hook.add(fn)` 注册，`hook.run(val)` 执行链 |
| `parser.js` | Markdown 解析主流水线（frontmatter→wikilink→MD→hook） |
| `renderer.js` | DOM 挂载；`mountPage` / `renderInfobox` / `renderHome` |
| `router.js` | URL hash 路由；解析 `#pid` / `#?recent` / `#?search` |
| `registry.js` | 加载 `pages.json`，提供 `resolvePageId(target)` |
| `wikilink.js` | `[[id]]` / `[[id\|text]]` 解析与展开 |
| `frontmatter.js` | YAML frontmatter 分离（`---` 块） |
| `util.js` | `escapeHtml` / `TYPE_LABELS` / `showFatal` |
| `special.js` | `Special:` 命名空间页（Settings / AllPages 等） |

---

## 3. Hook 系统

所有 hook 均为异步 filter 链：handler 返回新值则替换，返回 `undefined` 则透传。

### 全部 Hook

```javascript
// 注册方式
core.hooks.<hookName>.add(async (value, ...rest) => { ... });

// 五个 hook
onBoot(core)
  // 插件初始化完成，core 已就绪。适合一次性全局初始化。

onRoute(rawHash, core) → string | null | undefined
  // 路由前拦截。返回字符串则重写 hash；返回 null 表示已自行处理（阻止默认路由）。

onBeforeRender(body, {pid, meta, front}) → body
  // MD 源文本预处理。替换或注入语法（如 ::: 块 → 占位符）。

onAfterRender(html, {pid, meta, front}) → html
  // MD→HTML 完成后。替换占位符为最终 HTML，或做 DOM 无关的 HTML 修改。

onInfobox(rows, front, meta) → rows
  // sidebar infobox 行数组（HTML 字符串[]）。追加或修改行。
```

### 调用时序

```
onBeforeRender  (parseMarkdown 内)
onAfterRender   (parseMarkdown 内)
onInfobox       (renderInfobox 内，parseMarkdown 之后)
```

---

## 4. 插件结构

### 文件布局

```
wiki/public/plugins/
└── <plugin-id>/
    ├── plugin.json    # 元数据（必需）
    └── index.js       # 插件主体（必需，ES module）
```

### plugin.json 格式

```json
{
  "id": "my-plugin",
  "name": "插件显示名",
  "version": "1.0.0",
  "description": "一句话说明",
  "entry": "index.js",
  "settings_key": "my_plugin"   // 可选，对应 localStorage wiki_settings.plugins.<key>
}
```

### index.js 最小骨架

```javascript
export default {
  name: 'my-plugin',
  version: '1.0.0',

  async init(core) {
    // 在这里注册 hook
    core.hooks.onAfterRender.add(async (html, ctx) => {
      // 处理 html，返回新 html
      return html.replace(/TODO/, '<mark>TODO</mark>');
    });
  },
};
```

### 注册插件

编辑 `wiki/public/plugins.json`，在 `plugins[]` 数组中加入条目：

```json
{
  "id": "my-plugin",
  "entry": "plugins/my-plugin/index.js",
  "name": "...",
  "version": "1.0.0",
  "description": "..."
}
```

> `scan_plugins.py` 可自动扫描 plugins/ 目录重新生成此文件：
> ```bash
> python wiki/scripts/scan_plugins.py
> ```

---

## 5. 占位符约定

wikilink 和语义块都用 Unicode 私用区字符作为 MD 渲染期间的占位符，
避免 markdown-it 对 `|` 等字符的特殊处理。

| 用途 | 开 | 关 | 所在文件 |
|------|----|----|---------|
| wikilink `[[...]]` | `` | `` | `wikilink.js` |
| 语义块 `:::` | `` | `` | `plugins/semantic-block/index.js` |

新插件如需占位符，使用 `` 以上的私用区字符，避免冲突。

---

## 6. 现有插件列表

| ID | 功能 | Hook 使用 |
|----|------|-----------|
| `semantic-block` | `::: infobox` / `::: meta` 语义块 | onBeforeRender, onAfterRender, onInfobox |
| `math` | KaTeX 数学公式 `$...$` | onAfterRender |

---

## 7. 新功能开发指引

### 扩展 infobox sidebar 字段

在任意插件的 `onInfobox` handler 中向 `rows` 数组 push HTML 字符串：

```javascript
core.hooks.onInfobox.add(async (rows, front, meta) => {
  if (front.my_field) {
    rows.push(`<tr><th>自定义</th><td>${escapeHtml(front.my_field)}</td></tr>`);
  }
  return rows;
});
```

### 新增 MD 语法扩展

1. `onBeforeRender`：用正则匹配新语法，替换为 `\uE04XN\uE04Y` 占位符，存到模块变量
2. `onAfterRender`：将 `<p>\uE04XN\uE04Y</p>` 替换为最终 HTML

参考 `plugins/semantic-block/index.js` 的完整实现。

### 自定义路由

```javascript
core.hooks.onRoute.add(async (raw, core) => {
  if (raw.startsWith('?mypage')) {
    document.getElementById('article').innerHTML = '...';
    return null;   // null = 已处理，阻止默认路由
  }
  // return undefined = 不干预
});
```

### 访问调试

浏览器控制台：`window.__wiki` 即 `core` 对象，可查看 registry、hooks、plugins。

---

## 8. 数据文件

| 文件 | 内容 | 生成方式 |
|------|------|---------|
| `pages.json` | 全量页面索引（id/label/aliases/type/tags/quality_score...） | `python wiki/scripts/build_registry.py` |
| `plugins.json` | 已启用插件清单 | 手编 或 `python wiki/scripts/scan_plugins.py` |
| `recent.json` | 最近更新列表 | `python wiki/scripts/record_revision.py` |
| `pages/<id>.md` | 页面源文件（YAML frontmatter + Markdown body） | 手写 或脚本生成 |

---

## 9. Python 端（静态渲染）

`wiki/scripts/render_html.py` 可将 `.md` 批量编译为 `.html`，用于离线/SEO 场景。
它与客户端 JS 管道**相互独立**，需分别维护逻辑同步：

- 语义块解析：`wiki/scripts/semantic_block.py`（Python）↔ `plugins/semantic-block/index.js`（JS）
- 新语法如在两端都需支持，要同步修改两个文件

```bash
# 重新渲染单页
python wiki/scripts/render_html.py wiki/public/pages/项羽.md

# 重新渲染全部
python wiki/scripts/render_html.py wiki/public/pages/*.md
```
