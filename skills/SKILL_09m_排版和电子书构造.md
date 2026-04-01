---
name: skill-09m
description: 古籍专业排版与电子书生成,将语义标注版本导出为高质量印刷品和电子书。当需要生成符合古籍排版规范的PDF、EPUB等格式时使用。支持LuaTeX竖排、紫色编号锚点、语义着色、多版本对照等专业功能。
---

# SKILL 09m: 排版和电子书构造 — 从语义标注到专业出版物

> 将语义标注Markdown转换为符合古籍排版规范的印刷品（PDF）和电子书（EPUB/MOBI），保留语义信息的同时提供专业的排版质量。

---

**⚠️ 状态说明**：本SKILL为规划文档，所有脚本和工具链**尚未开发**。当前为设计阶段，定义排版规范、技术选型和实现路径。

**核心价值**：
- 将语义标注知识库转化为**可印刷、可传播、可长期保存**的出版物
- 实现**线上阅读器↔纸质书↔电子书**的紫色编号统一引用
- 探索**语义信息如何在印刷媒介中可视化**的古籍排版新范式

---

## 一、设计理念

### 为什么需要专业排版

**Web阅读器 vs. 纸质阅读**：
- HTML阅读器（SKILL_09a）优势：交互、搜索、超链接、即时更新
- 纸质/电子书优势：便携、沉浸、专注、无设备依赖、更适合长时间阅读

**语义标注的价值**：
- 传统古籍排版：纯文字 + 句读标点
- 语义标注排版：**18类实体着色 + 4类动词标识 + 紫色编号系统**
- 目标：将语义信息以符合印刷规范的形式呈现

### 核心目标

1. **古籍排版规范**：遵循LuaTeX-CN等专业古籍排版标准（版心、行列、竖排等）
2. **语义信息保留**：实体着色、动词标识、段落编号在印刷版中可用
3. **多版本导出**：纯文本版、语法高亮版、对照版（原文+现代标点）、注释版
4. **电子书适配**：EPUB/MOBI格式优化，支持阅读器的语义导航
5. **可复现引用**：紫色编号（Purple Numbers）在印刷版中作为段落编号，确保精确引用

---

## 二、排版管线

### 2.1 整体流程

```
chapter_md/*.tagged.md
    ↓ 01 预处理：语义标注→排版中间格式
    ↓     - 实体Token→排版指令（颜色/样式）
    ↓     - Purple Numbers→段落编号
    ↓     - 区块标记→版式区分（太史公曰/赞/韵文）
    ↓
    ↓ 02 排版引擎分支
    ├─▶ LuaTeX-CN → PDF（古籍专业排版）
    │       - 竖排/横排可选
    │       - 版心/鱼尾/乌丝栏
    │       - 三家注侧栏/夹注
    │       - 实体着色（CMYK配色）
    │
    ├─▶ Pandoc + LaTeX → PDF（现代学术排版）
    │       - 横排为主
    │       - 实体高亮（彩色/单色可选）
    │       - 脚注/尾注/边注
    │
    └─▶ Pandoc → EPUB/MOBI（电子书）
            - 语义HTML内嵌
            - CSS着色样式
            - 目录/索引/超链接
```

### 2.2 关键技术选型

| 格式 | 引擎 | 优势 | 适用场景 |
|------|------|------|---------|
| **PDF（古籍竖排）** | LuaTeX-CN | 专业古籍排版规范（版心/鱼尾/竖排） | 古籍复原式出版、学术研究影印本 |
| **PDF（现代横排）** | Pandoc + XeLaTeX | 现代学术规范、易于集成脚注 | 现代教材、学术论文、研究著作 |
| **EPUB 3.0** | Pandoc | 语义HTML + CSS、设备兼容性好 | Kindle/Apple Books/通用阅读器 |
| **MOBI** | Pandoc + KindleGen | Kindle原生格式 | Kindle设备专用 |

---

## 三、LuaTeX-CN古籍排版

### 3.1 核心规范（参考 open-guji/luatex-cn）

**版面结构**：
- **版心**（text block）：可配置页边距、行数、每行字数
- **标准模板**：8行×21字（四库全书标准），可自定义
- **鱼尾装饰**：单鱼尾/双鱼尾可选
- **乌丝栏**：丝线边框模拟古籍栏线

