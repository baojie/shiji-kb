# 更新日志 (Changelog)

本文档记录《史记》知识库项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [Unreleased]

### 计划中

- 实施10大高级分析
- 开发交互式可视化平台
- 构建Neo4j知识图谱数据库
- index页面展开小节目录、章节卡片高度可变

---

## [项目文件结构整理](https://github.com/baojie/shiji-kb/commit/0de6edc) - 2026-02-08

### 更改 (Changed)

- 📁 **工具脚本统一到 `scripts/` 目录**
  - 移入lint_markdown.py、lint_html.py、fix_verse_format.py等11个工具脚本
  - 根目录仅保留 render_shiji_html.py 和 generate_all_chapters.py 两个核心脚本
- 📝 **文档统一到 `doc/` 目录**
  - 移入CHANGELOG.md、TODO.md、FORMAT_SPECIFICATION.md、WORKFLOW.md等
  - 移入小节划分完成报告.md等中文文档

---

## [HTML渲染修复](https://github.com/baojie/shiji-kb/commit/fbf6b4b) - 2026-02-08

### 修复 (Fixed)

- 🐛 **标注符号泄露修复**
  - 修复嵌套实体标注时 `$`、`@` 等标记符号泄露到HTML的问题
  - 调整ENTITY_PATTERNS处理顺序：外层标记（`**`、`*`）先于内层标记（`@`最后）
  - 添加安全网清理：最终移除所有残留标注符号
- 🎵 **韵文格式修复**
  - 修复秦始皇本纪等章节的韵文/诗歌格式（verse类）
- 💬 **对话缩进**
  - 为引语内容添加CSS缩进样式（`.quoted`类）

---

## [全部130章小节划分](https://github.com/baojie/shiji-kb/commit/98d97a3) - 2026-02-08

### 新增 (Added)

- 📑 **为全部130章完成有意义的小节划分**
  - 每章按内容语义划分为多个小节
  - 小节数据保存到 sections_data.json
  - index页面各章卡片显示可点击的小节链接

---

## [项目结构重构](https://github.com/baojie/shiji-kb/commit/2f8f0ad) - 2026-02-08

### 新增 (Added)
- 📁 **项目结构大幅重构**
  - 创建 `kg/` 目录统一管理知识图谱相关内容
  - 创建 `doc/` 目录管理技术文档
  - 创建 `temp/` 目录存放历史开发文件
  - 创建 `private/` 目录存放隐私敏感脚本
- 🎮 **史记争霸游戏**
  - 初始版本包含4个章节的互动游戏
  - Netlify部署包创建脚本
  - 游戏设计文档和说明

### 更改 (Changed)
- 🔧 **Python脚本整理**
  - 5个知识图谱脚本移至 `kg/` 目录并统一 `kg_` 前缀
  - 6个历史开发工具移至 `temp/` 目录
  - 根目录保留6个核心HTML生成工具
  - 移除所有脚本中的个人路径信息
- 📝 **文档整理**
  - 技术规范文档移至 `doc/` 目录
  - 知识图谱相关文档移至 `kg/` 目录
  - 游戏设计文档移至 `game/` 目录
  - 根目录仅保留 `README.md` 和 `TODO.md`
- 📖 **README.md重大更新**
  - 更新目录结构说明
  - 更新所有文档路径引用
  - 添加脚本使用说明

### 修复 (Fixed)
- 🐛 修复知识图谱脚本输出路径错误
- 🔒 移除所有脚本中的隐私路径信息

---

## [知识图谱系统完善](https://github.com/baojie/shiji-kb/commit/863b6c3) - 2026-02-07

### 新增 (Added)
- 📊 **知识图谱系统完善**
  - 知识图谱脚本统一命名规范（kg_前缀）
  - 知识图谱输出统一到 `kg/` 子目录
  - 创建 `kg/README.md` 详细文档
- 📂 **scripts/目录规范**
  - 特定章节处理脚本移至 `temp/`
  - 保留6个通用工具脚本

### 更改 (Changed)
- 🔄 **批处理脚本整理**
  - 46个临时批处理文件移至 `temp/` 目录
  - 创建 `temp/README.md` 说明文档
- 📋 **文档路径更新**
  - 更新所有知识图谱脚本使用说明
  - 统一输出路径为相对路径

---

## [HTML展示系统完善](https://github.com/baojie/shiji-kb/commit/02508b4) - 2026-02-06

### 新增 (Added)
- 🌐 **HTML展示系统完善**
  - 引号格式修复工具 `fix_quote_issues.py`
  - 小节链接提取工具 `extract_sections.py`
  - 索引页小节链接更新工具 `update_index_with_sections.py`
  - 章节内部section ID添加工具
  - 完整的 `sections_data.json` 数据文件
