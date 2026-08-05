#!/usr/bin/env bash
jqBin="$1"
claudeConfigPath="$HOME/.claude.json"
if [ ! -f "$claudeConfigPath" ]; then
	exit 0
fi
currentWorkingDirectory="$(cd "$PWD" && pwd -P)"
if "$jqBin" -e --arg cwd "$currentWorkingDirectory" '.projects[$cwd].hasTrustDialogAccepted == true' "$claudeConfigPath" >/dev/null 2>&1; then
	exit 0
fi
temporaryFilePath="$(mktemp "${claudeConfigPath}.XXXXXX")"
if "$jqBin" --arg cwd "$currentWorkingDirectory" '.projects[$cwd].hasTrustDialogAccepted = true' "$claudeConfigPath" >"$temporaryFilePath"; then
	mv "$temporaryFilePath" "$claudeConfigPath"
else
	rm -f "$temporaryFilePath"
fi
