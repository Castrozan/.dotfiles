#!/usr/bin/env bash

_start_tmux() {
	if [ -n "${HERDR_ENV:-}" ]; then
		return
	fi

	if ! command -v tmux >/dev/null 2>&1; then
		return
	fi

	if ! tmux has-session -t screensaver 2>/dev/null; then
		(
			source "$HOME/.dotfiles/home/base/terminal/shell/screensaver.sh" 2>/dev/null || true
			source "$HOME/.dotfiles/home/base/terminal/shell/tmux_main.sh" 2>/dev/null || true
			_start_screensaver_tmux_session 2>/dev/null || true
			_start_main_tmux_session 2>/dev/null || true
		) &
	fi

	if [ -z "${TMUX:-}" ] &&
		[ -z "${VSCODE_PID:-}" ] &&
		[[ "$(ps -o comm= -p "$PPID" 2>/dev/null)" != *cursor* ]]; then
		tmux attach -t screensaver 2>/dev/null
	fi
}

case $- in
*i*)
	if [ "$TERM" != "dumb" ]; then
		_start_tmux
	fi
	;;
esac
