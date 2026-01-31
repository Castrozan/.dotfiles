#!/usr/bin/env bash
# Talk to Romário via Grid Bridge (sync — waits for response)
# Usage: ./talk-to-romario.sh "message"
# Routes to Romário's main Telegram session.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/bot-bridge.sh" romario "$1" sync
