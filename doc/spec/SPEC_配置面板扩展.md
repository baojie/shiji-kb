# 配置面板扩展指南

**版本**: 1.0
**日期**: 2026-03-31
**文件**: `docs/js/settings-panel-config.js`

## 概述

配置面板采用集中配置、动态生成的设计，所有配置项定义在一个JavaScript配置文件中，HTML模板只需包含一个空的 `<div id="settings-panel"></div>` 容器即可。

**优势**：
- ✅ 添加新选项只需修改一个JS文件
- ✅ 无需修改130个HTML文件
- ✅ 所有配置项集中管理
- ✅ 自动处理localStorage持久化

## 架构设计

### 文件结构

```
docs/
  js/
    settings-panel-config.js    # 配置项定义和面板生成逻辑
    heading-pinyin.js            # 拼音功能实现
    purple-numbers.js            # 紫色编号功能实现
    ...                          # 其他功能模块
  chapters/
    001_五帝本纪.html            # HTML只包含空容器
    002_夏本纪.html
    ...
```

### HTML模板（简化）

```html
<!-- 浮动配置按钮 -->
<button id="settings-toggle" title="显示设置">⚙️</button>

<!-- 配置面板（由 settings-panel-config.js 动态生成内容） -->
<div id="settings-panel"></div>

<!-- 引入配置脚本 -->
<script src="../js/settings-panel-config.js"></script>
```

## 添加新配置选项

### 步骤1: 编辑配置数组

编辑 `docs/js/settings-panel-config.js`，在 `SETTINGS_CONFIG` 数组中添加新配置项：

```javascript
const SETTINGS_CONFIG = [
    {
        id: 'syntax-highlight',          // HTML元素ID
        label: '语法高亮',                // 显示标签
        storageKey: 'shiji-syntax-highlight',  // localStorage键名
        defaultValue: true,               // 默认值
        onChange: function(enabled) {     // 状态改变时的回调函数
            updateSyntaxHighlight(enabled);
        }
    },
    {
        id: 'pinyin-display',
        label: '拼音注释',
        storageKey: 'shiji-pinyin-display',
        defaultValue: true,
        onChange: function(enabled) {
            updatePinyinDisplay(enabled);
        }
    },
    // 添加新选项
    {
        id: 'entity-tooltip',
        label: '实体提示',
        storageKey: 'shiji-entity-tooltip',
        defaultValue: true,
        onChange: function(enabled) {
            updateEntityTooltip(enabled);  // 需要实现这个函数
        }
    }
];
```

### 步骤2: 实现onChange函数

在同一文件中添加对应的处理函数：

```javascript
/**
 * 更新实体提示显示
 */
function updateEntityTooltip(enabled) {
    if (enabled) {
        document.body.classList.remove('entity-tooltip-off');
    } else {
        document.body.classList.add('entity-tooltip-off');
    }
}
```

### 步骤3: 添加CSS样式（如需要）

编辑 `docs/css/shiji-styles.css`：

```css
/* 实体提示关闭时的样式 */
body.entity-tooltip-off .entity-popup {
    display: none !important;
}
```

### 步骤4: 重新生成HTML

```bash
# 重新生成所有章节
python generate_all_chapters.py

# 或单个章节
python render_shiji_html.py chapter_md/001_五帝本纪.tagged.md docs/chapters/001_五帝本纪.html
```

**注意**：由于配置是在JS中动态生成的，理论上不需要重新生成HTML，但如果你之前生成的HTML使用的是旧的模板（包含硬编码的选项），则需要重新生成。

## 配置项字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | HTML checkbox元素的ID，必须唯一 |
| `label` | string | ✓ | 显示给用户的文字标签 |
| `storageKey` | string | ✓ | localStorage中的键名，建议格式：`shiji-功能名` |
| `defaultValue` | boolean | ✓ | 默认启用/禁用状态 |
| `onChange` | function | ✓ | 状态改变时的回调函数，参数为 `enabled`（boolean） |

## 配置项示例

### 示例1: 简单开关（添加/移除CSS类）

```javascript
{
    id: 'footnote-display',
    label: '注释显示',
    storageKey: 'shiji-footnote-display',
    defaultValue: true,
    onChange: function(enabled) {
        if (enabled) {
            document.body.classList.remove('footnote-off');
        } else {
            document.body.classList.add('footnote-off');
        }
    }
}
```

对应CSS：
```css
body.footnote-off .footnote {
    display: none;
}
```

