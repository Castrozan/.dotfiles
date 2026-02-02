#!/usr/bin/env bash
# Talk to Clever via Grid Bridge (async — fire and forget)
# Usage: ./talk-to-clever.sh "message"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/bot-bridge.sh" clever "$1"
