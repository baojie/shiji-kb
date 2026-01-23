# 史记知识库 - GitHub Pages

本目录包含《史记》知识库的在线展示版本。

## 文件结构

```
site/
├── index.html          # 主索引页面
├── css/                # 样式文件
│   └── shiji-styles.css
├── chapters/           # 章节 HTML 文件
│   ├── 001_五帝本纪.tagged.html
│   ├── 002_夏本纪.tagged.html
│   ├── 003_殷本纪.tagged.html
│   └── 004_周本纪.tagged.html
└── .nojekyll          # 禁用 Jekyll 处理
```

## 在线访问

配置 GitHub Pages 后，可以通过以下 URL 访问：
- `https://[username].github.io/[repository]/`

## 本地预览

在项目根目录运行：

```bash
# 使用 Python 启动简单 HTTP 服务器
cd site
python3 -m http.server 8000
```

然后在浏览器访问 `http://localhost:8000`

## 功能特点

- 命名实体标注（人名、地名、官职、朝代等）
- 段落编号系统
- 对话内容样式标识
- 响应式设计，支持移动端浏览
