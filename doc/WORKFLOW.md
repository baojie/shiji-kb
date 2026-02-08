# 史记知识库开发工作流程

完整的开发、质量检查和发布流程文档。

---

## 📋 目录

1. [开发流程](#开发流程)
2. [质量检查](#质量检查)
3. [发布流程](#发布流程)
4. [常用命令](#常用命令)
5. [故障排除](#故障排除)

---

## 🔧 开发流程

### 1. 编辑Markdown文件

```bash
# 编辑章节内容
vim chapter_md/001_五帝本纪.tagged.md

# 检查编辑后的文件
python3 lint_markdown.py chapter_md/001_五帝本纪.tagged.md
```

**编辑规范：**
- 使用11类实体标注（`@人名@`, `=地名=`, etc.）
- 段落编号格式：`[1]`, `[1.1]`, `[1.1.1]`
- 小节标题：`## 小节名称`（有意义的名称）
- 对话引用：`> 引用内容`

### 2. 添加小节标题

有两种方式：

**方式A：手动添加**
```bash
# 查看章节结构，确定分节点
python3 add_sections_to_chapter.py chapter_md/061_伯夷列传.tagged.md

# 在适当位置添加 ## 小节标题
```

**方式B：AI辅助**（推荐用于复杂章节）
```bash
# 使用Task agent处理
# 参考之前的agent a300d97的方法
```

### 3. 提取小节数据

```bash
# 提取所有章节的小节信息
python3 extract_all_sections.py

# 更新Index页面的小节链接
python3 update_index_with_sections.py
```

### 4. 生成HTML预览

```bash
# 生成所有章节的HTML（自动运行质量检查）
python3 generate_all_chapters.py

# 生成的HTML在 docs/chapters/ 目录
# 质量检查结果会自动显示
```

---

## ✅ 质量检查

### 自动检查（推荐）

质量检查已集成到生成脚本中，会自动运行：

```bash
# 生成时自动检查
python3 generate_all_chapters.py
# 输出末尾会显示: ✅ HTML质量检查通过

# 发布时自动检查
./publish_to_docs.sh
# 步骤8-9会运行质量检查
```

### 手动检查

需要单独检查某些文件时：

```bash
# 检查Markdown文件
python3 lint_markdown.py chapter_md/001_五帝本纪.tagged.md
python3 lint_markdown.py chapter_md/  # 检查整个目录

# 检查HTML文件
python3 lint_html.py docs/chapters/001_五帝本纪.html
python3 lint_html.py docs/chapters/  # 检查整个目录
python3 lint_html.py docs/index.html  # 检查首页

# 检查统计报告
python3 lint_markdown.py chapter_md/ > lint_report.txt 2>&1
python3 lint_html.py docs/chapters/ >> lint_report.txt 2>&1
```

### 检查项目

**Markdown检查：**
- ✓ 实体标注语法（11类）
- ✓ 段落编号连续性
- ✓ 标题层级结构
- ✓ 特殊字符和编码

**HTML检查：**
- ✓ HTML标签闭合
- ✓ Purple Numbers完整性
- ✓ 导航链接正确性
- ✓ CSS/JS资源引用
- ✓ 页面元数据

### 修复常见问题

```bash
# 修复HTML标题中的.tagged后缀
./fix_html_titles.sh

# 修复导航链接（已集成到publish脚本）
# 由 publish_to_docs.sh 自动处理
```

---

## 🚀 发布流程

### 一键发布（推荐）

```bash
# 完整的发布流程（包含质量检查）
./publish_to_docs.sh

# 脚本会自动：
# 1. 准备docs目录结构
# 2. 复制CSS/JS文件
# 3. 生成所有章节HTML
# 4. 移除.tagged后缀
# 5. 修复路径引用
# 6. 修复导航链接
# 7. 更新index.html
# 8-9. 运行质量检查 ✨

# 然后按提示推送到GitHub
git add docs/
git commit -m "Update GitHub Pages content"
git push
```

### 分步发布（调试用）

```bash
# 步骤1: 生成HTML
python3 generate_all_chapters.py

# 步骤2: 重命名文件
cd docs/chapters
for file in *.tagged.html; do
    mv "$file" "${file/.tagged.html/.html}"
done
cd ../..

# 步骤3: 修复路径
cd docs/chapters
for file in *.html; do
    sed -i 's|href="../docs/index.html"|href="../index.html"|g' "$file"
    sed -i 's|href="\([0-9]\{3\}_[^"]*\)\.tagged\.html"|href="\1.html"|g' "$file"
done
cd ../..

# 步骤4: 质量检查
python3 lint_html.py docs/chapters/

# 步骤5: 推送
git add docs/
git commit -m "Update content"
git push
```

---

## 🛠️ 常用命令

### 开发命令

```bash
# 快速检查当前工作
git status

# 查看小节覆盖情况
python3 -c "
import json
data = json.load(open('sections_data.json'))
print(f'有小节的章节: {len(data)}/130')
"

# 统计实体数量
python3 analyze_word_frequency.py
```

### 质量检查命令

```bash
# 快速检查所有文件
python3 lint_markdown.py chapter_md/ | grep "总计:"
python3 lint_html.py docs/chapters/ | grep "总计:"

# 只显示错误（不含警告）
python3 lint_html.py docs/chapters/ 2>&1 | grep "❌"

# 保存完整报告
python3 lint_markdown.py chapter_md/ > /tmp/md_lint.txt 2>&1
python3 lint_html.py docs/chapters/ > /tmp/html_lint.txt 2>&1
```

### Git命令

```bash
# 查看最近的提交
git log --oneline -10

# 查看某个文件的修改历史
git log --follow docs/index.html

# 恢复误删的文件
git checkout HEAD -- docs/index.html

# 查看未提交的更改
git diff
git diff --cached  # 查看已暂存的更改
```

---

## 🔍 故障排除

### 问题1: Lint检查报告太多警告

**症状：** lint_html.py显示100+警告

**原因：**
- HTML标题包含`.tagged`后缀
- 导航链接包含`.tagged.html`

**解决：**
```bash
./fix_html_titles.sh
./publish_to_docs.sh  # 自动修复导航链接
```

---

### 问题2: Index页面设计丢失

**症状：** index.html变成简单列表

**原因：** 被 generate_all_chapters.py 覆盖

**解决：**
```bash
# 从模板恢复
cp docs/index.html.template docs/index.html

# 或从Git历史恢复
git checkout d4bfcb4 -- docs/index.html
```

**预防：** 脚本已添加保护，会自动检测详细设计版本并跳过覆盖

---

### 问题3: Purple Numbers点击无效

**症状：** 点击段落编号不能复制链接

**原因：** purple-numbers.js未加载

**解决：**
```bash
# 检查JS文件是否存在
ls -lh docs/js/purple-numbers.js

# 检查HTML引用
grep "purple-numbers.js" docs/chapters/001_五帝本纪.html

# 重新发布
./publish_to_docs.sh
```

---

### 问题4: 小节链接不显示

**症状：** Index页面没有小节快速链接

**原因：**
1. 章节Markdown文件没有`## 小节标题`
2. sections_data.json未更新

**解决：**
```bash
# 1. 添加小节标题到Markdown
vim chapter_md/061_伯夷列传.tagged.md
# 添加 ## 小节名称

# 2. 重新提取小节
python3 extract_all_sections.py

# 3. 更新Index
python3 update_index_with_sections.py

# 4. 重新生成HTML
python3 generate_all_chapters.py
```

---

### 问题5: Git push被拒绝

**症状：** `! [rejected] main -> main (fetch first)`

**原因：** 远程仓库有新提交

**解决：**
```bash
# 拉取远程更改
git pull --rebase

# 解决冲突（如果有）
git status
# 编辑冲突文件
git add <解决的文件>
git rebase --continue

# 重新推送
git push
```

---

## 📊 项目状态检查

### 快速状态检查脚本

```bash
#!/bin/bash
# 保存为 check_status.sh

echo "========== 项目状态检查 =========="
echo ""

# 1. Markdown文件
md_count=$(ls chapter_md/*.tagged.md 2>/dev/null | wc -l)
echo "Markdown文件: $md_count / 130"

# 2. HTML文件
html_count=$(ls docs/chapters/*.html 2>/dev/null | wc -l)
echo "HTML文件: $html_count / 130"

# 3. 小节覆盖
if [ -f "sections_data.json" ]; then
    section_count=$(python3 -c "import json; print(len(json.load(open('sections_data.json'))))")
    echo "有小节章节: $section_count / 130"
fi

# 4. Git状态
uncommitted=$(git status --short | wc -l)
echo "未提交文件: $uncommitted"

# 5. 质量检查
echo ""
echo "运行快速质量检查..."
python3 lint_html.py docs/chapters/ 2>&1 | grep "总计:"

echo ""
echo "========== 检查完成 =========="
```

---

## 🎯 最佳实践

### 开发习惯

1. **频繁提交** - 每完成一个章节就提交
   ```bash
   git add chapter_md/001_五帝本纪.tagged.md
   git commit -m "完成001_五帝本纪的实体标注"
   ```

2. **运行检查** - 编辑后立即检查
   ```bash
   python3 lint_markdown.py chapter_md/001_五帝本纪.tagged.md
   ```

3. **增量发布** - 不要积累太多更改才发布
   ```bash
   # 每完成5-10个章节就发布一次
   ./publish_to_docs.sh
   git push
   ```

### 质量保证

1. **自动化优先** - 使用集成的lint检查
2. **修复所有错误** - 警告可以保留，但错误必须修复
3. **保护设计** - 不要手动编辑生成的HTML
4. **备份重要文件** - Index页面等关键文件要有备份

### 团队协作

1. **清晰的提交信息**
   ```bash
   git commit -m "添加061-070列传的小节划分"
   ```

2. **Pull before Push**
   ```bash
   git pull --rebase
   git push
   ```

3. **使用分支**（可选）
   ```bash
   git checkout -b feature/add-sections-061-070
   # 工作...
   git push -u origin feature/add-sections-061-070
   # 创建PR
   ```

---

## 📚 相关文档

- [LINT_GUIDE.md](LINT_GUIDE.md) - Lint工具详细使用指南
- [docs/README_INDEX_PROTECTION.md](docs/README_INDEX_PROTECTION.md) - Index设计保护说明
- [README.md](README.md) - 项目总体说明
- [doc/ENTITY_TAGGING_SCHEME.md](doc/ENTITY_TAGGING_SCHEME.md) - 实体标注规范

---

**创建时间**: 2026-02-08
**版本**: 1.0
**维护者**: 史记知识库项目组
