#!/usr/bin/env bash
# 把 wiki 静态部分发布到 GitHub Pages (docs/wiki).
#
# 用 symlink 方案 (docs/wiki → ../wiki/public), 不复制文件.
# 本脚本只做:
#   1. 确保符号链接存在
#   2. 重建 semantic.json + pages.json (让发布物带最新数据)
#   3. 打印提示: git 提交 docs/wiki 符号链接 + wiki/public/ 内容 + wiki/data/
#
# GitHub Pages 发布后的 URL: https://baojie.github.io/shiji-kb/wiki/
#
# ⚠️ /api/* 接口在 GitHub Pages 上不可用 (无后端).
#    当前 wiki 页面 UI 不依赖 /api, 纯静态可完整工作.
#    语义插件若将来接入 /api, 需单独设计静态化方案.

set -euo pipefail

WIKI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$WIKI_ROOT/.." && pwd)"
DOCS_WIKI="$REPO_ROOT/docs/wiki"
PUBLIC_DIR="$WIKI_ROOT/public"

echo "[1/3] 检查 symlink $DOCS_WIKI → ../wiki/public"
if [[ -L "$DOCS_WIKI" ]]; then
  target="$(readlink "$DOCS_WIKI")"
  if [[ "$target" == "../wiki/public" ]]; then
    echo "  ✓ symlink 已就位"
  else
    echo "  ✗ symlink 指向 '$target', 期望 '../wiki/public'" >&2
    exit 1
  fi
elif [[ -e "$DOCS_WIKI" ]]; then
  echo "  ✗ $DOCS_WIKI 存在但不是 symlink" >&2
  exit 1
else
  echo "  创建 symlink"
  (cd "$REPO_ROOT/docs" && ln -s ../wiki/public wiki)
fi

echo "[2/3] 重建 wiki/data/semantic.json (供 pages.json enrich)"
node "$WIKI_ROOT/server/api/seed.js"

echo "[3/3] 重建 pages.json"
python3 "$WIKI_ROOT/scripts/build_registry.py" "$PUBLIC_DIR/pages"

echo ""
echo "=== 完成 ==="
echo "发布到 GitHub Pages 需要 git 提交:"
echo "  docs/wiki                    (symlink)"
echo "  wiki/public/                 (源内容, pages.json 也在里面)"
echo ""
echo "wiki/data/semantic.json 在 .gitignore 里, 不会提交;"
echo "首次 pages.json 生成需要它, 之后 pages.json 已含 enrich 后字段."
echo ""
echo "本地预览发布路径:"
echo "  node wiki/server/serve.js docs 8000"
echo "  打开 http://localhost:8000/wiki/"
