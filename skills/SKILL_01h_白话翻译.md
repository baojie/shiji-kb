---
name: "SKILL_01h"
title: "白话翻译"
description: "史记章节按PN段落进行文言文到白话文的翻译规范"
---

# SKILL_01h: 白话翻译

## 快速开始

### 何时使用
- 为史记章节生成现代白话文翻译
- 按PN段落为单位进行翻译
- 确保翻译质量符合准确性、流畅性、简洁性标准

### 核心步骤
1. 读取章节 `.tagged.md` 文件，提取所有PN段落
2. 使用Task工具调用translation subagent，按PN顺序翻译
3. 保存翻译结果到 `doc/translation/NNN_章节名_白话.md`
4. 验证实体标注完整性

### 成功标准
- ✅ 所有PN段落完整翻译
- ✅ 实体标注（〖@〗〖=〗等）完整保留
- ✅ 译文准确、流畅、简洁
- ✅ 文件保存到正确目录

---

## Translation Agent提示词

```
任务：将以下文言文段落翻译为现代白话文

**原文**（PN [X]）：
[原文内容]

**翻译要求**：
1. **准确性**：忠实原文含义，不增删内容
2. **流畅性**：使用现代汉语表达，符合当代阅读习惯
3. **简洁性**：保持史记简练风格，避免冗长
4. **保留实体标注**：必须完整保留原文中的所有实体标注符号（18类）：
   - 人名：〖@人名〗
   - 地名：〖=地名〗
   - 官职：〖;官职〗
   - 时间：〖%时间〗
   - 氏族：〖&氏族〗
   - 邦国：〖◆邦国〗
   - 制度：〖^制度〗
   - 族群：〖~族群〗
   - 器物：〖•器物〗
   - 天文：〖!天文〗
   - 神话：〖?神话〗
   - 生物：〖+生物〗
   - 身份：〖#身份〗
   - 数量：〖$数量〗
   - 典籍：〖{典籍〗
   - 礼仪：〖:礼仪〗
   - 刑法：〖[刑法〗
   - 思想：〖_思想〗
   - 消歧：〖TYPE 显示名|规范名〗

5. **消歧语法（白话上下文）**：
   - **继承原文消歧**：原文 `.tagged.md` 中凡有 `|` 消歧的实体，白话译文必须保留 `|规范名` 部分
   - **surface 可随白话改写**：白话中实体的显示名可替换为更通用的形式（如文言"籍"→白话"项羽"），但规范名保持不变
     - 例：文言 `〖@籍|项籍〗` → 白话 `〖@项羽|项籍〗`（surface 改，规范不动）
     - 例：文言 `〖@阿父|齐桓公〗` → 白话 `〖@齐桓公|齐桓公〗`（surface 规范化）
   - **原文未消歧时不擅自添加**：若原文是 `〖@桓公〗`（无 `|`），白话保持 `〖@桓公〗`；只有原文已经做了消歧的，才继承
   - **渲染规则**：白话 HTML 渲染时应优先显示**规范名**（`|` 右侧），文言渲染保持显示**显示名**（`|` 左侧）——详见 `scripts/semantic_tags.py` 的白话渲染模式

6. **段落标题**：为每个PN段落提炼一个简短标题（4-8字），概括段落主要内容；若难提炼可留空（但 `## [X]` 头必须有）。JSON 生成器已容错（027 等仅 `## [N]` 无标题章节正常）。

7. **空父级 PN 必须占位**：源 `[N]` 无内容但有子段 `[N.1]...` 时，白话仍必须写 `## [N] 本段` + "（本段内容在以下子段中。）"。否则前端翻译框无定位锚点。

8. **严禁 `---` 行**：JSON 解析器按首个 `---` 切分文档；译文中**绝对不要**出现独立 `---` 行（历史教训：003 因此丢失 [34][35]）。

9. **不要保留 `[0]`**：源中 `[0]` 是章节标题，HTML 页面已有 `<h1>`，白话译文不需要 `## [0]`；否则前端会多一块冗余翻译。

10. **表章仅译散文**：013-022 表章只翻 `[N]`/`[N.M]` 数字编号，跳过 `[aN]`/`[rN]`/`[bN]` 等字母前缀表行。

**输出格式**：
## [X] 段落标题
[译文内容，保留所有实体标注]

**示例**：
原文PN [1]: 〖@黄帝〗者，〖@少典〗之子，姓〖&公孙〗，名曰〖@轩辕〗。生而神灵，弱而能言，幼而徇齐，长而敦敏，成而聪明。

