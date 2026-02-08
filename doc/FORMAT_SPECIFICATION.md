# 史记知识库 Markdown 和 HTML 格式规范

基于项目实践和历史对话总结的完整格式要求。

---

## 目录

1. [Markdown格式规范](#markdown格式规范)
2. [HTML格式规范](#html格式规范)
3. [实体标注规范](#实体标注规范)
4. [Purple Numbers规范](#purple-numbers规范)
5. [小节划分规范](#小节划分规范)
6. [文件命名规范](#文件命名规范)

---

## Markdown格式规范

### 1. 文件结构

```markdown
# [0] 章节标题

## 小节标题1

[1] 第一段内容...

[1.1] 第一段的子段落...

## 小节标题2

[2] 第二段内容...

## 太史公曰

[N] 太史公评论...
```

**要求：**
- 必须有一个一级标题（`# [0] 章节标题`）
- 小节使用二级标题（`## 小节名称`）
- 小节标题要有意义，不能是"段落1-10"这样的机械划分
- 段落编号从[0]开始，可以使用多级编号（[1], [1.1], [1.1.1]）

### 2. 实体标注

**11类实体标注系统：**

| 标记符号 | 实体类型 | CSS类名 | 颜色 | 示例 |
|---------|---------|---------|------|------|
| `@人名@` | 人名 | person | #8B4513 棕色 | @黄帝@ @轩辕@ |
| `=地名=` | 地名 | place | #B8860B 金黄 | =阪泉之野= =涿鹿= |
| `#官职#` | 官职 | official | #8B0000 深红 | #天子# #云师# |
| `%时间%` | 时间 | time | #008B8B 青色 | %七十年% %三年% |
| `&朝代&` | 朝代/氏族 | dynasty | #9370DB 紫色 | &神农氏& &蜀山氏& |
| `^制度^` | 制度/典章 | institution | #4682B4 钢蓝 | ^五典^ ^五刑^ |
| `~族群~` | 族群/部落 | tribe | #2F4F4F 深灰 | ~荤粥~ ~三苗~ |
| `*器物*` | 器物/书名 | artifact | #CD853F 秘鲁棕 | *宝鼎* *璿玑玉衡* |
| `!天文!` | 天文/历法 | astronomy | #483D8B 深蓝紫 | !星鸟! !闰月! |
| `?神话?` | 神话/传说 | mythical | #8B008B 深洋红 | ?浑沌? ?饕餮? |
| `🌿动植物🌿` | 动植物 | flora-fauna | #228B22 森林绿 | 🌿熊🌿 🌿百穀🌿 |

**标注原则：**
- 成对出现，不能有未闭合的标注
- 不能嵌套（如 `@=地名=@` 是错误的）
- 不能为空（如 `@@` 是错误的）
- 优先标注最外层实体类型

### 3. 段落编号 (Purple Numbers)

**格式：**
```markdown
[0] 标题段落
[1] 一级段落
[1.1] 二级段落
[1.1.1] 三级段落
[2] 下一个一级段落
```

**规则：**
- 每个段落必须有唯一编号
- 编号使用方括号 `[]`
- 支持多级编号，用 `.` 分隔
- 一级编号建议连续（可以有跳号，但需合理）
- 编号永久不变（用于引用）

### 4. 对话引用

```markdown
> @孔子@曰："天下有道，则礼乐征伐自天子出。"
```

**规则：**
- 对话/引文使用 `>` 开头
- 引用内部仍需标注实体

### 5. 特殊要求

- 使用UTF-8编码
- 使用半角标点（段落编号外）
- 不使用全角数字
- 避免零宽字符
- 每行建议不超过200字符

---

## HTML格式规范

### 1. 文件结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>章节标题</title>
    <link rel="stylesheet" href="../css/shiji-styles.css">
    <link rel="stylesheet" href="../css/chapter-nav.css">
    <script src="../js/purple-numbers.js"></script>
</head>
<body>
<nav class="chapter-nav">
    <a href="../index.html" class="nav-home">回到主页</a>
    <a href="005_秦本纪.html" class="nav-prev">← 上一页</a>
    <a href="007_项羽本纪.html" class="nav-next">下一页 →</a>
</nav>

<h1><a href="#pn-0" id="pn-0" class="para-num">0</a> 章节标题</h1>

<h2>小节标题</h2>

<p><a href="#pn-1" id="pn-1" class="para-num">1</a>
   <span class="person" title="人名">黄帝</span>者...
</p>

</body>
</html>
```

### 2. Purple Numbers 实现

**段落编号链接：**
```html
<a href="#pn-1" id="pn-1" class="para-num" title="点击复制链接">1</a>
```

**要求：**
- `href` 和 `id` 必须一致
- 使用 `pn-` 前缀
- 添加 `title` 提示
- 包含 JavaScript 交互（purple-numbers.js）

### 3. 实体标注的HTML

```html
<span class="person" title="人名">黄帝</span>
<span class="place" title="地名">涿鹿</span>
<span class="official" title="官职">天子</span>
<span class="time" title="时间">三年</span>
<span class="dynasty" title="朝代/氏族">神农氏</span>
<span class="institution" title="制度">五典</span>
<span class="tribe" title="族群">三苗</span>
<span class="artifact" title="器物/书名">宝鼎</span>
<span class="astronomy" title="天文">星鸟</span>
<span class="mythical" title="神话">浑沌</span>
<span class="flora-fauna" title="动植物">熊</span>
```

**要求：**
- 使用 `<span>` 标签
- class 属性使用标准CSS类名
- title 属性显示实体类型

### 4. 导航链接

**要求：**
- 主页链接：`href="../index.html"`（不是 `../docs/index.html`）
- 章节链接：`href="001_五帝本纪.html"`（不包含 `.tagged`）
- 原文链接：`href="../original_text/001_五帝本纪.txt"`
- CSS链接：`href="../css/shiji-styles.css"`（不包含 `docs/`）
- JS链接：`src="../js/purple-numbers.js"`（不包含 `docs/`）

### 5. 页面元数据

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>001_五帝本纪</title> <!-- 不包含.tagged -->
    <link rel="stylesheet" href="../css/shiji-styles.css">
    <link rel="stylesheet" href="../css/chapter-nav.css">
    <script src="../js/purple-numbers.js"></script>
</head>
```

**要求：**
- UTF-8编码声明
- 移动端viewport设置
- 标题不包含 `.tagged` 后缀
- 正确引用CSS和JS文件

---

## 实体标注规范

### 1. 标注优先级

**必须标注：**
1. 人名（历史人物、虚构人物）
2. 地名（行政区、山川、建筑）
3. 官职（职位、爵位、尊称）
4. 时间（年份、月份、季节）
5. 朝代/氏族（王朝、部族、家族）

**选择性标注：**
6. 制度（法律、礼仪、政治制度）
7. 族群（民族、部落）
8. 器物/书名（工具、书籍、乐器）
9. 天文/历法（星宿、节气）
10. 神话/传说（神兽、传说人物）
11. 动植物（具体物种）

### 2. 复杂情况处理

**人名 vs 官职：**
```markdown
✅ 正确: @萧何@为#丞相#
❌ 错误: #萧丞相#（不要合并）
```

**地名 vs 国名：**
```markdown
✅ 正确: &秦&攻=邯郸=
❌ 错误: =秦=攻=邯郸=（秦是朝代不是地名）
```

**多重身份：**
```markdown
✅ 优先标注人名: @汉武帝@
✅ 可替代标注: #皇帝#（如果强调职位）
```

### 3. 特殊实体

**职位/标题（新标记$，用于替代#）：**
```markdown
$天子$ $上将军$ $丞相$
```

**引号标记：**
```markdown
> 引用的对话或文字
```

---

## Purple Numbers规范

### 1. 设计理念

Purple Numbers 是对计算机先驱 Doug Engelbart 的致敬：
- 每个段落有唯一、永久的编号
- 可以精确引用到具体段落
- 支持超链接和知识管理

### 2. 编号格式

**单级编号：**
```markdown
[0] 标题
[1] 第一段
[2] 第二段
```

**多级编号：**
```markdown
[1] 主题段落
[1.1] 第一个子段落
[1.2] 第二个子段落
[1.2.1] 更细的子段落
[2] 下一个主题
```

### 3. HTML实现

```html
<a href="#pn-1" id="pn-1" class="para-num" title="点击复制链接">1</a>
```

**CSS样式：**
```css
.para-num {
    background-color: #F3E5F5;  /* 淡紫色背景 */
    color: #7B1FA2;             /* 紫色文字 */
    border: 1px solid #CE93D8;  /* 淡紫色边框 */
    padding: 2px 6px;
    border-radius: 3px;
    margin-right: 8px;
    cursor: pointer;
}
```

### 4. JavaScript交互

purple-numbers.js 提供：
- 点击复制段落链接到剪贴板
- 悬停提示
- URL哈希导航（直接跳转到#pn-5）

---

## 小节划分规范

### 1. 小节标题要求

**必须：**
- 使用二级标题 `##`
- 标题要有意义，反映内容主题
- 简洁明了（5-10字）
- 符合史记文体风格

**禁止：**
- ❌ `## 段落1-10`（机械划分）
- ❌ `## 第一部分`（无意义）
- ❌ `## [1] 标题`（不要包含段落编号）

**示例：**
```markdown
✅ ## 黄帝的兴起与征战
✅ ## 巨鹿之战
✅ ## 太史公评论
❌ ## 第1-10段
❌ ## Part 1
```

### 2. 小节划分原则

**按内容主题划分：**
- 人物传记：早年经历、主要功绩、晚年结局
- 战争：起因、过程、结果
- 政治：政策、影响、评价

**按时间顺序划分：**
- 年代阶段（如"秦王政时期"）
- 事件序列（如"统一六国"）

**按人物划分：**
- 列传中多个人物（如"颜回传"、"子路传"）

### 3. 小节数量建议

| 章节长度 | 建议小节数 | 备注 |
|---------|-----------|------|
| < 10段 | 2-3个 | 短篇列传 |
| 10-30段 | 3-5个 | 中等列传 |
| 30-60段 | 5-8个 | 长篇列传、世家 |
| 60-100段 | 8-12个 | 本纪 |
| > 100段 | 12-20个 | 书、表 |

### 4. 特殊章节

**本纪：**
- 按时间顺序（年代、重大事件）
- 按主题（政治、军事、改革）

**世家：**
- 按世系（各代传承）
- 按事件（主要功绩）

**列传：**
- 单人：生平阶段
- 多人：按人物分节

**书：**
- 按主题分类（如天官书：星宿分类）
- 按历史沿革

**表：**
- 按时间段
- 按人物/事件类型

---

## 文件命名规范

### 1. Markdown文件

**格式：**
```
NNN_章节名称.tagged.md
```

**示例：**
```
001_五帝本纪.tagged.md
027_天官书.tagged.md
061_伯夷列传.tagged.md
```

**要求：**
- 三位数字编号（001-130）
- 下划线分隔
- `.tagged.md` 后缀表示已标注

### 2. HTML文件

**格式：**
```
NNN_章节名称.html
```

**示例：**
```
001_五帝本纪.html
027_天官书.html
061_伯夷列传.html
```

**要求：**
- 三位数字编号
- 不包含 `.tagged` （发布时移除）
- 与Markdown文件名对应

### 3. 原文文件

**格式：**
```
NNN_章节名称.txt
```

**示例：**
```
001_五帝本纪.txt
027_天官书.txt
```

### 4. 辅助文件

```
sections_data.json          # 小节数据
vocabularies/              # 词表目录
  人名.txt
  地名.txt
events/                    # 事件数据
genealogy/                 # 家谱数据
```

---

## 质量标准与检查

### 1. Markdown质量检查 (`lint_markdown.py`)

使用 `lint_markdown.py` 检查：
```bash
python3 lint_markdown.py chapter_md/001_五帝本纪.tagged.md
python3 lint_markdown.py chapter_md/  # 检查整个目录
```

#### 检查项目

**1.1 实体标注语法**（错误级别）
- ✓ 检查11类实体标注的正确性
- ✓ 未闭合标注（如单个 `@` 符号）
- ✓ 空标注（如 `@@`）
- ✓ 嵌套标注（如 `@=地名=@`）

**1.2 段落编号**（错误+警告）
- ✓ Purple Numbers 格式（`[1]`, `[1.1]`, `[1.1.1]`）
- ✓ 编号格式合法性（只能包含数字和点）
- ✓ 一级编号连续性检查

**1.3 标题结构**（警告）
- ✓ 一级标题数量（应该只有一个）
- ✓ 标题层级跳跃（如从 `#` 直接到 `###`）
- ✓ 标题中包含段落编号（不建议）

**1.4 引用标记**（提示）
- ✓ `>` 开头的引用行
- ✓ 未标记的对话检测（包含"曰"等引语动词）

**1.5 特殊字符**（警告）
- ✓ 全角数字（应改为半角）
- ✓ 段落编号中的全角标点
- ✓ 零宽字符检测（U+200B等）

**1.6 行长度**（提示）
- ✓ 超过200字符的行（建议分段）

#### 质量标准

**零错误标准：**
- 无未闭合标注
- 无空标注
- 段落编号格式正确（只含数字和点）
- 无严重嵌套问题

**可接受的警告：**
- 段落编号不连续（使用多级编号时）
- 标题层级跳跃（某些特殊结构）
- 未标记对话提示（并非所有"曰"都是对话）

**退出代码：**
- `0` - 无错误
- `1` - 有错误

---

### 2. HTML质量检查 (`lint_html.py`)

使用 `lint_html.py` 检查：
```bash
python3 lint_html.py docs/chapters/001_五帝本纪.html
python3 lint_html.py docs/chapters/  # 检查整个目录
```

#### 检查项目

**2.1 HTML结构**（错误级别）
- ✓ 标签闭合和嵌套正确性
- ✓ 必需标签存在（`<html>`, `<head>`, `<body>`, `<title>`）
- ✓ HTML解析无错误

**2.2 实体样式**（警告）
- ✓ CSS类名正确性（11个标准实体类名）
- ✓ 拼写错误检测
- ✓ 未知类名警告

标准CSS类名：
```
person, place, official, time, dynasty, institution,
tribe, artifact, astronomy, mythical, flora-fauna
```

**2.3 Purple Numbers**（错误+警告）
- ✓ 锚点格式（`<a href="#pn-1" id="pn-1" class="para-num">`）
- ✓ href和id一致性
- ✓ 编号连续性

**2.4 导航链接**（错误+警告）
- ✓ 主页链接格式（`../index.html` 不是 `../docs/index.html`）
- ✓ `.tagged.html` 后缀残留检测（必须移除）
- ✓ 上一页/下一页链接格式
- ✓ 章节链接文件名格式（`NNN_章节名.html`）

**2.5 资源引用**（错误+警告）
- ✓ 必需CSS文件（`../css/shiji-styles.css`, `../css/chapter-nav.css`）
- ✓ Purple Numbers JS文件（`../js/purple-numbers.js`）
- ✓ 错误路径检测（如 `../docs/css/` 应为 `../css/`）

**2.6 页面元数据**（错误+警告）
- ✓ UTF-8字符编码声明
- ✓ 页面标题中的 `.tagged` 后缀（必须移除）
- ✓ 特殊字符转义检查

#### 质量标准

**零错误标准：**
- HTML结构完整
- 所有链接正确（无.tagged残留）
- CSS/JS路径正确（无docs/残留）
- Purple Numbers的href和id一致

**可接受的警告：**
- 段落编号不连续（正常）
- 某些可疑CSS类名（需人工确认）

**退出代码：**
- `0` - 无错误
- `1` - 有错误

---

### 3. 已知限制

#### Markdown Linter限制

1. **误报**：可能将Markdown标题的 `#` 误识别为官职标注
   - 解决方案：检测逻辑已排除标题行

2. **复杂嵌套**：某些合法的复杂标注可能被误报
   - 示例：`@#御史大夫#萧何@` (人名包含官职)
   - 属于警告级别，需人工判断

3. **引用检测**：可能将非对话的"曰"误报为未标记对话
   - 属于提示级别，不影响整体检查

#### HTML Linter限制

1. **复杂嵌套**：对于非常复杂的HTML结构可能漏检
2. **JavaScript内容**：不检查`<script>`标签内的JavaScript代码
3. **性能**：大文件（>1MB）检查较慢

---

### 4. 常见错误示例

#### 错误1: 未闭合的人名标注
```markdown
❌ 错误: @黄帝 征战四方
✅ 正确: @黄帝@ 征战四方
```

#### 错误2: 空标注
```markdown
❌ 错误: @@ 或 ==
✅ 正确: @黄帝@ 或 =涿鹿=
```

#### 错误3: 嵌套标注
```markdown
❌ 错误: @=地名=@
✅ 正确: @人名@ 或 =地名=（选择最外层实体类型）
```

#### 错误4: 段落编号格式错误
```markdown
❌ 错误: [1.a] 或 [1-2]
✅ 正确: [1.1] 或 [2]
```

#### 错误5: .tagged.html链接残留
```html
❌ 错误: <a href="001_五帝本纪.tagged.html">
✅ 正确: <a href="001_五帝本纪.html">
```

#### 错误6: CSS路径错误
```html
❌ 错误: <link href="../docs/css/shiji-styles.css">
✅ 正确: <link href="../css/shiji-styles.css">
```

#### 错误7: Purple Numbers不一致
```html
❌ 错误: <a href="#pn-10" id="pn-11" class="para-num">
✅ 正确: <a href="#pn-10" id="pn-10" class="para-num">
```

---

### 5. 发布前检查清单

**准备阶段：**
- [ ] Markdown实体标注完整（11类实体）
- [ ] 小节划分有意义（非机械划分）
- [ ] 段落编号正确且唯一

**生成阶段：**
- [ ] HTML生成成功
- [ ] Purple Numbers正确实现
- [ ] 导航链接正确

**质量检查：**
- [ ] `lint_markdown.py` 零错误
- [ ] `lint_html.py` 零错误
- [ ] 手动抽查2-3个章节

**发布阶段：**
- [ ] Git提交信息清晰
- [ ] 推送到远程仓库
- [ ] 验证GitHub Pages更新

---

## 示例

### 完整的Markdown示例

```markdown
# [0] 五帝本纪

## @黄帝@

### 兴起与征讨

[1] @黄帝@者，@少典@之子，姓公孙，名曰@轩辕@。生而神灵，弱而能言，幼而徇齐，长而敦敏，成而聪明。

[1.1] %轩辕之时%，&神农氏&世衰。诸侯相侵伐，暴虐百姓，而&神农氏&弗能征。

### 统一天下

[2] @轩辕@乃修德振兵，治^五气^，蓺^五种^，抚万民，度四方，教熊罴貔貅貙虎，以与@炎帝@战於=阪泉之野=。三战，然後得其志。

## 太史公曰

[27] 太史公曰：学者多称五帝，尚矣。然《尚书》独载@尧@以来；而百家言&黄帝&，其文不雅驯，荐绅先生难言之。
```

### 完整的HTML示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>001_五帝本纪</title>
    <link rel="stylesheet" href="../css/shiji-styles.css">
    <link rel="stylesheet" href="../css/chapter-nav.css">
    <script src="../js/purple-numbers.js"></script>
</head>
<body>
<nav class="chapter-nav">
    <a href="../index.html" class="nav-home">回到主页</a>
    <a href="002_夏本纪.html" class="nav-next">下一页 →</a>
</nav>

<h1><a href="#pn-0" id="pn-0" class="para-num">0</a> 五帝本纪
    <a href="../original_text/001_五帝本纪.txt" class="original-text-link">原文</a>
</h1>

<h2><span class="person">黄帝</span></h2>

<h3>兴起与征讨</h3>

<p><a href="#pn-1" id="pn-1" class="para-num">1</a>
<span class="person" title="人名">黄帝</span>者，
<span class="person" title="人名">少典</span>之子，姓公孙，名曰
<span class="person" title="人名">轩辕</span>。生而神灵，弱而能言，幼而徇齐，长而敦敏，成而聪明。
</p>

</body>
</html>
```

---

## 参考文档

- [ENTITY_TAGGING_SCHEME.md](doc/ENTITY_TAGGING_SCHEME.md) - 实体标注详细方案
- [PURPLE_NUMBERS.md](doc/PURPLE_NUMBERS.md) - Purple Numbers设计说明
- [LINT_GUIDE.md](LINT_GUIDE.md) - Lint工具使用指南
- [WORKFLOW.md](WORKFLOW.md) - 开发工作流程

---

**创建时间**: 2026-02-08
**版本**: 1.0
**维护者**: 史记知识库项目组