**文字排列**：
- **竖排优先**：默认竖排从右到左，支持横排选项
- **网格定位**：像素级精确还原历史格式
- **字符间距**：支持传统中文可变字宽

**注释系统**：
- **夹注**：双栏侧注，跨列/跨页自动平衡
- **边注**：页眉注释、行侧评注
- **句读模式**：传统句读符/现代标点/无标点三种可切换

**特殊功能**：
- **改字**：字符校正标记
- **印章**：透明度可控的印章模拟
- **抬头**：自动换行的抬头处理
- **脚注变体**：节末注/页底注

**标点处理**：
- 大陆/台湾标准差异支持
- 标点压缩规则
- 排版约束自动应用

### 3.2 语义标注的排版映射

**实体着色方案（CMYK印刷色）**：

| 实体类型 | Web颜色（RGB） | 印刷颜色（CMYK） | 排版样式 |
|---------|---------------|----------------|---------|
| 人名 | #8B4513 褐色 | C30 M50 Y70 K20 | 实线下划线 + 淡黄底 |
| 地名 | #B8860B 深金 | C20 M30 Y80 K10 | 双实线 |
| 官职 | #8B0000 暗红 | C20 M100 Y100 K40 | 中粗 |
| 时间 | #008B8B 深青 | C100 M20 Y20 K10 | 斜体（宋体倾斜） |
| 朝代 | #9370DB 中紫 | C40 M50 Y0 K0 | 淡紫底 + 实线下划线 |
| 典籍 | #4B0082 靛蓝 | C100 M100 Y0 K20 | 波浪线 + 书名号 |
| 神话 | #8B008B 深品红 | C50 M100 Y0 K10 | 波浪线 + 中粗 |
| 数量 | #2E8B57 海绿 | C80 M0 Y50 K20 | 中粗 |

**动词着色方案**：

| 动词类型 | Web颜色 | 印刷颜色（CMYK） | 排版样式 |
|---------|--------|----------------|---------|
| 军事动词 | #DC143C 深红 | C10 M100 Y80 K0 | 加粗 + 淡红底 |
| 刑罚动词 | #8B0000 暗红 | C20 M100 Y100 K40 | 加粗 + 底线 |

**单色印刷版本**：
- 实体：下划线变化（实线/虚线/点线/波浪线）+ 字重变化（regular/medium/bold）
- 动词：加粗 + 方框（□）前缀
- 保持语义区分，降低印刷成本

### 3.3 紫色编号系统

**在印刷版中的呈现**：
- 段落编号 `[1.2.3]` 排版为页边注或行内小字
- 单色版：灰色小字（10pt，正文14pt）
- 彩色版：淡紫色（C20 M30 Y0 K0）
- 位置选项：
  - **页边注**（推荐）：不干扰正文，便于引用
  - **行内**：紧跟段首，适合现代排版
  - **页底索引**：每页列出该页所有段落编号

**交叉引用**：
- 书籍印刷版和Web版使用相同编号体系
- 印刷版引用：见[1.2.3]
- Web版链接：https://shiji-kb.org/007#pn-1.2.3
- 实现**纸质版↔电子版精确对应**

### 3.4 区块差异化排版

| 区块类型 | Web样式 | 印刷样式（LuaTeX） |
|---------|--------|-------------------|
| 太史公曰 | 暗金左边框 + 暖白底 | 单独段落 + 小字（12pt） + 缩进 + 顶部装饰线 |
| 赞 | 棕色左边框 + 斜体 | 楷体 + 居中 + 上下装饰线 |
| 诗歌/韵文 | 橄榄绿左边框 + 斜体 | 楷体 + 缩进 + 保持硬换行 |
| 对话引用 | 淡褐底 + 虚线 | 缩进两字 + 楷体 |

---

## 四、现代学术排版（Pandoc + LaTeX）

### 4.1 适用场景

- 现代教材、参考书
- 学术论文、研究著作
- 需要复杂公式、图表、参考文献的场景
- 横排为主，适合现代阅读习惯

### 4.2 排版特性

**页面设置**：
- A4/B5可选，页边距符合出版规范
- 页眉：章节名 + 页码
- 页脚：书名 + 版权信息

**实体高亮**：
- 彩色版：使用 `\textcolor{}` 命令，颜色与Web版一致
- 单色版：使用 `\underline{}/\textbf{}/\emph{}` 组合区分18类实体
- 索引生成：自动提取实体生成书末索引

