# SKILL 05a: 渲染与发布 — 从标注文本到可交互HTML

> 将 `chapter_md/*.tagged.md` 标注文本渲染为带语法高亮的HTML页面，并发布到 GitHub Pages。

---

## 一、工序位置

```
标注文本 (chapter_md/*.tagged.md)
    ↓ 渲染（本SKILL）
HTML页面 (docs/chapters/*.html)
    ↓ 发布
GitHub Pages
```

与主管线并行，标注完成后即可渲染。

---

## 二、渲染器

### 核心逻辑

`render_shiji_html.py` — 有序正则替换，将Token标记转为HTML span：

```python
ENTITY_PATTERNS = [
    (r'\*\*(.+?)\*\*', 'bold'),      # 粗体先于*器物*
    (r'\^(.+?)\^', 'institution'),
    ...
    (r'@(.+?)@', 'person'),           # 人名最后（常作内层）
]
```

**处理顺序**：`**粗体**` → 外层标记 → 内层标记 → `@人名@`（最后）

### 段落锚点

段落编号 `[1.1]` 渲染为可点击锚点，生成永久链接 `#pn-1.1`。

---

## 三、CSS样式

- **配色**：深沉暗色系，低透明度背景
- **字体**：思源宋体（Noto Serif SC），行高2.0
- **对话**：斜体 + 极淡褐色底色 + 虚线边界
- **表格**：全视口宽度、sticky表头、交替行背景

---

## 四、实体索引页

```
扫描 tagged.md → 正则提取实体 → 别名合并 → 拼音排序 → 生成HTML索引页
```

每类实体生成独立索引页，条目含出现次数、章节分布、别名列表。

---

## 五、发布

```bash
python render_shiji_html.py          # 渲染全部章节
python generate_all_chapters.py      # 批量生成
bash publish_to_docs.sh              # 发布到 GitHub Pages
```
