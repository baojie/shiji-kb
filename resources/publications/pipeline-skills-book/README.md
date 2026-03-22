# 史记知识库构造管线技能手册

## 简介

本文档集合将SKILL 00-09系列的所有管线技能整合为单个PDF手册，方便阅读和分享。

## 包含内容

完整的知识库构造管线技术规范，共40个技能文档：

- **SKILL 00**: 管线总览
- **SKILL 01**: 古籍校勘
- **SKILL 02**: 结构分析（含8个子技能：章节切分、区块处理、三家注标注等）
- **SKILL 03**: 实体构建（含5个子技能：实体标注、消歧、反思、渲染等）
- **SKILL 04**: 事件构建（含6个子技能：事件识别、年代推断、动词标注等）
- **SKILL 05**: 关系构建（含5个子技能：事件关系、实体关系、人物关系等）
- **SKILL 06**: 本体构建（含1个子技能：实体到本体）
- **SKILL 07**: 逻辑推理（含3个子技能：生卒年推断、姓氏推理、反常推理）
- **SKILL 08**: SKU构造
- **SKILL 09**: 应用构造（含2个子技能：认知辅助阅读器、知识库游戏化）

## 文件说明

- `史记知识库构造管线技能手册.pdf` - 最终生成的PDF文档（3.0 MB）
- `史记知识库构造管线技能手册.html` - 中间HTML文件
- `generate_pipeline_skills_pdf.py` - PDF生成脚本

## 如何重新生成

### 依赖安装

```bash
pip3 install --break-system-packages markdown weasyprint
```

### 生成PDF

```bash
python3 generate_pipeline_skills_pdf.py
```

脚本会自动：
1. 从 `skills/` 目录读取所有 SKILL_00 到 SKILL_09 开头的Markdown文件
2. 按文件名排序合并
3. 生成带封面和目录的HTML
4. 转换为PDF格式

## 文档特点

- 完整的管线技术规范
- 从古籍校勘到应用构造的全流程覆盖
- 包含详细的实施步骤和示例
- 适合技术人员参考和学习

## 作者

鲍捷
- Email: baojie@gmail.com
- 微信: baojiexigua
- GitHub: @baojie

## 生成日期

2026-03-19

## 相关文档

- [大规模知识库构造元技能方法论](../meta-skill-book/) - 14个核心元技能的方法论文档
- [在线技能文档目录](https://github.com/baojie/shiji-kb/tree/main/skills)
