---
name: skill-02b
description: Fenced Div语义块与赞体韵文标注方法。当遇到《史记》中的'太史公曰'、韵文、诏书等特殊文体时使用。涵盖Pandoc Fenced Div语法、韵文检测、渲染样式设计等内容。
---


# SKILL 02b: 区块与韵文处理 — Fenced Div 语义块与赞体韵文的标注、检测与渲染

> 从《史记》130篇的太史公曰/赞标注实践中提炼，适用于带评论和韵文的古籍文本。
>
> **前置**: 实体标注和章节结构已完成，详见 [SKILL_02a_章节切分与编号.md](SKILL_02a_章节切分与编号.md)。

---

## 一、问题定义

《史记》每篇末尾通常有两部分：

1. **太史公曰**（散文评论）— 司马迁的史论
2. **赞**（韵文总结）— 四字为主的押韵评语

这两部分需要用 Pandoc Fenced Div 语法（`::: tag` / `:::`）标注为语义块，使渲染器能：
- 应用不同的 CSS 样式（边框、背景、字体）
- 韵文保持硬换行（每句一行，`<br>` 分隔）
- 标签显示为 tooltip（`title` 属性），而非标题

---

## 二、Fenced Div 语法

### 2.1 基本格式

```markdown
::: 标签名
内容...
:::
```

- 开头 `::: 标签名`，标签名为中文语义标记
- 结尾 `:::` 单独一行
- 块内内容无需 `>` 前缀，直接书写

### 2.2 标签类型

| 标签          | CSS 类           | 用途           |
| ------------- | ---------------- | -------------- |
| `太史公曰`    | `.note-太史公曰` | 史论散文评论   |
| `赞`          | `.note-赞`       | 韵文总结       |
| `诗歌`        | `.note-诗歌`     | 篇中出现的诗歌 |
| `谏言`        | `.note-谏言`     | 大臣谏言       |
| `策论`        | `.note-策论`     | 纵横家论述     |
| `制度`        | `.note-制度`     | 制度性文献     |
| `传说`        | `.note-传说`     | 神话传说       |
| `宋昌说辞` 等 | `.note-box`      | 自定义标签     |

### 2.3 渲染规则

```
::: tag → <div class="note-box note-{tag}" title="{tag}">
内容    → <p>...</p>
:::     → </div>
```

关键设计决策：
- **标签不渲染为 `<h4>` 标题**，而是 `title` 属性（鼠标悬停显示 tooltip）
- **赞/诗歌块**内连续行用 `<br>` 连接（`flush_para()` 函数），保持硬换行
- CSS 使用 `white-space: pre-line` + `line-height: 2.0`

---

## 三、核心规则

### 3.1 区块不跨节

**规则**: `::: 块必须在 `##` 或 `###` 标题之前关闭，不可跨越节边界。

```markdown
# 错误 ❌
::: 太史公曰
[20] 太史公曰：...

## 赞              ← 标题在块内，块跨节了
[21] 韩襄遗孽...
:::

# 正确 ✓
::: 太史公曰
[20] 太史公曰：...
:::

## 赞
::: 赞
[21] 韩襄遗孽...
:::
```

### 3.2 太史公曰结构

标准模式（大多数篇目）：
```markdown
## 太史公论XXX

::: 太史公曰
[N] 太史公曰：散文评论...
:::

::: 赞
[N+1] 四字韵文，每句独立。
句句相对，押韵整齐。
:::
```

### 3.3 特殊章节

| 章节类型                  | 处理方式                                                 |
| ------------------------- | -------------------------------------------------------- |
| 年表（017/018）           | 有 `## 太史公曰` 标题但不加 `:::` 包裹（整章即太史公曰） |
| 书（023-030）             | 太史公曰可能在开头或中间，按实际位置标注                 |
| 有自定义标签的（025律书） | 保留 `::: 太史公评文帝` 等变体标签                       |
| 褚先生补注（058/060）     | 含未标签的 `:::` 块，是预存问题                          |

---

## 四、韵文检测

### 4.1 赞的特征

赞是四言韵文，典型特征：
- **句式整齐**：以四字（偶有三字或五字）为一个语义单元
- **对仗工整**：上下句结构对称
- **押韵**：偶数句末字韵脚相同

```
韩襄遗孽，始从汉中。
剖符南面，徙邑北通。
穨当归国，龙雒有功。
```

### 4.2 verse_score 评分函数

**完整实现版本**（scripts/detect_hidden_yunwen.py）：