**注释系统**：
- 三家注：脚注/尾注/边注三种模式可选
- 现代注释：支持LaTeX的 `\footnote{}` 和 `marginnote` 包

**紫色编号**：
- 使用 `\label{}` 和 `\ref{}` 实现段落编号
- 交叉引用：自动计算页码（见第X页[1.2.3]）

### 4.3 Pandoc转换配置

**Markdown → LaTeX 模板**：

```yaml
# pandoc-shiji.yaml
from: markdown+fenced_divs+pipe_tables
to: latex
template: templates/shiji-latex.template
variables:
  documentclass: ctexbook
  classoption:
    - UTF8
    - a4paper
    - twoside
  fontsize: 12pt
  mainfont: Noto Serif SC
  geometry:
    - top=2.5cm
    - bottom=2.5cm
    - left=3cm
    - right=2.5cm
  colorlinks: true
  # 自定义命令
  header-includes: |
    \usepackage{xcolor}
    \usepackage{soul}  % 下划线包
    \definecolor{personcolor}{RGB}{139,69,19}
    \definecolor{placecolor}{RGB}{184,134,11}
    \newcommand{\person}[1]{\textcolor{personcolor}{\underline{#1}}}
    \newcommand{\place}[1]{\textcolor{placecolor}{\dashuline{#1}}}
    % ... 18类实体定义
```

**转换命令**：

```bash
pandoc chapter_md/007_项羽本纪.tagged.md \
  -o output/007_项羽本纪.pdf \
  --defaults=pandoc-shiji.yaml \
  --pdf-engine=xelatex \
  --filter=filters/shiji-entity-filter.lua
```

### 4.4 Lua Filter（语义标注预处理）

**`filters/shiji-entity-filter.lua`**：

```lua
-- 将〖@人名〗转为LaTeX命令\person{人名}
function Span(elem)
  if elem.classes[1] == "person" then
    return pandoc.RawInline('latex', '\\person{' .. elem.content .. '}')
  elseif elem.classes[1] == "place" then
    return pandoc.RawInline('latex', '\\place{' .. elem.content .. '}')
  end
  -- ... 其他类型
end
```

---

## 五、电子书生成（EPUB/MOBI）

### 5.1 EPUB 3.0规范

**优势**：
- 语义HTML + CSS，与Web阅读器技术栈一致
- 支持超链接、实体索引、目录导航
- 设备兼容性好（Apple Books/Kobo/Nook/通用阅读器）

**转换流程**：

```bash
# 使用Pandoc生成EPUB
pandoc chapter_md/*.tagged.md \
  -o output/史记.epub \
  --metadata title="史记" \
  --metadata author="司马迁" \
  --metadata lang="zh-CN" \
  --css=epub-styles/shiji-epub.css \
  --epub-cover-image=resources/cover.jpg \
  --epub-metadata=epub-metadata.xml \
  --filter=filters/shiji-epub-filter.lua \
  --toc-depth=3
```

**`shiji-epub.css`**：
- 基于 `docs/css/shiji-styles.css`（Web版样式）
- 适配阅读器限制（字体回退、固定布局→流式布局）
- 实体颜色优化（适应黑夜模式）

### 5.2 MOBI（Kindle专用）

**转换流程**：

```bash
# 先生成EPUB，再转MOBI
pandoc ... -o output/史记.epub
kindlegen output/史记.epub -o 史记.mobi

# 或使用Calibre转换
ebook-convert output/史记.epub output/史记.mobi \
  --pretty-print \
  --no-inline-toc \
  --enable-heuristics
```

**Kindle限制与优化**：
- Kindle不完全支持CSS3 → 使用HTML `<font color="">` 作为回退
- 紫色编号 → 转为普通段落编号
- 超链接保留（Kindle支持内部跳转）

### 5.3 语义导航

**EPUB目录结构**（NCX + Nav）：

```
史记（130章）
├─ 本纪（12章）
│  ├─ 001 五帝本纪
│  │  ├─ [1] 黄帝纪
│  │  ├─ [2] 颛顼纪
│  │  └─ [3] 帝喾纪
│  └─ 007 项羽本纪
│     ├─ [1] 早年
│     └─ [2] 鸿门宴
├─ 世家（30章）
└─ 列传（70章）
```

