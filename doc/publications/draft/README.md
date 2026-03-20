# 技术文章渲染说明

## 使用专用渲染器

技术文章使用专用渲染器 `render_tech_article.py`，支持：

1. **技术文章特定实体**
   - 〖#术语〗 `.terminology`
   - 〖※职业〗 `.profession`  
   - 〖★方法论〗 `.methodology`
   - 〖|典籍〗 `.book`（技术文章格式）

2. **知识工程动词**
   - ⟦◆构建⟧ `.verb-construct`
   - ⟦◇处理⟧ `.verb-process`
   - ⟦◎推理⟧ `.verb-reason`
   - ⟦◈应用⟧ `.verb-apply`

3. **排版特性**
   - 句子级排版（每句一行）
   - 语义缩进（因果、递进等逻辑关系）
   - 自动添加文章日期

## 渲染命令

```bash
python render_tech_article.py doc/publications/draft/从历史书中探索知识图谱.tagged.md
```

## CSS样式

技术文章使用同目录下的 `kg-tech-article-styles.css`
