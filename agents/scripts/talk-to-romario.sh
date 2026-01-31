#!/usr/bin/env bash
# Talk to Romário via Grid Bridge (async — fire and forget)
# Usage: ./talk-to-romario.sh "message"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/bot-bridge.sh" romario "$1"
