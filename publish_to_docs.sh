#!/bin/bash
# 一键发布脚本：从 chapter_md 同步到 docs 目录
# 用法: ./publish_to_docs.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  史记知识库 - 发布到 GitHub Pages"
echo "=========================================="
echo ""

# 检查目录是否存在
if [ ! -d "chapter_md" ]; then
    echo "错误: chapter_md 目录不存在"
    exit 1
fi

if [ ! -d "doc" ]; then
    echo "错误: doc 目录不存在"
    exit 1
fi

# 创建 docs 目录结构（如果不存在）
echo "1. 准备 docs 目录结构..."
mkdir -p docs/chapters
mkdir -p docs/css
mkdir -p docs/js

# 复制 CSS 文件
echo "2. 复制 CSS 样式文件..."
cp doc/shiji-styles.css docs/css/
cp docs/css/chapter-nav.css docs/css/ 2>/dev/null || echo "   chapter-nav.css 已存在"

# 复制 JS 文件
echo "3. 复制 JavaScript 文件..."
cp docs/js/purple-numbers.js docs/js/ 2>/dev/null || echo "   purple-numbers.js 已存在"

# 复制 HTML 文件
echo "4. 复制章节 HTML 文件..."
cp chapter_md/*.tagged.html docs/chapters/

# 修复 HTML 文件中的 CSS 路径和原文链接路径
echo "5. 修复 CSS 引用路径和原文链接路径..."
cd docs/chapters
for file in *.html; do
    # 将任何绝对路径或相对路径改为标准的相对路径
    sed -i 's|href="[^"]*shiji-styles.css"|href="../css/shiji-styles.css"|g' "$file"
    # 修复chapter-nav.css路径
    sed -i 's|href="../docs/css/chapter-nav.css"|href="../css/chapter-nav.css"|g' "$file"
    # 修复purple-numbers.js路径
    sed -i 's|src="../docs/js/purple-numbers.js"|src="../js/purple-numbers.js"|g' "$file"
    # 修复原文链接路径：从 ../docs/original_text/ 改为 ../original_text/
    sed -i 's|href="../docs/original_text/|href="../original_text/|g' "$file"
    # 修复主页链接路径：从 ../docs/index.html 改为 ../index.html
    sed -i 's|href="../docs/index.html"|href="../index.html"|g' "$file"
done
cd ../..

# 确保 .nojekyll 文件存在
if [ ! -f "docs/.nojekyll" ]; then
    echo "6. 创建 .nojekyll 文件..."
    touch docs/.nojekyll
fi

# 统计文件数量
html_count=$(ls -1 docs/chapters/*.html 2>/dev/null | wc -l)

echo ""
echo "=========================================="
echo "  发布完成！"
echo "=========================================="
echo "已复制 $html_count 个 HTML 文件到 docs/chapters/"
echo "CSS 文件已更新到 docs/css/"
echo "JS 文件已更新到 docs/js/"
echo ""
echo "下一步："
echo "  git add docs/"
echo "  git commit -m \"Update GitHub Pages content\""
echo "  git push"
echo ""
