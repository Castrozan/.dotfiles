#!/usr/bin/env bash
# Agent Grid — Bot-to-bot bridge via OpenClaw HTTP API over Tailscale
# Usage: bot-bridge.sh <target-agent> "message" [sync|async]
#
# Tokens are read from ~/.openclaw/grid-tokens/<agent>.token (never hardcoded)
# Uses user="8128478854" to route to the target agent's main Telegram session
set -euo pipefail

TARGET="${1:-}"
MESSAGE="${2:-}"
MODE="${3:-sync}"

# Grid agent registry (host:port)
declare -A GRID_HOSTS=(
  [cleber]="REDACTED_IP_1:18789"
  [romario]="REDACTED_IP_2:18790"
)

# Telegram relay config
ARMADA_LUCAS_GROUP="REDACTED_GROUP_ID"

if [ -z "$TARGET" ] || [ -z "$MESSAGE" ]; then
  echo "Usage: $0 <agent-name> \"message\" [sync|async]" >&2
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

# Read token from file
TOKEN_FILE="$HOME/.openclaw/grid-tokens/${TARGET}.token"
if [ ! -f "$TOKEN_FILE" ]; then
  echo "Token file not found: $TOKEN_FILE" >&2
  echo "Create it: echo 'your-token' > $TOKEN_FILE && chmod 400 $TOKEN_FILE" >&2
  exit 1
fi
TOKEN=$(cat "$TOKEN_FILE" | tr -d '[:space:]')

# Read own bot token for Telegram relay (optional)
OWN_BOT_TOKEN=""
if [ -f /run/agenix/telegram-bot-token ]; then
  OWN_BOT_TOKEN=$(cat /run/agenix/telegram-bot-token)
elif [ -f "$HOME/.openclaw/telegram-bot-token" ]; then
  OWN_BOT_TOKEN=$(cat "$HOME/.openclaw/telegram-bot-token")
fi

# Escape message for JSON
json_escape() {
  printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

send_api() {
  local msg="$1"
  local json_msg
  json_msg=$(json_escape "$msg")

  curl -s --max-time 120 -X POST "http://${HOST}:${PORT}/v1/chat/completions" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -H "x-openclaw-agent-id: main" \
    -H "x-openclaw-session-key: agent:main:default" \
    -d "{
      \"model\": \"anthropic/claude-opus-4-5\",
      \"messages\": [{\"role\": \"user\", \"content\": ${json_msg}}]
    }" | python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    print(d['choices'][0]['message']['content'])
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
"
}

send_api_async() {
  local msg="$1"
  local json_msg
  json_msg=$(json_escape "$msg")

  curl -s --max-time 5 -X POST "http://${HOST}:${PORT}/v1/chat/completions" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -H "x-openclaw-agent-id: main" \
    -H "x-openclaw-session-key: agent:main:default" \
    -d "{
      \"model\": \"anthropic/claude-opus-4-5\",
      \"messages\": [{\"role\": \"user\", \"content\": ${json_msg}}],
      \"stream\": true
    }" > /dev/null 2>&1 &

  echo "Message sent to ${TARGET} (async)"
}

relay_to_group() {
  local text="$1"
  if [ -n "$OWN_BOT_TOKEN" ]; then
    local encoded
    encoded=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$text")
    curl -s --max-time 10 "https://api.telegram.org/bot${OWN_BOT_TOKEN}/sendMessage?chat_id=${ARMADA_LUCAS_GROUP}&text=${encoded}" > /dev/null 2>&1 || true
  fi
}

# Relay outgoing message to Armada Lucas
relay_to_group "→ ${TARGET}: ${MESSAGE}"

if [ "$MODE" = "async" ]; then
  send_api_async "$MESSAGE"
else
  RESPONSE=$(send_api "$MESSAGE")
  relay_to_group "← ${TARGET}: ${RESPONSE}"
  echo "$RESPONSE"
fi
