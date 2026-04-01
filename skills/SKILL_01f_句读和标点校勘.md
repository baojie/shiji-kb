---
name: skill-01f
title: 句读和标点校勘
description: 古籍断句与标点符号使用规范。包括无标点古籍的AI自动断句与质量控制、已标点版本的标点反思、标点符号规范约定、以及文本完整性检查中的标点处理规则。
version: 2.0
last_updated: 2026-04-02
---

# SKILL 01f: 句读和标点校勘

> **核心理念**：标点是文本理解的第一道工序。准确的句读是一切语义分析的基础。

---

## 一、快速开始

### 何时使用此Skill

- **场景1**：接收到无标点的古籍原文，需要进行自动断句和标点
- **场景2**：已有标点的版本存在明显句读错误，需要系统性反思
- **场景3**：多版本对照时发现标点差异，需要确定最佳方案
- **场景4**：验证标注完整性时，需要理解标点符号的处理规则

### 核心步骤（句读工序位置）

```
【校勘管线】
① 句读与标点 (SKILL_01f)        ← 最前置工序，建立文本骨架
   ↓
② 多版本互校 (SKILL_01b)        ← 确定定本
   ↓
③ 表格校勘 (SKILL_01c)          ← 特殊结构校勘
   ↓
④ 正音与拼音 (SKILL_01d)        ← 标注读音
   ↓
⑤ 繁简体处理 (SKILL_01e)        ← 繁简转换
   ↓
⑥ 结构化标注 (SKILL_02*)        ← 章节切分、区块、三家注等
   ↓
⑦ 实体标注 (SKILL_03*)          ← 人名、地名、官职、书名等
   ↓
⑧ 标注完整性维护 (SKILL_01a)    ← 验证所有标注未篡改原文
```

**为何句读在最前面**：
- 句读错误会导致语义切分错误，影响所有后续工序
- 标点是文本的"骨架"，骨架不对，血肉无从依附
- 句读完成后，才能进行多版本对照（不同版本的句读可能不同）

### 成功标准

- [ ] **断句准确率**：AI断句后人工校对，错误率 <5%（每千字<50处错误）
- [ ] **标点规范性**：全部使用全角标点，引号嵌套正确（" " → ' '）
- [ ] **换行符规范**：使用LF（Unix格式），无CRLF
- [ ] **韵文格式规范**：每句一行，保持韵律
- [ ] **语义完整性**：句子边界与语义边界一致，无误断、误连
- [ ] **多版本一致性**：关键句读与权威版本（中华书局等）一致
- [ ] **完整性验证通过**：lint_text_integrity.py 检查通过

---

## 二、标点符号规范

### 2.1 基本原则

**古籍标点三原则**（参考《标点符号用法》GB/T 15834-2011）：

1. **全角优先**：古籍整理中，所有标点符号必须使用全角字符
2. **语义优先**：标点服从语义，不拘泥于现代语法
3. **从俗从简**：常用标点优先，避免过度使用冷僻符号

### 2.2 换行符规范

**本项目统一使用 LF（Unix风格）换行符**：

| 规范 | 说明 | 字符编码 |
|-----|------|---------|
| **使用** | LF（\n） | 0x0a |
| **禁止** | CRLF（\r\n） | 0x0d 0x0a |

**配置方法**：
```json
// .vscode/settings.json
{
  "files.eol": "\n"
}
```

```bash
# Git配置
git config --global core.autocrlf input
```

