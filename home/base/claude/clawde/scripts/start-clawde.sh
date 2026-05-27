#!/usr/bin/env bash

set -euo pipefail

target_session_name="${1:-$DEFAULT_TMUX_SESSION_NAME}"

if "$TMUX_BIN" has-session -t "$target_session_name" 2>/dev/null; then
	echo "Session $target_session_name already running. Attach with: tmux attach -t $target_session_name" >&2
	exit 0
fi

systemctl --user restart "$SYSTEMD_USER_SERVICE_NAME"
