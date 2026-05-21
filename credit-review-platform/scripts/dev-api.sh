#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
echo "Starting API on http://localhost:8000"
python3.12 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