**详细说明**：参见 [references/SKILL_01f_background.md - 换行符配置详解](./references/SKILL_01f_background.md#换行符配置详解)

### 2.3 标点符号对照表

| 类型 | 符号 | Unicode | 用法 | 禁止使用 |
|-----|------|---------|------|---------|
| **句号** | 。 | U+3002 | 陈述句结尾 | ❌ 半角. |
| **逗号** | ，| U+FF0C | 句内停顿 | ❌ 半角, |
| **顿号** | 、 | U+3001 | 并列词语间 | ❌ 半角, |
| **分号** | ；| U+FF1B | 复句内并列分句间 | ❌ 半角; |
| **冒号** | ：| U+FF1A | 提示下文、总结上文 | ❌ 半角: |
| **问号** | ？| U+FF1F | 疑问句结尾 | ❌ 半角? |
| **叹号** | ！| U+FF01 | 感叹句结尾 | ❌ 半角! |
| **左双引号** | " | U+201C | 第一层引用 | ❌ 半角" 直角「 |
| **右双引号** | " | U+201D | 第一层引用结束 | ❌ 半角" 直角」 |
| **左单引号** | ' | U+2018 | 第二层引用（引用内引用） | ❌ 半角' 直角『 |
| **右单引号** | ' | U+2019 | 第二层引用结束 | ❌ 半角' 直角』 |
| **左书名号** | 《 | U+300A | 书名、篇名 | ❌ < |
| **右书名号** | 》 | U+300B | 书名、篇名结束 | ❌ > |
| **破折号** | —— | U+2014×2 | 注释、转折、延长 | ❌ -- - |
| **省略号** | …… | U+2026×2 | 文字省略 | ❌ ... 。。。 |

### 2.4 引号嵌套规则

**嵌套顺序**（从外到内）：

```
第一层：" "  （弯双引号）
第二层：' '  （弯单引号）
第三层：" "  （重复第一层）
```

**示例**：

```
太史公曰："孔子称'《尚书》言"夏礼吾能言之"，而不能徵'，信矣。"
         └─第1层────┘└第2层─┘└──第3层────────┘
```

**常见错误**：
- ❌ 使用半角引号 " '
- ❌ 使用直角引号 「」 『』（日文用法）
- ❌ 第一层用单引号 ''
- ❌ 忘记嵌套层次，全部用同一种引号

### 2.5 特殊情况处理

#### 对话与引文

**直接引语**（说话内容）：
```
高祖曰："大风起兮云飞扬，威加海内兮归故乡，安得猛士兮守四方！"
```

**间接引语**（转述）：
```
太史公称孔子言为人君难，为人臣不易。
```

**长对话分段**（推荐每段独立引号）：
```
高祖曰："吾以羽檄征天下兵，未有至者，今独邯郸先至，此可以助我乎？"

又曰："诸君知天下同苦秦久矣。今诸侯皆叛秦，项氏最强。"
```

**详细说明**：参见 [references/SKILL_01f_background.md - Q6](./references/SKILL_01f_background.md#q-长对话分段时引号应该如何使用)

#### 韵文与诗歌

**基本原则**：
1. **每句一行**：每个韵脚结束后换行
2. **句内不断**：句子内部不加句号（允许逗号）
3. **保持对仗**：对仗句式保持格式一致

**示例**：
```markdown
大风起兮云飞扬，
威加海内兮归故乡，
安得猛士兮守四方！
```

**详细说明**：参见 [references/SKILL_01f_background.md - Q5](./references/SKILL_01f_background.md#q-韵文应该如何断句和换行)

#### 并列结构

**顿号、逗号、分号层次**：

```
层次1（词语并列）：顿号
    天下之大，东、西、南、北四方

层次2（短句并列）：逗号
    为人君难，为人臣不易

层次3（分句并列）：分号
    高祖起于沛，项羽起于会稽；二人争天下，高祖胜，项羽败
```

#### 表格中的标点

**表格内标点规则**：
- 单元格内完整句子：使用句号
- 单元格内短语/词语：不加标点
- 多项并列：使用顿号或逗号

### 2.6 标点与标注的关系

**核心原则**：
- 标点符号**在标注符号外部**
- 标点标记语义边界，标注符号标记实体/结构

**正确示例**：
```
〖@高祖〗曰："天下初定，吾欲都〖=洛阳〗。"
```

**错误示例**：
```
❌ 〖@高祖曰：〗   # 标点在标注内部
❌ 〖@高祖〗曰："   # 引号开始在标注后（应该在"曰"后）
```

---

## 三、工作流程

### 场景A：无标点古籍自动断句

```bash
# 步骤1：准备无标点原文（archive/raw/无标点原文.txt）

# 步骤2：AI自动断句
python scripts/punctuation/auto_punctuate.py archive/raw/无标点原文.txt

# 步骤3：人工校对（VSCode + 对照参考版本）

# 步骤4：质量验证
python scripts/punctuation/validate_punctuation.py curation_base/初稿_已标点.txt
```

**技术方案**：
- **推荐**：gj.cool API（https://gj.cool）- 准确率92-99%
- **备选**：本地模型（Qwen/GLM-4）- 准确率90-95%

**代码示例**：参见 [references/SKILL_01f_code_examples.md - gj.cool API调用](./references/SKILL_01f_code_examples.md#gjcool-api-调用)

### 场景B：已标点版本的反思

```bash
# 步骤1：提取现有标点模式
python scripts/punctuation/extract_pattern.py chapter_md/001_*.tagged.md

# 步骤2：对照多版本
python scripts/punctuation/compare_punctuation.py 001 --sources wiki,zhonghua

# 步骤3：AI反思建议
python scripts/punctuation/reflect_punctuation.py chapter_md/001_*.tagged.md

# 步骤4：人工决策与修正
```

**反思提示词模板**：参见 [references/SKILL_01f_code_examples.md - 反思提示词](./references/SKILL_01f_code_examples.md#反思提示词)

### 场景C：文本完整性检查中的标点处理

**标点处理规则**（在 lint_text_integrity.py 中）：

1. **原文无标点** → 标注文件的标点全部视为"结构性添加"
2. **标注文件去除标注符号后，标点保留**
3. **比对时，规范化映射消除全角/半角差异**
4. **引号差异**（"" vs 「」 vs 『』）通过规范化映射忽略

**详细说明**：参见本文档第六章"完整性检查中的标点处理"

---

## 四、工具与脚本

### 验证工具

- `scripts/lint_symbol_conflicts.py` - 符号冲突检测 ✅
  - 检查：半角标点、直角引号、标点在标注内、Markdown在标注内、嵌套标注、标注跨标点
  - 智能过滤：自动忽略紫色编号中的半角句号（如 [23.2.1]）、标注语法中的半角符号
  - 用法：`python scripts/lint_symbol_conflicts.py chapter_md/*.md`

### 修复工具

- `scripts/fix_halfwidth_quotes.py` - 半角引号修复（智能判断左右引号）✅
- `scripts/fix_misplaced_fullwidth_quotes.py` - 全角引号左右修正 ✅
- `scripts/fix_all_halfwidth_symbols.py` - 半角标点符号批量修复 ✅
- `scripts/fix_square_quotes.py` - 直角引号修复 ✅
- `scripts/fix_nested_annotations.py` - 嵌套标注修复 ✅

### 待开发工具

以下工具为规划中：

**自动断句**：
- `scripts/punctuation/auto_punctuate.py` - AI自动断句（gj.cool API）
- `scripts/punctuation/auto_punctuate_local.py` - 本地模型断句

**验证与检查**：
- `scripts/punctuation/lint_punctuation.py` - 标点规则检查
- `scripts/punctuation/validate_punctuation.py` - 标点语义验证

**对照与反思**：
- `scripts/punctuation/compare_punctuation.py` - 多版本标点对比
- `scripts/punctuation/reflect_punctuation.py` - AI标点反思

---

## 五、使用示例

### 示例：批量修复半角符号（完整流程）

```bash
# 第一步：检测问题
python scripts/lint_symbol_conflicts.py chapter_md/*.tagged.md

# 第二步：修复半角引号
python scripts/fix_halfwidth_quotes.py

# 第三步：修正全角引号左右
python scripts/fix_misplaced_fullwidth_quotes.py

# 第四步：修复其他半角标点
python scripts/fix_all_halfwidth_symbols.py

# 第五步：修复直角引号
python scripts/fix_square_quotes.py

# 第六步：修复嵌套标注
python scripts/fix_nested_annotations.py

# 第七步：验证修复结果
python scripts/lint_symbol_conflicts.py chapter_md/*.tagged.md

# 输出示例：
# 检查文件: 130 个
# 发现问题: 0 处  ✓
```

**修复脚本的智能特性**：

1. **智能判断左右引号**：根据上下文自动判断是左引号还是右引号
2. **智能保留合法符号**：紫色编号中的句号、数字小数点、时间格式冒号等
3. **Unicode精确处理**：使用显式Unicode码点避免编码问题
4. **智能展平嵌套**：根据前后缀规则展平嵌套标注

---

## 六、完整性检查中的标点处理

### 6.1 标点去除规则

在 lint_text_integrity.py 中，标点去除遵循以下规则：

**原文无标点的情况**（如《史记》原始文本）：
- 原文：`太史公曰余读史记至于孔子世家观其言`
- 标注文件：`〖@太史公〗曰：余读〖^史记〗至于〖^孔子世家〗，观其言。`
- 去除标注后：`太史公曰：余读史记至于孔子世家，观其言。`
- **比对规则**：标注文件去除标点后 == 原文

**原文有标点的情况**（如已标点的版本）：
- 原文：`太史公曰：余读《史记》至于《孔子世家》，观其言。`
- 标注文件：`〖@太史公〗曰：余读〖^史记〗至于〖^孔子世家〗，观其言。`
- 去除标注后：`太史公曰：余读史记至于孔子世家，观其言。`
- **比对规则**：标注文件去除标注（保留标点）== 原文（保留标点）

### 6.2 标点规范化映射

为消除全角/半角差异，使用规范化映射表：

| 原始符号 | 规范化为 | 说明 |
|---------|---------|------|
| `. , ; : ? !` | `。，；：？！` | 半角 → 全角 |
| `" " ' '` | `" " ' '` | 半角引号 → 全角引号 |
| `「」『』` | `" " ' '` | 直角引号 → 弯引号 |
| `< >` | `《》` | 半角书名号 → 全角 |

**代码示例**：参见 [references/SKILL_01f_code_examples.md - 标点规范化映射](./references/SKILL_01f_code_examples.md#标点规范化映射)

---

## 七、检查清单

### 执行前检查

- [ ] 确认原文是否有标点（影响后续处理流程）
- [ ] 准备参考版本（维基文库、中华书局等）
- [ ] 确认换行符统一为LF格式

### 执行中验证

- [ ] 句子长度合理（一般不超过50字）
- [ ] 引号成对且嵌套正确
- [ ] 韵文格式正确（每句一行）
- [ ] 对话引号使用正确
- [ ] 全部使用全角标点

### 执行后验证

- [ ] 运行 lint_symbol_conflicts.py 无错误
- [ ] 运行 lint_text_integrity.py 通过
- [ ] 对照参考版本，关键句读一致
- [ ] 人工抽查10-20个段落，无明显错误

---

## 八、FAQ

### Q1: 为什么句读工序在最前面？

**答案**：句读（标点）是文本结构化的基础，影响后续所有标注工序。标点错误会导致语义切分错误，影响人名、地名等实体标注的准确性。

**详细说明**：参见 [references/SKILL_01f_background.md - Q1](./references/SKILL_01f_background.md#q-为什么句读工序在最前面)

### Q2: 原文有标点时，是否还需要反思？

**答案**：需要。不同版本标点可能不同，需要对照至少2个版本并使用AI提示可疑位置。

**详细说明**：参见 [references/SKILL_01f_background.md - Q2](./references/SKILL_01f_background.md#q-原文有标点时是否还需要反思)

### Q3: gj.cool API 断句准确率如何？

**答案**：整体准确率96.3%（基于《史记》测试数据），句号识别98.1%，逗号94.7%。

**详细说明**：参见 [references/SKILL_01f_background.md - gj.cool准确率评估](./references/SKILL_01f_background.md#gjcool-api-准确率评估)

### Q4: 如何处理标点与标注符号的冲突？

**答案**：标点符号应在标注符号外部。例如：`〖@高祖〗曰："..."`

**正确示例**：
```
✓ 〖@高祖〗曰："天下初定。"
✓ 〖@张良〗、〖@韩信〗辅之。
```

**错误示例**：
```
❌ 〖@高祖曰：〗"天下初定。"
❌ 〖@张良、〗〖@韩信〗辅之。
```

### Q5: 韵文应该如何断句和换行？

**答案**：每句一行，句内不加句号，保持韵律。

**详细说明与示例**：参见 [references/SKILL_01f_background.md - Q5](./references/SKILL_01f_background.md#q-韵文应该如何断句和换行)

### Q6: Windows用户如何处理换行符问题？

**答案**：推荐使用LF格式，配置 `core.autocrlf=input`。现代Windows编辑器完全支持LF。

**详细说明**：参见 [references/SKILL_01f_background.md - Windows用户换行符处理](./references/SKILL_01f_background.md#windows用户如何处理换行符问题)

---

## 九、相关文档

### 关联Skill

- [SKILL_01a_标注完整性维护](./SKILL_01a_标注完整性维护.md) - 验证标注未篡改原文
- [SKILL_01b_多版本互校](./SKILL_01b_多版本互校.md) - 对照多版本确定定本
- [SKILL_01g_符号冲突检测与修复](./SKILL_01g_符号冲突检测与修复.md) - 半角/全角符号检测

### 拆分文档

- [references/SKILL_01f_code_examples.md](./references/SKILL_01f_code_examples.md) - 代码示例（gj.cool API、本地模型、质量检查等）
- [references/SKILL_01f_background.md](./references/SKILL_01f_background.md) - 背景信息与扩展FAQ（换行符配置、技术方案对比、学术资源等）

### 参考标准

- 《标点符号用法》（GB/T 15834-2011）
- 《古籍标点通则》（2009年修订）
- 中华书局点校本《史记》（2013年修订）

### 学术资源

参见 [references/SKILL_01f_background.md - 学术参考资源](./references/SKILL_01f_background.md#学术参考资源)
