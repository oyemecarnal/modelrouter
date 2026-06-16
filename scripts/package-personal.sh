#!/usr/bin/env bash
# Build Personal-tier tarball (no secrets, no venv).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VER="$(cat VERSION 2>/dev/null || echo dev)"
OUT="dist/modelrouter-${VER}-personal.tar.gz"

mkdir -p dist
tar -czf "$OUT" \
  --exclude='./.git' \
  --exclude='./.venv' \
  --exclude='./.env' \
  --exclude='./data' \
  --exclude='./dist' \
  --exclude='./tokens/.env.local' \
  --exclude='./tokens/.venv' \
  --exclude='./__pycache__' \
  --exclude='.DS_Store' \
  .

echo "==> Personal tarball: $OUT ($(du -h "$OUT" | awk '{print $1}'))"
echo "    Docs: docs/LANDING.md · docs/ENV.md · docs/LAPTOP_DAEMON.md"
