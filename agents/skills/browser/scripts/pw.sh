#!/usr/bin/env bash
# pw — Fast persistent browser automation (Playwright + CDP)
# Sessions persist in ~/.local/share/pw-browser/.
set -euo pipefail

PW_PORT="${PW_PORT:-9222}"
PW_CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/pw-cli"
PW_DATA="${PW_BROWSER_DATA:-$HOME/.local/share/pw-browser}"
PW_JS="${PW_JS:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../skills/browser/pw.js}"

# Shared Chrome flags for all launch modes
CHROME_FLAGS=(
  --remote-debugging-port="$PW_PORT"
  --user-data-dir="$PW_DATA"
  --no-first-run
  --no-default-browser-check
  --disable-extensions
  --disable-sync
  --use-fake-ui-for-media-stream
  --autoplay-policy=no-user-gesture-required
  --disable-background-timer-throttling
  --disable-backgrounding-occluded-windows
)

find_browser() {
  command -v chromium 2>/dev/null || command -v google-chrome-stable 2>/dev/null || command -v brave 2>/dev/null || echo ""
}

case "${1:-help}" in
  help|-h|--help)
    cat <<'HELP'
pw — browser automation (headless by default)

  open <url> [--new] [--headed]   Navigate (--new=new tab, --headed=visible window)
  back                            Go back in history
  forward                         Go forward in history
  scroll <up|down> [px]           Scroll page (default 500px)
  snap                            Accessibility tree (semantic YAML)
  elements                        Interactive elements with [index]
  text                            Full page text content
  html                            Full page HTML
  url                             Current URL
  title                           Page title
  click <index|selector>          Click element by index or CSS selector
  click-text <text>               Click element by visible text
  fill <selector> <value>         Fill input field
  type <selector> <value>         Type into field (keystroke by keystroke)
  select <selector> <value>       Select dropdown option
  press <key>                     Press keyboard key (Enter, Tab, etc.)
  screenshot [path] [--full]      Screenshot (default: /tmp/pw-screenshot.png)
  eval <js>                       Evaluate JavaScript expression
  wait <selector>                 Wait for element to appear
  wait --text <text>              Wait for text to appear
  tabs                            List open tabs
  tab <n>                         Switch to tab by index
  status                          Check if browser is running
  close                           Kill browser
HELP
    exit 0
    ;;

  close)
    pkill -f "remote-debugging-port=$PW_PORT.*user-data-dir=$PW_DATA" 2>/dev/null \
      && echo "Agent browser closed." \
      || echo "No agent browser running."
    exit 0
    ;;

  status)
    echo -n "Agent browser (port $PW_PORT): "
    curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1 && echo "ready" || echo "not running"
    exit 0
    ;;
esac

# Handle open --headed: stop headless, launch visible browser, block until closed
if [ "${1:-}" = "open" ] && [[ " ${*} " == *" --headed "* ]]; then
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
  URL=""
  for arg in "${@:2}"; do
    [[ "$arg" == "--headed" || "$arg" == "--new" ]] && continue
    URL="$arg"
    break
  done
  mkdir -p "$PW_DATA"
  echo "Opening headed browser..."
  echo "Close the browser window when done."
  "$BROWSER" "${CHROME_FLAGS[@]}" "${URL:-about:blank}" 2>/dev/null
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
  "$BROWSER" --headless=new "${CHROME_FLAGS[@]}" >/dev/null 2>&1 &

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
