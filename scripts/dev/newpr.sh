#!/usr/bin/env bash
# newpr — 一条命令开 PR：建分支 → push → gh pr create
#
# Usage:
#   ./scripts/dev/newpr.sh <branch-name> [PR title]
#   ./scripts/dev/newpr.sh chore/cleanup-deps
#   ./scripts/dev/newpr.sh fix/cors-default "fix(cors): tighten default origins"
#
# Recommended branch naming:
#   feat/<topic>      —— 新功能
#   fix/<topic>       —— bug 修复
#   chore/<topic>     —— 工程/构建
#   docs/<topic>      —— 文档
#   refactor/<topic>  —— 重构
#   test/<topic>      —— 测试
#
# 工作流（per CONTRIBUTING.md）：每次改动都通过 PR，不 push main。

set -euo pipefail

if [[ $# -lt 1 ]]; then
  cat <<EOF
Usage: $0 <branch-name> [PR title]

Examples:
  $0 chore/slim-deps
  $0 fix/typo-readme "docs: fix typo in README"

Don't forget: commit your changes first; this script then creates a branch
from your current commits, pushes it, and opens a PR.
EOF
  exit 1
fi

BRANCH="$1"
TITLE="${2:-}"

# 必须在 main 上才能基于 main 拉新分支（避免基于杂分支）
CURRENT="$(git symbolic-ref --short HEAD)"
if [[ "$CURRENT" != "main" ]]; then
  echo "⚠️  当前在 '$CURRENT'，本脚本期望从 main 拉分支"
  read -r -p "继续从 '$CURRENT' 拉？[y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]] || exit 1
fi

# 检查工作树有未提交改动
if [[ -z "$(git status --porcelain)" ]]; then
  echo "⚠️  工作树没有未提交改动；脚本会建空分支但 PR 会被 GitHub 拒绝"
  read -r -p "继续？[y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]] || exit 1
fi

echo "→ 切到新分支 $BRANCH"
git checkout -b "$BRANCH"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "→ 自动 git add + commit"
  git add -A
  git commit -m "${TITLE:-WIP: $BRANCH}"
fi

echo "→ push 到 origin/$BRANCH"
git push -u origin "$BRANCH"

echo "→ gh pr create"
if [[ -n "$TITLE" ]]; then
  gh pr create --title "$TITLE" --body "Auto-created via scripts/dev/newpr.sh."
else
  gh pr create --fill
fi

echo "✓ Done. 等 CI 通过、自审，再 \`gh pr merge\` 或在 GitHub 上 merge。"
