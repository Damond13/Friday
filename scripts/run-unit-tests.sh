#!/usr/bin/env bash
# 运行单元测试
set -euo pipefail
cd "$(dirname "$0")/.."
echo "===== 运行单元测试 ====="
uv run pytest tests/unit/ -v "$@"