译文:
## [1] 黄帝简介
〖@黄帝〗是〖@少典〗的儿子，姓〖&公孙〗，名叫〖@轩辕〗。他生下来就有神奇的灵性，幼年时就能说话，少年时聪慧过人，成年后敦厚聪敏，最终成为一位智慧超群的领袖。
```

---

## 工作流程

### 1. 准备阶段
```bash
# 1. 读取章节文件，确认PN编号范围
python scripts/extract_pn_segments.py chapter_md/NNN_章节名.tagged.md

# 2. 创建翻译输出目录（如不存在）
mkdir -p doc/translation
```

### 2. 翻译执行
使用Task工具批量调用translation subagent：
- 小/中章（<500 行）：单 agent 全章翻译
- 中大章（500-1000 行）：单 agent 但注意 stall
- **超长章（>1000 行或 >400 PN）**：必须**分 part 并行**翻译（部分区间 [1-50]/[51-100]/... 各存入 `_partN.md`），完成后 shell 合并并 `scripts/generate_translation_json.py`。006/007/008/128/130 均用此模式。单 agent 强行翻一个超长章节会被 watchdog kill（stall 600s）。
- 容错：API 配额用尽或内容过滤触发时重试，必要时缩小区间再分。

### 3. 质量检查

标准的三步校验（通常在 agent 内嵌 inline Python 即可）：

```python
import re
src = open('chapter_md/NNN_章节名.tagged.md').read()
tgt = open('doc/translation/NNN_章节名_白话.md').read()
src_pns = sorted(set(re.findall(r'\[(\d+(?:\.\d+)*)\]', src)))
src_pns = [p for p in src_pns if p != '0']
tgt_pns = sorted(set(re.findall(r'^## \[(\d+(?:\.\d+)*)\]', tgt, re.M)))
missing = [p for p in src_pns if p not in tgt_pns]
extra = [p for p in tgt_pns if p not in src_pns]
print(f'src={len(src_pns)} tgt={len(tgt_pns)} missing={missing[:5]} extra={extra[:5]}')
```

全库审核：
```bash
# 全库 PN/标注对齐、surface 消歧一致性审核
python scripts/sync_translation_disambig.py --all
```

### 4. 生成JSON输出文件

**⚠️ 关键改进（2026-04-14）**：JSON生成时在Python端完成语义标注渲染，前端直接使用渲染后的HTML

```bash
# 使用统一脚本生成JSON（自动进行语义标注渲染）
python scripts/generate_translation_json.py 001

# 批量生成多个章节
python scripts/generate_translation_json.py 001 002 003

# 生成所有已有翻译
python scripts/generate_translation_json.py --all
```

**生成的JSON格式**：
```json
{
  "chapter": "001",
  "title": "五帝本纪",
  "translations": {
    "1": {
      "title": "黄帝简介",
      "text": "<span class=\"person\" title=\"人名\">黄帝</span>是<span class=\"person\" title=\"人名\">少典</span>的儿子..."
    }
  }
}
```

**JSON格式要求**：
- 章节编号使用三位数字（如"001"）
- PN编号作为键（如"1", "1.1", "2.3"）
- **范围键**：当多个连续子段落共享一条翻译时，使用 `"起始-结束"` 格式（如 `"12.1-12.3"`, `"12.4-12.6"`）
  - 范围键的翻译覆盖该范围内所有子段落的内容
  - 前端会以范围起始PN（`12.1`）为定位锚点，将翻译框插入包含这些`<li>`的`<ul>`之后
  - 同一`<ul>`后的多个范围翻译按JSON键顺序依次追加
- 每个PN包含title（段落标题）和text（译文内容，**已渲染为HTML**）
- **text字段包含完整的HTML标签**，实体标注已转换为 `<span class="类型">` 格式
- 使用 `scripts/semantic_tags.py` 的 `render_tags_to_html()` 函数进行渲染

**为什么在Python端渲染？**
- **避免双重维护**：标注规范可能会进化，只在Python端维护渲染逻辑，避免Python和JavaScript双重实现
- **性能优化**：预渲染减少前端计算负担
- **一致性保证**：所有页面使用相同的渲染逻辑（由 `semantic_tags.py` 统一提供）

### 5. 前端显示机制
白话翻译通过以下机制显示：
- 翻译数据存储在 `docs/translations/NNN.json`
- 用户点击"白话翻译"开关时，前端fetch对应JSON文件
- 在每个PN段落后动态插入 `<div class="modern-translation" data-pn="键值">` 容器
- **`<li>` 子段落处理**：HTML中部分子段落（如12.1-12.11）位于`<ul>/<ol>`内的`<li>`元素中，块级`<div>`无法合法插入列表内部。前端会先跳出到列表层级（`<ul>`），再将翻译框插在整个列表之后
- **范围键**：JSON中的范围键（如`"12.1-12.3"`）以起始PN（`12.1`）为DOM定位锚点；同一列表后的多个范围翻译按键顺序追加，不会倒序
- 当"智能分段"启用时，子段落的翻译随原文段落同步折叠
- 翻译内容不受"拼音注释"和"繁简转换"功能影响（添加`pinyin-off`类）

### 6. 视觉设计规范（2026-04-14更新）

**设计目标**：白话翻译必须在视觉上与文言文原文形成清晰对比

**视觉对比方案**：

| 维度 | 文言文原文 | 白话翻译 |
|------|-----------|---------|
| **字体** | 宋体（衬线） | 黑体（无衬线） |
| **背景色** | `#fdfdf8` 米黄色 | `#f0f8ff` 淡蓝色 |
| **边框色** | `#8B4513` 褐色 | `#4682B4` 钢青色 |
| **文字色** | `#2c2c2c` 纯黑 | `#2c3e50` 深蓝灰 |
| **字号** | 1em | 0.92em（略小）|
| **风格** | 传统、庄重 | 现代、清新 |

