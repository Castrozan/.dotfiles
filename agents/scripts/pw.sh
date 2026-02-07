#!/usr/bin/env bash
# pw — Fast persistent browser automation (Playwright + CDP)
# Auto-starts Chrome and installs playwright on first use.
set -euo pipefail

PW_PORT="${PW_PORT:-19222}"
PW_CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/pw-cli"
PW_DATA="/tmp/pw-data-$$uid"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PW_JS="$SCRIPT_DIR/../skills/playwright-mcp/pw.js"
CHROME="$(command -v google-chrome-stable 2>/dev/null || command -v chromium 2>/dev/null || echo "")"

if [ -z "$CHROME" ]; then
  echo "Error: No Chrome/Chromium found in PATH" >&2
  exit 1
fi

# Handle close — kill the Chrome debug instance
if [ "${1:-}" = "close" ]; then
  pkill -f "remote-debugging-port=$PW_PORT" 2>/dev/null && echo "Browser closed." || echo "No browser running."
  exit 0
fi

# Handle status
if [ "${1:-}" = "status" ]; then
  if curl -s "http://127.0.0.1:$PW_PORT/json/version" 2>/dev/null | head -1; then
    echo "Browser running on port $PW_PORT"
  else
    echo "No browser running."
  fi
  exit 0
fi

# Auto-install playwright in cache dir (one-time, ~2s)
if [ ! -d "$PW_CACHE/node_modules/playwright" ]; then
  echo "Installing playwright (one-time)..." >&2
  mkdir -p "$PW_CACHE"
  npm install --prefix "$PW_CACHE" --silent playwright 2>/dev/null
  echo "Done." >&2
fi

# Auto-start Chrome with remote debugging if not running
if ! curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1; then
  mkdir -p "$PW_DATA"
  "$CHROME" \
    --headless=new \
    --remote-debugging-port="$PW_PORT" \
    --user-data-dir="$PW_DATA" \
    --no-first-run \
    --no-default-browser-check \
    --disable-background-networking \
    --disable-extensions \
    --disable-sync \
    >/dev/null 2>&1 &

  # Wait for Chrome to accept connections (up to 4s)
  for _ in $(seq 1 20); do
    curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1 && break
    sleep 0.2
  done

  if ! curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1; then
    echo "Error: Chrome failed to start on port $PW_PORT" >&2
    exit 1
  fi
fi

# Run the command
NODE_PATH="$PW_CACHE/node_modules" PW_PORT="$PW_PORT" exec node "$PW_JS" "$@"
