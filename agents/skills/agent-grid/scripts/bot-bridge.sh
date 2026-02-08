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

# Grid agent registry — read from agenix secret at runtime
GRID_HOSTS_FILE="/run/agenix/grid-hosts"
if [ ! -f "$GRID_HOSTS_FILE" ]; then
  echo "Grid hosts file not found: $GRID_HOSTS_FILE" >&2
  exit 1
fi

if [ -z "$TARGET" ] || [ -z "$MESSAGE" ]; then
  AGENTS=$(jq -r 'keys | join(", ")' "$GRID_HOSTS_FILE")
  echo "Usage: $0 <agent-name> \"message\"" >&2
  echo "Available agents: $AGENTS" >&2
  exit 1
fi

HOST_PORT=$(jq -r --arg t "$TARGET" '.[$t] // empty' "$GRID_HOSTS_FILE")
if [ -z "$HOST_PORT" ]; then
  AGENTS=$(jq -r 'keys | join(", ")' "$GRID_HOSTS_FILE")
  echo "Unknown agent: $TARGET" >&2
  echo "Available agents: $AGENTS" >&2
  exit 1
fi

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
    \"model\": \"@model@\",
    \"messages\": [{\"role\": \"user\", \"content\": ${json_msg}}],
    \"stream\": true
  }" > /dev/null 2>&1 &

echo "✉️  Message queued for ${TARGET}"