**CSS实现** (`docs/css/shiji-styles.css`):
```css
.modern-translation {
    font-family: "Noto Sans SC", "Source Han Sans SC", sans-serif;
    background-color: #f0f8ff;
    border-left: 4px solid #4682B4;
    color: #2c3e50;
    font-size: 0.92em;
    line-height: 1.85;
    /* 圆角和阴影增强"卡片"感 */
    border-radius: 6px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
```

**设计理念**：
- **字体对比**：宋体（传统）vs 黑体（现代）是最直观的区分手段
- **色调对比**：暖色（古典）vs 冷色（现代）营造不同阅读氛围
- **实体标注**：白话翻译中的实体保持原文颜色体系，但字重增加（500）以适配黑体

**测试页面**：`docs/test/test-translation-rendering.html` 包含视觉对比测试

---

## 消歧语法（白话上下文）

### 核心规则

1. **继承不漏**：源文件 `chapter_md/NNN.tagged.md` 中凡有 `|` 消歧的实体，白话必须保留 `|规范名`
2. **surface 可变**：白话显示名可改（如"籍"→"项羽"），规范名保持不变
3. **不擅自添加**：源无 `|` 时白话也不加
4. **渲染显示 surface（规范名）**：`generate_translation_json.py` 调用 `render_tags_to_html(..., prefer_canonical=True)`
   - `〖@羽|项羽〗` → `<span title="人名·规范：项羽">羽（项羽）</span>`
   - surface 与 canonical 相同时只显示一次，如 `〖@项籍|项籍〗` → `项籍`
   - 未消歧的实体如 `〖@项籍〗` → 保持显示 `项籍`（无括号）

### 演化更新机制

当源 `.tagged.md` 新增或修改消歧后，运行同步脚本保持译文一致：

```bash
# 审核所有章节（只报告不修改）
python scripts/sync_translation_disambig.py --all

# 审核并自动同步（将源的新增消歧批量应用到译文）
python scripts/sync_translation_disambig.py --all --apply

# 单章操作
python scripts/sync_translation_disambig.py 002
python scripts/sync_translation_disambig.py 002 --apply
```

脚本逻辑（`scripts/sync_translation_disambig.py`）：

- **收集源映射**：从源文件抽取所有 `〖T surface|canonical〗`，构建 `{marker: {surface: canonical}}`
- **审核译文**：对每个译文实体
  - 若已有 `|canonical`：验证 canonical 在源规范池中
  - 若无 `|` 但 surface 是源已知映射：建议补齐
- **apply 模式**：对"建议补齐"项做全文替换 `〖T surface〗` → `〖T surface|canonical〗`

### 注意事项

