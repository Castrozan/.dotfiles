#!/usr/bin/env bash
# pw — Fast persistent browser automation (Playwright + CDP)
# Default: connects to user's Brave (always has --remote-debugging-port=19222).
# --chrome: forces a separate headless Chrome instance (port 19223).
set -euo pipefail

# --chrome flag: use headless Chrome instead of Brave
USE_CHROME=false
if [ "${1:-}" = "--chrome" ]; then
  USE_CHROME=true
  shift
fi

BRAVE_PORT=19222
CHROME_PORT=19223

if [ "$USE_CHROME" = true ]; then
  PW_PORT="$CHROME_PORT"
else
  PW_PORT="${PW_PORT:-$BRAVE_PORT}"
fi

PW_CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/pw-cli"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PW_JS="$SCRIPT_DIR/../skills/playwright-mcp/pw.js"

# Handle close
if [ "${1:-}" = "close" ]; then
  if [ "$USE_CHROME" = true ]; then
    pkill -f "headless.*remote-debugging-port=$CHROME_PORT" 2>/dev/null && echo "Headless Chrome closed." || echo "No headless Chrome running."
  else
    echo "Brave stays running (it's your main browser). Use --chrome close to kill headless."
  fi
  exit 0
fi

# Handle status
if [ "${1:-}" = "status" ]; then
  echo -n "Brave (port $BRAVE_PORT): "
  curl -sf "http://127.0.0.1:$BRAVE_PORT/json/version" >/dev/null 2>&1 && echo "ready" || echo "not running"
  echo -n "Chrome (port $CHROME_PORT): "
  curl -sf "http://127.0.0.1:$CHROME_PORT/json/version" >/dev/null 2>&1 && echo "ready" || echo "not running"
  exit 0
fi

# Auto-install playwright in cache dir (one-time)
if [ ! -d "$PW_CACHE/node_modules/playwright" ]; then
  echo "Installing playwright (one-time)..." >&2
  mkdir -p "$PW_CACHE"
  npm install --prefix "$PW_CACHE" --silent playwright 2>/dev/null
  echo "Done." >&2
fi

# Ensure browser is available on the target port
if ! curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1; then
  if [ "$USE_CHROME" = true ] || [ "$PW_PORT" = "$CHROME_PORT" ]; then
    # Launch headless Chrome
    CHROME="$(command -v google-chrome-stable 2>/dev/null || command -v chromium 2>/dev/null || echo "")"
    if [ -z "$CHROME" ]; then
      echo "Error: No Chrome/Chromium found in PATH" >&2
      exit 1
    fi
    PW_DATA="/tmp/pw-chrome-data"
    mkdir -p "$PW_DATA"
    "$CHROME" \
      --headless=new \
      --remote-debugging-port="$CHROME_PORT" \
      --user-data-dir="$PW_DATA" \
      --no-first-run \
      --no-default-browser-check \
      --disable-background-networking \
      --disable-extensions \
      --disable-sync \
      >/dev/null 2>&1 &

    for _ in $(seq 1 20); do
      curl -sf "http://127.0.0.1:$CHROME_PORT/json/version" >/dev/null 2>&1 && break
      sleep 0.2
    done
  else
    echo "Error: Brave not running on port $PW_PORT. Start Brave or use: pw --chrome <cmd>" >&2
    exit 1
  fi

  if ! curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1; then
    echo "Error: Failed to start browser on port $PW_PORT" >&2
    exit 1
  fi
fi

NODE_PATH="$PW_CACHE/node_modules" PW_PORT="$PW_PORT" exec node "$PW_JS" "$@"
