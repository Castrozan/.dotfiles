#!/usr/bin/env bash
# Talk to Cleber via Grid Bridge (async — doesn't block on busy session)
# Usage: ./talk-to-cleber.sh "message"
# Messages queue in Cleber's main session and arrive when he's free.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/bot-bridge.sh" cleber "$1" async
