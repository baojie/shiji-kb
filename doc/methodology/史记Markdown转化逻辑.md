# 《史记》语义化 Markdown 转化逻辑

> 本文档已重构为根目录下的 SKILL 文档。

---

## 文本语义化（TXT → tagged.md）

完整规范已迁移至：**[SKILL_古籍文本语义化.md](../../SKILL_古籍文本语义化.md)**

涵盖：
- 章节层级结构（#/##/###）
- 段落编号规则（Purple Numbers，[N]、[N.1]、[N.1.1]）
- 11类实体 Token 标注（@人名@、=地名= 等）
- 对话拆分规则（X曰 → 列表格式）
- NOTE 块（谏言/策论/制度/传说）
- 段落长度控制（叙事段落 ≤150 字）
- 大模型 NER 推荐工作流

## Markdown → HTML 渲染与发布

完整流程见：**[doc/workflow/开发工作流程.md](../workflow/开发工作流程.md)**

涵盖：
- 单章渲染（`render_shiji_html.py`）
- 批量生成（`generate_all_chapters.py`）
- 发布到 GitHub Pages（`./publish_to_docs.sh`）
