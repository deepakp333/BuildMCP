#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../frontend"
echo "Starting frontend on http://localhost:5173 (proxies /api -> :8000)"
npm run dev
