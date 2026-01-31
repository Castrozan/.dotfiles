#!/usr/bin/env bash
# Talk to Cleber via Grid Bridge (async — fire and forget)
# Usage: ./talk-to-cleber.sh "message"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/bot-bridge.sh" cleber "$1"