**实体索引（EPUB Landmarks）**：
- 人名索引：所有人物按拼音排序，链接到首次出现
- 地名索引：所有地点，链接到描述详细的段落
- 时间索引：编年表，链接到对应纪年的章节

---

## 六、多版本导出策略

### 6.1 版本矩阵

| 版本类型 | 格式 | 特点 | 适用读者 |
|---------|------|------|---------|
| **纯文本版** | TXT/MD | 无标注，只有句读标点 | 最大兼容性，盲人阅读器 |
| **简标版** | PDF/EPUB | 仅人名/地名/时间着色 | 初学者，降低认知负担 |
| **全标版** | PDF/EPUB | 18类实体 + 4类动词 | 深度研究，完整语义信息 |
| **对照版** | PDF | 左页原文（繁体无标点）+ 右页标注版 | 对照学习，版本研究 |
| **注释版** | PDF/EPUB | 全标版 + 三家注侧栏 | 学术研究，古注参考 |
| **黑白印刷版** | PDF | 单色方案（下划线/字重区分） | 降低印刷成本 |

### 6.2 批量生成脚本

**`scripts/generate_all_formats.py`**：

```python
#!/usr/bin/env python3
"""
批量生成所有格式版本

用法：
  python scripts/generate_all_formats.py --version all
  python scripts/generate_all_formats.py --version full-epub
  python scripts/generate_all_formats.py --chapter 007 --version luatex-pdf
"""

VERSIONS = {
    'plaintext': {
        'format': 'txt',
        'preprocess': strip_all_tags,
        'engine': None
    },
    'simple-epub': {
        'format': 'epub',
        'preprocess': keep_basic_tags,  # 仅保留@/=/%
        'engine': 'pandoc',
        'css': 'epub-styles/simple.css'
    },
    'full-epub': {
        'format': 'epub',
        'preprocess': None,  # 保留所有标注
        'engine': 'pandoc',
        'css': 'epub-styles/full.css'
    },
    'luatex-pdf': {
        'format': 'pdf',
        'preprocess': convert_to_luatex,
        'engine': 'lualatex',
        'template': 'templates/shiji-luatex.template'
    },
    'modern-pdf': {
        'format': 'pdf',
        'preprocess': convert_to_pandoc_latex,
        'engine': 'pandoc+xelatex',
        'template': 'templates/shiji-modern.template'
    },
    'contrast-pdf': {
        'format': 'pdf',
        'preprocess': build_contrast_version,
        'engine': 'pandoc+xelatex',
        'layout': 'two-column'  # 左原文右标注
    }
}

def generate_version(chapter_file, version_name):
    config = VERSIONS[version_name]
    # 读取源文件
    content = read_file(chapter_file)
    # 预处理
    if config['preprocess']:
        content = config['preprocess'](content)
    # 调用引擎
    if config['engine'] == 'pandoc':
        run_pandoc(content, config)
    elif config['engine'] == 'lualatex':
        run_lualatex(content, config)
    # ...
```

---

## 七、质量检查与验证

### 7.1 排版质量Lint

**`scripts/lint_typeset.py`**：

```bash
python scripts/lint_typeset.py output/007_项羽本纪.pdf

检查项：
✓ PDF元数据完整（标题/作者/关键词）
✓ 字体嵌入正确（Noto Serif SC已嵌入）
✓ 目录书签层级正确（3级目录）
✓ 超链接有效（内部锚点/外部URL）
✓ 紫色编号连续性（无跳号/重复）
✗ 发现孤行（orphan）：第12页底部单行
⚠ 建议：调整段落间距或手动分页
```

### 7.2 语义完整性检查

**验证标注未丢失**：

```bash
# 对比源文件和PDF提取文本
python scripts/verify_semantic_integrity.py \
  chapter_md/007_项羽本纪.tagged.md \
  output/007_项羽本纪.pdf

检查：
✓ 实体数量匹配（源文件1823个 → PDF渲染1823个）
✓ 紫色编号完整（[1.1]-[1.89]无遗漏）
✓ 区块标记正确（太史公曰/赞渲染正确）
```

### 7.3 阅读器兼容性测试

**EPUB验证**：

```bash
# EPUBCheck官方验证工具
java -jar epubcheck.jar output/史记.epub

# Calibre格式转换测试
ebook-viewer output/史记.epub

# 真机测试清单
□ Kindle Paperwhite（MOBI）
□ Apple Books（EPUB）
□ Kobo Libra（EPUB）
□ Google Play Books（EPUB）
```

