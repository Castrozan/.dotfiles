readonly maximumWaitSeconds=180
readonly pollIntervalSeconds=2

waitDeadlineEpoch=$(($(date +%s) + maximumWaitSeconds))

while true; do
  backendState="$(tailscale status --json 2>/dev/null | jq -r '.BackendState // empty' 2>/dev/null || true)"
  if [ "$backendState" = "Running" ]; then
    exit 0
  fi
  if [ "$(date +%s)" -ge "$waitDeadlineEpoch" ]; then
    echo "tailscale backend did not reach Running within ${maximumWaitSeconds}s (last state: ${backendState:-unknown})" >&2
    exit 1
  fi
  sleep "$pollIntervalSeconds"
done
