# 技术文章渲染器完成说明

## 文件位置
`/home/baojie/work/knowledge/shiji-kb/render_tech_article.py`

## 功能概述

`render_tech_article.py` 是专门用于渲染技术文章的Markdown到HTML转换器，基于史记渲染器修改，专用于 `doc/publications/` 下的技术文章。

## 已实现功能

### 1. 技术文章专用实体类型支持

新增3种技术文章专用实体类型：
- **术语** `〖#术语〗` → `<span class="terminology">`
- **职业** `〖※职业〗` → `<span class="profession">`
- **方法论** `〖★方法论〗` → `<span class="methodology">`

### 2. 知识工程动词分类系统

实现4类知识工程工作流动词标注：
- **构建动词** `⟦◆构建⟧` → `<span class="verb-construct">` (知识创造)
- **处理动词** `⟦◇处理⟧` → `<span class="verb-process">` (数据整理)
- **推理动词** `⟦◎推理⟧` → `<span class="verb-reason">` (逻辑分析)
- **应用动词** `⟦◈应用⟧` → `<span class="verb-apply">` (实践使用)

### 3. CSS路径智能检测

```python
# 优先使用同目录下的技术文章CSS
css_file = md_path.parent / 'kg-tech-article-styles.css'
# 如果不存在，尝试使用docs/css下的备用CSS
if not css_file.exists():
    css_file = md_path.parent.parent / 'docs' / 'css' / 'shiji-styles.css'
```

默认CSS：`kg-tech-article-styles.css`（与markdown文件同目录）

### 4. 文章日期自动生成

从文件修改时间自动提取发表日期：
```python
from datetime import datetime
article_mtime = os.path.getmtime(md_path)
article_date = datetime.fromtimestamp(article_mtime).strftime('%Y年%m月%d日')
```

在h1标题后自动插入日期元数据：
```html
<h1>标题</h1>
<div class="article-meta">发表于 2026年03月19日</div>
```

### 5. 句子级排版与语义缩进

新增 `split_paragraph_to_sentences()` 函数：
- 按句号、问号、感叹号分割段落为句子
- 检测逻辑连接词（因此、所以、由此、从而、进而、此外等15个）
- 自动应用语义缩进（0em / 2em）
- 输出结构：
  ```html
  <p class="sentence-layout">
      <span class="sentence-indent-0">第一句。</span>
      <span class="sentence-indent-1">因此第二句。</span>
  </p>
  ```

### 6. 简化的HTML模板

移除史记专用功能：
- ❌ 章节导航栏（prev/next links）
- ❌ 原文链接
- ❌ 章节导航CSS
- ❌ Purple Numbers JS
- ❌ 氏族名称转换
- ❌ 年表数据注入

保留核心功能：
- ✅ 实体标注渲染
- ✅ 动词分类渲染
- ✅ 引号对话样式
- ✅ 段落编号（Purple Numbers）
- ✅ 表格转换
- ✅ 韵文自动分行
- ✅ 嵌套span展平

## 使用方法

### 基本用法
```bash
python render_tech_article.py <markdown文件> [输出文件] [css文件]
```

### 示例
```bash
python render_tech_article.py doc/publications/draft/从历史书中探索知识图谱.tagged.md
```

### 参数说明
- `<markdown文件>`: 必需，输入的 `.tagged.md` 文件路径
- `[输出文件]`: 可选，默认为同名 `.html` 文件
- `[css文件]`: 可选，默认为同目录下的 `kg-tech-article-styles.css`

## 实体类型完整列表

### 史记通用实体（继承）
1. `〖@人名〗` → person
2. `〖=地名〗` → place
3. `〖;官职〗` → official
4. `〖%时间〗` → time
5. `〖&氏族〗` → dynasty
6. `〖'邦国〗` → feudal-state
7. `〖^制度〗` → institution
8. `〖~族群〗` → tribe
9. `〖•器物〗` → artifact
10. `〖!天文〗` → astronomy
11. `〖?神话〗` → mythical
12. `〖+生物〗` → biology
13. `〖{典籍〗` / `〖|典籍〗` → book（书名号外置）
14. `〖:礼仪〗` → ritual
15. `〖[刑法〗` → legal
16. `〖_思想〗` → concept
17. `〖$数量〗` → quantity