- 同步脚本的 `--apply` 做**全文替换**，所以同一文件内同一表面形式的实体都会被统一
- 若译者使用了"规范名即 surface"的形式（如 `〖@项籍|项籍〗`），脚本不会警告——规范名一致即可
- "未知规范名"类警告需要人工审核——通常是译者自创的消歧（如 〖[活埋|坑〗）在源中不存在
- 运行顺序：每次修改源 `tagged.md` 的消歧 → `sync_translation_disambig.py --all --apply` → `generate_translation_json.py --all`

---

## Surface 翻译（白话化古词）

源 tagged.md 里某些 surface 是文言形式（"岁/馀/雒/江/河"等），白话译文应改为现代形式。脚本 `scripts/translate_surface.py` 集中维护这些规则：

```bash
# 审核（dry-run）
python scripts/translate_surface.py --all

# 应用
python scripts/translate_surface.py --all --apply

# 完后重跑 JSON
python scripts/generate_translation_json.py --all
```

**已内置规则**：
- **时间 `%`**：岁→年（|时长 语境）、岁馀→一年多、月馀→一个多月、十馀X→十多X、X日→X天、明日→第二天、终日→整天 等
- **地名 `=`**：单字河流 江→长江 / 河→黄河 / 淮→淮河 / 济→济水 / 汉/洛/渭/泾/泗/沂→加"水"后缀；雒→洛（全部含雒地名）
- **天文 `!`**：太白→金星|太白、荧惑→火星|荧惑、辰星→水星|辰星、岁星→木星|岁星、填星/镇星→土星
- **典籍 `{`**：诗→诗经|诗、书→尚书|书、易→易经|易、礼→礼记|礼、乐→乐经|乐
- **身份 `#`**：黔首→百姓|黔首、黎民→百姓|黎民、黎庶→百姓|黎庶、黔黎→百姓|黔黎

**不翻译**（保留原貌）：
- 官职/邦国/氏族/族群/器物/生物/数量/刑法/思想：或为专有名词，或现代仍用
- 身份中 寡人/朕/孤/庶人/布衣：历史自称和语感不宜抹去
- 制度 `^` 和 礼仪 `:`：史记专有制度名与礼节

**扩展规则**：直接编辑 `translate_surface.py` 的 `EXACT_REPLACEMENTS` 或 `REGEX_RULES`，再 `--all --apply` 生效。

**冗余括号自动清理**：脚本还会清理 `〖T X|Y〗（Z）` 中 Z∈{X,Y} 的冗余解释括号（防止渲染出 "X（Y）（Z）"）。

---

## 成语渲染

`〘※成语〙` 或 `〘※shiji|modern〙` 在 `render_tags_to_html` 中渲染为 `<span class="idiom">`：
- 文言模式：显示 shiji 形式
- 白话模式（prefer_canonical=True）：若有 modern 显示 `shiji（modern）`；否则显示 shiji
- CSS 类名 `idiom`（`docs/css/shiji-styles.css` L250 起）

---

## 注意事项

1. **实体标注是强制要求**：译文中必须完整保留原文的所有实体标注，这是知识图谱构建的基础
2. **不要过度解释**：翻译应忠实原文，不要添加原文没有的历史背景或注释
3. **保持简练**：史记以简洁著称，译文也应避免啰嗦
4. **尊重文体**：保留赞文、奏疏、诏书等特殊文体的语气和格式
5. **PN段落独立性**：每个PN段落应能独立理解，不依赖前后文
6. **不受其他显示选项影响**：白话翻译内容不应被拼音注释或繁简转换影响

---

## 检查清单

**执行前**：
- [ ] 章节 `.tagged.md` 文件已完成实体标注
- [ ] PN编号完整且无重复
- [ ] 翻译输出目录已创建

**执行中**：
- [ ] 使用标准提示词调用translation agent
- [ ] 验证每个译文段落的实体标注完整性
- [ ] 段落标题简洁准确

**执行后**：
- [ ] 所有PN段落翻译完整
- [ ] 实体标注验证通过
- [ ] 译文质量符合准确性、流畅性、简洁性标准
- [ ] 文件保存到 `doc/translation/` 目录
- [ ] 提交git时使用清晰的commit message

---

**最后更新**: 2026-04-22（130 章白话翻译全库落地，增补消歧继承/surface 翻译/成语渲染/超长章分 part 等规范）
**关联文件**: `doc/translation/`, `chapter_md/*.tagged.md`, `docs/translations/*.json`
**关联脚本**: `scripts/generate_translation_json.py`, `scripts/semantic_tags.py`, `scripts/sync_translation_disambig.py`, `scripts/translate_surface.py`
