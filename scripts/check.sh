#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

format() {
    echo "==> Formatting with black..."
    uv run black backend/ main.py
}

check() {
    echo "==> Checking formatting with black..."
    uv run black --check backend/ main.py
}

usage() {
    echo "Usage: $0 [--fix]"
    echo "  (no args)  Check formatting only — exit non-zero if changes needed"
    echo "  --fix      Auto-format all files in place"
}

cd "$ROOT"

case "${1:-}" in
    --fix)   format ;;
    --help)  usage ;;
    "")      check ;;
    *)       echo "Unknown option: $1"; usage; exit 1 ;;
esac
