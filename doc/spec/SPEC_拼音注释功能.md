# 史记知识库拼音注释功能规范

**版本**: 1.0
**日期**: 2026-03-31
**状态**: 已实现

## 概述

本文档描述史记知识库中汉字拼音注释功能的完整实现规范。该功能使用HTML5标准的 `<ruby>` 标注实现拼音与汉字的精确对齐，为读者提供便捷的阅读辅助。

## 目标

1. **可读性**: 为《史记》中的汉字提供拼音注释，降低生僻字认读门槛
2. **精确对齐**: 每个汉字的拼音直接显示在该汉字正上方
3. **用户可控**: 支持用户通过设置面板开关拼音显示
4. **全面覆盖**: 覆盖标题（h1/h2/h3）、段落（p）、引用块（blockquote）、列表项（li）
5. **性能优化**: 分帧处理避免页面卡顿

## 技术架构

### 1. 核心技术栈

- **HTML**: `<ruby>` + `<rt>` 标准元素
- **JavaScript**: ES6+ (动态导入、异步函数、DOM操作)
- **CSS**: Ruby标注样式、响应式间距控制
- **外部依赖**: `pinyin-pro` v3.28.0 (通过CDN动态加载)

### 2. 文件结构

```
shiji-kb/
├── docs/
│   ├── js/
│   │   ├── heading-pinyin.js        # 拼音注释核心脚本
│   │   └── settings-panel.js        # 设置面板交互脚本
│   ├── css/
│   │   └── shiji-styles.css         # 包含拼音样式定义
│   ├── data/
│   │   └── special-pronunciation.json  # 特殊读音词表
│   └── chapters/
│       └── *.html                   # 生成的章节HTML文件
├── doc/spec/
│   ├── 拼音注释功能规范.md          # 本文档
│   └── 特殊读音词表维护说明.md      # 特殊读音维护指南
├── skills/
│   └── SKILL_01d_正音与拼音标注.md  # SKILL文档
└── render_shiji_html.py             # HTML生成脚本（包含拼音引用）
```

## 实现细节

### 1. HTML结构

#### 1.1 页面引用

每个章节HTML文件的 `<head>` 中包含：

```html
<link rel="stylesheet" href="../css/shiji-styles.css">
<script defer src="../js/heading-pinyin.js"></script>
```

#### 1.2 设置面板

```html
<div id="settings-panel">
    <h3>显示设置</h3>
    <div class="setting-group">
        <label class="setting-item">
            <input type="checkbox" id="syntax-highlight" checked>
            <span>语法高亮</span>
        </label>
        <label class="setting-item">
            <input type="checkbox" id="pinyin-display" checked>
            <span>拼音注释</span>
        </label>
    </div>
</div>
```

#### 1.3 Ruby标注结构

拼音脚本会将原始文本转换为：

```html
<!-- 原始文本 -->
黄帝者，少典之子

<!-- 转换后 -->
<ruby><span class="hanzi">黄</span><rt class="pinyin-rt">huáng</rt></ruby>
<ruby><span class="hanzi">帝</span><rt class="pinyin-rt">dì</rt></ruby>
者，
<ruby><span class="hanzi">少</span><rt class="pinyin-rt">shǎo</rt></ruby>
<ruby><span class="hanzi">典</span><rt class="pinyin-rt">diǎn</rt></ruby>
之子
```

### 2. JavaScript实现

#### 2.1 核心函数

**文件**: `docs/js/heading-pinyin.js`

##### 主要函数说明

1. **`isHan(ch)`**
   - 功能：判断字符是否为汉字
   - 正则：`/[\u4e00-\u9fff]/`

2. **`isPolyphonicCached(pinyinFn, ch)`**
   - 功能：判断汉字是否为多音字（带缓存）
   - 缓存：使用 `Map` 对象缓存结果

3. **`addRubyAnnotation(node, pinyinFn, inEntity)`**
   - 功能：递归遍历DOM节点，为汉字添加ruby标注
   - 参数：
     - `node`: DOM节点
     - `pinyinFn`: 拼音函数
     - `inEntity`: 是否在专名链接内
   - 返回：处理后的节点或DocumentFragment