---

## 八、工具与脚本

### 8.1 核心脚本清单

**⚠️ 所有脚本均未开发，下表为规划设计**

| 脚本 | 功能 | 依赖 | 状态 |
|------|------|------|------|
| `scripts/generate_all_formats.py` | 批量生成所有格式 | Pandoc, LuaTeX | 🔴 未开发 |
| `scripts/convert_to_luatex.py` | 语义标注→LuaTeX源码 | - | 🔴 未开发 |
| `scripts/convert_to_pandoc_latex.py` | 语义标注→Pandoc LaTeX | - | 🔴 未开发 |
| `scripts/build_epub.py` | 生成EPUB（含索引/目录） | Pandoc | 🔴 未开发 |
| `scripts/lint_typeset.py` | PDF质量检查 | PyPDF2 | 🔴 未开发 |
| `scripts/verify_semantic_integrity.py` | 语义完整性验证 | pdfplumber | 🔴 未开发 |
| `filters/shiji-entity-filter.lua` | Pandoc Lua Filter（实体渲染） | Pandoc | 🔴 未开发 |
| `filters/shiji-epub-filter.lua` | EPUB专用Filter | Pandoc | 🔴 未开发 |

### 8.2 依赖安装

**LaTeX环境**：

```bash
# macOS
brew install --cask mactex-no-gui
tlmgr install luatexja luatexja-preset

# Ubuntu/Debian
sudo apt install texlive-full texlive-luatex texlive-lang-chinese

# LuaTeX-CN（古籍排版包）
git clone https://github.com/open-guji/luatex-cn.git
cd luatex-cn
# 按README安装
```

**Pandoc生态**：

```bash
# Pandoc 3.0+
brew install pandoc  # macOS
sudo apt install pandoc  # Linux

# KindleGen（MOBI转换）
wget https://archive.org/download/kindlegen/kindlegen_linux_2.6_i386_v2_9.tar.gz
tar xzf kindlegen*.tar.gz
sudo mv kindlegen /usr/local/bin/

# Calibre（备选EPUB→MOBI）
sudo apt install calibre
```

**Python依赖**：

```bash
pip install -r requirements-typeset.txt
# PyPDF2, pdfplumber, pypandoc, ebooklib
```

---

## 九、上游依赖与下游应用

### 9.1 上游依赖

| 上游技能 | 提供 | 排版用途 |
|---------|------|---------|
| SKILL_01 古籍校勘 | 定本文字、异体字处理 | 排版源文本 |
| SKILL_02a 章节切分 | 段落编号（Purple Numbers） | 紫色编号系统 |
| SKILL_02b 区块处理 | 太史公曰/赞/韵文标记 | 区块差异化排版 |
| SKILL_02c 三家注 | 集解/索隐/正义 | 注释排版（侧栏/脚注） |
| SKILL_03a 实体标注 | 18类实体Token | 实体着色方案 |
| SKILL_04f 动词标注 | 4类动词Token | 动词着色方案 |
| SKILL_09a 语法高亮辅助阅读 | Web版CSS配色方案 | 颜色映射到CMYK |

### 9.2 下游应用

| 应用场景 | 说明 |
|---------|------|
| **古籍出版** | 语义标注版《史记》纸质书，彩色印刷 + 紫色编号引用系统 |
| **教育教材** | 现代横排版，实体高亮辅助教学，配套电子书 |
| **学术研究** | 对照版（原文+标注），便于版本对比和引用 |
| **电子阅读** | EPUB/MOBI版本，便携学习，离线查询 |
| **按需印刷** | POD（Print on Demand），读者自选版本（全标/简标/黑白） |

### 9.3 与Web阅读器的协同

| 特性 | Web阅读器 | 电子书/印刷版 | 协同价值 |
|------|----------|--------------|---------|
| 紫色编号 | 可点击锚点 | 页边注/行内编号 | **统一引用坐标**，线上线下精确对应 |
| 实体着色 | RGB颜色 | CMYK印刷色 | 视觉一致性，降低认知切换成本 |
| 超链接 | 实体索引跳转 | 纸质版无超链接，电子书保留 | 电子书作为Web版的离线版 |
| 三家注 | 右栏面板 | 侧栏/脚注/尾注 | 排版形式不同，内容一致 |
| 更新频率 | 实时更新 | 版本固化 | Web版做实验性更新，电子书做稳定发布 |

