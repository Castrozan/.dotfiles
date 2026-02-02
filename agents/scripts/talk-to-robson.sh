#!/usr/bin/env bash
# Talk to Robson via Grid Bridge (async — fire and forget)
# Usage: ./talk-to-robson.sh "message"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/bot-bridge.sh" robson "$1"