4. **`addPinyinToElement(el, pinyinFn)`**
   - 功能：为元素添加拼音注释（原地修改）
   - 标记：使用 `data-pinyin-added` 避免重复处理

5. **`init()`**
   - 功能：初始化函数，加载拼音库并处理页面元素
   - 流程：
     1. 动态导入 `pinyin-pro` (CDN多镜像回退)
     2. 处理标题元素（h1, h2, h3）
     3. 收集正文元素（p, blockquote, li）
     4. 使用 `requestIdleCallback` 分帧处理

#### 2.2 CDN回退机制

```javascript
const cdnUrls = [
  "https://cdn.jsdelivr.net/npm/pinyin-pro@3.28.0/+esm",      // 主CDN
  "https://cdn.jsdelivr.net/npm/pinyin-pro@3.21.0/+esm",      // 备用版本
  "https://esm.sh/pinyin-pro@3.28.0",                          // 备用CDN
];
```

#### 2.3 性能优化

- **分帧处理**: 使用 `requestIdleCallback` 避免长页面阻塞
- **缓存机制**: 多音字判断结果缓存到 `Map`
- **增量处理**: 通过 `data-pinyin-added` 标记避免重复处理
- **延迟加载**: 使用 `defer` 属性延迟脚本执行

#### 2.4 设置面板交互

**文件**: `docs/js/settings-panel.js`

关键功能：
- 监听拼音开关 checkbox 变化
- 切换 `body.pinyin-off` class
- 使用 `localStorage` 持久化设置
- 默认状态：开启

```javascript
// 拼音显示开关
if (pinyinCheckbox) {
    pinyinCheckbox.addEventListener('change', function() {
        const isEnabled = this.checked;
        updatePinyinDisplay(isEnabled);
        localStorage.setItem('shiji-pinyin-display', isEnabled);
    });
}

function updatePinyinDisplay(enabled) {
    if (enabled) {
        document.body.classList.remove('pinyin-off');
    } else {
        document.body.classList.add('pinyin-off');
    }
}
```

### 3. CSS样式

**文件**: `docs/css/shiji-styles.css` (行 245-298)

#### 3.1 Ruby标注基础样式

```css
ruby {
    ruby-position: over;
    ruby-align: center;
    margin: 0 0.03em;  /* ruby元素之间的左右间距 */
}
```

#### 3.2 拼音文本样式

```css
rt.pinyin-rt {
    font-family: system-ui, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 0.5em;
    font-weight: 400;
    color: #7a6e62;
    letter-spacing: 0.03em;  /* 拼音字母间距 */
    line-height: 1.2;
    padding: 0 0.08em;  /* 拼音左右padding */
}
```

#### 3.3 标题中的拼音

```css
h1 rt.pinyin-rt,
h2 rt.pinyin-rt,
h3 rt.pinyin-rt {
    font-size: 0.55em;
    color: #6a5a4a;
    padding: 0 0.1em;
}
```

#### 3.4 汉字样式

```css
ruby .hanzi {
    letter-spacing: 0.02em;  /* 汉字间距 */
}
```

#### 3.5 拼音开关功能

```css
/* 关闭拼音时隐藏所有 rt 元素 */
body.pinyin-off rt.pinyin-rt {
    display: none;
}

/* 开启拼音时增加行高以适应ruby标注 */
body:not(.pinyin-off) p,
body:not(.pinyin-off) li,
body:not(.pinyin-off) blockquote {
    line-height: 2.2;
}

body:not(.pinyin-off) h1,
body:not(.pinyin-off) h2,
body:not(.pinyin-off) h3 {
    line-height: 1.8;
}
```

#### 3.6 间距参数说明