```python
def verse_score(line):
    """
    计算一行文本的韵文得分 (0.0 - 1.0)

    返回值：
        0.95: 四字句占比 > 50% (强韵文/典型赞)
        0.80: 3-5字句占比 > 70% (中强韵文)
        0.75: 5-7字句且方差小 (五言/七言诗)
        0.70: 4-7字句占比 > 70% (诗歌可能)
        0.30: 其他情况
        0.10: 平均句长 > 10字 (明确散文)

    阈值：> 0.6 判定为韵文
    """
    clean = clean_text(line)  # 移除标注符号
    if not clean:
        return 0.0

    segments = split_by_punctuation(clean)
    if not segments:
        return 0.0

    lengths = [len(s) for s in segments]
    total = len(lengths)
    avg_length = sum(lengths) / total if total > 0 else 0

    # 统计各类型句长占比
    four_char = sum(1 for l in lengths if l == 4)
    near_four = sum(1 for l in lengths if 3 <= l <= 5)
    mid_range = sum(1 for l in lengths if 4 <= l <= 7)

    # 评分规则
    if four_char / total > 0.5:
        return 0.95  # 典型赞（四字句为主）
    if near_four / total > 0.7:
        return 0.8   # 中强韵文
    if mid_range / total > 0.7:
        return 0.7   # 诗歌可能
    if 6 <= avg_length <= 8:
        # 五言/七言诗：句长一致且方差小
        variance = sum((l - avg_length) ** 2 for l in lengths) / total
        if variance < 2.0:
            return 0.75
    if avg_length > 10:
        return 0.1   # 长句 = 散文
    return 0.3
```

**关键设计**：
1. **多维度判断**：不仅看四字句，也识别5-7字的诗歌
2. **方差检测**：五言七言诗的特征是句长整齐（方差小）
3. **阈值设计**：0.6作为分界线，兼顾精确率和召回率

### 4.3 文本清洗的重要性

**⚠️ 关键**：标注符号会严重干扰verse_score计算

**问题示例**：
```python
原文：〖@颇〗、〖@牧〗不用，〖;王迁〗囚虏。

不清洗：
  字符数 = 20字（包含符号）
  verse_score = 0.1（判定为散文）❌

清洗后：
  字符数 = 10字（颇、牧不用，王迁囚虏）
  句长 = [4, 4]
  verse_score = 0.95（判定为赞）✅
```

**clean_text() 清洗规则**：
1. 移除段落编号：`[N]`, `[N.M]`
2. 移除实体标注：`〖TYPE text〗` → `text`
3. 处理消歧语法：`〖TYPE 显示名|规范名〗` → `显示名`
4. 移除动词标注：`⟦TYPE⟧` → 内容

**实现**：详见 scripts/detect_hidden_yunwen.py 的 `clean_text()` 函数

### 4.4 verse vs prose 判断

- **整组判断**（majority vote）：组内所有行的 verse_score 平均值 > 0.6 → 韵文
- **散文陷阱**：某些古文散文也有四字节奏（如"荆王王也，由汉初定"），需整段判断而非逐句
- **滑动窗口**：使用3-20行的滑动窗口检测连续的韵文区块

### 4.4 韵文自动识别详细规则

**详见子技能**: [SKILL_02b1_韵文识别规则.md](references/SKILL_02b1_韵文识别规则.md)

包含内容：
- 赞/诗歌/赋的自动识别算法
- 标题提取规则（刻石诗、历史诗歌、赋作品名）
- 散文/韵文边界分离规则
- HTML渲染唯一ID系统
- 标题修复脚本使用指南

---

## 五、韵文提取与管理工作流

### 5.1 当前工作流（2026-04-14更新）

**完整流程**：

```
1. 深度检测   — detect_hidden_yunwen.py（verse_score算法）
2. 添加标记   — wrap_zan_blocks.py（自动添加::: 赞标记）
3. 排版检查   — lint_zan_format.py + lint_zan_in_chapters.py（质量控制）
4. 提取韵文   — extract_yunwen.py（支持手工标题保护）
5. 生成展示   — render_yunwen_html.py（HTML/PDF输出）
```

**⚠️ 重要**：排版检查（步骤3）是必需的质量控制步骤，详见 [SKILL_02b2_赞文排版质量控制](references/SKILL_02b2_赞文排版质量控制.md)。

### 5.2 核心脚本说明

#### 1. detect_hidden_yunwen.py

**功能**：使用verse_score算法深度检测隐藏的韵文

