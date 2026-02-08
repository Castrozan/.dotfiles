#!/usr/bin/env bash
# pw — Fast persistent browser automation (Playwright + CDP)
# Uses a dedicated agent browser profile (lightweight, no extensions).
# Sessions persist in ~/.local/share/pw-browser/.
# Headless by default. Use --headed for manual login.
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

find_browser() {
  command -v brave 2>/dev/null || command -v google-chrome-stable 2>/dev/null || command -v chromium 2>/dev/null || echo ""
}

# Handle open --headed: stop headless, launch visible browser, block until closed
if [ "${1:-}" = "open" ] && [[ " ${*} " == *" --headed "* ]]; then
  # Stop running headless browser if any
  if curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1; then
    echo "Stopping headless browser..."
    pkill -f "remote-debugging-port=$PW_PORT.*user-data-dir=$PW_DATA" 2>/dev/null || true
    sleep 0.5
  fi
  BROWSER="$(find_browser)"
  if [ -z "$BROWSER" ]; then
    echo "Error: No browser found in PATH" >&2
    exit 1
  fi
  # Extract URL (skip "open", "--headed", "--new")
  URL=""
  for arg in "${@:2}"; do
    [[ "$arg" == "--headed" || "$arg" == "--new" ]] && continue
    URL="$arg"
    break
  done
  mkdir -p "$PW_DATA"
  echo "Opening headed browser..."
  echo "Profile: $PW_DATA"
  echo "Close the browser window when done."
  "$BROWSER" \
    --remote-debugging-port="$PW_PORT" \
    --user-data-dir="$PW_DATA" \
    --no-first-run \
    --no-default-browser-check \
    --disable-extensions \
    --disable-sync \
    "${URL:-about:blank}" 2>/dev/null
  echo "Session saved."
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
  BROWSER="$(find_browser)"
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
