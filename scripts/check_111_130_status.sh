#!/bin/bash
# 检查111-130章节处理状态

echo "======================================================================"
echo "《史记》111-130列传章节处理状态检查"
echo "======================================================================"

BASE_DIR="/home/baojie/work/shiji-kb"
INPUT_DIR="$BASE_DIR/docs/original_text"
OUTPUT_DIR="$BASE_DIR/chapter_md"
PROGRESS_FILE="$BASE_DIR/progress_111_130.json"

# 定义章节列表
CHAPTERS=(
    "111_卫将军骠骑列传"
    "112_平津侯主父列传"
    "113_南越列传"
    "114_东越列传"
    "115_朝鲜列传"
    "116_西南夷列传"
    "117_司马相如列传"
    "118_淮南衡山列传"
    "119_循吏列传"
    "120_汲郑列传"
    "121_儒林列传"
    "122_酷吏列传"
    "123_大宛列传"
    "124_游侠列传"
    "125_佞幸列传"
    "126_滑稽列传"
    "127_日者列传"
    "128_龟策列传"
    "129_货殖列传"
    "130_太史公自序"
)

echo ""
echo "1. 输入文件检查"
echo "----------------------------------------------------------------------"
INPUT_COUNT=0
for chapter in "${CHAPTERS[@]}"; do
    if [ -f "$INPUT_DIR/${chapter}.txt" ]; then
        INPUT_COUNT=$((INPUT_COUNT + 1))
        SIZE=$(du -h "$INPUT_DIR/${chapter}.txt" | cut -f1)
        echo "✅ $chapter.txt ($SIZE)"
    else
        echo "❌ $chapter.txt (不存在)"
    fi
done
echo ""
echo "输入文件: $INPUT_COUNT / ${#CHAPTERS[@]}"

echo ""
echo "2. 输出文件检查"
echo "----------------------------------------------------------------------"
OUTPUT_COUNT=0
for chapter in "${CHAPTERS[@]}"; do
    if [ -f "$OUTPUT_DIR/${chapter}.tagged.md" ]; then
        OUTPUT_COUNT=$((OUTPUT_COUNT + 1))
        SIZE=$(du -h "$OUTPUT_DIR/${chapter}.tagged.md" | cut -f1)
        LINES=$(wc -l < "$OUTPUT_DIR/${chapter}.tagged.md")
        PERSONS=$(grep -o '@[^@]*@' "$OUTPUT_DIR/${chapter}.tagged.md" | wc -l)
        PLACES=$(grep -o '=[^=]*=' "$OUTPUT_DIR/${chapter}.tagged.md" | wc -l)
        echo "✅ $chapter ($SIZE, $LINES行, @人名:$PERSONS, =地名:$PLACES)"
    else
        echo "⏳ $chapter (未处理)"
    fi
done
echo ""
echo "已完成: $OUTPUT_COUNT / ${#CHAPTERS[@]}"

echo ""
echo "3. 进度文件检查"
echo "----------------------------------------------------------------------"
if [ -f "$PROGRESS_FILE" ]; then
    echo "✅ 进度文件存在: $PROGRESS_FILE"
    echo ""
    echo "内容:"
    cat "$PROGRESS_FILE"
else
    echo "⏳ 进度文件不存在（首次运行时会自动创建）"
fi

echo ""
echo "4. 待处理章节"
echo "----------------------------------------------------------------------"
PENDING_COUNT=0
for chapter in "${CHAPTERS[@]}"; do
    if [ ! -f "$OUTPUT_DIR/${chapter}.tagged.md" ]; then
        PENDING_COUNT=$((PENDING_COUNT + 1))
        echo "⏳ $chapter"
    fi
done

if [ $PENDING_COUNT -eq 0 ]; then
    echo "✅ 全部章节已完成！"
else
    echo ""
    echo "待处理: $PENDING_COUNT 个章节"
fi

echo ""
echo "5. 特殊章节状态"
echo "----------------------------------------------------------------------"
# 检查130太史公自序
if [ -f "$OUTPUT_DIR/130_太史公自序.tagged.md" ]; then
    SIZE=$(du -h "$OUTPUT_DIR/130_太史公自序.tagged.md" | cut -f1)
    LINES=$(wc -l < "$OUTPUT_DIR/130_太史公自序.tagged.md")
    echo "✅ 130_太史公自序 已完成 ($SIZE, $LINES行)"
    echo "   这是《史记》最重要的篇章之一！"
else
    echo "⏳ 130_太史公自序 待处理"
    echo "   ⭐⭐⭐ 这是《史记》最重要的篇章，需要特别细致处理！"
fi

echo ""
echo "======================================================================"
echo "检查完成"
echo "======================================================================"
echo ""
echo "下一步操作："
if [ $PENDING_COUNT -gt 0 ]; then
    echo "  1. 设置API密钥: export ANTHROPIC_API_KEY='your-key'"
    echo "  2. 运行处理脚本: ./scripts/run_111_130.sh"
    echo "  或直接运行: python3 scripts/process_chapters_111_130.py"
else
    echo "  ✅ 所有章节已处理完成！"
    echo "  可以进行后续处理："
    echo "    - 生成HTML: python3 render_shiji_html.py"
    echo "    - 验证标注: python3 scripts/validate_all_chapters.py"
fi
echo ""
