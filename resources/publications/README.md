# Publications - 出版物与分享

史记知识库项目的对外出版物、文章、演讲资料等。

## 📚 核心出版物

### 1. 方法论手册（PDF）

两本系统性方法论手册，总结了用AI Agent构建大规模知识图谱的完整方法体系：

| 手册 | 页数 | 大小 | 内容 | 目录 |
|------|------|------|------|------|
| [大规模知识库构造元技能方法论](meta-skill-book/) | 425页 | 2.6MB | 14个通用元技能方法论 | [查看](meta-skill-book/) |
| [史记知识库构造管线技能手册](pipeline-skills-book/) | 438页 | 3.0MB | 40个管线技能（从校勘到应用） | [查看](pipeline-skills-book/) |

**适用场景**：古籍数字化、法律文书结构化、医学文献提取、企业知识图谱构建等任何大规模知识工程项目。

### 2. 学术演讲（Talks）

| 日期 | 标题 | 格式 | 场合 |
|------|------|------|------|
| 2026-03-19 | [用Agent构造大规模知识库](talks/2026-03-19_用Agent构造大规模知识库.pdf) | PDF/PPTX | 技术分享 |

## 📝 已发布文章

| 标题 | 平台 | 日期 | 文件 |
|------|------|------|------|
| 给《史记》加上语法高亮：一个人+一群AI的55小时 | 01fish | 2026-03-08 | [查看](公众号文章/2026-03-08_给史记装上语法高亮.md) |

## 📄 草稿与内部文档

### Draft - 待发布文章

| 文件 | 说明 | 状态 |
|------|------|------|
| [agentic_ontology_101.md](draft/agentic_ontology_101.md) | Agentic Ontology 101（英文），对标 Noy & McGuinness 2001 经典论文 | draft |
| [史记阅读器重构与语义排版.md](draft/史记阅读器重构与语义排版.md) | 五层阅读器进化与认知辅助设计 | draft |

### Notes - 过程记录与思考

| 文件 | 说明 | 用途 |
|------|------|------|
| [项目初衷、愿景与未来方向.md](notes/项目初衷、愿景与未来方向.md) | 项目核心理念与演化路径 | 内部参考 |
| [史记语法高亮创造过程.md](notes/史记语法高亮创造过程.md) | 语法高亮功能开发的详细过程记录 | 公众号文章源草稿 |

## 📂 目录结构

```
publications/
├── meta-skill-book/        # 元技能方法论PDF（425页，2.6MB）
│   ├── 大规模知识库构造元技能方法论.pdf
│   ├── 大规模知识库构造元技能方法论.html
│   ├── 大规模知识库构造元技能方法论_摘要.md
│   ├── generate_meta_skills_pdf.py
│   └── README.md
│
├── pipeline-skills-book/   # 管线技能手册PDF（438页，3.0MB）
│   ├── 史记知识库构造管线技能手册.pdf
│   ├── 史记知识库构造管线技能手册.html
│   ├── generate_pipeline_skills_pdf.py
│   └── README.md
│
├── talks/                  # 演讲资料
│   ├── 2026-03-19_用Agent构造大规模知识库.pdf
│   └── 2026-03-19_用Agent构造大规模知识库.pptx
│
├── 公众号文章/             # 已发布的外部文章
│   └── 2026-03-08_给史记装上语法高亮.md
│
├── draft/                  # 待发布草稿
│   ├── agentic_ontology_101.md
│   ├── 史记阅读器重构与语义排版.md
│   └── fig*.{png,jpg}      # 配图资源
│
├── notes/                  # 过程记录与内部文档
│   ├── 项目初衷、愿景与未来方向.md
│   └── 史记语法高亮创造过程.md
│
└── README.md               # 本文档
```

## 🔧 重新生成PDF手册

### 安装依赖

```bash
pip3 install --break-system-packages markdown weasyprint
```

### 生成命令

```bash
# 元技能方法论手册
cd meta-skill-book
python3 generate_meta_skills_pdf.py

# 管线技能手册
cd pipeline-skills-book
python3 generate_pipeline_skills_pdf.py
```

## 📋 发布规范

### 文件命名规范

- **已发布文章**：`YYYY-MM-DD_标题.md`（放入对应平台子目录）
- **草稿文件**：`标题.md`（放入 `draft/` 目录）
- **过程记录**：`标题.md`（放入 `notes/` 目录）
- **演讲资料**：`YYYY-MM-DD_标题.{pdf,pptx}`（放入 `talks/` 目录）

### 草稿元数据（Frontmatter）

每个草稿文件头部应包含：

```yaml
---
status: draft | published
published_as: 公众号文章/YYYY-MM-DD_标题.md   # 发布后填写
platforms: [01fish, 微信公众号, ...]            # 发布后填写
published_date: YYYY-MM-DD                    # 发布后填写
---
```

## 📞 联系方式

**作者**：鲍捷
- Email: baojie@gmail.com
- 微信: baojiexigua
- GitHub: [@baojie](https://github.com/baojie)

---

**最后更新**：2026-03-19
