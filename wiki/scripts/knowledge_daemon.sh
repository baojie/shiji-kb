#!/usr/bin/env bash
# knowledge_daemon.sh — 后台每分钟刷新 knowledge_latest.json
#
# 用法（通常由 bootstrap.sh 自动调用，不需要手动运行）:
#   bash wiki/scripts/knowledge_daemon.sh &
#
# 防止重复：PID 文件在 /tmp/shiji_knowledge_daemon.pid
# 停止：kill $(cat /tmp/shiji_knowledge_daemon.pid)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="/tmp/shiji_knowledge_daemon.pid"

# 已有实例在运行则直接退出
if [[ -f "$PID_FILE" ]]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "[knowledge_daemon] 已在运行 (pid=$OLD_PID)，跳过"
    exit 0
  fi
fi

echo $$ > "$PID_FILE"
trap "rm -f $PID_FILE" EXIT

echo "[knowledge_daemon] 启动 (pid=$$)，每 60s 刷新一次"

cd "$ROOT"
while true; do
  python3 wiki/scripts/compute_knowledge.py 2>/dev/null || true
  sleep 60
done
