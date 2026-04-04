# SKILL_01d3 技术实现细节

> **参考文档**：前端Ruby标注技术、性能优化策略、故障排除指南

---

## 一、前端Ruby标注技术

### 1.1 HTML5 Ruby标准

**Ruby标注**是HTML5标准元素，用于为东亚文字添加注音。

**基本结构**：

```html
<ruby>
  <span class="hanzi">史</span>
  <rt class="pinyin-rt">shǐ</rt>
</ruby>
```

**渲染效果**：

```
  shǐ
  史
```

### 1.2 实现架构

**核心文件**：

| 文件 | 功能 | 行数 |
|------|------|------|
| `docs/js/heading-pinyin.js` | 拼音标注核心逻辑 | ~300行 |
| `docs/js/settings-panel.js` | 拼音开关控制 | ~100行 |
| `docs/css/shiji-styles.css` (L245-298) | Ruby标注样式 | 54行 |

**技术栈**：
- **前端库**：pinyin-pro（JavaScript拼音库）
- **数据格式**：JSON（特殊读音词表）
- **渲染引擎**：纯JavaScript（无依赖框架）

### 1.3 标注流程

```
1. 页面加载
   ↓
2. 加载 special-pronunciation.json
   ↓
3. 扫描DOM（h1, h2, h3, p, blockquote, li）
   ↓
4. 逐字处理
   ├─ 匹配特殊词表（长词优先）
   │  ├─ 匹配成功 → 应用特殊读音
   │  └─ 匹配失败 → 使用pinyin-pro
   ↓
5. 插入<ruby>标签
   ↓
6. 应用CSS样式
```

### 1.4 核心代码片段

**特殊词表匹配**（heading-pinyin.js）：

```javascript
// 按词长降序排序（优先匹配长词）
const sortedEntries = entries.sort((a, b) =>
  b.text.length - a.text.length
);

// 从左到右扫描文本
let i = 0;
while (i < text.length) {
  let matched = false;

  // 尝试匹配特殊词表
  for (const entry of sortedEntries) {
    if (text.substr(i, entry.text.length) === entry.text) {
      // 应用特殊读音
      applySpecialPronunciation(entry);
      i += entry.text.length;
      matched = true;
      break;
    }
  }

  // 未匹配则使用默认读音
  if (!matched) {
    const char = text[i];
    const py = pinyin(char, { toneType: 'symbol' });
    addRubyTag(char, py);
    i++;
  }
}
```

**Ruby标签生成**：

```javascript
function addRubyTag(char, py) {
  const ruby = document.createElement('ruby');
  const hanzi = document.createElement('span');
  const rt = document.createElement('rt');

  hanzi.className = 'hanzi';
  hanzi.textContent = char;

  rt.className = 'pinyin-rt';
  rt.textContent = py;

  ruby.appendChild(hanzi);
  ruby.appendChild(rt);

  return ruby;
}
```

---

## 二、CSS样式设计

### 2.1 Ruby标注样式

**文件**：`docs/css/shiji-styles.css` (L245-298)

**核心样式**：

```css
/* Ruby容器 */
ruby {
  ruby-position: over;  /* 拼音显示在上方 */
  display: inline-flex;
  flex-direction: column;
  align-items: center;
}

/* 拼音注音 */
.pinyin-rt {
  font-size: 0.5em;     /* 拼音字号为汉字的50% */
  font-weight: normal;
  color: #666;          /* 灰色，不抢眼 */
  line-height: 1.2;
  margin-bottom: 2px;
}

/* 汉字 */
.hanzi {
  font-size: 1em;
  line-height: 1.8;
}

/* 标题中的拼音样式调整 */
h1 .pinyin-rt,
h2 .pinyin-rt,
h3 .pinyin-rt {
  font-size: 0.4em;     /* 标题拼音更小 */
  margin-bottom: 3px;
}
```

### 2.2 拼音开关控制

**隐藏拼音**：

```css
body.hide-pinyin .pinyin-rt {
  display: none;
}
```

**JavaScript切换**：

```javascript
// settings-panel.js
function togglePinyin(showPinyin) {
  if (showPinyin) {
    document.body.classList.remove('hide-pinyin');
  } else {
    document.body.classList.add('hide-pinyin');
  }

  // 保存到localStorage
  localStorage.setItem('showPinyin', showPinyin);
}
```

### 2.3 响应式设计

**移动端优化**：

```css
@media (max-width: 768px) {
  .pinyin-rt {
    font-size: 0.45em;  /* 移动端拼音稍大 */
  }

  ruby {
    margin: 0 1px;      /* 增加字间距 */
  }
}
```

---

