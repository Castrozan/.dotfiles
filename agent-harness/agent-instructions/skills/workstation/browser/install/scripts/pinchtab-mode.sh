set -euo pipefail

requestedMode="${1:-status}"

waitForServerHealthy() {
  for _ in $(seq 1 20); do
    if [ "$(pinchtab health 2>/dev/null | head -n 1)" = "ok" ]; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

switchDisplayModeAndRestart() {
  local mode="$1"
  pinchtab config set instanceDefaults.mode "$mode" >/dev/null
  pinchtab server restart >/dev/null 2>&1 || true
  if waitForServerHealthy; then
    echo "pinchtab display mode is now ${mode}"
  else
    echo "pinchtab switched to ${mode} but the server did not report healthy within 10s; check 'pinchtab health'" >&2
  fi
  pinchtab instances 2>/dev/null || true
}

case "$requestedMode" in
  headed | headless)
    switchDisplayModeAndRestart "$requestedMode"
    ;;
  status)
    printf 'display mode: '
    pinchtab config get instanceDefaults.mode
    pinchtab instances 2>/dev/null || true
    ;;
  *)
    echo "usage: pinchtab-mode [headed|headless|status]" >&2
    exit 2
    ;;
esac
