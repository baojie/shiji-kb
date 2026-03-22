# resources/ - 静态参考资料

本目录包含项目的静态参考资料，与运行时生成的文档（`doc/`）区分开来。

## 目录结构

```
resources/
├── publications/      # 出版物（论文、书籍、演讲）
│   ├── meta-skill-book/       # 元技能方法论PDF（425页，2.35MB）
│   ├── pipeline-skills-book/  # 管线技能手册PDF（438页，3.01MB）
│   ├── draft/                 # 技术文章草稿
│   │   └── 从历史书中探索知识图谱.pdf
│   ├── notes/                 # 写作笔记
│   ├── talks/                 # 演讲材料
│   └── 公众号文章/            # 公众号系列文章
│
├── references/        # 外部参考文献
│   ├── IDEA.md                # 创意与想法记录
│   └── 图形化阅读价值系统.pdf
│
└── help/              # 写作指南、使用帮助
    └── CONTRIBUTING.md        # 参与指南（规划中）
```

## 核心资源

### 📚 两本方法论手册

1. **[大规模知识库构造元技能方法论](publications/meta-skill-book/大规模知识库构造元技能方法论.pdf)** (425页，2.35MB)
   - 14个元技能：OTF+JIT+Bootstrap、反思循环、冷启动、柳叶刀方法等
   - 通用知识工程方法论，可迁移到任何领域

2. **[史记知识库构造管线技能手册](publications/pipeline-skills-book/史记知识库构造管线技能手册.pdf)** (438页，3.01MB)
   - 40个管线技能：校勘→结构分析→实体构建→事件构建→关系构建→本体构建→逻辑推理→SKU→应用
   - 古籍处理完整技术栈

### 📄 技术文章

- **[从历史书中探索知识图谱](publications/draft/从历史书中探索知识图谱.pdf)** (14页，1.5MB)
  - 项目缘起、核心成果、技术架构、元技能体系的完整呈现
  - 发表于 2026-03-19

### 🎤 演讲材料

- **[用Agent构建大规模知识库](publications/talks/2026-03-19_用Agent构建大规模知识库.pdf)**
  - PPTX + PDF 版本

## 与 doc/ 的区别

| 目录 | 性质 | 内容 | 示例 |
|------|------|------|------|
| **resources/** | 静态参考资料 | 出版物、论文、外部文献 | PDF手册、技术文章、演讲PPT |
| **doc/** | 动态生成文档 | 规范、日志、反思报告 | 实体反思报告、技术规范、工作流文档 |

## 生成PDF手册

### 元技能方法论
```bash
cd resources/publications/meta-skill-book
python3 generate_meta_skills_pdf.py
```

### 管线技能手册
```bash
cd resources/publications/pipeline-skills-book
python3 generate_pipeline_skills_pdf.py
```

## 相关目录

- 运行时文档：[`doc/`](../doc/)
- 项目结构总览：[`PROJECT_STRUCTURE.md`](help/PROJECT_STRUCTURE.md)
- 技能文档：[`skills/`](../skills/)
