#!/bin/bash
# 显示最近N天的工作日志摘要

DAYS=${1:-7}  # 默认显示最近7天

echo "========================================"
echo "最近 ${DAYS} 天的工作日志摘要"
echo "========================================"
echo ""

# 获取最近N天有提交的日期
dates=$(git log --since="${DAYS} days ago" --pretty=format:"%ad" --date=short | sort -u)

for date in $dates; do
    log_file="logs/daily/${date}.md"

    if [ -f "$log_file" ]; then
        echo "📅 ${date}"
        echo "----------------------------------------"

        # 提取核心功能变化部分（前几行）
        sed -n '/^## 核心功能变化/,/^## 技术细节/p' "$log_file" | \
            grep -E '^\- ' | head -3 | sed 's/^/  /'

        # 提取提交统计
        commits=$(grep "提交次数:" "$log_file" | sed 's/.*提交次数: //')
        [ -n "$commits" ] && echo "  📊 ${commits}次提交"

        echo ""
    fi
done

echo "========================================"
echo "详细日志请查看 logs/daily/ 目录"
echo "========================================"
