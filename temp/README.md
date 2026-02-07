# 临时文件目录

本目录存放项目开发过程中的临时脚本、处理报告和进度文件。

## 目录内容

### 批处理脚本 (18个)
用于批量处理史记章节的Python脚本，包括：
- `batch_*.py` - 批量标注脚本
- `process_*.py` - 章节处理脚本

这些脚本用于项目开发阶段的批量处理任务，已完成使命。

### 历史开发工具 (6个)
从根目录移动过来的早期开发工具：
- `annotate_entities.py` / `_v2.py` / `_v3.py` - 实体标注工具（3个版本）
- `add_numbering.py` - 添加段落编号
- `improve_readability.py` - 改善可读性
- `split_shiji.py` - 拆分史记完整文本

### 特定章节处理脚本 (9个)
从scripts/目录移动过来的特定章节批处理脚本：
- `*111_130*` - 111-130章节处理相关（5个文件）
- `generate_html_051_060.py` - 051-060世家HTML生成
- `start_processing_084_095.sh` - 084-095列传处理启动脚本
- `start_processing.sh` - 通用处理启动脚本

### 处理报告 (23个)
各批次处理的进度报告、完成报告、质控报告等文档：
- 处理报告
- 完成报告
- 质控验证
- 使用说明

### 进度文件 (2个)
JSON格式的处理进度跟踪文件：
- `progress_043_050.json`
- `progress_096_110.json`

### 其他临时文件
- 差异报告
- 章节列表
- 快速开始指南

## 说明

这些文件保留作为项目开发历史记录，但不再用于日常开发流程。

当前项目使用的主要脚本：
- `generate_all_chapters.py` - 批量生成所有章节HTML
- `render_shiji_html.py` - 单个章节Markdown转HTML
- `extract_sections.py` - 提取章节小节信息
- `update_index_with_sections.py` - 更新索引页
