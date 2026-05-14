#!/bin/bash
# 生成每月成本报告的快捷脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_ROOT/doc/reports"

echo "📊 生成 Claude Code 每月成本报告..."
echo ""

# 生成月报
python3 "$SCRIPT_DIR/generate_cost_report.py" --period monthly --output "$OUTPUT_DIR"

echo ""
echo "✅ 报告已生成！"
echo ""
echo "📁 报告位置: $OUTPUT_DIR/"
echo "📝 查看报告: cat $OUTPUT_DIR/monthly_report_*.md | tail -150"
