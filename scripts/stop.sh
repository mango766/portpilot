#!/usr/bin/env bash
# Stop any PortPilot instance running on the configured port.
set -euo pipefail
PORT="${PORT:-7777}"
PIDS="$(lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN -t 2>/dev/null || true)"
if [ -z "${PIDS}" ]; then
  echo "No PortPilot found on port ${PORT}."
  exit 0
fi
echo "Stopping PortPilot (pid ${PIDS})…"
kill ${PIDS}
