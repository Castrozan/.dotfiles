#!/usr/bin/env bash
# Agent Grid — Bot-to-bot bridge via OpenClaw HTTP API over Tailscale
# Usage: bot-bridge.sh <target-agent> "message"
#
# Always async: fires the message and returns immediately.
# The target gateway queues it; the bot processes it when free.
#
# Tokens are read from ~/.openclaw/grid-tokens/<agent>.token (never hardcoded)
set -euo pipefail

TARGET="${1:-}"
MESSAGE="${2:-}"

# Grid agent registry (host:port)
declare -A GRID_HOSTS=(
  [cleber]="REDACTED_IP_1:18789"
  [romario]="REDACTED_IP_2:18790"
)

if [ -z "$TARGET" ] || [ -z "$MESSAGE" ]; then
  echo "Usage: $0 <agent-name> \"message\"" >&2
  echo "Available agents: ${!GRID_HOSTS[*]}" >&2
  exit 1
fi

if [ -z "${GRID_HOSTS[$TARGET]+x}" ]; then
  echo "Unknown agent: $TARGET" >&2
  echo "Available agents: ${!GRID_HOSTS[*]}" >&2
  exit 1
fi

HOST_PORT="${GRID_HOSTS[$TARGET]}"
HOST="${HOST_PORT%%:*}"
PORT="${HOST_PORT##*:}"

# Read token: prefer agenix path, fall back to legacy location
AGENIX_TOKEN="/run/agenix/grid-token-${TARGET}"
LEGACY_TOKEN="$HOME/.openclaw/grid-tokens/${TARGET}.token"

if [ -f "$AGENIX_TOKEN" ]; then
  TOKEN=$(cat "$AGENIX_TOKEN" | tr -d '[:space:]')
elif [ -f "$LEGACY_TOKEN" ]; then
  TOKEN=$(cat "$LEGACY_TOKEN" | tr -d '[:space:]')
else
  echo "Token not found: $AGENIX_TOKEN or $LEGACY_TOKEN" >&2
  exit 1
fi

# Escape message for JSON
json_escape() {
  printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

json_msg=$(json_escape "$MESSAGE")

# Fire-and-forget: stream=true so gateway accepts immediately, curl disconnects after 5s
curl -s --max-time 5 -X POST "http://${HOST}:${PORT}/v1/chat/completions" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "x-openclaw-session-key: agent:main:main" \
  -d "{
    \"model\": \"anthropic/claude-opus-4-5\",
    \"messages\": [{\"role\": \"user\", \"content\": ${json_msg}}],
    \"stream\": true
  }" > /dev/null 2>&1 &

echo "✉️  Message queued for ${TARGET}"