## 三、性能优化

### 3.1 加载优化

**问题**：词表加载阻塞渲染

**优化方案**：

```javascript
// 异步加载词表
async function loadPronunciationDict() {
  const response = await fetch('/data/special-pronunciation.json');
  const data = await response.json();
  return data.entries;
}

// 渐进式渲染
async function initPinyin() {
  // 先使用默认读音渲染
  renderWithDefaultPronunciation();

  // 异步加载词表
  const entries = await loadPronunciationDict();

  // 替换特殊读音
  updateWithSpecialPronunciation(entries);
}
```

### 3.2 匹配优化

**问题**：词表匹配O(n*m)复杂度

**优化方案1：Trie树**（未实现）

```javascript
class TrieNode {
  constructor() {
    this.children = {};
    this.entry = null;
  }
}

class PronunciationTrie {
  constructor(entries) {
    this.root = new TrieNode();
    this.build(entries);
  }

  // 构建Trie树
  build(entries) {
    for (const entry of entries) {
      let node = this.root;
      for (const char of entry.text) {
        if (!node.children[char]) {
          node.children[char] = new TrieNode();
        }
        node = node.children[char];
      }
      node.entry = entry;
    }
  }

  // 最长匹配
  longestMatch(text, start) {
    let node = this.root;
    let lastMatch = null;
    let matchLen = 0;

    for (let i = start; i < text.length; i++) {
      const char = text[i];
      if (!node.children[char]) break;

      node = node.children[char];
      if (node.entry) {
        lastMatch = node.entry;
        matchLen = i - start + 1;
      }
    }

    return { entry: lastMatch, length: matchLen };
  }
}
```

**优化方案2：HashMap预处理**

```javascript
// 构建词条索引
const entryMap = new Map();
for (const entry of entries) {
  entryMap.set(entry.text, entry);
}

// O(1)查找
function findEntry(text, start, maxLen) {
  for (let len = maxLen; len >= 1; len--) {
    const substr = text.substr(start, len);
    if (entryMap.has(substr)) {
      return entryMap.get(substr);
    }
  }
  return null;
}
```

### 3.3 渲染优化

**问题**：大量DOM操作导致页面卡顿

**优化方案**：DocumentFragment批量插入

```javascript
function renderPinyin(container, text, entries) {
  const fragment = document.createDocumentFragment();

  // 批量生成Ruby标签
  let i = 0;
  while (i < text.length) {
    const ruby = createRubyTag(text, i, entries);
    fragment.appendChild(ruby);
    i += ruby.dataset.charLen || 1;
  }

  // 一次性插入DOM
  container.innerHTML = '';
  container.appendChild(fragment);
}
```

---

## 四、故障排除

### 4.1 常见问题

#### 问题1：拼音不显示

**症状**：页面加载后没有拼音标注

**排查步骤**：

1. 检查控制台错误
   ```javascript
   // 查看是否有加载错误
   console.log('Pinyin script loaded:', typeof applyPinyin !== 'undefined');
   ```

2. 检查词表加载
   ```javascript
   fetch('/data/special-pronunciation.json')
     .then(r => r.json())
     .then(d => console.log('Dictionary loaded:', d.entries.length))
     .catch(e => console.error('Failed to load:', e));
   ```

3. 检查拼音开关
   ```javascript
   console.log('Show pinyin:', localStorage.getItem('showPinyin'));
   ```

**解决方案**：
- 确保`heading-pinyin.js`正确引入
- 检查词表路径是否正确
- 清除localStorage重置设置

#### 问题2：特殊读音不生效

**症状**：特殊词汇使用了默认读音

**排查步骤**：

1. 检查词条格式
   ```json
   {
     "text": "冒顿",  // 完全匹配原文
     "pinyin": ["mò", "dú"],  // 数组长度必须匹配
     "context": "匈奴单于名",
     "note": "..."
   }
   ```

2. 检查匹配逻辑
   ```javascript
   console.log('Matching:', text.substr(i, entry.text.length) === entry.text);
   ```

3. 检查词长排序
   ```javascript
   console.log('Entry order:', entries.map(e => e.text.length));
   ```

**解决方案**：
- 确保text字段完全匹配
- pinyin数组长度与text长度一致
- 词表按长度降序排序

#### 问题3：页面加载慢

**症状**：拼音标注导致页面卡顿

**性能分析**：

```javascript
console.time('Pinyin rendering');
applyPinyin();
console.timeEnd('Pinyin rendering');
```

**优化建议**：
- 减少词表规模（Lint清理）
- 使用DocumentFragment批量插入
- 考虑Web Worker异步处理

### 4.2 调试工具