- 📝 **index.html重大改进**
  - 添加未来开发路线图
  - 每章添加可点击的小节链接
  - 移除统计部分（设计优化）
  - 实体标签示例简化（仅显示颜色）

### 修复 (Fixed)
- 🐛 **引号格式问题**
  - 修复56章及其他40章的引号HTML渲染错误
  - 使用负向后顾断言避免匹配HTML属性
  - 批量重新生成所有受影响章节

---

## [完整HTML生成系统](https://github.com/baojie/shiji-kb/commit/02508b4) - 2026-02-06

### 新增 (Added)
- 🏗️ **完整HTML生成系统**
  - 130章节全部生成HTML
  - 批量生成工具 `generate_all_chapters.py`
  - 统一的HTML渲染框架
- 📊 **研究方法体系**
  - 《研究方法总则.md》
  - 《史记高级分析计划.md》
  - 《史记统计分析.md》
  - 《史记编年表.md》

### 更改 (Changed)
- 📈 **标注进度**
  - 完成99/130章节标注（76.2%）
  - 涵盖本纪12篇、表10篇、书8篇、世家30篇、列传39篇

---

## [核心标注系统建立](https://github.com/baojie/shiji-kb/commit/73c7aed) - 2026-01-23

### 新增 (Added)
- 📚 **核心标注系统建立**
  - 11类实体标注规范（人名、地名、官职、时间等）
  - Purple Numbers段落编号系统
  - Markdown转HTML核心工具 `render_shiji_html.py`
- 🎨 **样式系统**
  - 实体语法高亮（11种不同颜色）
  - 对话内容样式（斜体+网纹阴影）
  - 段落编号小黄框样式
  - 可点击的段落锚点和hash URL分享
- 📖 **文本结构化**
  - 长段落智能拆分逻辑
  - 对话内容拆分规则
  - 列表结构识别
  - 诗歌按行排版

### 更改 (Changed)
- 🔄 **文件重命名**
  - `*.simple.md` → `*.tagged.md`

---

## [项目启动/RDF试验](https://github.com/baojie/shiji-kb/commit/256f6cc) - 2025-02至03

### 新增 (Added)
- 🚀 **项目启动** (2025-02-04)
  - 手工编写RDF/TTL知识图谱（高祖本纪8.1、8.2节）
  - 创建本体定义文件 `ontology.ttl`
  - 建立GitHub仓库
- 📝 **技术路线转型** (2026-01-22起)
  - 拆分130篇《史记》原始文本
  - 转向Markdown标注系统
  - 完成五帝本纪、夏本纪初步转化

---

## 标注进度统计

| Commit | 日期 | 已标注章节 | 完成度 | 里程碑 |
|--------|------|-----------|--------|--------|
| [2f8f0ad](https://github.com/baojie/shiji-kb/commit/2f8f0ad) | 2026-02-08 | 130/130 | 100% ✅ | 项目结构重构 |
| [863b6c3](https://github.com/baojie/shiji-kb/commit/863b6c3) | 2026-02-07 | 130/130 | 100% ✅ | 知识图谱系统 |
| [02508b4](https://github.com/baojie/shiji-kb/commit/02508b4) | 2026-02-06 | 130/130 | 100% ✅ | HTML展示完善 |
| [02508b4](https://github.com/baojie/shiji-kb/commit/02508b4) | 2026-02-06 | 130/130 | 100% ✅ | 完整HTML生成 |
| [73c7aed](https://github.com/baojie/shiji-kb/commit/73c7aed) | 2026-01-23 | 52/130 | 40% | 核心系统建立 |
| [256f6cc](https://github.com/baojie/shiji-kb/commit/256f6cc) | 2025-02至03 | 2/130 | 1.5% | 项目启动+RDF/TTL |

---

## 技术栈变更

### 当前技术栈
- Python 3.9+
- JavaScript (ES6+)
- HTML5/CSS3
- Markdown
- Git/GitHub

### 未来计划
- Neo4j（知识图谱数据库）
- D3.js（可视化）
- React（前端框架）
- FastAPI（后端API）

---

## 贡献者

- [@baojie](https://github.com/baojie) - 项目创建者和主要维护者
- Claude Sonnet 4.5 / Opus 4.6 - AI助手（标注工具开发、文档编写）

---

## 许可证变更

- **v0.1.0+**:
  - 内容：CC BY-NC-SA 4.0
  - 代码：MIT License

---

**最后更新**: 2026-02-08
**当前版本**: v0.5.0
