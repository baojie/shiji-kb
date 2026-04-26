# backlinks 插件

在每个页面末尾注入「被以下页面引用」区块，按类型分组展示反向链接。

---

## 数据来源

`wiki/public/backlinks.json`，由构建脚本生成：

```bash
python3 wiki/scripts/build_backlinks.py
```

结构：
```json
{
  "曹参": [
    { "id": "曹参初从沛公", "label": "曹参初从沛公", "type": "event" },
    ...
  ]
}
```

---

## 渲染

反向链接按页面类型分组（人名、地名、邦国、事件……），每组内链接并排显示。若某页面无反向引用，则不渲染该区块。

```html
<section class="backlinks" id="backlinks">
  <h2 class="bl-heading">被以下页面引用</h2>
  <div class="bl-body">
    <span class="bl-group">
      <span class="bl-group-label">事件</span>
      <a class="wikilink resolved bl-link" href="#曹参初从沛公">曹参初从沛公</a>
      ...
    </span>
  </div>
</section>
```

---

## Hook 使用

| Hook | 作用 |
|---|---|
| `onBoot` | 一次性 fetch `backlinks.json`，挂载到 `core.backlinks` |
| `onAfterRender` | 在渲染后的 HTML 末尾追加反向链接区块 |

---

## 构建依赖

无外部依赖。`backlinks.json` 必须在部署前由构建脚本生成，否则区块静默不显示。
