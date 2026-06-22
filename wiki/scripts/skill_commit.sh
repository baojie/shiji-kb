#!/usr/bin/env bash
# skill_commit.sh — 授权给 /rfc /evolve /wiki skill 使用的 git commit 包装器
#
# 直接调用 `git commit` 已被 settings.json deny 列表拦截。
# skill 必须通过本脚本提交，以保证所有 wiki 提交都经过授权入口。
#
# 用法（与 git commit 完全兼容）:
#   bash wiki/scripts/skill_commit.sh -m "消息"
#   bash wiki/scripts/skill_commit.sh -m "$(cat <<'EOF'
#   多行消息
#   EOF
#   )"
set -euo pipefail
exec git commit "$@"
