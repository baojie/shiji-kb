#!/usr/bin/env bash
# wiki-daemon.sh — 史记 Wiki 守护进程管理
#
# 用法（从仓库根或 wiki/ 目录均可）:
#   ./wiki/wiki-daemon.sh start [port]   # 启动（默认端口 5247）
#   ./wiki/wiki-daemon.sh stop           # 停止
#   ./wiki/wiki-daemon.sh restart [port] # 重启
#   ./wiki/wiki-daemon.sh status         # 查看状态
#   ./wiki/wiki-daemon.sh log            # 实时查看日志（tail -f）

set -euo pipefail

PORT="${2:-5247}"
WIKI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLIC_DIR="$WIKI_ROOT/public"
DATA_DIR="$WIKI_ROOT/data"
REGISTRY_SCRIPT="$WIKI_ROOT/scripts/build_registry.py"
SERVE_SCRIPT="$WIKI_ROOT/server/serve.js"
SEED_SCRIPT="$WIKI_ROOT/server/api/seed.js"
SEMANTIC_DB="$DATA_DIR/semantic.json"

PID_FILE="/tmp/shiji_wiki.pid"
LOG_FILE="$WIKI_ROOT/logs/wiki-server.log"

# ── 内部函数 ──────────────────────────────────────────────────────────────────

_is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

_start() {
  if _is_running; then
    echo "[wiki] 已在运行 (pid=$(cat "$PID_FILE"))，使用 restart 重启"
    return 0
  fi

  # 前置检查
  for f in "$PUBLIC_DIR" "$REGISTRY_SCRIPT" "$SERVE_SCRIPT"; do
    if [[ ! -e "$f" ]]; then
      echo "✗ 未找到: $f" >&2; exit 1
    fi
  done
  if ! command -v node >/dev/null 2>&1; then
    echo "✗ 未找到 node，请先安装 Node.js" >&2; exit 1
  fi

  echo "[wiki] 构建语义数据库..."
  if [[ ! -f "$SEMANTIC_DB" ]]; then
    node "$SEED_SCRIPT" >> "$LOG_FILE" 2>&1
  fi

  echo "[wiki] 重建页面注册表..."
  python3 "$REGISTRY_SCRIPT" "$PUBLIC_DIR/pages" >> "$LOG_FILE" 2>&1

  echo "[wiki] 以守护进程启动 (端口 $PORT)..."
  nohup node "$SERVE_SCRIPT" "$PUBLIC_DIR" "$PORT" >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  sleep 0.5

  if _is_running; then
    echo "[wiki] 已启动 (pid=$(cat "$PID_FILE"))，日志: $LOG_FILE"
    echo "[wiki] 访问: http://localhost:$PORT"
  else
    echo "✗ 启动失败，查看日志: $LOG_FILE" >&2
    rm -f "$PID_FILE"
    exit 1
  fi
}

_stop() {
  if ! _is_running; then
    echo "[wiki] 未在运行"
    rm -f "$PID_FILE"
    return 0
  fi
  local pid
  pid=$(cat "$PID_FILE")
  echo "[wiki] 停止 (pid=$pid)..."
  kill "$pid"
  # 等待最多 5 秒
  local i=0
  while kill -0 "$pid" 2>/dev/null && (( i < 10 )); do
    sleep 0.5; i=$(( i + 1 ))
  done
  if kill -0 "$pid" 2>/dev/null; then
    echo "[wiki] 未响应，强制终止..."
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
  echo "[wiki] 已停止"
}

_status() {
  if _is_running; then
    local pid
    pid=$(cat "$PID_FILE")
    echo "[wiki] 运行中 (pid=$pid)，端口 $PORT"
    echo "[wiki] 日志: $LOG_FILE"
  else
    echo "[wiki] 未运行"
    [[ -f "$PID_FILE" ]] && rm -f "$PID_FILE"
  fi
}

# ── 命令分发 ──────────────────────────────────────────────────────────────────

CMD="${1:-help}"

case "$CMD" in
  start)
    _start
    ;;
  stop)
    _stop
    ;;
  restart)
    _stop
    _start
    ;;
  status)
    _status
    ;;
  log)
    exec tail -f "$LOG_FILE"
    ;;
  *)
    echo "用法: $0 {start|stop|restart|status|log} [port]"
    echo "  start [port]   启动守护进程（默认端口 5247）"
    echo "  stop           停止守护进程"
    echo "  restart [port] 重启守护进程"
    echo "  status         查看运行状态"
    echo "  log            实时查看服务日志"
    exit 1
    ;;
esac
