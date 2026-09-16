#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "setup" ]; then
	exec bash "$YOUTUBE_CLI_SETUP_SCRIPT"
fi

VENV="$YOUTUBE_CLI_VIRTUALENV_PATH"

if [ ! -f "$VENV/bin/python" ] || ! "$VENV/bin/pip" show google-api-python-client &>/dev/null; then
	echo "[nix] Installing youtube-cli dependencies..." >&2
	python -m venv "$VENV" 2>/dev/null || true
	"$VENV/bin/pip" install --quiet --upgrade \
		google-api-python-client \
		google-auth-oauthlib \
		google-auth-httplib2 >&2
fi

exec "$VENV/bin/python" "$YOUTUBE_CLI_SCRIPT" "$@"
