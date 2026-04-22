#!/usr/bin/env bash
# 启动史记 wiki 本地服务
#
# 用法:
#   ./wiki.sh              # 默认端口 8000
#   ./wiki.sh 9000         # 指定端口
#
# 执行步骤:
#   1. 用 build_registry.py 重建 wiki/pages.json (扫描 wiki/pages/*.md)
#   2. 启动 Node 静态服务器 (scripts/wiki/serve.js), 根目录 = wiki/

set -euo pipefail

PORT="${1:-8000}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_DIR="$ROOT/wiki"
REGISTRY_SCRIPT="$ROOT/scripts/wiki/build_registry.py"
SERVE_SCRIPT="$ROOT/scripts/wiki/serve.js"

if [[ ! -d "$WIKI_DIR" ]]; then
  echo "✗ 未找到 $WIKI_DIR" >&2
  exit 1
fi
if [[ ! -f "$REGISTRY_SCRIPT" ]]; then
  echo "✗ 未找到 $REGISTRY_SCRIPT" >&2
  exit 1
fi
if [[ ! -f "$SERVE_SCRIPT" ]]; then
  echo "✗ 未找到 $SERVE_SCRIPT" >&2
  exit 1
fi
if ! command -v node >/dev/null 2>&1; then
  echo "✗ 未找到 node, 请先安装 Node.js" >&2
  exit 1
fi

echo "[1/2] 重建注册表"
python3 "$REGISTRY_SCRIPT" "$WIKI_DIR/pages"

echo "[2/2] 启动服务 (Ctrl+C 停止)"
exec node "$SERVE_SCRIPT" "$WIKI_DIR" "$PORT"
