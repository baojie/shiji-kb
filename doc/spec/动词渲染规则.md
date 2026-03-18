# 动词标注渲染规则 v3.0

本文档定义动词标注在HTML中的渲染规则，包括CSS样式、视觉设计理念和实现细节。

---

## 目录

1. [渲染流程](#渲染流程)
2. [CSS样式规则](#css样式规则)
3. [视觉设计理念](#视觉设计理念)
4. [HTML输出示例](#html输出示例)
5. [与名词实体的视觉区分](#与名词实体的视觉区分)

---

## 渲染流程

### 1. Markdown到HTML的转换

**输入（Markdown）**：
```markdown
〖'楚〗⟦◈伐⟧〖'随〗。⟦◉杀⟧〖;令尹〗〖@子西〗，〖[斩首〗八万。
```

**输出（HTML）**：
```html
<span class="feudal-state">楚</span>
<span class="verb-military" title="军事动词">伐</span>
<span class="feudal-state">随</span>。
<span class="verb-penalty" title="刑罚动词">杀</span>
<span class="official">令尹</span>
<span class="person">子西</span>，
<span class="legal">斩首</span>八万。
```

### 2. 正则表达式规则

定义在 [render_shiji_html.py](../../render_shiji_html.py:43-51)：

```python
ENTITY_PATTERNS = [
    # 动词标注（v3.0，优先处理）
    (r'⟦◈([^⟦⟧|]+)\|([^⟦⟧]+)⟧', r'<span class="verb-military" title="军事动词：\2" data-canonical="\2">\1</span>'),  # 军事动词（消歧）
    (r'⟦◈([^⟦⟧]+)⟧', r'<span class="verb-military" title="军事动词">\1</span>'),                                        # 军事动词
    (r'⟦◉([^⟦⟧|]+)\|([^⟦⟧]+)⟧', r'<span class="verb-penalty" title="刑罚动词：\2" data-canonical="\2">\1</span>'),   # 刑罚动词（消歧）
    (r'⟦◉([^⟦⟧]+)⟧', r'<span class="verb-penalty" title="刑罚动词">\1</span>'),                                         # 刑罚动词
    (r'⟦○([^⟦⟧|]+)\|([^⟦⟧]+)⟧', r'<span class="verb-political" title="政治动词：\2" data-canonical="\2">\1</span>'), # 政治动词（预留）
    (r'⟦○([^⟦⟧]+)⟧', r'<span class="verb-political" title="政治动词">\1</span>'),                                       # 政治动词（预留）
    (r'⟦◇([^⟦⟧|]+)\|([^⟦⟧]+)⟧', r'<span class="verb-economic" title="经济动词：\2" data-canonical="\2">\1</span>'),  # 经济动词（预留）
    (r'⟦◇([^⟦⟧]+)⟧', r'<span class="verb-economic" title="经济动词">\1</span>'),                                        # 经济动词（预留）
    # ... 名词实体模式 ...
]
```

### 3. 处理优先级

动词标注**必须优先于名词标注**处理，原因：
- 动词和名词使用不同的外层符号（`⟦⟧` vs `〖〗`），不会冲突
- 优先处理可确保正则匹配的确定性
- 避免与其他实体模式的潜在干扰

---

## CSS样式规则

定义在 [shiji-styles.css](../../docs/css/shiji-styles.css:145-191)：

### 1. 军事动词 `verb-military`

**标注格式**：`⟦◈伐⟧`、`⟦◈攻⟧`、`⟦◈击⟧`

**CSS规则**：
```css
.verb-military {
    color: #DC143C;              /* 深红色 - 战争与冲突 */
    background-color: rgba(220, 20, 60, 0.08);  /* 淡红背景 */
    padding: 0 2px;
    border-radius: 2px;
    font-weight: 600;            /* 加粗强调军事行动 */
    cursor: help;
}
```

**视觉效果**：
- 颜色：深红色（#DC143C），象征战争与冲突
- 背景：8%透明度的淡红色
- 字重：600（半粗体），突出军事行动的重要性
- 圆角：2px，柔和边缘

**示例**：
<span style="color: #DC143C; background-color: rgba(220, 20, 60, 0.08); padding: 0 2px; border-radius: 2px; font-weight: 600;">伐</span>、
<span style="color: #DC143C; background-color: rgba(220, 20, 60, 0.08); padding: 0 2px; border-radius: 2px; font-weight: 600;">攻</span>、
<span style="color: #DC143C; background-color: rgba(220, 20, 60, 0.08); padding: 0 2px; border-radius: 2px; font-weight: 600;">击</span>

### 2. 刑罚动词 `verb-penalty`

**标注格式**：`⟦◉杀⟧`、`⟦◉诛⟧`、`⟦◉斩⟧`

**CSS规则**：
```css
.verb-penalty {
    color: #8B0000;              /* 暗红色 - 刑罚与惩处 */
    background-color: rgba(139, 0, 0, 0.06);    /* 淡暗红背景 */
    border-bottom: 1px solid rgba(139, 0, 0, 0.3);  /* 底部边框强调 */
    padding: 0 2px;
    font-weight: 600;
    cursor: help;
}
```

**视觉效果**：
- 颜色：暗红色（#8B0000），象征刑罚与惩处
- 背景：6%透明度的淡暗红色
- 底部边框：1px实线，30%透明度，增强视觉区分
- 字重：600（半粗体）

**示例**：
<span style="color: #8B0000; background-color: rgba(139, 0, 0, 0.06); border-bottom: 1px solid rgba(139, 0, 0, 0.3); padding: 0 2px; font-weight: 600;">杀</span>、
<span style="color: #8B0000; background-color: rgba(139, 0, 0, 0.06); border-bottom: 1px solid rgba(139, 0, 0, 0.3); padding: 0 2px; font-weight: 600;">诛</span>、
<span style="color: #8B0000; background-color: rgba(139, 0, 0, 0.06); border-bottom: 1px solid rgba(139, 0, 0, 0.3); padding: 0 2px; font-weight: 600;">斩</span>

### 3. 政治动词 `verb-political`（预留）

**标注格式**：`⟦○立⟧`、`⟦○封⟧`、`⟦○拜⟧`

**CSS规则**：
```css
.verb-political {
    color: #4169E1;              /* 皇家蓝 - 政治与外交 */
    background-color: rgba(65, 105, 225, 0.06);
    padding: 0 2px;
    border-radius: 2px;
    font-weight: 500;
    cursor: help;
}
```

**视觉效果**：
- 颜色：皇家蓝（#4169E1），象征政治与外交
- 背景：6%透明度的淡蓝色
- 字重：500（中等粗体）
- 圆角：2px

### 4. 经济动词 `verb-economic`（预留）

**标注格式**：`⟦◇赐⟧`、`⟦◇贡⟧`、`⟦◇赂⟧`

**CSS规则**：
```css
.verb-economic {
    color: #DAA520;              /* 金杆色 - 经济与财货 */
    background-color: rgba(218, 165, 32, 0.06);
    padding: 0 2px;
    border-radius: 2px;
    font-weight: 500;
    cursor: help;
}
```

**视觉效果**：
- 颜色：金杆色（#DAA520），象征经济与财货
- 背景：6%透明度的淡金色
- 字重：500（中等粗体）
- 圆角：2px

---

## 视觉设计理念

### 设计原则

1. **醒目但不喧宾夺主**
   - 动词样式与名词实体保持视觉层级一致
   - 不过度装饰，保持阅读流畅性
   - 颜色对比度适中，避免视觉疲劳

2. **类型区分明确**
   - 军事动词：深红色 + 背景 + 加粗（最强调）
   - 刑罚动词：暗红色 + 背景 + 底部边框（次强调）
   - 政治/经济：蓝/金色 + 背景（中等强调）

3. **语义化配色**
   - 红色系：军事（深红）、刑罚（暗红），象征冲突与惩罚
   - 蓝色系：政治（皇家蓝），象征权威与外交
   - 金色系：经济（金杆色），象征财富与交易

4. **交互友好**
   - `cursor: help`：鼠标悬停显示帮助光标
   - `title` 属性：显示动词类型及消歧信息
   - `data-canonical` 属性：记录消歧后的规范形式

### 视觉层级

| 层级 | 元素 | 视觉特征 | 强调程度 |
|------|------|---------|---------|
| **最高** | 军事动词 | 深红色 + 背景 + font-weight:600 | ★★★★★ |
| **次高** | 刑罚动词 | 暗红色 + 背景 + 底部边框 + font-weight:600 | ★★★★☆ |
| **中等** | 政治/经济动词 | 蓝/金色 + 背景 + font-weight:500 | ★★★☆☆ |
| **基准** | 名词实体 | 各类颜色 + 下划线/背景等 | ★★★☆☆ |
| **最低** | 普通文本 | 默认黑色 | ★☆☆☆☆ |

---

## HTML输出示例

### 示例1：单纯军事行动

**Markdown**：
```markdown
〖'楚〗⟦◈伐⟧〖'随〗。〖'楚〗⟦◈灭⟧〖'邓〗。
```

**HTML**：
```html
<span class="feudal-state" title="邦国">楚</span>
<span class="verb-military" title="军事动词">伐</span>
<span class="feudal-state" title="邦国">随</span>。
<span class="feudal-state" title="邦国">楚</span>
<span class="verb-military" title="军事动词">灭</span>
<span class="feudal-state" title="邦国">邓</span>。
```

**渲染效果**（文字描述）：
> <span style="color: #B266B2; border-bottom: 1px solid #B266B280;">楚</span><span style="color: #DC143C; background-color: rgba(220, 20, 60, 0.08); padding: 0 2px; border-radius: 2px; font-weight: 600;">伐</span><span style="color: #B266B2; border-bottom: 1px solid #B266B280;">随</span>。<span style="color: #B266B2; border-bottom: 1px solid #B266B280;">楚</span><span style="color: #DC143C; background-color: rgba(220, 20, 60, 0.08); padding: 0 2px; border-radius: 2px; font-weight: 600;">灭</span><span style="color: #B266B2; border-bottom: 1px solid #B266B280;">邓</span>。

### 示例2：复杂战役叙述

**Markdown**：
```markdown
〖'吴〗⟦◈伐|征伐⟧⟦◈败|击败⟧〖@子常〗，〖@子常〗⟦◈走|逃亡⟧奔〖'郑〗
```

**HTML**：
```html
<span class="feudal-state" title="邦国">吴</span>
<span class="verb-military" title="军事动词：征伐" data-canonical="征伐">伐</span>
<span class="verb-military" title="军事动词：击败" data-canonical="击败">败</span>
<span class="person" title="人名">子常</span>，
<span class="person" title="人名">子常</span>
<span class="verb-military" title="军事动词：逃亡" data-canonical="逃亡">走</span>奔
<span class="feudal-state" title="邦国">郑</span>
```

### 示例3：政治处决

**Markdown**：
```markdown
〖@帝喾〗以〖%庚寅〗日⟦◉诛⟧〖@重黎〗
```

**HTML**：
```html
<span class="person" title="人名">帝喾</span>以
<span class="time" title="时间">庚寅</span>日
<span class="verb-penalty" title="刑罚动词">诛</span>
<span class="person" title="人名">重黎</span>
```

### 示例4：刑罚与制度混用

**Markdown**：
```markdown
⟦◉杀⟧〖;令尹〗〖@子西〗，〖[斩首〗八万
```

**HTML**：
```html
<span class="verb-penalty" title="刑罚动词">杀</span>
<span class="official" title="官职">令尹</span>
<span class="person" title="人名">子西</span>，
<span class="legal" title="刑法">斩首</span>八万
```

**说明**：
- `⟦◉杀⟧` - 动词：杀害行为
- `〖[斩首〗` - 名词：刑罚制度术语

---

## 与名词实体的视觉区分

### 对比表

| 维度 | 名词实体 | 动词实体 |
|------|---------|---------|
| **外层符号** | `〖〗` (白色龟甲括号) | `⟦⟧` (数学双方括号) |
| **TYPE符号** | 文本符号（@=;%等） | 几何符号（◈◉○◇） |
| **CSS类名前缀** | 直接类型名（person/place等） | `verb-` 前缀（verb-military等） |
| **主要视觉特征** | 下划线/背景/斜体等多样化 | 背景+加粗为主，统一风格 |
| **颜色系统** | 18种独立颜色 | 4种语义化颜色（红/红/蓝/金） |
| **强调程度** | 中等（与文本区分） | 较强（加粗+背景） |

### 混合标注示例

**完整句子**：
```markdown
〖'楚〗⟦◈伐⟧〖'随〗。⟦◉杀⟧〖;令尹〗〖@子西〗，〖[斩首〗八万。
```

**视觉解析**：
- **邦国**（紫色下划线）：楚、随
- **军事动词**（深红色背景）：伐
- **刑罚动词**（暗红色背景+底部边框）：杀
- **官职**（深红色）：令尹
- **人名**（棕色下划线）：子西
- **刑罚制度**（暗红色淡背景）：斩首
- **普通文本**（黑色）：八万

---

## 技术实现细节

### 1. tooltip显示

鼠标悬停在动词上时，显示tooltip：

- **基本格式**：`title="军事动词"` 或 `title="刑罚动词"`
- **消歧格式**：`title="军事动词：征伐"` 或 `title="刑罚动词：处死"`

### 2. 数据属性

使用 `data-canonical` 属性记录消歧信息：

```html
<span class="verb-military" title="军事动词：征伐" data-canonical="征伐">伐</span>
```

未来可用于：
- JavaScript交互（点击显示详情）
- 语义检索（按规范形式搜索）
- 数据分析（统计动词使用频率）

### 3. 响应式设计

所有动词样式在不同屏幕尺寸下保持一致：
- 字重：600（军事/刑罚）或 500（政治/经济）
- 内边距：0 2px（固定）
- 背景透明度：6%-8%（固定）

### 4. 可访问性

- `cursor: help`：视觉提示可交互
- 颜色对比度：符合WCAG AA标准
- 不依赖颜色区分：辅以背景、边框、字重

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| **v3.0** | 2026-03-19 | 首次发布动词渲染规则，定义军事/刑罚两大类CSS样式 |

---

## 相关文档

- [动词标注规范](动词标注规范.md) - 完整的动词标注语法和分类体系
- [标注格式规范](标注格式规范.md) - 整体标注格式要求
- [实体标注方案](实体标注方案.md) - 名词实体标注体系

---

**文档维护**: Claude AI Agent
**最后更新**: 2026-03-19
**CSS文件**: [shiji-styles.css](../../docs/css/shiji-styles.css)
**渲染脚本**: [render_shiji_html.py](../../render_shiji_html.py)
