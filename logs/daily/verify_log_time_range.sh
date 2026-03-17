#!/bin/bash
# 验证日志文件的实际时间范围

DATE=${1:-$(date -d "yesterday" +%Y-%m-%d)}

# 计算时间范围
START_DATE=$(date -d "$DATE -1 day" +%Y-%m-%d)
START_TIME="$START_DATE 07:00:00"
END_TIME="$DATE 07:00:00"

echo "========================================"
echo "📅 验证日志: $DATE.md"
echo "========================================"
echo ""
echo "⏰ 时间范围:"
echo "  开始: $START_TIME"
echo "  结束: $END_TIME (不含)"
echo ""

# 统计提交数
COUNT=$(git log --since="$START_TIME" --until="$END_TIME" --oneline 2>/dev/null | wc -l)
echo "📊 提交总数: $COUNT 次"
echo ""

if [ $COUNT -gt 0 ]; then
    echo "📝 提交列表:"
    echo "----------------------------------------"
    git log --since="$START_TIME" --until="$END_TIME" \
        --pretty=format:"  %ai | %s" 2>/dev/null
    echo ""
    echo ""

    # 时间分布统计
    echo "⏱️  时间分布:"
    echo "----------------------------------------"

    # 统计各时间段的提交数
    # 07:00-12:00 (上午)
    morning=$(git log --since="$START_DATE 07:00" --until="$START_DATE 12:00" --oneline 2>/dev/null | wc -l)
    # 12:00-18:00 (下午)
    afternoon=$(git log --since="$START_DATE 12:00" --until="$START_DATE 18:00" --oneline 2>/dev/null | wc -l)
    # 18:00-24:00 (晚上)
    evening=$(git log --since="$START_DATE 18:00" --until="$START_DATE 23:59:59" --oneline 2>/dev/null | wc -l)
    # 00:00-07:00 (凌晨)
    dawn=$(git log --since="$DATE 00:00" --until="$END_TIME" --oneline 2>/dev/null | wc -l)

    echo "  上午 (07:00-12:00): $morning 次"
    echo "  下午 (12:00-18:00): $afternoon 次"
    echo "  晚上 (18:00-24:00): $evening 次"
    echo "  凌晨 (00:00-07:00): $dawn 次"
    echo ""

    # 检查是否有7点之后的误入提交
    echo "🔍 边界检查:"
    echo "----------------------------------------"
    next_day=$(date -d "$DATE +1 day" +%Y-%m-%d)
    leak=$(git log --since="$END_TIME" --until="$END_TIME +1 hour" --oneline 2>/dev/null | wc -l)
    if [ $leak -gt 0 ]; then
        echo "  ⚠️  发现 $leak 次提交在 07:00-08:00，应归入 $next_day.md"
    else
        echo "  ✓ 无边界溢出"
    fi
fi

echo ""
echo "========================================"
