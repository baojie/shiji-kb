#!/bin/bash
# 一键发布脚本：生成HTML并发布到 GitHub Pages
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

# 生成所有章节HTML（带 .tagged.html 后缀）
# 注意：generate_all_chapters.py 已添加保护机制，
#       不会覆盖已存在的详细设计版 index.html
echo "4. 生成所有章节HTML文件..."
python generate_all_chapters.py

# 在 docs/chapters/ 中重命名文件：移除 .tagged 后缀
echo "5. 移除文件名中的 .tagged 后缀..."
cd docs/chapters
renamed_count=0
for file in *.tagged.html; do
    if [ -f "$file" ]; then
        newname="${file/.tagged.html/.html}"
        mv "$file" "$newname"
        renamed_count=$((renamed_count + 1))
    fi
done
echo "   已重命名 $renamed_count 个文件"
cd ../..

# 修复 HTML 文件中的 CSS 路径和原文链接路径
echo "6. 修复 HTML 文件中的路径引用..."
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
    # 修复导航链接：移除章节链接中的 .tagged 后缀
    sed -i 's|href="\([0-9]\{3\}_[^"]*\)\.tagged\.html"|href="\1.html"|g' "$file"
done
cd ../..

# 更新索引页面中的链接（移除 .tagged 后缀）
echo "7. 更新索引页面中的链接..."
if [ -f "docs/index.html" ]; then
    sed -i 's|\.tagged\.html|.html|g' docs/index.html
    echo "   已更新 index.html 中的章节链接"
fi

# 确保 .nojekyll 文件存在
if [ ! -f "docs/.nojekyll" ]; then
    echo "8. 创建 .nojekyll 文件..."
    touch docs/.nojekyll
fi

# 统计文件数量
html_count=$(ls -1 docs/chapters/*.html 2>/dev/null | wc -l)

echo ""
echo "=========================================="
echo "  发布完成！"
echo "=========================================="
echo "已生成并处理 $html_count 个 HTML 文件"
echo "所有文件已移除 .tagged 后缀"
echo "CSS 文件已更新到 docs/css/"
echo "JS 文件已更新到 docs/js/"
echo ""
echo "下一步："
echo "  git add docs/"
echo "  git commit -m \"Update GitHub Pages content\""
echo "  git push"
echo ""
