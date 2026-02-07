# 史记知识库 Lint 工具使用指南

本项目提供两个代码质量检查工具，用于确保Markdown和HTML文件的一致性和正确性。

---

## 📝 Markdown Linter (`lint_markdown.py`)

### 检查项目

1. **实体标注语法** - 检查11类实体标注的正确性
   - 未闭合标注（如单个 `@` 符号）
   - 空标注（如 `@@`）
   - 嵌套标注（如 `@=地名=@`）

2. **段落编号** - Purple Numbers 格式和连续性
   - 编号格式（`[1]`, `[1.1]`, `[1.1.1]`）
   - 一级编号连续性
   - 非法字符

3. **标题结构** - Markdown标题层级
   - 一级标题数量（应该只有一个）
   - 标题层级跳跃（如从 `#` 直接到 `###`）
   - 标题中的段落编号

4. **引用标记** - 对话引用格式
   - `>` 开头的引用行
   - 未标记的对话（提示）

5. **特殊字符** - 编码和格式问题
   - 全角数字/标点
   - 零宽字符
   - 过长行（建议）

### 使用方法

```bash
# 检查单个文件
python3 lint_markdown.py chapter_md/001_五帝本纪.tagged.md

# 检查整个目录
python3 lint_markdown.py chapter_md/

# 检查所有已标注文件
python3 lint_markdown.py chapter_md/*.tagged.md
```

### 输出示例

```
正在检查: 001_五帝本纪.tagged.md
======================================================================

❌ 错误 (2):
  • 发现未闭合的人名标注 '@'
  • 段落编号格式错误: [1.a]

⚠️  警告 (5):
  • 空人名标注
  • 一级段落编号不连续，缺失: [5, 7]
  • 标题层级跳跃 (从 # 到 ###)
  • 有3个标题包含段落编号
  • 发现全角数字: {'１', '２'}

ℹ️  提示 (1):
  • 有5行超过200字符（建议分段）

======================================================================
总计: 2 错误, 5 警告, 1 提示
```

### 退出代码

- `0` - 无错误
- `1` - 有错误

---

## 🌐 HTML Linter (`lint_html.py`)

### 检查项目

1. **HTML结构** - 标签完整性
   - 标签闭合和嵌套
   - 必需标签（`<html>`, `<head>`, `<body>`, `<title>`）
   - HTML解析错误

2. **实体样式** - CSS类名正确性
   - 11个标准实体类名
   - 拼写错误检测
   - 未知类名警告

3. **Purple Numbers** - 段落编号链接
   - 锚点格式（`<a href="#pn-1" id="pn-1">`）
   - 编号连续性
   - href和id一致性

4. **导航链接** - 页面导航
   - 主页链接格式
   - `.tagged.html` 后缀残留
   - 上一页/下一页链接格式

5. **资源引用** - CSS/JS文件
   - 必需的CSS文件（`shiji-styles.css`, `chapter-nav.css`）
   - Purple Numbers JS文件
   - 错误的路径（如 `../docs/css/`）

6. **页面元数据**
   - 字符编码声明（UTF-8）
   - 页面标题中的 `.tagged` 后缀
   - 特殊字符转义

### 使用方法

```bash
# 检查单个HTML文件
python3 lint_html.py docs/chapters/001_五帝本纪.html

# 检查整个目录
python3 lint_html.py docs/chapters/

# 检查index.html
python3 lint_html.py docs/index.html
```

### 输出示例

```
正在检查: 006_秦始皇本纪.html
======================================================================

❌ 错误 (3):
  • 发现5个.tagged.html链接（应该已移除）
    • href="005_秦本纪.tagged.html"
    • href="007_项羽本纪.tagged.html"
  • CSS路径错误（包含docs/）: ['docs/css/shiji-styles.css']
  • 段落编号不一致: href='#pn-10' id='pn-11'

⚠️  警告 (2):
  • 页面标题包含.tagged后缀: 006_秦始皇本纪.tagged
  • 段落编号不连续，缺失: [5]

======================================================================
总计: 3 错误, 2 警告
```

---

## 🔧 集成到工作流

### 发布前检查

在运行 `publish_to_docs.sh` 之前检查文件质量：

```bash
#!/bin/bash
# pre-publish-check.sh

echo "检查Markdown文件..."
python3 lint_markdown.py chapter_md/ || exit 1

echo "生成HTML..."
./publish_to_docs.sh

echo "检查生成的HTML文件..."
python3 lint_html.py docs/chapters/ || exit 1

echo "✅ 所有检查通过，可以发布"
```

### Git Pre-commit Hook

在 `.git/hooks/pre-commit` 中添加：

```bash
#!/bin/bash
# 只检查即将提交的Markdown文件

staged_md_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.tagged\.md$')

if [ -n "$staged_md_files" ]; then
    echo "运行Markdown lint检查..."
    for file in $staged_md_files; do
        python3 lint_markdown.py "$file" || exit 1
    done
fi

echo "✅ Lint检查通过"
```

### CI/CD 集成

在GitHub Actions中：

```yaml
name: Lint Check

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Lint Markdown
        run: python3 lint_markdown.py chapter_md/
      - name: Lint HTML
        run: python3 lint_html.py docs/chapters/
```

---

## 📊 批量检查统计

检查所有文件并生成统计报告：

```bash
# Markdown统计
echo "=== Markdown文件检查 ===" > lint_report.txt
python3 lint_markdown.py chapter_md/ >> lint_report.txt 2>&1

# HTML统计
echo "\n=== HTML文件检查 ===" >> lint_report.txt
python3 lint_html.py docs/chapters/ >> lint_report.txt 2>&1

# 查看报告
cat lint_report.txt
```

---

## ⚠️ 已知问题和限制

### Markdown Linter

1. **误报**: 可能将Markdown标题的 `#` 误识别为官职标注
   - 解决方案：改进检测逻辑，排除标题行

2. **嵌套标注**: 某些合法的复杂标注可能被误报
   - 示例：`@#御史大夫#萧何@` (人名包含官职)

3. **引用检测**: 可能将非对话的"曰"误报为未标记对话
   - 这是提示级别，不影响整体检查

### HTML Linter

1. **复杂嵌套**: 对于非常复杂的HTML结构可能漏检
2. **JavaScript内容**: 不检查`<script>`标签内的JavaScript代码
3. **性能**: 大文件（>1MB）检查较慢

---

## 🔍 常见错误和修复

### 错误1: 未闭合的人名标注

```markdown
❌ 错误: @黄帝 征战四方
✅ 正确: @黄帝@ 征战四方
```

### 错误2: .tagged.html 链接残留

```html
❌ 错误: <a href="001_五帝本纪.tagged.html">
✅ 正确: <a href="001_五帝本纪.html">
```

### 错误3: CSS路径错误

```html
❌ 错误: <link href="../docs/css/shiji-styles.css">
✅ 正确: <link href="../css/shiji-styles.css">
```

### 错误4: 段落编号不一致

```html
❌ 错误: <a href="#pn-10" id="pn-11">
✅ 正确: <a href="#pn-10" id="pn-10">
```

---

## 🚀 未来改进

- [ ] 添加自动修复功能（`--fix` 参数）
- [ ] 详细模式（`-v` 参数）显示更多信息
- [ ] JSON格式输出（用于CI/CD集成）
- [ ] 自定义规则配置文件
- [ ] 增量检查（只检查修改的文件）
- [ ] IDE插件（VSCode扩展）

---

**创建时间**: 2026-02-08
**版本**: 1.0
**维护者**: 史记知识库项目组