---

## 十、未来扩展

### 10.1 智能排版优化

- **AI段落分页**：避免孤行/寡行，优化章节分页
- **动态字距调整**：根据内容密度自动调整字距，避免过松/过紧
- **语义感知分页**：重要段落（太史公曰/赞）不跨页

### 10.2 交互式PDF

- **PDF表单**：嵌入搜索框、实体过滤器
- **分层PDF**：可切换显示/隐藏实体着色层
- **注释层**：读者可在PDF中添加个人注释，导出为独立层

### 10.3 多语言版本

- **英译本排版**：《Records of the Grand Historian》语义标注版
- **对照版**：中英对照，左页中文右页英文，紫色编号对齐
- **注音版**：拼音标注层（针对海外学习者）

### 10.4 个性化定制

- **用户自选配色**：Web界面选择配色方案 → 生成个性化PDF/EPUB
- **章节定制**：只导出感兴趣的章节，组合为个人选集
- **标注密度**：简标版（3类）/中标版（8类）/全标版（18类）可选

---

## 十一、快速开始（规划）

**⚠️ 注意：以下命令为规划设计，脚本尚未实现**

### 未来的使用流程：生成项羽本纪的多个版本

```bash
# 1. 安装依赖（环境准备）
pip install -r requirements-typeset.txt
brew install pandoc mactex

# 2. 生成EPUB电子书（全标版）[🔴 未实现]
python scripts/generate_all_formats.py \
  --chapter 007 \
  --version full-epub \
  --output output/007_项羽本纪.epub

# 3. 生成现代PDF（横排，彩色）[🔴 未实现]
python scripts/generate_all_formats.py \
  --chapter 007 \
  --version modern-pdf \
  --output output/007_项羽本纪_现代版.pdf

# 4. 生成古籍PDF（竖排，LuaTeX）[🔴 未实现]
python scripts/generate_all_formats.py \
  --chapter 007 \
  --version luatex-pdf \
  --output output/007_项羽本纪_古籍版.pdf

# 5. 生成对照版PDF（左原文右标注）[🔴 未实现]
python scripts/generate_all_formats.py \
  --chapter 007 \
  --version contrast-pdf \
  --output output/007_项羽本纪_对照版.pdf

# 6. 批量生成所有章节的EPUB [🔴 未实现]
python scripts/generate_all_formats.py \
  --all-chapters \
  --version full-epub \
  --output output/史记全集.epub

# 7. 质量检查 [🔴 未实现]
python scripts/lint_typeset.py output/007_项羽本纪.epub
python scripts/verify_semantic_integrity.py \
  chapter_md/007_项羽本纪.tagged.md \
  output/007_项羽本纪_现代版.pdf
```

### 成功标准

- [ ] PDF/EPUB文件成功生成，无错误
- [ ] 实体着色正确（18类颜色/样式符合规范）
- [ ] 紫色编号完整且连续
- [ ] 目录/索引/超链接有效
- [ ] 通过 `lint_typeset.py` 所有检查
- [ ] 通过 `verify_semantic_integrity.py` 验证
- [ ] 在至少2个阅读器/设备上测试（EPUB）

---

## 十二、参考资源

### 古籍排版规范