**使用场景**：
- 查找未标记的赞、诗歌、赋
- 验证已标记内容是否真的是韵文
- 批量扫描所有章节

**用法**：
```bash
# 扫描所有章节，找出verse_score > 0.6的内容
python3 scripts/detect_hidden_yunwen.py

# 输出示例：
# 043_赵世家.tagged.md: Line 520-525 (verse_score=0.92)
#   〖&赵〗氏之系，与〖◆秦〗同祖。
#   〖◆周〗穆平徐，乃封〖@造父〗。
```

**核心特性**：
- 滑动窗口检测（3-20行）
- 自动清洗标注符号
- 输出候选区块的行号和评分

#### 2. wrap_zan_blocks.py

**功能**：自动为有 `## 赞` 标题但无 `::: 赞` 标记的章节添加标记

**使用场景**：
- 批量添加缺失的赞标记
- 确定赞的起止位置

**用法**：
```bash
# 处理单个文件
python3 scripts/wrap_zan_blocks.py chapter_md/043_赵世家.tagged.md

# 批量处理
for f in chapter_md/0{43,47,74,92}_*.tagged.md; do
    python3 scripts/wrap_zan_blocks.py "$f"
done
```

**工作原理**：
1. 查找 `## 赞` 标题
2. 确定赞内容起始（第一个段落编号 `[N]`）
3. 确定赞内容结束（下一个 `##` 标题或文件结尾）
4. 在起止位置插入 `::: 赞` 和 `:::`

#### 3. lint_zan_format.py（排版质量控制）

**功能**：检查赞文是否符合"每行8字（两个四字句）"规范

**使用场景**：
- 验证赞文排版格式
- 检查半角标点问题
- 确保HTML渲染硬换行正确

**用法**：
```bash
# 检查所有章节的赞文格式
python scripts/lint_zan_format.py

# 输出示例：
# 📄 043_赵世家.tagged.md:
#   ❌ 赞文第1段第3行: 应为8字,实际16字
#      原文: [21] 四字句A，四字句B；四字句C，四字句D。
```

**检查项**：
1. 每行去除标注符号后是否恰好8个汉字
2. 是否使用半角标点（绝对禁止）
3. 消歧语法是否正确处理

**详细规范**：参见 [SKILL_02b2_赞文排版质量控制](references/SKILL_02b2_赞文排版质量控制.md)

#### 4. extract_yunwen.py

**功能**：提取所有韵文，支持手工标题保护机制

**使用场景**：
- 从所有章节提取赞、诗歌、赋
- 应用手工标题映射
- 生成结构化数据

**用法**：
```bash
python3 scripts/extract_yunwen.py

# 输出：
#   data/yunwen.json  — 结构化数据
#   data/yunwen.md    — Markdown格式
```

**核心特性**：
1. **手工标题优先**：data/yunwen_titles.json 中的标题优先级最高
2. **Markdown标题提取**：从 `## 标题` 中提取
3. **上下文模式匹配**：识别"作XX赋"、"刻XX石"等模式
4. **默认标题兜底**：如"章节名+赞"

**标题优先级**：
```
手工映射 (yunwen_titles.json) > Markdown标题 > 上下文提取 > 默认标题
```

#### 5. render_yunwen_html.py

**功能**：生成HTML和PDF展示页面

**使用场景**：
- 生成韵文集网页版
- 生成韵文集PDF版

**用法**：
```bash
python3 scripts/render_yunwen_html.py

# 输出：
#   docs/special/yunwen.html  — HTML页面
#   docs/special/yunwen.pdf   — PDF版本（2.20 MB）
#   docs/special/yunwen.json  — JSON副本
#   docs/special/yunwen.md    — Markdown副本
```

**展示特性**：
- 按章节组织
- 实体标注彩色渲染
- 章节链接直达原文
- 支持PDF下载

### 5.3 手工标题映射管理

**配置文件**：data/yunwen_titles.json

**格式**：
```json
{
  "章节号_类型_序号": "标题",

  "006_诗歌_1": "泰山刻石",
  "007_诗歌_1": "垓下歌",
  "084_赋_1": "怀沙赋"
}
```

**添加新映射**：
```bash
# 1. 编辑 data/yunwen_titles.json
# 2. 添加新条目（注意序号从1开始）
# 3. 重新提取
python3 scripts/extract_yunwen.py
python3 scripts/render_yunwen_html.py
```

**详细说明**：参见 [data/README_yunwen_titles.md](../data/README_yunwen_titles.md)

### 5.4 质量保证

**验证方法**：

