---
name: skill-03d
description: 标注文本HTML渲染与结构语义表现。当需要将.tagged.md转换为可视化网页、生成实体索引、发布到GitHub Pages时使用。适用于成果展示、在线阅读器构建、知识库发布等场景。
---


# SKILL 03d: HTML渲染与结构语义表现 — 标注文本输出为HTML

> 将标注完成的 `chapter_md/*.tagged.md` 输出为可发布的HTML。本SKILL仅描述从实体构建阶段到输出的衔接；渲染器、配色、交互等详细设计见 **SKILL 09a 语法高亮辅助阅读**。

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

→ **[SKILL 09a 语法高亮辅助阅读](SKILL_09a_语法高亮辅助阅读.md)**

---

## 五、TODO 规划

### 5.1 HTML5语义化改造

**现状问题**：
- 当前生成的HTML结构不够语义化
- 未充分利用HTML5的语义标签
- HTML结构与Markdown源文件的逻辑结构对应不够清晰

**改造目标**：
- 使用HTML5语义标签（`<article>`, `<section>`, `<aside>`, `<nav>` 等）
- HTML结构严格对应Markdown的层次结构
- 段落编号（Purple Numbers）映射为明确的HTML锚点
- 区块（Fenced Div）映射为语义化的`<div>`结构
- 实体标注保持内联语义（`<span>`配合`data-*`属性）

**预期效果**：
- 提升页面可访问性（accessibility）
- 便于搜索引擎理解内容结构
- 简化CSS样式层次
- 便于JavaScript操作DOM结构
- 为语义搜索和图谱探索提供更好的结构基础

**实现优先级**：中等（待SKILL_09d实现时配合改造）
