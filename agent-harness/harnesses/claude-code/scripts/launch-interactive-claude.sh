#!/usr/bin/env bash

case "$#:${1:-}" in
1:--help | 1:-h | 1:--version | 1:-v) exec "$CLAUDE_LAUNCHER_BINARY" "$@" ;;
esac
claudeSystemPromptFile="$CLAUDE_LAUNCHER_SYSTEM_PROMPT_FILE"
claudeSettingsFile="$CLAUDE_LAUNCHER_SETTINGS_FILE"
# shellcheck source=/dev/null
source "$CLAUDE_LAUNCHER_WORKSPACE_PROFILE_DISPATCH_FILE"
export AGENT_INTERACTIVE_PREFERENCES_PATH="$claudeSystemPromptFile"
case "${1-}" in
remote-control | rc | remote | sync | bridge) exec "$CLAUDE_LAUNCHER_BINARY" "$@" ;;
esac
exec "$CLAUDE_LAUNCHER_BINARY" \
	--dangerously-skip-permissions \
	--append-system-prompt-file "$claudeSystemPromptFile" \
	--plugin-dir "$CLAUDE_LAUNCHER_PLUGIN_DIRECTORY" \
	--settings "$claudeSettingsFile" \
	"$@"
