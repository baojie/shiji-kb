#!/bin/bash
# 简单的HTTP服务器，用于测试原型
# 使用随机可用端口

cd "$(dirname "$0")/../.."

# 查找可用端口（从8000开始，如果被占用则递增）
PORT=8000
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    PORT=$((PORT + 1))
done

echo "============================================"
echo "启动HTTP服务器 (端口: $PORT)"
echo "============================================"
echo ""
echo "三家注展示方式："
echo "  侧边栏v1 (基础): http://localhost:$PORT/labs/prototypes/001_sanjia_sidebar.html"
echo "  侧边栏v2 (动态连线⭐): http://localhost:$PORT/labs/prototypes/001_sanjia_sidebar_v2.html"
echo "  行下式: http://localhost:$PORT/labs/prototypes/001_sanjia_inline.html"
echo "  弹出式: http://localhost:$PORT/labs/prototypes/prototype_marginal_notes.html"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "============================================"
echo ""

python3 -m http.server $PORT
