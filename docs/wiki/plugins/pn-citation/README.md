# pn-citation 插件

将页面正文中的段落号引文渲染为指向史记原文 HTML 锚点的外链。

---

## 语法

插件识别两种写法：

**标准写法**（wikilink 形式，展开后）：
```markdown
（[[040_楚世家|040-082]]）
```

**纯文本写法**：
```markdown
（040-082）
（040-082意旨）
（022-r7）
```

`意旨` 后缀表示转述而非直引，链接正常生成。`r` 前缀表示表格行号。

---

## 渲染结果

```html
（<a class="pn-citation" href="https://baojie.github.io/shiji-kb/chapters/040_楚世家.html#pn-82"
    target="_blank" title="040-82 原文">040-82</a>）
```

链接在新标签页打开，`title` 属性显示章节-段落号。

---

## 目标 URL

```
https://baojie.github.io/shiji-kb/chapters/{章节文件名}.html#pn-{段落号}
```

章节文件名从 `data/chapter_map.json` 解析（格式：`{"040": "040_楚世家", ...}`）。匹配不到章节号时保留原文不变。

---

## Hook 使用

| Hook | 作用 |
|---|---|
| `onBoot` | fetch `data/chapter_map.json`，构建章节号 → 文件名映射 |
| `onAfterRender` | 正则替换 HTML 中所有引文形式为带链接的 `<a>` 标签 |

---

## 数据依赖

`wiki/public/data/chapter_map.json`，结构：
```json
{ "040": "040_楚世家", "054": "054_曹相国世家", ... }
```