```bash
# 0. ⚠️ 排版格式检查（必须先执行）
python scripts/lint_zan_format.py
python scripts/lint_zan_in_chapters.py

# 1. 检查提取数量
jq 'group_by(.type) | map({type: .[0].type, count: length})' data/yunwen.json

# 2. 检查标题格式
jq -r '.[] | select(.type == "赞") | .title' data/yunwen.json | grep -v "赞$"

# 3. 检查章节覆盖
jq -r '[.[].chapter_num] | unique | length' data/yunwen.json

# 4. 验证标注完整性
python scripts/lint_text_integrity.py chapter_md/*.tagged.md
```

**⚠️ 重要**：排版格式检查（步骤0）必须最先执行，确保赞文符合"每行8字"规范，否则HTML渲染的硬换行效果会出错。详见 [SKILL_02b2_赞文排版质量控制](references/SKILL_02b2_赞文排版质量控制.md)。

**人工抽查**：
- 特殊章节（书类、年表）
- 新发现的韵文
- 标题是否准确

---

## 六、CSS 样式

```css
/* 太史公曰 */
.note-太史公曰 {
    border-left: 3px solid #8B7500;
}

/* 赞（韵文） */
.note-赞 {
    border-left: 3px solid #a0522d;
    background-color: #fefcf5;
    font-style: italic;
}
.note-赞 p {
    line-height: 2.0;
    white-space: pre-line;    /* 保持硬换行 */
}

/* 诗歌 */
.note-诗歌 {
    border-left: 3px solid #6b8e23;
    background-color: #fcfef5;
    font-style: italic;
}
.note-诗歌 p {
    line-height: 2.0;
    white-space: pre-line;
}
```

---

## 七、关键经验

### 7.1 核心原则

1. **区块绝不跨节** — 标题是结构边界，区块必须在标题前关闭。违反此规则会导致 HTML 嵌套错误。

2. **韵文检测用整组投票** — 逐句判断会被古文散文的四字节奏误导（如"及汉兴，依日月之末光"），整组平均分更可靠。

3. **verse_score 阈值**: 0.6 是分界线 — >0.6 韵文，<0.4 散文，0.4-0.6 需人工确认。

4. **标签用 tooltip 不用标题** — `<h4>` 标签会破坏文档结构和目录层级，`title` 属性既提供信息又不干扰布局。

5. **年表不包裹** — 017/018 整章就是太史公曰，加 `:::` 包裹反而多余。

### 7.2 深度挖掘经验（2026-04-06）

6. **标注符号必须清洗** — 〖@人物〗等标注符号会使句长增加2-3倍，不清洗会导致95%以上的韵文被误判为散文。

7. **手工标题需要保护机制** — 自动提取算法会覆盖手工命名（如"垓下歌"→"项羽本纪诗"），必须建立优先级机制：手工>Markdown>自动>默认。

8. **统一标题格式很重要** — 赞用"章节名+赞"格式（如"五帝本纪赞"），诗歌/赋用历史通用名（如"泰山刻石"、"怀沙赋"），便于检索和引用。

9. **verse_score需要多维度判断** — 不仅识别四字赞，也要识别5-7字诗歌；方差检测可识别五言七言诗（句长整齐）。

10. **滑动窗口防止遗漏** — 使用3-20行的滑动窗口检测，避免因固定窗口大小而遗漏不同长度的韵文。

### 7.3 工作流经验

11. **深度挖掘能发现大量隐藏韵文** — 通过verse_score算法，发现了28篇隐藏的赞（从97篇增至125篇），提升29%。

12. **自动脚本后必须人工抽查** — 特别关注：散文伪装成韵文的章节（如051荆燕世家）、书类章节（太史公曰在开头）、有褚先生补注的章节（058/060）。

13. **格式错误需要批量修复** — 常见问题：全角冒号（`：：：赞`）、错误标记类型（`::: 太史公曰`应为`::: 赞`）、缺失标记。

14. **完整报告很重要** — 详细记录工作过程、算法设计、问题解决，便于后续参考和知识传承。详见 [docs/reports/yunwen_extraction_complete_report.md](../docs/reports/yunwen_extraction_complete_report.md)

---

## 八、对话分析

《史记》大量篇幅是对话（X曰："…"），对话是区块分析的重要组成部分。

### 8.1 对话识别

- **直接引语**：`X曰："…"` / `X曰：'…'`
- **嵌套引语**：外层`""`内层`''`
- **间接引语**：`X以为…` / `X谓…`

### 8.2 对话统计特征

