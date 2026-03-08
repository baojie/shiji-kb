#!/bin/bash
# Agent-based review batch helper
#
# 用法：在 Claude Code 中运行以下流程（每章）：
#
# 1. 生成提示词:
#    python kg/events/scripts/run_review_pipeline.py --prompt NNN > /tmp/prompt_NNN.txt
#
# 2. 用 Agent 工具执行反思（读取 /tmp/prompt_NNN.txt 内容作为 prompt）
#    Agent 输出 JSON 到 /tmp/reflect_NNN.json
#
# 3. 导入结果:
#    python kg/events/scripts/run_review_pipeline.py --ingest NNN /tmp/reflect_NNN.json
#
# 本脚本仅用于生成所有章节的提示词文件（批量预生成）

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE="$SCRIPT_DIR/run_review_pipeline.py"

START=${1:-001}
END=${2:-130}

echo "批量生成提示词: $START — $END"

for i in $(seq -w $START $END); do
    PROMPT_FILE="/tmp/prompt_${i}.txt"
    if [ -f "$PROMPT_FILE" ]; then
        echo "  跳过 $i (已存在)"
        continue
    fi
    python "$PIPELINE" --prompt "$i" > "$PROMPT_FILE" 2>/dev/null
    if [ $? -eq 0 ]; then
        LINES=$(wc -l < "$PROMPT_FILE")
        echo "  $i: $LINES 行"
    else
        echo "  $i: 跳过 (无事件索引)"
        rm -f "$PROMPT_FILE"
    fi
done

echo "完成。提示词文件在 /tmp/prompt_NNN.txt"
