# 报错按钮功能说明

## 功能概述

在所有章节页面的右上角，除了设置按钮（⚙️）外，现在还有一个浮动的报错按钮（🐛）。

用户在阅读过程中发现任何问题（标注错误、显示问题、内容疑问等），可以点击此按钮快速提交Issue到GitHub。

## 位置和样式

- **位置**：固定在页面右上角，设置按钮（⚙️）下方
- **图标**：🐛 (Bug emoji)
- **交互**：hover时放大，保持与设置按钮一致的视觉风格

## 工作流程

1. **用户点击报错按钮**
2. **自动打开GitHub Issues页面**，并预填充以下信息：
   - Issue标题：`[报错] 当前页面标题`
   - Issue标签：`bug,用户报告`
   - Issue正文模板：
     ```
     ### 问题描述
     [请描述您发现的问题]

     ### 页面位置
     - 页面: 当前页面标题
     - URL: 当前页面URL

     ### 截图
     [请在此处粘贴截图]

     ### 其他信息
     [如有其他补充信息请在此处说明]
     ```

3. **用户补充信息**：
   - 描述问题
   - 截屏粘贴（推荐）
   - 提交Issue

## 技术实现

### 文件结构

```
docs/
├── js/
│   ├── report-issue-button.js  # 新增：报错按钮功能
│   └── shiji-imports.js        # 已更新：导入报错按钮
└── css/
    └── shiji-styles.css        # 已更新：报错按钮样式
```

### 自动加载

所有章节HTML文件已通过 `shiji-imports.js` 自动加载此功能，无需手动添加。

### 代码位置

- **JavaScript**: [docs/js/report-issue-button.js](js/report-issue-button.js)
- **CSS样式**: [docs/css/shiji-styles.css](css/shiji-styles.css) (搜索 `#report-issue-button`)
- **导入配置**: [docs/js/shiji-imports.js](js/shiji-imports.js)

## 用户指引

在README.md中已添加两处"报告问题"链接：
1. 顶部导航栏
2. 在线阅读器章节

提示用户推荐使用"截屏+paste"方式报告问题，这是最简单直观的方式。

## 响应式设计

- **桌面端**：按钮定位在内容区域右侧
- **移动端** (< 960px)：按钮回退到屏幕右侧固定位置

## 浏览器兼容性

- 使用标准Web API（URLSearchParams, window.open）
- 兼容所有现代浏览器
- 无第三方依赖
