#!/usr/bin/env bash
# 启动史记 wiki 本地服务
#
# 用法:
#   ./wiki/wiki.sh          # 默认端口 8000 (从仓库根运行)
#   ./wiki.sh 9000          # 指定端口 (从 wiki/ 内运行)
#
# 目录约定:
#   wiki/public/            HTTP 根, 客户端能看到的全部
#   wiki/server/            Node 服务器 (不公开)
#   wiki/scripts/           构建期工具 (Python, 不公开)
#   wiki/data/              (未来) DB / 运行时数据, 不公开
#
# 执行步骤:
#   1. 用 scripts/build_registry.py 重建 wiki/public/pages.json
#   2. exec node server/serve.js wiki/public <port>

set -euo pipefail

PORT="${1:-8000}"
WIKI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLIC_DIR="$WIKI_ROOT/public"
DATA_DIR="$WIKI_ROOT/data"
REGISTRY_SCRIPT="$WIKI_ROOT/scripts/build_registry.py"
SERVE_SCRIPT="$WIKI_ROOT/server/serve.js"
SEED_SCRIPT="$WIKI_ROOT/server/api/seed.js"
SEMANTIC_DB="$DATA_DIR/semantic.json"

if [[ ! -d "$PUBLIC_DIR" ]]; then
  echo "✗ 未找到 $PUBLIC_DIR" >&2
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

if [[ ! -f "$SEMANTIC_DB" ]]; then
  echo "[1/3] 首次运行, 构建语义数据库 $SEMANTIC_DB"
  node "$SEED_SCRIPT"
else
  echo "[1/3] 语义数据库已存在: $SEMANTIC_DB (删除可重建)"
fi

echo "[2/3] 重建页面注册表 (注入 semantic 数据)"
python3 "$REGISTRY_SCRIPT" "$PUBLIC_DIR/pages"

echo "[3/3] 启动服务 (Ctrl+C 停止)"
exec node "$SERVE_SCRIPT" "$PUBLIC_DIR" "$PORT"
