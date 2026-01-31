#!/usr/bin/env bash
# Quick wrapper — talk to another agent in the grid (synchronous)
# Usage: talk-to-agent.sh <agent-name> "message"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/bot-bridge.sh" "$1" "$2" sync
