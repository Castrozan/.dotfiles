#!/usr/bin/env bash
# Kicks the clawde systemd-user service if no matching tmux session is already
# attached. Reports the existing attach command when already up.
# Driven by TMUX_BIN, TMUX_SESSION_NAME, SYSTEMD_USER_SERVICE_NAME env vars.

set -euo pipefail

if "$TMUX_BIN" has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
	echo "Session $TMUX_SESSION_NAME already running. Attach with: tmux attach -t $TMUX_SESSION_NAME" >&2
	exit 0
fi

systemctl --user restart "$SYSTEMD_USER_SERVICE_NAME"