### 示例2: 复杂逻辑（调用外部模块）

```javascript
{
    id: 'night-mode',
    label: '夜间模式',
    storageKey: 'shiji-night-mode',
    defaultValue: false,
    onChange: function(enabled) {
        // 调用外部夜间模式模块
        if (window.ThemeManager) {
            window.ThemeManager.setNightMode(enabled);
        }
    }
}
```

### 示例3: 需要异步初始化的功能

```javascript
{
    id: 'search-index',
    label: '搜索索引',
    storageKey: 'shiji-search-index',
    defaultValue: false,
    onChange: function(enabled) {
        if (enabled) {
            // 异步加载搜索模块
            loadSearchModule().then(() => {
                window.SearchEngine.enable();
            });
        } else {
            if (window.SearchEngine) {
                window.SearchEngine.disable();
            }
        }
    }
}
```

## 高级用法

### 动态添加配置项

可以通过暴露的API动态添加配置项（例如在插件系统中）：

```javascript
// 在其他脚本中添加新配置项
window.ShijiSettings.addSetting({
    id: 'my-plugin-option',
    label: '我的插件',
    storageKey: 'shiji-my-plugin',
    defaultValue: true,
    onChange: function(enabled) {
        console.log('我的插件状态:', enabled);
    }
});
```

### 获取当前配置

```javascript
// 读取某个配置的当前值
const isPinyinEnabled = localStorage.getItem('shiji-pinyin-display') === 'true';

// 或通过checkbox状态
const checkbox = document.getElementById('pinyin-display');
const isEnabled = checkbox ? checkbox.checked : true;
```

## 测试检查清单

添加新配置项后，检查以下项目：

- [ ] 配置项在面板中正确显示
- [ ] 勾选/取消勾选功能正常
- [ ] localStorage正确保存状态
- [ ] 刷新页面后状态保持一致
- [ ] onChange函数正常执行
- [ ] CSS样式正确应用
- [ ] 不同浏览器表现一致
- [ ] 移动端显示正常

## 故障排除

### 问题1: 配置项不显示

**检查**：
- 浏览器控制台是否有JS错误
- `settings-panel-config.js` 是否正确加载
- 配置对象格式是否正确

### 问题2: 状态不持久化

**检查**：
- `storageKey` 是否唯一
- localStorage是否被禁用（隐私模式）
- 是否有其他代码清空了localStorage

### 问题3: onChange不执行

**检查**：
- 函数语法是否正确
- 是否有异常抛出（查看控制台）
- 确认checkbox的change事件已绑定

## 最佳实践

### 1. 命名规范

- **ID**: 使用kebab-case，如 `entity-highlight`
- **storageKey**: 统一前缀 `shiji-`，如 `shiji-entity-highlight`
- **CSS类**: 功能名 + `-off`，如 `entity-highlight-off`

### 2. 默认值选择

- 对用户有帮助的功能默认**开启**（如拼音注释、语法高亮）
- 资源密集型功能默认**关闭**（如全文搜索索引）
- 实验性功能默认**关闭**

### 3. 性能考虑

- onChange函数应该尽可能快速执行
- 避免在onChange中执行大量DOM操作
- 需要异步加载的功能使用懒加载

### 4. 用户体验

- 标签文字简洁明了（2-4个汉字）
- 提供tooltip说明（如需要）
- 分组相关功能（使用多个setting-group）

## 未来扩展

### 计划中的配置项

- [ ] 注释显示（三家注/索隐/正义）
- [ ] 实体高亮颜色方案
- [ ] 字体大小调节
- [ ] 行距调节
- [ ] 夜间模式
- [ ] 阅读进度保存
- [ ] 全文搜索

### 分组支持

未来可以支持配置项分组：

```javascript
const SETTINGS_GROUPS = [
    {
        title: '显示选项',
        settings: [
            { id: 'syntax-highlight', ... },
            { id: 'pinyin-display', ... }
        ]
    },
    {
        title: '高级选项',
        settings: [
            { id: 'search-index', ... },
            { id: 'debug-mode', ... }
        ]
    }
];
```

## 参考资料

- **配置脚本**: `docs/js/settings-panel-config.js`
- **HTML模板**: `render_shiji_html.py` (行796-805)
- **样式文件**: `docs/css/shiji-styles.css`
- **拼音功能**: `SKILL_01d_正音与拼音标注.md`

---

**维护者**: Claude
**最后更新**: 2026-03-31