### 技术文章专用实体（新增）
18. `〖#术语〗` → terminology（技术术语）
19. `〖※职业〗` → profession（现代职业）
20. `〖★方法论〗` → methodology（方法论）

### 技术文章动词（新增）
21. `⟦◆构建⟧` → verb-construct
22. `⟦◇处理⟧` → verb-process
23. `⟦◎推理⟧` → verb-reason
24. `⟦◈应用⟧` → verb-apply

## 配套CSS要求

`kg-tech-article-styles.css` 需包含以下类的样式定义：

```css
/* 技术文章专用实体 */
.terminology { /* 术语样式 */ }
.profession { /* 职业样式 */ }
.methodology { /* 方法论样式 */ }

/* 知识工程动词 */
.verb-construct { /* 构建动词样式 */ }
.verb-process { /* 处理动词样式 */ }
.verb-reason { /* 推理动词样式 */ }
.verb-apply { /* 应用动词样式 */ }

/* 句子级排版 */
p.sentence-layout {
    display: flex;
    flex-direction: column;
    gap: 0.3em;
}

.sentence-indent-0 {
    display: block;
    padding-left: 0;
}

.sentence-indent-1 {
    display: block;
    padding-left: 2em;
}

/* 文章元数据 */
.article-meta {
    margin-top: 10px;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #e0dcc8;
    color: #666;
    font-size: 0.9em;
}
```

## 与史记渲染器的区别

| 功能 | 史记渲染器 | 技术文章渲染器 |
|------|-----------|---------------|
| CSS默认路径 | `docs/css/shiji-styles.css` | `kg-tech-article-styles.css`（同目录） |
| 导航栏 | ✅ 前后章导航 | ❌ 独立文章 |
| 日期显示 | ❌ | ✅ 从文件mtime |
| 原文链接 | ✅ | ❌ |
| 动词分类 | 军事/政治/刑罚/经济 | 构建/处理/推理/应用 |
| 术语支持 | ❌ | ✅ terminology |
| 职业支持 | ❌ | ✅ profession |
| 方法论支持 | ❌ | ✅ methodology |
| 句子级排版 | ❌ | ✅ 语义缩进 |
| 氏族名转换 | ✅ | ❌ |
| 年表注入 | ✅ | ❌ |

## 文件状态

✅ **完成** - 所有计划功能已实现

## 测试建议

```bash
# 1. 渲染技术文章
python render_tech_article.py doc/publications/draft/从历史书中探索知识图谱.tagged.md

# 2. 在浏览器中打开生成的HTML
# 检查：
# - 实体颜色是否正确
# - 动词分类是否显示
# - 日期是否出现在标题下
# - 句子是否正确缩进
# - CSS样式是否加载

# 3. 语法检查
python -m py_compile render_tech_article.py
```

## 相关文件

- 源脚本：[render_tech_article.py](../render_tech_article.py)
- CSS样式：[kg-tech-article-styles.css](publications/draft/kg-tech-article-styles.css)
- 示例文章：[从历史书中探索知识图谱.tagged.md](publications/draft/从历史书中探索知识图谱.tagged.md)
- 文档重组计划：[DOC_REORGANIZATION_PLAN.md](DOC_REORGANIZATION_PLAN.md)

## 更新日志

- **2026-03-19**: 初始完成，基于史记渲染器创建技术文章专用版本
  - 新增3种技术实体类型（术语、职业、方法论）
  - 新增4类知识工程动词标注
  - 实现CSS路径智能检测
  - 实现文章日期自动生成
  - 实现句子级语义缩进
  - 移除史记专用功能（导航栏、年表等）
  - 简化为独立文章HTML模板
