#!/usr/bin/env bash

case "$#:${1:-}" in
1:--help | 1:-h | 1:--version | 1:-v) exec "$CLAUDE_LAUNCHER_BINARY" "$@" ;;
esac
export AGENT_INTERACTIVE_PREFERENCES_PATH="$CLAUDE_LAUNCHER_SYSTEM_PROMPT_FILE"
case "${1-}" in
remote-control | rc | remote | sync | bridge) exec "$CLAUDE_LAUNCHER_BINARY" "$@" ;;
esac
exec "$CLAUDE_LAUNCHER_BINARY" \
	--dangerously-skip-permissions \
	--append-system-prompt-file "$CLAUDE_LAUNCHER_SYSTEM_PROMPT_FILE" \
	--plugin-dir "$CLAUDE_LAUNCHER_PLUGIN_DIRECTORY" \
	--settings "$CLAUDE_LAUNCHER_SETTINGS_FILE" \
	"$@"
