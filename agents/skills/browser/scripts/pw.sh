#!/usr/bin/env bash
set -euo pipefail

# Ensure display env vars are set for headed mode (needed when run from systemd)
if [[ -z "${WAYLAND_DISPLAY:-}" ]] && [[ -d "/run/user/${UID:-1000}" ]]; then
  for candidate in wayland-1 wayland-0; do
    if [[ -e "/run/user/${UID:-1000}/${candidate}" ]]; then
      export WAYLAND_DISPLAY="$candidate"
      break
    fi
  done
fi
if [[ -z "${DISPLAY:-}" ]]; then
  export DISPLAY=":0"
fi

PW_PORT="${PW_PORT:-9222}"
PW_DAEMON_PORT="$((PW_PORT + 1))"
PW_CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/pw-cli"
PW_DATA="${PW_BROWSER_DATA:-$HOME/.local/share/pw-browser}"
PW_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PW_DAEMON_JS="${PW_DAEMON_JS:-$PW_SCRIPT_DIR/pw-daemon.js}"

CHROME_FLAGS=(
  --remote-debugging-port="$PW_PORT"
  --user-data-dir="$PW_DATA"
  --no-first-run
  --no-default-browser-check
  --disable-extensions
  --disable-sync
  --autoplay-policy=no-user-gesture-required
  --disable-background-timer-throttling
  --disable-backgrounding-occluded-windows
  --disable-notifications
  --disable-popup-blocking
  --disable-translate
  --password-store=basic
  --disable-features=PasswordLeakDetection
  --lang=en-US
)

find_browser() {
  command -v chromium 2>/dev/null || command -v google-chrome-stable 2>/dev/null || command -v brave 2>/dev/null || echo ""
}

send_command() {
  local commandName="$1"
  shift
  local argsJson="[]"
  if [ $# -gt 0 ]; then
    argsJson=$(printf '%s\n' "$@" | jq -R . | jq -s .)
  fi
  local response
  local httpCode
  response=$(curl -sf -o - -w "\n%{http_code}" -X POST "http://127.0.0.1:$PW_DAEMON_PORT" \
    -H "Content-Type: application/json" \
    -d "{\"cmd\":$(echo "$commandName" | jq -R .),\"args\":$argsJson}" 2>/dev/null) || {
    echo "Error: daemon not responding" >&2
    return 1
  }
  httpCode=$(echo "$response" | tail -1)
  local body
  body=$(echo "$response" | sed '$d')
  if [ "$httpCode" = "200" ]; then
    [ -n "$body" ] && echo "$body"
    return 0
  else
    echo "Error: $body" >&2
    return 1
  fi
}

daemon_alive() {
  curl -sf -X POST "http://127.0.0.1:$PW_DAEMON_PORT" \
    -d '{"cmd":"ping","args":[]}' >/dev/null 2>&1
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
  close                           Kill browser and daemon
HELP
    exit 0
    ;;

  close)
    pkill -f "pw-daemon.js" 2>/dev/null || true
    pkill -f "remote-debugging-port=$PW_PORT.*user-data-dir=$PW_DATA" 2>/dev/null \
      && echo "Agent browser closed." \
      || echo "No agent browser running."
    exit 0
    ;;

  status)
    echo -n "Agent browser (port $PW_PORT): "
    curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1 && echo "ready" || echo "not running"
    echo -n "Daemon (port $PW_DAEMON_PORT): "
    daemon_alive && echo "ready" || echo "not running"
    exit 0
    ;;
esac

PW_HEADED="${PW_HEADED:-false}"
if [[ " ${*} " == *" --headed "* ]]; then
  PW_HEADED="true"
fi

if [ ! -d "$PW_CACHE/node_modules/playwright" ]; then
  echo "Installing playwright (one-time)..." >&2
  mkdir -p "$PW_CACHE"
  npm install --prefix "$PW_CACHE" --silent playwright 2>/dev/null
  echo "Done." >&2
fi

launch_browser() {
  BROWSER="$(find_browser)"
  if [ -z "$BROWSER" ]; then
    echo "Error: No browser found in PATH" >&2
    exit 1
  fi
  mkdir -p "$PW_DATA"
  if [ "$PW_HEADED" = "true" ]; then
    "$BROWSER" "${CHROME_FLAGS[@]}" "about:blank" >/dev/null 2>&1 &
  else
    "$BROWSER" --headless=new "${CHROME_FLAGS[@]}" >/dev/null 2>&1 &
  fi
  for _ in $(seq 1 20); do
    curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1 && break
    sleep 0.2
  done
  if ! curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1; then
    echo "Error: Failed to start agent browser on port $PW_PORT" >&2
    exit 1
  fi
}

if ! curl -sf "http://127.0.0.1:$PW_PORT/json/version" >/dev/null 2>&1; then
  launch_browser
elif [ "$PW_HEADED" = "true" ]; then
  BROWSER_PID=$(pgrep -f "remote-debugging-port=$PW_PORT.*user-data-dir=" 2>/dev/null | head -1)
  if [ -n "$BROWSER_PID" ] && tr '\0' ' ' < "/proc/$BROWSER_PID/cmdline" 2>/dev/null | grep -q headless; then
    pkill -f "pw-daemon.js" 2>/dev/null || true
    pkill -f "remote-debugging-port=$PW_PORT.*user-data-dir=$PW_DATA" 2>/dev/null || true
    sleep 0.5
    launch_browser
  fi
fi

if ! daemon_alive; then
  pkill -f "pw-daemon.js" 2>/dev/null || true
  NODE_PATH="$PW_CACHE/node_modules" PW_PORT="$PW_PORT" node "$PW_DAEMON_JS" >/dev/null 2>&1 &
  for _ in $(seq 1 30); do
    daemon_alive && break
    sleep 0.1
  done
  if ! daemon_alive; then
    echo "Error: Failed to start pw daemon" >&2
    exit 1
  fi
fi

FILTERED_ARGS=()
for arg in "$@"; do
  [[ "$arg" == "--headed" ]] && continue
  FILTERED_ARGS+=("$arg")
done

send_command "${FILTERED_ARGS[@]}"
