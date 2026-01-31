#!/usr/bin/env bash
# Talk to Romário via Grid Bridge (async — fire and forget)
# Usage: ./talk-to-romario.sh "message"
# Routes to Romário's main Telegram session. Message queues and arrives when he's free.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/bot-bridge.sh" romario "$1" async