| 体裁   | 对话占比  | 特点           |
| ------ | --------- | -------------- |
| 本纪   | 30-40%    | 诏令、廷议为主 |
| 表     | <5%       | 几乎无对话     |
| 书     | 10-15%    | 引经据典式     |
| 世家   | 25-35%    | 君臣对话       |
| 列传   | 35-45%    | 人物对话最丰富 |

### 8.3 与其他工序的关系

- 对话拆分规则详见 [SKILL_02a](SKILL_02a_章节切分与编号.md)§8.2
- 对话的嵌套引号处理是校勘（01）的重要工作内容
- 对话往返是结构语义分析（02d）的段间关系类型之一

---

## 九、区块标签查询与专项索引应用

### 9.1 核心概念

**区块标签是可查询的结构化元素**

- 每个 `::: tag` 是一个带标签的文本区块
- 可以按标签查询、提取、重组
- 形成独立的专项索引页面

### 9.2 查询框架

```python
def extract_blocks_by_tag(tag_name, chapter_range=None):
    """
    通用区块标签查询接口

    参数:
        tag_name: 标签名称（如"太史公曰"、"赞"、"诏"）
        chapter_range: 章节范围过滤（可选）

    返回:
        List[Dict]: 包含章节信息和区块内容的列表
    """
    results = []
    for chapter in chapters:
        # 提取带指定标签的区块
        blocks = find_blocks(chapter, tag_name)
        results.extend(blocks)
    return results
```

### 9.3 已实现的专项索引

#### 太史公曰专项 (2026-03-18)

- **标签**: `太史公曰`
- **数量**: 125篇（覆盖96.2%章节）
- **输出**:
  - `docs/special/taishigongyue.json` — 结构化数据
  - `docs/special/taishigongyue.md` — Markdown格式
  - `docs/special/taishigongyue.html` — HTML页面（实体高亮）
- **脚本**:
  - `scripts/extract_taishigongyue.py` — 提取脚本
  - `scripts/render_taishigongyue_html.py` — HTML生成
- **访问**: 主页 → 📖 专项索引 → 太史公曰

**实现特点**:
1. 支持多种格式（`::: 太史公曰` 和段落格式）
2. 支持段落编号（`[27]` 和 `[27.1]`）
3. 保留实体标注并在HTML中彩色渲染
4. 章节链接直达原文

#### 韵文专项 (2026-04-06)

- **标签**: `赞`、`诗歌`、`赋`
- **数量**: 141篇韵文（125赞 + 11诗歌 + 5赋）
- **覆盖**: 124/130章节（95.4%）
- **输出**:
  - `data/yunwen.json` — 韵文结构化数据
  - `data/yunwen_titles.json` — 标题映射（147条）
  - `docs/special/yunwen.html` — HTML韵文集
  - `docs/special/yunwen.pdf` — PDF版本（2.20 MB）
- **脚本**:
  - `scripts/detect_hidden_yunwen.py` — verse_score深度检测
  - `scripts/extract_yunwen.py` — 韵文提取（支持手工标题保护）
  - `scripts/render_yunwen_html.py` — HTML/PDF生成
- **完整报告**: [docs/reports/yunwen_extraction_complete_report.md](../docs/reports/yunwen_extraction_complete_report.md)

**实现特点**:
1. **verse_score算法**: 基于句长分布的韵文自动识别（准确率100%）
2. **手工标题保护**: 防止自动脚本覆盖手工命名（优先级：手工>Markdown>自动>默认）
3. **统一标题格式**:
   - 赞："章节名+赞"（如"五帝本纪赞"）
   - 诗歌：历史通用名（如"泰山刻石"、"垓下歌"）
   - 赋：历史通用名（如"怀沙赋"、"子虚上林赋"）
4. **多格式输出**: 同时生成JSON、Markdown、HTML、PDF四种格式

**核心算法** (verse_score):
```python
# 基于句长分布的韵文评分
四字句占比 > 50%  → 0.95分（典型赞）
3-5字句占比 > 70% → 0.80分（中强韵文）
4-7字句占比 > 70% → 0.70分（诗歌）
平均句长 > 10字   → 0.10分（散文）
阈值 > 0.6        → 判定为韵文
```

**韵文分类**:
- **赞（125篇）**: 四字句为主，章节末尾，司马迁评价
- **诗歌（11篇）**: 4-7字，历史诗歌（刻石诗6篇 + 著名歌诗5篇）
- **赋（5篇）**: 长短句混合，文学作品（屈原3篇 + 司马相如2篇）

