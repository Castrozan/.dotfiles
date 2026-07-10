#!/usr/bin/env bash

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

	herdr
}

case $- in
*i*)
	if [ "$TERM" != "dumb" ]; then
		_start_herdr
	fi
	;;
esac
