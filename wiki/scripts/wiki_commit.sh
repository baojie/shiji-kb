#!/usr/bin/env bash
# wiki_commit.sh — 由 /wiki skill 调用，执行 commit + push
# 用法: bash wiki/scripts/wiki_commit.sh "commit message"
set -euo pipefail

MSG="${1:-}"
if [[ -z "$MSG" ]]; then
  echo "用法: bash wiki/scripts/wiki_commit.sh \"commit message\"" >&2
  exit 1
fi

git commit -m "$MSG"
git push
