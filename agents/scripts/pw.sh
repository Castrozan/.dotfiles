#!/usr/bin/env bash
# pw — Fast persistent browser automation (Playwright + CDP)
# Uses a dedicated agent browser profile (lightweight, no extensions).
# User logs in once (WhatsApp etc.), sessions persist in ~/.local/share/pw-browser/.
# The agent browser auto-launches on port 9222 when needed.
set -euo pipefail

PW_PORT="${PW_PORT:-9222}"
PW_CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/pw-cli"
PW_DATA="${PW_BROWSER_DATA:-$HOME/.local/share/pw-browser}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PW_JS="$SCRIPT_DIR/../skills/playwright-mcp/pw.js"

# Handle close — kill the agent browser
if [ "${1:-}" = "close" ]; then
  pkill -f "remote-debugging-port=$PW_PORT.*user-data-dir=$PW_DATA" 2>/dev/null \
    && echo "Agent browser closed." \
    || echo "No agent browser running."
  exit 0
fi

# Handle status
if [ "${1:-}" = "status" ]; then
  echo -n "Agent browser (port $PW_PORT): "
  curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1 && echo "ready" || echo "not running"
  exit 0
fi

# Handle login — launch headed so user can log in to sites
if [ "${1:-}" = "login" ]; then
  if curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1; then
    echo "Agent browser already running. Close it first: pw close"
    exit 1
  fi
  BROWSER="$(command -v brave 2>/dev/null || command -v google-chrome-stable 2>/dev/null || command -v chromium 2>/dev/null || echo "")"
  if [ -z "$BROWSER" ]; then
    echo "Error: No browser found in PATH" >&2
    exit 1
  fi
  mkdir -p "$PW_DATA"
  echo "Launching agent browser in headed mode for login..."
  echo "Profile: $PW_DATA"
  echo "Log in to any sites you need, then close the browser."
  "$BROWSER" \
    --remote-debugging-port="$PW_PORT" \
    --user-data-dir="$PW_DATA" \
    --no-first-run \
    --no-default-browser-check \
    --disable-extensions \
    --disable-sync \
    "${2:-about:blank}" 2>/dev/null
  echo "Login session saved."
  exit 0
fi

# Auto-install playwright in cache dir (one-time)
if [ ! -d "$PW_CACHE/node_modules/playwright" ]; then
  echo "Installing playwright (one-time)..." >&2
  mkdir -p "$PW_CACHE"
  npm install --prefix "$PW_CACHE" --silent playwright 2>/dev/null
  echo "Done." >&2
fi

# Auto-launch agent browser (headless) if not running
if ! curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1; then
  BROWSER="$(command -v brave 2>/dev/null || command -v google-chrome-stable 2>/dev/null || command -v chromium 2>/dev/null || echo "")"
  if [ -z "$BROWSER" ]; then
    echo "Error: No browser found in PATH" >&2
    exit 1
  fi
  mkdir -p "$PW_DATA"
  "$BROWSER" \
    --headless=new \
    --remote-debugging-port="$PW_PORT" \
    --user-data-dir="$PW_DATA" \
    --no-first-run \
    --no-default-browser-check \
    --disable-extensions \
    --disable-sync \
    >/dev/null 2>&1 &

  for _ in $(seq 1 20); do
    curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1 && break
    sleep 0.2
  done

  if ! curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1; then
    echo "Error: Failed to start agent browser on port $PW_PORT" >&2
    exit 1
  fi
fi

NODE_PATH="$PW_CACHE/node_modules" PW_PORT="$PW_PORT" exec node "$PW_JS" "$@"