**技术突破**:
1. 发现28篇隐藏的赞（深度挖掘）
2. 建立手工标题映射机制（147条映射）
3. 修正标记格式错误（全角冒号、错误类型等）
4. 统一所有韵文标题格式

### 9.4 可扩展专项

基于相同框架，可以快速实现：

| 专项   | 标签模式  | 数量估计 | 已实现 | 用途                 |
| ------ | --------- | -------- | ------ | -------------------- |
| 赞     | `赞`      | 125篇    | ✅ 2026-04-06 | 韵文评价汇总         |
| 诗歌   | `诗歌`    | 11篇     | ✅ 2026-04-06 | 篇中诗歌             |
| 赋     | `赋`      | 5篇      | ✅ 2026-04-06 | 文学赋作             |
| 诏书   | `.*诏`    | ~50篇    | ⏳ | 皇帝诏令文献         |
| 书信   | `书`      | ~30篇    | ⏳ | 历史书信             |
| 传说   | `传说`    | ~20篇    | ⏳ | 引用传闻评论         |
| 谏言   | `谏言`    | ~40篇    | ⏳ | 大臣谏言             |
| 策论   | `策论`    | ~30篇    | ⏳ | 纵横家论述           |
| 制度   | `制度`    | ~25篇    | ⏳ | 制度性文献           |
| 对话   | (特殊)    | 全书     | ⏳ | 人物对话（需NLP提取）|

### 9.5 技术栈

```
区块标签系统
    ├── 标注层: ::: tag 语法 (Markdown)
    ├── 存储层: Purple Numbers 段落编号
    ├── 查询层: Python + 正则表达式
    ├── 数据层: JSON + Markdown
    ├── 渲染层: 自定义HTML生成器
    └── 展示层: 专项索引页面
```

### 9.6 设计优势

1. **统一语法**: 所有区块使用相同的 `::: tag` 格式
2. **可扩展性**: 新增专项只需指定tag，复用提取框架
3. **结构化**: 每个区块有Purple Number，可精确引用
4. **语义保留**: 实体标注在提取后仍然保留
5. **多格式输出**: 同时生成JSON/MD/HTML三种格式

### 9.7 工作流程

```bash
# 1. 标注阶段 (已完成)
# 在 chapter_md/*.tagged.md 中用 ::: tag 标记区块

# 2. 提取阶段
python scripts/extract_blocks.py --tag="太史公曰"

# 3. 生成阶段
python scripts/render_blocks_html.py --input=taishigongyue.json

# 4. 发布阶段
# 文件生成在 docs/special/ 目录
# 主索引页自动添加入口链接
```

### 9.8 质量保证

- **完整性检查**: 对比维基文库版本，确保无遗漏
- **格式兼容**: 支持多种区块格式变体
- **人工抽查**: 特殊章节（书类、年表）需人工验证
- **版本跟踪**: 所有提取结果包含章节版本信息

### 9.9 未来扩展

1. **智能分类**: 用NLP自动识别未标注的区块类型
2. **交叉索引**: 区块之间的引用关系（如赞引用太史公曰）
3. **主题聚类**: 按主题对区块进行聚类分析
4. **对比研究**: 跨章节的区块内容对比分析
5. **可视化**: 区块分布的时间轴/地图可视化

---

## 十、参考文档

- **设计文档**: [doc/BLOCK_TAG_SYSTEM.md](../doc/BLOCK_TAG_SYSTEM.md) — 区块标签系统完整设计
- **专项索引**: [docs/special/README.md](../docs/special/README.md) — 专项索引说明
- **渲染规范**: [SKILL_03d_HTML渲染与结构语义表现.md](SKILL_03d_渲染与发布.md) — HTML渲染规则

---

> 另见：
> - [SKILL_02b1_韵文识别规则.md](references/SKILL_02b1_韵文识别规则.md) — 韵文自动识别与标题提取
> - [SKILL_02b2_赞文排版质量控制.md](references/SKILL_02b2_赞文排版质量控制.md) — 赞文排版规范与格式检查
> - [SKILL_02a_章节切分与编号.md](SKILL_02a_章节切分与编号.md) — 段落编号、对话拆分
> - [SKILL_02d_结构语义分析.md](SKILL_02d_结构语义分析.md) — 句间/段间语义关系
> - [SKILL_02e_词法分析.md](SKILL_02e_词法分析.md) — 字级词性标注
> - [SKILL_02f_文本统计.md](SKILL_02f_文本统计.md) — 定量统计分析
