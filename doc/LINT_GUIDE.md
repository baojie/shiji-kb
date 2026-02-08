# 史记知识库 Lint 工具使用指南

本项目提供两个代码质量检查工具，用于确保Markdown和HTML文件的一致性和正确性。

**详细的检查项目和质量标准请参考：[FORMAT_SPECIFICATION.md](FORMAT_SPECIFICATION.md#质量标准与检查)**

---

## 📝 Markdown Linter (`lint_markdown.py`)

自动检查Markdown文件是否符合项目格式规范，包括：
- ✓ 11类实体标注语法正确性
- ✓ Purple Numbers段落编号格式
- ✓ 标题层级结构
- ✓ 引用标记格式
- ✓ 特殊字符和编码问题

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

自动检查HTML文件是否符合项目格式规范，包括：
- ✓ HTML结构完整性（标签闭合、必需标签）
- ✓ 11个实体CSS类名正确性
- ✓ Purple Numbers锚点格式
- ✓ 导航链接正确性（无.tagged残留）
- ✓ CSS/JS资源引用路径
- ✓ 页面元数据（编码、标题）

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

## 🔍 故障排除

### 常见问题

**Q: Linter报告"未闭合的人名标注"，但我看起来是闭合的？**

A: 检查是否使用了全角符号。必须使用半角 `@`，不能是全角 `＠`。

**Q: 为什么段落编号不连续会报警告？**

A: 这是正常的警告。如果你使用了多级编号（如[1], [1.1], [2]），系统会提示一级编号不连续。这可以接受，不影响发布。

**Q: HTML Linter说找不到Purple Numbers，但我能看到段落编号？**

A: 检查锚点格式是否正确：`<a href="#pn-1" id="pn-1" class="para-num">1</a>`。三个属性都必须存在且格式正确。

**Q: .tagged.html链接已经修复了，为什么还是报错？**

A: 运行 `python3 lint_html.py docs/chapters/文件名.html` 重新检查具体文件，确认错误行号。可能有多处需要修复。

---

## ⚠️ 已知限制

完整的限制说明请参考：[FORMAT_SPECIFICATION.md - 已知限制](FORMAT_SPECIFICATION.md#3-已知限制)

**Markdown Linter:**
- 可能将Markdown标题的 `#` 误识别为官职标注（已优化）
- 某些复杂嵌套标注可能误报（属于警告级别）

**HTML Linter:**
- 非常复杂的HTML结构可能漏检
- 不检查JavaScript代码内容
- 大文件（>1MB）检查较慢

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
