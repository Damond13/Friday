#!/usr/bin/env bash
# 运行集成测试
set -euo pipefail
cd "$(dirname "$0")/.."
echo "===== 运行集成测试 ====="
uv run pytest tests/integration/ -v "$@"