| 参数 | 值 | 说明 |
|------|------|------|
| `ruby margin` | 0.03em | Ruby元素之间的间距 |
| `rt padding` | 0.08em (正文) / 0.1em (标题) | 拼音左右内边距 |
| `rt letter-spacing` | 0.03em | 拼音字母间距 |
| `hanzi letter-spacing` | 0.02em | 汉字间距 |
| `line-height` | 2.2 (正文) / 1.8 (标题) | 行高适配 |

### 4. HTML生成集成

**文件**: `render_shiji_html.py`

#### 4.1 模板集成点

在HTML模板的 `<head>` 部分（第793行）：

```python
<script defer src="../js/heading-pinyin.js"></script>
```

在设置面板部分（第808-811行）：

```python
<label class="setting-item">
    <input type="checkbox" id="pinyin-display" checked>
    <span>拼音注释</span>
</label>
```

#### 4.2 生成命令

```bash
# 生成单个章节
python render_shiji_html.py chapter_md/001_五帝本纪.tagged.md docs/chapters/001_五帝本纪.html

# 批量生成所有章节
python generate_all_chapters.py
```

## 功能特性

### 1. 覆盖范围

| 元素类型 | 选择器 | 说明 |
|---------|--------|------|
| 一级标题 | `h1` | 章节主标题 |
| 二级标题 | `h2` | 大节标题 |
| 三级标题 | `h3` | 小节标题（如"赞"） |
| 段落 | `body p` | 正文段落 |
| 引用块 | `body blockquote` | 韵文、对话等 |
| 列表项 | `body li` | 列表项内容 |

**排除范围**:
- 导航栏 (`nav` 内元素)
- 段落编号 (`a.para-num`)
- 原文链接 (`a.original-text-link`)
- 脚本和样式标签

### 2. 专名处理

- **识别**: 通过 `a.entity-link` 选择器识别知识图谱标注的专名
- **递归跟踪**: 在DOM遍历时传递 `inEntity` 标志
- **样式保持**: 专名拼音样式与普通拼音一致（不再红色强调）

### 3. 多音字处理

- **识别**: 调用 `pinyin-pro` 的 `multiple: true` 选项
- **缓存**: 使用 `Map` 缓存判断结果
- **样式**: 与普通拼音保持一致

### 4. 特殊读音处理

#### 4.1 特殊读音词表

**数据文件**: `docs/data/special-pronunciation.json`

维护史记中特殊读音词汇（古代人名、地名、族群称号等），确保读音准确。

**词表结构**:
```json
{
  "text": "冒顿",
  "pinyin": ["mò", "dú"],
  "context": "匈奴单于名",
  "note": "冒顿单于，'冒'读mò，'顿'读dú"
}
```

#### 4.2 匹配规则

- **最长匹配优先**: 词表按文本长度降序排序
- **从左到右扫描**: 顺序匹配文本
- **完全匹配**: 只有完整匹配才应用特殊读音
- **回退机制**: 未匹配时使用标准读音

#### 4.3 常见类别

| 类别 | 示例 | 标准读音 | 特殊读音 |
|------|------|----------|---------|
| 人名 | 冒顿 | mào dùn | mò dú |
| 人名 | 句践 | jù jiàn | gōu jiǎn |
| 地名 | 会稽 | huì jī | kuài jī |
| 地名 | 番禺 | fān yú | pān yú |
| 称号 | 单于 | dān yú | chán yú |
| 称号 | 阏氏 | è shì | yān zhī |
| 姓氏 | 华 | huá | huà |
| 姓氏 | 仇 | chóu | qiú |

#### 4.4 维护文档

详细说明见 `doc/pronunciation/特殊读音词表维护说明.md`

### 5. 用户控制

| 功能 | 实现方式 | 默认状态 |
|------|---------|---------|
| 开关控制 | 设置面板checkbox | 开启 |
| 状态持久化 | localStorage (`shiji-pinyin-display`) | 记住用户选择 |
| 即时生效 | CSS class切换 (`body.pinyin-off`) | 无需刷新 |

## 浏览器兼容性

### 支持的浏览器

- Chrome/Edge 85+
- Firefox 80+
- Safari 14+
- Opera 71+

