#!/bin/bash
# 史记事件地铁图 — 启动脚本

PORT=${1:-1046}
APP_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "史记事件地铁图"
echo "  地址: http://localhost:$PORT"
echo "  目录: $APP_DIR"
echo "  按 Ctrl+C 停止"
echo ""

cd "$APP_DIR"

if command -v python3 &>/dev/null; then
    python3 -m http.server "$PORT"
elif command -v python &>/dev/null; then
    python -m SimpleHTTPServer "$PORT"
elif command -v npx &>/dev/null; then
    npx serve -l "$PORT" .
else
    echo "错误: 未找到 python3 / python / npx，请安装其中之一"
    exit 1
fi
