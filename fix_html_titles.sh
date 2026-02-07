#!/bin/bash
# 批量修复HTML文件标题中的.tagged后缀

echo "修复HTML文件标题中的.tagged后缀..."

fixed_count=0

for file in docs/chapters/*.html; do
    if grep -q '<title>.*\.tagged</title>' "$file"; then
        # 移除标题中的.tagged
        sed -i 's|<title>\([^<]*\)\.tagged</title>|<title>\1</title>|g' "$file"
        fixed_count=$((fixed_count + 1))
        echo "  ✓ $(basename "$file")"
    fi
done

echo ""
echo "=========================================="
echo "已修复 $fixed_count 个文件的标题"
echo "=========================================="
