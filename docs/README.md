# 史记知识库 - GitHub Pages

本目录包含《史记》知识库的在线展示版本。

## 在线访问

- **首页**：https://baojie.github.io/shiji-kb
- **事件地铁图**：https://baojie.github.io/shiji-kb/app/metro/

## 文件结构

```
docs/
├── index.html              # 首页（瀑布流卡片布局）
├── css/shiji-styles.css    # 样式表
├── chapters/               # HTML格式章节（130篇）
├── entities/               # 实体索引页面（11类+event.html+总览）
├── original_text/          # 130篇原始文本
└── .nojekyll               # 禁用 Jekyll 处理
```

## 功能特点

- **认知辅助阅读**：11类命名实体语法高亮（人名、地名、官职、朝代等）
- **段落编号系统**：Purple Numbers，支持精确引用
- **对话内容样式**：引语和对话标识
- **实体索引**：11类实体索引页面（11,000+条目），正文实体可点击跳转
- **事件时间索引**：按历史分期分组的3,092个事件索引（event.html）
- **响应式设计**：支持移动端浏览

## 本地预览

```bash
cd docs
python3 -m http.server 8000
```

然后在浏览器访问 `http://localhost:8000`
