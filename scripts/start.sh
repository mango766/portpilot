#!/usr/bin/env bash
# PortPilot launcher — runs the dashboard in the foreground.
#
# Usage:
#   ./scripts/start.sh                    # default port 7777
#   PORT=7777 ./scripts/start.sh          # override port
#
set -euo pipefail

PORT="${PORT:-7777}"
HOST="${HOST:-127.0.0.1}"

cd "$(dirname "$0")/.."

# Ensure dependencies are present.
python3 - <<'PY' >/dev/null 2>&1 || {
  echo "📦 Installing dependencies..."
  python3 -m pip install --quiet -r requirements.txt
}
import fastapi, uvicorn, psutil, httpx  # noqa: F401
PY

export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"

echo "🚀 PortPilot starting at http://${HOST}:${PORT}"
exec python3 -m portpilot.server --host "${HOST}" --port "${PORT}"
