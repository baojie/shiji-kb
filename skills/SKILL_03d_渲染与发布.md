# SKILL 03d: 渲染与发布 — 标注文本输出为HTML

> 将标注完成的 `chapter_md/*.tagged.md` 输出为可发布的HTML。本SKILL仅描述从实体构建阶段到输出的衔接；渲染器、配色、交互等详细设计见 **SKILL 09a 认知辅助阅读器**。

---

## 一、工序位置

```
标注文本 (chapter_md/*.tagged.md)
    ↓ 渲染（SKILL 09a）
HTML页面 (docs/chapters/*.html)
    ↓ 发布
GitHub Pages
```

与主管线并行，标注完成后即可渲染。

---

## 二、快速命令

```bash
# 渲染单章
python render_shiji_html.py chapter_md/001_五帝本纪.tagged.md

# 批量生成全部130章
python generate_all_chapters.py

# 完整发布流水线（生成 + 路径修复 + lint检查）
bash publish_to_docs.sh
```

---

## 三、质量检查

```bash
# HTML格式检查
python scripts/lint_html.py docs/chapters/

# Markdown标注格式检查
python scripts/lint_markdown.py chapter_md/001_五帝本纪.tagged.md
```

---

## 四、详细设计

渲染器实现、18类实体配色、段落结构语义化、交互功能、实体索引页、发布流水线等详见：

→ **[SKILL 09a 认知辅助阅读器](SKILL_09a_认知辅助阅读器.md)**
