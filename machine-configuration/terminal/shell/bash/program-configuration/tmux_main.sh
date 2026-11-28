#!/usr/bin/env bash

_start_main_tmux_session() {
	if ! tmux has-session -t main 2>/dev/null; then
		tmux new-session -d -s main -n main
	fi
}
