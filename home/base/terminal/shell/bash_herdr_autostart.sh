#!/usr/bin/env bash

_current_workspace_number() {
	local stateFilePath="${HAMMERSPOON_WORKSPACE_STATE_FILE:-$HOME/.cache/hammerspoon/workspace-grid-state}"
	local currentWorkspaceNumber
	currentWorkspaceNumber="$(head -1 "$stateFilePath" 2>/dev/null)"
	case "$currentWorkspaceNumber" in
	'' | *[!0-9]*) return ;;
	*) printf '%s\n' "$currentWorkspaceNumber" ;;
	esac
}

_current_workspace_herdr_session_name() {
	local currentWorkspaceNumber
	currentWorkspaceNumber="$(_current_workspace_number)"
	if [ -z "$currentWorkspaceNumber" ]; then
		return
	fi
	if [ -n "${HERDR_DEFAULT_SESSION_WORKSPACE_NUMBER:-}" ] &&
		[ "$currentWorkspaceNumber" = "$HERDR_DEFAULT_SESSION_WORKSPACE_NUMBER" ]; then
		return
	fi
	printf 'workspace-%s\n' "$currentWorkspaceNumber"
}

_start_herdr() {
	if [ -n "${HERDR_ENV:-}" ]; then
		return
	fi

	if [ -n "${TMUX:-}" ]; then
		return
	fi

	if ! command -v herdr >/dev/null 2>&1; then
		return
	fi

	if [ -n "${VSCODE_PID:-}" ] ||
		[[ "$(ps -o comm= -p "$PPID" 2>/dev/null)" == *cursor* ]]; then
		return
	fi

	local perWorkspaceSessionName
	perWorkspaceSessionName="$(_current_workspace_herdr_session_name)"
	if [ -n "$perWorkspaceSessionName" ]; then
		herdr --session "$perWorkspaceSessionName"
	else
		herdr
	fi
}

case $- in
*i*)
	if [ "$TERM" != "dumb" ]; then
		_start_herdr
	fi
	;;
esac