**浏览器控制台命令**：

```javascript
// 查看当前词表
fetch('/data/special-pronunciation.json')
  .then(r => r.json())
  .then(d => console.table(d.entries));

// 测试单字拼音
const { pinyin } = require('pinyin-pro');  // Node环境
console.log(pinyin('称王', { type: 'array' }));

// 强制重新渲染
applyPinyin();

// 清除设置
localStorage.clear();
location.reload();
```

---

## 五、扩展功能

### 5.1 拼音样式切换

**需求**：用户选择不同拼音样式（带声调/不带声调/数字声调）

**实现**：

```javascript
const pinyinStyles = {
  symbol: { toneType: 'symbol' },   // shǐ
  none: { toneType: 'none' },       // shi
  num: { toneType: 'num' }          // shi3
};

function setPinyinStyle(style) {
  const config = pinyinStyles[style];
  // 重新渲染所有拼音
  document.querySelectorAll('.pinyin-rt').forEach(rt => {
    const char = rt.previousElementSibling.textContent;
    rt.textContent = pinyin(char, config);
  });
}
```

### 5.2 拼音大小调节

**需求**：用户调整拼音字号

**实现**：

```css
:root {
  --pinyin-size: 0.5em;
}

.pinyin-rt {
  font-size: var(--pinyin-size);
}
```

```javascript
function setPinyinSize(size) {
  document.documentElement.style.setProperty('--pinyin-size', size + 'em');
  localStorage.setItem('pinyinSize', size);
}
```

### 5.3 导出带拼音文本

**需求**：导出纯文本格式的拼音标注

**实现**：

```javascript
function exportPinyinText() {
  const content = document.querySelector('article');
  const rubies = content.querySelectorAll('ruby');

  let text = '';
  rubies.forEach(ruby => {
    const hanzi = ruby.querySelector('.hanzi').textContent;
    const py = ruby.querySelector('.pinyin-rt').textContent;
    text += `${hanzi}(${py})`;
  });

  return text;
}
```

---

## 六、测试策略

### 6.1 单元测试

**测试框架**：Jest（待实现）

**测试用例**：

```javascript
describe('Pinyin Annotation', () => {
  test('should match special pronunciation', () => {
    const entries = [
      { text: '冒顿', pinyin: ['mò', 'dú'] }
    ];
    const result = matchSpecialPronunciation('冒顿单于', 0, entries);
    expect(result.entry.text).toBe('冒顿');
    expect(result.length).toBe(2);
  });

  test('should prioritize longer matches', () => {
    const entries = [
      { text: '车骑将军', pinyin: ['chē', 'jì', 'jiàng', 'jūn'] },
      { text: '车骑', pinyin: ['chē', 'jì'] }
    ];
    const result = matchSpecialPronunciation('车骑将军', 0, entries);
    expect(result.entry.text).toBe('车骑将军');
  });
});
```

### 6.2 集成测试

**测试场景**：
1. 页面加载后拼音正常显示
2. 特殊词汇读音正确
3. 拼音开关功能正常
4. 设置持久化到localStorage

**E2E测试**（Playwright）：

```javascript
test('pinyin annotation works', async ({ page }) => {
  await page.goto('/chapters/001.html');

  // 检查拼音是否显示
  const pinyinCount = await page.locator('.pinyin-rt').count();
  expect(pinyinCount).toBeGreaterThan(0);

  // 检查特殊读音
  const maodun = await page.locator('text=冒顿').first();
  const py = await maodun.locator('.pinyin-rt').textContent();
  expect(py).toBe('mò dú');

  // 测试开关
  await page.click('#pinyin-toggle');
  const visible = await page.locator('.pinyin-rt').isVisible();
  expect(visible).toBe(false);
});
```

---

## 七、相关文档

- [SKILL_01d_正音与拼音标注](../SKILL_01d_正音与拼音标注.md) - 主文档
- [SKILL_01d1_词表设计原则详解](./SKILL_01d1_词表设计原则详解.md) - 设计原则
- [SKILL_01d2_史记正义提取方法](./SKILL_01d2_史记正义提取方法.md) - 提取方法

## 八、参考资源

### 技术文档

- [HTML5 Ruby标准](https://www.w3.org/TR/html5/text-level-semantics.html#the-ruby-element)
- [pinyin-pro文档](https://github.com/zh-lx/pinyin-pro)
- [CSS Ruby Layout](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_ruby_layout)

### 工具库

- [pinyin-pro](https://github.com/zh-lx/pinyin-pro) - JavaScript拼音库
- [pypinyin](https://github.com/mozillazg/python-pinyin) - Python拼音库（服务端）
