#!/usr/bin/env bash
# Butler 首次启动: 跑 discover, 填 queue.md, 记一次 observe 动作.
#
# 用法:
#   wiki/scripts/butler/bootstrap.sh
#
# 每次 butler 长期停机后也可重跑, queue.md 会被重新填充 (旧条目会被覆盖).
# 若只想追加新候选 (保留旧 queue), 手动跑各 discover 脚本并 >> queue.md.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BUTLER="$ROOT/wiki/scripts/butler"
LOG="$ROOT/logs/wiki_butler"
SEMANTIC="$ROOT/wiki/data/semantic.json"
SEED="$ROOT/wiki/server/api/seed.js"

echo "[butler-bootstrap] 仓库根: $ROOT"

# 状态目录
mkdir -p "$LOG/reflections"
touch "$LOG/actions.jsonl" "$LOG/failures.jsonl" "$LOG/skill_changes.md"

# semantic.json 前置: 若没就跑 seed
if [[ ! -f "$SEMANTIC" ]]; then
  echo "[0/3] semantic.json 缺失, 运行 seed.js"
  node "$SEED"
fi

echo ""
echo "[1/3] discover_kg"
KG_MD=$(python3 "$BUTLER/discover_kg.py" --top 30 2>/tmp/butler_kg.err)
cat /tmp/butler_kg.err | tail -1

echo ""
echo "[2/3] discover_sku"
SKU_MD=$(python3 "$BUTLER/discover_sku.py" 2>/tmp/butler_sku.err)
cat /tmp/butler_sku.err | tail -1

echo ""
echo "[3/3] 写 queue.md"

cat > "$LOG/queue.md" <<MARK
# Butler 候选队列

> 由 bootstrap.sh 于 $(date +%Y-%m-%d) 填充.
> P0 高优 / P1 中优 / P2 低优. 每次 invocation 只做 1 条, 按 W1 优先级选.

$KG_MD

$SKU_MD

---

## P2 低优 (手动加入)

（留给用户手动追加的低优任务）
MARK

# 记一次 observe 动作
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
P0_COUNT=$( { grep -o '\[P0\]' "$LOG/queue.md" || true; } | wc -l | tr -d ' ')
P1_COUNT=$( { grep -o '\[P1\]' "$LOG/queue.md" || true; } | wc -l | tr -d ' ')
cat >> "$LOG/actions.jsonl" <<JSONL
{"ts":"$TS","mode":"observe","action":"bootstrap","target":"logs/wiki_butler/queue.md","rationale":"首次扫描填 queue","result":"accept","p0_count":$P0_COUNT,"p1_count":$P1_COUNT,"verdict":"accept","diff_lines":0}
JSONL

# 知识量快照
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python "$SCRIPT_DIR/compute_knowledge.py" 2>&1 || true

echo ""
echo "=========================================="
echo "  bootstrap 完成"
echo "=========================================="
echo "  queue.md : $LOG/queue.md"
echo "  P0 候选  : $P0_COUNT"
echo "  P1 候选  : $P1_COUNT"
echo ""
echo "下一步:"
echo "  1. 人工 review queue.md, 删不合理候选"
echo "  2. 调 Claude 走 PROMPT.md 做一轮 atomic action"
echo "  3. 或 /loop 30m \"$(cat $BUTLER/PROMPT.md | head -1)\" 自动循环"