- [LuaTeX-CN项目](https://github.com/open-guji/luatex-cn) - 古籍专业排版宏包
- [四库全书排版规范](https://zh.wikisource.org/wiki/四库全书) - 版心/行列标准
- 《中国古籍版本学》（李致忠） - 古籍版式术语

### 现代排版技术

- [Pandoc Manual](https://pandoc.org/MANUAL.html) - Pandoc完整文档
- [EPUB 3.3 Specification](https://www.w3.org/TR/epub-33/) - EPUB标准
- [LaTeX中文排版指南](https://github.com/CTeX-org/ctex-doc) - CTeX文档

### 项目文档

- [SKILL_09a 语法高亮辅助阅读](SKILL_09a_语法高亮辅助阅读.md) - Web版渲染规范
- [实体渲染规划 v5.0](../doc/spec/RENDER_实体规划.md) - 实体配色方案
- [动词渲染规则 v4.0](../doc/spec/RENDER_动词规则.md) - 动词标识方案
- [SKILL_02a 章节切分](SKILL_02a_章节切分.md) - 紫色编号系统

---

## 十三、实施路线图

**当前状态**：规划阶段（2026-04-01）

### 阶段1：基础架构（预计2-3周）

**目标**：实现最简单的EPUB导出

- [ ] 开发 `convert_to_pandoc_markdown.py`：〖TYPE〗→Pandoc Markdown（span标记）
- [ ] 创建基础CSS模板：`epub-styles/simple.css`（复用Web版配色）
- [ ] 实现 `build_epub.py`：单章EPUB生成
- [ ] 测试：在Apple Books/Calibre中验证

**里程碑**：生成007章《项羽本纪》的可读EPUB版本

### 阶段2：PDF现代横排（预计2-3周）

**目标**：Pandoc + XeLaTeX生成彩色PDF

- [ ] 开发 `convert_to_pandoc_latex.py`：生成LaTeX命令
- [ ] 创建LaTeX模板：`templates/shiji-modern.template`
- [ ] 实现Lua Filter：`filters/shiji-entity-filter.lua`（实体→LaTeX宏）
- [ ] 开发 `lint_typeset.py`：PDF质量检查基础版
- [ ] 测试：紫色编号/实体着色/区块样式

**里程碑**：生成007章的彩色PDF，通过质量检查

### 阶段3：批量生成与多版本（预计1-2周）

**目标**：支持全部130章和版本矩阵

- [ ] 开发 `generate_all_formats.py`：批量生成框架
- [ ] 实现版本配置：plaintext/simple/full版本
- [ ] 开发 `verify_semantic_integrity.py`：语义完整性验证
- [ ] 测试：批量生成全130章EPUB
- [ ] 文档：编写使用手册

**里程碑**：一键生成《史记》全集EPUB（全标版）

### 阶段4：古籍排版（预计3-4周）

**目标**：LuaTeX-CN竖排PDF

- [ ] 研究LuaTeX-CN宏包使用
- [ ] 开发 `convert_to_luatex.py`：生成LuaTeX源码
- [ ] 设计竖排实体着色方案（CMYK配色）
- [ ] 实现三家注侧栏排版
- [ ] 创建四库全书风格模板：`templates/siku.template`
- [ ] 测试：竖排版本对比测试

**里程碑**：生成007章的竖排PDF，模拟古籍版式

### 阶段5：高级功能（预计2-3周）

**目标**：对照版、注释版、交互式PDF

- [ ] 实现对照版排版：左原文右标注
- [ ] 实现注释版：三家注脚注/边注
- [ ] 实现单色印刷方案：下划线/字重区分
- [ ] 开发个性化配置：用户自选版本参数
- [ ] 测试：多版本并行生成

**里程碑**：支持6种版本类型的完整生成流水线

### 未来扩展（长期规划）

- 交互式PDF（嵌入搜索/分层显示）
- 多语言版本（中英对照）
- AI段落分页优化
- Web界面：可视化配置生成参数

---

## 十四、检查清单

### 排版前

- [ ] 确认源文件通过 `lint_purple_numbers.py` 检查（紫色编号完整）
- [ ] 确认源文件通过 `lint_text_integrity.py` 检查（无嵌套标注）
- [ ] 确认所需字体已安装（Noto Serif SC/思源宋体/楷体）
- [ ] 确认LaTeX/Pandoc环境正确配置

### 排版中

- [ ] 预处理脚本无错误输出
- [ ] 编译引擎无fatal error（warning可接受）
- [ ] 生成文件大小合理（PDF 5-20MB/章，EPUB 2-10MB/章）

### 排版后

- [ ] 运行 `lint_typeset.py` 质量检查
- [ ] 运行 `verify_semantic_integrity.py` 语义完整性验证
- [ ] 人工抽查10%内容（实体着色、紫色编号、区块样式）
- [ ] 电子书在至少2个阅读器上测试
- [ ] 检查元数据（标题/作者/关键词/语言）
- [ ] 检查目录/索引链接有效性

### 发布前

- [ ] 准备版本说明文档（标注版本、配色方案、使用说明）
- [ ] 生成预览图（封面、内页示例）
- [ ] 打包发布（PDF/EPUB/MOBI + README）
- [ ] 更新CHANGELOG