### 依赖的Web标准

- HTML5 Ruby标注
- ES6+ JavaScript (async/await, 动态import)
- CSS3
- localStorage API
- requestIdleCallback API (可选，有回退)

## 已知限制

1. **网络依赖**: 需要联网加载 `pinyin-pro` 库
2. **CDN可用性**: 依赖CDN服务（已配置多镜像回退）
3. **首次加载**: 第一次加载需要下载拼音库（约100KB）
4. **浏览器缓存**: 后续访问使用浏览器缓存，性能较好

## 测试要点

### 功能测试

- [ ] 标题拼音显示正确（h1/h2/h3）
- [ ] 正文段落拼音显示正确
- [ ] 引用块拼音显示正确（如"赞"）
- [ ] 列表项拼音显示正确
- [ ] 专名链接内拼音正常
- [ ] 特殊读音词自动应用（如"冒顿单于" mò dú chán yú）
- [ ] 特殊读音鼠标悬停显示提示
- [ ] 拼音开关功能正常
- [ ] localStorage持久化正常
- [ ] 刷新页面后设置保持

### 样式测试

- [ ] 拼音与汉字对齐
- [ ] 拼音间距适中
- [ ] 行高适配正确
- [ ] 关闭拼音后行高恢复
- [ ] 不同浏览器渲染一致

### 性能测试

- [ ] 长页面无明显卡顿
- [ ] requestIdleCallback正常工作
- [ ] 重复访问加载速度快（CDN缓存）

## 故障排除

### 问题1: 拼音不显示

**可能原因**:
1. 网络连接问题，CDN无法访问
2. JavaScript加载失败
3. 拼音开关被关闭

**解决方法**:
1. 检查浏览器控制台错误信息
2. 确认CDN可访问
3. 检查设置面板中拼音选项状态

### 问题2: 拼音错位

**可能原因**:
1. CSS文件未正确加载
2. 自定义样式冲突

**解决方法**:
1. 强制刷新页面（Ctrl+F5）
2. 检查CSS加载状态
3. 检查是否有自定义样式覆盖

### 问题3: 性能问题

**可能原因**:
1. 页面内容过长
2. 浏览器不支持requestIdleCallback

**解决方法**:
1. 已内置setTimeout回退机制
2. 考虑分页显示超长内容

## 维护指南

### 调整拼音间距

修改 `docs/css/shiji-styles.css` 中的间距参数：

```css
ruby { margin: 0 0.03em; }           /* Ruby元素间距 */
rt.pinyin-rt {
    letter-spacing: 0.03em;          /* 字母间距 */
    padding: 0 0.08em;               /* 拼音padding */
}
ruby .hanzi { letter-spacing: 0.02em; } /* 汉字间距 */
```

### 调整拼音颜色

修改 `rt.pinyin-rt` 的 `color` 属性：

```css
rt.pinyin-rt {
    color: #7a6e62;  /* 正文拼音颜色 */
}

h1 rt.pinyin-rt,
h2 rt.pinyin-rt,
h3 rt.pinyin-rt {
    color: #6a5a4a;  /* 标题拼音颜色 */
}
```

### 更新拼音库版本

修改 `docs/js/heading-pinyin.js` 中的CDN URL：

```javascript
const cdnUrls = [
  "https://cdn.jsdelivr.net/npm/pinyin-pro@新版本号/+esm",
  // ...
];
```

### 添加新的元素类型

在 `init()` 函数中添加新的选择器：

```javascript
document.querySelectorAll("body 新选择器").forEach(collectFlowElement);
```

## 相关Issue

- #25: 希望增加拼音注释，方便阅读

## 更新历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-03-31 | 初始版本，实现Ruby标注方式的拼音显示 |

## 参考资源

- [HTML Ruby标注规范](https://www.w3.org/TR/html52/textlevel-semantics.html#the-ruby-element)
- [pinyin-pro文档](https://github.com/zh-lx/pinyin-pro)
- [CSS Ruby Layout](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_ruby_layout)
